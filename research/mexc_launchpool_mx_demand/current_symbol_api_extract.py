import requests,re
from urllib.parse import urljoin
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
page=S.get("https://www.mexc.com/market-data-download/BTC",timeout=30).text
scripts=sorted(set(urljoin("https://www.mexc.com",m) for m in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',page,re.I)))
for s in scripts:
    try: t=S.get(s,timeout=30).text
    except Exception: continue
    for key in ["useStaticSpotSymbolsMap","staticSpotSymbolsMap","market/symbols","symbolsMap"]:
        start=0
        hits=0
        while hits<5:
            p=t.find(key,start)
            if p<0: break
            print("\nSCRIPT",s,"KEY",key,"POS",p)
            print(t[max(0,p-12000):p+18000])
            print("\n---END---\n")
            hits+=1; start=p+len(key)
