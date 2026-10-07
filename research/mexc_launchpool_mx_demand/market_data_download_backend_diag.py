import requests,re,json,os
from urllib.parse import urljoin
OUT="artifacts/mlmxd_market_data_backend_diag"
os.makedirs(OUT,exist_ok=True)
urls=[
 "https://www.mexc.com/market-data-download/BTC",
 "https://www.mexc.com/market-data-download/MX",
 "https://www.mexc.com/market-data-download?search=MX&type=kline",
]
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
out=[]
scripts=set()
for u in urls:
    r=S.get(u,timeout=30)
    rec={"url":u,"status":r.status_code,"final_url":r.url,"len":len(r.text)}
    for pat in [r'https?://[^"\']+',r'/api/[^"\']+',r'[^"\']+\.js']:
        vals=re.findall(pat,r.text)
        rec[pat]=vals[:100]
    out.append(rec)
    for m in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',r.text,re.I):
        scripts.add(urljoin(r.url,m))
json.dump(out,open(f"{OUT}/pages.json","w"),indent=2)
hits=[]
for s in sorted(scripts):
    try:
        t=S.get(s,timeout=30).text
        low=t.lower()
        if "market-data-download" in low or ("kline" in low and "download" in low):
            snippets=[]
            for key in ["market-data-download","download","kline","15min","monthly"]:
                pos=low.find(key)
                if pos>=0: snippets.append(t[max(0,pos-1000):pos+3000])
            hits.append({"script":s,"len":len(t),"snippets":snippets[:10]})
    except Exception as e:
        hits.append({"script":s,"error":repr(e)})
json.dump(hits,open(f"{OUT}/script_hits.json","w"),indent=2)
print(json.dumps({"pages":out,"scripts":len(scripts),"hit_scripts":len([x for x in hits if x.get("snippets")])},indent=2))
