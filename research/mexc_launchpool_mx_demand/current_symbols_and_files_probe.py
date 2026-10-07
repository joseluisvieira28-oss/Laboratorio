import requests,json
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
u=BASE+"/api/platform/spot/market-v2/web/symbolsV2"
r=S.get(u,timeout=30)
print("SYMBOL_ENDPOINT",r.status_code,r.url)
r.raise_for_status()
obj=r.json()

usdt=((obj.get("data") or {}).get("symbols") or {}).get("USDT") or []
print("USDT_ROWS",len(usdt))

def choose(base):
    exact=[d for d in usdt if str(d.get("vn","")).upper()==base]
    if not exact:
        return None,None
    # deterministic: prefer active-looking row, then first by srt/id
    exact=sorted(exact,key=lambda d:(0 if d.get("sts")==1 else 1, d.get("srt",10**9), str(d.get("id",""))))
    return exact[0].get("id"),exact[0]

for base in ["MX","BTC"]:
    sid,d=choose(base)
    target=base+"_USDT"
    print("CHOSEN",target,sid,json.dumps(d,ensure_ascii=False)[:5000] if d else None)
    if sid is None: continue
    file_path=f"SPOT2/kline/{sid}/daily/Min15/"
    for host in [BASE,"https://api.mexc.com"]:
        try:
            rr=S.get(host+"/file-svc/history/download",params={"filePath":file_path},timeout=30)
            print("FILES",target,host,rr.status_code,rr.url,rr.text[:30000])
        except Exception as e:
            print("FILES_ERR",target,host,repr(e))
