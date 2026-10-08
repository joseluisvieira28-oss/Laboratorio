import requests,re,json,os,time
OUT="artifacts/mlrts_v012_bundle_symbol_id_probe";os.makedirs(OUT,exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0"})
TOKENS=["XTER","IP","TERM","K","EPT","SHM","ICEBERG","BOMB","TRN","EMBLEM","NEX"]
pages=[
 "https://www.mexc.com/market-data-download",
 "https://www.mexc.com/market-data-download/BTC",
]
scripts=set()
for u in pages:
    try:
        t=S.get(u,timeout=30).text
        scripts.update(re.findall(r'https://static\.mocortech\.com/[^"\']+\.js',t))
        scripts.update("https://www.mexc.com"+x for x in re.findall(r'src="([^"]+\.js)"',t) if x.startswith("/"))
    except: pass
scripts=list(scripts)[:120]
found={t:[] for t in TOKENS}
script_receipts=[]
for i,u in enumerate(scripts):
    try:
        r=S.get(u,timeout=30);txt=r.text
        script_receipts.append({"url":u,"status":r.status_code,"len":len(txt)})
        if not r.ok:continue
        for tok in TOKENS:
            if tok+"_USDT" not in txt and f'"vn":"{tok}"' not in txt: continue
            ctx=[]
            for needle in [tok+"_USDT",f'"vn":"{tok}"']:
                start=0
                for _ in range(8):
                    p=txt.find(needle,start)
                    if p<0:break
                    c=txt[max(0,p-1200):p+2200]
                    ids=re.findall(r'"id":"([^"]{8,80})"',c)
                    ctx.append({"needle":needle,"ids":ids[:10],"context":c[:3400]})
                    start=p+len(needle)
            found[tok].append({"script":u,"contexts":ctx})
    except Exception as e:
        script_receipts.append({"url":u,"error":repr(e)})
    time.sleep(.03)
out={"scripts_scanned":len(scripts),"found":found,"scripts":script_receipts}
with open(f"{OUT}/probe.json","w") as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({"scripts_scanned":len(scripts),"token_hit_counts":{k:len(v) for k,v in found.items()}},indent=2))
