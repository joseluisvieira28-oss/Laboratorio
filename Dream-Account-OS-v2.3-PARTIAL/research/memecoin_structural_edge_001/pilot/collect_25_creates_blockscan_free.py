#!/usr/bin/env python3
"""MSEL-001 frozen 25-launch collector via standard archival block RPCs.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

This is the free-tier fallback/authority route. It intentionally avoids the
Helius-only paid `getTransactionsForAddress` method and uses standard archival
Solana RPC reads: getFirstAvailableBlock, getSlot, getBlocksWithLimit,
getBlockTime, getBlocks, getBlock.

A free Helius key should be sufficient because Helius documents archival block
access on all plans. No transaction is submitted and no chain state is changed.

Environment:
  HELIUS_API_KEY      required unless MSEL_RPC_URL is supplied
  MSEL_RPC_URL        optional full archival RPC URL
  MSEL_OUT_DIR        optional output directory
  MSEL_MAX_BLOCKS     optional safety cap after boundary (default 5000)
  MSEL_RPS_DELAY      optional delay between requests (default 0.12 seconds)
  MSEL_BOUNDARY_PAD   optional local boundary window in slots (default 256)
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from collect_25_creates import (
    CREATE_DISC,
    FROZEN_START_ISO,
    FROZEN_START_UNIX,
    HISTORICAL_IDL_COMMIT,
    PUMP_PROGRAM,
    TARGET_CREATES,
    extract_creates,
)

COLLECTOR_VERSION = "FREE_TIER_ARCHIVAL_BLOCKSCAN_V01"
HISTORICAL_IDL_BLOB_SHA = "7f1fc8cfa2f54eead1330ae4f14acdc2b5adf3b4"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "Missing HELIUS_API_KEY (or MSEL_RPC_URL). A free Helius project key is sufficient for this route."
        )
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


class Rpc:
    def __init__(self, url: str, raw_dir: pathlib.Path, delay: float) -> None:
        self.url = url
        self.raw_dir = raw_dir
        self.delay = delay
        self.request_id = 0
        self.receipts: List[Dict[str, Any]] = []

    def call(self, method: str, params: list, *, retain_raw: bool = True) -> Any:
        self.request_id += 1
        payload = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        request_bytes = canonical_json_bytes(payload)
        req = urllib.request.Request(
            self.url,
            data=request_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "MSEL-001/0.2 blockscan research-only"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_bytes = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"RPC_HTTP_{exc.code} method={method}: {detail[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"RPC_NETWORK_FAILURE method={method}: {exc}") from exc

        try:
            parsed = json.loads(response_bytes)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"RPC_INVALID_JSON method={method}") from exc
        if parsed.get("error"):
            raise RuntimeError(f"RPC_ERROR method={method}: {parsed['error']}")

        receipt: Dict[str, Any] = {
            "request_id": self.request_id,
            "method": method,
            "request_sha256": sha256_bytes(request_bytes),
            "response_sha256": sha256_bytes(response_bytes),
            "response_bytes": len(response_bytes),
        }
        if retain_raw:
            name = f"{self.request_id:06d}_{method}_{receipt['response_sha256'][:16]}.json"
            (self.raw_dir / name).write_bytes(response_bytes)
            receipt["raw_file"] = name
        self.receipts.append(receipt)
        if self.delay:
            time.sleep(self.delay)
        return parsed.get("result")


def next_confirmed_slot(rpc: Rpc, start_slot: int) -> Optional[int]:
    result = rpc.call("getBlocksWithLimit", [start_slot, 1], retain_raw=False)
    if not isinstance(result, list):
        raise RuntimeError("BAD_GET_BLOCKS_WITH_LIMIT_RESPONSE")
    return int(result[0]) if result else None


def get_block_time(rpc: Rpc, slot: int) -> int:
    result = rpc.call("getBlockTime", [slot], retain_raw=False)
    if not isinstance(result, int):
        raise RuntimeError(f"MISSING_BLOCK_TIME slot={slot}")
    return result


def find_boundary_candidate(rpc: Rpc) -> int:
    """Binary-search a slot near the first confirmed block after the frozen time."""
    lo_raw = rpc.call("getFirstAvailableBlock", [], retain_raw=False)
    hi_raw = rpc.call("getSlot", [{"commitment": "finalized"}], retain_raw=False)
    if not isinstance(lo_raw, int) or not isinstance(hi_raw, int):
        raise RuntimeError("FAILED_TO_GET_PROVIDER_SLOT_BOUNDS")
    lo, hi = int(lo_raw), int(hi_raw)

    first = next_confirmed_slot(rpc, lo)
    if first is None or get_block_time(rpc, first) > FROZEN_START_UNIX:
        raise RuntimeError("PROVIDER_HISTORY_STARTS_AFTER_FROZEN_TIME")

    while lo < hi:
        mid = (lo + hi) // 2
        confirmed = next_confirmed_slot(rpc, mid)
        if confirmed is None or confirmed > hi:
            hi = mid
            continue
        t = get_block_time(rpc, confirmed)
        if t <= FROZEN_START_UNIX:
            lo = confirmed + 1
        else:
            hi = mid

    candidate = next_confirmed_slot(rpc, lo)
    if candidate is None:
        raise RuntimeError("BOUNDARY_SEARCH_NO_CANDIDATE")
    return candidate


def get_confirmed_slots(rpc: Rpc, start_slot: int, end_slot: int) -> List[int]:
    result = rpc.call("getBlocks", [start_slot, end_slot], retain_raw=False)
    if not isinstance(result, list):
        raise RuntimeError("BAD_GET_BLOCKS_RESPONSE")
    return [int(x) for x in result]


def refine_boundary(rpc: Rpc, candidate: int, pad: int) -> int:
    """Prove a local before/after boundary and reject non-monotonic block time."""
    slots = get_confirmed_slots(rpc, max(0, candidate - pad), candidate + pad)
    if not slots:
        raise RuntimeError("EMPTY_BOUNDARY_WINDOW")
    timed: List[Tuple[int, int]] = [(slot, get_block_time(rpc, slot)) for slot in slots]

    for (slot_a, time_a), (slot_b, time_b) in zip(timed, timed[1:]):
        if slot_b <= slot_a:
            raise RuntimeError("NON_INCREASING_SLOT_ORDER")
        if time_b < time_a:
            raise RuntimeError(
                f"NON_MONOTONIC_BLOCKTIME {slot_a}:{time_a} -> {slot_b}:{time_b}"
            )

    before = [(s, t) for s, t in timed if t <= FROZEN_START_UNIX]
    after = [(s, t) for s, t in timed if t > FROZEN_START_UNIX]
    if not before or not after:
        raise RuntimeError("BOUNDARY_PAD_INSUFFICIENT: increase MSEL_BOUNDARY_PAD")
    if before[-1][0] >= after[0][0]:
        raise RuntimeError("BOUNDARY_ORDER_INCONSISTENT")
    return after[0][0]


def fetch_block(rpc: Rpc, slot: int) -> Dict[str, Any]:
    result = rpc.call(
        "getBlock",
        [
            slot,
            {
                "encoding": "json",
                "transactionDetails": "full",
                "rewards": False,
                "maxSupportedTransactionVersion": 0,
                "commitment": "finalized",
            },
        ],
        retain_raw=True,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"GET_BLOCK_NULL_OR_BAD slot={slot}")
    if not isinstance(result.get("blockTime"), int):
        raise RuntimeError(f"GET_BLOCK_MISSING_TIME slot={slot}")
    if not isinstance(result.get("transactions"), list):
        raise RuntimeError(f"GET_BLOCK_MISSING_FULL_TRANSACTIONS slot={slot}")
    return result


def write_json(path: pathlib.Path, obj: Any) -> str:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def main() -> int:
    out_dir = pathlib.Path(
        os.environ.get("MSEL_OUT_DIR", "data/msel001_pilot25_blockscan")
    ).resolve()
    raw_dir = out_dir / "raw_rpc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    max_blocks = int(os.environ.get("MSEL_MAX_BLOCKS", "5000"))
    delay = float(os.environ.get("MSEL_RPS_DELAY", "0.12"))
    boundary_pad = int(os.environ.get("MSEL_BOUNDARY_PAD", "256"))
    if max_blocks <= 0 or delay < 0 or boundary_pad <= 0:
        raise RuntimeError("INVALID_SAFETY_CONFIGURATION")

    rpc = Rpc(rpc_url(), raw_dir, delay)
    candidate = find_boundary_candidate(rpc)
    boundary = refine_boundary(rpc, candidate, boundary_pad)

    records: List[Dict[str, Any]] = []
    blocks_scanned = 0
    cursor = boundary
    global_tx_order = 0

    while len(records) < TARGET_CREATES and blocks_scanned < max_blocks:
        end_slot = cursor + min(255, max_blocks - blocks_scanned)
        slots = get_confirmed_slots(rpc, cursor, end_slot)
        if not slots:
            cursor = end_slot + 1
            continue

        for slot in slots:
            if blocks_scanned >= max_blocks:
                break
            block = fetch_block(rpc, slot)
            blocks_scanned += 1
            block_time = int(block["blockTime"])
            if block_time <= FROZEN_START_UNIX:
                raise RuntimeError(f"BOUNDARY_REGRESSION slot={slot} blockTime={block_time}")

            for tx_index, tx_item in enumerate(block["transactions"]):
                global_tx_order += 1
                if not isinstance(tx_item, dict):
                    raise RuntimeError(f"BAD_TRANSACTION_SHAPE slot={slot} tx={tx_index}")
                meta = tx_item.get("meta")
                if not isinstance(meta, dict):
                    raise RuntimeError(f"MISSING_META slot={slot} tx={tx_index}")
                if meta.get("err") is not None:
                    continue

                enriched = dict(tx_item)
                enriched["slot"] = slot
                enriched["blockTime"] = block_time
                enriched["transactionIndex"] = tx_index
                creates = extract_creates(enriched, global_tx_order)

                # Existing decoder does not promise canonical execution ordering for
                # multiple CREATEs in one transaction. Such a case is rare but must
                # fail closed rather than guess the cohort order.
                if len(creates) > 1:
                    raise RuntimeError(
                        f"MULTI_CREATE_TX_UNSUPPORTED signature={creates[0].get('signature')} count={len(creates)}"
                    )
                records.extend(creates)
                if len(records) >= TARGET_CREATES:
                    break
            if len(records) >= TARGET_CREATES:
                break
        cursor = slots[-1] + 1

    if len(records) < TARGET_CREATES:
        raise RuntimeError(
            f"INSUFFICIENT_SOURCE_WINDOW decoded={len(records)}/{TARGET_CREATES} blocks_scanned={blocks_scanned}"
        )

    records = records[:TARGET_CREATES]
    records.sort(
        key=lambda r: (
            int(r["slot"]),
            int(r["transaction_index"]),
            r["signature"] or "",
            int(r["instruction_index"]),
        )
    )

    if len({r["mint"] for r in records}) != TARGET_CREATES:
        raise RuntimeError("DUPLICATE_MINT_IN_FROZEN_COHORT")
    if len({(r["signature"], r["instruction_scope"], r["instruction_index"]) for r in records}) != TARGET_CREATES:
        raise RuntimeError("DUPLICATE_CREATE_EVENT_IN_FROZEN_COHORT")

    cohort_path = out_dir / "cohort_25.jsonl"
    with cohort_path.open("w", encoding="utf-8") as handle:
        for rank, record in enumerate(records, 1):
            row = dict(record)
            row["cohort_rank"] = rank
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    cohort_sha = sha256_bytes(cohort_path.read_bytes())

    receipts_path = out_dir / "rpc_receipts.json"
    receipts_sha = write_json(receipts_path, rpc.receipts)

    manifest = {
        "lab": "MSEL-001",
        "collector": COLLECTOR_VERSION,
        "status": "FEATURE_SOURCE_ONLY_OUTCOMES_LOCKED",
        "selection_rule": "first 25 successful Pump CREATE instructions with blockTime > frozen timestamp in canonical block transaction order",
        "frozen_start_utc": FROZEN_START_ISO,
        "frozen_start_unix": FROZEN_START_UNIX,
        "program_id": PUMP_PROGRAM,
        "historical_idl_commit": HISTORICAL_IDL_COMMIT,
        "historical_idl_blob_sha": HISTORICAL_IDL_BLOB_SHA,
        "create_discriminator_hex": CREATE_DISC.hex(),
        "boundary_slot": boundary,
        "blocks_scanned": blocks_scanned,
        "rpc_request_count": len(rpc.receipts),
        "rpc_receipts_sha256": receipts_sha,
        "cohort_size": len(records),
        "cohort_sha256": cohort_sha,
        "outcomes_opened": False,
    }
    manifest_path = out_dir / "source_manifest.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: frozen cohort reconstructed via standard archival blockscan")
    print(f"boundary slot: {boundary}")
    print(f"blocks scanned: {blocks_scanned}")
    print(f"rpc requests: {len(rpc.receipts)}")
    print(f"cohort sha256: {cohort_sha}")
    print(f"manifest sha256: {manifest_sha}")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
