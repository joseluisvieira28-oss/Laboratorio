from __future__ import annotations
import hashlib,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_mark_source"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/market/history-mark-price-candles"
INST="AVAX-USDT-SWAP"
ANCHORS=[
"2025-01-01T00:00:00Z",
"2025-04-01T08:00:00Z",
"2025-07-01T16:00:00Z",
"2025-10-01T00:00:00Z",
"2025-12-31T08:00:00Z",
]
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 mark-source/1.0"

def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def query(t):
    params={"instId":INST,"bar":"1m","after":str(t+10*60_000),"limit":"30"}
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        body=json.loads(r.read().decode("utf-8","replace"))
        status=r.status
    if body.get("code")!="0": raise RuntimeError(f"OKX:{body.get('code')}:{body.get('msg')}")
    rows=body.get("data") or []
    ts=[int(x[0]) for x in rows]
    confirms=[str(x[5]) for x in rows if len(x)>5]
    return {"http_status":status,"count":len(ts),"min_ts":min(ts) if ts else None,"max_ts":max(ts) if ts else None,
            "anchor_present":t in set(ts),"confirm_counts":{k:confirms.count(k) for k in sorted(set(confirms))},
            "timestamps_sha256":h(sorted(ts))}

def main():
    results={}
    for a in ANCHORS:
        results[a]=query(ms(a)); time.sleep(.25)
    ok=all(x["anchor_present"] for x in results.values()) and all((x["max_ts"] or 0)<ms("2026-01-01T00:00:00Z") for x in results.values())
    rec={"lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002","stage":"OKX_MARK_PRICE_SOURCE_GATE",
         "classification":"OKX_MARK_PRICE_SOURCE_PASS" if ok else "OKX_MARK_PRICE_SOURCE_BLOCKED",
         "instrument":INST,"bar":"1m","anchors":results,
         "mark_price_values_persisted":False,"signal_calculation_performed":False,
         "return_calculation_performed":False,"pnl_calculation_performed":False,"2026_plus_accessed":False}
    rec["fingerprint"]=h(rec)
    (OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_MARK_PRICE_SOURCE_RECEIPT_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":rec["classification"],"anchors":{k:v["anchor_present"] for k,v in results.items()},"fingerprint":rec["fingerprint"]},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
