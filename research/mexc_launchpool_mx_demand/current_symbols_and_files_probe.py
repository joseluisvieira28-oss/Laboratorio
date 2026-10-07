import requests,json,re
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
u=BASE+"/api/platform/spot/market-v2/web/symbolsV2"
r=S.get(u,timeout=30)
print("SYMBOL_ENDPOINT",r.status_code,r.url)
print("HEAD",r.text[:1000])
r.raise_for_status()
obj=r.json()

matches=[]
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)

for d in walk(obj):
    s=json.dumps(d,ensure_ascii=False)
    if "MX_USDT" in s or "BTC_USDT" in s:
        matches.append(d)
print("MATCHES",json.dumps(matches,ensure_ascii=False,indent=2)[:30000])

def choose(target):
    for d in matches:
        # direct symbol-like fields first
        vals={str(k):v for k,v in d.items()}
        text=json.dumps(d,ensure_ascii=False)
        if target in text:
            for k in ["id","symbolId","symbol_id","marketId","market_id"]:
                if k in d:
                    return d[k],d
    return None,None

for target in ["MX_USDT","BTC_USDT"]:
    sid,d=choose(target)
    print("CHOSEN",target,sid,json.dumps(d,ensure_ascii=False)[:5000] if d else None)
    if sid is None: continue
    path=f"SPOT2/kline/{sid}/daily/Min15/"
    for host in [BASE,"https://api.mexc.com"]:
        rr=S.get(host+"/file-svc/history/download",params={"filePath":path},timeout=30)
        print("FILES",target,host,rr.status_code,rr.url,rr.text[:20000])
