from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from typing import Any

import psycopg
from flask import Flask, jsonify, request

APP_VERSION = "tv-ingest-v0.1"
LAB_ID = "TV-FOOTPRINT-CALIBRATION-001"
SENSOR_VERSION = "MM-V1"
SYMBOL = "BINANCE:BTCUSDT"
TIMEFRAME = "5"
FORWARD_START_MS = 1790247600000  # 2026-09-24 11:00:00 UTC

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

DDL = """
CREATE TABLE IF NOT EXISTS tv_footprint_calibration_receipts (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL,
    app_version TEXT NOT NULL,
    lab_id TEXT NOT NULL,
    sensor_version TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    bar_open_ms BIGINT NOT NULL,
    bar_close_ms BIGINT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    raw_payload JSONB NOT NULL,
    UNIQUE (lab_id, sensor_version, symbol, timeframe, bar_close_ms)
);

CREATE INDEX IF NOT EXISTS idx_tvfp_received_at
    ON tv_footprint_calibration_receipts (received_at DESC);

CREATE INDEX IF NOT EXISTS idx_tvfp_bar_close
    ON tv_footprint_calibration_receipts (bar_close_ms DESC);
"""


class ValidationError(ValueError):
    pass


def _dsn() -> str:
    value = os.getenv("TELEMETRY_DB_DSN") or os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("TELEMETRY_DB_DSN/DATABASE_URL missing")
    return value


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

    identity = {
        "lab_id": LAB_ID,
        "sensor_version": SENSOR_VERSION,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
    }
    for key, expected in identity.items():
        if payload.get(key) != expected:
            raise ValidationError(f"{key} mismatch")

    for key in INT_KEYS:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(f"{key} must be integer")

    for key in FLOAT_OR_NULL_KEYS:
        if not _is_number_or_null(payload.get(key)):
            raise ValidationError(f"{key} must be finite number or null")

    if payload["bar_open_ms"] % 300000 != 0:
        raise ValidationError("bar_open_ms not aligned to UTC 5-minute boundary")
    if payload["bar_close_ms"] - payload["bar_open_ms"] != 300000:
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


def ensure_schema() -> None:
    with psycopg.connect(_dsn(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()


def _db_health() -> tuple[bool, str]:
    try:
        with psycopg.connect(_dsn(), connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True, "ok"
    except Exception as exc:
        return False, type(exc).__name__


def _auth(path_token: str) -> bool:
    supplied = path_token.encode("utf-8")
    expected = _token().encode("utf-8")
    return hashlib.sha256(supplied).digest() == hashlib.sha256(expected).digest()


app = Flask(__name__)
_schema_ready = False


@app.get("/health")
def health():
    db_ok, db_state = _db_health()
    status = 200 if db_ok else 503
    return jsonify(
        {
            "service": "tradingview-research-ingest",
            "version": APP_VERSION,
            "db": db_state,
            "lab_id": LAB_ID,
            "trading_authority": "NONE",
        }
    ), status


@app.post("/v1/tradingview/<path_token>")
def ingest(path_token: str):
    global _schema_ready

    if not _auth(path_token):
        return jsonify({"status": "rejected", "reason": "unauthorized"}), 401

    if request.content_length is not None and request.content_length > 64_000:
        return jsonify({"status": "rejected", "reason": "payload_too_large"}), 413

    payload = request.get_json(silent=True)
    try:
        payload = validate_payload(payload)
    except ValidationError as exc:
        return jsonify({"status": "rejected", "reason": str(exc)}), 422

    if not _schema_ready:
        ensure_schema()
        _schema_ready = True

    received_at = datetime.now(timezone.utc)
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_sha = hashlib.sha256(canonical).hexdigest()

    inserted = False
    receipt_id = None

    with psycopg.connect(_dsn(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tv_footprint_calibration_receipts (
                    received_at, app_version, lab_id, sensor_version, symbol,
                    timeframe, bar_open_ms, bar_close_ms, payload_sha256, raw_payload
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                ON CONFLICT (lab_id, sensor_version, symbol, timeframe, bar_close_ms)
                DO NOTHING
                RETURNING id
                """,
                (
                    received_at,
                    APP_VERSION,
                    payload["lab_id"],
                    payload["sensor_version"],
                    payload["symbol"],
                    payload["timeframe"],
                    payload["bar_open_ms"],
                    payload["bar_close_ms"],
                    payload_sha,
                    json.dumps(payload, separators=(",", ":"), sort_keys=True),
                ),
            )
            row = cur.fetchone()
            if row:
                inserted = True
                receipt_id = row[0]
        conn.commit()

    return jsonify(
        {
            "status": "accepted" if inserted else "duplicate",
            "receipt_id": receipt_id,
            "bar_close_ms": payload["bar_close_ms"],
            "payload_sha256": payload_sha,
            "trading_authority": "NONE",
        }
    ), 202 if inserted else 200


@app.get("/v1/status/<path_token>")
def status(path_token: str):
    if not _auth(path_token):
        return jsonify({"status": "rejected", "reason": "unauthorized"}), 401

    ensure_schema()

    with psycopg.connect(_dsn(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*),
                    MIN(bar_close_ms),
                    MAX(bar_close_ms),
                    MAX(received_at)
                FROM tv_footprint_calibration_receipts
                WHERE lab_id=%s AND sensor_version=%s AND symbol=%s AND timeframe=%s
                """,
                (LAB_ID, SENSOR_VERSION, SYMBOL, TIMEFRAME),
            )
            count, min_bar, max_bar, last_received = cur.fetchone()

    return jsonify(
        {
            "lab_id": LAB_ID,
            "sensor_version": SENSOR_VERSION,
            "symbol": SYMBOL,
            "timeframe": TIMEFRAME,
            "receipts": int(count),
            "first_bar_close_ms": min_bar,
            "last_bar_close_ms": max_bar,
            "last_received_at": last_received.isoformat() if last_received else None,
            "minimum_terminal_bars": 2016,
            "terminal_gate_ready": int(count) >= 2016,
            "trading_authority": "NONE",
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
