#!/usr/bin/env python3
"""Outcome-blind calibration summary for LICP-001."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path

WINDOWS_MS=[500,1000,5000,15000,60000]
QS=[.95,.99,.995,.999]

def qtile(xs,q):
    if not xs:return None
    a=sorted(xs); i=(len(a)-1)*q; lo=math.floor(i); hi=math.ceil(i)
    if lo==hi:return a[lo]
    return a[lo]*(hi-i)+a[hi]*(i-lo)

def main():
    p=argparse.ArgumentParser(); p.add_argument("jsonl"); p.add_argument("--out",default=None); a=p.parse_args()
    rows=[]
    for line in Path(a.jsonl).read_text(encoding="utf-8").splitlines():
        if line.strip(): rows.append(json.loads(line))
    by=defaultdict(list)
    for r in rows: by[(r["venue"],r["symbol"])].append(r)
    report={"schema":"licp001.calibration.v1","outcome_blind":True,"groups":{}}
    for (venue,sym),rs in sorted(by.items()):
        rs.sort(key=lambda x:x["exchange_ts_ms"]); key=f"{venue}:{sym}"
        g={"events":len(rs),"windows":{}}
        for w in WINDOWS_MS:
            vals=[]
            left=0; total=0.0
            for right,r in enumerate(rs):
                total+=float(r["notional_proxy"])
                t=r["exchange_ts_ms"]
                while left<=right and rs[left]["exchange_ts_ms"]<t-w:
                    total-=float(rs[left]["notional_proxy"]); left+=1
                vals.append(total)
            g["windows"][str(w)]={"observations":len(vals),"notional_quantiles":{str(q):qtile(vals,q) for q in QS}}
        report["groups"][key]=g
    out=json.dumps(report,indent=2,sort_keys=True)
    if a.out: Path(a.out).write_text(out,encoding="utf-8")
    print(out)
if __name__=="__main__":main()
