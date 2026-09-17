#!/usr/bin/env python3
"""PMD-001 V0.12 chain-exact pre-migration feature extractor.

SOURCE-ONLY. Reads V0.7 full chain-exact raw transaction evidence and derives
only information strictly before the exact migration boundary. It never reads
post-migration prices or economic outcomes.

The feature recipe is frozen in CHAIN_EXACT_FEATURE_RECIPE_FREEZE_V012.md.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from intrablock_boundary_probe_v05 import (
    PUMP_PROGRAM,
    account_keys,
    ix_data,
    resolve_ix_accounts,
    resolve_program,
)

TRADE_EVENT_DISC = hashlib.sha256(b"event:TradeEvent").digest()[:8]
BUY_DISCS = {
    hashlib.sha256(b"global:buy").digest()[:8]: "buy",
    hashlib.sha256(b"global:buy_v2").digest()[:8]: "buy",
}
SELL_DISCS = {
    hashlib.sha256(b"global:sell").digest()[:8]: "sell",
    hashlib.sha256(b"global:sell_v2").digest()[:8]: "sell",
}
WINDOWS = (30, 60, 300)
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58_ALPHABET[r] + s
    leading = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * leading + (s or "")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def compiled_instructions(item: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    tx = item.get("transaction") or {}
    msg = tx.get("message") or {}
    out.extend(x for x in (msg.get("instructions") or []) if isinstance(x, dict))
    meta = item.get("meta") or {}
    for group in meta.get("innerInstructions") or []:
        if not isinstance(group, dict):
            continue
        out.extend(x for x in (group.get("instructions") or []) if isinstance(x, dict))
    return out


def trade_intents(item: dict[str, Any], mint: str, pda: str) -> list[str]:
    """Recognize frozen legacy + v2 trade instructions; logs add a fail-closed fallback."""
    keys = account_keys(item)
    kinds: list[str] = []
    for ix in compiled_instructions(item):
        if resolve_program(ix, keys) != PUMP_PROGRAM:
            continue
        data = ix_data(ix)
        if len(data) < 8:
            continue
        accounts = set(resolve_ix_accounts(ix, keys))
        if mint not in accounts or pda not in accounts:
            continue
        disc = bytes(data[:8])
        if disc in BUY_DISCS:
            kinds.append("buy")
        elif disc in SELL_DISCS:
            kinds.append("sell")
    if not kinds:
        logs = [str(x) for x in ((item.get("meta") or {}).get("logMessages") or [])]
        for line in logs:
            if "Instruction: Buy" in line:
                kinds.append("buy")
            elif "Instruction: Sell" in line:
                kinds.append("sell")
    return kinds


def parse_trade_event_blob(blob: bytes, target_mint: str, block_time: int | float | None) -> dict[str, Any] | None:
    # Anchor emit!/emit_cpi! may place an event wrapper before the event discriminator.
    at = blob.find(TRADE_EVENT_DISC)
    if at < 0 or at > 32:
        return None
    p = at + 8
    # Stable TradeEvent prefix: mint, sol, token, is_buy, user, timestamp,
    # virtual_sol, virtual_token, real_sol, real_token.
    need = 32 + 8 + 8 + 1 + 32 + 8 + 8 + 8 + 8 + 8
    if len(blob) < p + need:
        return None
    mint = b58encode(blob[p:p+32]); p += 32
    sol_amount = int.from_bytes(blob[p:p+8], "little"); p += 8
    token_amount = int.from_bytes(blob[p:p+8], "little"); p += 8
    flag = blob[p]; p += 1
    if flag not in (0, 1):
        return None
    user = b58encode(blob[p:p+32]); p += 32
    timestamp = int.from_bytes(blob[p:p+8], "little", signed=True); p += 8
    virtual_sol = int.from_bytes(blob[p:p+8], "little"); p += 8
    virtual_token = int.from_bytes(blob[p:p+8], "little"); p += 8
    real_sol = int.from_bytes(blob[p:p+8], "little"); p += 8
    real_token = int.from_bytes(blob[p:p+8], "little"); p += 8
    if mint != target_mint or sol_amount <= 0 or token_amount <= 0:
        return None
    if block_time is not None and abs(timestamp - int(block_time)) > 30:
        return None
    return {
        "mint": mint,
        "sol_lamports": sol_amount,
        "sol_amount": sol_amount / 1_000_000_000.0,
        "token_amount_raw": token_amount,
        "side": "buy" if flag == 1 else "sell",
        "user": user,
        "timestamp": timestamp,
        "virtual_sol_reserves": virtual_sol,
        "virtual_token_reserves": virtual_token,
        "real_sol_reserves": real_sol,
        "real_token_reserves": real_token,
    }


def event_blobs(item: dict[str, Any]) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for line in ((item.get("meta") or {}).get("logMessages") or []):
        s = str(line)
        marker = "Program data: "
        if marker in s:
            try:
                out.append(("log_program_data", base64.b64decode(s.split(marker, 1)[1].strip(), validate=True)))
            except Exception:
                pass
    keys = account_keys(item)
    for ix in compiled_instructions(item):
        if resolve_program(ix, keys) != PUMP_PROGRAM:
            continue
        raw = ix_data(ix)
        if raw:
            out.append(("pump_instruction_data", raw))
    return out


def extract_events(item: dict[str, Any], mint: str, block_time: int | float | None) -> list[dict[str, Any]]:
    found: dict[tuple[Any, ...], dict[str, Any]] = {}
    keys = set(account_keys(item))
    for source, blob in event_blobs(item):
        ev = parse_trade_event_blob(blob, mint, block_time)
        if ev is None or ev["user"] not in keys:
            continue
        fp = (
            ev["mint"], ev["sol_lamports"], ev["token_amount_raw"], ev["side"],
            ev["user"], ev["timestamp"], ev["virtual_sol_reserves"], ev["virtual_token_reserves"],
            ev["real_sol_reserves"], ev["real_token_reserves"],
        )
        rec = dict(ev)
        rec.setdefault("decode_sources", []).append(source)
        if fp in found:
            found[fp]["decode_sources"] = sorted(set(found[fp]["decode_sources"] + rec["decode_sources"]))
        else:
            found[fp] = rec
    return list(found.values())


def window_metrics(events: list[dict[str, Any]], tx_audit: list[dict[str, Any]], boundary_time: float, sec: int, source_complete: bool) -> dict[str, Any]:
    evs = [e for e in events if float(e["block_time"]) >= boundary_time - sec]
    txs = [t for t in tx_audit if float(t["block_time"]) >= boundary_time - sec]
    intents = sum(int(t["intent_count"]) for t in txs)
    undecoded = sum(int(t["undecoded_intents"]) for t in txs)
    ambiguous = sum(int(t["ambiguous_events"]) for t in txs)
    decoder_complete = bool(source_complete and undecoded == 0 and ambiguous == 0)
    buys = [e for e in evs if e["side"] == "buy"]
    sells = [e for e in evs if e["side"] == "sell"]
    amounts = [float(e["sol_amount"]) for e in evs]
    buy_sol = sum(float(e["sol_amount"]) for e in buys)
    sell_sol = sum(float(e["sol_amount"]) for e in sells)
    n = len(evs)
    participants = {e["user"] for e in evs}
    buyers = {e["user"] for e in buys}
    sellers = {e["user"] for e in sells}
    denom = buy_sol + sell_sol
    result: dict[str, Any] = {
        "window_seconds": sec,
        "source_complete": bool(source_complete),
        "decoder_complete": decoder_complete,
        "recognized_trade_intents": intents,
        "undecoded_trade_intents": undecoded,
        "ambiguous_events": ambiguous,
        "decoded_trade_events": n,
    }
    # Missing decode is not silently converted to zero economic flow.
    if not decoder_complete:
        for k in [
            "buy_count","sell_count","unique_buyers","unique_sellers","unique_participants",
            "buy_volume_sol","sell_volume_sol","net_flow_sol","volume_balance","count_balance",
            "buy_fraction","wallet_breadth","avg_trade_sol","median_trade_sol","largest_buy_sol","largest_sell_sol",
        ]:
            result[k] = None
        return result
    result.update({
        "buy_count": len(buys),
        "sell_count": len(sells),
        "unique_buyers": len(buyers),
        "unique_sellers": len(sellers),
        "unique_participants": len(participants),
        "buy_volume_sol": buy_sol,
        "sell_volume_sol": sell_sol,
        "net_flow_sol": buy_sol - sell_sol,
        "volume_balance": ((buy_sol - sell_sol) / denom) if denom > 0 else 0.0,
        "count_balance": ((len(buys) - len(sells)) / n) if n else 0.0,
        "buy_fraction": (len(buys) / n) if n else 0.0,
        "wallet_breadth": (len(participants) / n) if n else 0.0,
        "avg_trade_sol": statistics.fmean(amounts) if amounts else 0.0,
        "median_trade_sol": statistics.median(amounts) if amounts else 0.0,
        "largest_buy_sol": max((float(e["sol_amount"]) for e in buys), default=0.0),
        "largest_sell_sol": max((float(e["sol_amount"]) for e in sells), default=0.0),
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.input_root)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    for p in sorted(root.rglob("source_rebuild_summary.jsonl")):
        summaries.extend(read_jsonl(p))
    by_mint = {str(r.get("mint")): r for r in summaries if r.get("mint")}
    if len(by_mint) != len(summaries):
        raise RuntimeError("duplicate or missing mint in V0.7 summaries")

    raw_files = {p.stem: p for p in root.rglob("raw/*.jsonl")}
    rows: list[dict[str, Any]] = []
    total_events = total_intents = total_undecoded = total_ambiguous = 0
    for mint, summary in sorted(by_mint.items(), key=lambda kv: (str(kv[1].get("t0")), kv[0])):
        source_complete = bool(summary.get("source_complete"))
        boundary_time = summary.get("chain_boundary_block_time")
        pda = str(summary.get("bonding_curve_pda") or "")
        pool = str(summary.get("pool_address") or "")
        events: list[dict[str, Any]] = []
        tx_audit: list[dict[str, Any]] = []
        raw_path = raw_files.get(mint)
        if raw_path and boundary_time is not None:
            for rec in read_jsonl(raw_path):
                if rec.get("outcomes_opened") is not False:
                    raise RuntimeError(f"outcome wall violation in raw evidence for {mint}")
                item = rec.get("transaction") or {}
                order = rec.get("ledger_order") or {}
                bt = order.get("block_time")
                if bt is None:
                    continue
                intents = trade_intents(item, mint, pda)
                decoded = extract_events(item, mint, bt)
                recognized_sides = set(intents)
                valid: list[dict[str, Any]] = []
                ambiguous = 0
                for ev in decoded:
                    if recognized_sides and ev["side"] not in recognized_sides:
                        ambiguous += 1
                        continue
                    ev = dict(ev)
                    ev.update({"block_time": bt, "slot": order.get("slot"), "transaction_index": order.get("transaction_index")})
                    valid.append(ev)
                undecoded = max(0, len(intents) - len(valid))
                tx_audit.append({
                    "block_time": bt,
                    "intent_count": len(intents),
                    "decoded_events": len(valid),
                    "undecoded_intents": undecoded,
                    "ambiguous_events": ambiguous,
                })
                events.extend(valid)
                total_events += len(valid); total_intents += len(intents); total_undecoded += undecoded; total_ambiguous += ambiguous

        row: dict[str, Any] = {
            "lab": "PMD-001",
            "stage": "CHAIN_EXACT_FEATURES_V012",
            "economic_outcomes_opened": False,
            "promotion_authority": False,
            "mint": mint,
            "t0": summary.get("t0"),
            "migration_variant": summary.get("migration_variant"),
            "pool_address": pool,
            "chain_boundary_block_time": boundary_time,
            "chain_boundary_slot": summary.get("chain_boundary_slot"),
            "chain_boundary_transaction_index": summary.get("chain_boundary_transaction_index"),
            "source_complete": source_complete,
            "feature_source_eligible": bool(summary.get("feature_source_eligible")),
            "successful_target_pre_boundary_transactions": summary.get("successful_target_pre_boundary_transactions"),
            "decoded_events_total_300s": len(events),
            "recognized_trade_intents_total_300s": sum(int(x["intent_count"]) for x in tx_audit),
            "undecoded_trade_intents_total_300s": sum(int(x["undecoded_intents"]) for x in tx_audit),
            "ambiguous_events_total_300s": sum(int(x["ambiguous_events"]) for x in tx_audit),
        }
        if events and boundary_time is not None:
            distances = [float(boundary_time) - float(e["block_time"]) for e in events]
            row["nearest_decoded_trade_seconds_to_boundary"] = min(distances)
            row["furthest_decoded_trade_seconds_to_boundary"] = max(distances)
        else:
            row["nearest_decoded_trade_seconds_to_boundary"] = None
            row["furthest_decoded_trade_seconds_to_boundary"] = None
        for sec in WINDOWS:
            m = window_metrics(events, tx_audit, float(boundary_time) if boundary_time is not None else math.nan, sec, source_complete) if boundary_time is not None else {"window_seconds":sec,"source_complete":False,"decoder_complete":False}
            for k, v in m.items():
                if k not in {"window_seconds"}:
                    row[f"{k}_w{sec}"] = v

        # Frozen acceleration features; only calculate when both component windows decode completely.
        for metric in ["net_flow_sol","buy_volume_sol","sell_volume_sol","decoded_trade_events","unique_participants"]:
            a60 = row.get(f"{metric}_w60"); a300 = row.get(f"{metric}_w300")
            row[f"{metric}_accel_per_min_w60_vs_w300"] = (a60 - a300 / 5.0) if a60 is not None and a300 is not None else None
            a30 = row.get(f"{metric}_w30"); a60b = row.get(f"{metric}_w60")
            row[f"{metric}_accel_per_sec_w30_vs_w60"] = (a30 / 30.0 - a60b / 60.0) if a30 is not None and a60b is not None else None
        rows.append(row)

    rows_path = out / "chain_exact_features_v012.jsonl"
    rows_path.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    receipt = {
        "lab": "PMD-001",
        "stage": "CHAIN_EXACT_FEATURES_V012",
        "economic_outcomes_opened": False,
        "promotion_authority": False,
        "summary_rows": len(summaries),
        "unique_mints": len(by_mint),
        "raw_mint_files": len(raw_files),
        "source_complete_rows": sum(bool(r.get("source_complete")) for r in rows),
        "feature_source_eligible_rows": sum(bool(r.get("feature_source_eligible")) for r in rows),
        "decoder_complete_w30": sum(bool(r.get("decoder_complete_w30")) for r in rows),
        "decoder_complete_w60": sum(bool(r.get("decoder_complete_w60")) for r in rows),
        "decoder_complete_w300": sum(bool(r.get("decoder_complete_w300")) for r in rows),
        "decoded_trade_events": total_events,
        "recognized_trade_intents": total_intents,
        "undecoded_trade_intents": total_undecoded,
        "ambiguous_events": total_ambiguous,
        "trade_event_discriminator_hex": TRADE_EVENT_DISC.hex(),
        "rows_sha256": sha256_file(rows_path),
    }
    (out / "chain_exact_features_v012_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
