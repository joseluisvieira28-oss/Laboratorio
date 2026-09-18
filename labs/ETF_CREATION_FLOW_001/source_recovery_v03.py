#!/usr/bin/env python3
from __future__ import annotations
import ast, csv, hashlib, io, json, math, re, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT=Path("labs/ETF_CREATION_FLOW_001")
AUTH=json.loads((ROOT/"SOURCE_RECOVERY_AUTHORITY_V0.3.json").read_text())
OUT=Path("artifacts/etf_creation_flow_source_recovery_v03")
OUT.mkdir(parents=True,exist_ok=True)
BASE=AUTH["official_host"]
S=requests.Session()
S.headers.update({
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept-Language":"en-US,en;q=0.9",
    "Referer":"https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf"
})

def h(b): return hashlib.sha256(b).hexdigest()

def norm_key(s):
    return re.sub(r"[^a-z0-9]+"," ",str(s).lower()).strip()

def target_forms(d):
    z=datetime.strptime(d,"%Y-%m-%d")
    return {
        d,
        d.replace("-",""),
        z.strftime("%b %d, %Y"),
        z.strftime("%B %d, %Y"),
        z.strftime("%m/%d/%Y"),
    }

def num(v):
    if isinstance(v,(int,float)) and not isinstance(v,bool):
        x=float(v); return x if math.isfinite(x) else None
    if isinstance(v,str):
        s=v.strip().replace(",","").replace("$","")
        s=re.sub(r"\s+","",s)
        try:
            x=float(s); return x if math.isfinite(x) else None
        except: return None
    return None

def walk(x,path="$"):
    if isinstance(x,dict):
        for k,v in x.items():
            p=path+"."+str(k)
            yield p,k,v
            yield from walk(v,p)
    elif isinstance(x,list):
        for i,v in enumerate(x):
            yield from walk(v,f"{path}[{i}]")

def unwrap_object_text(t):
    s=t.strip().lstrip("\ufeff")
    # Remove common anti-XSSI prefixes without touching object content.
    for prefix in (")]}',", ")]}'", "while(1);", "for(;;);"):
        if s.startswith(prefix):
            s=s[len(prefix):].lstrip()
    # Strip a simple JSONP callback or parenthesis wrapper.
    first=s.find("{"); last=s.rfind("}")
    if first>=0 and last>first:
        return s[first:last+1]
    return s

def parse_object_text(t):
    core=unwrap_object_text(t)
    try:
        return json.loads(core),"strict_or_wrapped_json"
    except Exception:
        pass
    try:
        obj=ast.literal_eval(core)
        if isinstance(obj,(dict,list)):
            return obj,"python_literal_object"
    except Exception:
        pass
    return None,None

def parse_csv_or_text(t,requested_date):
    rows=[]
    try:
        rows=list(csv.reader(io.StringIO(t)))
    except Exception:
        rows=[]
    date_ok=False
    share_hit=None
    forms={x.lower() for x in target_forms(requested_date)}
    for row in rows[:80]:
        if not row: continue
        line=" ".join(str(x) for x in row)
        if any(f in line.lower() for f in forms):
            date_ok=True
        key=norm_key(row[0] if row else "")
        if key=="shares outstanding" and len(row)>=2:
            x=num(row[1])
            if x is not None and x>0:
                share_hit={"path":"csv_row","key":row[0],"value":x}
    return date_ok,share_hit,"csv_or_text_rows"

def extract_obj(obj,t,requested_date):
    forms={x.lower() for x in target_forms(requested_date)}
    date_hits=[]
    share_hits=[]
    for path,k,v in walk(obj):
        ks=norm_key(k)
        if ks=="shares outstanding" or ("shares" in ks and "outstanding" in ks):
            x=num(v)
            if x is not None and x>0:
                share_hits.append({"path":path,"key":str(k),"value":x})
        if isinstance(v,(str,int,float)):
            sv=str(v).lower()
            if any(f in sv for f in forms):
                date_hits.append({"path":path,"key":str(k),"value":str(v)[:120]})
    raw_lower=t.lower()
    date_ok=bool(date_hits) or any(f in raw_lower for f in forms)
    return date_ok,(share_hits[0] if share_hits else None),date_hits[:10]

def route_url(route_id,d):
    ymd=d.replace("-","")
    path="/us/products/333011/ishares-bitcoin-trust-etf/1467271812596.ajax"
    if route_id=="ajax_json_tab_all":
        q={"fileType":"json","tab":"all","asOfDate":ymd}
    elif route_id=="ajax_json_fund":
        q={"fileType":"json","fileName":"IBIT_holdings","dataType":"fund","asOfDate":ymd}
    elif route_id=="ajax_csv_fund":
        q={"fileType":"csv","fileName":"IBIT_holdings","dataType":"fund","asOfDate":ymd}
    else:
        raise ValueError(route_id)
    return BASE+path+"?"+urlencode(q)

def fetch_bounded(url,route_id):
    headers={"X-Requested-With":"XMLHttpRequest"}
    headers["Accept"]="application/json,text/javascript,*/*;q=0.1" if "json" in route_id else "text/csv,text/plain,*/*;q=0.1"
    r=S.get(url,headers=headers,timeout=45,stream=True,allow_redirects=True)
    status=r.status_code
    ctype=(r.headers.get("Content-Type") or "").lower()
    # For an HTML misroute, keep only the page head and abort before current fund data can be traversed.
    limit=2048 if "text/html" in ctype else 2_000_000
    chunks=[]; total=0
    for chunk in r.iter_content(8192):
        if not chunk: continue
        remain=limit-total
        if remain<=0: break
        chunks.append(chunk[:remain]); total+=min(len(chunk),remain)
        if total>=limit: break
    b=b"".join(chunks)
    return status,ctype,b,str(r.url)

def sanitize_preview(t):
    s=re.sub(r"\s+"," ",t[:500])
    # Do not retain current/protected numeric fund values from a misrouted page.
    s=re.sub(r"\b(?:2025|2026)\b","[PROTECTED_YEAR]",s)
    return s[:300]

probes=[]
protected_marker_detected=False
for route in [x["id"] for x in AUTH["permitted_routes"]]:
    for d in AUTH["frozen_probe_dates"]:
        url=route_url(route,d)
        rec={"route":route,"requested_date":d,"url":url}
        try:
            status,ctype,b,final_url=fetch_bounded(url,route)
            text=b.decode("utf-8-sig","replace")
            rec.update({
                "status":status,"content_type":ctype,"byte_count_read":len(b),
                "sha256_bounded_bytes":h(b),"final_url":final_url
            })
            if status!=200:
                rec.update({"pass":False,"reason":f"HTTP_{status}","preview":sanitize_preview(text)})
                probes.append(rec); continue
            if "text/html" in ctype or text.lstrip().lower().startswith("<!doctype html"):
                rec.update({"pass":False,"reason":"HTML_MISROUTE","preview":sanitize_preview(text)})
                probes.append(rec); continue
            # Reject any obvious protected-year payload before scientific parsing.
            if re.search(r"\b(?:2025|2026)[-/]",text) or re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+202[56]\b",text):
                protected_marker_detected=True
                rec.update({"pass":False,"reason":"PROTECTED_PERIOD_PAYLOAD_DETECTED","preview":sanitize_preview(text)})
                probes.append(rec); continue

            obj,mode=parse_object_text(text)
            if obj is not None:
                date_ok,share_hit,date_hits=extract_obj(obj,text,d)
                rec.update({"parser_mode":mode,"date_match":date_ok,"date_hits":date_hits,
                            "shares_outstanding_hit":share_hit})
            else:
                date_ok,share_hit,mode=parse_csv_or_text(text,d)
                rec.update({"parser_mode":mode,"date_match":date_ok,"shares_outstanding_hit":share_hit,
                            "preview":sanitize_preview(text) if not(date_ok and share_hit) else None})
            rec["pass"]=bool(rec.get("date_match") and rec.get("shares_outstanding_hit"))
            if not rec["pass"] and "reason" not in rec:
                rec["reason"]="EXACT_DATE_OR_EXPLICIT_SHARES_MISSING"
        except Exception as e:
            rec.update({"pass":False,"reason":"EXCEPTION","error":type(e).__name__+":"+str(e)})
        probes.append(rec)
        time.sleep(0.2)

summary={}
for route in [x["id"] for x in AUTH["permitted_routes"]]:
    rr=[x for x in probes if x["route"]==route]
    exact=[x for x in rr if x.get("pass")]
    quarters={(int(x["requested_date"][:4]),(int(x["requested_date"][5:7])-1)//3+1) for x in exact}
    summary[route]={"exact_dates":len(exact),"distinct_quarters":len(quarters),
                    "pass":len(exact)>=AUTH["pass_gate"]["minimum_exact_dates"] and len(quarters)>=AUTH["pass_gate"]["minimum_distinct_calendar_quarters"]}
passing=[k for k,v in summary.items() if v["pass"]]

if protected_marker_detected:
    classification=AUTH["classifications"]["provenance_failure"]
elif passing:
    classification=AUTH["classifications"]["pass"]
else:
    classification=AUTH["classifications"]["blocked"]

receipt={
    "lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":classification,
    "passing_routes":passing,"route_summary":summary,"probes":probes,
    "btc_market_data_accessed":False,"returns_computed":False,"pnl_computed":False,
    "access_2025":False,"access_2026":False if not protected_marker_detected else "PAYLOAD_CONTAMINATION_DETECTED_FAIL_CLOSED",
    "live_trading":False,"exchange_mutation":False,"merge_to_main":False
}
p=OUT/"ETF_CREATION_FLOW_001_SOURCE_RECOVERY_V0.3.json"
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({
    "authority_sha256":h((ROOT/"SOURCE_RECOVERY_AUTHORITY_V0.3.json").read_bytes()),
    "result_sha256":h(p.read_bytes())
},indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
sys.exit(2 if classification in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 0)
