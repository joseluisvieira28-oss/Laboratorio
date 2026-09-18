#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,math,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT=Path("labs/ETF_CREATION_FLOW_001")
AUTH=json.loads((ROOT/"SOURCE_RECOVERY_AUTHORITY_V0.4.json").read_text())
OUT=Path("artifacts/etf_creation_flow_source_recovery_v04");OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0","Accept":"application/json,text/plain,*/*","Referer":"https://www.ishares.com/"})

def sha(b): return hashlib.sha256(b).hexdigest()

def num(v):
    vals=v if isinstance(v,list) else [v]
    for x in vals:
        if isinstance(x,(int,float)) and not isinstance(x,bool):
            y=float(x)
            if math.isfinite(y) and y>0:return y
        if isinstance(x,str):
            s=x.replace(",","").replace("$","").strip()
            try:
                y=float(s)
                if math.isfinite(y) and y>0:return y
            except: pass
    return None

def normalize_date(v):
    vals=v if isinstance(v,list) else [v]
    out=[]
    for x in vals:
        if x is None:continue
        if isinstance(x,(int,float)) and not isinstance(x,bool):
            y=float(x)
            try:
                if y>1e12: z=datetime.fromtimestamp(y/1000,tz=timezone.utc)
                elif y>1e9: z=datetime.fromtimestamp(y,tz=timezone.utc)
                else: continue
                out.append(z.strftime("%Y-%m-%d"));continue
            except: pass
        s=str(x).strip()
        for fmt in ("%Y-%m-%d","%Y%m%d","%b %d, %Y","%B %d, %Y","%m/%d/%Y"):
            try:
                out.append(datetime.strptime(s,fmt).strftime("%Y-%m-%d"));break
            except: pass
    return out

def walk_dates(x,path="$"):
    found=[]
    if isinstance(x,dict):
        for k,v in x.items():
            nk=re.sub(r"[^a-z0-9]+","",str(k).lower())
            if "date" in nk or "asof" in nk:
                for d in normalize_date(v):
                    found.append({"path":path+"."+str(k),"date":d})
            found.extend(walk_dates(v,path+"."+str(k)))
    elif isinstance(x,list):
        for i,v in enumerate(x):
            found.extend(walk_dates(v,f"{path}[{i}]"))
    return found

def get_keyfacts(obj):
    try:
        return obj["componentsByNameMap"]["keyFundFacts"]["containersByNameMap"]["default"]["dataPointsByNameMap"]
    except Exception as e:
        raise ValueError("KEY_FACTS_PATH_MISSING") from e

def build_url(base,d):
    q=dict(AUTH["fixed_params"]);q["asOfDate"]=d.replace("-","")
    return base+"?"+urlencode(q)

probes=[]
protected_contamination=False
for route in AUTH["routes"]:
    for d in AUTH["frozen_probe_dates"]:
        url=build_url(route["base"],d)
        rec={"route":route["id"],"requested_date":d,"url":url}
        try:
            r=S.get(url,timeout=45,allow_redirects=True)
            b=r.content
            rec.update({"http_status":r.status_code,"content_type":r.headers.get("Content-Type"),"byte_count":len(b),"sha256":sha(b),"final_url":str(r.url)})
            if r.status_code!=200:
                rec.update({"pass":False,"reason":f"HTTP_{r.status_code}"});probes.append(rec);continue
            text=b.decode("utf-8-sig","replace").strip()
            if text.startswith("<"):
                rec.update({"pass":False,"reason":"HTML_MISROUTE"});probes.append(rec);continue
            obj=json.loads(text)
            dp=get_keyfacts(obj)
            so=dp.get("sharesOutstanding")
            if not isinstance(so,dict):
                rec.update({"pass":False,"reason":"SHARES_OUTSTANDING_FIELD_MISSING"});probes.append(rec);continue

            # Returned-date evidence: first inspect the scientific field itself, then the keyfacts component.
            field_dates=[]
            for key in ("asOfDate","asofDate","date"):
                if key in so: field_dates.extend(normalize_date(so.get(key)))
            component_dates=walk_dates(dp)
            all_dates=[]
            for x in field_dates:
                if x not in all_dates:all_dates.append(x)
            for x in component_dates:
                if x["date"] not in all_dates:all_dates.append(x["date"])

            protected=[x for x in all_dates if x.startswith("2025-") or x.startswith("2026-")]
            if protected:
                protected_contamination=True
                rec.update({"pass":False,"reason":"PROTECTED_DATE_RETURNED","returned_dates":protected[:5]})
                probes.append(rec);continue

            exact=(d in all_dates)
            val=num(so.get("value"))
            if val is None: val=num(so.get("formattedValue"))
            rec.update({
                "shares_outstanding":val if exact else None,
                "date_match":exact,
                "returned_dates":all_dates[:12],
                "shares_field_has_asof":field_dates,
                "pass":bool(exact and val is not None and val>0)
            })
            if not rec["pass"]:
                rec["reason"]="DATE_BINDING_FAIL" if not exact else "SHARES_VALUE_FAIL"
        except Exception as e:
            rec.update({"pass":False,"reason":"EXCEPTION","error":type(e).__name__+":"+str(e)})
        probes.append(rec)
        time.sleep(0.2)

summary={}
for route in AUTH["routes"]:
    rr=[x for x in probes if x["route"]==route["id"]]
    good=[x for x in rr if x.get("pass")]
    qs={(int(x["requested_date"][:4]),(int(x["requested_date"][5:7])-1)//3+1) for x in good}
    summary[route["id"]]={"exact_dates":len(good),"distinct_quarters":len(qs),
                          "pass":len(good)>=AUTH["pass_gate"]["minimum_exact_dates"] and len(qs)>=AUTH["pass_gate"]["minimum_distinct_calendar_quarters"]}
passing=[k for k,v in summary.items() if v["pass"]]
if protected_contamination:
    cls=AUTH["classifications"]["provenance_failure"]
elif passing:
    cls=AUTH["classifications"]["pass"]
else:
    cls=AUTH["classifications"]["blocked"]

receipt={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,
         "passing_routes":passing,"route_summary":summary,"probes":probes,
         "btc_market_data_accessed":False,"returns_computed":False,"pnl_computed":False,
         "fundDownload_historical_component":False,
         "access_2025":False if not protected_contamination else "PROVIDER_RETURNED_PROTECTED_DATE_FAIL_CLOSED",
         "access_2026":False if not protected_contamination else "PROVIDER_RETURNED_PROTECTED_DATE_FAIL_CLOSED",
         "live_trading":False,"exchange_mutation":False,"merge_to_main":False}
p=OUT/"ETF_CREATION_FLOW_001_SOURCE_RECOVERY_V0.4.json";p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"SOURCE_RECOVERY_AUTHORITY_V0.4.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
sys.exit(2 if cls in (AUTH["classifications"]["provenance_failure"],AUTH["classifications"]["technical_failure"]) else 0)
