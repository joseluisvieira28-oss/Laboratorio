#!/usr/bin/env python3
"""One-shot PUBLIC MEXC ETH/SOL source and hypothetical $500 size gate.

No candle outcomes, authenticated APIs, order endpoints, wallets, balances or trading.
Source PASS never equals executable fill, future profits or leverage approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from research.mexc_convex_gateway_v01 import mexc_causal_gateway as src
from research.mexc_convex_ethsol_4r_v01 import model

SYMBOLS = ("ETH_USDT", "SOL_USDT")
OUTPUT_PATH = Path("research/mexc_convex_ethsol_4r_v01/SOURCE_CAPITAL_RECEIPT.json")


def one_shot():
    report = {
        "experiment": "MEXC-CONVEX-ETHSOL-4R-001",
        "version": "SOURCE_CAPITAL_GATE_V0_1",
        "run_commit": os.environ.get("GITHUB_SHA"),
        "started_utc": src.utc(),
        "source_only": True,
        "account_access": False,
        "actual_balance_read": False,
        "orders": False,
        "trading": False,
        "funding_observed": False,
        "leverage_certified": False,
        "profitability_tested": False,
        "scorable_forward_trades": 0,
        "hypothetical_equity_usdt": "500",
        "fee_taker_side": str(model.FEE),
        "fees_derived_from": "locked experimental MEXC API fee assumption, NOT public detail's fee field",
        "symbols": {},
        "raw_public_get_receipts": [],
        "errors": [],
    }
    try:
        server_ms, receipt = src.fetch("/api/v1/contract/ping")
        report["raw_public_get_receipts"].append(receipt)
        midpoint = (receipt["request_ms"] + receipt["receipt_ms"]) // 2
        skew_ms = int(server_ms) - midpoint
        report["server_clock_offset_ms"] = skew_ms
        if abs(skew_ms) > 1000 or receipt["latency_ms"] > 2000:
            raise ValueError("CLOCK_OR_PING_BLOCKED")
        for symbol in SYMBOLS:
            entry = {"status": "SOURCE_BLOCKED", "receipts": []}
            report["symbols"][symbol] = entry
            try:
                contract_raw, cm = src.fetch(
                    "/api/v1/contract/detail", {"symbol": symbol})
                entry["receipts"].append(cm)
                info = src.contract(contract_raw, symbol)
                entry["contract_public"] = {k: str(v) for k, v in info.items()}
                if info["apiAllowed"] is not True:
                    raise ValueError("API_NOT_ALLOWED_PUBLIC_METADATA")
                observed_before_book = src.now_ms()
                depth_raw, bm = src.fetch(
                    "/api/v1/contract/depth/" + symbol, {"limit": 20})
                entry["receipts"].append(bm)
                book = src.depth(depth_raw, bm, info, observed_before_book)
                entry["public_quote"] = {
                    "best_bid": book["best_bid"],
                    "best_ask": book["best_ask"],
                    "spread_bps": book["spread_bps"],
                    "quote_age_ms": book["quote_age_ms"],
                    "exchange_timestamp_ms": book["snapshot_exchange_ms"],
                    "depth_50_usdt": book["scenarios"]["50"],
                }
                if book["scenarios"]["50"]["status"] != "QUOTE_SIZE_SAMPLE_PASS":
                    raise ValueError("50_USDT_DEPTH_SOURCE_BLOCKED")
                size = model.risk_limited_contracts(
                    500, book["best_ask"],
                    info["contractSize"], info["minVol"],
                    info["volUnit"], info["maxVol"],
                    current_open_planned_risk_usdt=0)
                entry["risk_limited_size"] = size
                if size["status"] != "HYPOTHETICAL_SIZE_PASS":
                    raise ValueError(size["status"])
                # Planned <=30.07169 notional and independently sized $50 book depth is a
                # source proxy ONLY; contract fill restrictions and 24/7 books unverified.
                entry["status"] = "PUBLIC_SOURCE_HYPOTHETICAL_SIZE_PASS"
            except Exception as exc:
                entry["reason"] = type(exc).__name__ + ":" + str(exc)
                report["errors"].append(symbol + ":" + entry["reason"])
    except Exception as exc:
        report["errors"].append("GLOBAL:" + type(exc).__name__ + ":" + str(exc))
    report["completed_utc"] = src.utc()
    report["classification"] = (
        "SOURCE_CAPITAL_GATE_PASS_DIAGNOSTIC"
        if not report["errors"] and len(report["symbols"]) == len(SYMBOLS)
           and all(z.get("status") == "PUBLIC_SOURCE_HYPOTHETICAL_SIZE_PASS"
                   for z in report["symbols"].values())
        else "SOURCE_CAPITAL_GATE_BLOCKED"
    )
    report["authority"] = ("NO_PROSPECTIVE_FORWARD_ACTIVATION / "
                           "NO_REAL_EXECUTION_OR_PROFIT_PROMOTION")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "classification": report["classification"],
        "errors": report["errors"],
        "symbols": {k: {
            "status": v.get("status"),
            "reason": v.get("reason"),
            "hypothetical_size": v.get("risk_limited_size", {}).get("status"),
            "contracts": v.get("risk_limited_size", {}).get("contracts"),
            "notional": v.get("risk_limited_size", {}).get("notional_usdt"),
            "planned_risk": v.get("risk_limited_size", {}).get("planned_stop_risk_usdt"),
            "quote_age_ms": v.get("public_quote", {}).get("quote_age_ms")}
            for k, v in report["symbols"].items()},
        "scorable_forward_trades": 0,
        "orders": False,
    }, indent=2))
    return report["classification"]


if __name__ == "__main__":
    if one_shot() != "SOURCE_CAPITAL_GATE_PASS_DIAGNOSTIC":
        raise SystemExit(2)
