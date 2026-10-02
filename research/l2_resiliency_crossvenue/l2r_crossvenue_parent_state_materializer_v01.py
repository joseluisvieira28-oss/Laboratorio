#!/usr/bin/env python3
from __future__ import annotations
import argparse, concurrent.futures, csv, datetime as dt, gzip, hashlib, json, math, re
from collections import Counter, deque
from pathlib import Path
import lz4.frame

LAB_ID = "L2R-CROSSVENUE-001"
PARENT_LAB = "L2-RESILIENCY-001"
EXPECTED_MANIFEST_SHA256 = "59e16ce8ea41658c2ea0fc6f2489d4deafbdc676e008d0b93f95ee6e3864913d"
EXPECTED_ANCHOR_SHA256 = "be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3"
EXPECTED_OBJECTS = 8707
EXPECTED_BYTES = 6832137900
EXPECTED_RECORDS = 50717748
EXPECTED_ACCEPTED = 50717668
EXPECTED_STALE = 80
EXPECTED_EQUAL = 158
EXPECTED_SEGMENTS = 11
EXPECTED_ELIGIBLE_TRANSITIONS = 50717657
EXPECTED_ASK_SWEEPS = 4721124
EXPECTED_BID_SWEEPS = 4460354
EXPECTED_SWEEPS = 9181478
EXPECTED_AMBIGUOUS = 24087
EXPECTED_SEGMENT_EVENTS = {1:(138709,121702,4148),2:(256425,258996,6959),3:(1886038,1808068,9474),4:(354649,352271,613),5:(79793,72007,154),6:(54588,49339,95),7:(11780,10585,15),8:(46939,42967,83),9:(885384,807828,1186),10:(20468,19568,19),11:(986351,917023,1341)}
HORIZONS_MS=(1000,5000,15000)
MAX_LATENESS_NS=1100000000
KEY_RE=re.compile(r"^market_data/(2024\d{4})/([0-9]|1[0-9]|2[0-3])/l2Book/BTC\.lz4$")
ISO_RE=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z?$")
READ_CHUNK=1024*1024
FIELDS=["segment_id","event_seq","event_envelope_ns","event_payload_ms","side","direction","pre_depth5","rr_1000","group_1000","status_1000","lateness_ms_1000","rr_5000","group_5000","status_5000","lateness_ms_5000","rr_15000","group_15000","status_15000","lateness_ms_15000"]
class Fail(RuntimeError): pass

def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(READ_CHUNK),b""): h.update(b)
    return h.hexdigest()

def key_hour(key):
    m=KEY_RE.fullmatch(key)
    if not m: raise Fail("illegal/protected key: "+key)
    ymd,hh=m.groups()
    d=dt.datetime.strptime(ymd+f"{int(hh):02d}","%Y%m%d%H").replace(tzinfo=dt.timezone.utc)
    if d.year!=2024: raise Fail("protected year key: "+key)
    return d

def key_bounds_ns(key):
    d=key_hour(key); s=int(d.timestamp())*1000000000
    return s,s+3600000000000

def build_segments(rows):
    ordered=sorted(rows,key=lambda r:key_hour(r["key"])); out=[]; cur=[]; prev=None
    for row in ordered:
        h=key_hour(row["key"])
        if prev is None or h==prev+dt.timedelta(hours=1): cur.append(row)
        else: out.append(cur); cur=[row]
        prev=h
    if cur: out.append(cur)
    return out

def parse_env_ns(s):
    m=ISO_RE.fullmatch(str(s).strip())
    if not m: raise Fail("invalid envelope timestamp")
    base,frac=m.groups()
    d=dt.datetime.strptime(base,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    ns=((frac or "")+"000000000")[:9]
    return int(d.timestamp())*1000000000+int(ns)

def finite_num(v,field):
    if isinstance(v,bool): raise Fail("boolean "+field)
    try: x=float(v)
    except Exception as e: raise Fail("non-numeric "+field) from e
    if not math.isfinite(x): raise Fail("non-finite "+field)
    return x

def extract_state(obj):
    raw=obj.get("raw")
    if not isinstance(raw,dict) or raw.get("channel")!="l2Book": raise Fail("wrong raw/channel")
    data=raw.get("data")
    if not isinstance(data,dict) or data.get("coin")!="BTC": raise Fail("wrong data/coin")
    payload=data.get("time")
    if isinstance(payload,bool) or not isinstance(payload,int): raise Fail("payload time not int")
    levels=data.get("levels")
    if not isinstance(levels,list) or len(levels)!=2: raise Fail("invalid levels")
    bids,asks=levels
    if len(bids)<5 or len(asks)<5: raise Fail("fewer than top5")
    bid_px=[]; ask_px=[]; bid_sz=[]; ask_sz=[]
    for side,pxs,szs in ((bids,bid_px,bid_sz),(asks,ask_px,ask_sz)):
        for i,lvl in enumerate(side):
            if not isinstance(lvl,dict): raise Fail("level not object")
            p=finite_num(lvl.get("px"),"px"); s=finite_num(lvl.get("sz"),"sz"); n=lvl.get("n")
            if p<=0 or s<0 or isinstance(n,bool) or not isinstance(n,int) or n<0: raise Fail("invalid level")
            pxs.append(p)
            if i<5: szs.append(s)
    if not all(bid_px[i]>bid_px[i+1] for i in range(4)): raise Fail("bid top5 order")
    if not all(ask_px[i]<ask_px[i+1] for i in range(4)): raise Fail("ask top5 order")
    if bid_px[0]>=ask_px[0]: raise Fail("locked/crossed")
    return {"payload_ms":payload,"bid_best":bid_px[0],"ask_best":ask_px[0],"bid_prices_all":tuple(bid_px),"ask_prices_all":tuple(ask_px),"bid_depth5":sum(bid_sz),"ask_depth5":sum(ask_sz)}

def process_segment(args):
    sid,rows,raw_root,out_dir=args; root=Path(raw_root); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    out_path=out/f"L2R_CROSSVENUE_001_PARENT_STATE_SEGMENT_{sid:02d}_V0_1.csv.gz"
    prev_state=None; last_env=None; last_payload=None; totals=Counter(); timing=Counter(); active={}; queues={h:deque() for h in HORIZONS_MS}; eid_next=0
    with gzip.open(out_path,"wt",encoding="utf-8",newline="") as gz:
        w=csv.DictWriter(gz,fieldnames=FIELDS); w.writeheader()
        def finalize(ev):
            row={"segment_id":sid,"event_seq":ev["eid"],"event_envelope_ns":ev["env_ns"],"event_payload_ms":ev["payload_ms"],"side":ev["side"],"direction":ev["direction"],"pre_depth5":f"{ev['pre_depth']:.12f}"}
            for h in HORIZONS_MS:
                r=ev["h"].get(h)
                if r is None:
                    row[f"rr_{h}"]=""; row[f"group_{h}"]=""; row[f"status_{h}"]=ev["status"][h]; row[f"lateness_ms_{h}"]=ev["lateness"].get(h,"")
                else:
                    rr=r["depth5"]/ev["pre_depth"] if ev["pre_depth"]>0 else None
                    row[f"rr_{h}"]="" if rr is None else f"{rr:.12f}"; row[f"group_{h}"]="" if rr is None else ("WEAK" if rr<1 else "STRONG"); row[f"status_{h}"]="OK"; row[f"lateness_ms_{h}"]=f"{r['lateness_ns']/1000000:.6f}"
            w.writerow(row)
        def resolve(eid,h,state,lateness_ns=None,status="OK"):
            ev=active[eid]
            if h in ev["resolved"]: raise Fail("double horizon resolution")
            ev["resolved"].add(h); ev["status"][h]=status
            if state is None:
                ev["h"][h]=None
                if lateness_ns is not None: ev["lateness"][h]=f"{lateness_ns/1000000:.6f}"
                timing[f"{h}_{status}"]+=1
            else:
                depth=state["ask_depth5"] if ev["side"]=="ASK" else state["bid_depth5"]; ev["h"][h]={"depth5":depth,"lateness_ns":lateness_ns or 0}; timing[f"{h}_OK"]+=1
            if len(ev["resolved"])==len(HORIZONS_MS): finalize(ev); del active[eid]
        def resolve_due(env_ns,state):
            for h in HORIZONS_MS:
                q=queues[h]
                while q and q[0][0]<=env_ns:
                    target,eid=q.popleft(); late=env_ns-target
                    if late<=MAX_LATENESS_NS: resolve(eid,h,state,late,"OK")
                    else: resolve(eid,h,None,late,"MISSING_LATE")
        def create_event(env_ns,state,side,pre_depth):
            nonlocal eid_next
            eid=eid_next; eid_next+=1
            active[eid]={"eid":eid,"env_ns":env_ns,"payload_ms":state["payload_ms"],"side":side,"direction":1 if side=="ASK" else -1,"pre_depth":pre_depth,"h":{},"resolved":set(),"status":{},"lateness":{}}
            for h in HORIZONS_MS: queues[h].append((env_ns+h*1000000,eid))
        def consume(env_ns,state):
            nonlocal prev_state
            resolve_due(env_ns,state)
            if prev_state is not None:
                totals["eligible_transitions"]+=1; ask_worse=state["ask_best"]>prev_state["ask_best"]; bid_worse=state["bid_best"]<prev_state["bid_best"]
                if ask_worse and bid_worse: totals["ambiguous"]+=1
                elif ask_worse:
                    if any(p==prev_state["ask_best"] for p in state["ask_prices_all"]): raise Fail("prior ask still present")
                    totals["ask_sweeps"]+=1; create_event(env_ns,state,"ASK",prev_state["ask_depth5"])
                elif bid_worse:
                    if any(p==prev_state["bid_best"] for p in state["bid_prices_all"]): raise Fail("prior bid still present")
                    totals["bid_sweeps"]+=1; create_event(env_ns,state,"BID",prev_state["bid_depth5"])
                else: totals["non_sweep"]+=1
            prev_state=state
        for row in rows:
            key=row["key"]; path=root/Path(*key.split("/"))
            if not path.exists(): raise Fail("raw missing: "+key)
            start_ns,end_ns=key_bounds_ns(key); expected_size=int(row["actual_size"]); expected_sha=str(row["sha256"]).lower(); expected_md5=str(row["md5"]).lower(); expected_etag=str(row["inventory_etag"]).strip().strip('"').lower()
            h256=hashlib.sha256(); hmd5=hashlib.md5(); actual_size=0; pending=b""; dec=lz4.frame.LZ4FrameDecompressor()
            def process_line(line):
                nonlocal last_env,last_payload
                totals["records"]+=1; obj=json.loads(line); env=parse_env_ns(obj["time"])
                if not(start_ns<=env<end_ns): raise Fail("envelope outside key hour")
                state=extract_state(obj); payload=state["payload_ms"]
                if last_env is not None and env<last_env: raise Fail("envelope backwards")
                if payload*1000000>env: raise Fail("future payload")
                last_env=env
                if last_payload is not None and payload<last_payload: totals["stale"]+=1; return
                if last_payload is not None and payload==last_payload: totals["equal"]+=1
                last_payload=payload; totals["accepted"]+=1; consume(env,state)
            with path.open("rb") as f:
                while True:
                    chunk=f.read(READ_CHUNK)
                    if not chunk: break
                    actual_size+=len(chunk); h256.update(chunk); hmd5.update(chunk); outb=dec.decompress(chunk)
                    if not outb: continue
                    pending+=outb; lines=pending.split(b"\n"); pending=lines.pop()
                    for line in lines:
                        if line.strip(): process_line(line)
            if pending.strip(): process_line(pending)
            if not dec.eof: raise Fail("incomplete LZ4: "+key)
            if not(actual_size==expected_size and h256.hexdigest()==expected_sha and hmd5.hexdigest()==expected_md5 and expected_md5==expected_etag): raise Fail("byte binding mismatch: "+key)
            totals["objects"]+=1
        for h in HORIZONS_MS:
            q=queues[h]
            while q:
                _,eid=q.popleft(); resolve(eid,h,None,None,"MISSING_SEGMENT_END")
        if active: raise Fail(f"active events remain: {len(active)}")
    expected=EXPECTED_SEGMENT_EVENTS[sid]; observed=(totals["ask_sweeps"],totals["bid_sweeps"],totals["ambiguous"])
    if observed!=expected: raise Fail(f"segment event guard mismatch {sid}: {observed} != {expected}")
    return {"segment_id":sid,"path":str(out_path),"sha256":sha256_file(out_path),"rows":totals["ask_sweeps"]+totals["bid_sweeps"],"totals":dict(totals),"timing":dict(timing)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw-root",required=True); ap.add_argument("--workers",type=int,default=4); ap.add_argument("--out-dir",default=""); args=ap.parse_args()
    root=Path(args.raw_root); manifest=root/"L2_RESILIENCY_001_2024_BTC_RAW_SHA256_MANIFEST_V0_1.csv"; anchors=root/"_SWEEP_EVENT_PREFLIGHT_V0_1"/"L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv"
    if not manifest.exists(): raise SystemExit(f"manifest missing: {manifest}")
    if not anchors.exists(): raise SystemExit(f"canonical anchors missing: {anchors}")
    if sha256_file(manifest)!=EXPECTED_MANIFEST_SHA256: raise SystemExit("FAIL-CLOSED manifest SHA mismatch")
    if sha256_file(anchors)!=EXPECTED_ANCHOR_SHA256: raise SystemExit("FAIL-CLOSED anchor SHA mismatch")
    with manifest.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=EXPECTED_OBJECTS: raise SystemExit("FAIL-CLOSED object count")
    if len({r["key"] for r in rows})!=EXPECTED_OBJECTS: raise SystemExit("FAIL-CLOSED duplicate keys")
    if sum(int(r["actual_size"]) for r in rows)!=EXPECTED_BYTES: raise SystemExit("FAIL-CLOSED byte total")
    segments=build_segments(rows)
    if len(segments)!=EXPECTED_SEGMENTS: raise SystemExit("FAIL-CLOSED segment count")
    out=Path(args.out_dir) if args.out_dir else root/"_CROSSVENUE_PARENT_STATE_V0_1"; jobs=[(i+1,seg,str(root),str(out)) for i,seg in enumerate(segments)]; results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1,min(args.workers,4))) as ex:
        futs=[ex.submit(process_segment,j) for j in jobs]
        for fut in concurrent.futures.as_completed(futs):
            r=fut.result(); results.append(r); print(f"segment {r['segment_id']} PASS rows={r['rows']:,} sha256={r['sha256']}")
    results.sort(key=lambda x:x["segment_id"]); totals=Counter()
    for r in results: totals.update(r["totals"])
    guards={"objects":totals["objects"]==EXPECTED_OBJECTS,"records":totals["records"]==EXPECTED_RECORDS,"accepted":totals["accepted"]==EXPECTED_ACCEPTED,"stale":totals["stale"]==EXPECTED_STALE,"equal":totals["equal"]==EXPECTED_EQUAL,"eligible_transitions":totals["eligible_transitions"]==EXPECTED_ELIGIBLE_TRANSITIONS,"ask_sweeps":totals["ask_sweeps"]==EXPECTED_ASK_SWEEPS,"bid_sweeps":totals["bid_sweeps"]==EXPECTED_BID_SWEEPS,"sweep_total":totals["ask_sweeps"]+totals["bid_sweeps"]==EXPECTED_SWEEPS,"ambiguous":totals["ambiguous"]==EXPECTED_AMBIGUOUS}
    classification="PARENT_STATE_MATERIALIZATION_PASS" if all(guards.values()) else "PARENT_STATE_GUARD_FAIL_CLOSED"
    receipt={"schema_version":"0.1","lab_id":LAB_ID,"parent_lab":PARENT_LAB,"classification":classification,"provenance_runner_sha256":"7f135689afd9f51a758e2c98b5c8da9fe3c7f3eca15f40eced7fdb53b03d2eaf","manifest_sha256":EXPECTED_MANIFEST_SHA256,"anchor_sha256":EXPECTED_ANCHOR_SHA256,"horizons_ms":list(HORIZONS_MS),"timing_max_lateness_ms":1100,"weak_rule":"RR < 1.0","strong_rule":"RR >= 1.0","segments":results,"guards":guards,"totals":dict(totals),"firewalls":{"binance_read":False,"returns_computed":False,"signed_response_computed":False,"pnl_computed":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"main_merge":False}}
    out.mkdir(parents=True,exist_ok=True); rp=out/"L2R_CROSSVENUE_001_PARENT_STATE_MATERIALIZATION_RECEIPT_V0_1.json"; rp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"receipt":str(rp),"guards":guards},indent=2)); return 0 if classification.endswith("_PASS") else 2
if __name__=="__main__": raise SystemExit(main())
