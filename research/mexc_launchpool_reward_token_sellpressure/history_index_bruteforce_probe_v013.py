import requests,json,os,re,time
from datetime import datetime,timezone,timedelta
OUT="artifacts/mlrts_v013_history_index_bruteforce";os.makedirs(OUT,exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0"})
BASE="https://www.mexc.com"
EVENTS=[
("XTER","2025-01-08T10:00:00Z"),("IP","2025-02-13T09:00:00Z"),
("TERM","2025-03-26T04:00:00Z"),("K","2025-03-31T15:00:00Z"),
("EPT","2025-04-21T12:00:00Z"),("SHM","2025-05-08T10:00:00Z"),
("ICEBERG","2025-05-20T11:00:00Z"),("BOMB","2025-06-17T10:10:00Z"),
("TRN","2025-07-17T17:00:00Z"),("EMBLEM","2026-04-16T15:00:00Z"),
("NEX","2026-05-20T15:00:00Z")]
# Pull any symbol metadata routes exposed publicly and harvest candidate ids for tokens.
routes=[
 BASE+"/api/platform/spot/market-v2/web/symbolsV2",
 BASE+"/api/platform/spot/market-v2/web/symbols",
 BASE+"/api/platform/spot2/market/symbols",
 "https://api.mexc.com/api/platform/spot2/market/symbols",
]
candidates={t:set() for t,_ in EVENTS}
route_receipts=[]
for u in routes:
    try:
        r=S.get(u,timeout=30);route_receipts.append({"url":u,"status":r.status_code,"len":len(r.text)})
        if not r.ok: continue
        txt=r.text
        for t,_ in EVENTS:
            for m in re.finditer(r'\{[^{}]{0,1200}\}',txt):
                s=m.group(0)
                if t+"_USDT" in s or re.search(rf'"vn"\s*:\s*"{re.escape(t)}"',s,re.I):
                    for kpat in [r'"id"\s*:\s*"([^"]+)"',r'"symbolId"\s*:\s*"([^"]+)"',r'"marketId"\s*:\s*"([^"]+)"']:
                        candidates[t].update(re.findall(kpat,s))
    except Exception as e: route_receipts.append({"url":u,"error":repr(e)})

# Probe history file indexes for all harvested ids and record which contain file dates covering T0.
results={}
for t,t0s in EVENTS:
    dt=datetime.fromisoformat(t0s.replace("Z","+00:00"))
    dates={(dt+timedelta(hours=8)).date().isoformat(),(dt+timedelta(hours=8,days=1)).date().isoformat()}
    rec={"candidate_ids":sorted(candidates[t]),"working":[]}
    for sid in sorted(candidates[t]):
        for prefix in ["SPOT2/kline","SPOT/kline"]:
            fp=f"{prefix}/{sid}/daily/Min15/"
            try:
                r=S.get(BASE+"/file-svc/history/download",params={"filePath":fp},timeout=30)
                if not r.ok: continue
                obj=r.json(); data=obj.get("data") or []
                names=[x.get("fileName","") for x in data]
                hits=[n for n in names if any(d in n for d in dates)]
                if hits:
                    rec["working"].append({"id":sid,"prefix":prefix,"files":hits[:20],"count":len(data)})
            except: pass
    results[t]=rec

out={"routes":route_receipts,"results":results,"tokens_with_working_history":sum(1 for v in results.values() if v["working"])}
with open(f"{OUT}/probe.json","w") as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({"tokens_with_working_history":out["tokens_with_working_history"],"working":{k:v["working"] for k,v in results.items() if v["working"]}},ensure_ascii=False,indent=2))
