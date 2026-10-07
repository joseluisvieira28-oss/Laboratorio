#!/usr/bin/env python3
import json,urllib.request,ssl
from datetime import datetime,timezone
TARGET=datetime.fromisoformat("2024-03-28T07:30:17.312779865+00:00")
RPCS=[
 "https://shentu.rpc.m.anode.team",
 "https://shentu-rpc.panthea.eu",
 "https://rpc.shentu.org",
 "https://shentu.rpc.m.stavr.tech"
]
UA={"User-Agent":"CryptoLab-CTK-T0/0.2"}
def req(url):
  try:
    r=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(r,timeout=10,context=ssl.create_default_context()) as x:return json.loads(x.read().decode()),None
  except Exception as e:return None,f"{type(e).__name__}: {e}"
def block(rpc,h):
  j,e=req(f"{rpc}/block?height={h}")
  if e or not j or not j.get("result"):return None,e or "no result"
  z=j["result"]; hd=z["block"]["header"]
  return {"height":int(hd["height"]),"time":hd["time"],"hash":z["block_id"]["hash"]},None
def dt(s):return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)
out={"target":TARGET.isoformat(),"providers":[]}
for rpc in RPCS:
  rec={"rpc":rpc,"ladder":[]}; lo=hi=None
  for h in range(4603000,20000001,500000):
    b,e=block(rpc,h); rec["ladder"].append({"height":h,"time":b["time"] if b else None,"error":e})
    if not b:continue
    if dt(b["time"])<TARGET: lo=b
    elif lo: hi=b; break
  if lo and hi:
    l,r=lo["height"],hi["height"]
    while l+1<r:
      m=(l+r)//2;b,e=block(rpc,m)
      if not b:rec["binary_error"]={"height":m,"error":e};break
      if dt(b["time"])<TARGET:l=m
      else:r=m
    else:
      b,e=block(rpc,r);p,_=block(rpc,r-1)
      rec["boundary"]={"prev":p,"first_ge":b}
  out["providers"].append(rec)
print(json.dumps(out,indent=2))
open("ctk38_alt_t0_v02.json","w").write(json.dumps(out,indent=2))
