#!/usr/bin/env python3
"""MSEL-001 Pilot25 economic evaluation V14.

LOCAL-ONLY / RESEARCH-ONLY / FAIL-CLOSED.

Authorized by V13F binding. This script opens the sealed V13 future transaction
bytes and computes the frozen Pilot25 outcome diagnostics under V12A/V12.

Important fail-closed limitation for this first evaluator implementation:
- Pump bonding-curve future SELLs are decoded exactly from historical TradeEvent.
- If ANY Pump migrate instruction or historical PumpSwap event appears in the
  sealed 24h source, the script STOPS BEFORE LABELS. Migration continuity is
  frozen by V12 and must be decoded canonically rather than ignored.

Pilot25 cannot by itself claim SURVIVES_MVE.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import struct
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

EXPECTED_BINDING_SHA = "0a02806c2795f4e308fcd88aba0dcfb69c9c6e064dcc6fa1d5b976e872d5f7ec"
EXPECTED_V03_EVENTS_SHA = "973798aa4b8a861aff60c7e73075c12e2bdf803fe56515d73f8ed76a9cda3c97"
EXPECTED_V11_RISK_SHA = "5857267a7d0203fa0e8e70eeafc34017d225a84a7809c97accce8bbb76f7fb8e"
EXPECTED_V13_MANIFEST_SHA = "f2101ff97eb995f8f1df66ed9d11dd46b4bc24d558e67139b74df53a2a00cdde"
EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_FUTURE_TX = 904

DECISION_SECONDS = 300
WINDOWS = (900, 3600, 21600, 86400)
ENTRY_GROSS_LAMPORTS = 10_000_000
SELL_FLOOR_LAMPORTS = 10_000_000
CATASTROPHE_THRESHOLD = -0.80
WINNER_THRESHOLD = 1.00
STRESS_HAIRCUT = 0.03

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
DEFAULT_PUBKEY = "11111111111111111111111111111111"

TRADE_EVENT_DISC = bytes([189, 219, 127, 211, 78, 230, 97, 238])
TRADE_EVENT_LEN = 225
PUMP_MIGRATE_DISC = bytes([155, 234, 231, 146, 236, 158, 162, 30])
PUMPSWAP_BUY_EVENT_DISC = bytes([103, 244, 82, 31, 44, 245, 119, 119])
PUMPSWAP_SELL_EVENT_DISC = bytes([62, 47, 55, 10, 165, 3, 220, 42])
PUMPSWAP_CREATE_POOL_EVENT_DISC = bytes([177, 49, 12, 210, 160, 118, 167, 116])

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_INDEX = {c: i for i, c in enumerate(B58_ALPHABET)}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(p: pathlib.Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def jl(p: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def dumpj(p: pathlib.Path, obj: Any) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V14_OUTPUT_ALREADY_EXISTS {p}; preserve prior evaluation")
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def dumpjl(p: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V14_OUTPUT_ALREADY_EXISTS {p}; preserve prior evaluation")
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sha(p)


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        if c not in B58_INDEX:
            raise ValueError(f"invalid base58 char {c!r}")
        n = n * 58 + B58_INDEX[c]
    raw = b"" if n == 0 else n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    chars = ""
    while n:
        n, rem = divmod(n, 58)
        chars = B58_ALPHABET[rem] + chars
    pad = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * pad + (chars or "")


def read_u64(raw: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<Q", raw, off)[0], off + 8


def read_i64(raw: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<q", raw, off)[0], off + 8


def read_pubkey(raw: bytes, off: int) -> Tuple[str, int]:
    return b58encode(raw[off:off+32]), off + 32


def decode_trade_event(raw: bytes) -> Dict[str, Any]:
    if not raw.startswith(TRADE_EVENT_DISC) or len(raw) != TRADE_EVENT_LEN:
        raise RuntimeError("PUMP_TRADE_EVENT_SHAPE_FAILURE")
    off = 8
    mint, off = read_pubkey(raw, off)
    sol_amount, off = read_u64(raw, off)
    token_amount, off = read_u64(raw, off)
    is_buy = bool(raw[off]); off += 1
    user, off = read_pubkey(raw, off)
    timestamp, off = read_i64(raw, off)
    virtual_sol, off = read_u64(raw, off)
    virtual_token, off = read_u64(raw, off)
    real_sol, off = read_u64(raw, off)
    real_token, off = read_u64(raw, off)
    fee_recipient, off = read_pubkey(raw, off)
    fee_bps, off = read_u64(raw, off)
    fee, off = read_u64(raw, off)
    creator, off = read_pubkey(raw, off)
    creator_fee_bps, off = read_u64(raw, off)
    creator_fee, off = read_u64(raw, off)
    if off != TRADE_EVENT_LEN:
        raise RuntimeError("PUMP_TRADE_EVENT_OFFSET_FAILURE")
    return {
        "mint": mint,
        "sol_amount_raw": sol_amount,
        "token_amount_raw": token_amount,
        "side": "buy" if is_buy else "sell",
        "user": user,
        "timestamp": timestamp,
        "virtual_sol_reserves_raw": virtual_sol,
        "virtual_token_reserves_raw": virtual_token,
        "real_sol_reserves_raw": real_sol,
        "real_token_reserves_raw": real_token,
        "fee_recipient": fee_recipient,
        "fee_basis_points": fee_bps,
        "protocol_fee_raw": fee,
        "creator": creator,
        "creator_fee_basis_points": creator_fee_bps,
        "creator_fee_raw": creator_fee,
    }


def program_data_records(logs: List[str]) -> List[Tuple[int, bytes]]:
    out = []
    for i, line in enumerate(logs or []):
        if not isinstance(line, str) or not line.startswith("Program data: "):
            continue
        try:
            raw = base64.b64decode(line.split("Program data: ", 1)[1].strip(), validate=True)
        except Exception:
            continue
        out.append((i, raw))
    return out


def normalized_account_keys(result: Dict[str, Any]) -> List[str]:
    tx = result.get("transaction") or {}
    msg = tx.get("message") or {}
    keys: List[str] = []
    for k in msg.get("accountKeys") or []:
        if isinstance(k, str):
            keys.append(k)
        elif isinstance(k, dict) and isinstance(k.get("pubkey"), str):
            keys.append(k["pubkey"])
        else:
            raise RuntimeError("ACCOUNT_KEY_SHAPE_FAILURE")
    loaded = (result.get("meta") or {}).get("loadedAddresses") or {}
    for k in (loaded.get("writable") or []):
        keys.append(str(k))
    for k in (loaded.get("readonly") or []):
        keys.append(str(k))
    return keys


def all_compiled_instructions(result: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    msg = ((result.get("transaction") or {}).get("message") or {})
    for ix in msg.get("instructions") or []:
        if isinstance(ix, dict):
            yield ix
    for group in ((result.get("meta") or {}).get("innerInstructions") or []):
        for ix in group.get("instructions") or []:
            if isinstance(ix, dict):
                yield ix


def has_pump_migrate(result: Dict[str, Any]) -> bool:
    keys = normalized_account_keys(result)
    for ix in all_compiled_instructions(result):
        pidx = ix.get("programIdIndex")
        data = ix.get("data")
        if pidx is None or not isinstance(data, str):
            continue
        if int(pidx) < 0 or int(pidx) >= len(keys):
            raise RuntimeError("PROGRAM_INDEX_OUT_OF_RANGE")
        if keys[int(pidx)] != PUMP_PROGRAM:
            continue
        try:
            raw = b58decode(data)
        except Exception:
            continue
        if raw.startswith(PUMP_MIGRATE_DISC):
            return True
    return False


def entry_quote_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    creator = str(state.get("creator") or DEFAULT_PUBKEY)
    total_fee_bps = int(state["fee_basis_points"])
    if creator != DEFAULT_PUBKEY:
        total_fee_bps += int(state["creator_fee_basis_points"])
    input_after_fee = ENTRY_GROSS_LAMPORTS * 10_000 // (10_000 + total_fee_bps)
    vsol = int(state["virtual_sol_reserves_raw"])
    vtok = int(state["virtual_token_reserves_raw"])
    rtok = int(state["real_token_reserves_raw"])
    tokens_uncapped = input_after_fee * vtok // (vsol + input_after_fee)
    tokens = min(tokens_uncapped, rtok)
    if tokens <= 0:
        raise RuntimeError(f"ZERO_ENTRY_TOKENS mint={state['mint']}")
    return {
        "entry_gross_lamports": ENTRY_GROSS_LAMPORTS,
        "entry_tokens_raw": tokens,
        "entry_price_raw_lamports_per_token_raw": ENTRY_GROSS_LAMPORTS / tokens,
        "entry_total_fee_bps": total_fee_bps,
        "entry_state_signature": state.get("signature"),
        "entry_state_block_time": int(state["block_time"]),
    }


def safe_rate(n: int, d: int) -> Optional[float]:
    return None if d == 0 else n / d


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    dsource = here / "data" / "msel001_pilot25_outcome_source_v13"
    dbind = here / "data" / "msel001_pilot25_v14_binding_v13f"
    dfeat = here / "data" / "msel001_pilot25_feature_v11"
    dpre = here / "data" / "msel001_t5_forensics"
    dcohort = here / "data" / "msel001_pilot25_blockscan"

    binding_p = dbind / "v14_input_binding_v13f.json"
    v13m_p = dsource / "outcome_source_manifest_v13.json"
    sig_index_p = dsource / "future_signature_index_v13.jsonl"
    risk_p = dfeat / "pilot25_primary_risk_order_v11.jsonl"
    events_p = dpre / "trade_events_economic_v03.jsonl"
    cohort_p = dcohort / "cohort_25.jsonl"

    for p in (binding_p, v13m_p, sig_index_p, risk_p, events_p, cohort_p):
        if not p.exists():
            raise RuntimeError(f"MISSING_INPUT {p}")
    if sha(binding_p) != EXPECTED_BINDING_SHA:
        raise RuntimeError(f"V13F_BINDING_HASH_MISMATCH actual={sha(binding_p)}")
    if sha(v13m_p) != EXPECTED_V13_MANIFEST_SHA:
        raise RuntimeError("V13_MANIFEST_HASH_MISMATCH")
    if sha(risk_p) != EXPECTED_V11_RISK_SHA:
        raise RuntimeError("V11_RISK_HASH_MISMATCH")
    if sha(events_p) != EXPECTED_V03_EVENTS_SHA:
        raise RuntimeError("V03_EVENTS_HASH_MISMATCH")
    if sha(cohort_p) != EXPECTED_COHORT_SHA:
        raise RuntimeError("COHORT_HASH_MISMATCH")

    binding = j(binding_p)
    if binding.get("v14_pilot_economic_evaluation_authorized") is not True:
        raise RuntimeError("V14_NOT_AUTHORIZED_BY_BINDING")
    if int(binding.get("entry_coverage_mints", 0)) != 25:
        raise RuntimeError("ENTRY_COVERAGE_NOT_25")

    v13m = j(v13m_p)
    if v13m.get("all_25_mint_histories_exhausted_to_create_boundary") is not True:
        raise RuntimeError("V13_SOURCE_INCOMPLETE")
    if int(v13m.get("raw_transaction_count", -1)) != EXPECTED_FUTURE_TX:
        raise RuntimeError("V13_RAW_TX_COUNT_MISMATCH")
    if v13m.get("future_signature_index_sha256") != sha(sig_index_p):
        raise RuntimeError("V13_SIGNATURE_INDEX_HASH_MISMATCH")

    risk_rows = jl(risk_p)
    cohort = jl(cohort_p)
    if len(risk_rows) != 25 or len(cohort) != 25:
        raise RuntimeError("PILOT_SHAPE_FAILURE")
    risk_by_mint = {r["mint"]: r for r in risk_rows}
    cohort_by_mint = {r["mint"]: r for r in cohort}
    if set(risk_by_mint) != set(cohort_by_mint):
        raise RuntimeError("RISK_COHORT_MINT_MISMATCH")

    events = jl(events_p)
    pre_by_mint: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in events:
        if r.get("mint") in cohort_by_mint:
            deadline = int(cohort_by_mint[r["mint"]]["block_time"]) + DECISION_SECONDS
            if int(r["block_time"]) <= deadline:
                pre_by_mint[r["mint"]].append(r)
    entries: Dict[str, Dict[str, Any]] = {}
    for mint in sorted(cohort_by_mint):
        rows = pre_by_mint.get(mint) or []
        if not rows:
            raise RuntimeError(f"NO_PRE_T5_STATE mint={mint}")
        state = max(rows, key=lambda r: (int(r["block_time"]), int(r.get("slot", 0)), int(r.get("transaction_index", 0)), int(r.get("log_index", 0))))
        e = entry_quote_from_state(state)
        e.update({"mint": mint, "decision_time": int(cohort_by_mint[mint]["block_time"]) + DECISION_SECONDS})
        entries[mint] = e
    if len(entries) != 25:
        raise RuntimeError("ENTRY_RECONSTRUCTION_NOT_25")

    sig_rows = jl(sig_index_p)
    if len(sig_rows) != EXPECTED_FUTURE_TX:
        raise RuntimeError(f"SIGNATURE_INDEX_COUNT_MISMATCH {len(sig_rows)}/{EXPECTED_FUTURE_TX}")
    raw_dir = dsource / "raw_transactions"
    future_events: List[Dict[str, Any]] = []
    migration_sigs: List[str] = []
    pumpswap_event_sigs: List[Dict[str, Any]] = []
    missing_results: List[str] = []

    for idx in sig_rows:
        p = raw_dir / str(idx["raw_transaction_file"])
        if not p.exists():
            raise RuntimeError(f"MISSING_RAW_TX {p.name}")
        if sha(p) != str(idx["raw_transaction_sha256"]):
            raise RuntimeError(f"RAW_TX_HASH_MISMATCH {p.name}")
        payload = json.loads(p.read_bytes())
        result = payload.get("result")
        if not isinstance(result, dict):
            missing_results.append(str(idx["signature"]))
            continue
        meta = result.get("meta") or {}
        if meta.get("err") is not None:
            continue
        sig = str(idx["signature"])
        bt = int(result.get("blockTime") if result.get("blockTime") is not None else idx["block_time"])
        if has_pump_migrate(result):
            migration_sigs.append(sig)
        tx_pump_events = []
        for log_index, raw in program_data_records(meta.get("logMessages") or []):
            if raw.startswith(TRADE_EVENT_DISC):
                ev = decode_trade_event(raw)
                ev.update({"signature": sig, "block_time": bt, "log_index": log_index})
                tx_pump_events.append(ev)
            elif raw.startswith(PUMPSWAP_BUY_EVENT_DISC):
                pumpswap_event_sigs.append({"signature": sig, "kind": "BUY_EVENT"})
            elif raw.startswith(PUMPSWAP_SELL_EVENT_DISC):
                pumpswap_event_sigs.append({"signature": sig, "kind": "SELL_EVENT"})
            elif raw.startswith(PUMPSWAP_CREATE_POOL_EVENT_DISC):
                pumpswap_event_sigs.append({"signature": sig, "kind": "CREATE_POOL_EVENT"})

        atomic_keys = set()
        buys = [e for e in tx_pump_events if e["side"] == "buy"]
        sells = [e for e in tx_pump_events if e["side"] == "sell"]
        for b in buys:
            for s in sells:
                if b["mint"] == s["mint"] and int(b["token_amount_raw"]) == int(s["token_amount_raw"]):
                    atomic_keys.add((b["mint"], int(b["token_amount_raw"])))
        for ev in tx_pump_events:
            ev["atomic_roundtrip_component"] = (ev["mint"], int(ev["token_amount_raw"])) in atomic_keys
            if ev["mint"] in cohort_by_mint:
                future_events.append(ev)

    if missing_results:
        raise RuntimeError(f"OUTCOME_SOURCE_UNRESOLVED missing_transaction_results={len(missing_results)}")
    if migration_sigs or pumpswap_event_sigs:
        kinds: Dict[str, int] = {}
        for r in pumpswap_event_sigs:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print("BLOCKED: canonical PumpSwap migration continuity required before labels")
        print(f"Pump migrate transactions detected: {len(set(migration_sigs))}")
        print(f"PumpSwap historical event records detected: {len(pumpswap_event_sigs)}")
        print(f"PumpSwap event kinds: {kinds}")
        print("NO RETURNS OR LABELS COMPUTED")
        raise RuntimeError("PUMPSWAP_PATH_PRESENT_REQUIRES_CANONICAL_MIGRATION_DECODER")

    sells_by_mint: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in future_events:
        mint = ev["mint"]
        decision = entries[mint]["decision_time"]
        if ev["side"] != "sell" or int(ev["block_time"]) <= decision:
            continue
        if int(ev["sol_amount_raw"]) < SELL_FLOOR_LAMPORTS:
            continue
        if ev.get("atomic_roundtrip_component"):
            continue
        price = int(ev["sol_amount_raw"]) / int(ev["token_amount_raw"])
        ret = price / float(entries[mint]["entry_price_raw_lamports_per_token_raw"]) - 1.0
        stressed = (1.0 + ret) * (1.0 - STRESS_HAIRCUT) - 1.0
        row = dict(ev)
        row.update({"exit_price_raw_lamports_per_token_raw": price, "return_raw": ret, "return_stressed_3pct": stressed})
        sells_by_mint[mint].append(row)

    outcome_rows = []
    for mint in sorted(cohort_by_mint, key=lambda m: int(cohort_by_mint[m]["cohort_rank"])):
        decision = entries[mint]["decision_time"]
        rs = sorted(sells_by_mint.get(mint, []), key=lambda r: (int(r["block_time"]), r["signature"], int(r["log_index"])))
        row: Dict[str, Any] = {
            "mint": mint,
            "cohort_rank": int(cohort_by_mint[mint]["cohort_rank"]),
            "decision_time": decision,
            "entry": entries[mint],
            "valid_sell_count_24h": len([r for r in rs if int(r["block_time"]) <= decision + 86400]),
        }
        for w in WINDOWS:
            wr = [r for r in rs if int(r["block_time"]) <= decision + w]
            row[f"sell_count_{w}s"] = len(wr)
            row[f"min_return_{w}s"] = min((float(r["return_raw"]) for r in wr), default=None)
            row[f"max_return_{w}s"] = max((float(r["return_raw"]) for r in wr), default=None)
            row[f"min_return_stressed_{w}s"] = min((float(r["return_stressed_3pct"]) for r in wr), default=None)
            row[f"max_return_stressed_{w}s"] = max((float(r["return_stressed_3pct"]) for r in wr), default=None)
        r24 = [r for r in rs if int(r["block_time"]) <= decision + 86400]
        no_sell = len(r24) == 0
        min24 = min((float(r["return_raw"]) for r in r24), default=None)
        max24 = max((float(r["return_raw"]) for r in r24), default=None)
        min24s = min((float(r["return_stressed_3pct"]) for r in r24), default=None)
        max24s = max((float(r["return_stressed_3pct"]) for r in r24), default=None)
        row["catastrophic_liquidity_absence"] = no_sell
        row["catastrophic_24h"] = bool(no_sell or (min24 is not None and min24 <= CATASTROPHE_THRESHOLD))
        row["winner_24h"] = bool(max24 is not None and max24 >= WINNER_THRESHOLD)
        row["catastrophic_24h_stressed"] = bool(no_sell or (min24s is not None and min24s <= CATASTROPHE_THRESHOLD))
        row["winner_24h_stressed"] = bool(max24s is not None and max24s >= WINNER_THRESHOLD)
        rr = risk_by_mint[mint]
        row.update({
            "primary_risk_rank_1_is_safest": int(rr["primary_risk_rank_1_is_safest"]),
            "primary_pilot_risk_score": float(rr["primary_pilot_risk_score"]),
            "slice_safest20": bool(rr["slice_safest20"]),
            "slice_safest50": bool(rr["slice_safest50"]),
            "slice_riskiest20": bool(rr["slice_riskiest20"]),
        })
        outcome_rows.append(row)

    def slice_stats(name: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(rows)
        cats = sum(bool(r["catastrophic_24h"]) for r in rows)
        wins = sum(bool(r["winner_24h"]) for r in rows)
        cats_s = sum(bool(r["catastrophic_24h_stressed"]) for r in rows)
        wins_s = sum(bool(r["winner_24h_stressed"]) for r in rows)
        return {"slice": name, "n": n, "catastrophes": cats, "catastrophe_rate": safe_rate(cats, n),
                "winners": wins, "winner_rate": safe_rate(wins, n),
                "catastrophes_stressed": cats_s, "catastrophe_rate_stressed": safe_rate(cats_s, n),
                "winners_stressed": wins_s, "winner_rate_stressed": safe_rate(wins_s, n)}

    full = outcome_rows
    s20 = [r for r in outcome_rows if r["slice_safest20"]]
    s50 = [r for r in outcome_rows if r["slice_safest50"]]
    r20 = [r for r in outcome_rows if r["slice_riskiest20"]]
    stats = [slice_stats("full", full), slice_stats("safest20", s20), slice_stats("safest50", s50), slice_stats("riskiest20", r20)]
    smap = {r["slice"]: r for r in stats}
    base = float(smap["full"]["catastrophe_rate"])
    g1 = None if base == 0 else float(smap["safest20"]["catastrophe_rate"]) <= 0.60 * base
    g2 = None if base == 0 else float(smap["safest50"]["catastrophe_rate"]) <= 0.80 * base
    g3 = None if base == 0 else float(smap["riskiest20"]["catastrophe_rate"]) >= 1.50 * base
    total_winners = int(smap["full"]["winners"])
    winner_retention = None if total_winners == 0 else int(smap["safest50"]["winners"]) / total_winners
    g4 = None if winner_retention is None else winner_retention >= 0.50

    partial_gates = {
        "gate1_safest20_catastrophe_le_60pct_baseline": g1,
        "gate2_safest50_catastrophe_le_80pct_baseline": g2,
        "gate3_riskiest20_catastrophe_ge_1p5x_baseline": g3,
        "gate4_safest50_winner_retention_ge_50pct": g4,
        "winner_retention_safest50": winner_retention,
        "gate5_structural_vs_price_volume_control": None,
        "gate6_three_chronological_oos_blocks": None,
        "gate7_leakage_source_gate": True,
        "full_mve_verdict_authorized": False,
    }

    out = here / "data" / "msel001_pilot25_outcomes_v14"
    outcomes_p = out / "pilot25_outcomes_v14.jsonl"
    sells_p = out / "valid_future_pump_sells_v14.jsonl"
    stats_p = out / "pilot25_slice_stats_v14.json"
    gates_p = out / "pilot25_partial_mve_gates_v14.json"
    out_sha = dumpjl(outcomes_p, outcome_rows)
    sell_sha = dumpjl(sells_p, [r for mint in sorted(sells_by_mint) for r in sells_by_mint[mint]])
    stats_sha = dumpj(stats_p, stats)
    gates_sha = dumpj(gates_p, partial_gates)
    manifest = {
        "artifact": "MSEL_PILOT25_ECONOMIC_EVALUATION_V14",
        "pilot_only": True,
        "full_mve_verdict_authorized": False,
        "source_v13f_binding_sha256": EXPECTED_BINDING_SHA,
        "source_v13_manifest_sha256": EXPECTED_V13_MANIFEST_SHA,
        "source_v03_trade_events_sha256": EXPECTED_V03_EVENTS_SHA,
        "source_v11_risk_order_sha256": EXPECTED_V11_RISK_SHA,
        "entry_authority": "V12A_T5_PUMP_CURVE_GROSS_0.01_SOL",
        "future_path": "PUMP_ONLY_CONFIRMED_NO_MIGRATION_OR_PUMPSWAP_EVENT_IN_SEALED_24H_SOURCE",
        "outcome_rows": 25,
        "valid_future_pump_sells": sum(len(v) for v in sells_by_mint.values()),
        "outcomes_sha256": out_sha,
        "valid_future_pump_sells_sha256": sell_sha,
        "slice_stats_sha256": stats_sha,
        "partial_gates_sha256": gates_sha,
        "returns_computed": True,
        "labels_computed": True,
        "slice_statistics_computed": True,
        "verdict_computed": False,
    }
    man_p = out / "pilot25_outcome_manifest_v14.json"
    man_sha = dumpj(man_p, manifest)

    print("PASS: Pilot25 economic evaluation V14 complete")
    print("future path: Pump-only; no migration/PumpSwap path detected in sealed source")
    print(f"valid future Pump SELL executions >=0.01 SOL: {manifest['valid_future_pump_sells']}")
    print(f"full catastrophe rate: {smap['full']['catastrophe_rate']}")
    print(f"safest20 catastrophe rate: {smap['safest20']['catastrophe_rate']}")
    print(f"safest50 catastrophe rate: {smap['safest50']['catastrophe_rate']}")
    print(f"riskiest20 catastrophe rate: {smap['riskiest20']['catastrophe_rate']}")
    print(f"full +100% winners: {smap['full']['winners']}")
    print(f"safest50 +100% winners: {smap['safest50']['winners']}")
    print(f"safest50 winner retention: {winner_retention}")
    print(f"partial frozen gates 1/2/3/4: {g1}/{g2}/{g3}/{g4}")
    print(f"manifest sha256: {man_sha}")
    print("PILOT25 ONLY — FULL SURVIVES_MVE VERDICT NOT AUTHORIZED")
    print("NO LIVE TRADING / NO MAIN MERGE / NO POST-OUTCOME TUNING")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
