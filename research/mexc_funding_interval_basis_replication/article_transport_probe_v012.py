#!/usr/bin/env python3
import requests
URLS=[
 "https://www.mexc.com/support/articles/17827791520083?handleDefaultLocale=keep",
 "https://www.mexc.com/en-GB/support/articles/17827791520083",
 "https://www.mexc.com/announcements/article/mexc-the-usdt-m-futures-funding-rate-settlement-frequency-adjustment-nov-27-17827791520083",
]
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 CryptoLab-MFIBR/0.1.2","Accept-Language":"en-US,en;q=0.9"})
for u in URLS:
    try:
        r=S.get(u,timeout=30,allow_redirects=True)
        body=r.text
        print("URL",u)
        print("HTTP",r.status_code,"LEN",len(r.content),"FINAL",r.url)
        low=body.lower()
        print("HAS_ADJUSTED", "has adjusted the funding rate settlement frequency" in low)
        print("HAS_12_50", "12:50" in body)
        print("SNIP", body[:500].replace("\n"," "))
    except Exception as e:
        print("ERR",u,type(e).__name__,str(e))
