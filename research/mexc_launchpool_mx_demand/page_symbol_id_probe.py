import requests,re,json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
for asset in ["MX","BTC"]:
    u=f"https://www.mexc.com/market-data-download/{asset}"
    t=S.get(u,timeout=30).text
    print("\nASSET",asset,"LEN",len(t))
    for needle in [f'"{asset}_USDT"',f'{asset}_USDT',f'"currency":"{asset}"',"staticSpotSymbolsMap"]:
        pos=t.find(needle)
        print("NEEDLE",needle,"POS",pos)
        if pos>=0: print(t[max(0,pos-2500):pos+5000])
