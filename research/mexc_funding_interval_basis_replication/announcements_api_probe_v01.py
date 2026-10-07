#!/usr/bin/env python3
import json,requests
URL="https://api.mexc.com/api/v3/announcements"
S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-MFIBR/0.1","Accept":"application/json"})
for p in [1,2,5,10,25,50,100,200]:
    try:
        r=S.get(URL,params={"language":"en-US","page":p,"limit":100},timeout=30)
        print("API_HTTP",p,r.status_code,"LEN",len(r.content))
        print("API_BODY",p,r.text[:4000])
    except Exception as e:
        print("API_ERR",p,type(e).__name__,str(e))
