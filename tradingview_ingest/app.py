from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request

APP_VERSION = "tv-ingest-v0.2-log-ledger"
LAB_ID = "TV-FOOTPRINT-CALIBRATION-001"
SENSOR_VERSION = "MM-V1"
SYMBOL = "BINANCE:BTCUSDT"
TIMEFRAME = "5"
FORWARD_START_MS = 1790247600000  # 2026-09-24 11:00:00 UTC
BAR_MS = 300000
MAX_BODY_BYTES = 64_000
RECENT_KEYS_MAX = 4096
LOG_PREFIX = "TVFP_RECEIPT "

REQUIRED_KEYS = {
    "lab_id",
    "sensor_version",
    "symbol",
    "timeframe",
    "bar_open_ms",
    "bar_close_ms",
    "close",
    "tv_total_volume",
    "tv_buy_volume",
    "tv_sell_volume",
    "tv_delta",
    "tv_delta_pct",
    "poc_mid",
    "poc_migration_bps",
    "vah",
    "val",
    "buy_imbalance_rows",
    "sell_imbalance_rows",
    "footprint_rows",
    "ltf_intrabars",
    "ltf_path_efficiency",
    "ltf_signed_volume_pct",
    "volume_z",
    "bar_return_bps",
    "eth_ret",
    "sol_ret",
    "cme_btc_ret",
    "ndx_ret",
    "dxy_ret",
}

INT_KEYS = {
    "bar_open_ms",
    "bar_close_ms",
    "buy_imbalance_rows",
    "sell_imbalance_rows",
    "footprint_rows",
    "ltf_intrabars",
}

FLOAT_OR_NULL_KEYS = REQUIRED_KEYS - {
    "lab_id", "sensor_version", "symbol", "timeframe"
} - INT_KEYS


class ValidationError(ValueError):
    pass


def _token() -> str:
    value = os.getenv("TV_WEBHOOK_TOKEN", "")
    if len(value) < 24:
        raise RuntimeError("TV_WEBHOOK_TOKEN missing or too short")
    return value


def _is_number_or_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("payload must be a JSON object")

    missing = sorted(REQUIRED_KEYS - set(payload))
    extra = sorted(set(payload) - REQUIRED_KEYS)
    if missing:
        raise ValidationError("missing keys: " + ",".join(missing))
    if extra:
        raise ValidationError("unknown keys: " + ",".join(extra))

    expected_identity = {
        "lab_id": LAB_ID,
        "sensor_version": SENSOR_VERSION,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
    }
    for key, expected in expected_identity.items():
        if payload.get(key) != expected:
            raise ValidationError(f"{key} mismatch")

    for key in INT_KEYS:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(f"{key} must be integer")

    for key in FLOAT_OR_NULL_KEYS:
        if not _is_number_or_null(payload.get(key)):
            raise ValidationError(f"{key} must be finite number or null")

    if payload["bar_open_ms"] % BAR_MS != 0:
        raise ValidationError("bar_open_ms not aligned to UTC 5-minute boundary")
    if payload["bar_close_ms"] - payload["bar_open_ms"] != BAR_MS:
        raise ValidationError("bar interval must equal 5 minutes")
    if payload["bar_close_ms"] < FORWARD_START_MS:
        raise ValidationError("pre-forward-boundary observation rejected")

    if payload["footprint_rows"] < 0:
        raise ValidationError("footprint_rows cannot be negative")
    if payload["ltf_intrabars"] < 0 or payload["ltf_intrabars"] > 5:
        raise ValidationError("ltf_intrabars outside frozen 0..5 range")
    if payload["buy_imbalance_rows"] < 0 or payload["sell_imbalance_rows"] < 0:
        raise ValidationError("imbalance row counts cannot be negative")

    return payload


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def evidence_key(payload: dict[str, Any]) -> str:
    return "|".join(
        [
            payload["lab_id"],
            payload["sensor_version"],
            payload["symbol"],
            payload["timeframe"],
            str(payload["bar_close_ms"]),
        ]
    )


def receipt_record(payload: dict[str, Any], received_at: datetime) -> dict[str, Any]:
    canonical = canonical_payload(payload)
    return {
        "record_type": "TVFP_RECEIPT",
        "app_version": APP_VERSION,
        "received_at": received_at.isoformat(),
        "evidence_key": evidence_key(payload),
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "payload": payload,
        "trading_authority": "NONE",
    }


def emit_receipt(record: dict[str, Any]) -> None:
    line = LOG_PREFIX + json.dumps(
        record,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    print(line, file=sys.stdout, flush=True)


app = Flask(__name__)
_recent: OrderedDict[str, None] = OrderedDict()
accepted_in_process = 0
duplicates_in_process = 0


def _auth(path_token: str) -> bool:
    try:
        expected = _token()
    except RuntimeError:
        return False
    return hmac.compare_digest(path_token, expected)


def _remember(key: str) -> bool:
    """Return True if key was already observed in the current process."""
    if key in _recent:
        _recent.move_to_end(key)
        return True
    _recent[key] = None
    if len(_recent) > RECENT_KEYS_MAX:
        _recent.popitem(last=False)
    return False


@app.get("/health")
def health():
    token_ok = len(os.getenv("TV_WEBHOOK_TOKEN", "")) >= 24
    return jsonify(
        {
            "service": "tradingview-research-ingest",
            "version": APP_VERSION,
            "token_configured": token_ok,
            "lab_id": LAB_ID,
            "sensor_version": SENSOR_VERSION,
            "transport_ledger": "render_app_logs",
            "trading_authority": "NONE",
        }
    ), 200 if token_ok else 503


@app.post("/v1/tradingview/<path_token>")
def ingest(path_token: str):
    global accepted_in_process, duplicates_in_process

    if not _auth(path_token):
        return jsonify({"status": "rejected", "reason": "unauthorized"}), 401

    if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
        return jsonify({"status": "rejected", "reason": "payload_too_large"}), 413

    payload = request.get_json(silent=True)
    try:
        payload = validate_payload(payload)
    except ValidationError as exc:
        return jsonify({"status": "rejected", "reason": str(exc)}), 422

    now = datetime.now(timezone.utc)
    record = receipt_record(payload, now)
    key = record["evidence_key"]
    duplicate = _remember(key)

    # Every accepted delivery is logged. The evidence key is deterministic, so
    # final corpus extraction deduplicates independently of process restarts.
    emit_receipt(record)

    if duplicate:
        duplicates_in_process += 1
    else:
        accepted_in_process += 1

    return jsonify(
        {
            "status": "duplicate_in_process" if duplicate else "accepted",
            "evidence_key": key,
            "payload_sha256": record["payload_sha256"],
            "bar_close_ms": payload["bar_close_ms"],
            "trading_authority": "NONE",
        }
    ), 200 if duplicate else 202


@app.get("/v1/status/<path_token>")
def status(path_token: str):
    if not _auth(path_token):
        return jsonify({"status": "rejected", "reason": "unauthorized"}), 401

    return jsonify(
        {
            "lab_id": LAB_ID,
            "sensor_version": SENSOR_VERSION,
            "symbol": SYMBOL,
            "timeframe": TIMEFRAME,
            "accepted_in_current_process": accepted_in_process,
            "duplicates_in_current_process": duplicates_in_process,
            "recent_evidence_keys_in_memory": len(_recent),
            "authoritative_count_source": "render_app_logs_after_dedup",
            "minimum_terminal_bars": 2016,
            "trading_authority": "NONE",
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
