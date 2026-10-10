#!/usr/bin/env python3
"""Static client-only exporter route reconnaissance; no exports, no address-specific calls."""
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse
from urllib import request, error
from datetime import datetime, timezone

HOME="https://trade-export.hypedexer.com/"
OUT=Path("research/hype_buyback_flow_001/receipts/exporter_static_v031")
OUT.mkdir(parents=True,exist_ok=True)
MAX=1048576

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script":
            d=dict(attrs)
            if d.get("src"):self.paths.append(d["src"])

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
http=request.build_opener(NoRedirect)

def fetch(url, label):
    start=datetime.now(timezone.utc).isoformat()
    t=time.monotonic()
    rec={"label":label,"url":url,"requested_at_utc":start}
    try:
        req=request.Request(url,headers={"User-Agent":"CryptoLab-Research-Static-Only/0.3.1"})
        with http.open(req,timeout=12) as resp:
            data=resp.read(MAX+1)
            rec["http_code"]=resp.status
            rec["content_type"]=resp.headers.get("Content-Type","")
        rec["sha256"]=hashlib.sha256(data).hexdigest()
        rec["bytes"]=len(data)
        rec["too_large"]=len(data)>MAX
        if len(data)>MAX:return rec,None
        return rec,data
    except error.HTTPError as e:
        rec["http_code"]=e.code
    except (OSError,error.URLError,TimeoutError) as e:
        rec["error_type"]=type(e).__name__
    finally:
        rec["elapsed_ms"]=round((time.monotonic()-t)*1000,2)
        rec["received_at_utc"]=datetime.now(timezone.utc).isoformat()
    return rec,None

rec={"candidate_id":"HYPE-BUYBACK-FLOW-001","phase":"SOURCE_ONLY",
     "export_requests":0,"address_specific_requests":0,"login":0,"api_keys":0,
     "outcome_reads":0,"trading_authority":"NONE",
     "run_id":os.environ.get("GITHUB_RUN_ID","LOCAL"),
     "head_commit":os.environ.get("GITHUB_SHA","UNSET"),"captures":[]}
home,html=fetch(HOME,"exporter_public_html")
rec["captures"].append(home)
if html:
    p=Scripts()
    p.feed(html.decode("utf-8","replace"))
    assets=list(dict.fromkeys(urljoin(HOME,path) for path in p.paths))
    assets=[a for a in assets if urlparse(a).hostname=="trade-export.hypedexer.com" and urlparse(a).path.endswith(".js")]
    def score(u):
        p=urlparse(u).path.lower()
        return 0 if "page" in p or "app" in p or "index" in p else 1
    assets=sorted(assets,key=score)
    rec["same_origin_script_count"]=len(assets)
    rec["selected_script_paths"]=[urlparse(a).path for a in assets[:10]]
    for k,u in enumerate(assets[:10]):
        meta,body=fetch(u,f"public_static_js_{k+1}")
        if body:
            s=body.decode("utf-8","replace")
            patterns={
                "public_api_urls":sorted(set(re.findall(r"https?://[a-zA-Z0-9.\-]+(?:/[a-zA-Z0-9_./\-]+)?",s)))[:20],
                "literal_api_paths":sorted(set(re.findall(r"""(?:/api/[a-zA-Z0-9_./-]+|/export/[a-zA-Z0-9_./-]+|/download/[a-zA-Z0-9_./-]+)""",s)))[:30],
            }
            meta["only_static_strings"]=patterns
            meta["source_clue_counts"]={q: s.lower().count(q) for q in ("hypedexer","api/","export","download","history","csv","gzip")}
            meta["mentions_csv_gz"]=(".csv.gz" in s)
            meta["mentions_export"]=("export" in s.lower())
            meta["mentions_auth"]=any(z in s.lower() for z in ("authorization","apikey","api_key"))
        rec["captures"].append(meta)
rec["finished_utc"]=datetime.now(timezone.utc).isoformat()
(OUT/"PUBLIC_EXPORT_FRONTEND_ROUTE_RECEIPT_V031.json").write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
print(json.dumps(rec,sort_keys=True,indent=2))
