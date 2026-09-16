#!/usr/bin/env python3
"""PMD-001 V0.5 exact on-chain migration-boundary feasibility probe.

Outcome-blind. Identifies the exact Pump `migrate` instruction for frozen
cross-date candidates and classifies same-T0-second bonding-curve signatures
by finalized block (slot, transaction_index) relative to that boundary.

This script has no Source Gate or economic-outcome authority.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts, sha256_json
from source_rebuild_block_first_v03 import get_blocks_batched

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
MIGRATE_DISC = bytes([155,234,231,146,236,158,162,30])
BUY_DISC = bytes([102,6,61,18,1,218,235,234])
SELL_DISC = bytes([51,230,133,164,1,127,131,173])
SIG_LIMIT = 1000
PROBE_INDICES = (0, 1, 5, 10)
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_MAP = {c:i for i,c in enumerate(B58_ALPHABET)}


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        if ch not in B58_MAP:
            raise ValueError(f"invalid base58 character: {ch!r}")
        n = n * 58 + B58_MAP[ch]
    raw = b"" if n == 0 else n.to_bytes((n.bit_length() + 7) // 8, "big")
    leading = len(s) - len(s.lstrip("1"))
    return b"\x00" * leading + raw


def account_keys(item: dict[str, Any]) -> list[str]:
    tx = item.get("transaction") or {}
    msg = tx.get("message") or {}
    static = msg.get("accountKeys") or []
    keys: list[str] = []
    for k in static:
        if isinstance(k, str):
            keys.append(k)
        elif isinstance(k, dict):
            keys.append(str(k.get("pubkey")))
        else:
            keys.append(str(k))
    meta = item.get("meta") or {}
    loaded = meta.get("loadedAddresses") or {}
    keys.extend(str(x) for x in (loaded.get("writable") or []))
    keys.extend(str(x) for x in (loaded.get("readonly") or []))
    return keys


def outer_instructions(item: dict[str, Any]) -> list[dict[str, Any]]:
    tx = item.get("transaction") or {}
    msg = tx.get("message") or {}
    return [x for x in (msg.get("instructions") or []) if isinstance(x, dict)]


def resolve_program(ix: dict[str, Any], keys: list[str]) -> str | None:
    if isinstance(ix.get("programId"), str):
        return ix["programId"]
    pidx = ix.get("programIdIndex")
    if isinstance(pidx, int) and 0 <= pidx < len(keys):
        return keys[pidx]
    return None


def resolve_ix_accounts(ix: dict[str, Any], keys: list[str]) -> list[str]:
    out: list[str] = []
    for a in ix.get("accounts") or []:
        if isinstance(a, int) and 0 <= a < len(keys):
            out.append(keys[a])
        elif isinstance(a, str):
            out.append(a)
    return out


def ix_data(ix: dict[str, Any]) -> bytes:
    data = ix.get("data")
    if not isinstance(data, str):
        return b""
    try:
        return b58decode(data)
    except Exception:
        return b""


def pump_ix_kind(item: dict[str, Any], mint: str, pda: str, pool: str) -> tuple[bool, list[str]]:
    """Return (is_exact_migrate, detected Pump buy/sell instruction kinds)."""
    keys = account_keys(item)
    migrate = False
    trade_kinds: list[str] = []
    for ix in outer_instructions(item):
        if resolve_program(ix, keys) != PUMP_PROGRAM:
            continue
        data = ix_data(ix)
        accounts = set(resolve_ix_accounts(ix, keys))
        if data.startswith(MIGRATE_DISC) and mint in accounts and pda in accounts and pool in accounts:
            migrate = True
        if mint in accounts and pda in accounts:
            if data.startswith(BUY_DISC):
                trade_kinds.append("buy")
            elif data.startswith(SELL_DISC):
                trade_kinds.append("sell")
    return migrate, trade_kinds


def tx_signature(item: dict[str, Any]) -> str | None:
    tx = item.get("transaction") or {}
    sigs = tx.get("signatures") or []
    return str(sigs[0]) if sigs else None


def paginate_to_prior_second(rpc: Rpc, pda: str, target_second: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
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
        all_rows.extend(page)
        times = [x.get("blockTime") for x in page]
        if any(x is None for x in times):
            null_time = True
        vals = [int(x) for x in times if x is not None]
        if vals and min(vals) < target_second:
            crossed = True
            break
        if len(page) < SIG_LIMIT:
            exhausted = True
            break
        before = page[-1].get("signature")
        if not before:
            break
        if pages > 100:
            raise RuntimeError("pagination safety stop")
    by_sig: dict[str, dict[str, Any]] = {}
    conflicts = 0
    for r in all_rows:
        s = r.get("signature")
        if not s:
            continue
        if s in by_sig and by_sig[s] != r:
            conflicts += 1
        else:
            by_sig[s] = r
    return list(by_sig.values()), {
        "signature_pages": pages,
        "crossed_prior_second": crossed,
        "history_exhausted": exhausted,
        "null_block_time_seen": null_time,
        "signature_conflicts": conflicts,
    }


def process_row(rpc: Rpc, row: dict[str, Any], probe_index: int, root: Path, batch_size: int) -> dict[str, Any]:
    mint = row["mint"]
    pool = row.get("pool_address")
    if not pool:
        raise RuntimeError(f"missing canonical pool for {mint}")
    pda = bonding_curve_pda(mint)
    t0 = parse_ts(row["t0"])
    target_second = int(math.floor(t0))

    sigs, paging = paginate_to_prior_second(rpc, pda, target_second)
    same = [x for x in sigs if x.get("blockTime") is not None and int(x["blockTime"]) == target_second]
    same.sort(key=lambda x: (int(x.get("slot") or -1), str(x.get("signature") or "")))
    slots = sorted({int(x["slot"]) for x in same if x.get("slot") is not None})
    fetched = get_blocks_batched(rpc, slots, batch_size) if slots else {}

    candidate_boundaries: list[dict[str, Any]] = []
    sig_positions: dict[str, dict[str, Any]] = {}
    block_errors = 0
    block_evidence: list[dict[str, Any]] = []
    evidence_dir = root / "blocks" / f"idx_{probe_index}_{mint}"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    for slot in slots:
        rec = fetched.get(slot) or {}
        block = rec.get("block")
        if not isinstance(block, dict) or block.get("_rpc_error"):
            block_errors += 1
            continue
        btime = block.get("blockTime")
        block_sha = sha256_json(block)
        block_evidence.append({
            "slot": slot,
            "block_time": btime,
            "retrieved_at_utc": rec.get("retrieved_at_utc"),
            "canonical_block_sha256": block_sha,
            "transport": rec.get("transport"),
            "remediated": bool(rec.get("remediated")),
        })
        with gzip.open(evidence_dir / f"slot_{slot}.json.gz", "wt", encoding="utf-8") as gf:
            json.dump({
                "lab":"PMD-001","stage":"INTRABLOCK_BOUNDARY_PROBE_V05","outcomes_opened":False,
                "probe_index":probe_index,"mint":mint,"slot":slot,
                "retrieved_at_utc":rec.get("retrieved_at_utc"),
                "canonical_block_sha256":block_sha,"block":block,
            }, gf, sort_keys=True, ensure_ascii=False)

        for tx_index, item in enumerate(block.get("transactions") or []):
            if not isinstance(item, dict):
                continue
            sig = tx_signature(item)
            if sig:
                sig_positions[sig] = {
                    "slot": slot,
                    "transaction_index": tx_index,
                    "block_time": btime,
                    "success": (item.get("meta") or {}).get("err") is None,
                    "transaction_sha256": sha256_json(item),
                    "item": item,
                }
            exact_migrate, _kinds = pump_ix_kind(item, mint, pda, pool)
            if exact_migrate and (item.get("meta") or {}).get("err") is None:
                candidate_boundaries.append({
                    "signature": sig,
                    "slot": slot,
                    "transaction_index": tx_index,
                    "block_time": btime,
                    "transaction_sha256": sha256_json(item),
                })

    unique_boundary_keys = {(x["slot"], x["transaction_index"], x["signature"]) for x in candidate_boundaries}
    boundary = candidate_boundaries[0] if len(unique_boundary_keys) == 1 else None
    boundary_key = (int(boundary["slot"]), int(boundary["transaction_index"])) if boundary else None
    boundary_aligns = bool(boundary and int(boundary.get("block_time")) == target_second)

    before_rows: list[dict[str, Any]] = []
    after_rows: list[dict[str, Any]] = []
    missing_positions: list[str] = []
    successful_pump_trades_before = 0
    trade_kinds_before: dict[str, int] = {"buy":0,"sell":0}

    for meta in same:
        sig = str(meta.get("signature"))
        pos = sig_positions.get(sig)
        if not pos:
            missing_positions.append(sig)
            continue
        key = (int(pos["slot"]), int(pos["transaction_index"]))
        rec = {
            "signature": sig,
            "slot": pos["slot"],
            "transaction_index": pos["transaction_index"],
            "signature_meta_success": meta.get("err") is None,
            "transaction_success": pos["success"],
            "transaction_sha256": pos["transaction_sha256"],
        }
        if boundary_key is not None and key < boundary_key:
            before_rows.append(rec)
            _mig, kinds = pump_ix_kind(pos["item"], mint, pda, pool)
            if pos["success"] and kinds:
                successful_pump_trades_before += 1
                for k in set(kinds):
                    trade_kinds_before[k] = trade_kinds_before.get(k,0) + 1
        else:
            after_rows.append(rec)

    history_resolved = bool(
        paging["signature_conflicts"] == 0
        and not paging["null_block_time_seen"]
        and (paging["crossed_prior_second"] or paging["history_exhausted"])
    )
    positions_complete = len(missing_positions) == 0 and len(sig_positions) >= len(same)
    boundary_unique = len(unique_boundary_keys) == 1
    feasible = bool(
        boundary_unique and boundary_aligns and history_resolved and block_errors == 0
        and positions_complete and len(same) > 0
    )

    raw = {
        "lab":"PMD-001","stage":"INTRABLOCK_BOUNDARY_PROBE_V05","outcomes_opened":False,
        "probe_index":probe_index,"mint":mint,"pool_address":pool,"bonding_curve_pda":pda,
        "corpus_t0":row["t0"],"target_integer_second":target_second,
        "paging":paging,"same_second_signature_meta":same,
        "boundary_candidates":candidate_boundaries,"block_evidence":block_evidence,
        "same_second_before_boundary":before_rows,"same_second_at_or_after_boundary":after_rows,
        "missing_signature_positions":missing_positions,
    }
    raw_path = root / f"probe_idx_{probe_index}_{mint}.json"
    raw_path.write_text(json.dumps(raw,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    return {
        "lab":"PMD-001","stage":"INTRABLOCK_BOUNDARY_PROBE_V05","outcomes_opened":False,
        "probe_index":probe_index,"mint":mint,"pool_address":pool,"bonding_curve_pda":pda,
        "corpus_t0":row["t0"],"target_integer_second":target_second,
        "same_second_signatures":len(same),"unique_same_second_slots":len(slots),
        "boundary_candidates":len(unique_boundary_keys),
        "boundary_found_unique":boundary_unique,
        "boundary_signature":boundary.get("signature") if boundary else None,
        "boundary_slot":boundary.get("slot") if boundary else None,
        "boundary_transaction_index":boundary.get("transaction_index") if boundary else None,
        "boundary_block_time":boundary.get("block_time") if boundary else None,
        "boundary_aligns_corpus_t0_second":boundary_aligns,
        "same_second_before_boundary":len(before_rows),
        "same_second_at_or_after_boundary":len(after_rows),
        "successful_pump_buy_sell_transactions_before_boundary":successful_pump_trades_before,
        "pump_trade_kinds_before_boundary":trade_kinds_before,
        "missing_signature_positions":len(missing_positions),
        "block_errors":block_errors,"history_resolved":history_resolved,
        "same_second_positions_complete":positions_complete,
        "method_feasible_for_row":feasible,
        "raw_evidence_file":str(raw_path),
        "raw_evidence_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--crossdate-manifest",required=True)
    ap.add_argument("--out-dir",default="pmd_intrablock_boundary_probe_v05")
    ap.add_argument("--rpc-url",default="https://api.mainnet-beta.solana.com")
    ap.add_argument("--source-name",default="solana_public_rpc_intrablock_boundary_v05")
    ap.add_argument("--block-batch-size",type=int,default=4)
    args=ap.parse_args()

    rows=load_manifest(Path(args.crossdate_manifest))
    if len(rows)!=20:
        raise RuntimeError(f"expected frozen cross-date 20 rows, found {len(rows)}")

    # Assert the exact frozen probe mints by index so later manifest drift fails closed.
    expected={
        0:"9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump",
        1:"QHhbroZxDShtSXm9X2RqjpQP9FvpxbSTUWktPMopump",
        5:"7N3RPJC7ZxXyEnVyx8i83dcKb9QjMjV34cH2VKjypump",
        10:"71HtXHfexjKgem92Y5sPLPb6qkmtqWmPUzdKAcU9pump",
    }
    for i,m in expected.items():
        if rows[i]["mint"]!=m:
            raise RuntimeError(f"frozen probe manifest mismatch at {i}: {rows[i]['mint']} != {m}")

    root=Path(args.out_dir); root.mkdir(parents=True,exist_ok=True)
    rpc=Rpc(args.rpc_url,args.source_name)
    summaries=[]
    for i in PROBE_INDICES:
        r=process_row(rpc,rows[i],i,root,args.block_batch_size)
        summaries.append(r)
        print(json.dumps(r,sort_keys=True,ensure_ascii=False),flush=True)

    summary_path=root/"intrablock_boundary_probe_v05_summary.jsonl"
    summary_path.write_text("".join(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n" for r in summaries),encoding="utf-8")
    feasible=all(r["method_feasible_for_row"] for r in summaries)
    receipt={
        "lab":"PMD-001","stage":"INTRABLOCK_BOUNDARY_FEASIBILITY_V05","economic_outcomes_opened":False,
        "probe_indices":list(PROBE_INDICES),"probe_rows":len(summaries),
        "rows_method_feasible":sum(bool(r["method_feasible_for_row"]) for r in summaries),
        "failed_precision_rows_recovered_with_preboundary_same_second_trades":sum(
            1 for r in summaries if r["probe_index"] in (1,5) and r["method_feasible_for_row"] and r["successful_pump_buy_sell_transactions_before_boundary"]>0
        ),
        "summary_sha256":hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "verdict":"INTRABLOCK_BOUNDARY_METHOD_FEASIBLE" if feasible else "INTRABLOCK_BOUNDARY_METHOD_UNRESOLVED",
        "full_population_v05_authorized":False,
        "outcomes_opened":False,
    }
    (root/"intrablock_boundary_probe_v05_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if feasible else 2

if __name__=="__main__":
    raise SystemExit(main())
