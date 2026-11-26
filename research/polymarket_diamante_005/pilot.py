"""August 8 source checks and double-taker baseline on a mirrored complementary book."""
import json
from pathlib import Path

import duckdb

db = duckdb.connect(config={"threads": 4, "TimeZone": "UTC"})
db.execute("CREATE VIEW book AS SELECT * FROM 'data/l2-08.parquet'")
db.execute("CREATE VIEW tape AS SELECT * FROM 'data/trades-08.parquet'")
db.execute("CREATE VIEW markets AS SELECT * FROM 'data/markets.parquet' WHERE start_time::DATE = '2026-08-08'")
db.execute("""
CREATE VIEW quotes AS
SELECT b.market_slug, local_timestamp, timestamp, event_type,
       CASE WHEN event_type='book' THEN list_min(ask_prices) ELSE best_ask END AS ask,
       CASE WHEN event_type='book' THEN list_max(bid_prices) ELSE best_bid END AS bid
FROM book b JOIN markets m USING(market_slug)
WHERE event_type IN ('book','price_change')
AND local_timestamp >= start_time::TIMESTAMP AND local_timestamp < end_time::TIMESTAMP
""")
stats = db.sql("""
SELECT count(*), count(DISTINCT market_slug), count(*) FILTER (WHERE ask > 0 AND ask < 1 AND bid > 0 AND bid < 1),
       count(*) FILTER (WHERE bid > ask + 1e-9),
       count(*) FILTER (WHERE bid > ask + 1e-9 AND ask > 0 AND ask < 1 AND bid > 0 AND bid < 1),
       quantile_cont(1000*epoch(local_timestamp-timestamp), [0.5,0.95,0.99]),
       count(*) FILTER (WHERE local_timestamp < timestamp)
FROM quotes
""").fetchall()[0]
fields = ("quote_events", "markets", "two_sided_executable_prices", "crossed_including_sentinels",
          "crossed_executable_prices", "receive_ms_p50_p95_p99", "negative_delay")
result = dict(zip(fields, stats))
result["baseline"] = {
    "rule": "No entry unless simultaneous best ask UP plus best ask DOWN is below 1 before fees. "
            "DOWN ask is 1 minus YES bid under the PMData mirror convention. "
            "This is a simultaneous price gate, with no sequential opportunities evaluated.",
    "capitals": {str(capital): {"entry_candidates": 0, "pnl": 0, "capital_locked": 0}
                 for capital in (100, 250, 500, 1000, 5000)} if stats[4] == 0 else None,
}
for name in ("chainlink_streams", "chainlink_streams_twap60s"):
    summary = db.sql(f"""
    SELECT count(*), count(DISTINCT observationsTimestamp), min(observationsTimestamp)::VARCHAR,
           max(observationsTimestamp)::VARCHAR,
           quantile_cont(1000*epoch(receiveMicrosecondTimestamp-observationsTimestamp), [0.5,0.95,0.99]),
           count(*) FILTER (WHERE receiveMicrosecondTimestamp < observationsTimestamp)
    FROM 'data/{name}-08.parquet'
    """).fetchall()[0]
    result[name] = dict(zip(("rows", "unique_observation_times", "first", "last", "receive_ms_p50_p95_p99",
                             "negative_delay"), summary))
result["trade_messages"] = db.sql("SELECT count(*) FROM tape").fetchall()[0][0]
Path("pilot.json").write_text(json.dumps(result, indent=2) + "\n")
