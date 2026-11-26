"""Read-only verification of actual fees on a stratified sample of Polygon receipts."""
import concurrent.futures
import json
from pathlib import Path
from subprocess import check_output

import duckdb

WALLET = "0x3048d65321be3497164cdfc2996f94f98a2e7537"
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"
TOPIC = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
db = duckdb.connect(config={"threads": 4})
rows = db.sql(f"""
SELECT market_slug, transactionHash, _log_index, taker='{EXCHANGE}' AS aggressive,
       usd_amount, token_amount, price
FROM read_parquet('data/fills-*.parquet',filename=true) WHERE maker='{WALLET}'
QUALIFY row_number() OVER (PARTITION BY filename, aggressive ORDER BY transactionHash, _log_index) <= 2
""").fetchall()

def recover(row):
    slug, tx, index, aggressive, cost, qty, price = row
    payload = json.dumps(dict(jsonrpc="2.0", id=1, method="eth_getTransactionReceipt", params=[tx]))
    item = dict(slug=slug, tx=tx, index=index, aggressive=aggressive, usd=cost, tokens=qty,
                modeled_fee=0.07*qty*price*(1-price) if aggressive else 0.0)
    try:
        data = json.loads(check_output(["curl", "-fsS", "--max-time", "15", "-H",
                                        "Content-Type: application/json", "--data-raw", payload,
                                        "https://polygon.drpc.org"]))["result"]
        log = next(log for log in data["logs"] if int(log["logIndex"], 16) == index)
        assert log["address"] == EXCHANGE and log["topics"][0] == TOPIC
        assert log["topics"][2][-40:] == WALLET[2:]
        assert (log["topics"][3][-40:] == EXCHANGE[2:]) == aggressive
        words = log["data"][2:]
        side, token, maker, taker, fee = [int(words[i:i+64], 16) for i in range(0, 64*5, 64)]
        item.update(block=int(data["blockNumber"], 16), token_id=str(token), fee_units=fee,
                    amount_match=side == 0 and abs(cost-maker/1e6) < 0.001 and abs(qty-taker/1e6) < 0.001)
    except Exception as error:
        item["error"] = str(error)
    return item

with concurrent.futures.ThreadPoolExecutor(10) as executor:
    items = list(executor.map(recover, rows))
Path("fee_sample.json").write_text(json.dumps(items, indent=2) + "\n")
