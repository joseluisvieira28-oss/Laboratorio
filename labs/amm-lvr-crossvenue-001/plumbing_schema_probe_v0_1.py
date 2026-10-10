from __future__ import annotations

import csv, io, json, pathlib, urllib.request, zipfile
from collections import Counter

OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

DEX_URL = "https://raw.githubusercontent.com/tivas-g/Wu_Comparing_CEX_DEX_Execution/main/cexdex_data_sample_20230808.csv"
BBO_URL = "https://data.binance.vision/data/futures/um/daily/bookTicker/ETHUSDT/ETHUSDT-bookTicker-2023-08-08.zip"

def read_url(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-AMM-LVR-001-plumbing/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

dex_raw=read_url(DEX_URL)
dex_reader=csv.DictReader(io.StringIO(dex_raw.decode("utf-8-sig")))
dex_rows=list(dex_reader)
relevant=[r for r in dex_rows if {str(r.get("token_bought_symbol","")).upper(),str(r.get("token_sold_symbol","")).upper()}=={"WETH","USDT"}]

bbo_zip=read_url(BBO_URL)
with zipfile.ZipFile(io.BytesIO(bbo_zip)) as z:
    names=z.namelist()
    raw=z.read(names[0])
text=raw.decode("utf-8-sig")
bbo_reader=csv.reader(io.StringIO(text))
first_rows=[]
for i,row in enumerate(bbo_reader):
    first_rows.append(row)
    if i>=4: break

probe={
  "lab_id":"AMM-LVR-CROSSVENUE-001",
  "phase":"PLUMBING_SCHEMA_PROBE_V0.1",
  "dex_rows_total":len(dex_rows),
  "dex_columns":dex_reader.fieldnames,
  "weth_usdt_rows":len(relevant),
  "weth_usdt_first_rows":[{k:r.get(k) for k in [
      "block_number","block_time","tx_hash","mev_bot_label","base_fees","priority_fees",
      "cb_transfer","mev_value","volume","token_bought_amount","token_sold_amount",
      "token_bought_symbol","token_sold_symbol","pair","multi_trade"
  ]} for r in relevant[:5]],
  "weth_usdt_multi_trade_counts":dict(Counter(str(r.get("multi_trade")) for r in relevant)),
  "bbo_zip_members":names,
  "bbo_first_rows":first_rows,
  "economic_verdict_opened":False,
  "note":"Schema/units probe only. No PnL or edge adjudication."
}
(OUT/"plumbing_schema_probe_v0_1.json").write_text(json.dumps(probe,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(probe,indent=2,sort_keys=True))
if len(relevant)==0 or len(first_rows)<2:
    raise SystemExit(2)
