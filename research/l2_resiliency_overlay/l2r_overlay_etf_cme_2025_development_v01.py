#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, io, json, math, re, zipfile
from collections import Counter, deque
from pathlib import Path

LAB_ID="L2R-OVERLAY-ETF-CME-001"
IMPLEMENTATION_VERSION="0.1"
EXPECTED_MANIFEST_SHA256="767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3"
EXPECTED_OBJECTS=8400
EXPECTED_BYTES=8975275014
EXPECTED_ETF_ARTIFACT_SHA256="40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1"
EXPECTED_ETF_ROWS=50
MAX_LATENESS_NS=1_100_000_000
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
KEY_RE=re.compile(r"^market_data/(2025\d{4})/([0-9]|1[0-9]|2[0-3])/l2Book/BTC\.lz4$")
ISO_RE=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z?$")

class FailClosed(RuntimeError): pass

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*READ_CHUNK),b""): h.update(b)
    return h.hexdigest()

def parse_env_ns(s:str)->int:
    m=ISO_RE.fullmatch(s.strip())
    if not m: raise FailClosed(f"invalid envelope time {s}")
    base,frac=m.groups()
    d=dt.datetime.strptime(base,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp())*1_000_000_000+int(((frac or "")+"000000000")[:9])

def ns_from_date(s:str)->int:
    d=dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp())*1_000_000_000

def ns_to_iso(ns:int)->str:
    sec,rem=divmod(ns,1_000_000_000)
    d=dt.datetime.fromtimestamp(sec,tz=dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S")+f".{rem:09d}Z"

def key_hour(key:str)->dt.datetime:
    m=KEY_RE.fullmatch(key)
    if not m: raise FailClosed(f"illegal key {key}")
    ymd,hs=m.groups()
    return dt.datetime.strptime(ymd+f"{int(hs):02d}","%Y%m%d%H").replace(tzinfo=dt.timezone.utc)

def key_for_hour(d:dt.datetime)->str:
    return f"market_data/{d:%Y%m%d}/{d.hour}/l2Book/BTC.lz4"

def key_bounds_ns(key:str):
    d=key_hour(key); s=int(d.timestamp())*1_000_000_000
    return s,s+3_600_000_000_000

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
    return {
      "payload_ms":p,"mid":(bp[0]+ap[0])/2,
      "bid":bp[0],"ask":ap[0],
      "bid_prices_all":tuple(bp),"ask_prices_all":tuple(ap),
      "bid_depth5":sum(bsz),"ask_depth5":sum(asz)
    }

def parse_etf_artifact(p:Path):
    if sha256_file(p)!=EXPECTED_ETF_ARTIFACT_SHA256:
        raise FailClosed("ETF artifact SHA256 mismatch")
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
        target=next((n for n in names if n.endswith("oos_2025_observations.csv")),None)
        if not target: raise FailClosed("ETF observations CSV absent")
        rows=list(csv.DictReader(io.StringIO(z.read(target).decode("utf-8-sig"))))
    if len(rows)!=EXPECTED_ETF_ROWS: raise FailClosed(f"ETF row count {len(rows)} != 50")
    if rows[0]["entry"]!="2025-01-15" or rows[-1]["exit"]!="2025-12-31":
        raise FailClosed("ETF boundary identity mismatch")
    out=[]
    for i,r in enumerate(rows):
        pos=int(float(r["position"]))
        if pos not in (-1,0,1): raise FailClosed("illegal ETF position")
        t0=ns_from_date(r["entry"]+"T00:00:00")
        out.append({"idx":i,"entry":r["entry"],"position":pos,"t0_ns":t0})
    return out

def build_segments(rows):
    rows=sorted(rows,key=lambda r:key_hour(r["key"]))
    out=[]; cur=[]; prev=None
    for r in rows:
        h=key_hour(r["key"])
        if prev is None or h==prev+dt.timedelta(hours=1): cur.append(r)
        else: out.append(cur); cur=[r]
        prev=h
    if cur: out.append(cur)
    return out

def mean(xs): return sum(xs)/len(xs) if xs else None

def run(base:Path, etf_artifact:Path):
    manifest=base/"_EVIDENCE_2025_VALIDATION_V0_1"/"L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv"
    if not manifest.exists(): raise FailClosed(f"manifest missing: {manifest}")
    if sha256_file(manifest)!=EXPECTED_MANIFEST_SHA256: raise FailClosed("canonical manifest SHA mismatch")
    with manifest.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=EXPECTED_OBJECTS or sum(int(r["content_length"]) for r in rows)!=EXPECTED_BYTES:
        raise FailClosed("canonical corpus identity mismatch")
    manifest_by_key={r["key"]:r for r in rows}
    etf=parse_etf_artifact(etf_artifact)
    nonzero=[r for r in etf if r["position"]!=0]

    # Exact source viability known before outcome evaluation: current and prior hours must exist.
    for rec in nonzero:
        t0=dt.datetime.fromtimestamp(rec["t0_ns"]/1e9,tz=dt.timezone.utc)
        rec["source_gate"]=(
          key_for_hour(t0) in manifest_by_key and
          key_for_hour(t0-dt.timedelta(hours=1)) in manifest_by_key
        )
        rec["t0_mid"]=None
        rec["snapshotted"]=False
        rec["cells"]={name:{"class":"SOURCE_GATED" if not rec["source_gate"] else None} for name,_,_ in CELLS}

    t0s=sorted([r["t0_ns"] for r in nonzero if r["source_gate"]])
    rec_by_t0={r["t0_ns"]:r for r in nonzero if r["source_gate"]}
    t0_index=0
    mid_index=0

    active={}
    selected_archive={}
    queues={h:deque() for h in HORIZONS_MS}
    eid=0
    prev=None
    last_payload=None
    last_env=None
    totals=Counter()

    def resolve_event(i,h,env,st):
        ev=active.get(i) or selected_archive.get(i)
        if ev is None or h in ev["resolved"]: return
        ev["resolved"].add(h)
        ev["h"][h]={"env":env,"st":st} if st is not None else None
        # If selected anywhere, retain; otherwise delete once max horizon resolved.
        if len(ev["resolved"])==len(HORIZONS_MS):
            if ev.get("selected_count",0)>0:
                selected_archive[i]=ev
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
            "pre_depth":pre_depth,"h":{},"resolved":set(),"selected_count":0}
        active[i]=ev
        for h in HORIZONS_MS: queues[h].append((env+h*1_000_000,i))

    def snapshot(rec):
        if rec["snapshotted"] or not rec["source_gate"]: return
        t0=rec["t0_ns"]
        for name,rh,yh in CELLS:
            best=None
            for ev in active.values():
                rr=ev["h"].get(rh)
                if rr is None: continue
                if rr["env"]>t0: continue
                y_target=ev["event_env"]+yh*1_000_000
                if y_target<=t0: continue
                if ev["pre_depth"]<=0: continue
                rstate=rr["st"]
                depth=rstate["ask_depth5"] if ev["side"]=="ASK" else rstate["bid_depth5"]
                if depth/ev["pre_depth"]>=1.0: continue
                key=(rr["env"],ev["event_env"],ev["id"])
                if best is None or key>best[0]: best=(key,ev)
            if best is None:
                rec["cells"][name]={"class":"NO_ACTIVE_WEAK"}
            else:
                ev=best[1]; ev["selected_count"]+=1
                rec["cells"][name]={
                  "class":"ALIGNED" if ev["direction"]==rec["position"] else "OPPOSED",
                  "event_id":ev["id"],"event_direction":ev["direction"],
                  "event_env":ev["event_env"],"r_env":ev["h"][rh]["env"],
                  "y_target":ev["event_env"]+yh*1_000_000
                }
        rec["snapshotted"]=True

    def snapshot_before(env):
        nonlocal t0_index
        while t0_index<len(t0s) and t0s[t0_index]<env:
            snapshot(rec_by_t0[t0s[t0_index]])
            t0_index+=1

    def after_state(env,st):
        nonlocal t0_index,mid_index
        # Exact equality can use the accepted state at T0 causally.
        while t0_index<len(t0s) and t0s[t0_index]==env:
            snapshot(rec_by_t0[t0s[t0_index]])
            t0_index+=1
        # First accepted midpoint at/after each exact T0, max lateness 1100ms.
        while mid_index<len(t0s) and t0s[mid_index]<=env:
            t0=t0s[mid_index]
            if env-t0<=MAX_LATENESS_NS:
                rec_by_t0[t0]["t0_mid"]=st["mid"]
            mid_index+=1

    def consume(env,st):
        nonlocal prev
        snapshot_before(env)
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
        after_state(env,st)

    segments=build_segments(rows)
    for seg_i,seg in enumerate(segments,1):
        prev=None; last_payload=None; last_env=None
        # active events cannot cross immutable source gaps.
        active.clear()
        for h in HORIZONS_MS: queues[h].clear()
        for row in seg:
            key=row["key"]
            path=base/"HL_L2R_2025_BTC_RAW_V0_1"/Path(*str(row["local_relpath"]).replace("\\","/").split("/"))
            if not path.exists(): raise FailClosed(f"raw object missing {path}")
            start,end=key_bounds_ns(key)
            import lz4.frame
            dec=lz4.frame.LZ4FrameDecompressor(); pending=b""
            hsha=hashlib.sha256(); hmd5=hashlib.md5(); actual=0
            def proc(line):
                nonlocal last_env,last_payload
                o=json.loads(line); env=parse_env_ns(o["time"])
                if not(start<=env<end): raise FailClosed("envelope outside key hour")
                st=extract_state(o); p=st["payload_ms"]
                if last_env is not None and env<last_env: raise FailClosed("envelope backwards")
                future=p*1_000_000>env; last_env=env
                if last_payload is not None and p<last_payload:
                    totals["stale"]+=1; return
                if not future: last_payload=p
                totals["accepted"]+=1
                consume(env,st)
            with path.open("rb") as f:
                while True:
                    b=f.read(READ_CHUNK)
                    if not b: break
                    actual+=len(b); hsha.update(b); hmd5.update(b)
                    out=dec.decompress(b)
                    if not out: continue
                    pending+=out; parts=pending.split(b"\n"); pending=parts.pop()
                    for line in parts:
                        if line.strip(): proc(line)
            if pending.strip(): proc(pending)
            if not dec.eof: raise FailClosed(f"incomplete LZ4 {key}")
            if actual!=int(row["content_length"]) or hsha.hexdigest().lower()!=row["sha256"].lower() or hmd5.hexdigest().lower()!=row["md5"].lower():
                raise FailClosed(f"byte/hash mismatch {key}")
            totals["objects"]+=1
        # snapshot T0s inside/at end of segment if their clock precedes the next source.
        if last_env is not None: snapshot_before(last_env+1)
        # unresolved selected events at a segment end cannot produce Y and remain outcome-gated.
        for ev in list(active.values()):
            if ev.get("selected_count",0)>0: selected_archive[ev["id"]]=ev

    # Any T0 with present keys but never snapshotted is source/timing gated.
    while t0_index<len(t0s):
        snapshot(rec_by_t0[t0s[t0_index]]); t0_index+=1

    # Compute outcomes without parent weekly PnL.
    ledgers=[]
    cell_stats={}
    for name,rh,yh in CELLS:
        vals_a=[]; vals_o=[]; counts=Counter()
        for rec in nonzero:
            c=rec["cells"][name]
            cls=c["class"] if c else "SOURCE_GATED"
            counts[cls]+=1
            residual=None
            if cls in ("ALIGNED","OPPOSED"):
                ev=selected_archive.get(c["event_id"]) or active.get(c["event_id"])
                y=ev["h"].get(yh) if ev else None
                if rec["t0_mid"] is None or y is None or y["st"] is None:
                    cls="SOURCE_GATED"; counts[c["class"]]-=1; counts[cls]+=1
                else:
                    residual=rec["position"]*10000.0*(y["st"]["mid"]/rec["t0_mid"]-1.0)
                    (vals_a if cls=="ALIGNED" else vals_o).append(residual)
            ledgers.append({
              "entry":rec["entry"],"position":rec["position"],"cell":name,"classification":cls,
              "event_time":ns_to_iso(c["event_env"]) if c and c.get("event_env") else "",
              "r_observation_time":ns_to_iso(c["r_env"]) if c and c.get("r_env") else "",
              "y_target_time":ns_to_iso(c["y_target"]) if c and c.get("y_target") else "",
              "residual_bps":"" if residual is None else residual,
              "delay_benefit_bps":"" if residual is None or cls!="OPPOSED" else -residual
            })
        sep=(mean(vals_a)-mean(vals_o)) if vals_a and vals_o else None
        cell_stats[name]={
          "parent_nonzero_rows":len(nonzero),
          "aligned_n":len(vals_a),"opposed_n":len(vals_o),
          "no_active_weak_n":counts["NO_ACTIVE_WEAK"],"source_gated_n":counts["SOURCE_GATED"],
          "aligned_mean_residual_bps":mean(vals_a),
          "opposed_mean_residual_bps":mean(vals_o),
          "separation_bps":sep,
          "opposed_mean_delay_benefit_bps":(-mean(vals_o)) if vals_o else None,
          "sample_viable":len(vals_a)>=8 and len(vals_o)>=8
        }

    global_source_evaluable=sum(1 for r in nonzero if r["source_gate"] and r["t0_mid"] is not None)
    all_cells_viable=all(s["sample_viable"] for s in cell_stats.values())
    seps=[s["separation_bps"] for s in cell_stats.values() if s["sample_viable"]]
    delays=[s["opposed_mean_delay_benefit_bps"] for s in cell_stats.values() if s["sample_viable"]]
    pos_cells=sum(1 for s in cell_stats.values() if s["sample_viable"] and s["separation_bps"]>0)
    pos_by_r={}
    for rh in (1000,5000,15000):
        pos_by_r[str(rh)]=any(cell_stats[name]["sample_viable"] and cell_stats[name]["separation_bps"]>0 for name,crh,_ in CELLS if crh==rh)
    source_sample_ok=global_source_evaluable>=40 and all_cells_viable and len(seps)==6
    support={
      "source_sample_viability":source_sample_ok,
      "panel_equal_weight_separation_positive":source_sample_ok and mean(seps)>0,
      "at_least_4_of_6_positive_cells":source_sample_ok and pos_cells>=4,
      "each_R_family_positive":source_sample_ok and all(pos_by_r.values()),
      "panel_opposed_delay_benefit_positive":source_sample_ok and mean(delays)>0
    }
    if not source_sample_ok:
        classification="DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE"
    elif all(support.values()):
        classification="DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED"
    else:
        classification="DEVELOPMENT_OVERLAY_NO_SUPPORT"

    outdir=base/"_EVIDENCE_L2R_OVERLAY_ETF_CME_V0_1"; outdir.mkdir(parents=True,exist_ok=True)
    ledger_path=outdir/"L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_LEDGER_V0_1.csv"
    with ledger_path.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["entry","position","cell","classification","event_time","r_observation_time","y_target_time","residual_bps","delay_benefit_bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(ledgers)
    cells_path=outdir/"L2R_OVERLAY_ETF_CME_001_2025_CELL_SUMMARY_V0_1.csv"
    with cells_path.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["cell"]+list(next(iter(cell_stats.values())).keys())
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for name,_,_ in CELLS: w.writerow({"cell":name,**cell_stats[name]})
    receipt={
      "schema_version":"0.1","implementation_version":IMPLEMENTATION_VERSION,"lab_id":LAB_ID,
      "classification":classification,
      "evidence_status":"POST_PARENT_2025_DEVELOPMENT_ONLY__NOT_INDEPENDENT_VALIDATION",
      "parent_etf_artifact_sha256":EXPECTED_ETF_ARTIFACT_SHA256,
      "parent_l2_manifest_sha256":EXPECTED_MANIFEST_SHA256,
      "parent_etf_rows":len(etf),"parent_nonzero_rows":len(nonzero),
      "global_source_evaluable_rows":global_source_evaluable,
      "cell_summary":cell_stats,
      "panel":{
        "equal_weight_separation_bps":mean(seps) if len(seps)==6 else None,
        "positive_cells":pos_cells,
        "positive_by_R":pos_by_r,
        "equal_weight_opposed_delay_benefit_bps":mean(delays) if len(delays)==6 else None,
        "support_gate":support
      },
      "raw_scan":{"objects_verified":totals["objects"],"accepted_states":totals["accepted"],"stale_late_payload":totals["stale"],"ambiguous_sweeps":totals["ambiguous"]},
      "firewalls":{"access_2026":False,"market_data_network":False,"orders":False,"live_trading":False,"exchange_mutation":False,"main_merge":False},
      "interpretation":"Reference-price entry-timing development diagnostic only. No parent weekly PnL filtering and no executable fill claim."
    }
    receipt_path=outdir/"L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_RECEIPT_V0_1.json"
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    zpath=base/"L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_EVIDENCE_V0_1.zip"
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(ledger_path,ledger_path.name); z.write(cells_path,cells_path.name); z.write(receipt_path,receipt_path.name)
    print(json.dumps(receipt,indent=2,sort_keys=True))
    print("EVIDENCE_ZIP",zpath)
    print("EVIDENCE_SHA256",sha256_file(zpath))
    return receipt

def self_test():
    # Gate arithmetic and direction semantics only; no market data.
    assert (1*10000*(101/100-1))>0
    assert (-1*10000*(99/100-1))>0
    synthetic={
      "a":[1.0,2.0,0.5,1.5,1.2,0.8,1.1,1.3],
      "o":[-1.0,-0.5,-1.5,-0.8,-1.2,-0.7,-1.1,-0.9]
    }
    sep=mean(synthetic["a"])-mean(synthetic["o"])
    assert sep>0 and -mean(synthetic["o"])>0
    print("SELF_TEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default=str(Path.home()/"Desktop"/"L2R_2025_BTC_VALIDATION_LOCAL"))
    ap.add_argument("--etf-artifact",required=False)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return
    if not args.etf_artifact: raise SystemExit("--etf-artifact is required")
    run(Path(args.base).resolve(),Path(args.etf_artifact).resolve())

if __name__=="__main__": main()
