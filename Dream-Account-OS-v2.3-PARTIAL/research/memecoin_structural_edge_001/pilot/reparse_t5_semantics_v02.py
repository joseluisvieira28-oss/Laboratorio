#!/usr/bin/env python3
"""MSEL-001 semantic reparse V0.2 from already-captured raw RPC blocks.

READ-ONLY / LOCAL-ONLY / OUTCOMES LOCKED.

Purpose:
- correct historical Pump BUY/SELL account attribution (user is accounts[6]);
- separate associated_bonding_curve / associated_user / wallet signer;
- classify no-delivery dust buys and atomic buy+sell round-trips;
- classify non-Pump token changes as initial mint / burn-close / transfer candidate;
- regenerate T+1/T+3/T+5 activity features while preserving V0.1 holder state;
- explicitly BLOCK gross-turnover / final Organicity until per-instruction economic value is decoded.

No network calls. No prices. No graduation/outcomes. No trading.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import struct
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from collect_25_creates import (
    PUMP_PROGRAM,
    b58decode,
    get_all_keys,
    get_ix_data,
    outer_and_inner_instructions,
    resolve_ix_accounts,
    resolve_program_id,
    transaction_signature,
)

BUY_DISC = bytes([102, 6, 61, 18, 1, 218, 235, 234])
SELL_DISC = bytes([51, 230, 133, 164, 1, 127, 131, 173])
EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_DUST_BUYS = 11
EXPECTED_ATOMIC_ROUNDTRIP_TXS = 151
VERSION = "MSEL_T5_SEMANTIC_REPARSE_V02"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(path: pathlib.Path, obj: Any) -> str:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return sha256_bytes(path.read_bytes())


def parse_u64_pair(raw: bytes) -> Tuple[int, int]:
    if len(raw) < 24:
        raise RuntimeError("TRUNCATED_TRADE_INSTRUCTION")
    return struct.unpack_from("<QQ", raw, 8)


def token_amount_for_account(meta: Dict[str, Any], keys: Sequence[str], token_account: str, mint: str, phase: str) -> int:
    entries = meta.get("preTokenBalances") if phase == "pre" else meta.get("postTokenBalances")
    for e in entries or []:
        if e.get("mint") != mint:
            continue
        idx = e.get("accountIndex")
        if not isinstance(idx, int) or not (0 <= idx < len(keys)):
            continue
        if keys[idx] != token_account:
            continue
        ui = e.get("uiTokenAmount") or {}
        return int(ui.get("amount") or 0)
    return 0


def corrected_trade_rows(item: Dict[str, Any], target_mints: set[str]) -> List[Dict[str, Any]]:
    meta = item.get("meta") or {}
    keys = get_all_keys(item)
    if not keys:
        return []
    sig = transaction_signature(item)
    out: List[Dict[str, Any]] = []
    for scope, ix_idx, ix in outer_and_inner_instructions(item):
        if resolve_program_id(ix, keys) != PUMP_PROGRAM:
            continue
        data = get_ix_data(ix)
        if not data:
            continue
        try:
            raw = b58decode(data)
        except Exception:
            continue
        if raw.startswith(BUY_DISC):
            side = "buy"
        elif raw.startswith(SELL_DISC):
            side = "sell"
        else:
            continue
        accounts = resolve_ix_accounts(ix, keys)
        if len(accounts) <= 6:
            raise RuntimeError(f"TRADE_ACCOUNT_SHAPE_FAILURE sig={sig} scope={scope} ix={ix_idx} len={len(accounts)}")
        mint = accounts[2]
        if mint not in target_mints:
            continue
        amount, limit_value = parse_u64_pair(raw)
        associated_bonding_curve = accounts[4]
        associated_user = accounts[5]
        user = accounts[6]
        pre_amt = token_amount_for_account(meta, keys, associated_user, mint, "pre")
        post_amt = token_amount_for_account(meta, keys, associated_user, mint, "post")
        out.append({
            "signature": sig,
            "side": side,
            "scope": scope,
            "instruction_index": ix_idx,
            "mint": mint,
            "bonding_curve": accounts[3],
            "associated_bonding_curve": associated_bonding_curve,
            "associated_user": associated_user,
            "user": user,
            "amount_tokens_raw": amount,
            "max_sol_cost_raw" if side == "buy" else "min_sol_output_raw": limit_value,
            "user_token_pre_raw": pre_amt,
            "user_token_post_raw": post_amt,
            "user_token_delta_raw": post_amt - pre_amt,
            "instruction_data_sha256": sha256_bytes(raw),
        })
    return out


def classify_nonpump(logs: Sequence[str]) -> str:
    text = "\n".join(logs)
    if "Instruction: Create" in text and "Instruction: MintTo" in text:
        return "INITIAL_MINT"
    if "Instruction: Burn" in text or "Instruction: BurnChecked" in text:
        return "DUST_BURN_CLOSE" if "Instruction: CloseAccount" in text else "BURN"
    if "Instruction: Transfer" in text or "Instruction: TransferChecked" in text:
        return "DIRECT_TRANSFER_CANDIDATE"
    return "UNRESOLVED_NON_PUMP_TOKEN_CHANGE"


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    raw_dir = d / "raw_rpc"
    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    receipts_path = d / "rpc_receipts.json"
    v01_trades_path = d / "trade_events.jsonl"
    v01_changes_path = d / "token_balance_changes.jsonl"
    v01_snapshots_path = d / "snapshots_t1_t3_t5.jsonl"
    v01_manifest_path = d / "source_manifest.json"

    required = [cohort_path, receipts_path, v01_trades_path, v01_changes_path, v01_snapshots_path, v01_manifest_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")

    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    by_mint = {r["mint"]: r for r in cohort}
    target_mints = set(by_mint)
    v01_trades = load_jsonl(v01_trades_path)
    v01_changes = load_jsonl(v01_changes_path)
    v01_snapshots = load_jsonl(v01_snapshots_path)
    manifest = load_json(v01_manifest_path)

    for key, path in [
        ("trade_events_sha256", v01_trades_path),
        ("token_balance_changes_sha256", v01_changes_path),
        ("snapshots_sha256", v01_snapshots_path),
    ]:
        if manifest.get(key) != sha256_bytes(path.read_bytes()):
            raise RuntimeError(f"V01_HASH_MISMATCH {key}")

    target_trade_sigs = {r["signature"] for r in v01_trades}
    nonpump_rows = [r for r in v01_changes if not r.get("pump_trade_for_mint")]
    target_nonpump_sigs = {r["signature"] for r in nonpump_rows}
    wanted = target_trade_sigs | target_nonpump_sigs

    receipts = load_json(receipts_path)
    corrected: List[Dict[str, Any]] = []
    tx_semantics: Dict[str, Dict[str, Any]] = {}
    found: set[str] = set()

    slot_time_by_sig: Dict[str, Tuple[int, int, int]] = {}
    for r in v01_trades:
        slot_time_by_sig.setdefault(r["signature"], (int(r["slot"]), int(r["transaction_index"]), int(r["block_time"])))
    for r in nonpump_rows:
        slot_time_by_sig.setdefault(r["signature"], (int(r["slot"]), int(r["transaction_index"]), int(r["block_time"])))

    block_receipts = [r for r in receipts if r.get("method") == "getBlock" and r.get("raw_file")]
    if len(block_receipts) != int(manifest.get("blocks_scanned", -1)):
        raise RuntimeError(f"RAW_BLOCK_COUNT_MISMATCH {len(block_receipts)}/{manifest.get('blocks_scanned')}")

    for rec in sorted(block_receipts, key=lambda x: int(x["request_id"])):
        p = raw_dir / rec["raw_file"]
        if not p.exists():
            raise RuntimeError(f"MISSING_RAW_BLOCK {p.name}")
        blob = p.read_bytes()
        if sha256_bytes(blob) != rec["response_sha256"]:
            raise RuntimeError(f"RAW_BLOCK_HASH_MISMATCH {p.name}")
        payload = json.loads(blob)
        block = payload.get("result")
        if not isinstance(block, dict):
            continue
        for item in block.get("transactions") or []:
            if not isinstance(item, dict):
                continue
            sig = transaction_signature(item)
            if sig not in wanted:
                continue
            found.add(sig)
            if sig in target_trade_sigs:
                rows = corrected_trade_rows(item, target_mints)
                for row in rows:
                    slot, tx_index, block_time = slot_time_by_sig[sig]
                    row.update({"slot": slot, "transaction_index": tx_index, "block_time": block_time})
                    corrected.append(row)
            if sig in target_nonpump_sigs:
                logs = (item.get("meta") or {}).get("logMessages") or []
                tx_semantics[sig] = {
                    "signature": sig,
                    "semantic_class": classify_nonpump(logs),
                    "log_instruction_lines": [x for x in logs if "Instruction:" in x],
                }

    if found != wanted:
        miss = sorted(wanted - found)
        raise RuntimeError(f"RAW_SIGNATURE_RECONCILIATION_FAILURE missing={miss[:10]} count={len(miss)}")

    # Reconcile corrected instructions one-for-one with V0.1 by signature/mint/side/instruction index.
    def key(r: Dict[str, Any]) -> Tuple[Any, ...]:
        return (r["signature"], r["mint"], r["side"], r["scope"], int(r["instruction_index"]))
    old_keys = {key(r) for r in v01_trades}
    new_keys = {key(r) for r in corrected}
    if old_keys != new_keys or len(corrected) != len(v01_trades):
        raise RuntimeError(f"TRADE_RECONCILIATION_FAILURE old={len(v01_trades)} new={len(corrected)}")

    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in corrected:
        groups[(r["signature"], r["mint"])].append(r)

    atomic_keys: set[Tuple[str, str]] = set()
    for k, rows in groups.items():
        buys = [r for r in rows if r["side"] == "buy"]
        sells = [r for r in rows if r["side"] == "sell"]
        if buys and sells and sum(int(r["amount_tokens_raw"]) for r in buys) == sum(int(r["amount_tokens_raw"]) for r in sells):
            atomic_keys.add(k)

    dust_count = 0
    for r in corrected:
        k = (r["signature"], r["mint"])
        if k in atomic_keys:
            r["semantic_class"] = "ATOMIC_ROUNDTRIP_COMPONENT"
        elif (
            r["side"] == "buy"
            and int(r["user_token_delta_raw"]) <= 0
            and int(r["amount_tokens_raw"]) <= 1
            and int(r.get("max_sol_cost_raw", 0)) <= 5
        ):
            r["semantic_class"] = "NO_DELIVERY_DUST_BUY"
            dust_count += 1
        elif r["side"] == "buy":
            r["semantic_class"] = "ECONOMIC_BUY_CANDIDATE"
        else:
            r["semantic_class"] = "ECONOMIC_SELL_CANDIDATE"

    if dust_count != EXPECTED_DUST_BUYS:
        raise RuntimeError(f"DUST_BUY_RECONCILIATION_FAILURE {dust_count}/{EXPECTED_DUST_BUYS}")
    if len(atomic_keys) != EXPECTED_ATOMIC_ROUNDTRIP_TXS:
        raise RuntimeError(f"ATOMIC_ROUNDTRIP_RECONCILIATION_FAILURE {len(atomic_keys)}/{EXPECTED_ATOMIC_ROUNDTRIP_TXS}")

    nonpump_semantics: List[Dict[str, Any]] = []
    for r in nonpump_rows:
        s = dict(tx_semantics[r["signature"]])
        s.update({
            "slot": r["slot"],
            "transaction_index": r["transaction_index"],
            "block_time": r["block_time"],
            "mint": r["mint"],
            "token_account": r["token_account"],
            "owner": r["owner"],
            "delta_raw": r["delta_raw"],
        })
        nonpump_semantics.append(s)

    unresolved = [r for r in nonpump_semantics if r["semantic_class"] == "UNRESOLVED_NON_PUMP_TOKEN_CHANGE"]
    if unresolved:
        raise RuntimeError(f"NONPUMP_SEMANTIC_UNRESOLVED count={len(unresolved)}")

    corrected.sort(key=lambda r: (r["slot"], r["transaction_index"], r["signature"], str(r["scope"]), r["instruction_index"]))
    nonpump_semantics.sort(key=lambda r: (r["slot"], r["transaction_index"], r["signature"], r["mint"]))

    snapshots_v02: List[Dict[str, Any]] = []
    for old in v01_snapshots:
        mint = old["mint"]
        horizon = int(old["snapshot_horizon_seconds"])
        deadline = int(old["snapshot_deadline"])
        relevant = [r for r in corrected if r["mint"] == mint and int(r["block_time"]) <= deadline]
        buys = [r for r in relevant if r["side"] == "buy"]
        sells = [r for r in relevant if r["side"] == "sell"]
        econ_buys = [r for r in relevant if r["semantic_class"] == "ECONOMIC_BUY_CANDIDATE"]
        econ_sells = [r for r in relevant if r["semantic_class"] == "ECONOMIC_SELL_CANDIDATE"]
        atomic_tx = {(r["signature"], r["mint"]) for r in relevant if r["semantic_class"] == "ATOMIC_ROUNDTRIP_COMPONENT"}
        dust = [r for r in relevant if r["semantic_class"] == "NO_DELIVERY_DUST_BUY"]
        creator = by_mint[mint]["origin_creator"]
        direct_transfer_candidates = {
            r["signature"] for r in nonpump_semantics
            if r["mint"] == mint and int(r["block_time"]) <= deadline and r["semantic_class"] == "DIRECT_TRANSFER_CANDIDATE"
        }

        row = dict(old)
        row["semantic_reparse_version"] = VERSION
        row["v01_sum_abs_tx_net_curve_change_raw"] = row.pop("curve_lamport_gross_turnover_raw", None)
        row["gross_trade_turnover_lamports"] = None
        row["gross_trade_turnover_status"] = "BLOCKED_PENDING_PER_INSTRUCTION_TRADE_VALUE"
        row["unique_buyers_raw_wallet_corrected"] = len({r["user"] for r in buys})
        row["unique_sellers_raw_wallet_corrected"] = len({r["user"] for r in sells})
        row["unique_external_buyers_ex_creator_raw_corrected"] = len({r["user"] for r in buys if r["user"] != creator})
        row["no_delivery_dust_buy_count"] = len(dust)
        row["atomic_roundtrip_tx_count"] = len(atomic_tx)
        row["atomic_roundtrip_instruction_count"] = sum(1 for r in relevant if r["semantic_class"] == "ATOMIC_ROUNDTRIP_COMPONENT")
        row["economic_buy_instruction_count"] = len(econ_buys)
        row["economic_sell_instruction_count"] = len(econ_sells)
        row["unique_economic_buyers"] = len({r["user"] for r in econ_buys})
        row["unique_external_economic_buyers_ex_creator"] = len({r["user"] for r in econ_buys if r["user"] != creator})
        row["unique_economic_sellers"] = len({r["user"] for r in econ_sells})
        row["direct_transfer_candidate_tx_count"] = len(direct_transfer_candidates)
        row["direct_non_pump_token_change_tx_count_v01"] = row.pop("direct_non_pump_token_change_tx_count", None)
        row["economic_clustering_applied"] = False
        row["organicity_ratio_final_available"] = False
        row["outcomes_opened"] = False
        snapshots_v02.append(row)

    out_trades = d / "trade_events_semantic_v02.jsonl"
    out_nonpump = d / "non_pump_token_semantics_v02.jsonl"
    out_snapshots = d / "snapshots_t1_t3_t5_semantic_v02.jsonl"
    trades_sha = write_jsonl(out_trades, corrected)
    nonpump_sha = write_jsonl(out_nonpump, nonpump_semantics)
    snapshots_sha = write_jsonl(out_snapshots, snapshots_v02)

    class_counts: Dict[str, int] = defaultdict(int)
    for r in corrected:
        class_counts[r["semantic_class"]] += 1
    nonpump_counts: Dict[str, int] = defaultdict(int)
    for r in nonpump_semantics:
        nonpump_counts[r["semantic_class"]] += 1

    out_manifest_obj = {
        "lab": "MSEL-001",
        "version": VERSION,
        "status": "SEMANTIC_REPARSE_PASS_OUTCOMES_LOCKED",
        "cohort_sha256": EXPECTED_COHORT_SHA256,
        "v01_manifest_sha256": sha256_bytes(v01_manifest_path.read_bytes()),
        "v01_trade_events_sha256": sha256_bytes(v01_trades_path.read_bytes()),
        "v01_token_balance_changes_sha256": sha256_bytes(v01_changes_path.read_bytes()),
        "v01_snapshots_sha256": sha256_bytes(v01_snapshots_path.read_bytes()),
        "raw_blocks_verified": len(block_receipts),
        "corrected_trade_instruction_count": len(corrected),
        "trade_semantic_class_counts": dict(sorted(class_counts.items())),
        "atomic_roundtrip_tx_count": len(atomic_keys),
        "no_delivery_dust_buy_count": dust_count,
        "non_pump_semantic_counts": dict(sorted(nonpump_counts.items())),
        "trade_events_semantic_v02_sha256": trades_sha,
        "non_pump_token_semantics_v02_sha256": nonpump_sha,
        "snapshots_semantic_v02_sha256": snapshots_sha,
        "gross_trade_turnover_status": "BLOCKED_PENDING_PER_INSTRUCTION_TRADE_VALUE",
        "economic_clustering_applied": False,
        "organicity_ratio_final_available": False,
        "outcomes_opened": False,
    }
    out_manifest = d / "semantic_reparse_v02_manifest.json"
    manifest_sha = write_json(out_manifest, out_manifest_obj)

    print("PASS: semantic T+5 reparse V02 complete")
    print(f"raw blocks verified: {len(block_receipts)}")
    print(f"corrected trade instructions: {len(corrected)}")
    print(f"atomic round-trip txs: {len(atomic_keys)}")
    print(f"no-delivery dust buys: {dust_count}")
    print(f"non-Pump semantics: {dict(sorted(nonpump_counts.items()))}")
    print(f"manifest sha256: {manifest_sha}")
    print("GROSS TURNOVER REMAINS BLOCKED")
    print("ECONOMIC CLUSTERING NOT YET APPLIED")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
