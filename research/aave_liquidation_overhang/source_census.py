#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 source census.

Source-only / outcome-blind.
- Queries only Aave V3 Ethereum Pool / PoolConfigurator event structure.
- Requests no log.data field and decodes no economic amount/rate/price/balance.
- Enumerates only event IDs, block timestamps and indexed participant identities.
- Hard stops at the frozen 2024-12-31 boundary.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
MAX_TS = 1_735_689_599  # 2024-12-31 23:59:59 UTC

# Chunking is transport-only. The union is the exact frozen block envelope.
CHUNKS = [
    (16_490_000, 17_750_000),
    (17_750_001, 19_000_000),
    (19_000_001, 20_250_000),
    (20_250_001, 21_525_890),
]

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

TOPIC_TO_EVENT = {
    "0x" + keccak(sig.encode()).hex(): name for name, sig in EVENT_SIGNATURES.items()
}
POOL_TOPICS = [t for t, n in TOPIC_TO_EVENT.items() if n != "ReserveInitialized"]
CONFIG_TOPICS = [t for t, n in TOPIC_TO_EVENT.items() if n == "ReserveInitialized"]

# Indexed topic carrying the position owner / borrower identity.
USER_TOPIC_INDEX = {
    "Supply": 2,                # onBehalfOf
    "Withdraw": 2,              # user
    "Borrow": 2,                # onBehalfOf
    "Repay": 2,                 # user
    "ReserveUsedAsCollateralEnabled": 2,
    "ReserveUsedAsCollateralDisabled": 2,
    "LiquidationCall": 3,       # liquidated user
    "UserEModeSet": 1,
}


def topic_address(topic: str) -> str:
    if not isinstance(topic, str) or not topic.startswith("0x") or len(topic) != 66:
        raise ValueError("invalid indexed address topic")
    return "0x" + topic[-40:].lower()


def stream_chunk(start: int, end: int):
    body = {
        "type": "evm",
        "fromBlock": start,
        "toBlock": end,
        "fields": {
            "block": {"number": True, "timestamp": True},
            "log": {
                "address": True,
                "topics": True,
                "transactionHash": True,
                "logIndex": True,
            },
        },
        "logs": [
            {"address": [POOL], "topic0": POOL_TOPICS},
            {"address": [CONFIGURATOR], "topic0": CONFIG_TOPICS},
        ],
    }
    r = requests.post(
        PORTAL,
        json=body,
        timeout=(20, 240),
        stream=True,
        headers={"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/source-census-v0.1"},
    )
    r.raise_for_status()
    for raw in r.iter_lines(decode_unicode=True):
        if not raw:
            continue
        obj = json.loads(raw)
        if isinstance(obj, dict) and obj.get("error"):
            raise RuntimeError(f"portal error: {obj['error']}")
        yield obj


def main() -> int:
    counts: Counter[str] = Counter()
    users_by_event: dict[str, set[str]] = defaultdict(set)
    all_position_users: set[str] = set()
    liquidation_users: set[str] = set()
    seen_ids: set[tuple[str, int]] = set()
    structural_hasher = hashlib.sha256()
    chunks_receipt: list[dict[str, Any]] = []
    first_ts = None
    last_ts = None
    last_block = None
    failure = None

    try:
        for start, end in CHUNKS:
            chunk_logs = 0
            chunk_blocks_with_matches = 0
            chunk_first_ts = None
            chunk_last_ts = None
            for obj in stream_chunk(start, end):
                header = obj.get("header") or obj.get("block") or {}
                bn = header.get("number")
                ts = header.get("timestamp")
                logs = obj.get("logs") or []
                if bn is None or ts is None:
                    raise RuntimeError("missing block header number/timestamp")
                bn = int(bn)
                ts = int(ts)
                if not (start <= bn <= end):
                    raise RuntimeError("returned block outside requested chunk")
                if ts > MAX_TS:
                    raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
                if last_block is not None and bn < last_block:
                    raise RuntimeError("non-monotonic block order")
                last_block = bn
                if logs:
                    chunk_blocks_with_matches += 1
                    chunk_first_ts = ts if chunk_first_ts is None else min(chunk_first_ts, ts)
                    chunk_last_ts = ts if chunk_last_ts is None else max(chunk_last_ts, ts)
                    first_ts = ts if first_ts is None else min(first_ts, ts)
                    last_ts = ts if last_ts is None else max(last_ts, ts)
                for log in logs:
                    chunk_logs += 1
                    address = str(log.get("address", "")).lower()
                    topics = log.get("topics") or []
                    txh = log.get("transactionHash")
                    li = log.get("logIndex")
                    if address not in (POOL, CONFIGURATOR):
                        raise RuntimeError("unexpected contract address")
                    if not txh or li is None or not topics:
                        raise RuntimeError("log missing stable identity fields")
                    if isinstance(li, str):
                        li_int = int(li, 16) if li.startswith("0x") else int(li)
                    else:
                        li_int = int(li)
                    key = (str(txh).lower(), li_int)
                    if key in seen_ids:
                        raise RuntimeError("duplicate (transactionHash,logIndex)")
                    seen_ids.add(key)
                    topic0 = str(topics[0]).lower()
                    event = TOPIC_TO_EVENT.get(topic0)
                    if event is None:
                        raise RuntimeError("unexpected topic0")
                    if event == "ReserveInitialized" and address != CONFIGURATOR:
                        raise RuntimeError("ReserveInitialized from wrong address")
                    if event != "ReserveInitialized" and address != POOL:
                        raise RuntimeError("Pool event from wrong address")
                    counts[event] += 1

                    idx = USER_TOPIC_INDEX.get(event)
                    if idx is not None:
                        if len(topics) <= idx:
                            raise RuntimeError(f"missing participant topic for {event}")
                        user = topic_address(str(topics[idx]))
                        users_by_event[event].add(user)
                        all_position_users.add(user)
                        if event == "LiquidationCall":
                            liquidation_users.add(user)

                    canonical = f"{bn}|{str(txh).lower()}|{li_int}|{address}|{topic0}\n"
                    structural_hasher.update(canonical.encode())

            chunks_receipt.append({
                "from_block": start,
                "to_block": end,
                "matching_logs": chunk_logs,
                "blocks_with_matches": chunk_blocks_with_matches,
                "first_matching_timestamp": chunk_first_ts,
                "last_matching_timestamp": chunk_last_ts,
            })
    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:300]}"

    minimum_required = ["Borrow", "Repay", "LiquidationCall", "ReserveDataUpdated", "ReserveInitialized"]
    if failure:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    elif any(counts[x] <= 0 for x in minimum_required):
        classification = "INSUFFICIENT_SOURCE_COVERAGE"
    elif not all(c["matching_logs"] > 0 for c in chunks_receipt):
        classification = "INSUFFICIENT_SOURCE_COVERAGE"
    elif first_ts is None or last_ts is None or last_ts > MAX_TS:
        classification = "PROVENANCE_FAILURE"
    else:
        classification = "SOURCE_CENSUS_PASS"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "source": "SQD ethereum-mainnet Portal",
        "frozen_from_block": FROM_BLOCK,
        "frozen_to_block": TO_BLOCK,
        "hard_timestamp_ceiling": MAX_TS,
        "chunks": chunks_receipt,
        "event_counts": dict(sorted(counts.items())),
        "unique_participants_by_event": {k: len(v) for k, v in sorted(users_by_event.items())},
        "unique_position_users": len(all_position_users),
        "unique_liquidated_users": len(liquidation_users),
        "unique_log_ids": len(seen_ids),
        "first_matching_timestamp": first_ts,
        "last_matching_timestamp": last_ts,
        "structural_sha256": structural_hasher.hexdigest(),
        "failure": failure,
        "safety": {
            "log_data_requested": False,
            "economic_values_decoded": False,
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    outdir = Path("source_census_output")
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / "AAVE_LIQUIDATION_OVERHANG_001_SOURCE_CENSUS_RECEIPT_V0_1.json"
    outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    safe_summary = {
        "lab_id": LAB_ID,
        "classification": classification,
        "unique_log_ids": len(seen_ids),
        "unique_position_users": len(all_position_users),
        "unique_liquidated_users": len(liquidation_users),
        "events_present": sorted(k for k, v in counts.items() if v > 0),
        "protected_period_firewall": "PASS" if not (last_ts and last_ts > MAX_TS) else "FAIL",
        "economic_values_decoded": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    print(json.dumps(safe_summary, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
