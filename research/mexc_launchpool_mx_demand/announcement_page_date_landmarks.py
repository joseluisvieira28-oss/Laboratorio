import ccxt,json,time
from datetime import datetime,timezone
ex=ccxt.mexc({"enableRateLimit":True})
pages=[1,50,100,150,200,250,300,400,500,600,700,800,900,1000,1100,1200,1300,1397]
out=[]
for p in pages:
    try:
        x=ex.spot_public_get_announcements({"page":p})
        raw=x.get("data") if isinstance(x,dict) else x
        box=raw[0] if isinstance(raw,list) and raw else raw
        ds=(box or {}).get("details") or []
        ts=[int(d["postTime"]) for d in ds if d.get("postTime") is not None]
        out.append({"page":p,"n":len(ds),
          "newest":datetime.fromtimestamp(max(ts)/1000,timezone.utc).isoformat() if ts else None,
          "oldest":datetime.fromtimestamp(min(ts)/1000,timezone.utc).isoformat() if ts else None})
        time.sleep(1.0)
    except Exception as e:
        out.append({"page":p,"error":repr(e)})
        time.sleep(3)
print(json.dumps(out,indent=2))
