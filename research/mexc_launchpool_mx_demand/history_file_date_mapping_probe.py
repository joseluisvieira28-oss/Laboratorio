import requests,csv,io,json
from datetime import datetime,timezone,timedelta
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
IDS={"MX_USDT":"7fb2a8ab8a5e4eb699ac34ee340489f8","BTC_USDT":"2fb942154ef44a4ab2ef98c8afb6a4a7"}
T0=datetime.fromisoformat("2025-01-23T10:00:00+00:00")
targets=[T0,T0+timedelta(hours=1),T0+timedelta(hours=6),T0+timedelta(hours=24)]
for market,sid in IDS.items():
    idx=S.get(BASE+"/file-svc/history/download",params={"filePath":f"SPOT2/kline/{sid}/daily/Min15/"},timeout=30).json()["data"]
    mp={x["fileName"]:x for x in idx}
    print("MARKET",market)
    for ds in ["2025-01-22","2025-01-23","2025-01-24","2025-01-25"]:
        fn=f"{market}-Min15-{ds}.csv"
        rec=mp.get(fn)
        print("FILE",fn,"FOUND",bool(rec))
        if not rec: continue
        txt=S.get(rec["maskedUrl"],timeout=30).text
        rows=list(csv.DictReader(io.StringIO(txt)))
        times=[int(r["open_time"]) for r in rows if r.get("open_time")]
        if not times: continue
        lo=min(times); hi=max(times)
        print("RANGE",datetime.fromtimestamp(lo/1000,timezone.utc).isoformat(),datetime.fromtimestamp(hi/1000,timezone.utc).isoformat(),"N",len(times))
        st=set(times)
        for t in targets:
            ms=int(t.timestamp()*1000)
            print("TARGET",t.isoformat(),"PRESENT",ms in st)
