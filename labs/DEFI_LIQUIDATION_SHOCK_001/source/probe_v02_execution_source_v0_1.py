#!/usr/bin/env python3
import datetime as dt,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001-V0.2"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/V02_EXECUTION_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")
SYMBOL="SOLUSDT"
ZIP_TMPL="https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"
SUM_TMPL=ZIP_TMPL+".CHECKSUM"

def http_json(url,retries=6):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-v02-source/0.1"})
            with urllib.request.urlopen(q,timeout=45) as r:
                return int(r.status),json.loads(r.read())
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,451,500,502,503,504):
                time.sleep(min(15,2**i)); continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:200]}
            time.sleep(min(15,2**i))
    return None,last

def head(url,retries=6):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-v02-source/0.1"},method="HEAD")
            with urllib.request.urlopen(q,timeout=45) as r:
                return int(r.status),dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (403,404,405): return int(e.code),{}
            last={"http":e.code}
            if e.code in (429,500,502,503,504):
                time.sleep(min(15,2**i)); continue
            return int(e.code),{}
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:200]}
            time.sleep(min(15,2**i))
    return None,last or {}

errors=[]
metadata_routes=[
 "https://fapi.binance.com/fapi/v1/exchangeInfo?"+urllib.parse.urlencode({"symbol":SYMBOL}),
 "https://fapi.binance.com/fapi/v1/exchangeInfo"
]
st=obj=None; route=None
for u in metadata_routes:
    st,obj=http_json(u)
    if st==200 and isinstance(obj,dict):
        route=u; break

symbols=(obj or {}).get("symbols") or []
exact=[x for x in symbols if x.get("symbol")==SYMBOL]
meta={
 "http_status":st,"route":route,"exact_match_count":len(exact),
 "contract_type":exact[0].get("contractType") if len(exact)==1 else None,
 "status":exact[0].get("status") if len(exact)==1 else None,
 "onboard_date":exact[0].get("onboardDate") if len(exact)==1 else None,
 "base_asset":exact[0].get("baseAsset") if len(exact)==1 else None,
 "quote_asset":exact[0].get("quoteAsset") if len(exact)==1 else None
}
if len(exact)!=1:
    errors.append({"reason":"binance_um_solusdt_metadata_exact_match_failed","metadata":meta})
else:
    row=exact[0]
    if row.get("contractType")!="PERPETUAL" or row.get("baseAsset")!="SOL" or row.get("quoteAsset")!="USDT":
        errors.append({"reason":"binance_um_solusdt_contract_identity_mismatch","metadata":meta})

# Deterministic metadata-only monthly archive probes: 15th of each month 2021-12..2024-12.
dates=[]
y,m=2021,12
while (y,m)<=(2024,12):
    dates.append(dt.date(y,m,15).isoformat())
    m+=1
    if m==13: y+=1;m=1

probes=[]
for day in dates:
    zu=ZIP_TMPL.format(symbol=SYMBOL,date=day)
    su=SUM_TMPL.format(symbol=SYMBOL,date=day)
    zs,zh=head(zu); ss,sh=head(su)
    ok=(zs==200 and ss==200)
    probes.append({
      "date":day,"zip_head_status":zs,"checksum_head_status":ss,"pass":ok,
      "zip_content_length":zh.get("Content-Length") or zh.get("content-length")
    })
    if not ok:
        errors.append({"reason":"monthly_archive_probe_failed","date":day,"zip_status":zs,"checksum_status":ss})

classification="V02_EXECUTION_SOURCE_PASS" if not errors else "V02_EXECUTION_SOURCE_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "development_market":"BINANCE_USDTM_SOLUSDT_PERPETUAL",
 "market_metadata":meta,
 "monthly_probe_count":len(probes),
 "monthly_probe_pass_count":sum(1 for x in probes if x["pass"]),
 "monthly_probes":probes,
 "cost_stress_authority":{
   "reference_venue":"MEXC_API_FUTURES",
   "effective_date_utc":"2026-06-01T08:00:00Z",
   "maker_fee_bps_per_side":6.0,
   "taker_fee_bps_per_side":8.0,
   "primary_model":"taker_taker",
   "primary_slippage_bps_per_side":5.0,
   "primary_round_trip_cost_bps":26.0,
   "sensitivity_round_trip_cost_bps":[20.0,36.0],
   "note":"External published API fee authority frozen in DLS_V0_2_EXECUTABLE_VOLATILITY_DEVELOPMENT_FREEZE_V0.1.md"
 },
 "error_count":len(errors),"errors":errors,
 "firewall":{
   "archive_payload_downloaded":False,
   "candles_opened":False,
   "execution_outcomes_computed":False,
   "market_2025_opened":False,
   "market_2026_opened":False,
   "live_trading":False,
   "orders":False,
   "exchange_mutation":False,
   "merge_main":False
 }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"probe_pass":receipt["monthly_probe_pass_count"],"probe_total":len(probes),"error_count":len(errors),"market_metadata":meta},indent=2))
if classification!="V02_EXECUTION_SOURCE_PASS": raise SystemExit(2)
