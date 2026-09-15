#!/usr/bin/env python3
"""MSEL-001 T+1/T+3/T+5 forensic reconstruction via archival block scan.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

Inputs:
  data/msel001_pilot25_blockscan/cohort_25.jsonl

Outputs:
  data/msel001_t5_forensics/
    raw_rpc/                       exact getBlock JSON-RPC responses
    trade_events.jsonl             decoded Pump buy/sell instructions <= T+5
    token_balance_changes.jsonl     target-mint token-account pre/post changes <= T+5
    snapshots_t1_t3_t5.jsonl        raw point-in-time holder + flow snapshots
    source_manifest.json
    rpc_receipts.json

This script deliberately DOES NOT:
  - query market prices, DEX quotes, future highs/lows, graduation outcomes,
  - fetch current token metadata content,
  - infer wallet ownership from future activity,
  - cluster wallets,
  - trade or submit any transaction.

The objective is only to reconstruct what was objectively visible on-chain
through 300 seconds after each frozen CREATE.

Environment:
  HELIUS_API_KEY      required unless MSEL_RPC_URL is supplied
  MSEL_RPC_URL        optional archival Solana RPC URL
  MSEL_COHORT_PATH    optional cohort JSONL path
  MSEL_T5_OUT_DIR     optional output directory
  MSEL_RPS_DELAY      optional delay between RPC requests, default 0.12
  MSEL_MAX_BLOCKS     optional safety cap, default 2500
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import struct
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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
from collect_25_creates_blockscan_free import Rpc, get_confirmed_slots, fetch_block

EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_COHORT_SIZE = 25
BUY_DISC = bytes([102, 6, 61, 18, 1, 218, 235, 234])
SELL_DISC = bytes([51, 230, 133, 164, 1, 127, 131, 173])
SNAPSHOTS = (60, 180, 300)
COLLECTOR_VERSION = "MSEL_T5_FORENSIC_BLOCKSCAN_V01"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def write_json(path: pathlib.Path, obj: Any) -> str:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing HELIUS_API_KEY (or MSEL_RPC_URL).")
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


def load_cohort(path: pathlib.Path) -> List[Dict[str, Any]]:
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if digest != EXPECTED_COHORT_SHA256:
        raise RuntimeError(
            f"COHORT_HASH_MISMATCH expected={EXPECTED_COHORT_SHA256} actual={digest}"
        )
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != EXPECTED_COHORT_SIZE:
        raise RuntimeError(f"COHORT_SIZE_MISMATCH {len(rows)}/{EXPECTED_COHORT_SIZE}")
    if [r.get("cohort_rank") for r in rows] != list(range(1, EXPECTED_COHORT_SIZE + 1)):
        raise RuntimeError("COHORT_RANK_ORDER_FAILURE")
    if len({r.get("mint") for r in rows}) != EXPECTED_COHORT_SIZE:
        raise RuntimeError("COHORT_DUPLICATE_MINT")
    if len({r.get("signature") for r in rows}) != EXPECTED_COHORT_SIZE:
        raise RuntimeError("COHORT_DUPLICATE_SIGNATURE")
    return rows


def tx_after_launch(slot: int, tx_index: int, launch_slot: int, launch_tx_index: int) -> bool:
    return (slot, tx_index) >= (launch_slot, launch_tx_index)


def parse_u64_pair(raw: bytes) -> Tuple[int, int]:
    if len(raw) < 24:
        raise ValueError("truncated trade instruction data")
    return struct.unpack_from("<QQ", raw, 8)


def get_raw_amount(entry: Dict[str, Any]) -> Tuple[int, int]:
    ui = entry.get("uiTokenAmount") or {}
    amount = ui.get("amount")
    decimals = ui.get("decimals")
    if amount is None or decimals is None:
        raise ValueError("token balance missing amount/decimals")
    return int(amount), int(decimals)


def account_index(entry: Dict[str, Any]) -> int:
    idx = entry.get("accountIndex")
    if not isinstance(idx, int):
        raise ValueError("token balance accountIndex missing")
    return idx


def snapshot_owner_balances(token_accounts: Dict[str, Dict[str, Any]], mint: str) -> Dict[str, int]:
    out: Dict[str, int] = defaultdict(int)
    for state in token_accounts.values():
        if state["mint"] != mint:
            continue
        amount = int(state["amount"])
        owner = state.get("owner")
        if amount <= 0 or not owner:
            continue
        out[str(owner)] += amount
    return dict(out)


def concentration(values: List[int], n: int) -> Optional[float]:
    total = sum(values)
    if total <= 0:
        return None
    return sum(sorted(values, reverse=True)[:n]) / total


def iter_trade_instructions(
    item: Dict[str, Any],
    keys: Sequence[str],
    target_mints: set[str],
) -> Iterable[Dict[str, Any]]:
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
        if len(accounts) <= 5:
            raise RuntimeError(f"TRADE_ACCOUNT_SHAPE_FAILURE scope={scope} ix={ix_idx}")
        mint = accounts[2]
        if mint not in target_mints:
            continue
        amount, limit_value = parse_u64_pair(raw)
        yield {
            "side": side,
            "scope": scope,
            "instruction_index": ix_idx,
            "mint": mint,
            "bonding_curve": accounts[3],
            "associated_user": accounts[4],
            "user": accounts[5],
            "amount_tokens_raw": amount,
            "max_sol_cost_raw" if side == "buy" else "min_sol_output_raw": limit_value,
            "instruction_data_sha256": sha256_bytes(raw),
        }


def lamport_delta_for_pubkey(pubkey: str, keys: Sequence[str], meta: Dict[str, Any]) -> Optional[int]:
    try:
        idx = list(keys).index(pubkey)
    except ValueError:
        return None
    pre = meta.get("preBalances") or []
    post = meta.get("postBalances") or []
    if idx >= len(pre) or idx >= len(post):
        return None
    return int(post[idx]) - int(pre[idx])


def token_balance_entries(
    meta: Dict[str, Any],
    keys: Sequence[str],
    target_mints: set[str],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    def convert(entries: Any) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            mint = entry.get("mint")
            if mint not in target_mints:
                continue
            idx = account_index(entry)
            if not (0 <= idx < len(keys)):
                raise RuntimeError(f"TOKEN_ACCOUNT_INDEX_OOB idx={idx} keys={len(keys)}")
            token_account = keys[idx]
            amount, decimals = get_raw_amount(entry)
            out[token_account] = {
                "token_account": token_account,
                "mint": mint,
                "owner": entry.get("owner"),
                "amount": amount,
                "decimals": decimals,
            }
        return out

    return convert(meta.get("preTokenBalances")), convert(meta.get("postTokenBalances"))


def freeze_snapshot(
    cohort_row: Dict[str, Any],
    horizon: int,
    token_accounts: Dict[str, Dict[str, Any]],
    trades: List[Dict[str, Any]],
    balance_changes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    mint = cohort_row["mint"]
    origin_creator = cohort_row["origin_creator"]
    bonding_curve = cohort_row["bonding_curve"]
    owner_balances = snapshot_owner_balances(token_accounts, mint)

    bonding_curve_balance = int(owner_balances.get(bonding_curve, 0))
    external = {owner: amt for owner, amt in owner_balances.items() if owner != bonding_curve and amt > 0}
    ext_values = list(external.values())
    ext_total = sum(ext_values)
    creator_balance = int(external.get(origin_creator, 0))

    relevant_trades = [
        t for t in trades
        if t["mint"] == mint and int(t["block_time"]) <= int(cohort_row["block_time"]) + horizon
    ]
    buys = [t for t in relevant_trades if t["side"] == "buy"]
    sells = [t for t in relevant_trades if t["side"] == "sell"]

    curve_deltas = [
        int(t["curve_lamport_delta"])
        for t in relevant_trades
        if t.get("curve_lamport_delta") is not None
    ]
    gross_curve_turnover = sum(abs(x) for x in curve_deltas)
    net_curve_inflow = sum(curve_deltas)

    relevant_changes = [
        x for x in balance_changes
        if x["mint"] == mint and int(x["block_time"]) <= int(cohort_row["block_time"]) + horizon
    ]
    direct_change_txs = {
        (x["slot"], x["transaction_index"], x["signature"])
        for x in relevant_changes
        if not x["pump_trade_for_mint"]
    }

    return {
        "cohort_rank": cohort_row["cohort_rank"],
        "mint": mint,
        "launch_block_time": cohort_row["block_time"],
        "snapshot_horizon_seconds": horizon,
        "snapshot_deadline": int(cohort_row["block_time"]) + horizon,
        "raw_owner_count_including_curve": len(owner_balances),
        "raw_external_holder_count": len(external),
        "bonding_curve_token_balance_raw": bonding_curve_balance,
        "external_token_balance_raw": ext_total,
        "creator_external_balance_raw": creator_balance,
        "creator_share_external": (creator_balance / ext_total) if ext_total > 0 else None,
        "raw_external_top1_share": concentration(ext_values, 1),
        "raw_external_top3_share": concentration(ext_values, 3),
        "raw_external_top5_share": concentration(ext_values, 5),
        "raw_external_top10_share": concentration(ext_values, 10),
        "buy_instruction_count": len(buys),
        "sell_instruction_count": len(sells),
        "unique_buyers": len({t["user"] for t in buys}),
        "unique_sellers": len({t["user"] for t in sells}),
        "unique_external_buyers_ex_creator": len({t["user"] for t in buys if t["user"] != origin_creator}),
        "buy_token_amount_raw_sum": sum(int(t["amount_tokens_raw"]) for t in buys),
        "sell_token_amount_raw_sum": sum(int(t["amount_tokens_raw"]) for t in sells),
        "curve_lamport_gross_turnover_raw": gross_curve_turnover,
        "curve_lamport_net_inflow_raw": net_curve_inflow,
        "direct_non_pump_token_change_tx_count": len(direct_change_txs),
        "economic_clustering_applied": False,
        "organicity_ratio_final_available": False,
        "outcomes_opened": False,
    }


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_path = pathlib.Path(
        os.environ.get(
            "MSEL_COHORT_PATH",
            str(here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"),
        )
    ).resolve()
    out_dir = pathlib.Path(
        os.environ.get("MSEL_T5_OUT_DIR", str(here / "data" / "msel001_t5_forensics"))
    ).resolve()
    raw_dir = out_dir / "raw_rpc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    cohort = load_cohort(cohort_path)
    by_mint = {r["mint"]: r for r in cohort}
    target_mints = set(by_mint)
    cohort_signatures = {r["signature"] for r in cohort}
    min_slot = min(int(r["slot"]) for r in cohort)
    final_deadline = max(int(r["block_time"]) + 300 for r in cohort)

    delay = float(os.environ.get("MSEL_RPS_DELAY", "0.12"))
    max_blocks = int(os.environ.get("MSEL_MAX_BLOCKS", "2500"))
    if delay < 0 or max_blocks <= 0:
        raise RuntimeError("INVALID_SAFETY_CONFIGURATION")

    rpc = Rpc(rpc_url(), raw_dir, delay)

    token_accounts: Dict[str, Dict[str, Any]] = {}
    trades: List[Dict[str, Any]] = []
    balance_changes: List[Dict[str, Any]] = []
    create_signatures_seen: set[str] = set()
    decimals_by_mint: Dict[str, int] = {}
    snapshot_rows: List[Dict[str, Any]] = []
    frozen: set[Tuple[str, int]] = set()

    def freeze_due(before_block_time: int) -> None:
        for row in cohort:
            for horizon in SNAPSHOTS:
                key = (row["mint"], horizon)
                if key in frozen:
                    continue
                deadline = int(row["block_time"]) + horizon
                if deadline < before_block_time:
                    snapshot_rows.append(
                        freeze_snapshot(row, horizon, token_accounts, trades, balance_changes)
                    )
                    frozen.add(key)

    cursor = min_slot
    blocks_scanned = 0
    last_block_time: Optional[int] = None

    while blocks_scanned < max_blocks:
        slots = get_confirmed_slots(rpc, cursor, cursor + min(255, max_blocks - blocks_scanned))
        if not slots:
            cursor += 256
            continue

        for slot in slots:
            if blocks_scanned >= max_blocks:
                break
            block = fetch_block(rpc, slot)
            blocks_scanned += 1
            block_time = int(block["blockTime"])
            last_block_time = block_time

            freeze_due(block_time)
            if block_time > final_deadline and len(frozen) == EXPECTED_COHORT_SIZE * len(SNAPSHOTS):
                break

            for tx_index, item in enumerate(block["transactions"]):
                if not isinstance(item, dict):
                    raise RuntimeError(f"BAD_TRANSACTION_SHAPE slot={slot} tx={tx_index}")
                meta = item.get("meta")
                if not isinstance(meta, dict):
                    raise RuntimeError(f"MISSING_META slot={slot} tx={tx_index}")
                if meta.get("err") is not None:
                    continue

                sig = transaction_signature(item)
                if sig in cohort_signatures:
                    create_signatures_seen.add(sig)

                keys = get_all_keys(item)
                if not keys:
                    continue

                pump_trades = []
                for tr in iter_trade_instructions(item, keys, target_mints):
                    launch = by_mint[tr["mint"]]
                    if not tx_after_launch(slot, tx_index, int(launch["slot"]), int(launch["transaction_index"])):
                        continue
                    if block_time > int(launch["block_time"]) + 300:
                        continue
                    tr = dict(tr)
                    tr.update(
                        {
                            "slot": slot,
                            "transaction_index": tx_index,
                            "block_time": block_time,
                            "signature": sig,
                        }
                    )
                    tr["curve_lamport_delta"] = lamport_delta_for_pubkey(
                        tr["bonding_curve"], keys, meta
                    )
                    pump_trades.append(tr)
                    trades.append(tr)

                pre_tb, post_tb = token_balance_entries(meta, keys, target_mints)
                relevant_accounts = set(pre_tb) | set(post_tb)
                if relevant_accounts:
                    trade_mints_in_tx = {t["mint"] for t in pump_trades}
                    for token_account in sorted(relevant_accounts):
                        pre = pre_tb.get(token_account)
                        post = post_tb.get(token_account)
                        ref = post or pre
                        if ref is None:
                            continue
                        mint = ref["mint"]
                        launch = by_mint[mint]
                        if not tx_after_launch(slot, tx_index, int(launch["slot"]), int(launch["transaction_index"])):
                            continue
                        if block_time > int(launch["block_time"]) + 300:
                            continue

                        pre_amt = int(pre["amount"]) if pre else 0
                        post_amt = int(post["amount"]) if post else 0
                        decimals = int((post or pre)["decimals"])
                        known_dec = decimals_by_mint.setdefault(mint, decimals)
                        if known_dec != decimals:
                            raise RuntimeError(f"DECIMALS_CHANGED mint={mint}")

                        owner = (post or {}).get("owner") or (pre or {}).get("owner")
                        if owner is None:
                            previous = token_accounts.get(token_account)
                            owner = previous.get("owner") if previous else None
                        if owner is None:
                            raise RuntimeError(
                                f"UNRESOLVED_TOKEN_OWNER mint={mint} account={token_account} "
                                f"slot={slot} tx={tx_index}"
                            )

                        token_accounts[token_account] = {
                            "token_account": token_account,
                            "mint": mint,
                            "owner": owner,
                            "amount": post_amt,
                            "decimals": decimals,
                        }

                        if pre_amt != post_amt:
                            balance_changes.append(
                                {
                                    "slot": slot,
                                    "transaction_index": tx_index,
                                    "block_time": block_time,
                                    "signature": sig,
                                    "mint": mint,
                                    "token_account": token_account,
                                    "owner": owner,
                                    "pre_amount_raw": pre_amt,
                                    "post_amount_raw": post_amt,
                                    "delta_raw": post_amt - pre_amt,
                                    "pump_trade_for_mint": mint in trade_mints_in_tx,
                                }
                            )

            if block_time > final_deadline and len(frozen) == EXPECTED_COHORT_SIZE * len(SNAPSHOTS):
                break

        if last_block_time is not None and last_block_time > final_deadline:
            freeze_due(last_block_time + 1)
            if len(frozen) == EXPECTED_COHORT_SIZE * len(SNAPSHOTS):
                break
        cursor = slots[-1] + 1

    if create_signatures_seen != cohort_signatures:
        missing = sorted(cohort_signatures - create_signatures_seen)
        raise RuntimeError(f"CREATE_SIGNATURE_RECONCILIATION_FAILURE missing={missing[:5]}")
    if len(frozen) != EXPECTED_COHORT_SIZE * len(SNAPSHOTS):
        raise RuntimeError(
            f"SNAPSHOT_INCOMPLETE {len(frozen)}/{EXPECTED_COHORT_SIZE * len(SNAPSHOTS)}"
        )

    trades.sort(key=lambda x: (x["slot"], x["transaction_index"], x["signature"] or "", x["instruction_index"]))
    balance_changes.sort(
        key=lambda x: (x["slot"], x["transaction_index"], x["signature"] or "", x["token_account"])
    )
    snapshot_rows.sort(key=lambda x: (x["cohort_rank"], x["snapshot_horizon_seconds"]))

    trade_path = out_dir / "trade_events.jsonl"
    with trade_path.open("w", encoding="utf-8") as f:
        for row in trades:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    changes_path = out_dir / "token_balance_changes.jsonl"
    with changes_path.open("w", encoding="utf-8") as f:
        for row in balance_changes:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    snapshots_path = out_dir / "snapshots_t1_t3_t5.jsonl"
    with snapshots_path.open("w", encoding="utf-8") as f:
        for row in snapshot_rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    receipts_path = out_dir / "rpc_receipts.json"
    receipts_sha = write_json(receipts_path, rpc.receipts)

    manifest = {
        "lab": "MSEL-001",
        "collector": COLLECTOR_VERSION,
        "status": "T5_FEATURE_SOURCE_RECONSTRUCTION_OUTCOMES_LOCKED",
        "cohort_sha256": EXPECTED_COHORT_SHA256,
        "cohort_size": EXPECTED_COHORT_SIZE,
        "target_snapshot_seconds": list(SNAPSHOTS),
        "blocks_scanned": blocks_scanned,
        "rpc_request_count": len(rpc.receipts),
        "rpc_receipts_sha256": receipts_sha,
        "trade_events_count": len(trades),
        "token_balance_change_count": len(balance_changes),
        "snapshots_count": len(snapshot_rows),
        "trade_events_sha256": sha256_bytes(trade_path.read_bytes()),
        "token_balance_changes_sha256": sha256_bytes(changes_path.read_bytes()),
        "snapshots_sha256": sha256_bytes(snapshots_path.read_bytes()),
        "economic_clustering_applied": False,
        "organicity_ratio_final_available": False,
        "outcomes_opened": False,
    }
    manifest_path = out_dir / "source_manifest.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: T+1/T+3/T+5 on-chain forensic source reconstruction complete")
    print(f"blocks scanned: {blocks_scanned}")
    print(f"trade events: {len(trades)}")
    print(f"token balance changes: {len(balance_changes)}")
    print(f"snapshots: {len(snapshot_rows)}")
    print(f"manifest sha256: {manifest_sha}")
    print("ECONOMIC CLUSTERING NOT YET APPLIED")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
