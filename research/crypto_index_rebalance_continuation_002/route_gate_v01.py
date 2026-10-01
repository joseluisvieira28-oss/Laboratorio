#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,urllib.request,urllib.error,hashlib
from pathlib import Path
from collections import Counter

LAB_ID="CRYPTO-INDEX-REBALANCE-CONTINUATION-002"
BASE="https://data.binance.vision/data/futures/um/daily/klines"
UA="CryptoLab-CIRC002-RouteGate/0.1 source-only"
OUT=Path("artifacts/crypto_index_rebalance_continuation_002")

def head(url):
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {"ok":200<=int(r.status)<300,"status":int(r.status),
                    "content_length":r.headers.get("content-length"),
                    "etag":r.headers.get("etag")}
    except urllib.error.HTTPError as e:
        return {"ok":False,"status":int(e.code),"content_length":None,"etag":None}
    except Exception as e:
        return {"ok":False,"status":None,"error":type(e).__name__+":"+str(e)}

def route(symbol,date):
    name=f"{symbol}-1m-{date}.zip"
    url=f"{BASE}/{symbol}/1m/{name}"
    z=head(url); c=head(url+".CHECKSUM")
    return {"symbol":symbol,"date":date,"zip_url":url,"zip_head":z,
            "checksum_url":url+".CHECKSUM","checksum_head":c,
            "route_pass":bool(z.get("ok") and c.get("ok"))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",required=True);a=ap.parse_args()
    src=json.loads(Path(a.source).read_text())
    assert src["lab_id"]==LAB_ID and src["classification"]=="SOURCE_CENSUS_PASS"
    assert src["source_identity_sha256"]=="6aaaaa8132f0987a716926bf44fd9d2979d29925610b41e5a1ae1c109a929074"
    rows=[];cache={}
    for e in src["events"]:
        month=e["month_key"]
        impl=e["implementation_timestamp_utc"][:10]
        token=e["ticker"]+"USDT"
        key1=(token,impl);key2=("BTCUSDT",impl)
        if key1 not in cache:cache[key1]=route(*key1)
        if key2 not in cache:cache[key2]=route(*key2)
        primary=month!="2026-09"
        ok=cache[key1]["route_pass"] and cache[key2]["route_pass"]
        rows.append({
          "month_key":month,"ticker":e["ticker"],"direction":e["direction"],
          "implementation_date":impl,
          "token_symbol":token,"btc_symbol":"BTCUSDT",
          "token_route_pass":cache[key1]["route_pass"],
          "btc_route_pass":cache[key2]["route_pass"],
          "route_qualified":ok,
          "primary_confirmatory_eligible":bool(primary and ok),
          "exclusion_reason":None if primary else "2026-09_PARENT_PROSPECTIVE_OVERLAP"
        })
    eligible=[x for x in rows if x["primary_confirmatory_eligible"]]
    months=sorted({x["month_key"] for x in eligible})
    dirs=Counter(x["direction"] for x in eligible)
    gates={
      "min_16_route_qualified_legs":len(eligible)>=16,
      "min_4_route_qualified_months":len(months)>=4,
      "both_directions":dirs["ADD"]>0 and dirs["REMOVE"]>0,
      "btc_route_all_primary_change_dates":all(x["btc_route_pass"] for x in rows if x["month_key"]!="2026-09")
    }
    result={
      "lab_id":LAB_ID,"schema":"CIRC002_USDM_ROUTE_GATE_V0.1",
      "classification":"ROUTE_FEASIBILITY_PASS" if all(gates.values()) else "ROUTE_FEASIBILITY_BLOCKED",
      "source_identity_sha256":src["source_identity_sha256"],
      "all_source_legs":len(rows),
      "primary_route_qualified_legs":len(eligible),
      "primary_route_qualified_months":months,
      "primary_direction_counts":dict(dirs),
      "rows":rows,"route_objects":list(cache.values()),"gates":gates,
      "zip_body_bytes_read":0,"price_values_read":False,"returns_computed":False,"pnl_computed":False,
      "trading_authority":"NONE"
    }
    stable={"rows":rows,"route_objects":list(cache.values())}
    result["route_identity_sha256"]=hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"USD_M_ROUTE_GATE_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({k:result[k] for k in ["classification","all_source_legs","primary_route_qualified_legs","primary_route_qualified_months","primary_direction_counts","gates","route_identity_sha256","zip_body_bytes_read","price_values_read"]},indent=2,sort_keys=True))
    return 0 if result["classification"]=="ROUTE_FEASIBILITY_PASS" else 2
if __name__=="__main__":raise SystemExit(main())
