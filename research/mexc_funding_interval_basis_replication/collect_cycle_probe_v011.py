#!/usr/bin/env python3
from __future__ import annotations
import json, time
from datetime import datetime, timezone
import requests

URL="https://api.mexc.com/api/v1/contract/funding_rate/history"
SYMBOL="OBT_USDT"
EFFECTIVE=datetime(2025,11,8,8,10,tzinfo=timezone.utc)
EFFECTIVE_MS=int(EFFECTIVE.timestamp()*1000)
S=requests.Session()
S.headers.update({"User-Agent":"CryptoLab-MFIBR/0.1.1","Accept":"application/json"})

def safe_rows(payload):
    data=payload.get("data",payload) if isinstance(payload,dict) else {}
    if not isinstance(data,dict):
        return [],{}
    rows=data.get("resultList") or data.get("result_list") or []
    safe=[]
    for x in rows:
        if not isinstance(x,dict):
            continue
        # Deliberately whitelist mechanics-only fields. fundingRate is never accessed.
        y={k:x.get(k) for k in ("symbol","settleTime","collectCycle") if k in x}
        safe.append(y)
    meta={k:data.get(k) for k in ("pageSize","totalCount","totalPage","currentPage") if k in data}
    return safe,meta

all_rows=[]
for page in range(1,21):
    r=S.get(URL,params={"symbol":SYMBOL,"page_num":page,"page_size":1000},timeout=30)
    print("HTTP",page,r.status_code,"LEN",len(r.content))
    r.raise_for_status()
    rows,meta=safe_rows(r.json())
    print("META",page,json.dumps(meta,sort_keys=True),"SAFE_ROWS",len(rows))
    all_rows.extend(rows)
    times=[]
    for x in rows:
        try: times.append(int(x["settleTime"]))
        except Exception: pass
    if times:
        print("RANGE",page,min(times),max(times))
        if min(times) < EFFECTIVE_MS - 3*24*3600*1000 and max(times) > EFFECTIVE_MS + 3*24*3600*1000:
            break
    if not rows:
        break
    total=meta.get("totalPage")
    if isinstance(total,int) and page>=total:
        break
    time.sleep(0.5)

usable=[]
for x in all_rows:
    try:
        usable.append((int(x["settleTime"]),int(x["collectCycle"]),x.get("symbol")))
    except Exception:
        continue
usable=sorted(set(usable))
pre=[x for x in usable if x[0] < EFFECTIVE_MS][-5:]
post=[x for x in usable if x[0] >= EFFECTIVE_MS][:5]
print("EFFECTIVE_MS",EFFECTIVE_MS)
print("PRE_SAFE",json.dumps(pre))
print("POST_SAFE",json.dumps(post))
print("PRE_COUNT",len(pre),"POST_COUNT",len(post))
if len(pre)<3 or len(post)<3:
    raise SystemExit("MECHANICS_PROBE_FAIL_INSUFFICIENT_ROWS")
print("MECHANICS_PROBE_PASS")
