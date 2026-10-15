from __future__ import annotations
import json, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_001_okx_archive_diag_v01"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-001 okx archive enum diagnostic/1.0"
MODULES=["__SOURCE_ENUM_PROBE__","candlestick","candlesticks","candle","kline","fundingRate","funding-rate","funding_rate","funding"]
def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def probe(module):
    params={
      "module":module,
      "instType":"SWAP",
      "dateAggrType":"1M",
      "begin":ms("2024-01-01T00:00:00Z"),
      "end":ms("2024-02-01T00:00:00Z"),
      "instIdList":"BTC-USDT-SWAP",
    }
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    rec={"module":module,"params":params}
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8","replace")
            rec["http_status"]=r.status
            try: rec["body"]=json.loads(raw)
            except Exception: rec["body_text"]=raw[:2000]
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        rec["http_status"]=e.code
        try: rec["body"]=json.loads(raw)
        except Exception: rec["body_text"]=raw[:2000]
    except Exception as e:
        rec["transport_error"]=repr(e)
    return rec

def main():
    receipt={
      "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-001",
      "stage":"OKX_ARCHIVE_PROVIDER_VALIDATION_DIAGNOSTIC",
      "outcome_blind":True,
      "archive_payload_opened":False,
      "signal_calculation_performed":False,
      "return_calculation_performed":False,
      "pnl_calculation_performed":False,
      "probes":[]
    }
    for m in MODULES:
        receipt["probes"].append(probe(m)); time.sleep(0.35)
    p=OUT/"OKX_ARCHIVE_PROVIDER_VALIDATION_DIAGNOSTIC_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    for x in receipt["probes"]:
        body=x.get("body")
        print(x["module"],x.get("http_status"),json.dumps(body,sort_keys=True)[:1000] if body is not None else x.get("body_text") or x.get("transport_error"))
    return 0
if __name__=="__main__": raise SystemExit(main())
