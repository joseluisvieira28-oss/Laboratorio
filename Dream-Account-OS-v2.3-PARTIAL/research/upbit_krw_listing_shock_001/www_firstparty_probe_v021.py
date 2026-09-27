#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re,urllib.error,urllib.parse,urllib.request
from html.parser import HTMLParser
from pathlib import Path

TARGETS=[
 ("WWW_NOTICE","https://www.upbit.com/service_center/notice"),
 ("EXTERNAL_ROOT","https://external-announcements.upbit.com/"),
]
UA={
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0 Safari/537.36",
 "Accept":"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
 "Accept-Language":"ko-KR,ko;q=0.9,en;q=0.6",
}

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls=[]; self.title_len=0; self._title=False; self._title_text=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag.lower()=="script" and d.get("src"): self.urls.append(d["src"])
        if tag.lower()=="link" and d.get("href"): self.urls.append(d["href"])
        if tag.lower()=="title": self._title=True
    def handle_endtag(self,tag):
        if tag.lower()=="title": self._title=False
    def handle_data(self,data):
        if self._title: self._title_text.append(data)
    def finish(self):
        self.title_len=len("".join(self._title_text).strip())

def fetch(url):
    req=urllib.request.Request(url,headers=UA,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read()
            return r.status,dict(r.headers),raw,r.geturl(),None
    except urllib.error.HTTPError as e:
        raw=e.read()
        return e.code,dict(e.headers),raw,e.geturl(),repr(e)
    except Exception as e:
        return None,{},b"",url,repr(e)

out={"probe_id":"UKLS-WWW-FIRSTPARTY-V0.2.1","historical_enumeration_opened":False,"event_values_emitted":False,"results":[]}
classes=[]
for name,url in TARGETS:
    status,h,raw,final_url,err=fetch(url)
    ct=h.get("Content-Type") or h.get("content-type")
    rec={"name":name,"http_status":status,"content_type":ct,"response_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
         "final_url":final_url,"transport_error":err}
    txt=raw.decode("utf-8","replace")
    if name=="WWW_NOTICE" and status==200 and "html" in (ct or "").lower():
        p=P(); p.feed(txt); p.finish()
        hosts=set(); first_party_urls=[]
        for u in p.urls:
            try:
                absu=urllib.parse.urljoin(final_url,u); pr=urllib.parse.urlparse(absu)
                if pr.hostname: hosts.add(pr.hostname.lower())
                if pr.hostname and (pr.hostname=="upbit.com" or pr.hostname.endswith(".upbit.com")):
                    first_party_urls.append(absu)
            except Exception: pass
        rec["html_title_length"]=p.title_len
        rec["referenced_hostnames"]=sorted(hosts)
        rec["first_party_asset_urls"]=sorted(set(first_party_urls))[:200]
        rec["string_presence"]={
          "api-manager.upbit.com":"api-manager.upbit.com" in txt,
          "external-announcements.upbit.com":"external-announcements.upbit.com" in txt,
          "announcements":"announcements" in txt.lower(),
          "service_center/notice":"service_center/notice" in txt,
        }
        classes.append("WWW_FRONTEND_TRANSPORT_CANDIDATE")
    if name=="EXTERNAL_ROOT" and status in (200,204,301,302,307,308,400,401,403,404,405):
        # public service existence only; do not infer usable endpoint from a bare root
        rec["public_service_response_observed"]=True
        if status in (200,204,400,405):
            classes.append("EXTERNAL_ANNOUNCEMENT_HOST_CANDIDATE")
    out["results"].append(rec)

if "WWW_FRONTEND_TRANSPORT_CANDIDATE" in classes:
    out["classification"]="WWW_FRONTEND_TRANSPORT_CANDIDATE"
elif "EXTERNAL_ANNOUNCEMENT_HOST_CANDIDATE" in classes:
    out["classification"]="EXTERNAL_ANNOUNCEMENT_HOST_CANDIDATE"
else:
    out["classification"]="NO_NEW_FIRST_PARTY_TRANSPORT_CANDIDATE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_WWW_FIRSTPARTY_PROBE_V0_2_1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
