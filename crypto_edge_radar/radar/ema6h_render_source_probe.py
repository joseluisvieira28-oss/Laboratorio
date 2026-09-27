from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .strategies.ema6h_50x200_regime_forward import BinanceSpotKlineFeed

CANONICAL_RENDER_SERVICE_ID = "srv-dalqkpu1egvs73fhiehg"
OFFICIAL_BINANCE_SPOT_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("MARKET_DATA_ONLY", "https://data-api.binance.vision"),
    ("PRIMARY", "https://api.binance.com"),
    ("GCP", "https://api-gcp.binance.com"),
    ("API1", "https://api1.binance.com"),
    ("API2", "https://api2.binance.com"),
    ("API3", "https://api3.binance.com"),
    ("API4", "https://api4.binance.com"),
)

SAMPLE_SYMBOL = "BTCUSDT"
SAMPLE_INTERVAL = "15m"
SAMPLE_START_UTC = "2026-09-26T00:00:00Z"
SAMPLE_END_UTC = "2026-09-26T02:00:00Z"


def _ms(iso: str) -> int:
    return int(
        datetime.fromisoformat(iso.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .timestamp()
        * 1000
    )


def _scientific_sha(rows: list[Any]) -> str:
    science = [
        [
            int(row.open_time),
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            float(row.volume),
            int(row.close_time),
        ]
        for row in rows
    ]
    raw = json.dumps(science, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def probe_official_binance_hosts(
    *,
    timeout: int = 5,
    endpoints: tuple[tuple[str, str], ...] = OFFICIAL_BINANCE_SPOT_ENDPOINTS,
) -> dict[str, Any]:
    start_ms = _ms(SAMPLE_START_UTC)
    end_ms = _ms(SAMPLE_END_UTC)
    now_ms = _ms("2026-09-27T00:00:00Z")

    observations: list[dict[str, Any]] = []
    hashes: dict[str, list[str]] = {}

    for label, base_url in endpoints:
        feed = BinanceSpotKlineFeed(
            timeout=timeout,
            max_attempts=1,
            retry_backoff_seconds=0,
        )
        feed.base_url = base_url
        try:
            rows = feed.klines(
                SAMPLE_SYMBOL,
                SAMPLE_INTERVAL,
                start_ms=start_ms,
                end_ms=end_ms,
                now_ms=now_ms,
            )
            digest = _scientific_sha(rows)
            hashes.setdefault(digest, []).append(label)
            observations.append(
                {
                    "label": label,
                    "base_url": base_url,
                    "status": "PASS",
                    "rows": len(rows),
                    "scientific_sha256": digest,
                }
            )
        except Exception as exc:
            observations.append(
                {
                    "label": label,
                    "base_url": base_url,
                    "status": "ERROR",
                    "error_class": type(exc).__name__,
                    "error": str(exc)[:240],
                }
            )

    passing = [x for x in observations if x["status"] == "PASS"]
    if len(passing) >= 2 and len(hashes) == 1:
        classification = "PASS_EXACT_MULTI_HOST_EQUIVALENCE"
        equivalent_multi_host = True
    elif len(passing) >= 2 and len(hashes) > 1:
        classification = "FAIL_CLOSED_MULTI_HOST_DIVERGENCE"
        equivalent_multi_host = False
    elif len(passing) == 1:
        classification = "SINGLE_ACCESSIBLE_HOST_ONLY"
        equivalent_multi_host = False
    else:
        classification = "NO_ACCESSIBLE_BINANCE_SPOT_HOST"
        equivalent_multi_host = False

    return {
        "schema_version": "EMA6H_RENDER_SOURCE_PROBE_V0.1",
        "classification": classification,
        "equivalent_multi_host": equivalent_multi_host,
        "sample": {
            "symbol": SAMPLE_SYMBOL,
            "interval": SAMPLE_INTERVAL,
            "start_utc": SAMPLE_START_UTC,
            "end_utc": SAMPLE_END_UTC,
        },
        "passing_hosts": [x["label"] for x in passing],
        "distinct_scientific_hashes": len(hashes),
        "hash_groups": hashes,
        "observations": observations,
        "diagnostic_only": True,
        "automatic_source_switch": False,
        "science_changed": False,
        "outcomes_changed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


def emit_probe_log(*, timeout: int = 5) -> dict[str, Any]:
    receipt = probe_official_binance_hosts(timeout=timeout)
    print("EMA6H_RENDER_SOURCE_PROBE " + json.dumps(receipt, sort_keys=True), flush=True)
    return receipt
