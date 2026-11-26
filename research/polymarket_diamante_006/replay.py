"""Frozen October snapshot taker study. Run from the evidence directory."""
import argparse
import hashlib
import itertools
import json
import math
from collections import Counter
from heapq import heappop, heappush
from pathlib import Path

import duckdb

parser = argparse.ArgumentParser()
parser.add_argument("--holdout", action="store_true")
parser.add_argument("--asof", action="store_true")
args = parser.parse_args()
if args.asof and args.holdout:
    parser.error("Exploratory as-of replay cannot open holdout labels.")
DB = duckdb.connect(config={"threads": 4, "TimeZone": "UTC"})
DB.execute("CREATE VIEW source AS SELECT * FROM 'btc.parquet'")
FEE = 0.07
CAPITALS = (100, 250, 500, 1000, 5000)
STRESS = {"base": (500, 0.005, 0.25, 900000), "stress": (1000, 0.01, 0.10, 1800000)}
SIGNALS = ("clock", "reversal", "imbalance", "combined")
TIMES = (30, 90, 150)

def markets(first, last):
    if args.asof:
        return DB.execute("""
            WITH source_rows AS (
                SELECT market_slug, epoch_ms(market_end_at)-300000 AS opened,
                       epoch_ms(captured_at) AS ts, lower(outcome) AS side, best_bid, best_ask,
                       list_sum(list_slice(bid_sizes,1,3)) AS bid3,
                       list_sum(list_slice(ask_sizes,1,3)) AS ask3, ask_sizes[1] AS qty, crossed
                FROM source
                WHERE (market_end_at - INTERVAL 5 MINUTE)::DATE BETWEEN ?::DATE AND ?::DATE
                QUALIFY count(*) OVER (PARTITION BY market_slug, ts, side) = 1
            ), grid AS (
                SELECT market_slug, opened, opened+offset_ms AS ts
                FROM (SELECT DISTINCT market_slug,opened FROM source_rows),
                     range(0,300000,250) AS offsets(offset_ms)
            ), synchronized AS (
                SELECT g.market_slug, g.opened, g.ts, u.ts AS up_ts, d.ts AS down_ts,
                      u.best_bid, u.best_ask, u.bid3, u.ask3, u.qty,
                      d.best_ask AS down_ask, d.qty AS down_qty,
                      d.best_bid AS down_bid, u.crossed OR d.crossed AS crossed
                FROM grid g
                ASOF JOIN (SELECT * FROM source_rows WHERE side='up') u
                    ON g.market_slug=u.market_slug AND g.ts>=u.ts
                ASOF JOIN (SELECT * FROM source_rows WHERE side='down') d
                    ON g.market_slug=d.market_slug AND g.ts>=d.ts
            )
            SELECT market_slug, opened, ts-opened, best_bid,best_ask,bid3,ask3,qty,down_ask,down_qty
            FROM synchronized WHERE ts-up_ts<=1000 AND ts-down_ts<=1000 AND NOT crossed
              AND best_ask>0 AND best_ask<1 AND best_bid>0 AND best_bid<=best_ask AND qty>0
              AND down_ask>0 AND down_ask<1 AND down_bid>0 AND down_bid<=down_ask AND down_qty>0
            ORDER BY opened, market_slug, ts
        """, [first,last]).fetchall()
    return DB.execute("""
        WITH rows AS (
            SELECT market_slug, epoch_ms(market_end_at)-300000 AS opened,
                   epoch_ms(captured_at) AS ts, lower(outcome) AS side, best_bid, best_ask,
                   list_sum(list_slice(bid_sizes,1,3)) AS bid3,
                   list_sum(list_slice(ask_sizes,1,3)) AS ask3, ask_sizes[1] AS qty
            FROM source WHERE (market_end_at - INTERVAL 5 MINUTE)::DATE BETWEEN ?::DATE AND ?::DATE
                AND NOT crossed AND best_ask > 0 AND best_ask < 1 AND best_bid > 0
                AND best_bid <= best_ask AND ask_sizes[1] > 0
        ), clean AS (
            SELECT * FROM rows QUALIFY count(*) OVER (PARTITION BY market_slug, ts, side) = 1
        )
        SELECT u.market_slug, u.opened, u.ts-u.opened, u.best_bid, u.best_ask,
               u.bid3, u.ask3, u.qty, d.best_ask, d.qty
        FROM clean u JOIN clean d USING (market_slug, opened, ts)
        WHERE u.side='up' AND d.side='down' AND u.ts>=u.opened AND u.ts<u.opened+300000
        ORDER BY u.opened,u.market_slug,u.ts
    """, [first, last]).fetchall()

def labels(first, last):
    rows = DB.execute("""
        SELECT market_slug, string_agg(DISTINCT lower(winner), '|'),
               count(*) FILTER (WHERE winner IS NULL)
        FROM source WHERE (market_end_at - INTERVAL 5 MINUTE)::DATE BETWEEN ?::DATE AND ?::DATE
        GROUP BY market_slug
    """, [first, last]).fetchall()
    return {slug: {"yes":0, "up":0, "no":1, "down":1}[winner]
            for slug,winner,nulls in rows if winner in ("yes","no","up","down") and not nulls}

def unit_cost(price, slip):
    return min(1, price + slip) + FEE * price * (1-price)

def book_cost(row, side, slip):
    return unit_cost(row[4 if side == 0 else 8], slip)

def market_orders(slug, rows, time, name, friction, cash):
    latency, slip, haircut, _ = friction
    by_time = {row[2]: row for row in rows}
    now = time*1000
    current = by_time.get(now)
    earlier = by_time.get(now-10000)
    if current is None or earlier is None:
        return "no_data", None
    if any(by_time.get(t) is None for t in range(now-10000, now+1, 250)):
        return "no_data", None
    if name == "clock":
        side = hashlib.sha256(slug.encode()).digest()[0] % 2
    else:
        delta = ((current[3]+current[4])-(earlier[3]+earlier[4]))/2
        total_depth = current[5]+current[6]
        imbalance = (current[5]-current[6])/total_depth if total_depth else 0
        rev = (0 if delta < 0 else 1) if abs(delta) >= 0.04 else None
        imb = (0 if imbalance > 0 else 1) if abs(imbalance) >= 0.25 else None
        side = {"reversal": rev, "imbalance": imb, "combined": rev if rev == imb else None}[name]
    if side is None:
        return "no_signal", None
    arrival = by_time.get(now+latency) or by_time.get(now+latency+250)
    if arrival is None:
        return "unfilled", None
    first_cost = book_cost(arrival, side, slip)
    adverse_limit = book_cost(current, side, slip)+slip
    if first_cost > adverse_limit:
        return "unfilled", None
    target = min(0.05*cash/adverse_limit, 0.10*cash)
    quantity = min(target, haircut*arrival[7 if side == 0 else 9])
    if quantity <= 0:
        return "unfilled", None
    cost = quantity*first_cost
    hedge = 0.0
    opposite = 1-side
    next_order = arrival[2]+250
    for row in rows:
        stamp = row[2]
        if stamp < next_order or first_cost+book_cost(row, opposite, slip) > 0.995:
            continue
        # A sampled level must refresh before its displayed liquidity can be reused.
        check = by_time.get(stamp+latency) or by_time.get(stamp+latency+250)
        next_order = stamp+latency+250
        if check is None:
            continue
        price = book_cost(check, opposite, slip)
        if first_cost+price > 0.995:
            continue
        filled = max(0, min(quantity-hedge, haircut*check[7 if opposite==0 else 9], (cash-cost)/price))
        hedge += filled
        cost += filled*price
        # One IOC hedge per market after first executable hedge. Remaining quantity settles unhedged.
        if filled > 0:
            break
    return "filled", (side, quantity, hedge, cost)

def run(grouped, winners, capital, signal, time, scenario):
    free = float(capital)
    reserve = []
    counters = Counter()
    pnl = locked = payout_total = cost_total = unmatched = paired = max_locked = 0.0
    worst_market = 0.0
    details = []
    for slug, rows in grouped:
        opened = rows[0][1]
        while reserve and reserve[0][0] <= opened:
            _, invested, proceeds = heappop(reserve)
            locked -= invested
            free += proceeds
        status, order = market_orders(slug, rows, time, signal, STRESS[scenario], free)
        counters[status] += 1
        if order is None:
            continue
        if slug not in winners:
            raise ValueError(f"Missing settlement for an entered market: {slug}")
        side, qty, hedge, cost = order
        payout = qty if winners[slug] == side else hedge
        pnl += payout-cost
        max_locked = max(max_locked, locked+cost)
        worst_market = min(worst_market, payout-cost)
        locked += cost
        free -= cost
        payout_total += payout
        cost_total += cost
        paired += hedge
        unmatched += qty-hedge
        counters["full_hedge" if qty-hedge < 1e-8 else "partial_hedge" if hedge else "zero_hedge"] += 1
        heappush(reserve, (opened+300000+STRESS[scenario][3], cost, payout))
        details.append(dict(slug=slug, first_side=side, first=qty, paired=hedge, cost=cost, payout=payout))
    return dict(pnl=pnl, counters=dict(counters), max_locked=max_locked, worst_market=worst_market,
                paired=paired, unmatched=unmatched, cost=cost_total, payout=payout_total, details=details)

def phase(first, last, candidates):
    book = markets(first, last)
    grouped = [(slug, list(rows)) for slug,rows in itertools.groupby(book,key=lambda row:row[0])]
    outcomes = labels(first,last)
    results = {}
    for signal,time in candidates:
        for c in CAPITALS:
            for s in STRESS:
                results[f"{signal}:{time}:{c}:{s}"] = run(grouped,outcomes,c,signal,time,s)
    return results

candidates = list(itertools.product(SIGNALS,TIMES))
discovery = phase("2026-10-03","2026-10-03",candidates)
validation = phase("2026-10-04","2026-10-04",candidates)
passed = []
for signal,time in candidates:
    if signal=="clock":
        continue
    keys = [f"{signal}:{time}:500:{s}" for s in STRESS]
    if all(discovery[k]["pnl"] > 0 and validation[k]["pnl"] > 0
           and validation[k]["counters"].get("filled",0)>=30
           and validation[k]["pnl"] >= validation[f"clock:{time}:500:{k.split(':')[-1]}"]["pnl"]
           for k in keys):
        passed.append((signal,time))
result = dict(discovery=discovery, validation=validation, passed=passed, holdout=None)
if args.holdout and passed:
    result["holdout"] = phase("2026-10-05","2026-10-06",passed)
Path("asof_replay.json" if args.asof else "replay.json").write_text(json.dumps(result,separators=(",",":"))+"\n")
