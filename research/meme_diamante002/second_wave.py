#!/usr/bin/env python3
"""MEME-DIAMANTE-002: offline read-only trade-print proxy. NOT a trading bot."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

PROTOCOL = "MEME-DIAMANTE-002-v0.1-2026-11-18"
P = dict(min_age_s=180, max_age_s=3600, drawdown=.28, bounce=.12,
         max_peak_fraction=.95, window_s=300, min_buyers=8,
         min_address_buy=50., min_buy_share=.65, min_buy_usd=1200.,
         max_buyer_share=.35, min_liq=20000., entry_delay_s=30,
         latest_entry_s=120, stop=.25, take=.30, hold_s=1800,
         fee=.017, slip=.02, fixed_usd=.10, stake_usd=100.)

REQUIRED = ("mint", "timestamp", "tx", "wallet", "side", "price_usd",
            "amount_usd", "liquidity_usd", "source")

def load(path):
    rows, seen = [], set()
    quality = dict(invalid=0, duplicate=0)
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            if any(k not in r for k in REQUIRED) or r["side"] not in ("buy", "sell"):
                raise ValueError("field")
            if not isinstance(r["tx"], str) or not r["tx"] or not r["mint"] or not r["wallet"]:
                raise ValueError("identity")
            if any(not isinstance(r[k], (int, float)) or not math.isfinite(r[k]) for k in
                   ("timestamp", "price_usd", "amount_usd", "liquidity_usd")):
                raise ValueError("numeric")
            if r["timestamp"] <= 0 or r["price_usd"] <= 0 or r["amount_usd"] <= 0 or r["liquidity_usd"] < 0:
                raise ValueError("value")
            key = (r["mint"], r["tx"], r["side"])
            if key in seen:
                quality["duplicate"] += 1
                continue
            seen.add(key)
            rows.append(r)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            quality["invalid"] += 1
    rows.sort(key=lambda r: (r["mint"], r["timestamp"], r["tx"]))
    return rows, quality

def find_signal(trades, p=P):
    if len(trades) < 12:
        return None
    first = trades[0]["timestamp"]
    peak = trough = trades[0]["price_usd"]
    drawn = False
    for i, r in enumerate(trades):
        t, price = r["timestamp"], r["price_usd"]
        age = t-first
        if age > p["max_age_s"]:
            return None
        if not drawn:
            peak = max(peak, price)
            if age >= p["min_age_s"] and price <= peak*(1-p["drawdown"]):
                drawn = True
                trough = price
        else:
            trough = min(trough, price)
            if price < trough*(1+p["bounce"]) or price > peak*p["max_peak_fraction"]:
                continue
            if r["liquidity_usd"] < p["min_liq"]:
                continue
            buys = collections.defaultdict(float)
            buy_usd = sell_usd = 0.
            for h in trades[:i+1]:
                if t-p["window_s"] <= h["timestamp"] <= t:
                    if h["side"] == "buy":
                        buys[h["wallet"]] += h["amount_usd"]
                        buy_usd += h["amount_usd"]
                    else:
                        sell_usd += h["amount_usd"]
            if (sum(v >= p["min_address_buy"] for v in buys.values()) < p["min_buyers"]
                or buy_usd < p["min_buy_usd"]
                or buy_usd/(buy_usd+sell_usd) < p["min_buy_share"]
                or max(buys.values(), default=0)/buy_usd > p["max_buyer_share"]):
                continue
            return dict(mint=r["mint"], at=t, index=i, price=price,
                        peak_asof=peak, trough_asof=trough,
                        address_count=sum(v >= p["min_address_buy"] for v in buys.values()),
                        liquidity=r["liquidity_usd"],
                        caveat="Addresses are not proven distinct persons")
    return None

def simulate(trades, signal, p=P):
    later = trades[signal["index"]+1:]
    start = signal["at"]+p["entry_delay_s"]
    stop = signal["at"]+p["latest_entry_s"]
    entry = next((r for r in later if start <= r["timestamp"] <= stop
                  and r["liquidity_usd"] >= p["min_liq"]), None)
    if not entry:
        return dict(status="ENTRY_UNOBSERVED", net_return_pct=None)
    exit_trade, reason = None, None
    for r in later:
        if r["timestamp"] <= entry["timestamp"]:
            continue
        if r["price_usd"] <= entry["price_usd"]*(1-p["stop"]):
            exit_trade, reason = r, "STOP_PRINT"
            break
        if r["price_usd"] >= entry["price_usd"]*(1+p["take"]):
            exit_trade, reason = r, "TAKE_PRINT"
            break
        if r["timestamp"] >= entry["timestamp"]+p["hold_s"]:
            exit_trade, reason = r, "TIME_PRINT"
            break
    if not exit_trade:
        return dict(status="EXIT_UNOBSERVED", net_return_pct=None)
    if exit_trade["liquidity_usd"] < p["min_liq"]:
        return dict(status="EXIT_LIQUIDITY_BLOCKED", net_return_pct=None)
    units = (p["stake_usd"]*(1-p["fee"]))/(entry["price_usd"]*(1+p["slip"]))
    proceeds = units*exit_trade["price_usd"]*(1-p["slip"])*(1-p["fee"])
    pnl = proceeds-p["stake_usd"]-p["fixed_usd"]
    return dict(status="PRINT_PROXY_ONLY", reason=reason,
                entry_at=entry["timestamp"], exit_at=exit_trade["timestamp"],
                gross_pct=round(100*(exit_trade["price_usd"]/entry["price_usd"]-1),4),
                net_return_pct=round(100*pnl/p["stake_usd"],4))

def analyze(path):
    trades, quality = load(path)
    groups = collections.defaultdict(list)
    for r in trades:
        groups[r["mint"]].append(r)
    results = []
    for mint, tape in sorted(groups.items()):
        sig = find_signal(tape)
        results.append(dict(mint=mint, count=len(tape), signal=sig,
                            proxy=simulate(tape,sig) if sig else None))
    proxy = [r["proxy"] for r in results if r["proxy"]]
    valid = [r["net_return_pct"] for r in proxy if r["status"] == "PRINT_PROXY_ONLY"]
    return dict(protocol=PROTOCOL, source_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                quality=quality, trades=len(trades), tokens=len(groups), signals=len(proxy),
                print_proxy_outcomes=len(valid), censored=len(proxy)-len(valid),
                optimistic_mean_pct=round(sum(valid)/len(valid),4) if valid else None,
                params=P, results=results,
                gate="NO-GO ECONOMIC: prints not quotes; no complete universe, independent exits or controls")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(analyze(args.jsonl), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(report+"\n",encoding="utf-8")
    else:
        print(report)
