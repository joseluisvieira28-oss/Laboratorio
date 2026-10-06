#!/usr/bin/env python3
import hashlib,json,re,requests,xml.etree.ElementTree as ET
S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-FastSourceDiag/0.2"})
urls=[]
for domain in ["https://status.coinbase.com","https://status.exchange.coinbase.com"]:
  urls += [f"{domain}/history",f"{domain}/history?page=2",f"{domain}/history?page=10",
           f"{domain}/api/v2/incidents.json",f"{domain}/api/v2/incidents.json?page=2",
           f"{domain}/api/v2/incidents.json?page=10",
           f"{domain}/history.atom",f"{domain}/history.rss"]
out=[]
for u in urls:
  x={"url":u}
  try:
    r=S.get(u,timeout=7,allow_redirects=True)
    x.update(http=r.status_code,final_url=r.url,ctype=r.headers.get("content-type",""),bytes=len(r.content),
             sha256=hashlib.sha256(r.content).hexdigest())
    ct=x["ctype"].lower()
    if "json" in ct:
      try:
        d=r.json(); arr=d.get("incidents",[]) if isinstance(d,dict) else (d if isinstance(d,list) else [])
        x["count"]=len(arr)
        x["meta"]=[{k:i.get(k) for k in ("id","name","status","created_at","resolved_at","updated_at")} for i in arr[:6] if isinstance(i,dict)]
        years=[int(str(i.get("created_at"))[:4]) for i in arr if str(i.get("created_at",""))[:4].isdigit()]
        x["year_min"]=min(years) if years else None; x["year_max"]=max(years) if years else None
      except Exception as e: x["parse_error"]=type(e).__name__
    elif "atom" in ct or "rss" in ct or u.endswith(".atom") or u.endswith(".rss"):
      try:
        root=ET.fromstring(r.content)
        entries=root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not entries: entries=root.findall(".//item")
        x["count"]=len(entries)
        dates=[]; titles=[]
        for e in entries[:100]:
          title=e.find("{http://www.w3.org/2005/Atom}title") or e.find("title")
          upd=e.find("{http://www.w3.org/2005/Atom}updated") or e.find("pubDate")
          titles.append(title.text[:120] if title is not None and title.text else None)
          if upd is not None and upd.text: dates.append(upd.text)
        x["titles"]=titles[:8]; x["date_samples"]=dates[:8]
      except Exception as e: x["parse_error"]=type(e).__name__
    else:
      txt=r.text
      x["incidents_word_count"]=len(re.findall(r"incident",txt,re.I))
      x["incident_paths"]=re.findall(r'href=["\']([^"\']*?/incidents/[^"\']+)',txt,re.I)[:10]
      x["script_srcs"]=re.findall(r'<script[^>]+src=["\']([^"\']+)',txt,re.I)[:20]
      x["api_refs"]=re.findall(r'https?://[^"\'\s>]+(?:incident|history)[^"\'\s<]*',txt,re.I)[:20]
      x["page_marker_counts"]={m:txt.count(m) for m in ["incident-container","data-incident-id","incident_updates","history?page","api/v2/incidents"]}
  except Exception as e:
    x["error"]=type(e).__name__+":"+str(e)[:100]
  out.append(x)
for x in out: print("FAST_DIAG="+json.dumps(x,sort_keys=True))
json.dump(out,open("ctrrb_source_diag_fast.json","w"),indent=2,sort_keys=True)
print("FAST_DIAG_SAFETY=SOURCE_METADATA_ONLY")
