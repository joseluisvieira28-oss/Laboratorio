#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

FRONTIER_ID = "AAVE-RISK-PARAMETER-SHOCK-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
MAX_TS = 1_735_689_599
MAX_WINDOW = 75_000
TRANSIENT = {429, 500, 502, 503, 504, 529}

EVENT_SIGNATURES = {
    "ReserveBorrowing": "ReserveBorrowing(address,bool)",
    "CollateralConfigurationChanged": "CollateralConfigurationChanged(address,uint256,uint256,uint256)",
    "ReserveStableRateBorrowing": "ReserveStableRateBorrowing(address,bool)",
    "ReserveActive": "ReserveActive(address,bool)",
    "ReserveFrozen": "ReserveFrozen(address,bool)",
    "ReservePaused": "ReservePaused(address,bool)",
    "ReserveFactorChanged": "ReserveFactorChanged(address,uint256,uint256)",
    "BorrowCapChanged": "BorrowCapChanged(address,uint256,uint256)",
    "SupplyCapChanged": "SupplyCapChanged(address,uint256,uint256)",
    "LiquidationProtocolFeeChanged": "LiquidationProtocolFeeChanged(address,uint256,uint256)",
    "UnbackedMintCapChanged": "UnbackedMintCapChanged(address,uint256,uint256)",
    "EModeAssetCategoryChanged": "EModeAssetCategoryChanged(address,uint8,uint8)",
    "EModeCategoryAdded": "EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)",
    "ReserveInterestRateStrategyChanged": "ReserveInterestRateStrategyChanged(address,address,address)",
    "DebtCeilingChanged": "DebtCeilingChanged(address,uint256,uint256)",
    "SiloedBorrowingChanged": "SiloedBorrowingChanged(address,bool,bool)",
    "BorrowableInIsolationChanged": "BorrowableInIsolationChanged(address,bool)",
}
TOPIC_TO_EVENT = {"0x" + keccak(v.encode()).hex(): k for k, v in EVENT_SIGNATURES.items()}
TOPICS = sorted(TOPIC_TO_EVENT)

def post(body: dict[str, Any], stats: dict[str, int]) -> requests.Response:
    last = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL,
                json=body,
                timeout=(20, 180),
                stream=True,
                headers={
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip",
                    "User-Agent": FRONTIER_ID + "/source-census-v0.1",
                },
            )
            stats["http_attempts"] += 1
            if r.status_code in TRANSIENT:
                last = RuntimeError(f"transient HTTP {r.status_code}")
                retry_after = r.headers.get("Retry-After")
                r.close()
                if attempt < 7:
                    stats["transient_retries"] += 1
                    try:
                        delay = float(retry_after) if retry_after else min(20.0, 1.5 * (2 ** attempt))
                    except ValueError:
                        delay = min(20.0, 1.5 * (2 ** attempt))
                    time.sleep(delay)
                    continue
                raise last
            if r.status_code == 204:
                r.close()
                raise RuntimeError("unexpected Portal 204 inside frozen range")
            r.raise_for_status()
            stats["successful_http_responses"] += 1
            return r
        except (requests.RequestException, RuntimeError) as exc:
            last = exc
            if attempt < 7:
                stats["network_retries"] += 1
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
            raise
    raise RuntimeError(str(last))

def stream_range(stats: dict[str, int]):
    cursor = FROM_BLOCK
    while cursor <= TO_BLOCK:
        request_to = min(TO_BLOCK, cursor + MAX_WINDOW - 1)
        body = {
            "type": "evm",
            "fromBlock": cursor,
            "toBlock": request_to,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": {
                    "address": True,
                    "topics": True,
                    "transactionHash": True,
                    "logIndex": True,
                },
            },
            "logs": [{"address": [CONFIGURATOR], "topic0": TOPICS}],
        }
        r = post(body, stats)
        page_last = None
        rows = 0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                header = obj.get("header") or obj.get("block") or {}
                bn = header.get("number")
                if bn is None:
                    raise RuntimeError("Portal row missing continuation block number")
                bn = int(bn)
                if not (cursor <= bn <= request_to):
                    raise RuntimeError("Portal row outside requested transport window")
                if page_last is not None and bn < page_last:
                    raise RuntimeError("Portal page non-monotonic")
                page_last = bn
                rows += 1
                yield obj
        finally:
            r.close()
        if rows == 0 or page_last is None:
            # Sparse configurator events can legitimately produce a healthy
            # zero-match transport window. Treat the exact requested window as
            # covered and advance without manufacturing a scientific event.
            stats["empty_windows"] += 1
            stats["windows_completed"] += 1
            yield {"__transport_only__": True, "header": {"number": request_to}}
            cursor = request_to + 1
            continue
        if page_last < cursor:
            raise RuntimeError("Portal continuation did not advance")
        stats["portal_rows"] += rows
        stats["windows_completed"] += 1
        cursor = page_last + 1

def main() -> int:
    counts: Counter[str] = Counter()
    seen: set[tuple[str, int]] = set()
    structural = hashlib.sha256()
    stats = {
        "http_attempts": 0,
        "successful_http_responses": 0,
        "transient_retries": 0,
        "network_retries": 0,
        "portal_rows": 0,
        "windows_completed": 0,
        "empty_windows": 0,
    }
    first_ts = None
    last_ts = None
    terminal = None
    failure = None

    try:
        for obj in stream_range(stats):
            header = obj.get("header") or obj.get("block") or {}
            bn = int(header["number"])
            terminal = bn
            if obj.get("__transport_only__"):
                continue
            ts = int(header["timestamp"])
            if ts > MAX_TS:
                raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
            for log in obj.get("logs") or []:
                address = str(log.get("address", "")).lower()
                topics = log.get("topics") or []
                txh = log.get("transactionHash")
                li = log.get("logIndex")
                if address != CONFIGURATOR:
                    raise RuntimeError("unexpected contract address")
                if not topics or not txh or li is None:
                    raise RuntimeError("malformed log identity")
                topic0 = str(topics[0]).lower()
                event = TOPIC_TO_EVENT.get(topic0)
                if event is None:
                    raise RuntimeError("unexpected topic0")
                li_int = int(li, 16) if isinstance(li, str) and li.startswith("0x") else int(li)
                key = (str(txh).lower(), li_int)
                if key in seen:
                    raise RuntimeError("duplicate log identity")
                seen.add(key)
                counts[event] += 1
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)
                structural.update(f"{bn}|{str(txh).lower()}|{li_int}|{address}|{topic0}\n".encode())
        if terminal != TO_BLOCK:
            raise RuntimeError(f"terminal header {terminal} != frozen end {TO_BLOCK}")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:500]}"

    if failure:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    elif not seen:
        classification = "INSUFFICIENT_SOURCE_SAMPLE"
    elif last_ts is None or last_ts > MAX_TS:
        classification = "PROVENANCE_FAILURE"
    else:
        classification = "SOURCE_CENSUS_PASS"

    receipt = {
        "frontier_id": FRONTIER_ID,
        "phase": "SOURCE_CENSUS_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "source": "SQD ethereum-mainnet Portal",
        "pool_configurator": CONFIGURATOR,
        "from_block": FROM_BLOCK,
        "to_block": TO_BLOCK,
        "hard_timestamp_ceiling": MAX_TS,
        "event_counts": dict(sorted(counts.items())),
        "total_structural_events": sum(counts.values()),
        "unique_log_ids": len(seen),
        "first_matching_timestamp": first_ts,
        "last_matching_timestamp": last_ts,
        "terminal_header_block": terminal,
        "structural_sha256": structural.hexdigest(),
        "transport_stats": stats,
        "failure": failure,
        "safety": {
            "log_data_requested": False,
            "parameter_values_decoded": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "future_liquidation_outcomes_opened": False,
            "health_factor_computed": False,
            "liquidation_overhang_computed": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("out/aave_risk_parameter_shock")
    out.mkdir(parents=True, exist_ok=True)
    p = out / "AAVE_RISK_PARAMETER_SHOCK_001_SOURCE_CENSUS_RECEIPT_V0_1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "total_structural_events": sum(counts.values()),
        "event_counts": dict(sorted(counts.items())),
        "unique_log_ids": len(seen),
        "terminal_header_block": terminal,
        "log_data_requested": False,
        "returns_opened": False,
        "pnl_opened": False,
        "accessed_2025_or_2026": False,
    }, sort_keys=True))
    return 0 if classification in {"SOURCE_CENSUS_PASS", "INSUFFICIENT_SOURCE_SAMPLE"} else 2

if __name__ == "__main__":
    raise SystemExit(main())
