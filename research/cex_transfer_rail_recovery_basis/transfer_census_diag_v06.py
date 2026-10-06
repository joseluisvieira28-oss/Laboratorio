#!/usr/bin/env python3
import html,json,re,requests
from bs4 import BeautifulSoup

S=requests.Session();S.headers.update({"User-Agent":"CryptoLab-TransferCensusDiag/0.6"})
rows=[]
coverage=[]
for p in range(1,25):
    try:
        r=S.get(f"https://status.exchange.coinbase.com/history?page={p}",timeout=20)
        soup=BeautifulSoup(r.text,"html.parser")
        node=soup.find(attrs={"data-react-class":"HistoryIndex"})
        if not node: continue
        props=json.loads(html.unescape(node["data-react-props"]))
        months=props.get("months",[])
        for m in months:
            y=int(m.get("year",0) or 0); mon=m.get("name")
            coverage.append({"page":p,"year":y,"month":mon,"n":len(m.get("incidents",[]))})
            if 2022<=y<=2025:
                for x in m.get("incidents",[]):
                    name=str(x.get("name",""))
                    msg=str(x.get("message",""))
                    if re.search(r"send|receive|deposit|withdraw|transaction",name+" "+msg,re.I):
                        rows.append({"page":p,"year":y,"month":mon,
                                     "code":x.get("code"),"name":name,
                                     "timestamp":x.get("timestamp"),"impact":x.get("impact"),
                                     "message":msg})
        years=[int(m.get("year",0) or 0) for m in months if m.get("year")]
        if years and min(years)<2022: break
    except Exception as e:
        print("CENSUS_PAGE_ERROR="+json.dumps({"page":p,"error":type(e).__name__+":"+str(e)[:100]}))
json.dump({"coverage":coverage,"transfer_rows":rows},open("ctrrb_transfer_census_diag.json","w"),indent=2,sort_keys=True)
print("CENSUS_MONTH_COVERAGE="+json.dumps([x for x in coverage if 2021<=x["year"]<=2026],sort_keys=True))
print("CENSUS_TRANSFER_ROW_COUNT="+str(len(rows)))
for x in rows:
    print("TRANSFER_ROW="+json.dumps(x,sort_keys=True))
print("CENSUS_DIAG_SAFETY=OFFICIAL_STATUS_TEXT_ONLY_NO_MARKET_DATA")
