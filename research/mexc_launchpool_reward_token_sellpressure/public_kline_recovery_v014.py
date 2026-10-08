import requests,json,os,time
from datetime import datetime,timezone
OUT="artifacts/mlrts_v014_public_kline_recovery";os.makedirs(OUT,exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})
EVENTS=[
("IP","2025-02-13T09:00:00Z"),("TERM","2025-03-26T04:00:00Z"),
("K","2025-03-31T15:00:00Z"),("EPT","2025-04-21T12:00:00Z"),
("ICEBERG","2025-05-20T11:00:00Z"),("BOMB","2025-06-17T10:10:00Z"),
("TRN","2025-07-17T17:00:00Z")]
Q=15*60*1000
def ms(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def ceil15(t): return ((t+Q-1)//Q)*Q
hosts=["https://api.mexc.com","https://www.mexc.com"]
results={}
for sym,t0s in EVENTS:
    entry=ceil15(ms(t0s)); end=entry+25*3600_000
    attempts=[]
    for symbol in [sym+"USDT",sym+"_USDT"]:
      for host in hosts:
        for path in ["/api/v3/klines","/api/platform/spot/market/kline"]:
          try:
            params={"symbol":symbol,"interval":"15m","startTime":entry,"endTime":end,"limit":200}
            if "platform" in path:
                params={"symbol":symbol,"interval":"Min15","startTime":entry,"endTime":end}
            r=S.get(host+path,params=params,timeout=30)
            rec={"host":host,"path":path,"symbol":symbol,"status":r.status_code,"url":r.url,"text":r.text[:10000]}
            if r.ok:
                try:
                    obj=r.json(); rec["json_type"]=type(obj).__name__; rec["json"]=obj
                except: pass
            attempts.append(rec)
          except Exception as e: attempts.append({"host":host,"path":path,"symbol":symbol,"error":repr(e)})
          time.sleep(.08)
    results[sym]={"t0":t0s,"entry_ms":entry,"attempts":attempts}
with open(f"{OUT}/probe.json","w") as f:json.dump(results,f,ensure_ascii=False,indent=2)
summary={}
for sym,rec in results.items():
    hits=[]
    for a in rec["attempts"]:
        o=a.get("json")
        n=0
        if isinstance(o,list): n=len(o)
        elif isinstance(o,dict):
            for v in o.values():
                if isinstance(v,list): n=max(n,len(v))
                elif isinstance(v,dict):
                    for vv in v.values():
                        if isinstance(vv,list):n=max(n,len(vv))
        if n: hits.append({"host":a["host"],"path":a["path"],"symbol":a["symbol"],"rows":n})
    summary[sym]=hits
print(json.dumps(summary,indent=2))
with open(f"{OUT}/summary.json","w") as f:json.dump(summary,f,indent=2)
