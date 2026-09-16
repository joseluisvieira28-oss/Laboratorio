#!/usr/bin/env python3
"""PMD-001 block-first source collector V0.3 — batched JSON transport.

Outcome-blind. Scientific population/window/matching are unchanged from V0.2.
V0.3 changes only getBlock transport/representation:
- exact same required slots;
- JSON-RPC batches (default 4 slots per HTTP request);
- getBlock encoding='json' with full transaction details;
- missing/error batch items remediated individually;
- same safe [T0-300s, floor(T0)) cutoff and evidence contracts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import (
    Rpc, bonding_curve_pda, load_manifest, parse_ts, sha256_json, tx_has_target,
)

WINDOW_SECONDS = 300
SIG_LIMIT = 1000
DEFAULT_BLOCK_BATCH = 4


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def find_matches(block: Any, signature: str) -> list[Any]:
    out = []
    if not isinstance(block, dict):
        return out
    for item in block.get("transactions") or []:
        tx = item.get("transaction") if isinstance(item, dict) else None
        sigs = tx.get("signatures") if isinstance(tx, dict) else None
        if isinstance(sigs, list) and signature in sigs:
            out.append(item)
    return out


def individual_json_block(rpc: Rpc, slot: int) -> Any:
    return rpc.call("getBlock", [int(slot), {
        "commitment": "finalized",
        "encoding": "json",
        "transactionDetails": "full",
        "rewards": False,
        "maxSupportedTransactionVersion": 0,
    }])


def get_blocks_batched(rpc: Rpc, slots: list[int], batch_size: int) -> dict[int, dict[str, Any]]:
    """Return slot -> {block, retrieved_at_utc, transport, remediated}."""
    if batch_size < 1:
        raise ValueError("batch_size must be >=1")
    out: dict[int, dict[str, Any]] = {}
    for i in range(0, len(slots), batch_size):
        chunk = slots[i:i + batch_size]
        reqs = []
        id_to_slot: dict[int, int] = {}
        for slot in chunk:
            rpc.counter += 1
            rid = rpc.counter
            id_to_slot[rid] = int(slot)
            reqs.append({
                "jsonrpc": "2.0",
                "id": rid,
                "method": "getBlock",
                "params": [int(slot), {
                    "commitment": "finalized",
                    "encoding": "json",
                    "transactionDetails": "full",
                    "rewards": False,
                    "maxSupportedTransactionVersion": 0,
                }],
            })

        response = None
        batch_error = None
        try:
            response = rpc._post(reqs)
            if not isinstance(response, list):
                batch_error = "batch_response_not_list"
        except Exception as exc:
            batch_error = f"{type(exc).__name__}: {exc}"

        seen_ids: set[int] = set()
        duplicate_ids: set[int] = set()
        unknown_ids: list[Any] = []
        if isinstance(response, list):
            for item in response:
                if not isinstance(item, dict):
                    continue
                rid = item.get("id")
                if rid not in id_to_slot:
                    unknown_ids.append(rid)
                    continue
                if rid in seen_ids:
                    duplicate_ids.add(rid)
                    continue
                seen_ids.add(rid)
                slot = id_to_slot[rid]
                if "error" in item:
                    out[slot] = {
                        "block": {"_rpc_error": item["error"]},
                        "retrieved_at_utc": utc_now(),
                        "transport": "batch_json",
                        "remediated": False,
                    }
                else:
                    block = item.get("result")
                    if not isinstance(block, dict):
                        block = {"_rpc_error": "null_or_nonobject_block"}
                    out[slot] = {
                        "block": block,
                        "retrieved_at_utc": utc_now(),
                        "transport": "batch_json",
                        "remediated": False,
                    }

        # Ambiguous/invalid batch envelopes fail those items into individual remediation.
        needs_retry: set[int] = set()
        if batch_error or unknown_ids or duplicate_ids:
            needs_retry.update(chunk)
        else:
            for rid, slot in id_to_slot.items():
                rec = out.get(slot)
                if rid not in seen_ids or not rec or (isinstance(rec.get("block"), dict) and rec["block"].get("_rpc_error")):
                    needs_retry.add(slot)

        for slot in sorted(needs_retry):
            retrieved_at = utc_now()
            try:
                block = individual_json_block(rpc, slot)
                if not isinstance(block, dict):
                    block = {"_rpc_error": "null_or_nonobject_block"}
            except Exception as exc:
                block = {"_rpc_error": f"{type(exc).__name__}: {exc}"}
            out[slot] = {
                "block": block,
                "retrieved_at_utc": retrieved_at,
                "transport": "individual_json_remediation",
                "remediated": True,
            }
    return out


def collect_one(rpc: Rpc, row: dict[str, Any], root: Path, store_full_blocks: bool, block_batch_size: int) -> dict[str, Any]:
    mint = row["mint"]
    t0 = parse_ts(row["t0"])
    lo = t0 - WINDOW_SECONDS
    safe_cutoff = float(math.floor(t0))
    pda = bonding_curve_pda(mint)

    all_sigs = []
    before = None
    pages = 0
    crossed = False
    exhausted = False
    null_time = False
    while True:
        page = rpc.get_signatures(pda, before=before)
        pages += 1
        if not page:
            exhausted = True
            break
        all_sigs.extend(page)
        times = [x.get("blockTime") for x in page]
        if any(x is None for x in times):
            null_time = True
        vals = [float(x) for x in times if x is not None]
        if vals and min(vals) < lo:
            crossed = True
            break
        if len(page) < SIG_LIMIT:
            exhausted = True
            break
        before = page[-1].get("signature")
        if not before:
            break
        if pages > 100:
            raise RuntimeError(f"pagination safety stop: {mint}")

    by_sig = {}
    conflicts = 0
    for x in all_sigs:
        sig = x.get("signature")
        if not sig:
            continue
        if sig in by_sig and by_sig[sig] != x:
            conflicts += 1
        else:
            by_sig[sig] = x

    safe = [
        x for x in by_sig.values()
        if x.get("blockTime") is not None and lo <= float(x["blockTime"]) < safe_cutoff
    ]
    same_second = [
        x for x in by_sig.values()
        if x.get("blockTime") is not None and float(x["blockTime"]) == safe_cutoff
    ]
    safe.sort(key=lambda x: (x.get("slot") or -1, x.get("signature") or ""))
    slots = sorted({int(x["slot"]) for x in safe if x.get("slot") is not None})

    fetched = get_blocks_batched(rpc, slots, block_batch_size) if slots else {}
    blocks: dict[int, Any] = {}
    block_shas: dict[int, str] = {}
    block_retrieved_at: dict[int, str] = {}
    block_errors = 0
    remediated_blocks = 0
    batch_blocks = 0

    block_ledger = root / "block_hash_ledger.jsonl"
    block_dir = root / "blocks" / mint
    if store_full_blocks:
        block_dir.mkdir(parents=True, exist_ok=True)
    with block_ledger.open("a", encoding="utf-8") as ledger:
        for slot in slots:
            rec = fetched.get(slot) or {
                "block": {"_rpc_error": "slot_missing_from_fetch_result"},
                "retrieved_at_utc": utc_now(),
                "transport": "missing",
                "remediated": False,
            }
            block = rec["block"]
            retrieved_at = rec["retrieved_at_utc"]
            transport = rec["transport"]
            remediated = bool(rec["remediated"])
            if remediated:
                remediated_blocks += 1
            if transport == "batch_json":
                batch_blocks += 1
            if not isinstance(block, dict) or block.get("_rpc_error"):
                block_errors += 1
            blocks[slot] = block
            block_sha = sha256_json(block)
            block_shas[slot] = block_sha
            block_retrieved_at[slot] = retrieved_at
            ledger.write(json.dumps({
                "lab": "PMD-001",
                "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
                "outcomes_opened": False,
                "source_name": rpc.source_name,
                "mint": mint,
                "slot": slot,
                "block_time": block.get("blockTime") if isinstance(block, dict) else None,
                "retrieved_at_utc": retrieved_at,
                "transport": transport,
                "remediated_individually": remediated,
                "canonical_block_sha256": block_sha,
                "block_error": block.get("_rpc_error") if isinstance(block, dict) else "nonobject_block",
                "full_block_persisted": bool(store_full_blocks),
            }, sort_keys=True, ensure_ascii=False) + "\n")
            ledger.flush()
            if store_full_blocks:
                evidence = {
                    "lab": "PMD-001",
                    "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
                    "outcomes_opened": False,
                    "source_name": rpc.source_name,
                    "mint": mint,
                    "slot": slot,
                    "block_time": block.get("blockTime") if isinstance(block, dict) else None,
                    "retrieved_at_utc": retrieved_at,
                    "transport": transport,
                    "block": block,
                    "canonical_sha256": block_sha,
                }
                with gzip.open(block_dir / f"slot_{slot}.json.gz", "wt", encoding="utf-8") as gf:
                    json.dump(evidence, gf, sort_keys=True, ensure_ascii=False)

    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{mint}.jsonl"
    missing = 0
    duplicate_matches = 0
    target = 0
    successful = 0
    successful_target = 0
    with raw_path.open("w", encoding="utf-8") as f:
        for meta in safe:
            sig = meta["signature"]
            slot = int(meta["slot"])
            matches = find_matches(blocks.get(slot), sig)
            if len(matches) == 0:
                missing += 1
                tx = None
            elif len(matches) > 1:
                duplicate_matches += 1
                tx = matches[0]
            else:
                tx = matches[0]
            is_success = meta.get("err") is None
            if is_success:
                successful += 1
            is_target = tx_has_target(tx, mint, pda)
            if is_target:
                target += 1
            if is_success and is_target:
                successful_target += 1
            f.write(json.dumps({
                "lab": "PMD-001",
                "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
                "outcomes_opened": False,
                "source_name": rpc.source_name,
                "mint": mint,
                "t0": row["t0"],
                "safe_cutoff_unix_second": safe_cutoff,
                "same_second_quarantined": True,
                "bonding_curve_pda": pda,
                "signature_meta": meta,
                "source_block_sha256": block_shas.get(slot),
                "source_block_retrieved_at_utc": block_retrieved_at.get(slot),
                "feature_eligible_by_time": True,
                "target_pump_mint_pda_present": is_target,
                "transaction": tx,
                "raw_response_sha256": sha256_json(tx),
            }, sort_keys=True, ensure_ascii=False) + "\n")

    complete = (
        conflicts == 0
        and not null_time
        and (crossed or exhausted)
        and block_errors == 0
        and missing == 0
        and duplicate_matches == 0
        and len(slots) > 0
        and len(safe) > 0
        and all(block_retrieved_at.get(s) for s in slots)
        and all(block_shas.get(s) for s in slots)
    )
    feature_source_eligible = bool(complete and successful_target > 0)
    return {
        "lab": "PMD-001",
        "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
        "outcomes_opened": False,
        "source_name": rpc.source_name,
        "mint": mint,
        "t0": row["t0"],
        "safe_cutoff_unix_second": safe_cutoff,
        "bonding_curve_pda": pda,
        "window_seconds": WINDOW_SECONDS,
        "signature_pages": pages,
        "signatures_unique_seen": len(by_sig),
        "safe_in_window_signatures": len(safe),
        "successful_safe_in_window_signatures": successful,
        "same_second_signatures_quarantined": len(same_second),
        "unique_safe_in_window_slots": len(slots),
        "blocks_requested": len(slots),
        "blocks_from_batch": batch_blocks,
        "blocks_individually_remediated": remediated_blocks,
        "block_errors": block_errors,
        "missing_signature_bodies": missing,
        "duplicate_signature_body_matches": duplicate_matches,
        "signature_conflicts": conflicts,
        "null_block_time_seen": null_time,
        "crossed_lower_bound": crossed,
        "history_exhausted": exhausted,
        "valid_target_pump_transactions": target,
        "successful_target_pump_transactions": successful_target,
        "source_complete": complete,
        "feature_source_eligible": feature_source_eligible,
        "timestamp_precision_amendment_applied": True,
        "retrieval_timestamp_evidence_complete": bool(slots) and all(block_retrieved_at.get(s) for s in slots),
        "full_blocks_persisted": bool(store_full_blocks),
        "block_transport": "json_rpc_batch_getBlock_json_with_individual_remediation",
        "block_batch_size": block_batch_size,
        "raw_file": str(raw_path),
        "raw_file_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-dir", default="pmd_block_first_v03")
    ap.add_argument("--rpc-url", default=None)
    ap.add_argument("--source-name", default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--store-full-blocks", action="store_true")
    ap.add_argument("--block-batch-size", type=int, default=DEFAULT_BLOCK_BATCH)
    args = ap.parse_args()

    if args.rpc_url:
        url = args.rpc_url
        source = args.source_name or "generic_rpc_probe_batch_json"
    else:
        key = os.environ.get("HELIUS_API_KEY")
        if not key:
            print("HELIUS_API_KEY required for authenticated archival route", file=sys.stderr)
            return 3
        url = f"https://mainnet.helius-rpc.com/?api-key={key}"
        source = "helius_archival_rpc_block_first_batch_json"

    rows = load_manifest(Path(args.manifest))
    if args.start < 0 or args.start >= len(rows):
        raise ValueError("--start out of range")
    rows = rows[args.start:]
    if args.limit > 0:
        rows = rows[:args.limit]

    root = Path(args.out_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = root / "source_rebuild_summary.jsonl"
    rpc = Rpc(url, source)
    with summary.open("w", encoding="utf-8") as sf:
        for row in rows:
            try:
                res = collect_one(rpc, row, root, args.store_full_blocks, args.block_batch_size)
            except Exception as exc:
                res = {
                    "lab": "PMD-001",
                    "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
                    "outcomes_opened": False,
                    "source_name": source,
                    "mint": row["mint"],
                    "t0": row["t0"],
                    "source_complete": False,
                    "feature_source_eligible": False,
                    "timestamp_precision_amendment_applied": True,
                    "retrieval_timestamp_evidence_complete": False,
                    "collector_error": f"{type(exc).__name__}: {exc}",
                }
            sf.write(json.dumps(res, sort_keys=True, ensure_ascii=False) + "\n")
            sf.flush()
            print(json.dumps({k: res.get(k) for k in (
                "mint", "source_complete", "feature_source_eligible",
                "safe_in_window_signatures", "same_second_signatures_quarantined",
                "unique_safe_in_window_slots", "blocks_from_batch",
                "blocks_individually_remediated", "successful_target_pump_transactions",
                "collector_error"
            ) if k in res}, sort_keys=True))

    print(json.dumps({
        "lab": "PMD-001",
        "stage": "BLOCK_FIRST_REBUILD_V03_BATCH_JSON",
        "outcomes_opened": False,
        "source_name": source,
        "rows_attempted": len(rows),
        "rpc_request_counter": rpc.counter,
        "summary_path": str(summary),
        "full_blocks_persisted": bool(args.store_full_blocks),
        "block_batch_size": args.block_batch_size,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
