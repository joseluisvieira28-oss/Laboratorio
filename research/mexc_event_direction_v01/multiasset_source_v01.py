#!/usr/bin/env python3
"""Source-only MEXC Event Futures product and historical index gate, no outcome join."""
import datetime as dt, hashlib, json, math, pathlib, urllib.parse, urllib.request
OUT=pathlib.Path("artifacts/event_futures_multiasset_v01")
SNAP=pathlib.Path("artifacts/mexc_event_futures/v012/prospective_snapshot_v012.json")
SYMS=("BTC_USDT","ETH_USDT","NVIDIA_USDT","SPCXSTOCK_USDT","MUSTOCK_USDT")
START=int(dt.datetime(2026,10,22,tzinfo=dt.timezone.utc).timestamp())
END=int(dt.datetime(2026,10,24,tzinfo=dt.timezone.utc).timestamp())
EXPECTED=(END-START)//300
assert EXPECTED==576
def check_index(sym):
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/"+sym+"?"+urllib.parse.urlencode({"interval":"Min5","start":START,"end":END-300})
    rec={"symbol":sym,"url":url,"status":"SOURCE_BLOCKED","bars":0,"expected":EXPECTED}
    try:
        q=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-SourceOnly/0.1"})
        with urllib.request.urlopen(q,timeout=35) as resp:
            rec["http_status"]=resp.status
            raw=resp.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError("BODY_TOO_LARGE")
        rec["body_sha256"]=hashlib.sha256(raw).hexdigest()
        obj=json.loads(raw)
        if obj.get("success") is not True:raise ValueError("SUCCESS_FALSE")
        data=obj.get("data")
        if not isinstance(data,dict):raise ValueError("DATA_NOT_OBJECT")
        times=data.get("time");prices=data.get("open")
        if not isinstance(times,list) or not isinstance(prices,list) or len(times)!=len(prices):
            raise ValueError("SCHEMA_INVALID")
        if not times:raise ValueError("NO_INDEX_BARS")
        ts=[int(t) for t in times]
        ps=[float(p) for p in prices]
        if any(not(START<=t<END) or t%300 for t in ts):raise ValueError("TIMESTAMP_RANGE_OR_ALIGNMENT")
        if any(not(math.isfinite(x) and x>0) for x in ps):raise ValueError("INVALID_PRICE")
        if len(set(ts))!=len(ts):raise ValueError("DUPLICATE_BAR")
        rec.update(bars=len(ts),first_ts=min(ts),last_ts=max(ts),missing_slots=EXPECTED-len(ts))
        if len(ts)<int(EXPECTED*.8):raise ValueError("COVERAGE_BELOW_80_PERCENT")
        rec["status"]="HIST_INDEX_SOURCE_PASS"
    except Exception as e:
        rec["error"]=type(e).__name__+":"+str(e)[:200]
    return rec
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    obj=json.loads(SNAP.read_text())
    if obj.get("verdict")!="PROSPECTIVE_SNAPSHOT_PASS":raise ValueError("NO_VALID_EVENT_DETAILS")
    capture=obj.get("detail_capture") or {}
    raw=(capture.get("json") or {}).get("data")
    if not isinstance(raw,list):raise ValueError("PRODUCT_DATA_CHANGED")
    products=[]
    for p in raw:
        cycles=[]
        for unit,configs in (p.get("cycleConfigMap") or {}).items():
            if isinstance(configs,list):
                for c in configs:
                    cycles.append({"unit":unit,"value":c.get("val"),"up":c.get("upPayRate"),"down":c.get("downPayRate")})
        products.append({"symbol":p.get("symbol"),"state":p.get("state"),"contractId":p.get("contractId"),"cycles":cycles})
    indexes=[check_index(sym) for sym in SYMS]
    report={"study":"MEXC_EVENT_FUTURES_NEW_ASSETS_SOURCE_V01","product_observed_at":obj.get("observed_at_utc"),
            "product_source_hash":capture.get("sha256"),"products":products,"index_sources":indexes,
            "mli_identity":"UNVERIFIED_NO_ALIAS","historical_window":"2026-10-22/24 UTC",
            "gate":"SOURCE_DISCOVERY_DONE","price_direction_outcomes_opened":0,
            "historical_real_payouts":False,"protected_holdout_accessed":False,
            "trading_or_private_calls":0}
    (OUT/"source_gate.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"gate":report["gate"],"product_observed_at":report["product_observed_at"],
        "source_hash":report["product_source_hash"],
        "relevant_products":[p for p in products if p["symbol"] in SYMS or "MLI" in str(p["symbol"])],
        "index_sources":indexes,"mli_identity":report["mli_identity"]},indent=2,sort_keys=True))
if __name__=="__main__":main()
