"""Offline reconstruction from the pinned PMData Parquets. Usage: python reconstruct.py."""
import csv
import hashlib
import json
import random
from collections import deque
from pathlib import Path
from statistics import quantiles

import duckdb

WALLET = "0x3048d65321be3497164cdfc2996f94f98a2e7537"
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"
db = duckdb.connect(config={"threads": 4, "TimeZone": "UTC"})
db.execute("CREATE VIEW fills AS SELECT * FROM read_parquet('data/fills-*.parquet')")
db.execute("CREATE VIEW markets AS SELECT * FROM 'data/markets.parquet'")
db.execute(f"""
CREATE VIEW wallet AS
SELECT f.*, lower(outcome) AS token, winning_outcome AS winner, start_time::TIMESTAMP AS start_at,
       end_time::TIMESTAMP AS end_at, resolved_received_at,
       taker = '{EXCHANGE}' AS aggressive
FROM fills f JOIN markets m USING (market_slug) WHERE maker = '{WALLET}'
""")

integrity = db.sql("""
SELECT count(*) AS row_count, count(*) - count(DISTINCT (transactionHash, _log_index)) AS duplicate_keys,
       count(*) FILTER (WHERE transactionHash IS NULL OR _log_index IS NULL) AS missing_keys,
       count(*) FILTER (WHERE m.market_slug IS NULL) AS unjoined
FROM fills f LEFT JOIN markets m USING (market_slug)
""").fetchall()[0]
findings = {"integrity": dict(zip(("rows", "duplicate_keys", "missing_keys", "unjoined"), integrity))}
assert integrity[1:] == (0, 0, 0), integrity
assert db.sql("SELECT count(*) FROM markets").fetchall()[0][0] == 4032
wallet_summary = db.sql("""
SELECT count(*), count(DISTINCT market_slug), count(DISTINCT market_slug) FILTER (WHERE winner IS NOT NULL),
       count(*) FILTER (WHERE timestamp < start_at), count(*) FILTER (WHERE timestamp > end_at),
       count(*) FILTER (WHERE maker_side <> 'BUY' OR token NOT IN ('yes', 'no') OR token_amount <= 0)
FROM wallet
""").fetchall()[0]
findings["wallet"] = dict(zip(("rows", "markets", "settled_markets", "before_start", "after_end", "invalid"), wallet_summary))
assert wallet_summary[-1] == 0

records = db.sql("""
SELECT market_slug, start_at::DATE, winner, timestamp, token, usd_amount, token_amount, aggressive, price,
       resolved_received_at
FROM wallet ORDER BY market_slug, timestamp, _log_index, transactionHash
""").fetchall()

def market_result(rows):
    slug, date, winner = rows[0][:3]
    pending = {"yes": deque(), "no": deque()}
    pairs = pair_gross = pair_fee = purchases = fees = payout = 0.0
    qty_seconds = same_second = max_imbalance = max_age = 0.0
    yes = no = 0.0
    roles = [[0.0, 0.0] for _ in range(3)]
    for _, _, _, timestamp, token, cost, qty, aggressive, price, _ in rows:
        purchases += cost
        fee = qty * 0.07 * price * (1 - price) if aggressive else 0.0
        fees += fee
        payout += qty if token == winner else 0.0
        if token == "yes":
            yes += qty
        else:
            no += qty
        max_imbalance = max(max_imbalance, abs(yes - no))
        unit_cost, unit_fee = cost / qty, fee / qty
        opposite = pending["no" if token == "yes" else "yes"]
        while qty > 1e-9 and opposite:
            remaining, other_cost, other_fee, other_time, other_aggressive = opposite[0]
            paired = min(qty, remaining)
            age = (timestamp - other_time).total_seconds()
            pairs += paired
            pair_gross += paired * (1 - unit_cost - other_cost)
            pair_fee += paired * (unit_fee + other_fee)
            role = int(aggressive) + int(other_aggressive)
            roles[role][0] += paired
            roles[role][1] += paired * (1 - unit_cost - other_cost - unit_fee - other_fee)
            qty_seconds += paired * age
            same_second += paired if not age else 0
            max_age = max(max_age, age)
            qty -= paired
            remaining -= paired
            if remaining <= 1e-9:
                opposite.popleft()
            else:
                opposite[0] = (remaining, other_cost, other_fee, other_time, other_aggressive)
        if qty > 1e-9:
            pending[token].append((qty, unit_cost, unit_fee, timestamp, aggressive))
    return dict(slug=slug, date=str(date), winner=winner, wallet_fills=len(rows),
                maker_fills=sum(not row[7] for row in rows), taker_fills=sum(row[7] for row in rows),
                purchases=purchases, modeled_fees=fees, payout=payout if winner else None,
                gross=payout-purchases if winner else None, net=payout-purchases-fees if winner else None,
                pairs=pairs, pair_gross=pair_gross, pair_net=pair_gross-pair_fee,
                pair_qty_seconds=qty_seconds, same_second_pairs=same_second, max_pair_age=max_age,
                max_imbalance=max_imbalance, residual=abs(yes-no),
                pair_mm_qty=roles[0][0], pair_mm_net=roles[0][1],
                pair_mt_qty=roles[1][0], pair_mt_net=roles[1][1],
                pair_tt_qty=roles[2][0], pair_tt_net=roles[2][1])

from itertools import groupby

results = [market_result(list(group)) for _, group in groupby(records, key=lambda r: r[0])]
with open("markets_result.csv", "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

def totals(markets):
    known = [m for m in markets if m["winner"]]
    keys = ("wallet_fills", "maker_fills", "taker_fills", "purchases", "modeled_fees", "payout",
            "gross", "net", "pairs", "pair_gross", "pair_net", "pair_qty_seconds", "same_second_pairs", "pair_mm_qty", "pair_mm_net",
            "pair_mt_qty", "pair_mt_net", "pair_tt_qty", "pair_tt_net")
    result = {key: sum(m[key] for m in known) for key in keys}
    result.update(markets=len(known), missing_winners=len(markets)-len(known),
                  missing_purchases=sum(m["purchases"] for m in markets if not m["winner"]),
                  missing_modeled_fees=sum(m["modeled_fees"] for m in markets if not m["winner"]),
                  missing_min=sum(m["pairs"] for m in markets if not m["winner"]),
                  missing_max=sum(m["pairs"]+m["residual"] for m in markets if not m["winner"]))
    result["residual_net"] = result["net"] - result["pair_net"]
    result["net_margin"] = result["net"] / result["purchases"]
    result["pair_delay_weighted_seconds"] = result["pair_qty_seconds"] / result["pairs"]
    return result

gamma_path = Path("gamma_settlements.json")
if gamma_path.exists():
    official = {row["slug"]: {"up": "yes", "down": "no"}[row["winner"]]
                for row in json.loads(gamma_path.read_text()) if row.get("final")}
    extended = []
    for slug, group in groupby(records, key=lambda row: row[0]):
        rows = list(group)
        if rows[0][2] is None and slug in official:
            rows = [row[:2] + (official[slug],) + row[3:] for row in rows]
        extended.append(market_result(rows))
    findings["gamma_extended"] = totals(extended)
    findings["additional_gamma_pnl"] = findings["gamma_extended"]["net"] - totals(results)["net"]

findings["daily"] = {day: totals(list(group)) for day, group in groupby(results, key=lambda m: m["date"])}
findings["full"] = totals(results)
findings["rows_by_day"] = dict(db.sql("""
SELECT start_time::DATE::VARCHAR, count(*) FROM fills JOIN markets USING(market_slug) GROUP BY 1 ORDER BY 1
""").fetchall())
random_gen = random.Random(5005)
daily = list(findings["daily"].values())
boot = []
for _ in range(10000):
    indices = [random_gen.randrange(len(daily)) for _ in range((len(daily)+1)//2)]
    sample = [daily[(i + delta) % len(daily)] for i in indices for delta in (0, 1)][:len(daily)]
    boot.append(sum(d["net"] for d in sample) / sum(d["purchases"] for d in sample))
percentiles = quantiles(boot, n=1000)
findings["historical_only_two_day_circular_bootstrap_margin_95"] = [percentiles[24], percentiles[974]]
findings["fee_stress_net"] = {str(multiplier): findings["full"]["gross"] - multiplier * findings["full"]["modeled_fees"]
                              for multiplier in (0, 0.5, 1, 1.25, 1.5, 2)}
hashes = {}
for path in sorted(Path("data").glob("*.parquet")):
    with path.open("rb") as file:
        hashes[path.name] = hashlib.file_digest(file, "sha256").hexdigest()
findings["sha256"] = hashes
Path("reconstruction.json").write_text(json.dumps(findings, indent=2) + "\n")
