#!/usr/bin/env python3
import csv,hashlib,io,json,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/cclm002_binance_hourly_target_source_v01.json")
BASE="https://data.binance.vision/data/spot/monthly/klines"
SYMS=["AVAXUSDT","BTCUSDT"]
MONTH="2023-05"

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CCLM-002-TargetSource/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r:return r.read()

rows=[]
for sym in SYMS:
    name=f"{sym}-1h-{MONTH}.zip"
    url=f"{BASE}/{sym}/1h/{name}"
    raw=get(url)
    chk=get(url+".CHECKSUM").decode().strip().split()[0].lower()
    sha=hashlib.sha256(raw).hexdigest()
    z=zipfile.ZipFile(io.BytesIO(raw))
    members=z.namelist()
    csv_name=f"{sym}-1h-{MONTH}.csv"
    data=z.read(csv_name).decode()
    parsed=list(csv.reader(io.StringIO(data)))
    # Binance archive may have no header. Keep rows whose first field is numeric.
    data_rows=[r for r in parsed if r and r[0].isdigit()]
    opens=[int(r[0]) for r in data_rows]
    deltas=[b-a for a,b in zip(opens,opens[1:])]
    first=int(datetime(2023,5,1,tzinfo=timezone.utc).timestamp()*1000)
    last=int(datetime(2023,6,1,tzinfo=timezone.utc).timestamp()*1000)-3600000
    ok=(sha==chk and members==[csv_name] and len(opens)==744 and opens and opens[0]==first and opens[-1]==last
        and all(d==3600000 for d in deltas))
    rows.append({
      "symbol":sym,"url":url,"zip_sha256":sha,"checksum_expected":chk,"checksum_pass":sha==chk,
      "members":members,"row_count":len(opens),"first_open_ms":opens[0] if opens else None,
      "last_open_ms":opens[-1] if opens else None,"non_hourly_gap_count":sum(d!=3600000 for d in deltas),
      "pass":ok
    })
receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-SETTLED-FLOW-002",
 "stage":"BINANCE_HOURLY_TARGET_SOURCE_GATE_V0.1","fixture_month":MONTH,"interval":"1h",
 "classification":"BINANCE_HOURLY_TARGET_SOURCE_PASS" if all(x["pass"] for x in rows) else "BINANCE_HOURLY_TARGET_SOURCE_BLOCKED",
 "symbols":rows,"price_values_persisted":False,"returns_computed":False,"flow_join_performed":False,
 "market_outcome_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if receipt["classification"]!="BINANCE_HOURLY_TARGET_SOURCE_PASS":raise SystemExit(2)
