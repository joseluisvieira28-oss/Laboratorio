#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, io, json, math, zipfile
from collections import Counter, deque
from pathlib import Path
import lz4.frame

LAB_ID="L2R-OVERLAY-ETF-CME-PRET0-001"
IMPLEMENTATION_VERSION="0.1.1-SPARSE"
EXPECTED_ETF_ARTIFACT_SHA256="40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1"
EXPECTED_ETF_ROWS=50
EXPECTED_NONZERO_ROWS=49
EXPECTED_SPARSE_OBJECTS=92
EXPECTED_SOURCE_EVALUABLE_ROWS=46
SOURCE_GATED_DATES={"2025-10-22","2025-11-18","2025-11-26"}
MAX_LATENESS_NS=1_100_000_000
PRET0_MAX_STALENESS_NS=1_100_000_000
HORIZONS_MS=(1000,5000,15000,60000)
CELLS=(
 ("R1_Y5",1000,5000),
 ("R1_Y15",1000,15000),
 ("R1_Y60",1000,60000),
 ("R5_Y15",5000,15000),
 ("R5_Y60",5000,60000),
 ("R15_Y60",15000,60000),
)
READ_CHUNK=1024*1024

class FailClosed(RuntimeError): pass

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*READ_CHUNK),b""): h.update(b)
    return h.hexdigest()

def hashes_file(p:Path):
    h=hashlib.sha256(); m=hashlib.md5(); n=0
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*READ_CHUNK),b""):
            n+=len(b); h.update(b); m.update(b)
    return n,h.hexdigest(),m.hexdigest()

def ns_from_iso(s:str)->int:
    d=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp()*1_000_000_000)

def ns_from_date(s:str)->int:
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())*1_000_000_000

def ns_to_iso(ns:int)->str:
    sec,rem=divmod(ns,1_000_000_000)
    d=dt.datetime.fromtimestamp(sec,tz=dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S")+f".{rem:09d}Z"

def mean(xs): return sum(xs)/len(xs) if xs else None

def finite(v,name):
    if isinstance(v,bool): raise FailClosed(f"boolean {name}")
    try: x=float(v)
    except Exception as e: raise FailClosed(f"non-numeric {name}") from e
    if not math.isfinite(x): raise FailClosed(f"non-finite {name}")
    return x

def extract_state(o):
    if not isinstance(o,dict) or "raw" not in o or "time" not in o: raise FailClosed("schema top-level")
    raw=o["raw"]; data=raw.get("data") if isinstance(raw,dict) else None
    if not isinstance(data,dict) or raw.get("channel")!="l2Book" or data.get("coin")!="BTC": raise FailClosed("schema raw/data")
    p=data.get("time"); levels=data.get("levels")
    if isinstance(p,bool) or not isinstance(p,int): raise FailClosed("payload time")
    if not isinstance(levels,list) or len(levels)!=2: raise FailClosed("levels")
    bids,asks=levels
    if len(bids)<5 or len(asks)<5: raise FailClosed("top5")
    bp=[]; ap=[]; bsz=[]; asz=[]
    for side,pxs,szs in ((bids,bp,bsz),(asks,ap,asz)):
        for i,l in enumerate(side):
            if not isinstance(l,dict): raise FailClosed("level object")
            px=finite(l.get("px"),"px"); sz=finite(l.get("sz"),"sz")
            if px<=0 or sz<0: raise FailClosed("bad level")
            pxs.append(px)
            if i<5: szs.append(sz)
    if not all(bp[i]>bp[i+1] for i in range(4)): raise FailClosed("bid order")
    if not all(ap[i]<ap[i+1] for i in range(4)): raise FailClosed("ask order")
    if bp[0]>=ap[0]: raise FailClosed("crossed book")
    return {"payload_ms":p,"mid":(bp[0]+ap[0])/2,"bid":bp[0],"ask":ap[0],
      "bid_prices_all":tuple(bp),"ask_prices_all":tuple(ap),
      "bid_depth5":sum(bsz),"ask_depth5":sum(asz)}

def parse_etf_artifact(p:Path):
    if sha256_file(p)!=EXPECTED_ETF_ARTIFACT_SHA256: raise FailClosed("ETF artifact SHA256 mismatch")
    with zipfile.ZipFile(p) as z:
        target=next((n for n in z.namelist() if n.endswith("oos_2025_observations.csv")),None)
        if not target: raise FailClosed("ETF observations CSV absent")
        rows=list(csv.DictReader(io.StringIO(z.read(target).decode("utf-8-sig"))))
    if len(rows)!=EXPECTED_ETF_ROWS: raise FailClosed("ETF row count mismatch")
    if rows[0]["entry"]!="2025-01-15" or rows[-1]["exit"]!="2025-12-31": raise FailClosed("ETF boundary mismatch")
    out=[]
    for i,r in enumerate(rows):
        pos=int(float(r["position"]))
        if pos not in (-1,0,1): raise FailClosed("illegal ETF position")
        out.append({"idx":i,"entry":r["entry"],"position":pos,"t0_ns":ns_from_date(r["entry"]+"T00:00:00")})
    if sum(x["position"]!=0 for x in out)!=EXPECTED_NONZERO_ROWS: raise FailClosed("ETF nonzero row count mismatch")
    return out

def load_sparse_manifest(p:Path):
    with p.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=EXPECTED_SPARSE_OBJECTS: raise FailClosed(f"sparse manifest rows {len(rows)} != {EXPECTED_SPARSE_OBJECTS}")
    by_entry={}; seen=set()
    for r in rows:
        key=r["key"]
        if key in seen: raise FailClosed("duplicate source key")
        seen.add(key)
        role=r["role"]; entry=r["entry"]
        if role not in ("prior","t0"): raise FailClosed("illegal source role")
        by_entry.setdefault(entry,{})[role]=r
    if len(by_entry)!=EXPECTED_SOURCE_EVALUABLE_ROWS: raise FailClosed("source-evaluable entry count mismatch")
    for entry,d in by_entry.items():
        if set(d)!={"prior","t0"}: raise FailClosed(f"incomplete source pair {entry}")
    return rows,by_entry

def iter_hour(path:Path):
    with lz4.frame.open(path,"rb") as f:
        for rawline in f:
            if rawline.strip():
                o=json.loads(rawline)
                yield ns_from_iso(o["time"]),extract_state(o)

def verify_source_object(base:Path,row):
    p=base/"HL_L2R_2025_BTC_RAW_V0_1"/Path(*row["local_relpath"].replace("\\","/").split("/"))
    if not p.exists(): raise FailClosed(f"source object missing {row['key']}")
    n,sha,md5=hashes_file(p)
    if n!=int(row["content_length"]) or sha.lower()!=row["sha256"].lower() or md5.lower()!=row["md5"].lower():
        raise FailClosed(f"source object hash mismatch {row['key']}")
    return p

def analyze_entry(base:Path,rec,pair):
    t0=rec["t0_ns"]; cutoff=t0-60_000_000_000; prior_start=t0-3_600_000_000_000
    paths={role:verify_source_object(base,pair[role]) for role in ("prior","t0")}
    active={}; archive={}; queues={h:deque() for h in HORIZONS_MS}
    eid=0; prev=None; last_payload=None; last_env=None
    ref_mid=None; ref_env=None; snap=None; sync_env=None; totals=Counter()

    def resolve_event(i,h,env,st):
        ev=active.get(i) or archive.get(i)
        if ev is None or h in ev["resolved"]: return
        ev["resolved"].add(h); ev["h"][h]={"env":env,"st":st} if st is not None else None
        if len(ev["resolved"])==len(HORIZONS_MS):
            if ev.get("selected",False): archive[i]=ev
            active.pop(i,None)

    def resolve_due(env,st):
        for h in HORIZONS_MS:
            q=queues[h]
            while q and q[0][0]<=env:
                target,i=q.popleft()
                resolve_event(i,h,env,st if env-target<=MAX_LATENESS_NS else None)

    def create_event(env,side,pre_depth):
        nonlocal eid
        i=eid; eid+=1
        ev={"id":i,"event_env":env,"side":side,"direction":1 if side=="ASK" else -1,
            "pre_depth":pre_depth,"h":{},"resolved":set(),"selected":False}
        active[i]=ev
        for h in HORIZONS_MS: queues[h].append((env+h*1_000_000,i))

    def take_snapshot():
        nonlocal snap
        if snap is not None: return
        pret0_ok=ref_env is not None and ref_env<=t0 and t0-ref_env<=PRET0_MAX_STALENESS_NS
        cells={}
        for name,rh,yh in CELLS:
            best=None
            for ev in active.values():
                rr=ev["h"].get(rh)
                if rr is None or rr["env"]>t0: continue
                if ev["event_env"]+yh*1_000_000<=t0 or ev["pre_depth"]<=0: continue
                rstate=rr["st"]; depth=rstate["ask_depth5"] if ev["side"]=="ASK" else rstate["bid_depth5"]
                if depth/ev["pre_depth"]>=1.0: continue
                k=(rr["env"],ev["event_env"],ev["id"])
                if best is None or k>best[0]: best=(k,ev)
            if best is None:
                cells[name]={"class":"NO_ACTIVE_WEAK"}
            else:
                ev=best[1]; ev["selected"]=True
                cells[name]={"class":"ALIGNED" if ev["direction"]==rec["position"] else "OPPOSED",
                  "event_id":ev["id"],"event_direction":ev["direction"],"event_env":ev["event_env"],
                  "r_env":ev["h"][rh]["env"],"y_target":ev["event_env"]+yh*1_000_000}
        snap={"pret0_ok":pret0_ok,"pret0_mid":ref_mid if pret0_ok else None,
              "pret0_env":ref_env if pret0_ok else None,"cells":cells}

    def consume(env,st):
        nonlocal prev,ref_mid,ref_env
        if env>t0 and snap is None: take_snapshot()
        resolve_due(env,st)
        if prev is not None:
            aw=st["ask"]>prev["ask"]; bw=st["bid"]<prev["bid"]
            if aw and bw: totals["ambiguous"]+=1
            elif aw:
                if any(p==prev["ask"] for p in st["ask_prices_all"]): raise FailClosed("prior ask still present")
                totals["ask_sweeps"]+=1; create_event(env,"ASK",prev["ask_depth5"])
            elif bw:
                if any(p==prev["bid"] for p in st["bid_prices_all"]): raise FailClosed("prior bid still present")
                totals["bid_sweeps"]+=1; create_event(env,"BID",prev["bid_depth5"])
        prev=st
        if env<=t0: ref_mid=st["mid"]; ref_env=env
        if env==t0 and snap is None: take_snapshot()

    for role in ("prior","t0"):
        for env,st in iter_hour(paths[role]):
            totals["records"]+=1
            if last_env is not None and env<last_env: raise FailClosed("envelope backwards")
            p=st["payload_ms"]; future=p*1_000_000>env; last_env=env
            if last_payload is not None and p<last_payload:
                totals["stale"]+=1; continue
            if not future: last_payload=p
            totals["accepted"]+=1
            if sync_env is None and not future and p*1_000_000>=prior_start: sync_env=env
            consume(env,st)
    if snap is None: take_snapshot()
    if sync_env is None or sync_env>cutoff: raise FailClosed(f"normalization convergence not proven before cutoff for {rec['entry']}")

    ledgers=[]
    for name,rh,yh in CELLS:
        c=snap["cells"][name]; cls=c["class"]; residual=None
        if cls in ("ALIGNED","OPPOSED"):
            ev=archive.get(c["event_id"]) or active.get(c["event_id"]); y=ev["h"].get(yh) if ev else None
            if not snap["pret0_ok"] or y is None or y["st"] is None:
                cls="SOURCE_GATED"
            else:
                residual=rec["position"]*10000.0*(y["st"]["mid"]/snap["pret0_mid"]-1.0)
        ledgers.append({"entry":rec["entry"],"position":rec["position"],"cell":name,"classification":cls,
          "pret0_reference_time":ns_to_iso(snap["pret0_env"]) if snap["pret0_env"] is not None else "",
          "event_time":ns_to_iso(c["event_env"]) if c.get("event_env") else "",
          "r_observation_time":ns_to_iso(c["r_env"]) if c.get("r_env") else "",
          "y_target_time":ns_to_iso(c["y_target"]) if c.get("y_target") else "",
          "residual_bps":"" if residual is None else residual,
          "delay_benefit_bps":"" if residual is None or cls!="OPPOSED" else -residual})
    return {"entry":rec["entry"],"pret0_evaluable":bool(snap["pret0_ok"]),
      "pret0_reference_time":ns_to_iso(snap["pret0_env"]) if snap["pret0_env"] is not None else None,
      "sync_margin_seconds":(cutoff-sync_env)/1e9,"ledgers":ledgers,"totals":dict(totals)}

def run(base:Path,etf_artifact:Path,source_manifest:Path):
    etf=parse_etf_artifact(etf_artifact); _,by_entry=load_sparse_manifest(source_manifest)
    nonzero=[r for r in etf if r["position"]!=0]
    ledgers=[]; per_entry=[]; totals=Counter(); verified_objects=0
    for rec in nonzero:
        if rec["entry"] in SOURCE_GATED_DATES:
            for name,_,_ in CELLS:
                ledgers.append({"entry":rec["entry"],"position":rec["position"],"cell":name,"classification":"SOURCE_GATED",
                  "pret0_reference_time":"","event_time":"","r_observation_time":"","y_target_time":"","residual_bps":"","delay_benefit_bps":""})
            per_entry.append({"entry":rec["entry"],"source_gate":False,"pret0_evaluable":False}); continue
        pair=by_entry.get(rec["entry"])
        if not pair: raise FailClosed(f"missing sparse source pair {rec['entry']}")
        res=analyze_entry(base,rec,pair); verified_objects+=2
        ledgers.extend(res["ledgers"]); per_entry.append({"source_gate":True,**res}); totals.update(res["totals"])

    cell_stats={}
    for name,_,_ in CELLS:
        vals_a=[]; vals_o=[]; counts=Counter()
        for x in ledgers:
            if x["cell"]!=name: continue
            cls=x["classification"]; counts[cls]+=1
            if x["residual_bps"]!="":
                v=float(x["residual_bps"]); (vals_a if cls=="ALIGNED" else vals_o).append(v)
        sep=(mean(vals_a)-mean(vals_o)) if vals_a and vals_o else None
        cell_stats[name]={"parent_nonzero_rows":len(nonzero),"aligned_n":len(vals_a),"opposed_n":len(vals_o),
          "no_active_weak_n":counts["NO_ACTIVE_WEAK"],"source_gated_n":counts["SOURCE_GATED"],
          "aligned_mean_residual_bps":mean(vals_a),"opposed_mean_residual_bps":mean(vals_o),
          "separation_bps":sep,"opposed_mean_delay_benefit_bps":(-mean(vals_o)) if vals_o else None,
          "sample_viable":len(vals_a)>=8 and len(vals_o)>=8}

    global_source_evaluable=sum(1 for x in per_entry if x.get("source_gate") and x.get("pret0_evaluable"))
    all_cells_viable=all(s["sample_viable"] for s in cell_stats.values())
    seps=[s["separation_bps"] for s in cell_stats.values() if s["sample_viable"]]
    delays=[s["opposed_mean_delay_benefit_bps"] for s in cell_stats.values() if s["sample_viable"]]
    pos_cells=sum(1 for s in cell_stats.values() if s["sample_viable"] and s["separation_bps"]>0)
    pos_by_r={str(rh):any(cell_stats[name]["sample_viable"] and cell_stats[name]["separation_bps"]>0
                         for name,crh,_ in CELLS if crh==rh) for rh in (1000,5000,15000)}
    source_sample_ok=global_source_evaluable>=40 and all_cells_viable and len(seps)==6
    support={"source_sample_viability":source_sample_ok,
      "panel_equal_weight_separation_positive":source_sample_ok and mean(seps)>0,
      "at_least_4_of_6_positive_cells":source_sample_ok and pos_cells>=4,
      "each_R_family_positive":source_sample_ok and all(pos_by_r.values()),
      "panel_opposed_delay_benefit_positive":source_sample_ok and mean(delays)>0}
    if not source_sample_ok: classification="DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE"
    elif all(support.values()): classification="DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED"
    else: classification="DEVELOPMENT_OVERLAY_NO_SUPPORT"

    outdir=base/"_EVIDENCE_L2R_OVERLAY_ETF_CME_PRET0_V0_1"; outdir.mkdir(parents=True,exist_ok=True)
    ledger_path=outdir/"L2R_OVERLAY_ETF_CME_PRET0_001_2025_DEVELOPMENT_LEDGER_V0_1.csv"
    fields=["entry","position","cell","classification","pret0_reference_time","event_time","r_observation_time","y_target_time","residual_bps","delay_benefit_bps"]
    with ledger_path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(ledgers)
    cells_path=outdir/"L2R_OVERLAY_ETF_CME_PRET0_001_2025_CELL_SUMMARY_V0_1.csv"
    with cells_path.open("w",encoding="utf-8-sig",newline="") as f:
        fs=["cell"]+list(next(iter(cell_stats.values())).keys()); w=csv.DictWriter(f,fieldnames=fs); w.writeheader()
        for name,_,_ in CELLS: w.writerow({"cell":name,**cell_stats[name]})
    margins=[x["sync_margin_seconds"] for x in per_entry if x.get("source_gate") and "sync_margin_seconds" in x]
    receipt={"schema_version":"0.1.1","implementation_version":IMPLEMENTATION_VERSION,"lab_id":LAB_ID,
      "classification":classification,"evidence_status":"POST_PARENT_2025_DEVELOPMENT_ONLY__NOT_INDEPENDENT_VALIDATION",
      "parent_etf_artifact_sha256":EXPECTED_ETF_ARTIFACT_SHA256,
      "parent_l2_manifest_sha256":"767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3",
      "source_transport":"BYTE_PRESERVING_DRIVE_ARCHIVE_SPARSE_REPLAY",
      "parent_etf_rows":len(etf),"parent_nonzero_rows":len(nonzero),"source_gated_dates":sorted(SOURCE_GATED_DATES),
      "global_source_evaluable_rows":global_source_evaluable,"sparse_raw_objects_verified":verified_objects,
      "minimum_normalization_margin_seconds":min(margins) if margins else None,
      "reference_rule":{"type":"LAST_ACCEPTED_AT_OR_BEFORE_T0","max_staleness_ms":1100,"future_state_allowed":False,"fallback_to_R":False},
      "cell_summary":cell_stats,
      "panel":{"equal_weight_separation_bps":mean(seps) if len(seps)==6 else None,"positive_cells":pos_cells,
        "positive_by_R":pos_by_r,"equal_weight_opposed_delay_benefit_bps":mean(delays) if len(delays)==6 else None,
        "support_gate":support},
      "raw_scan":{"objects_verified":verified_objects,"accepted_states":totals["accepted"],
        "stale_late_payload":totals["stale"],"ambiguous_sweeps":totals["ambiguous"]},
      "firewalls":{"access_2026":False,"market_data_network":False,"orders":False,"live_trading":False,"exchange_mutation":False,"main_merge":False},
      "interpretation":"Causal PRET0 reference-price entry-timing development diagnostic only; no executable fill claim."}
    receipt_path=outdir/"L2R_OVERLAY_ETF_CME_PRET0_001_2025_DEVELOPMENT_RECEIPT_V0_1.json"
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    evidence=base/"L2R_OVERLAY_ETF_CME_PRET0_001_2025_DEVELOPMENT_EVIDENCE_V0_1.zip"
    with zipfile.ZipFile(evidence,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(ledger_path,ledger_path.name); z.write(cells_path,cells_path.name); z.write(receipt_path,receipt_path.name)
    print(json.dumps(receipt,indent=2,sort_keys=True)); print("EVIDENCE_ZIP",evidence); print("EVIDENCE_SHA256",sha256_file(evidence))
    return receipt

def self_test():
    t0=10_000_000_000
    def ref(last_env,last_mid):
        if last_env is None or last_mid is None or last_env>t0 or t0-last_env>PRET0_MAX_STALENESS_NS: return None
        return last_mid
    assert ref(t0-500_000_000,100.0)==100.0
    assert ref(t0,101.0)==101.0
    assert ref(t0-1_100_000_000,99.0)==99.0
    assert ref(t0-1_100_000_001,99.0) is None
    assert ref(t0+1,99.0) is None
    assert 1*10000*(101/100-1)>0
    assert -1*10000*(99/100-1)>0
    a=[1.0,2.0,0.5,1.5,1.2,0.8,1.1,1.3]; o=[-1.0,-0.5,-1.5,-0.8,-1.2,-0.7,-1.1,-0.9]
    assert mean(a)-mean(o)>0 and -mean(o)>0
    print("SELF_TEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default=str(Path.home()/"Desktop"/"L2R_2025_BTC_VALIDATION_LOCAL"))
    ap.add_argument("--etf-artifact"); ap.add_argument("--source-manifest"); ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return
    if not args.etf_artifact or not args.source_manifest: raise SystemExit("--etf-artifact and --source-manifest are required")
    run(Path(args.base).resolve(),Path(args.etf_artifact).resolve(),Path(args.source_manifest).resolve())

if __name__=="__main__": main()
