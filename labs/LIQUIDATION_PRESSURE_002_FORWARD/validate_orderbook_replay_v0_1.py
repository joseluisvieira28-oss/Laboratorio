from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

ap=argparse.ArgumentParser()
ap.add_argument("--input",default=str(OUT/"forward_raw_v0_1.jsonl"))
args=ap.parse_args()

books={}
stats=defaultdict(lambda:{
    "snapshots":0,"deltas":0,"updates":0,"pre_snapshot_deltas":0,
    "u_nonmonotonic":0,"seq_nonmonotonic":0,"crossed_books":0,
    "valid_books":0,"last_u":None,"last_seq":None,
})
errors=[]

def apply_side(side_map, rows):
    for row in rows or []:
        if not isinstance(row,list) or len(row)<2:
            continue
        p=str(row[0]); q=str(row[1])
        try:
            fq=float(q)
        except Exception:
            continue
        if fq==0:
            side_map.pop(p,None)
        else:
            side_map[p]=q

with pathlib.Path(args.input).open("r",encoding="utf-8") as f:
    for line_no,line in enumerate(f,1):
        if not line.strip():
            continue
        try:
            env=json.loads(line)
            msg=env.get("message") or {}
        except Exception as e:
            errors.append({"line":line_no,"error":"JSON:"+str(e)[:200]})
            continue

        topic=msg.get("topic","")
        if not topic.startswith("orderbook."):
            continue
        data=msg.get("data") or {}
        sym=data.get("s") or topic.rsplit(".",1)[-1]
        typ=msg.get("type")
        u=data.get("u")
        seq=data.get("seq")
        st=stats[sym]

        if typ=="snapshot" or u==1 or sym not in books:
            if typ!="snapshot" and u!=1 and sym not in books:
                st["pre_snapshot_deltas"]+=1
                continue
            books[sym]={"b":{},"a":{}}
            apply_side(books[sym]["b"],data.get("b"))
            apply_side(books[sym]["a"],data.get("a"))
            st["snapshots"]+=1
            st["last_u"]=u
            st["last_seq"]=seq
        elif typ=="delta":
            prev_u=st["last_u"]
            prev_seq=st["last_seq"]
            if isinstance(prev_u,int) and isinstance(u,int) and u<=prev_u:
                st["u_nonmonotonic"]+=1
            if isinstance(prev_seq,int) and isinstance(seq,int) and seq<prev_seq:
                st["seq_nonmonotonic"]+=1
            apply_side(books[sym]["b"],data.get("b"))
            apply_side(books[sym]["a"],data.get("a"))
            st["deltas"]+=1
            st["last_u"]=u
            st["last_seq"]=seq
        else:
            continue

        st["updates"]+=1
        bids=books[sym]["b"]
        asks=books[sym]["a"]
        if bids and asks:
            best_bid=max(float(x) for x in bids)
            best_ask=min(float(x) for x in asks)
            if best_bid>=best_ask:
                st["crossed_books"]+=1
            else:
                st["valid_books"]+=1

symbols={}
for sym,st0 in sorted(stats.items()):
    st=dict(st0)
    structural_pass=(
        st["snapshots"]>=1
        and st["valid_books"]>0
        and st["u_nonmonotonic"]==0
        and st["seq_nonmonotonic"]==0
        and st["crossed_books"]==0
    )
    st["structural_pass"]=structural_pass
    symbols[sym]=st

overall=bool(symbols) and all(x["structural_pass"] for x in symbols.values()) and not errors
receipt={
    "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
    "phase":"ORDERBOOK_REPLAY_INTEGRITY_V0.1",
    "verdict":"ORDERBOOK_REPLAY_PASS" if overall else "ORDERBOOK_REPLAY_FAIL_CLOSED",
    "symbols":symbols,
    "parse_error_count":len(errors),
    "parse_errors":errors[:20],
    "economic_outcomes_opened":False,
    "markouts_computed":False,
    "pnl_computed":False,
    "note":"Validates snapshot/delta reconstruction mechanics only; no liquidation-return relationship is inspected."
}
(OUT/"orderbook_replay_integrity_v0_1.json").write_text(
    json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8"
)
print(json.dumps(receipt,indent=2,sort_keys=True))
if not overall:
    raise SystemExit(2)
