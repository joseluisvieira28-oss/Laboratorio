#!/usr/bin/env python3
import datetime as dt,json,urllib.error,urllib.parse,urllib.request,time
from pathlib import Path

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DLS_V0_2_FUTURES_SOURCE_GATE_RECEIPT_V0.1.json")
symbol="SOLUSDT"
errors=[]
probes=[]

def http_json(url,retries=5):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-v02-source-gate/0.1"})
            with urllib.request.urlopen(q,timeout=45) as r:
                return int(r.status),json.loads(r.read())
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,500,502,503,504): time.sleep(min(15,2**i)); continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:200]}; time.sleep(min(15,2**i))
    return None,last

def head(url,retries=5):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-v02-source-gate/0.1"},method="HEAD")
            with urllib.request.urlopen(q,timeout=45) as r:return int(r.status),dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (404,403,405): return int(e.code),{}
            last={"http":e.code}
            if e.code in (429,500,502,503,504): time.sleep(min(15,2**i)); continue
            return int(e.code),{}
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:200]}; time.sleep(min(15,2**i))
    return None,last or {}

urls=[
 "https://fapi.binance.com/fapi/v1/exchangeInfo",
 "https://fapi1.binance.com/fapi/v1/exchangeInfo",
]
st=obj=None; route=None
for url in urls:
    st,obj=http_json(url)
    if st==200:
        route=url; break
symbols=(obj or {}).get("symbols") or []
exact=[x for x in symbols if x.get("symbol")==symbol and x.get("contractType")=="PERPETUAL" and x.get("quoteAsset")=="USDT" and x.get("baseAsset")=="SOL"]
if len(exact)!=1:
    errors.append({"reason":"futures_product_metadata_mismatch","http_status":st,"match_count":len(exact)})

# Metadata-only route probes, one deterministic day per quarter over open development period.
dates=[
 "2021-12-15",
 "2022-03-15","2022-06-15","2022-09-15","2022-12-15",
 "2023-03-15","2023-06-15","2023-09-15","2023-12-15",
 "2024-03-15","2024-06-15","2024-09-15","2024-12-15",
]
for day in dates:
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{day}.zip"
    zs,zh=head(base); cs,ch=head(base+".CHECKSUM")
    ok=(zs==200 and cs==200)
    probes.append({"date":day,"zip_head_status":zs,"checksum_head_status":cs,"pass":ok})
    if not ok: errors.append({"reason":"archive_route_probe_failed","date":day,"zip":zs,"checksum":cs})

classification="DLS_V0_2_FUTURES_SOURCE_PASS" if not errors else "DLS_V0_2_FUTURES_SOURCE_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "mission":"V0.2_EXECUTABLE_VOLATILITY",
 "classification":classification,
 "symbol":symbol,"market":"BINANCE_USDM_PERPETUAL","interval":"1m",
 "product_metadata_route":route,"product_metadata_http_status":st,
 "product_metadata_exact_match":len(exact)==1,
 "archive_route_template":"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip",
 "checksum_route_template":"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip.CHECKSUM",
 "development_start":"2021-12-08T00:00:00Z","development_end_exclusive":"2025-01-01T00:00:00Z",
 "metadata_probes":probes,"error_count":len(errors),"errors":errors,
 "market_payload_opened":False,"prices_opened":False,
 "protected_2025_opened":False,"protected_2026_opened":False,
 "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"probe_pass_count":sum(1 for p in probes if p["pass"]),"error_count":len(errors)},indent=2))
if errors: raise SystemExit(2)
