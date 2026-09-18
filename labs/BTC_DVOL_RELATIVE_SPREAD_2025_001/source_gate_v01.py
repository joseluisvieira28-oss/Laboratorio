#!/usr/bin/env python3
import hashlib,json,sys,time
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

ROOT=Path("labs/BTC_DVOL_RELATIVE_SPREAD_2025_001")
AUTH=json.loads((ROOT/"SOURCE_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/btc_dvol_relspread_2025_source_v01");OUT.mkdir(parents=True,exist_ok=True)
BASE="https://history.deribit.com/api/v2"
S=requests.Session();S.headers.update({"User-Agent":"SRC-Crypto-Lab-DVOL-RelSpread-2025-Source/0.1","Accept":"application/json"})
LOWER_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
UPPER_MS=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
CORE=("instrument_name","timestamp","price","amount","direction","index_price")

def sha(b): return hashlib.sha256(b).hexdigest()
def zdt(ms): return datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc)

def request(path,params,allow_miss=False):
    last=None
    for attempt,wait in enumerate((1,2,4)):
        try:
            r=S.get(BASE+path,params=params,timeout=40);raw=r.content;dig=sha(raw)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {path} sha256={dig}")
                if attempt<2: time.sleep(wait); continue
                raise last
            obj=r.json();err=obj.get("error") if isinstance(obj,dict) else None
            if err:
                msg=str(err.get("message","")).lower() if isinstance(err,dict) else str(err).lower()
                code=err.get("code") if isinstance(err,dict) else None
                data=err.get("data") if isinstance(err,dict) else None
                wrong=(code==-32602 and isinstance(data,dict) and str(data.get("param","")).lower()=="instrument_name" and str(data.get("reason","")).lower()=="wrong format")
                miss=allow_miss and (code in (11050,10004) or ("instrument" in msg and ("not found" in msg or "invalid" in msg)) or wrong)
                if miss:return None,{"endpoint":path,"sha256":dig,"candidate_miss":True}
                raise RuntimeError(f"API error {path} sha256={dig} error={err}")
            if r.status_code!=200:raise RuntimeError(f"HTTP {r.status_code} {path} sha256={dig}")
            return obj,{"endpoint":path,"sha256":dig,"bytes":len(raw)}
        except requests.RequestException as e:
            last=e
            if attempt<2:time.sleep(wait);continue
            raise
    raise last or RuntimeError("unreachable")

def wednesdays(a,b):
    d=date.fromisoformat(a);e=date.fromisoformat(b)
    while d<=e:
        yield d;d+=timedelta(days=7)
def iname(d): return "BTCDVOL_USDC-"+d.strftime("%d%b%y").upper()

def discover():
    out=[];rejected=[];receipts=[]
    for d in wednesdays(AUTH["source"]["candidate_start"],AUTH["source"]["candidate_end"]):
        name=iname(d);obj,rc=request("/public/get_instrument",{"instrument_name":name},True);rc["candidate"]=name;receipts.append(rc)
        if obj is None:continue
        rec=(obj or {}).get("result") or {};c=rec.get("creation_timestamp");e=rec.get("expiration_timestamp")
        valid=(rec.get("instrument_name")==name and rec.get("kind")=="future" and rec.get("price_index")=="btcdvol_usdc" and isinstance(c,(int,float)) and isinstance(e,(int,float)) and int(c)<UPPER_MS and int(e)>=LOWER_MS and int(e)<UPPER_MS)
        if valid:out.append({"instrument_name":name,"creation_timestamp":int(c),"expiration_timestamp":int(e)})
        else:rejected.append(name)
    return sorted(out,key=lambda x:x["expiration_timestamp"]),rejected,receipts

def slice_trades(name,a,b):
    if a>=UPPER_MS or b>=UPPER_MS:raise RuntimeError("2026 request blocked")
    obj,rc=request("/public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":a,"end_timestamp":b,"count":1000,"sorting":"asc"})
    rows=((obj or {}).get("result") or {}).get("trades") or [];rc.update({"instrument_name":name,"start_ms":a,"end_ms":b,"count":len(rows)})
    if len(rows)==1000:
        if b-a<=1000:raise RuntimeError(f"Unresolved overflow {name}")
        m=(a+b)//2;l,lr=slice_trades(name,a,m);r,rr=slice_trades(name,m+1,b);return l+r,[rc]+lr+rr
    return rows,[rc]

def acquire(name,a,b):
    cur=a;step=86400000;rows=[];rcs=[]
    while cur<=b:
        e=min(cur+step-1,b);x,rr=slice_trades(name,cur,e);rows.extend(x);rcs.extend(rr);cur=e+1;time.sleep(0.003)
    ded={}
    for i,x in enumerate(rows):
        ts=x.get("timestamp")
        if not isinstance(ts,(int,float)) or int(ts)<a or int(ts)>b or int(ts)>=UPPER_MS:raise RuntimeError(f"Out-of-range {name}")
        ded[str(x.get("trade_id",f"MISSING-{i}"))]=x
    ordinary=[];present=0;total=0
    for x in ded.values():
        if any(x.get(k) is not None for k in ("block_trade_id","block_rfq_quote_id","combo_id","combo_trade_id")):continue
        ordinary.append(x)
        for k in CORE:
            total+=1
            if x.get(k) is not None:present+=1
    days=sorted({zdt(x["timestamp"]).date().isoformat() for x in ordinary if isinstance(x.get("timestamp"),(int,float))})
    return {"count":len(ordinary),"days":days,"present":present,"total":total},rcs

def qtr(ms):
    z=zdt(ms);return f"{z.year}-Q{((z.month-1)//3)+1}"

result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":None,
"access_2026":False,"relative_basis_opened":False,"spread_opened":False,"returns_opened":False,"pnl_opened":False,
"live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
try:
    contracts,rejected,meta_rc=discover();pairs=[];source_rc=[];core_p=0;core_t=0;qdef=AUTH["qualifying_pair"]
    for i,(near,far) in enumerate(zip(contracts,contracts[1:]),1):
        start=max(near["creation_timestamp"],far["creation_timestamp"],LOWER_MS)
        end=min(near["expiration_timestamp"],far["expiration_timestamp"],UPPER_MS)-1
        if end<start:
            pairs.append({"near":near["instrument_name"],"far":far["instrument_name"],"has_overlap":False,"qualifying":False});continue
        n,nrc=acquire(near["instrument_name"],start,end);f,frc=acquire(far["instrument_name"],start,end);source_rc.extend(nrc+frc)
        common=sorted(set(n["days"])&set(f["days"]));core_p+=n["present"]+f["present"];core_t+=n["total"]+f["total"]
        qual=(n["count"]>=qdef["minimum_ordinary_public_trades_each_leg"] and f["count"]>=qdef["minimum_ordinary_public_trades_each_leg"] and len(n["days"])>=qdef["minimum_unique_active_utc_days_each_leg"] and len(f["days"])>=qdef["minimum_unique_active_utc_days_each_leg"] and len(common)>=qdef["minimum_common_active_utc_days"])
        pairs.append({"near":near["instrument_name"],"far":far["instrument_name"],"near_expiration_quarter":qtr(near["expiration_timestamp"]),
          "has_overlap":True,"overlap_start":start,"overlap_end":end,"near_trade_count":n["count"],"far_trade_count":f["count"],
          "near_active_days":len(n["days"]),"far_active_days":len(f["days"]),"common_active_days":len(common),"qualifying":qual})
        print(f"RELSPREAD_SOURCE_PROGRESS {i}/{len(contracts)-1} {near['instrument_name']}->{far['instrument_name']}",flush=True)
    overlaps=[x for x in pairs if x.get("has_overlap")];qual=[x for x in pairs if x.get("qualifying")]
    quarters=sorted({x["near_expiration_quarter"] for x in qual});common_total=sum(x["common_active_days"] for x in qual)
    g=AUTH["source_gates"];integrity=len(contracts)/(len(contracts)+len(rejected)) if (contracts or rejected) else 0.0;coverage=core_p/core_t if core_t else 0.0
    checks={"confirmed_contracts_ge_min":len(contracts)>=g["minimum_confirmed_contracts"],"adjacent_overlap_pairs_ge_min":len(overlaps)>=g["minimum_adjacent_overlap_pairs"],
      "qualifying_pairs_ge_min":len(qual)>=g["minimum_qualifying_adjacent_pairs"],"aggregate_common_pair_days_ge_min":common_total>=g["minimum_aggregate_common_pair_days"],
      "quarters_ge_min":len(quarters)>=g["minimum_distinct_near_expiration_quarters"],"core_coverage_ge_min":coverage>=g["core_field_coverage_minimum"],
      "metadata_integrity_ge_min":integrity>=g["exact_metadata_integrity_rate"]}
    cls=AUTH["classifications"]["pass"] if all(checks.values()) else AUTH["classifications"]["insufficient"]
    result.update({"classification":cls,"confirmed_contracts":len(contracts),"metadata_rejections":len(rejected),"adjacent_pairs":len(pairs),"overlap_pairs":len(overlaps),
      "qualifying_pairs":len(qual),"aggregate_common_pair_days":common_total,"qualifying_near_expiration_quarters":quarters,"core_field_coverage":coverage,
      "metadata_integrity_rate":integrity,"gate_checks":checks,"pair_summaries":pairs,"source_request_count":len(meta_rc)+len(source_rc),
      "source_receipt_sha256":sha(json.dumps(meta_rc+source_rc,sort_keys=True).encode())})
except Exception as e:
    txt=repr(e);result["classification"]=AUTH["classifications"]["provenance_failure"] if "2026 request blocked" in txt else AUTH["classifications"]["technical_failure"];result["error"]=txt
p=OUT/"source_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"SOURCE_AUTHORITY_V0.1.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="pair_summaries"},indent=2,sort_keys=True))
sys.exit(0 if result["classification"] not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)
