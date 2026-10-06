#!/usr/bin/env python3
import hashlib, json, re, requests
from bs4 import BeautifulSoup

S=requests.Session()
S.headers.update({"User-Agent":"CryptoLab-SourceDiagnostic/0.1 research-only"})
targets=[]
for domain in ["https://status.coinbase.com","https://status.exchange.coinbase.com"]:
    for page in [1,2,3,4,5,10,20,40]:
        targets.append(("html",f"{domain}/history?page={page}"))
    for page in [1,2,3,4,5,10,20]:
        targets.append(("json",f"{domain}/api/v2/incidents.json?page={page}"))

# Known public Statuspage page id from Coinbase Status API documentation.
for page in [1,2,3,4,5,10]:
    targets.append(("json",f"https://api.statuspage.io/v1/pages/kr0djjh0jyy9/incidents?page={page}"))
    targets.append(("json",f"https://statuspage.io/api/v2/pages/kr0djjh0jyy9/incidents?page={page}"))

def iso_year(s):
    m=re.search(r"(20\d\d)-",str(s or ""))
    return int(m.group(1)) if m else None

out=[]
for kind,url in targets:
    row={"kind":kind,"url":url}
    try:
        r=S.get(url,timeout=25,allow_redirects=True)
        row.update({
            "http":r.status_code,
            "final_url":r.url,
            "content_type":r.headers.get("content-type",""),
            "bytes":len(r.content),
            "sha256":hashlib.sha256(r.content).hexdigest(),
        })
        if "json" in r.headers.get("content-type","").lower() or kind=="json":
            try:
                obj=r.json()
                if isinstance(obj,dict):
                    arr=obj.get("incidents")
                    if arr is None and isinstance(obj.get("data"),list): arr=obj["data"]
                elif isinstance(obj,list):
                    arr=obj
                else: arr=None
                if isinstance(arr,list):
                    row["incident_count"]=len(arr)
                    safe=[]
                    for x in arr[:100]:
                        if not isinstance(x,dict): continue
                        safe.append({
                            "id":x.get("id"),
                            "name":x.get("name"),
                            "status":x.get("status"),
                            "created_at":x.get("created_at"),
                            "resolved_at":x.get("resolved_at"),
                            "updated_at":x.get("updated_at"),
                        })
                    row["incidents"]=safe
                    years=[iso_year(x.get("created_at")) for x in safe]
                    years=[y for y in years if y]
                    row["year_min"]=min(years) if years else None
                    row["year_max"]=max(years) if years else None
            except Exception as e:
                row["json_error"]=type(e).__name__
        if "text/html" in r.headers.get("content-type","").lower() or kind=="html":
            soup=BeautifulSoup(r.text,"html.parser")
            hrefs=[a.get("href","") for a in soup.find_all("a",href=True)]
            row["anchor_count"]=len(hrefs)
            row["incident_href_count"]=sum("/incidents/" in h for h in hrefs)
            row["stspg_href_count"]=sum("stspg.io/" in h for h in hrefs)
            row["incident_container_count"]=len(soup.select(".incident-container"))
            row["component_container_count"]=len(soup.select(".component-container"))
            row["data_incident_count"]=len(soup.select("[data-incident-id]"))
            # Safe source metadata only: paths and visible incident/title-like strings, no market data.
            row["sample_incident_hrefs"]=[h for h in hrefs if "/incidents/" in h][:8]
            txt=" ".join(soup.stripped_strings)
            years=[int(x) for x in re.findall(r"\b(20(?:1\d|2[0-6]))\b",txt)]
            row["visible_year_min"]=min(years) if years else None
            row["visible_year_max"]=max(years) if years else None
            row["text_prefix"]=txt[:500]
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:120]
    out.append(row)

with open("ctrrb_source_diagnostic.json","w") as f:
    json.dump(out,f,indent=2,sort_keys=True)
for x in out:
    print(json.dumps({k:x.get(k) for k in [
        "kind","url","http","final_url","bytes","incident_count","year_min","year_max",
        "anchor_count","incident_href_count","stspg_href_count","incident_container_count",
        "data_incident_count","visible_year_min","visible_year_max","error"
    ]},sort_keys=True))
    if x.get("incidents"):
        print("SAFE_INCIDENT_META="+json.dumps(x["incidents"][:8],sort_keys=True))
print("DIAGNOSTIC_SAFETY: source metadata only; no market endpoints or outcomes queried")
