#!/usr/bin/env python3
"""CED-1D-V1 2025 one-shot transferred replication runner V0.1.

Consumes only pre-frozen 2025 sources, the original V0.3 Momentum implementation,
and the mark-price interval funding binding. No 2026 access, tuning, live trading
or order capability.
"""
from __future__ import annotations
import argparse,array,csv,hashlib,importlib,io,json,math,random,re,statistics,sys,tempfile,zipfile
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path

V03_ZIP_SHA="df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958"
HYPOTHESES_SHA="dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693"
TARGETS=("CED1D-0031","CED1D-0241","CED1D-0251")
CELLS={
"CED1D-0031":{"family":"A_MOMENTUM","symbol":"AVAXUSDT","lookback":20,"horizon":1,"direction":"CONTINUATION","role":"PRIMARY_TARGET"},
"CED1D-0033":{"family":"A_MOMENTUM","symbol":"AVAXUSDT","lookback":20,"horizon":3,"direction":"CONTINUATION","role":"NEIGHBOUR_ONLY"},
"CED1D-0041":{"family":"A_MOMENTUM","symbol":"AVAXUSDT","lookback":60,"horizon":1,"direction":"CONTINUATION","role":"NEIGHBOUR_ONLY"},
"CED1D-0241":{"family":"A_MOMENTUM","symbol":"SOLUSDT","lookback":20,"horizon":1,"direction":"CONTINUATION","role":"PRIMARY_TARGET"},
"CED1D-0243":{"family":"A_MOMENTUM","symbol":"SOLUSDT","lookback":20,"horizon":3,"direction":"CONTINUATION","role":"NEIGHBOUR_ONLY"},
"CED1D-0251":{"family":"A_MOMENTUM","symbol":"SOLUSDT","lookback":60,"horizon":1,"direction":"CONTINUATION","role":"PRIMARY_TARGET"},
"CED1D-0253":{"family":"A_MOMENTUM","symbol":"SOLUSDT","lookback":60,"horizon":3,"direction":"CONTINUATION","role":"NEIGHBOUR_ONLY"},
"CED1D-0261":{"family":"A_MOMENTUM","symbol":"SOLUSDT","lookback":120,"horizon":1,"direction":"CONTINUATION","role":"NEIGHBOUR_ONLY"},
}
NEIGHBORS={
"CED1D-0031":("CED1D-0033","CED1D-0041"),
"CED1D-0241":("CED1D-0243","CED1D-0251"),
"CED1D-0251":("CED1D-0241","CED1D-0253","CED1D-0261"),
}
FIRST_SIGNAL_WEEK=date(2025,1,6)
END_SIGNAL_WEEK_EXCLUSIVE=date(2025,12,29)
BASE_COST=14.0
STRESS_COST=20.0
BOOT_REPS=9999
BOOT_SEED=20260908
HEADER_ALIASES={"open_time","opentime","timestamp","time","start_time"}

def sha_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def mean(xs): return math.fsum(xs)/len(xs) if xs else None
def week_start(d): return d-timedelta(days=d.weekday())
def complete_signal_week(d): return FIRST_SIGNAL_WEEK<=week_start(d)<END_SIGNAL_WEEK_EXCLUSIVE
def norm_header(s): return re.sub(r"[^a-z0-9_]+","",s.strip().lower().replace(" ","_"))
def norm_ms(v):
    n=int(float(v))
    while n>10**14: n//=1000
    return n

def percentile(vals,p):
    a=sorted(vals)
    if not a:return None
    pos=(len(a)-1)*p; lo=math.floor(pos); hi=math.ceil(pos)
    return a[lo]+(a[hi]-a[lo])*(pos-lo)

def load_original_hypotheses(v03_zip:Path,tmp:Path):
    if sha_file(v03_zip)!=V03_ZIP_SHA: raise RuntimeError("V03_RUNNER_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(v03_zip) as z:
        bad=z.testzip()
        if bad is not None: raise RuntimeError("V03_ZIP_CRC_FAIL")
        member="CED_1D_V1_RUNNER_FREEZE_V0.3/ced1d/hypotheses.py"
        if hashlib.sha256(z.read(member)).hexdigest()!=HYPOTHESES_SHA: raise RuntimeError("HYPOTHESES_SHA_MISMATCH")
        z.extractall(tmp)
    root=tmp/"CED_1D_V1_RUNNER_FREEZE_V0.3"
    sys.path.insert(0,str(root))
    return importlib.import_module("ced1d.hypotheses")

def parse_price_zip(path:Path):
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names)!=1: raise RuntimeError(f"PRICE_MEMBER_COUNT:{path}")
        rdr=csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8-sig",newline=""))
        first=True
        for row in rdr:
            if not row: continue
            if first:
                first=False
                if len(row)>=5 and norm_header(row[0]) in HEADER_ALIASES: continue
            if len(row)<5: raise RuntimeError(f"PRICE_SHORT_ROW:{path}")
            try: yield norm_ms(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4])
            except Exception as e: raise RuntimeError(f"PRICE_PARSE:{path}:{e}")

def build_bars(cache:Path,manifest:dict):
    per={"AVAXUSDT":{},"SOLUSDT":{}}
    for e in manifest["entries"]:
        p=cache/e["filename"]
        if not p.exists(): raise RuntimeError(f"PRICE_FILE_MISSING:{p}")
        if sha_file(p)!=e["sha256"]: raise RuntimeError(f"PRICE_SHA_MISMATCH:{p}")
        sym=e["symbol"]
        for ts,o,h,l,c in parse_price_zip(p):
            if ts>=1767225600000: raise RuntimeError("HARD_BLOCK_2026_PRICE")
            dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); day=dt.date().isoformat(); minute=dt.hour*60+dt.minute
            d=per[sym].get(day)
            if d is None:
                d={"date":day,"open":o,"high":h,"low":l,"close":c,"first_ts":ts,"last_ts":ts,"mask":0,"duplicates":0,"open_0001":None}
                per[sym][day]=d
            bit=1<<minute
            if d["mask"]&bit:d["duplicates"]+=1
            else:d["mask"]|=bit
            if ts<d["first_ts"]:d["first_ts"]=ts;d["open"]=o
            if ts>=d["last_ts"]:d["last_ts"]=ts;d["close"]=c
            d["high"]=max(d["high"],h);d["low"]=min(d["low"],l)
            if minute==1:d["open_0001"]=o
    bars={}
    for sym,dm in per.items():
        arr=[]
        for day in sorted(dm):
            d=dm[day]; minutes=d["mask"].bit_count()
            item={k:v for k,v in d.items() if k!="mask"}
            item["minutes"]=minutes; item["valid_day"]=minutes==1440 and d["duplicates"]==0 and d["open_0001"] is not None
            arr.append(item)
        bars[sym]=arr
    return bars

def generate_2025_events(hyp,bars,cfg):
    series=hyp.Series(bars)
    cache={"daily_rets":series.completed_daily_log_returns(),"rv20":series.rv20_map()}
    active_exit=None; out=[]
    for d in series.valid_dates:
        sd=date.fromisoformat(d)
        if sd.year!=2025: continue
        direction=hyp.signal_for(series,cfg,d,cache)
        if direction is None: continue
        ex,status=series.execution(d,cfg["horizon"])
        if status!="OK":
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE"}); continue
        entry=date.fromisoformat(ex["entry_day"]); exitd=date.fromisoformat(ex["exit_day"])
        if exitd.year>=2026:
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]}); continue
        if active_exit is not None and entry<active_exit:
            out.append({"signal_day":d,"status":"OVERLAP_BLOCKED","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]}); continue
        active_exit=exitd
        out.append({"signal_day":d,"status":"TRADE","direction":direction,**ex,"signed_return":direction*ex["raw_return"]})
    return out

def load_bindings(path:Path):
    d=json.loads(path.read_text())
    for sym in ("AVAXUSDT","SOLUSDT"):
        rows=d.get(sym,[])
        if len(rows)!=1095: raise RuntimeError(f"FUNDING_BIND_COUNT:{sym}:{len(rows)}")
        if any(int(r["fundingTime"])>=1767225600000 for r in rows): raise RuntimeError("HARD_BLOCK_2026_FUNDING")
    return d

def add_funding_bounds(event,symbol,bindings):
    if event["status"]!="TRADE":return event
    entry_ts=int(datetime.fromisoformat(event["entry_day"]).replace(tzinfo=timezone.utc).timestamp()*1000)+60000
    exit_ts=int(datetime.fromisoformat(event["exit_day"]).replace(tzinfo=timezone.utc).timestamp()*1000)+60000
    ep=float(event["entry_open"]); direction=int(event["direction"])
    lo=hi=0.0; settlements=0
    for r in bindings[symbol]:
        ft=int(r["fundingTime"])
        if not(entry_ts<ft<exit_ts): continue
        rate=float(r["fundingRate"]); coeff=-direction*rate/ep
        ml=float(r["markLow"]); mh=float(r["markHigh"])
        a=coeff*ml*10000; b=coeff*mh*10000
        lo+=min(a,b); hi+=max(a,b); settlements+=1
    gross=float(event["signed_return"])*10000
    return {**event,"gross_bps":gross,"funding_lower_bps":lo,"funding_upper_bps":hi,"funding_settlements":settlements,
            "base_lower_bps":gross-BASE_COST+lo,"base_upper_bps":gross-BASE_COST+hi,
            "stress_lower_bps":gross-STRESS_COST+lo,"stress_upper_bps":gross-STRESS_COST+hi}

def sample_gate(events):
    entry_days={date.fromisoformat(e["entry_day"]) for e in events}
    signal_weeks={week_start(date.fromisoformat(e["signal_day"])) for e in events}
    months={(d.year,d.month) for d in entry_days}
    m={"events":len(events),"active_days":len(entry_days),"active_week_clusters":len(signal_weeks),"active_months":len(months)}
    m["pass"]=m["events"]>=300 and m["active_days"]>=120 and m["active_week_clusters"]>=39 and m["active_months"]>=9
    return m

class WeekPlan:
    def __init__(self):
        weeks=[]; w=FIRST_SIGNAL_WEEK
        while w<END_SIGNAL_WEEK_EXCLUSIVE: weeks.append(w); w+=timedelta(days=7)
        self.weeks=weeks; rng=random.Random(BOOT_SEED); n=len(weeks)
        self.draws=[array.array("H",(rng.randrange(n) for _ in range(n))) for _ in range(BOOT_REPS)]

def bootstrap(events,field,plan):
    result={"status":None,"p_raw":None,"ci_low":None,"ci_high":None,"invalid_fraction":None}
    idx={w:i for i,w in enumerate(plan.weeks)}; bins=[[] for _ in plan.weeks]
    for e in events:
        w=week_start(date.fromisoformat(e["signal_day"]))
        if w not in idx: raise RuntimeError("NON_COMPLETE_WEEK_IN_BOOTSTRAP")
        bins[idx[w]].append(float(e[field]))
    sums=[math.fsum(x) for x in bins]; counts=[len(x) for x in bins]; obs=mean([float(e[field]) for e in events])
    if obs is None: result["status"]="INSUFFICIENT_SAMPLE"; return result
    est=[]; exceed=invalid=0
    for draw in plan.draws:
        n=sum(counts[i] for i in draw)
        if not n: invalid+=1; continue
        x=math.fsum(sums[i] for i in draw)/n; est.append(x); exceed+=(x-obs+2)>=obs
    result["invalid_fraction"]=invalid/BOOT_REPS
    if result["invalid_fraction"]>.01: result["status"]="INFERENCE_BLOCKED_INVALID_RESAMPLES"; return result
    est.sort(); result.update(status="PASS",p_raw=(1+exceed)/(BOOT_REPS+1),ci_low=percentile(est,.025),ci_high=percentile(est,.975))
    return result

def holm(pmap):
    items=sorted(((1.0 if p is None else float(p),k) for k,p in pmap.items()))
    out={}; running=0.0; m=len(items)
    for i,(p,k) in enumerate(items):
        adj=min(1.0,(m-i)*p); running=max(running,adj); out[k]=running
    return out

def path_metrics(events,base_field,stress_field):
    vals=[float(e[base_field]) for e in events]; stress=[float(e[stress_field]) for e in events]
    months=defaultdict(list); quarters=defaultdict(list); days=defaultdict(list)
    for e,v in zip(events,vals):
        d=date.fromisoformat(e["entry_day"]); months[d.strftime("%Y-%m")].append(v); quarters[f"{d.year}-Q{(d.month-1)//3+1}"].append(v); days[d.isoformat()].append(abs(v))
    absvals=[abs(v) for v in vals]; total=math.fsum(absvals)
    if total:
        month_share=max(math.fsum(abs(x) for x in v) for v in months.values())/total
        day_share=max(math.fsum(v) for v in days.values())/total
        top5=math.fsum(sorted(absvals,reverse=True)[:5])/total
        concentration_ratio=max(month_share/.30,day_share/.10,top5/.20)
    else:
        month_share=day_share=top5=concentration_ratio=None
    positive_month_frac=sum(math.fsum(v)>0 for v in months.values())/len(months) if months else None
    positive_quarters=sum(math.fsum(v)>0 for v in quarters.values())
    lomo=all(mean([v for e,v in zip(events,vals) if date.fromisoformat(e["entry_day"]).strftime("%Y-%m")!=m])>0 for m in months) if len(months)>1 else False
    gains=math.fsum(v for v in vals if v>0); losses=-math.fsum(v for v in vals if v<0)
    return {"mean_base_bps":mean(vals),"mean_stress_bps":mean(stress),"median_base_bps":statistics.median(vals) if vals else None,
            "win_rate_base":sum(v>0 for v in vals)/len(vals) if vals else None,"profit_factor_base":gains/losses if losses>0 else None,
            "positive_active_month_fraction":positive_month_frac,"positive_quarters":positive_quarters,"leave_one_month_out_all_positive":lomo,
            "month_abs_pnl_share":month_share,"day_abs_pnl_share":day_share,"top5_abs_pnl_share":top5,"concentration_ratio":concentration_ratio}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-cache",required=True); ap.add_argument("--price-manifest",required=True)
    ap.add_argument("--funding-bindings",required=True); ap.add_argument("--v03-runner-zip",required=True)
    ap.add_argument("--authorization",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args()
    auth=json.loads(Path(a.authorization).read_text())
    if auth.get("status")!="AUTHORIZED_ONE_SHOT_2025_CONFIRMATION" or auth.get("access_2026_plus") is not False: raise RuntimeError("AUTHORIZATION_FAIL")
    out=Path(a.output)
    if out.exists(): raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True)
    price_manifest=json.loads(Path(a.price_manifest).read_text())
    if price_manifest["document_id"]!="CED_1D_2025_SOURCE_MANIFEST_V0.2": raise RuntimeError("PRICE_MANIFEST_ID")
    bindings=load_bindings(Path(a.funding_bindings))
    with tempfile.TemporaryDirectory() as td:
        hyp=load_original_hypotheses(Path(a.v03_runner_zip),Path(td))
        bars=build_bars(Path(a.price_cache),price_manifest)
        ledgers={}; inference={}
        for cid,cfg0 in CELLS.items():
            cfg={k:v for k,v in cfg0.items() if k!="role"}
            rows=[add_funding_bounds(e,cfg["symbol"],bindings) for e in generate_2025_events(hyp,bars[cfg["symbol"]],cfg)]
            ledgers[cid]=rows
            inference[cid]=[e for e in rows if e["status"]=="TRADE" and complete_signal_week(date.fromisoformat(e["signal_day"]))]
    plan=WeekPlan(); results={}
    for cid in CELLS:
        es=inference[cid]; sg=sample_gate(es)
        lower=path_metrics(es,"base_lower_bps","stress_lower_bps"); upper=path_metrics(es,"base_upper_bps","stress_upper_bps")
        lower["bootstrap"]=bootstrap(es,"base_lower_bps",plan) if es else {"status":"INSUFFICIENT_SAMPLE","p_raw":None,"ci_low":None,"ci_high":None}
        upper["bootstrap"]=bootstrap(es,"base_upper_bps",plan) if es else {"status":"INSUFFICIENT_SAMPLE","p_raw":None,"ci_low":None,"ci_high":None}
        results[cid]={"config":CELLS[cid],"ledger_status_counts":{s:sum(r["status"]==s for r in ledgers[cid]) for s in ("TRADE","OVERLAP_BLOCKED","DATA_UNAVAILABLE")},
                      "inference_events":len(es),"sample_gate":sg,"lower":lower,"upper":upper}
    for path in ("lower","upper"):
        q=holm({cid:(results[cid][path]["bootstrap"].get("p_raw") if results[cid]["sample_gate"]["pass"] and results[cid][path]["bootstrap"].get("status")=="PASS" else 1.0) for cid in CELLS})
        for cid in CELLS: results[cid][path]["holm_adjusted_p"]=q[cid]
    for target in TARGETS:
        for path in ("lower","upper"):
            m=results[target][path]; qualifiers=[]
            for nid in NEIGHBORS[target]:
                nm=results[nid][path]
                ok=results[nid]["sample_gate"]["pass"] and nm["mean_base_bps"] is not None and nm["mean_base_bps"]>0 and m["mean_base_bps"] is not None and nm["mean_base_bps"]>=.5*m["mean_base_bps"]
                if ok: qualifiers.append(nid)
            frac=len(qualifiers)/len(NEIGHBORS[target])
            m["neighbor_ids"]=list(NEIGHBORS[target]);m["qualifying_neighbors"]=qualifiers;m["neighbor_fraction"]=frac
            m["gates"]={
              "sample":results[target]["sample_gate"]["pass"],
              "mean_base_gt_2":m["mean_base_bps"] is not None and m["mean_base_bps"]>2,
              "ci_lower_gt_0":m["bootstrap"].get("ci_low") is not None and m["bootstrap"]["ci_low"]>0,
              "holm_le_005":m["holm_adjusted_p"]<=.05,
              "stress_mean_ge_0":m["mean_stress_bps"] is not None and m["mean_stress_bps"]>=0,
              "positive_month_fraction_ge_2_3":m["positive_active_month_fraction"] is not None and m["positive_active_month_fraction"]>=2/3,
              "positive_quarters_ge_3":m["positive_quarters"]>=3,
              "neighbor_fraction_ge_075":frac>=.75,
              "concentration":m["concentration_ratio"] is not None and m["concentration_ratio"]<=1,
              "leave_one_month_out":bool(m["leave_one_month_out_all_positive"])
            }
            m["strict_v02_pass"]=all(m["gates"].values())
        if results[target]["lower"]["strict_v02_pass"]:
            verdict="V02_CONFIRMATION_PASS_ROBUST_TO_MARK_INTERVAL__EXECUTION_FEASIBILITY_BLOCKED"
        elif not results[target]["upper"]["strict_v02_pass"]:
            verdict="V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL"
        else:
            verdict="FUNDING_MARK_PRICE_INTERVAL_AMBIGUOUS"
        if not results[target]["sample_gate"]["pass"]: verdict="INSUFFICIENT_SAMPLE"
        results[target]["target_verdict"]=verdict
    ledger_rows=[]
    for cid,rows in ledgers.items():
        for r in rows: ledger_rows.append({"combination_id":cid,**r})
    ledger_fields=sorted({k for r in ledger_rows for k in r})
    with (out/"CED1D_2025_EVENT_LEDGER.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=ledger_fields,lineterminator="\n");w.writeheader();w.writerows(ledger_rows)
    receipt={"document_id":"CED_1D_2025_ONE_SHOT_CONFIRMATION_RECEIPT_V0.1","status":"ONE_SHOT_2025_CONFIRMATION_COMPLETE",
             "targets":list(TARGETS),"holm_family":list(CELLS),"results":results,
             "source":{"price_manifest":price_manifest["document_id"],"funding_binding_source":"FUNDING_MARK_INTERVAL_SOURCE_GATE"},
             "governance":{"2025_opened_once":True,"2026_accessed":False,"post_outcome_tuning":False,"live_trading":False,"orders":False,"exchange_mutation":False,"main_merge":False}}
    receipt["fingerprint"]=hashlib.sha256(canonical(receipt)).hexdigest()
    (out/"CED_1D_2025_ONE_SHOT_CONFIRMATION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    summary={t:{"verdict":results[t]["target_verdict"],"n":results[t]["inference_events"],
                "lower_mean":results[t]["lower"]["mean_base_bps"],"upper_mean":results[t]["upper"]["mean_base_bps"],
                "lower_p":results[t]["lower"]["bootstrap"].get("p_raw"),"upper_p":results[t]["upper"]["bootstrap"].get("p_raw"),
                "lower_holm":results[t]["lower"]["holm_adjusted_p"],"upper_holm":results[t]["upper"]["holm_adjusted_p"]} for t in TARGETS}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
