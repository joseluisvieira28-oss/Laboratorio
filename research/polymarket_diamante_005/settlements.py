"""Recover only catalog gaps from official Gamma, and verify market rules on August 8."""
import concurrent.futures
import json
import subprocess
from pathlib import Path

import duckdb

db = duckdb.connect()
slugs = db.sql("""
SELECT market_slug FROM 'data/markets.parquet' WHERE winning_outcome IS NULL
UNION SELECT 'btc-updown-5m-1786147200'
""").fetchall()

def recover(row):
    slug = row[0]
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
    try:
        market = json.loads(subprocess.check_output(["curl", "-fsSL", "--max-time", "15", url]))
        outcomes = json.loads(market["outcomes"])
        prices = json.loads(market["outcomePrices"])
        final = market.get("umaResolutionStatus") == "resolved" and sorted(map(float, prices)) == [0, 1]
        return dict(slug=slug, condition=market["conditionId"], final=final,
                    winner=outcomes[prices.index(max(prices, key=float))].lower() if final else None,
                    oracle=market.get("resolutionSource"), prices=prices,
                    status=market.get("umaResolutionStatus"), closed=market.get("closed"),
                    rules=market.get("description") if slug.endswith("1786147200") else None)
    except (subprocess.CalledProcessError, ValueError, KeyError) as error:
        return dict(slug=slug, error=str(error))

with concurrent.futures.ThreadPoolExecutor(8) as executor:
    results = list(executor.map(recover, slugs))
Path("gamma_settlements.json").write_text(json.dumps(results, indent=2) + "\n")
