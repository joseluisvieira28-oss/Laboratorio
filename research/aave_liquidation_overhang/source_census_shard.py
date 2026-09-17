#!/usr/bin/env python3
"""Transport-only shard for AAVE-LIQUIDATION-OVERHANG-001 source census.

Safety:
- source-only / outcome-blind;
- requests no log.data;
- decodes no economic values;
- reads only the block interval provided by SHARD_FROM_BLOCK/SHARD_TO_BLOCK;
- hard ceiling remains 2024-12-31T23:59:59Z.

A shard is not a scientific pass by itself. Only aggregate_source_census.py may
adjudicate SOURCE_CENSUS_PASS after proving exact contiguous coverage of the
frozen global envelope.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
GLOBAL_FROM_BLOCK = 16_490_000
GLOBAL_TO_BLOCK = 21_525_890
MAX_TS = 1_735_689_599
MAX_HTTP_BLOCK_WINDOW = 75_000
TRANSIENT = {429, 500, 502, 503, 504, 529}

EVENT_SIGNATURES = {
    "Supply": "Supply(address,address,address,uint256,uint16)",
    "Withdraw": "Withdraw(address,address,address,uint256)",
    "Borrow": "Borrow(address,address,address,uint256,uint8,uint256,uint16)",
    "Repay": "Repay(address,address,address,uint256,bool)",
    "ReserveUsedAsCollateralEnabled": "ReserveUsedAsCollateralEnabled(address,address)",
    "ReserveUsedAsCollateralDisabled": "ReserveUsedAsCollateralDisabled(address,address)",
    "LiquidationCall": "LiquidationCall(address,address,address,uint256,uint256,address,bool)",
    "ReserveDataUpdated": "ReserveDataUpdated(address,uint256,uint256,uint256,uint256,uint256)",
    "UserEModeSet": "UserEModeSet(address,uint8)",
    "ReserveInitialized": "ReserveInitialized(address,address,address,address,address)",
}
TOPIC_TO_EVENT = {"0x" + keccak(sig.encode()).hex(): name for name, sig in EVENT_SIGNATURES.items()}
POOL_TOPICS = [t for t, n in TOPIC_TO_EVENT.items() if n != "ReserveInitialized"]
CONFIG_TOPICS = [t for t, n in TOPIC_TO_EVENT.items() if n == "ReserveInitialized"]
USER_TOPIC_INDEX = {
    "Supply": 2, "Withdraw": 2, "Borrow": 2, "Repay": 2,
    "ReserveUsedAsCollateralEnabled": 2, "ReserveUsedAsCollateralDisabled": 2,
    "LiquidationCall": 3, "UserEModeSet": 1,
}


def topic_address(topic: str) -> str:
    if not isinstance(topic, str) or not topic.startswith("0x") or len(topic) != 66:
        raise ValueError("invalid indexed address topic")
    return "0x" + topic[-40:].lower()


def post(body: dict[str, Any], stats: dict[str, int]) -> requests.Response:
    last = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL, json=body, timeout=(20, 180), stream=True,
                headers={"Content-Type": "application/json", "Accept-Encoding": "gzip",
                         "User-Agent": f"{LAB_ID}/source-census-shard-v0.1"},
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


def stream_range(start: int, end: int, stats: dict[str, int]):
    cursor = start
    while cursor <= end:
        request_to = min(end, cursor + MAX_HTTP_BLOCK_WINDOW - 1)
        body = {
            "type": "evm", "fromBlock": cursor, "toBlock": request_to,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": {"address": True, "topics": True, "transactionHash": True, "logIndex": True},
            },
            "logs": [
                {"address": [POOL], "topic0": POOL_TOPICS},
                {"address": [CONFIGURATOR], "topic0": CONFIG_TOPICS},
            ],
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
            raise RuntimeError("Portal returned empty page inside frozen range")
        stats["portal_rows"] += rows
        cursor = page_last + 1


def main() -> int:
    start = int(os.environ["SHARD_FROM_BLOCK"])
    end = int(os.environ["SHARD_TO_BLOCK"])
    shard_id = os.environ.get("SHARD_ID", f"{start}-{end}")
    if not (GLOBAL_FROM_BLOCK <= start <= end <= GLOBAL_TO_BLOCK):
        raise SystemExit("invalid shard outside frozen envelope")

    counts: Counter[str] = Counter()
    users_by_event: dict[str, set[str]] = defaultdict(set)
    all_users: set[str] = set()
    liq_users: set[str] = set()
    seen: set[tuple[str, int]] = set()
    h = hashlib.sha256()
    first_ts = last_ts = None
    terminal = None
    failure = None
    stats = {"http_attempts": 0, "successful_http_responses": 0, "transient_retries": 0,
             "network_retries": 0, "portal_rows": 0}

    try:
        for obj in stream_range(start, end, stats):
            header = obj.get("header") or obj.get("block") or {}
            bn, ts = int(header["number"]), int(header["timestamp"])
            terminal = bn
            if ts > MAX_TS:
                raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)
            for log in obj.get("logs") or []:
                addr = str(log.get("address", "")).lower()
                topics = log.get("topics") or []
                txh, li = log.get("transactionHash"), log.get("logIndex")
                if addr not in (POOL, CONFIGURATOR) or not txh or li is None or not topics:
                    raise RuntimeError("invalid structural log")
                lii = int(li, 16) if isinstance(li, str) and li.startswith("0x") else int(li)
                key = (str(txh).lower(), lii)
                if key in seen:
                    raise RuntimeError("duplicate log identity inside shard")
                seen.add(key)
                topic0 = str(topics[0]).lower()
                event = TOPIC_TO_EVENT.get(topic0)
                if event is None:
                    raise RuntimeError("unexpected topic0")
                if event == "ReserveInitialized" and addr != CONFIGURATOR:
                    raise RuntimeError("ReserveInitialized wrong address")
                if event != "ReserveInitialized" and addr != POOL:
                    raise RuntimeError("Pool event wrong address")
                counts[event] += 1
                idx = USER_TOPIC_INDEX.get(event)
                if idx is not None:
                    if len(topics) <= idx:
                        raise RuntimeError(f"missing participant topic for {event}")
                    u = topic_address(str(topics[idx]))
                    users_by_event[event].add(u)
                    all_users.add(u)
                    if event == "LiquidationCall": liq_users.add(u)
                h.update(f"{bn}|{str(txh).lower()}|{lii}|{addr}|{topic0}\n".encode())
        if terminal != end:
            raise RuntimeError(f"terminal header {terminal} != shard end {end}")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:500]}"

    status = "SHARD_PASS" if failure is None and terminal == end else "SHARD_TECHNICAL_FAILURE"
    receipt = {
        "lab_id": LAB_ID, "phase": "SOURCE_CENSUS_SHARD_ONLY_OUTCOME_BLIND", "shard_id": shard_id,
        "from_block": start, "to_block": end, "terminal_header_block": terminal,
        "classification": status, "transport_stats": stats,
        "event_counts": dict(sorted(counts.items())),
        "participants_by_event": {k: sorted(v) for k, v in sorted(users_by_event.items())},
        "all_position_users": sorted(all_users), "liquidated_users": sorted(liq_users),
        "unique_log_ids": len(seen), "first_timestamp": first_ts, "last_timestamp": last_ts,
        "structural_sha256": h.hexdigest(), "failure": failure,
        "safety": {"log_data_requested": False, "economic_values_decoded": False,
                   "health_factor_computed": False, "overhang_computed": False,
                   "future_liquidation_outcome_computed": False, "market_prices_opened": False,
                   "returns_opened": False, "pnl_opened": False, "accessed_2025_or_2026": False,
                   "live_trading": False, "exchange_mutation": False},
    }
    out = Path("source_census_shards")
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"shard_{shard_id}.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"shard_id": shard_id, "classification": status, "unique_log_ids": len(seen),
                      "events_present": sorted(k for k,v in counts.items() if v),
                      "protected_period_firewall": "PASS", "economic_values_decoded": False,
                      "returns_opened": False, "pnl_opened": False}, sort_keys=True))
    return 0 if status == "SHARD_PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
