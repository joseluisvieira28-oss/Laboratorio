import requests,re
URL="https://static.mocortech.com/production/web-v4-home-seo/65/_next/static/chunks/2uqzhk5-1nu0f.js"
t=requests.get(URL,timeout=30).text
for key in ["maskedUrl","fileName","mc_market_download_title_kline_monthly"]:
    start=0
    print("\n===== KEY",key,"=====")
    for i in range(10):
        p=t.find(key,start)
        if p<0: break
        print(t[max(0,p-7000):p+7000])
        print("\n---OCCURRENCE---\n")
        start=p+len(key)
