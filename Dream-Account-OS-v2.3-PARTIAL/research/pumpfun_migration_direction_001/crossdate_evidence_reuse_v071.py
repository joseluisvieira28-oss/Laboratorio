#!/usr/bin/env python3
"""PMD-001 V0.7.1 cross-date evidence-reuse source gate.

Reuses immutable finalized full blocks from V0.6 run 35132853202, applies the
frozen V0.7 migrate+migrate_v2 boundary parser, queries finalized signature
metadata for the exact T*-300s window, and fetches only required slots absent
from the persisted artifact. No economic outcomes are opened.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, parse_ts, sha256_json, tx_has_target
from source_rebuild_block_first_v03 import get_blocks_batched
from chain_boundary_feasibility_v06 import paginate_window
from chain_boundary_semantics_v07 import is_actual_pool_creation_migration_v07, migration_variant_v07
from intrablock_boundary_probe_v05 import tx_signature

ART_RE = re.compile(r"PMD-001-chain-exact-v06-row-(\d+)$")
EXPECTED_ROWS = 20
EXPECTED_INDICES = set(range(EXPECTED_ROWS))
WINDOW_SECONDS = 300
SOURCE_RUN_ID = 35132853202


def artifact_index(path: Path) -> int | None:
    for p in [path, *path.parents]:
        m = ART_RE.match(p.name)
        if m:
            return int(m.group(1))
    return None


def load_json_gz(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def stored_sha(evidence: dict[str, Any]) -> str | None:
    return evidence.get("canonical_block_sha256") or evidence.get("canonical_sha256")


def one_summary(artifact_dir: Path) -> dict[str, Any]:
    p = artifact_dir / "source_rebuild_summary.jsonl"
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(rows) != 1:
        raise RuntimeError(f"{artifact_dir}: expected one source summary row, found {len(rows)}")
    return rows[0]


def scan_persisted_boundary(artifact_dir: Path, mint: str, pda: str, pool: str) -> tuple[dict[int, Path], list[dict], dict]:
    block_dir = artifact_dir / "blocks" / mint
    paths: dict[int, Path] = {}
    boundaries: list[dict] = []
    hash_mismatch = 0
    block_errors = 0
    malformed = 0
    for fp in sorted(block_dir.glob("slot_*.json.gz")):
        try:
            ev = load_json_gz(fp)
            slot = int(ev["slot"])
            block = ev.get("block")
            paths[slot] = fp
            if ev.get("outcomes_opened") is not False:
                malformed += 1
            if not isinstance(block, dict) or block.get("_rpc_error"):
                block_errors += 1
                continue
            actual = sha256_json(block)
            if stored_sha(ev) != actual:
                hash_mismatch += 1
                continue
            btime = block.get("blockTime")
            for tx_index, item in enumerate(block.get("transactions") or []):
                if not isinstance(item, dict):
                    continue
                if is_actual_pool_creation_migration_v07(item, mint, pda, pool):
                    boundaries.append({
                        "signature": tx_signature(item),
                        "slot": slot,
                        "block_time": int(btime),
                        "transaction_index": tx_index,
                        "variant": migration_variant_v07(item, mint, pda, pool),
                        "transaction_sha256": sha256_json(item),
                    })
        except Exception:
            malformed += 1
    unique = {(b["signature"], b["slot"], b["transaction_index"]) for b in boundaries}
    boundary = boundaries[0] if len(unique) == 1 else None
    stats = {
        "persisted_block_files": len(paths),
        "persisted_block_errors": block_errors,
        "persisted_hash_mismatch": hash_mismatch,
        "persisted_malformed": malformed,
        "qualifying_boundaries": len(unique),
    }
    return paths, ([boundary] if boundary else []), stats


def block_from_persisted(path: Path) -> tuple[dict | None, str | None]:
    ev = load_json_gz(path)
    block = ev.get("block")
    if not isinstance(block, dict) or block.get("_rpc_error"):
        return None, "stored_block_error"
    actual = sha256_json(block)
    if stored_sha(ev) != actual:
        return None, "stored_hash_mismatch"
    return block, None


def process_artifact(rpc: Rpc, artifact_dir: Path, out_root: Path, batch_size: int) -> dict[str, Any]:
    idx = artifact_index(artifact_dir)
    old = one_summary(artifact_dir)
    mint = old["mint"]
    pool = old["pool_address"]
    pda = old.get("bonding_curve_pda") or bonding_curve_pda(mint)
    t0 = old["t0"]

    persisted, boundary_list, scan = scan_persisted_boundary(artifact_dir, mint, pda, pool)
    boundary = boundary_list[0] if len(boundary_list) == 1 else None
    if not boundary:
        return {
            "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V071_REUSE_ROW","outcomes_opened":False,
            "crossdate_manifest_index":idx,"mint":mint,"t0":t0,"pool_address":pool,"bonding_curve_pda":pda,
            **scan,"source_complete":False,"feature_source_eligible":False,"error":"boundary_not_unique_from_frozen_v06_blocks"
        }

    boundary_key = (int(boundary["block_time"]), int(boundary["slot"]), int(boundary["transaction_index"]))
    feature_lo = float(boundary["block_time"]) - WINDOW_SECONDS
    try:
        sigs, paging = paginate_window(rpc, pda, feature_lo)
    except Exception as exc:
        return {
            "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V071_REUSE_ROW","outcomes_opened":False,
            "crossdate_manifest_index":idx,"mint":mint,"t0":t0,"pool_address":pool,"bonding_curve_pda":pda,
            **scan,"boundary":boundary,"source_complete":False,"feature_source_eligible":False,
            "error":f"signature_pagination:{type(exc).__name__}:{exc}"
        }

    window_meta = [
        x for x in sigs
        if x.get("blockTime") is not None and x.get("slot") is not None
        and feature_lo <= float(x["blockTime"]) <= float(boundary["block_time"])
    ]
    required_slots = sorted({int(x["slot"]) for x in window_meta})
    missing_slots = [s for s in required_slots if s not in persisted]
    gap_fetched = get_blocks_batched(rpc, missing_slots, batch_size) if missing_slots else {}

    gap_dir = out_root / "gap_blocks" / mint
    gap_dir.mkdir(parents=True, exist_ok=True)
    gap_ledger: list[dict] = []
    gap_errors = 0
    for slot in missing_slots:
        rec = gap_fetched.get(slot) or {}
        block = rec.get("block")
        if not isinstance(block, dict) or block.get("_rpc_error"):
            gap_errors += 1
            gap_ledger.append({"slot":slot,"error":(block or {}).get("_rpc_error") if isinstance(block,dict) else "missing_block"})
            continue
        bsha = sha256_json(block)
        ev = {
            "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V071_GAP_BLOCK","outcomes_opened":False,
            "source_run_reused":SOURCE_RUN_ID,"mint":mint,"slot":slot,
            "retrieved_at_utc":rec.get("retrieved_at_utc"),"transport":rec.get("transport"),
            "canonical_block_sha256":bsha,"block":block,
        }
        with gzip.open(gap_dir / f"slot_{slot}.json.gz", "wt", encoding="utf-8") as gf:
            json.dump(ev, gf, sort_keys=True, ensure_ascii=False)
        gap_ledger.append({"slot":slot,"canonical_block_sha256":bsha,"retrieved_at_utc":rec.get("retrieved_at_utc"),"transport":rec.get("transport"),"error":None})

    if gap_ledger:
        with (out_root / "gap_block_ledger.jsonl").open("a", encoding="utf-8") as f:
            for r in gap_ledger:
                f.write(json.dumps({"mint":mint, **r}, sort_keys=True) + "\n")

    paging_complete = bool(
        paging.get("signature_conflicts") == 0
        and not paging.get("null_block_time_seen")
        and (paging.get("crossed_lower_bound") or paging.get("history_exhausted"))
    )

    by_slot_meta: dict[int, list[dict]] = {}
    for m in window_meta:
        by_slot_meta.setdefault(int(m["slot"]), []).append(m)

    missing_positions = 0
    duplicate_positions = 0
    required_block_errors = 0
    pre_signatures = 0
    successful_pre = 0
    successful_target_pre = 0
    same_second_pre = 0
    same_second_after = 0
    reused_required_slots = 0

    for slot, metas in sorted(by_slot_meta.items()):
        block = None
        if slot in persisted:
            reused_required_slots += 1
            try:
                block, err = block_from_persisted(persisted[slot])
            except Exception:
                block, err = None, "stored_block_read_error"
            if err:
                required_block_errors += 1
                continue
        else:
            rec = gap_fetched.get(slot) or {}
            b = rec.get("block")
            if not isinstance(b, dict) or b.get("_rpc_error"):
                required_block_errors += 1
                continue
            block = b

        positions: dict[str, list[tuple[int, dict]]] = {}
        for tx_index, item in enumerate(block.get("transactions") or []):
            if not isinstance(item, dict):
                continue
            sig = tx_signature(item)
            if sig:
                positions.setdefault(sig, []).append((tx_index, item))

        for meta in metas:
            sig = str(meta.get("signature"))
            hits = positions.get(sig, [])
            if len(hits) == 0:
                missing_positions += 1
                continue
            if len(hits) > 1:
                duplicate_positions += 1
                continue
            tx_index, item = hits[0]
            key = (int(meta["blockTime"]), int(slot), int(tx_index))
            before = key < boundary_key
            if int(meta["blockTime"]) == int(boundary["block_time"]):
                if before:
                    same_second_pre += 1
                else:
                    same_second_after += 1
            if not before:
                continue
            pre_signatures += 1
            success = meta.get("err") is None and (item.get("meta") or {}).get("err") is None
            if success:
                successful_pre += 1
            if success and tx_has_target(item, mint, pda):
                successful_target_pre += 1

    source_complete = bool(
        scan["persisted_block_errors"] == 0
        and scan["persisted_hash_mismatch"] == 0
        and scan["persisted_malformed"] == 0
        and scan["qualifying_boundaries"] == 1
        and paging_complete
        and gap_errors == 0
        and required_block_errors == 0
        and missing_positions == 0
        and duplicate_positions == 0
    )
    eligible = bool(source_complete and successful_target_pre > 0)
    return {
        "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V071_REUSE_ROW","outcomes_opened":False,
        "source_run_reused":SOURCE_RUN_ID,"crossdate_manifest_index":idx,"mint":mint,"t0":t0,
        "pool_address":pool,"bonding_curve_pda":pda,"boundary_parser_version":"V07_MIGRATE_AND_MIGRATE_V2",
        "chain_boundary_signature":boundary["signature"],"chain_boundary_slot":boundary["slot"],
        "chain_boundary_block_time":boundary["block_time"],"chain_boundary_transaction_index":boundary["transaction_index"],
        "chain_boundary_variant":boundary["variant"],"corpus_minus_chain_boundary_seconds":parse_ts(t0)-float(boundary["block_time"]),
        "feature_window_lower_unix":feature_lo,"feature_window_seconds":WINDOW_SECONDS,
        **scan,"signature_pages":paging.get("signature_pages"),"signature_conflicts":paging.get("signature_conflicts"),
        "null_block_time_seen":paging.get("null_block_time_seen"),"paging_complete":paging_complete,
        "feature_window_signature_meta":len(window_meta),"required_feature_slots":len(required_slots),
        "reused_required_slots":reused_required_slots,"gap_slots_required":len(missing_slots),"gap_slots_errors":gap_errors,
        "required_block_errors":required_block_errors,"missing_signature_positions":missing_positions,
        "duplicate_signature_positions":duplicate_positions,"pre_boundary_signatures":pre_signatures,
        "successful_pre_boundary_signatures":successful_pre,"successful_target_pre_boundary_transactions":successful_target_pre,
        "same_boundary_second_pre":same_second_pre,"same_boundary_second_at_or_after":same_second_after,
        "source_complete":source_complete,"feature_source_eligible":eligible,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rpc-url", default="https://api.mainnet-beta.solana.com")
    ap.add_argument("--source-name", default="solana_public_rpc_chain_exact_crossdate_v071_reuse")
    ap.add_argument("--block-batch-size", type=int, default=4)
    args = ap.parse_args()

    root = Path(args.input_root)
    artifacts = sorted([p for p in root.iterdir() if p.is_dir() and ART_RE.match(p.name)], key=lambda p: artifact_index(p))
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rpc = Rpc(args.rpc_url, args.source_name)
    rows: list[dict] = []
    for p in artifacts:
        rec = process_artifact(rpc, p, out, args.block_batch_size)
        rows.append(rec)
        print(json.dumps({"index":rec.get("crossdate_manifest_index"),"mint":rec.get("mint"),"source_complete":rec.get("source_complete"),"eligible":rec.get("feature_source_eligible"),"gap_slots":rec.get("gap_slots_required"),"target_pre":rec.get("successful_target_pre_boundary_transactions")}, sort_keys=True), flush=True)

    indices = [r.get("crossdate_manifest_index") for r in rows]
    mints = [r.get("mint") for r in rows]
    dates = {str(r.get("t0"))[:10] for r in rows if r.get("t0")}
    complete = sum(bool(r.get("source_complete")) for r in rows)
    eligible = sum(bool(r.get("feature_source_eligible")) for r in rows)
    boundaries = sum(int(r.get("qualifying_boundaries") or 0) == 1 for r in rows)
    reconciliation = (
        len(rows) == EXPECTED_ROWS and set(x for x in indices if isinstance(x,int)) == EXPECTED_INDICES
        and len(set(mints)) == EXPECTED_ROWS and len(dates) == EXPECTED_ROWS
        and all(r.get("outcomes_opened") is False for r in rows)
    )
    if reconciliation and complete == EXPECTED_ROWS and eligible == EXPECTED_ROWS and boundaries == EXPECTED_ROWS:
        verdict = "CHAIN_EXACT_CROSSDATE_V071_REUSE_PASS"
    elif reconciliation:
        verdict = "CHAIN_EXACT_CROSSDATE_V071_REUSE_FAIL"
    else:
        verdict = "CHAIN_EXACT_CROSSDATE_V071_REUSE_TECHNICAL_INCOMPLETE"

    sorted_rows = sorted(rows, key=lambda r: int(r.get("crossdate_manifest_index", -1)))
    canon = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in sorted_rows)
    (out / "chain_exact_crossdate_v071_reuse_rows.jsonl").write_text(canon, encoding="utf-8")
    receipt = {
        "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V071_REUSE","economic_outcomes_opened":False,
        "source_run_reused":SOURCE_RUN_ID,"rows":len(rows),"unique_indices":len(set(indices)),"unique_mints":len(set(mints)),
        "distinct_dates":len(dates),"unique_chain_boundaries":boundaries,"source_complete_mints":complete,
        "feature_source_eligible_mints":eligible,"total_gap_slots_required":sum(int(r.get("gap_slots_required") or 0) for r in rows),
        "rpc_request_counter":rpc.counter,"rows_sha256":hashlib.sha256(canon.encode()).hexdigest(),"verdict":verdict,
    }
    (out / "chain_exact_crossdate_v071_reuse_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict == "CHAIN_EXACT_CROSSDATE_V071_REUSE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
