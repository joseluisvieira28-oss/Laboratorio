#!/usr/bin/env python3
# BOME source-only timestamp coverage map. No post-T0 prices printed.
import json,urllib.parse,urllib.request,time
t0=1710581406588;m=(t0//60000)*60000;sym="BOME"
def req(a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 r=urllib.request.Request("https://api.bitget.com/api/v3/market/history-candles?"+q,headers={"User-Agent":"Mozilla/5.0"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:j=json.load(x)
  return sorted(int(z[0]) for z in (j.get("data") or []))
 except Exception as e:return []
for size in [30,45,60,90]:
 out=set();start=m-24*3600000-10*60000;finish=m-60000
 a=start
 while a<=finish:
  b=min(a+(size-1)*60000,finish)
  out.update(req(a,b));a=b+60000;time.sleep(.02)
 base=[x for x in out if m-24*3600000<=x<m-3600000]
 print(json.dumps({"window_minutes":size,"n_all_pre":len(out),"n_baseline":len(base),
 "has_p0":m-60000 in out,"old_witness":any(x<=m-24*3600000+10*60000 for x in out),
 "first":min(out) if out else None,"last":max(out) if out else None}))
