#!/usr/bin/env python3
import datetime as dt
import json, re, statistics, sys, urllib.request, zipfile
from pathlib import Path

BASE="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/"
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Transition-Gate/0.1"}
SAMPLE_LINES=100_000
MAX_FILE_BYTES=500_000_000

def request(url, method="GET", timeout=60):
    req=urllib.request.Request(url,headers=UA,method=method)
    return urllib.request.urlopen(req,timeout=timeout)

def listing():
    with request(BASE,timeout=30) as r:
        text=r.read().decode("utf-8","replace")
    rows=[]
    for f in sorted(set(re.findall(r'href="([^"]+_BTCUSDT_ob(?:200|500)\.data\.zip)"',text))):
        m=re.match(r"(\d{4}-\d{2}-\d{2})_BTCUSDT_ob(200|500)\.data\.zip",f)
        if m:
            rows.append((dt.date.fromisoformat(m.group(1)),m.group(2),f))
    return rows

def choose(rows):
    pre=[r for r in rows if r[0] <= dt.date(2025,12,31)]
    d500=[r for r in pre if r[1]=="500"]
    d200=[r for r in pre if r[1]=="200"]
    if not d500 or not d200:
        raise RuntimeError("both_ob500_and_ob200_required")
    picks=[max(d500,key=lambda x:x[0]), min(d200,key=lambda x:x[0]), max(pre,key=lambda x:x[0])]
    out=[]; seen=set()
    for p in picks:
        if p[2] not in seen:
            out.append(p); seen.add(p[2])
    return out, {
      "last_ob500":max(d500,key=lambda x:x[0])[0].isoformat(),
      "first_ob200":min(d200,key=lambda x:x[0])[0].isoformat(),
      "latest_pre_holdout":max(pre,key=lambda x:x[0])[0].isoformat()
    }

def download(filename):
    url=BASE+filename
    with request(url,method="HEAD",timeout=30) as r:
        cl=r.headers.get("Content-Length")
        if cl and int(cl)>MAX_FILE_BYTES: raise RuntimeError(f"too_large:{cl}")
    path=Path("/tmp")/filename
    total=0
    with request(url,timeout=90) as r, path.open("wb") as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            total += len(chunk)
            if total>MAX_FILE_BYTES: raise RuntimeError(f"exceeded_cap:{total}")
            f.write(chunk)
    return path,total

def apply(book, rows):
    for row in rows or []:
        p=float(row[0]); q=float(row[1])
        if q==0: book.pop(p,None)
        else: book[p]=q

def inspect(date,depth,filename):
    out={"date":date.isoformat(),"depth":int(depth),"filename":filename}
    path,nbytes=download(filename); out["download_bytes"]=nbytes
    with zipfile.ZipFile(path) as zf:
        bad=zf.testzip(); out["zip_crc"]="PASS" if bad is None else f"FAIL:{bad}"
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1: raise RuntimeError(f"members:{len(names)}")
        bids={}; asks={}; snap=False
        stats={k:0 for k in ["lines","snapshots","deltas","json_errors","schema_errors","pre_snapshot_deltas","crossed_books","ts_nonmonotonic","cts_nonmonotonic","u_nonmonotonic","seq_nonmonotonic"]}
        pts=pcts=pu=pseq=None; dts=[]
        with zf.open(names[0]) as fh:
            for raw in fh:
                if stats["lines"]>=SAMPLE_LINES: break
                stats["lines"]+=1
                try: m=json.loads(raw)
                except Exception: stats["json_errors"]+=1; continue
                typ=m.get("type"); data=m.get("data") or {}
                if typ not in ("snapshot","delta") or "b" not in data or "a" not in data:
                    stats["schema_errors"]+=1; continue
                ts=m.get("ts"); cts=m.get("cts"); u=data.get("u"); seq=data.get("seq")
                if ts is not None and pts is not None:
                    if ts<pts: stats["ts_nonmonotonic"]+=1
                    else: dts.append(ts-pts)
                if cts is not None and pcts is not None and cts<pcts: stats["cts_nonmonotonic"]+=1
                if u is not None and pu is not None and typ!="snapshot" and u<pu: stats["u_nonmonotonic"]+=1
                if seq is not None and pseq is not None and seq<pseq: stats["seq_nonmonotonic"]+=1
                if ts is not None: pts=ts
                if cts is not None: pcts=cts
                if u is not None: pu=u
                if seq is not None: pseq=seq
                if typ=="snapshot":
                    stats["snapshots"]+=1
                    bids={float(p):float(q) for p,q,*_ in data["b"] if float(q)!=0}
                    asks={float(p):float(q) for p,q,*_ in data["a"] if float(q)!=0}
                    snap=True
                else:
                    stats["deltas"]+=1
                    if not snap:
                        stats["pre_snapshot_deltas"]+=1; continue
                    apply(bids,data["b"]); apply(asks,data["a"])
                if snap and bids and asks and max(bids)>=min(asks): stats["crossed_books"]+=1
        out["stats"]=stats
        out["final_levels"]={"bids":len(bids),"asks":len(asks)}
        if dts:
            sd=sorted(dts)
            out["message_delta_ms"]={"median":statistics.median(dts),"p95":sd[int(.95*(len(sd)-1))],"max":max(dts)}
        violations=sum(stats[k] for k in ["json_errors","schema_errors","pre_snapshot_deltas","crossed_books","ts_nonmonotonic","cts_nonmonotonic","u_nonmonotonic","seq_nonmonotonic"])
        out["gate"]="PASS_SAMPLE" if out["zip_crc"]=="PASS" and stats["snapshots"]>=1 and stats["deltas"]>=1000 and violations==0 else "BLOCKED"
    path.unlink(missing_ok=True)
    return out

def main():
    receipt={"generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"purpose":"STRATIFIED SOURCE INTEGRITY ONLY — NO OUTCOMES","sample_lines_per_file":SAMPLE_LINES}
    try:
        rows=listing(); picks,transition=choose(rows)
        receipt["transition"]=transition
        receipt["tested_files"]=[]
        for d,dep,f in picks:
            receipt["tested_files"].append(inspect(d,dep,f))
        receipt["gate"]="PASS_STRATIFIED_SAMPLE" if all(x["gate"]=="PASS_SAMPLE" for x in receipt["tested_files"]) else "BLOCKED"
    except Exception as e:
        receipt["gate"]="BLOCKED"; receipt["error"]=repr(e)
    Path("research/microstructure_scalping/receipts").mkdir(parents=True,exist_ok=True)
    Path("research/microstructure_scalping/receipts/bybit_transition_gate_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["gate"]=="PASS_STRATIFIED_SAMPLE" else 2

if __name__=="__main__": sys.exit(main())
