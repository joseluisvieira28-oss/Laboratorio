"""Re-audit already completed 2023-25 V5 trade-ledger artifacts only.

No market downloads, order APIs, 2026 holdout, optimization or trading.
See PRE_LEDGER_OUTCOME_FREEZE_2026_10_17.md for frozen scientific rules.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXTRA_BPS = (0, 6, 12, 20, 40)
CANDIDATES = (
    ("SOL_1H", "SOLUSDT", "1h", "common"),
    ("BNB_4H", "BNBUSDT", "4h", "common"),
    ("SOL_5M", "SOLUSDT", "5m", "native"),
)
START_MS, END_MS = 1672531200000, 1767225600000


def f(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}:NOT_NUMBER") from exc
    if not math.isfinite(v):
        raise ValueError(f"{name}:NONFINITE")
    return v


def load_source(root, symbol, kind):
    matches = []
    for path in root.rglob("RESULT.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("symbol") == symbol and (
            (kind == "common" and doc.get("status") == "COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT")
            or (kind == "native" and doc.get("status") == "HISTORICAL_NATIVE_5M_COMPLETE_NO_OOS_CREDIT")
        ):
            matches.append((path, doc))
    if len(matches) != 1:
        raise ValueError(f"EXACTLY_ONE_ORIGINAL_RECEIPT_REQUIRED:{symbol}:{kind}:{len(matches)}")
    path, doc = matches[0]
    expected = {"5m": 333216, "1h": 27768, "funding": 3288}
    if doc.get("source_counts") != expected or len(doc.get("source_manifest", [])) != 112:
        raise ValueError("PUBLISHER_SOURCE_CUSTODY_NOT_VERIFIED")
    if kind == "common" and (doc.get("independent_OOS") is not False or doc.get("actual_venue_fills") is not False):
        raise ValueError("FALSE_PROOF_FROM_COMMON_RECEIPT")
    if kind == "native" and (doc.get("independent_oos") is not False or doc.get("actual_exchange_fills") is not False):
        raise ValueError("FALSE_PROOF_FROM_NATIVE_RECEIPT")
    return path, doc


def ledger(path):
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"open_t", "close_t", "entry_price", "exit_price", "qty",
                    "entry_fees", "exit_fee", "funding", "net_pnl", "price_pnl",
                    "exit_year", "notional_return_pct"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("ORIGINAL_TRADE_CSV_SCHEMA_MISSING")
        rows = list(reader)
    if not rows:
        raise ValueError("EMPTY_TRADE_LEDGER")
    parsed = []
    for i, r in enumerate(rows):
        open_t, close_t = int(r["open_t"]), int(r["close_t"])
        if not (START_MS <= open_t < close_t <= END_MS):
            raise ValueError(f"INVALID_OR_OUTSIDE_HISTORY:{i}")
        d = {k: f(r[k], k) for k in required if k not in {"open_t", "close_t", "exit_year"}}
        if d["qty"] <= 0 or d["entry_price"] <= 0 or d["exit_price"] <= 0:
            raise ValueError("BAD_TRADE_QUANTITY_OR_PRICE")
        if d["entry_fees"] < 0 or d["exit_fee"] < 0:
            raise ValueError("BAD_FEE_SIGN")
        recon = d["price_pnl"] - d["entry_fees"] - d["exit_fee"] + d["funding"]
        if not math.isclose(d["net_pnl"], recon, abs_tol=1e-5, rel_tol=1e-9):
            raise ValueError(f"TRADE_CASH_IDENTITY_BROKEN:{i}")
        yr = datetime.fromtimestamp((close_t-1)/1000, tz=timezone.utc).year
        if int(r["exit_year"]) != yr:
            raise ValueError("YEAR_OF_CLOSED_TRADE_MISMATCH")
        if parsed and open_t < parsed[-1]["close_t"]:
            raise ValueError("REENTRANT_POSITION_IN_ONE_SLOT")
        d.update({"open_t": open_t, "close_t": close_t, "exit_year": yr,
                  "entry_notional": d["entry_price"] * d["qty"],
                  "hold_days": (close_t-open_t)/86400000.})
        parsed.append(d)
    return {"sha256": sha, "rows": parsed}


def analyze_one(name, source_path, model, path):
    data = ledger(path)
    rows = data["rows"]
    if len(rows) != model["closed_trades"]:
        raise ValueError("CLOSED_TRADE_COUNT_MISMATCH")
    net = sum(z["net_pnl"] for z in rows)
    profits = sorted((z["net_pnl"] for z in rows if z["net_pnl"] > 0), reverse=True)
    negative = sum(z["net_pnl"] for z in rows if z["net_pnl"] < 0)
    if len(profits) != model["wins"]:
        raise ValueError("WIN_COUNT_MISMATCH")
    if not math.isclose(net - sum(profits[:3]), model["removed_3_biggest_net_pnl_sum_usdt"], abs_tol=2e-4):
        raise ValueError("TOP_THREE_CANONICAL_LEDGER_MISMATCH")
    by_year = {}
    for yr in (2023, 2024, 2025):
        x = [z for z in rows if z["exit_year"] == yr]
        pnl = sum(z["net_pnl"] for z in x)
        original = float(model.get("annual_closed_trade_pnl_usdt", {}).get(str(yr), 0))
        if not math.isclose(pnl, original, abs_tol=2e-4):
            raise ValueError(f"YEAR_PNL_IDENTITY_MISMATCH:{yr}")
        by_year[str(yr)] = {"closed": len(x), "wins": sum(z["net_pnl"] > 0 for z in x),
                            "net_closed_pnl_usdt": round(pnl, 6)}
    streak = best = 0
    for z in rows:
        streak = 0 if z["net_pnl"] > 0 else streak+1
        best = max(best, streak)
    notional = sum(z["entry_notional"] for z in rows)
    costs = {}
    for bps in EXTRA_BPS:
        new = [z["net_pnl"]-z["entry_notional"]*bps/10000 for z in rows]
        costs[f"EXTRA_{bps}_BPS"] = {"closed_static_net_usdt": round(sum(new), 6),
                                    "positive_trades": sum(v > 0 for v in new)}
    # Fee *savings* is NOT venue backtest or valid trading counterfactual.
    hypothetical = sum(z["net_pnl"]+z["entry_notional"]*6/10000 for z in rows)
    return {
        "candidate": name, "cost": path.name.split("_")[-2] if "_" in path.name else "UNKNOWN",
        "input_result_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "input_trade_csv_sha256": data["sha256"], "closed_trades": len(rows),
        "wins": len(profits), "losses": len(rows)-len(profits),
        "closed_net_usdt_original": round(net, 6),
        "terminal_marked_return_pct_model": model["marked_return_pct"],
        "terminal_open_position": model["end_position_open"],
        "modeled_dd_pct": model["max_5m_low_stress_dd_pct"],
        "profit_factor": model["profit_factor"],
        "annual": by_year, "worst_consecutive_nonwinning_closes": best,
        "max_holding_days": round(max(z["hold_days"] for z in rows), 3),
        "top1_gross_winner_share_pct": round(100*sum(profits[:1])/sum(profits), 4),
        "top3_gross_winner_share_pct": round(100*sum(profits[:3])/sum(profits), 4),
        "top5_gross_winner_share_pct": round(100*sum(profits[:5])/sum(profits), 4),
        "remaining_closed_pnl_after_static_top3_usdt": round(net-sum(profits[:3]), 6),
        "total_original_entry_notional_usdt": round(notional, 6),
        "funding_in_closed_trades_usdt": round(sum(z["funding"] for z in rows), 6),
        "entry_exit_fees_in_closed_trades_usdt": round(sum(z["entry_fees"]+z["exit_fee"] for z in rows), 6),
        "static_extra_roundtrip_cost_scenarios": costs,
        "hypothetical_static_6bps_fee_saving_closed_pnl_usdt_NOT_VENUE_REPLAY": round(hypothetical,6),
        "ALPHA_OOS_CREDIT": "ZERO",
        "TRADING_AUTHORITY": "NONE"
    }, rows


def intersect(a, b):
    return a["open_t"] < b["close_t"] and b["open_t"] < a["close_t"]


def overlap_report(lanes):
    names = [c[0] for c in CANDIDATES]
    pairs = []
    for i, left in enumerate(names):
        for right in names[i+1:]:
            aa, bb = lanes[left], lanes[right]
            overlaps = [(x, y) for x in aa for y in bb if intersect(x, y)]
            pairs.append({"a": left, "b": right, "overlap_pairs": len(overlaps),
                          "unique_a_trades_overlapped": len({x["open_t"] for x,y in overlaps}),
                          "unique_b_trades_overlapped": len({y["open_t"] for x,y in overlaps}),
                          "same_underlying": left.startswith("SOL") and right.startswith("SOL")})
    edges = []
    for name, rows in lanes.items():
        for row in rows:
            edges.extend([(row["open_t"], 1, name), (row["close_t"], -1, name)])
    edges.sort(key=lambda z: (z[0], z[1]))  # close at T before open at T
    active = 0
    max_active = 0
    for t, delta, name in edges:
        active += delta
        max_active = max(max_active, active)
    if active != 0:
        raise ValueError("UNCLOSED_OVERLAP_EVENTS")
    return {"pairs": pairs, "max_simultaneously_open_on_separate_paper_ledgers": max_active,
            "WARNING": "No new shared-account portfolio or reliable joint DD is computed."}


def audit(common_root: Path, native_root: Path):
    out = []
    base_lanes = {}
    for name, sym, tf, kind in CANDIDATES:
        root = common_root if kind == "common" else native_root
        path, doc = load_source(root, sym, kind)
        for cost in ("BASE", "STRESS"):
            model = doc["model"][tf+"_"+cost] if kind == "common" else doc["models"][cost]
            csvpath = path.parent / (tf+"_"+cost+"_TRADES.csv" if kind=="common" else cost+"_TRADES.csv")
            if not csvpath.is_file():
                raise ValueError("MISSING_ORIGINAL_TRADE_CSV:"+str(csvpath))
            report, rows = analyze_one(name, path, model, csvpath)
            report["cost"] = cost
            out.append(report)
            if cost == "BASE":
                base_lanes[name] = rows
    if len(out) != 6:
        raise ValueError("EXPECTED_ALL_SIX_ARMS")
    return {"status": "COMPLETE_RETROSPECTIVE_HISTORICAL_ADVERSARIAL_NOT_OOS",
            "frozen_protocol": "PRE_LEDGER_OUTCOME_FREEZE_2026_10_17.md",
            "exact_original_runs": [38432883246, 38435206427],
            "models": out, "simultaneous_exposure": overlap_report(base_lanes),
            "cross_venue_actual_historical_bbo": "NOT_SUPPLIED",
            "historical_foreign_venue_exact_funding": "NOT_SUPPLIED",
            "original_nonlatched_stop_broker_ack": "NOT_PROVEN",
            "independent_OOS": False, "trading_authority": "NONE"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--common-source", type=Path, required=True)
    p.add_argument("--native-source", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    d = audit(args.common_source,args.native_source)
    (args.output_dir/"HISTORICAL_ADVERSARIAL_6_ARMS.json").write_text(
        json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for row in d["models"]:
        print("ADVERSARIAL_RESULT",json.dumps({
            k:row[k] for k in ("candidate","cost","closed_trades","closed_net_usdt_original",
                "terminal_marked_return_pct_model","annual",
                "remaining_closed_pnl_after_static_top3_usdt",
                "worst_consecutive_nonwinning_closes","static_extra_roundtrip_cost_scenarios")
        },sort_keys=True),flush=True)
    print("SIMULTANEOUS_EXPOSURE",json.dumps(d["simultaneous_exposure"],sort_keys=True))
    print("VERDICT","HISTORICAL_ONLY_NO_OOS_NO_LIVE_GO")


if __name__=="__main__":
    main()
