"""CONVEX V04 — frozen static L1 depth frontier, immutable V03C receipts only.

Pure stdlib. No API, market downloads, credential, orders, 2026 data, backtest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED = {"SOLUSDT": 33, "BNBUSDT": 6}
TIERS = ("0.25", "0.50", "0.75", "1.00")
FRESH = {"BOOK_QUOTE_CAUSAL_CANDIDATE", "TOP_OF_BOOK_SIZE_INSUFFICIENT"}
VALID = FRESH | {"SOURCE_NO_PRIOR_QUOTE", "QUOTE_2S_TO_10S_SENSITIVITY_ONLY",
                 "SOURCE_STALE_OVER_10S", "SOURCE_STILL_BLOCKED"}
COVERAGE_GATE = Decimal("0.95")
SIZE_GATE = Decimal("0.90")

def pos(value, label):
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("BAD_DECIMAL_" + label) from exc
    if not v.is_finite() or v <= 0:
        raise ValueError("NONPOSITIVE_" + label)
    return v

def analyze_receipt(doc, symbol, raw_sha256):
    if symbol not in EXPECTED:
        raise ValueError("UNREGISTERED_SYMBOL")
    if not isinstance(doc, dict) or doc.get("symbol") != symbol:
        raise ValueError("WRONG_ORIGINAL_RECEIPT")
    total = EXPECTED[symbol]
    checks = doc.get("all_entry_checks")
    if not isinstance(checks, list) or len(checks) != total or doc.get("full_population") != total:
        raise ValueError("INCOMPLETE_POPULATION")
    if (doc.get("source_original_run") != 38432883246
        or doc.get("source_v03b_run") != 39026521571
        or doc.get("trading_authority") != "NONE"
        or doc.get("protected_2026_opened") is not False
        or doc.get("cross_venue_execution_proven") is not False
        or doc.get("broker_native_stop_proven") is not False):
        raise ValueError("MISREPRESENTED_SOURCE_OR_AUTHORITY")
    if not doc.get("original_ledger_sha256") or not doc.get("source_v03b_receipt_sha256"):
        raise ValueError("NO_CUSTODY_FINGERPRINT")
    counts = Counter()
    times = set()
    fresh = []
    for x in checks:
        if not isinstance(x, dict) or x.get("symbol") != symbol:
            raise ValueError("CHECK_WRONG_SYMBOL")
        when = x.get("entry_utc")
        if not isinstance(when, str) or when in times:
            raise ValueError("BAD_OR_DUPLICATE_ENTRY")
        times.add(when)
        status = x.get("status")
        if status not in VALID:
            raise ValueError("UNRECOGNIZED_SOURCE_STATUS_" + str(status))
        counts[status] += 1
        if status in FRESH:
            age = x.get("quote_age_ms")
            if type(age) is not int or age < 0 or age > 2000:
                raise ValueError("FRESH_QUOTE_AGE_INVALID")
            ask_qty = pos(x.get("book_ask_qty"), "ASK_QTY")
            required_qty = pos(x.get("modeled_trade_qty"), "ORIGINAL_QTY")
            ask_price = pos(x.get("best_ask"), "ASK_PRICE")
            bid_price = pos(x.get("best_bid"), "BID_PRICE")
            if bid_price >= ask_price:
                raise ValueError("CROSSED_BOOK")
            bps = Decimal(str(x.get("ask_vs_modeled_entry_bps")))
            if not bps.is_finite():
                raise ValueError("BAD_BPS")
            fraction = ask_qty / required_qty
            if (status == "BOOK_QUOTE_CAUSAL_CANDIDATE") != (fraction >= 1):
                raise ValueError("ORIGINAL_FULL_SIZE_LABEL_CONTRADICTION")
            fresh.append({"fraction": fraction, "age": age, "quote_delta_bps": bps})
    if dict(sorted(counts.items())) != doc.get("new_status_counts"):
        raise ValueError("PUBLISHED_STATUS_COUNTS_DISAGREE")
    n = len(fresh)
    if not n:
        raise ValueError("NO_FRESH_SOURCE_OBSERVATIONS")
    if not (Decimal(n)/Decimal(total) >= COVERAGE_GATE) == (Decimal(str(doc.get("fresh_quote_fraction"))) >= COVERAGE_GATE):
        raise ValueError("SOURCE_FRESH_COVERAGE_CONTRADICTION")
    for f in fresh:
        if f["fraction"] <= 0:
            raise ValueError("IMPOSSIBLE_DEPTH_RATIO")
    tiers = []
    for t in TIERS:
        scale = Decimal(t)
        sufficient = sum(row["fraction"] >= scale for row in fresh)
        frac = Decimal(sufficient) / Decimal(n)
        source_ok = Decimal(n)/Decimal(total) >= COVERAGE_GATE
        tiers.append({
            "modeled_equity_notional_fraction_if_static": str(scale * Decimal("0.20")),
            "original_size_ratio": t,
            "fresh_sufficient_count": sufficient,
            "fresh_denominator": n,
            "all_original_denominator": total,
            "fresh_sufficiency_rate": str(frac),
            "source_coverage_gate_pass": source_ok,
            "frozen_single_best_ask_capacity_gate_pass": frac >= SIZE_GATE,
            "conditional_L1_screen_pass_not_execution": bool(source_ok and frac >= SIZE_GATE),
        })
    eligible = [v for v in tiers if v["conditional_L1_screen_pass_not_execution"]]
    # Explicitly descriptive and not optimized; no real strategy/position size promoted.
    return {
        "classification": "RETROSPECTIVE_ORIGINAL_V5_BINANCE_L1_CAPACITY_ONLY",
        "symbol": symbol,
        "original_run": 38432883246,
        "v03c_run": 39027126160,
        "v03c_receipt_sha256": raw_sha256,
        "original_ledger_sha256": doc["original_ledger_sha256"],
        "source_v03b_receipt_sha256": doc["source_v03b_receipt_sha256"],
        "full_population": total,
        "fresh_causal_quote_count": n,
        "source_coverage_fraction": str(Decimal(n)/Decimal(total)),
        "source_nonfresh_status_counts": dict(sorted((k,v) for k,v in counts.items() if k not in FRESH)),
        "original_full_20pct_equity_best_ask_capacity_count": sum(z["fraction"] >= 1 for z in fresh),
        "frozen_size_tiers": tiers,
        "largest_predeclared_tier_passing_source_only": eligible[-1]["original_size_ratio"] if eligible else None,
        "single_level_quote_is_not_a_guaranteed_fill": True,
        "new_backtest_or_pnl_computed": False,
        "cross_venue_execution_proven": False,
        "protected_2026_opened": False,
        "broker_stop_ack_verified": False,
        "independent_economic_OOS": False,
        "trading_authority": "NONE",
    }

def run(root):
    rows=[]
    for symbol in EXPECTED:
        files=list((root/symbol).rglob("V03C_STREAMING_SOURCE_CAP_REMEDIATION.json"))
        if len(files)!=1:
            raise ValueError("EXPECTED_EXACT_SOURCE_V03C_ARTIFACT_"+symbol+":"+str(len(files)))
        f=files[0]
        rows.append(analyze_receipt(json.loads(f.read_text(encoding="utf-8")), symbol,
                    hashlib.sha256(f.read_bytes()).hexdigest()))
    return {"status":"V04_HISTORICAL_L1_SIZE_FRONTIER_ONLY_NOT_ALPHA",
            "source_git_actions_run":39027126160,
            "population":39,
            "rows":rows,
            "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    d=run(a.source_dir)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"CONVEX_V04_HISTORICAL_L1_CAPACITY_FRONTIER.json").write_text(
        json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for row in d["rows"]:
        print("V04_CAPACITY_RESULT",json.dumps({
            "symbol":row["symbol"],
            "fresh":row["fresh_causal_quote_count"],
            "full":row["full_population"],
            "tiers":row["frozen_size_tiers"],
            "largest_predeclared_tier_passing_source_only":row["largest_predeclared_tier_passing_source_only"]
        },sort_keys=True))
    print("V04_VERDICT",d["status"],"NO_LIVE_GO")

if __name__=="__main__":
    main()
