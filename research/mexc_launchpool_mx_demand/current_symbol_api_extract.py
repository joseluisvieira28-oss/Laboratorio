import requests
URL="https://static.mocortech.com/production/web-v4-home-seo/65/_next/static/chunks/1z3331wy82let.js"
t=requests.get(URL,timeout=30).text
for key in ["InitSpotStore","setInitSpotSymbols","initSpot","originSpotSymbols","setSpot"]:
    print("\n===== "+key+" =====")
    start=0
    for _ in range(12):
        p=t.find(key,start)
        if p<0: break
        print(t[max(0,p-16000):p+24000])
        print("\n---\n")
        start=p+len(key)
