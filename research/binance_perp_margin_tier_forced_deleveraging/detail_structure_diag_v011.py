#!/usr/bin/env python3
import json, requests, re
CODES=[
 "e71da970ed29453c96018af9bf107311",
 "70c0260ac77048e2895689425b1fac00",
 "9c88b57603534ad68444e209ea9d9c28",
]
URL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
H={"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab","Accept-Language":"en-US,en;q=0.9","lang":"en","Referer":"https://www.binance.com/en/support/announcement"}

def walk(x,path="$",depth=0):
    if depth>12:return
    if isinstance(x,dict):
        print("DICT",path,"KEYS",sorted(x.keys()))
        for k,v in x.items(): walk(v,path+"."+str(k),depth+1)
    elif isinstance(x,list):
        print("LIST",path,"LEN",len(x))
        for i,v in enumerate(x[:6]): walk(v,f"{path}[{i}]",depth+1)
    elif isinstance(x,str):
        lo=x.lower()
        if any(q in lo for q in ["existing positions","leverage","margin tier","maintenance margin","liquidation","table","usdt"]):
            safe=re.sub(r"\s+"," ",x)[:700]
            print("STRING",path,"LEN",len(x),"PREFIX",repr(safe))
    elif isinstance(x,(int,float,bool)) or x is None:
        pass

for code in CODES:
    r=requests.get(URL,params={"articleCode":code},headers=H,timeout=40)
    print("\n=== CODE",code,"HTTP",r.status_code,"CT",r.headers.get("content-type"),"===")
    obj=r.json()
    walk(obj)
print("DIAG_SAFETY: official source structure/content only; no market endpoints/outcomes")
