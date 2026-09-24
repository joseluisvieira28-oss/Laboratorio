#!/usr/bin/env python3
import json, re, time, hashlib, requests
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL")
MAN=ROOT/"research/BINANCE_COLLATERAL_HAIRCUT_001_EVENT_MANIFEST_V0.1C.json"
OUT=ROOT/"runtime/binance_collateral_haircut_001/source_manifest_receipt_v01c.json"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab","clienttype":"web"})

def iter_dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from iter_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from iter_dicts(v)

def parse_ts(v):
    if isinstance(v,(int,float)):
        z=int(v); return z*1000 if z<10_000_000_000 else z
    if isinstance(v,str):
        q=v.strip()
        if re.fullmatch(r"\d{10,16}",q):
            z=int(q); return z*1000 if z<10_000_000_000 else z
        try:
            d=datetime.fromisoformat(q.replace("Z","+00:00"))
            if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
            return int(d.astimezone(timezone.utc).timestamp()*1000)
        except:return None
    return None

def release_ms(obj):
    vals=[]
    for d in iter_dicts(obj):
        for k,v in d.items():
            if k.lower() in {"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}:
                z=parse_ts(v)
                if z: vals.append(z)
    return min(vals) if vals else None

def title_of(obj):
    for d in iter_dicts(obj):
        v=d.get("title")
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def get(code):
    last=None
    for i in range(6):
        try:
            r=S.get(DETAIL,params={"articleCode":code},headers={"Referer":"https://www.binance.com/en/support/announcement"},timeout=45)
            if r.status_code==429 or r.status_code>=500: raise RuntimeError(f"HTTP {r.status_code}")
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i<5: time.sleep(min(15,1.5*(2**i)))
    raise RuntimeError(str(last))

def main():
    m=json.loads(MAN.read_text())
    ev=m["events"]
    arts=m["articles"]
    checks=[]
    try:
        assert len(arts)==5 and len(ev)==36
        assert sum(x["delta_pp"]<0 for x in ev)==8
        assert sum(x["delta_pp"]>0 for x in ev)==28
        assert len({(x["article_code"],x["effective_utc"]) for x in ev})==5
        assert len({x["asset"] for x in ev})>=15
        for a in arts:
            r=get(a["code"]); obj=r.json()
            code_ok=False
            for d in iter_dicts(obj):
                for k in ("code","articleCode","articlecode"):
                    if str(d.get(k,"")).lower()==a["code"].lower(): code_ok=True
            rel=release_ms(obj); title=title_of(obj)
            eff_ms=int(datetime.fromisoformat(a["effective_utc"].replace("Z","+00:00")).timestamp()*1000)
            text=json.dumps(obj,ensure_ascii=False)
            date=a["effective_utc"][:10]; hh=a["effective_utc"][11:16]
            timing_ok=(date in text and hh in text and rel is not None and rel<eff_ms)
            structural=("collateral ratio" in text.lower() and "portfolio margin" in text.lower())
            checks.append({"code":a["code"],"payload_code_match":code_ok,"release_ms":rel,"release_match":rel==a["release_ms"],"timing_ok":timing_ok,"structural":structural,"title":title,"response_sha256":hashlib.sha256(r.content).hexdigest()})
            if not (code_ok and rel==a["release_ms"] and timing_ok and structural):
                raise RuntimeError("official article validation failed "+a["code"])
            time.sleep(.5)
        receipt={"lab_id":m["lab_id"],"classification":"BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS","manifest_version":"V0.1C","articles":5,"asset_events":36,"independent_clusters":5,"unique_assets":len({x["asset"] for x in ev}),"tightening_events":8,"loosening_events":28,"official_checks":checks,"safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_opened":False,"mutation":False}}
    except Exception as e:
        receipt={"lab_id":"BINANCE-COLLATERAL-HAIRCUT-001","classification":"PROVENANCE_FAILURE","failure":f"{type(e).__name__}: {e}","official_checks":checks,"safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_opened":False,"mutation":False}}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt if receipt["classification"]!="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" else {k:receipt[k] for k in ["classification","articles","asset_events","independent_clusters","unique_assets","tightening_events","loosening_events"]},indent=2))
    return 0 if receipt["classification"]=="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" else 2
if __name__=="__main__": raise SystemExit(main())
