import ccxt,requests,json,re
ex=ccxt.mexc({"enableRateLimit":True})
x=ex.spot2_public_get_market_symbols({})
print("SYMBOLS_RAW_TYPE",type(x).__name__)
rows=[]
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
for d in walk(x):
    s=json.dumps(d,ensure_ascii=False)
    if "MX_USDT" in s or "BTC_USDT" in s or ('"symbol":"MX_USDT"' in s) or ('"symbol":"BTC_USDT"' in s):
        rows.append(d)
print("MATCHES",json.dumps(rows,ensure_ascii=False,indent=2)[:30000])

def pick_id(asset):
    target=asset+"_USDT"
    for d in rows:
        txt=json.dumps(d,ensure_ascii=False)
        if target in txt:
            for k in ["id","symbolId","symbol_id","marketId","market_id"]:
                if k in d:
                    return d[k]
    return None

for asset in ["MX","BTC"]:
    sid=pick_id(asset)
    print("ASSET_ID",asset,sid)
    if sid is None: continue
    path=f"SPOT2/kline/{sid}/daily/Min15/"
    for host in ["https://www.mexc.com","https://api.mexc.com"]:
        try:
            r=requests.get(host+"/file-svc/history/download",params={"filePath":path},timeout=30,headers={"User-Agent":"Mozilla/5.0"})
            print("FILE_SVC",asset,host,r.status_code,r.url,r.text[:10000])
        except Exception as e:
            print("FILE_SVC_ERR",asset,host,repr(e))
