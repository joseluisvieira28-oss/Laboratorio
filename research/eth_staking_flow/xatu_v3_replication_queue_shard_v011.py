#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("base_rep_source", HERE / "xatu_v3_replication_queue_shard_v01.py")
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

ORIGINAL_RECONSTRUCT_DAY = base.reconstruct_day
MAX_ATTEMPTS = 5


def retryable(exc: Exception) -> bool:
    if isinstance(exc, (OSError, TimeoutError, ConnectionError)):
        return True
    s = f"{type(exc).__name__}: {exc}".lower()
    keys = (
        "timeout", "timed out", "429", "502", "503", "504",
        "connection", "reset", "temporarily unavailable",
        "server disconnected", "response payload", "eof", "ssl",
        "remote protocol", "broken pipe",
    )
    return any(k in s for k in keys)


def reconstruct_day_v011(d):
    last = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            row = ORIGINAL_RECONSTRUCT_DAY(d)
            if attempt:
                row["transport_recovery_attempts"] = attempt + 1
            return row
        except Exception as exc:
            last = exc
            if not retryable(exc) or attempt >= MAX_ATTEMPTS - 1:
                raise
            delay = 2 ** (attempt + 1)
            print(json.dumps({
                "progress": "xatu_transport_retry",
                "date": d.isoformat(),
                "attempt": attempt + 1,
                "max_attempts": MAX_ATTEMPTS,
                "delay_seconds": delay,
                "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            }, sort_keys=True), flush=True)
            time.sleep(delay)
    raise last  # pragma: no cover


def main() -> int:
    base.reconstruct_day = reconstruct_day_v011
    rc = base.main()

    sid = base.os.environ["SHARD_ID"]
    p = Path("xatu_v3_replication_shards") / f"queue_rep_{sid}.json"
    if not p.exists():
        return 2

    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_SHARD_V0_1_1_TRANSPORT_RECOVERY"
    x["transport_recovery"] = {
        "original_run_id": 35387477455,
        "allowed_shards": ["202502", "202503", "202510"],
        "max_attempts_per_day": MAX_ATTEMPTS,
        "same_day_same_url_only": True,
        "scientific_rule_changed": False,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    if sid not in x["transport_recovery"]["allowed_shards"]:
        x["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        x["errors"] = (x.get("errors") or []) + [{"date": None, "error": "recovery shard outside frozen allowlist"}]
        rc = 2

    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "shard": sid,
        "classification": x.get("classification"),
        "observed": x.get("observed_dates"),
        "errors": len(x.get("errors") or []),
        "transport_recovery": True,
        "signal": False,
        "market": False,
        "returns": False,
        "pnl": False,
    }, sort_keys=True), flush=True)
    return 0 if x.get("classification") == "SHARD_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
