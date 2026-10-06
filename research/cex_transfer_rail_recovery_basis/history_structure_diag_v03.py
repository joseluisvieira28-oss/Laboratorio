#!/usr/bin/env python3
import json,re,requests
from bs4 import BeautifulSoup
S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-HistoryStructure/0.3"})
pages=[4,7,10,13,16,19]
out=[]
for p in pages:
    u=f"https://status.exchange.coinbase.com/history?page={p}"
    try:
        r=S.get(u,timeout=15)
        soup=BeautifulSoup(r.text,"html.parser")
        containers=soup.select(".incident-data.incident-container")
        if not containers:
            containers=soup.select(".incident-container")
        rows=[]
        for i,c in enumerate(containers[:12]):
            txt=" ".join(c.stripped_strings)
            attrs={k:str(v)[:200] for k,v in c.attrs.items()}
            # safe: official incident source text only, no market data.
            rows.append({
              "idx":i,"tag":c.name,"attrs":attrs,
              "text":txt[:1800],
              "h_text":[" ".join(h.stripped_strings)[:300] for h in c.find_all(["h1","h2","h3","h4","h5"])[:5]],
              "time_attrs":[dict(t.attrs) for t in c.find_all("time")[:10]],
              "time_text":[" ".join(t.stripped_strings) for t in c.find_all("time")[:10]]
            })
        fulltxt=" ".join(soup.stripped_strings)
        years=[int(x) for x in re.findall(r"\b(20(?:1\d|2[0-6]))\b",fulltxt)]
        out.append({"page":p,"http":r.status_code,"bytes":len(r.content),
                    "year_min":min(years) if years else None,"year_max":max(years) if years else None,
                    "containers":len(containers),"rows":rows})
    except Exception as e:
        out.append({"page":p,"error":type(e).__name__+":"+str(e)[:120]})
json.dump(out,open("ctrrb_history_structure_diag.json","w"),indent=2,sort_keys=True)
for page in out:
    print("HISTORY_PAGE_META="+json.dumps({k:page.get(k) for k in ("page","http","bytes","year_min","year_max","containers","error")},sort_keys=True))
    for row in page.get("rows",[])[:6]:
        print("HISTORY_CONTAINER="+json.dumps({"page":page["page"],**row},sort_keys=True))
print("STRUCTURE_DIAG_SAFETY=OFFICIAL_INCIDENT_TEXT_ONLY_NO_MARKET_DATA")
