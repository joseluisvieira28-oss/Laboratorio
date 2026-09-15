#!/usr/bin/env python3
"""MSEL-001 historical Pump TradeEvent extraction V0.3.

READ-ONLY / LOCAL-ONLY / OUTCOMES LOCKED.

Purpose:
- decode June-2025 Pump TradeEvent program-data records from the already captured raw blocks;
- reconcile them one-for-one with semantic reparse V0.2 trade instructions;
- recover per-trade SOL notional + protocol/creator fee fields;
- compute true event-level gross turnover and signed curve SOL flow at T+1/T+3/T+5;
- keep FINAL Organicity blocked until economic wallet clustering / funding attribution is applied.

No network calls. No future prices. No graduation data. No trading.

Historical schema authority:
  pump-fun/pump-public-docs commit e2b66e4fce2fc130955912315167dc41e56956ad
  TradeEvent discriminator: [189,219,127,211,78,230,97,238]
  TradeEvent encoded length: 225 bytes including discriminator.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import struct
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from collect_25_creates import transaction_signature

TRADE_EVENT_DISC = bytes([189, 219, 127, 211, 78, 230, 97, 238])
EXPECTED_EVENT_LEN = 225
EXPECTED_TRADE_EVENTS = 1081
EXPECTED_DUST_BUYS = 11
EXPECTED_ATOMIC_TXS = 151
EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
HISTORICAL_IDL_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"
VERSION = "MSEL_TRADE_EVENT_ECONOMIC_V03"
SNAPSHOTS = (60, 180, 300)

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    chars = ""
    while n:
        n, rem = divmod(n, 58)
        chars = B58_ALPHABET[rem] + chars
    pad = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * pad + (chars or "")


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


def read_u64(raw: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<Q", raw, off)[0], off + 8


def read_i64(raw: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<q", raw, off)[0], off + 8


def read_pubkey(raw: bytes, off: int) -> Tuple[str, int]:
    return b58encode(raw[off:off+32]), off + 32


def decode_trade_event(raw: bytes) -> Dict[str, Any]:
    if not raw.startswith(TRADE_EVENT_DISC):
        raise RuntimeError("NOT_TRADE_EVENT")
    if len(raw) != EXPECTED_EVENT_LEN:
        raise RuntimeError(f"TRADE_EVENT_LENGTH_MISMATCH {len(raw)}/{EXPECTED_EVENT_LEN}")
    off = 8
    mint, off = read_pubkey(raw, off)
    sol_amount, off = read_u64(raw, off)
    token_amount, off = read_u64(raw, off)
    is_buy = bool(raw[off]); off += 1
    user, off = read_pubkey(raw, off)
    timestamp, off = read_i64(raw, off)
    virtual_sol_reserves, off = read_u64(raw, off)
    virtual_token_reserves, off = read_u64(raw, off)
    real_sol_reserves, off = read_u64(raw, off)
    real_token_reserves, off = read_u64(raw, off)
    fee_recipient, off = read_pubkey(raw, off)
    fee_basis_points, off = read_u64(raw, off)
    fee, off = read_u64(raw, off)
    creator, off = read_pubkey(raw, off)
    creator_fee_basis_points, off = read_u64(raw, off)
    creator_fee, off = read_u64(raw, off)
    if off != EXPECTED_EVENT_LEN:
        raise RuntimeError(f"TRADE_EVENT_DECODE_OFFSET_FAILURE {off}/{EXPECTED_EVENT_LEN}")
    return {
        "mint": mint,
        "sol_amount_raw": sol_amount,
        "token_amount_raw": token_amount,
        "side": "buy" if is_buy else "sell",
        "user": user,
        "timestamp": timestamp,
        "virtual_sol_reserves_raw": virtual_sol_reserves,
        "virtual_token_reserves_raw": virtual_token_reserves,
        "real_sol_reserves_raw": real_sol_reserves,
        "real_token_reserves_raw": real_token_reserves,
        "fee_recipient": fee_recipient,
        "fee_basis_points": fee_basis_points,
        "protocol_fee_raw": fee,
        "creator": creator,
        "creator_fee_basis_points": creator_fee_basis_points,
        "creator_fee_raw": creator_fee,
        "event_data_sha256": sha256_bytes(raw),
    }


def program_data_trade_events(logs: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for log_index, line in enumerate(logs):
        if not isinstance(line, str) or not line.startswith("Program data: "):
            continue
        encoded = line.split("Program data: ", 1)[1].strip()
        try:
            raw = base64.b64decode(encoded, validate=True)
        except Exception:
            continue
        if not raw.startswith(TRADE_EVENT_DISC):
            continue
        event = decode_trade_event(raw)
        event["log_index"] = log_index
        out.append(event)
    return out


def semantic_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        row["mint"], row["side"], row["user"], int(row["amount_tokens_raw"])
    )


def event_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        row["mint"], row["side"], row["user"], int(row["token_amount_raw"])
    )


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    raw_dir = d / "raw_rpc"
    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    receipts_path = d / "rpc_receipts.json"
    semantic_path = d / "trade_events_semantic_v02.jsonl"

    required = [cohort_path, receipts_path, semantic_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")
    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    by_mint = {r["mint"]: r for r in cohort}
    target_mints = set(by_mint)
    semantic = load_jsonl(semantic_path)
    if len(semantic) != EXPECTED_TRADE_EVENTS:
        raise RuntimeError(f"SEMANTIC_TRADE_COUNT_MISMATCH {len(semantic)}/{EXPECTED_TRADE_EVENTS}")

    target_sigs = {r["signature"] for r in semantic}
    semantic_by_sig: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in semantic:
        semantic_by_sig[r["signature"]].append(r)

    atomic_tx_keys = {
        (r["signature"], r["mint"])
        for r in semantic
        if r.get("semantic_class") == "ATOMIC_ROUNDTRIP_COMPONENT"
    }
    if len(atomic_tx_keys) != EXPECTED_ATOMIC_TXS:
        raise RuntimeError(f"ATOMIC_TX_COUNT_MISMATCH {len(atomic_tx_keys)}/{EXPECTED_ATOMIC_TXS}")
    dust_count = sum(1 for r in semantic if r.get("semantic_class") == "NO_DELIVERY_DUST_BUY")
    if dust_count != EXPECTED_DUST_BUYS:
        raise RuntimeError(f"DUST_COUNT_MISMATCH {dust_count}/{EXPECTED_DUST_BUYS}")

    receipts = load_json(receipts_path)
    block_receipts = [r for r in receipts if r.get("method") == "getBlock" and r.get("raw_file")]
    events: List[Dict[str, Any]] = []
    found_sigs: set[str] = set()

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
        block_time = block.get("blockTime")
        for tx_index, item in enumerate(block.get("transactions") or []):
            if not isinstance(item, dict):
                continue
            sig = transaction_signature(item)
            if sig not in target_sigs:
                continue
            meta = item.get("meta") or {}
            if meta.get("err") is not None:
                raise RuntimeError(f"FAILED_TX_IN_SEMANTIC_SET {sig}")
            tx_events = program_data_trade_events(meta.get("logMessages") or [])
            if not tx_events:
                raise RuntimeError(f"NO_TRADE_EVENT_FOR_TRADE_TX {sig}")
            found_sigs.add(sig)
            for ev in tx_events:
                if ev["mint"] not in target_mints:
                    continue
                ev.update({
                    "signature": sig,
                    "slot": int(block.get("parentSlot", 0)) + 1 if block.get("parentSlot") is not None else None,
                    "transaction_index_from_block_array": tx_index,
                    "block_time": int(block_time) if block_time is not None else int(ev["timestamp"]),
                })
                events.append(ev)

    if found_sigs != target_sigs:
        miss = sorted(target_sigs - found_sigs)
        raise RuntimeError(f"TRADE_SIGNATURE_EVENT_SCAN_FAILURE missing={miss[:10]} count={len(miss)}")
    if len(events) != EXPECTED_TRADE_EVENTS:
        raise RuntimeError(f"TRADE_EVENT_COUNT_MISMATCH {len(events)}/{EXPECTED_TRADE_EVENTS}")

    # One-for-one semantic reconciliation within each transaction.
    reconciled: List[Dict[str, Any]] = []
    events_by_sig: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in events:
        events_by_sig[ev["signature"]].append(ev)

    for sig in sorted(target_sigs):
        sem_rows = list(semantic_by_sig[sig])
        ev_rows = sorted(events_by_sig[sig], key=lambda r: int(r["log_index"]))
        if len(sem_rows) != len(ev_rows):
            raise RuntimeError(f"TX_EVENT_INSTRUCTION_COUNT_MISMATCH sig={sig} sem={len(sem_rows)} event={len(ev_rows)}")
        unused = list(range(len(sem_rows)))
        for ev in ev_rows:
            k = event_key(ev)
            candidates = [i for i in unused if semantic_key(sem_rows[i]) == k]
            if not candidates:
                raise RuntimeError(f"EVENT_SEMANTIC_MATCH_FAILURE sig={sig} key={k}")
            classes = {sem_rows[i].get("semantic_class") for i in candidates}
            if len(classes) > 1:
                raise RuntimeError(f"EVENT_SEMANTIC_AMBIGUITY sig={sig} key={k} classes={sorted(classes)}")
            idx = candidates[0]
            unused.remove(idx)
            sem = sem_rows[idx]
            row = dict(ev)
            row.update({
                "semantic_class": sem.get("semantic_class"),
                "scope": sem.get("scope"),
                "instruction_index": sem.get("instruction_index"),
                "associated_bonding_curve": sem.get("associated_bonding_curve"),
                "associated_user": sem.get("associated_user"),
                "bonding_curve": sem.get("bonding_curve"),
                "user_token_delta_raw": sem.get("user_token_delta_raw"),
            })
            # Event timestamp should be contemporaneous with the transaction, not future information.
            if abs(int(row["timestamp"]) - int(sem["block_time"])) > 2:
                raise RuntimeError(f"EVENT_TIMESTAMP_MISMATCH sig={sig} event={row['timestamp']} block={sem['block_time']}")
            row["slot"] = int(sem["slot"])
            row["transaction_index"] = int(sem["transaction_index"])
            row["block_time"] = int(sem["block_time"])
            reconciled.append(row)
        if unused:
            raise RuntimeError(f"UNMATCHED_SEMANTIC_ROWS sig={sig} count={len(unused)}")

    reconciled.sort(key=lambda r: (r["slot"], r["transaction_index"], r["signature"], r["log_index"]))

    # Snapshot economics: event-level notional is the true gross trade measure.
    snapshots: List[Dict[str, Any]] = []
    for mint, launch in by_mint.items():
        launch_time = int(launch["block_time"])
        creator = launch["origin_creator"]
        for horizon in SNAPSHOTS:
            deadline = launch_time + horizon
            rows = [r for r in reconciled if r["mint"] == mint and int(r["block_time"]) <= deadline]
            economic = [r for r in rows if r["semantic_class"] in ("ECONOMIC_BUY_CANDIDATE", "ECONOMIC_SELL_CANDIDATE")]
            atomic = [r for r in rows if r["semantic_class"] == "ATOMIC_ROUNDTRIP_COMPONENT"]
            dust = [r for r in rows if r["semantic_class"] == "NO_DELIVERY_DUST_BUY"]

            def gross(rs: List[Dict[str, Any]]) -> int:
                return sum(int(r["sol_amount_raw"]) for r in rs)

            def signed_net(rs: List[Dict[str, Any]]) -> int:
                return sum(int(r["sol_amount_raw"]) if r["side"] == "buy" else -int(r["sol_amount_raw"]) for r in rs)

            def fees(rs: List[Dict[str, Any]]) -> Tuple[int, int]:
                return (
                    sum(int(r["protocol_fee_raw"]) for r in rs),
                    sum(int(r["creator_fee_raw"]) for r in rs),
                )

            protocol_fee_all, creator_fee_all = fees(rows)
            protocol_fee_econ, creator_fee_econ = fees(economic)
            econ_gross = gross(economic)
            econ_net = signed_net(economic)
            snapshots.append({
                "mint": mint,
                "cohort_rank": launch["cohort_rank"],
                "origin_creator": creator,
                "snapshot_horizon_seconds": horizon,
                "snapshot_deadline": deadline,
                "trade_event_count_all": len(rows),
                "gross_sol_notional_all_raw": gross(rows),
                "net_curve_sol_flow_all_raw": signed_net(rows),
                "protocol_fee_all_raw": protocol_fee_all,
                "creator_fee_all_raw": creator_fee_all,
                "atomic_roundtrip_component_count": len(atomic),
                "atomic_roundtrip_gross_sol_raw": gross(atomic),
                "no_delivery_dust_buy_count": len(dust),
                "no_delivery_dust_gross_sol_raw": gross(dust),
                "economic_trade_event_count_precluster": len(economic),
                "economic_gross_sol_notional_precluster_raw": econ_gross,
                "economic_net_curve_sol_flow_precluster_raw": econ_net,
                "economic_protocol_fee_precluster_raw": protocol_fee_econ,
                "economic_creator_fee_precluster_raw": creator_fee_econ,
                "economic_unique_buyers_precluster": len({r["user"] for r in economic if r["side"] == "buy"}),
                "economic_unique_sellers_precluster": len({r["user"] for r in economic if r["side"] == "sell"}),
                "economic_unique_buyers_ex_creator_precluster": len({r["user"] for r in economic if r["side"] == "buy" and r["user"] != creator}),
                "precluster_abs_net_to_gross": (abs(econ_net) / econ_gross) if econ_gross > 0 else None,
                "final_organicity_ratio_available": False,
                "economic_clustering_applied": False,
                "outcomes_opened": False,
            })

    if len(snapshots) != 25 * len(SNAPSHOTS):
        raise RuntimeError(f"SNAPSHOT_COUNT_FAILURE {len(snapshots)}/75")

    out_events = d / "trade_events_economic_v03.jsonl"
    out_snapshots = d / "snapshots_economic_v03.jsonl"
    events_sha = write_jsonl(out_events, reconciled)
    snapshots_sha = write_jsonl(out_snapshots, snapshots)

    manifest = {
        "artifact": "MSEL_TRADE_EVENT_ECONOMIC_V03",
        "version": VERSION,
        "lab": "MSEL-001",
        "historical_idl_commit": HISTORICAL_IDL_COMMIT,
        "historical_trade_event_discriminator": list(TRADE_EVENT_DISC),
        "historical_trade_event_encoded_length": EXPECTED_EVENT_LEN,
        "cohort_sha256": EXPECTED_COHORT_SHA256,
        "semantic_v02_sha256": sha256_bytes(semantic_path.read_bytes()),
        "rpc_receipts_sha256": sha256_bytes(receipts_path.read_bytes()),
        "raw_blocks_verified": len(block_receipts),
        "trade_events_reconciled": len(reconciled),
        "atomic_roundtrip_txs": len(atomic_tx_keys),
        "no_delivery_dust_buys": dust_count,
        "snapshots": len(snapshots),
        "trade_events_economic_v03_sha256": events_sha,
        "snapshots_economic_v03_sha256": snapshots_sha,
        "gross_turnover_status": "AVAILABLE_FROM_HISTORICAL_TRADE_EVENT_SOL_AMOUNT",
        "economic_clustering_applied": False,
        "final_organicity_ratio_available": False,
        "outcomes_opened": False,
    }
    manifest_path = d / "economic_manifest_v03.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: historical TradeEvent economic extraction V03 complete")
    print(f"raw blocks verified: {len(block_receipts)}")
    print(f"trade events reconciled: {len(reconciled)}")
    print(f"atomic round-trip txs: {len(atomic_tx_keys)}")
    print(f"no-delivery dust buys: {dust_count}")
    print(f"snapshots: {len(snapshots)}")
    print(f"manifest sha256: {manifest_sha}")
    print("TRUE GROSS TURNOVER NOW AVAILABLE")
    print("FINAL ORGANICITY REMAINS BLOCKED PENDING ECONOMIC CLUSTERING")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise SystemExit(2)
