import requests, json
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
IDS={
 "MX_USDT":"7fb2a8ab8a5e4eb699ac34ee340489f8",
 "BTC_USDT":"2fb942154ef44a4ab2ef98c8afb6a4a7",
}
for sym,sid in IDS.items():
    path=f"SPOT2/kline/{sid}/daily/Min15/"
    r=S.get(BASE+"/file-svc/history/download",params={"filePath":path},timeout=30)
    r.raise_for_status()
    obj=r.json()
    rows=obj.get("data") or []
    target=f"{sym}-Min15-2025-01-23.csv"
    rec=next((x for x in rows if x.get("fileName")==target),None)
    print("LIST",sym,"COUNT",len(rows),"TARGET",json.dumps(rec,ensure_ascii=False))
    if rec:
        u=rec["maskedUrl"]
        rr=S.get(u,timeout=30)
        print("CSV",sym,rr.status_code,rr.url)
        print(rr.text[:3000])
