#!/usr/bin/env python3
# Public Binance CMS announcement-source technical probe.
# Source-only. No market outcomes, no authentication, no account data.

import json,time,statistics,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
PARAMS={"type":1,"pageNo":1,"pageSize":20,"catalogId":48}
UA={"User-Agent":"Mozilla/5.0 CryptoLabFirstSecondsTrigger/1.0","Accept":"application/json"}

def once():
    q=urllib.parse.urlencode(PARAMS)
    req=urllib.request.Request(URL+"?"+q,headers=UA)
    t0=time.monotonic_ns()
    with urllib.request.urlopen(req,timeout=20) as r:
        body=r.read()
        status=r.status
    t1=time.monotonic_ns()
    obj=json.loads(body)
    arts=[]
    for cat in ((obj.get("data") or {}).get("catalogs") or []):
        arts.extend(cat.get("articles") or [])
    latest=arts[0] if arts else {}
    return {
      "status":status,
      "latency_ms":(t1-t0)/1e6,
      "local_monotonic_ns":t1,
      "article_count":len(arts),
      "latest_code":latest.get("code") or latest.get("id"),
      "latest_releaseDate":latest.get("releaseDate"),
      "latest_title_present":bool(latest.get("title")),
    }

rows=[]
for i in range(8):
    rows.append(once())
    time.sleep(0.35)

lats=[x["latency_ms"] for x in rows]
ids=[x["latest_code"] for x in rows]
result={
  "requests":len(rows),
  "all_http_200":all(x["status"]==200 for x in rows),
  "all_nonempty":all(x["article_count"]>0 for x in rows),
  "all_latest_identified":all(bool(x["latest_code"]) for x in rows),
  "latest_identity_stable_during_probe":len(set(ids))==1,
  "median_latency_ms":statistics.median(lats),
  "max_latency_ms":max(lats),
  "samples":rows,
}
result["trigger_source_gate_pass"]=(
    result["all_http_200"] and result["all_nonempty"] and result["all_latest_identified"]
)
print("FIRST_SECONDS_V01_ANNOUNCEMENT_SOURCE_BEGIN")
print(json.dumps(result,indent=2,sort_keys=True))
print("FIRST_SECONDS_V01_ANNOUNCEMENT_SOURCE_END")
if not result["trigger_source_gate_pass"]:
    raise SystemExit(2)
