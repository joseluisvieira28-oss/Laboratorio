import requests,re
URL="https://static.mocortech.com/production/web-v4-home-seo/65/_next/static/chunks/2uqzhk5-1nu0f.js"
t=requests.get(URL,timeout=30).text
for key in ["staticSpotSymbolsMap","useStaticSpotSymbolsMap","SPOT2"]:
    print("\n===== "+key+" =====")
    start=0
    for _ in range(8):
        p=t.find(key,start)
        if p<0: break
        print(t[max(0,p-9000):p+9000])
        print("\n---\n")
        start=p+len(key)
