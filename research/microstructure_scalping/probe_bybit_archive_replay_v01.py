#!/usr/bin/env python3
import datetime as dt
import json
import statistics
import sys
import urllib.request
import zipfile
from pathlib import Path

URL="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip"
MAX_BYTES=650_000_000
SAMPLE_LINES=250_000
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Raw-Replay/0.1"}

def download():
    req=urllib.request.Request(URL,headers=UA)
    out=Path("/tmp/bybit_l2_probe.zip")
    total=0
    with urllib.request.urlopen(req,timeout=60) as r, out.open("wb") as f:
        cl=r.headers.get("Content-Length")
        if cl and int(cl)>MAX_BYTES:
            raise RuntimeError(f"archive_too_large:{cl}")
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            total += len(chunk)
            if total>MAX_BYTES:
                raise RuntimeError(f"archive_exceeded_cap:{total}")
            f.write(chunk)
    return out,total

def apply_side(book, updates):
    for row in updates or []:
        if len(row)<2: continue
        p=float(row[0]); q=float(row[1])
        if q==0.0: book.pop(p,None)
        else: book[p]=q

def main():
    receipt={
      "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "purpose":"RAW L2 SOURCE INTEGRITY ONLY — NO PRICE-OUTCOME TEST",
      "url":URL,
      "sample_limit_lines":SAMPLE_LINES,
    }
    try:
        path,nbytes=download()
        receipt["download_bytes"]=nbytes
        with zipfile.ZipFile(path) as zf:
            bad=zf.testzip()
            receipt["zip_crc"]="PASS" if bad is None else f"FAIL:{bad}"
            names=[n for n in zf.namelist() if not n.endswith("/")]
            receipt["members"]=names
            if len(names)!=1:
                raise RuntimeError(f"unexpected_members:{len(names)}")
            bids={}; asks={}; have_snapshot=False
            stats={k:0 for k in [
              "lines","snapshots","deltas","json_errors","schema_errors",
              "pre_snapshot_deltas","crossed_books","ts_nonmonotonic",
              "cts_nonmonotonic","u_nonmonotonic","seq_nonmonotonic"
            ]}
            prev_ts=prev_cts=prev_u=prev_seq=None
            dts=[]
            first_ts=last_ts=None
            with zf.open(names[0]) as fh:
                for raw in fh:
                    if stats["lines"]>=SAMPLE_LINES: break
                    stats["lines"]+=1
                    try:
                        m=json.loads(raw)
                    except Exception:
                        stats["json_errors"]+=1; continue
                    typ=m.get("type"); data=m.get("data") or {}
                    if typ not in ("snapshot","delta") or "b" not in data or "a" not in data:
                        stats["schema_errors"]+=1; continue
                    ts=m.get("ts"); cts=m.get("cts"); u=data.get("u"); seq=data.get("seq")
                    if ts is not None:
                        if first_ts is None: first_ts=ts
                        last_ts=ts
                        if prev_ts is not None:
                            if ts<prev_ts: stats["ts_nonmonotonic"]+=1
                            else: dts.append(ts-prev_ts)
                        prev_ts=ts
                    if cts is not None:
                        if prev_cts is not None and cts<prev_cts: stats["cts_nonmonotonic"]+=1
                        prev_cts=cts
                    if u is not None:
                        if prev_u is not None and typ!="snapshot" and u<prev_u: stats["u_nonmonotonic"]+=1
                        prev_u=u
                    if seq is not None:
                        if prev_seq is not None and seq<prev_seq: stats["seq_nonmonotonic"]+=1
                        prev_seq=seq
                    if typ=="snapshot":
                        stats["snapshots"]+=1
                        bids={float(p):float(q) for p,q,*_ in data.get("b",[]) if float(q)!=0}
                        asks={float(p):float(q) for p,q,*_ in data.get("a",[]) if float(q)!=0}
                        have_snapshot=True
                    else:
                        stats["deltas"]+=1
                        if not have_snapshot:
                            stats["pre_snapshot_deltas"]+=1
                            continue
                        apply_side(bids,data.get("b",[])); apply_side(asks,data.get("a",[]))
                    if have_snapshot and bids and asks and max(bids)>=min(asks):
                        stats["crossed_books"]+=1
            receipt["stats"]=stats
            receipt["first_ts"]=first_ts
            receipt["last_ts"]=last_ts
            receipt["final_bid_levels"]=len(bids)
            receipt["final_ask_levels"]=len(asks)
            if dts:
                receipt["message_delta_ms"]={
                  "median":statistics.median(dts),
                  "p95":sorted(dts)[int(0.95*(len(dts)-1))],
                  "max":max(dts)
                }
            hard_fail = (
              receipt["zip_crc"]!="PASS" or
              stats["lines"]<10_000 or
              stats["snapshots"]<1 or
              stats["deltas"]<1_000 or
              stats["json_errors"]>0 or
              stats["schema_errors"]>0 or
              stats["pre_snapshot_deltas"]>0 or
              stats["crossed_books"]>0 or
              stats["ts_nonmonotonic"]>0 or
              stats["cts_nonmonotonic"]>0 or
              stats["u_nonmonotonic"]>0 or
              stats["seq_nonmonotonic"]>0
            )
            receipt["gate"]="BLOCKED" if hard_fail else "PASS_SAMPLE"
    except Exception as e:
        receipt["gate"]="BLOCKED"
        receipt["error"]=repr(e)
    Path("research/microstructure_scalping/receipts").mkdir(parents=True,exist_ok=True)
    Path("research/microstructure_scalping/receipts/bybit_raw_replay_v01.json").write_text(
      json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["gate"]=="PASS_SAMPLE" else 2

if __name__=="__main__":
    sys.exit(main())
