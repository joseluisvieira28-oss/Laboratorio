#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, html as htmlmod, json, re, subprocess, sys, urllib.parse, urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from html.parser import HTMLParser

ARCHIVE = "https://www.imfconnect.org/content/imf/en/gmm/archive.html"
OUT = Path("gmm_probe")
PDF_DIR = OUT / "pdf"
TXT_DIR = OUT / "text"
PDF_DIR.mkdir(parents=True, exist_ok=True)
TXT_DIR.mkdir(parents=True, exist_ok=True)

EVENTS = [
("US_CPI_2021-01-13","CPI","2021-01-13T13:30:00Z"),
("US_CPI_2021-02-10","CPI","2021-02-10T13:30:00Z"),
("US_CPI_2021-03-10","CPI","2021-03-10T13:30:00Z"),
("US_CPI_2021-04-13","CPI","2021-04-13T12:30:00Z"),
("US_CPI_2021-05-12","CPI","2021-05-12T12:30:00Z"),
("US_CPI_2021-06-10","CPI","2021-06-10T12:30:00Z"),
("US_CPI_2021-07-13","CPI","2021-07-13T12:30:00Z"),
("US_CPI_2021-08-11","CPI","2021-08-11T12:30:00Z"),
("US_CPI_2021-09-14","CPI","2021-09-14T12:30:00Z"),
("US_CPI_2021-10-13","CPI","2021-10-13T12:30:00Z"),
("US_CPI_2021-11-10","CPI","2021-11-10T13:30:00Z"),
("US_CPI_2021-12-10","CPI","2021-12-10T13:30:00Z"),
("US_NFP_2021-01-08","NFP","2021-01-08T13:30:00Z"),
("US_NFP_2021-02-05","NFP","2021-02-05T13:30:00Z"),
("US_NFP_2021-03-05","NFP","2021-03-05T13:30:00Z"),
("US_NFP_2021-04-02","NFP","2021-04-02T12:30:00Z"),
("US_NFP_2021-05-07","NFP","2021-05-07T12:30:00Z"),
("US_NFP_2021-06-04","NFP","2021-06-04T12:30:00Z"),
("US_NFP_2021-07-02","NFP","2021-07-02T12:30:00Z"),
("US_NFP_2021-08-06","NFP","2021-08-06T12:30:00Z"),
("US_NFP_2021-09-03","NFP","2021-09-03T12:30:00Z"),
("US_NFP_2021-10-08","NFP","2021-10-08T12:30:00Z"),
("US_NFP_2021-11-05","NFP","2021-11-05T12:30:00Z"),
("US_NFP_2021-12-03","NFP","2021-12-03T13:30:00Z"),
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.href=None
        self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            self.href=dict(attrs).get("href")
            self.text=[]
    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=="a" and self.href is not None:
            self.links.append((self.href," ".join(self.text).strip()))
            self.href=None
            self.text=[]

def get(url):
    # AEM archive hrefs contain literal spaces. Browsers percent-encode them;
    # urllib rejects such URLs unless we do the same explicitly.
    url=url.replace(" ", "%20")
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabSourceAudit/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read(), dict(r.headers)

def parse_label_date(label):
    s=re.sub(r"^(Monday|Tuesday|Wednesday|Thursday|Friday)[.,]?\s+","",label.strip(),flags=re.I)
    s=s.replace("Sept ","September ")
    for fmt in ("%B %d, %Y","%b %d, %Y"):
        try: return datetime.strptime(s,fmt).date()
        except ValueError: pass
    return None

raw,headers=get(ARCHIVE)
(OUT/"archive.html").write_bytes(raw)
parser=LinkParser(); parser.feed(raw.decode("utf-8","ignore"))
links={}
for href,label in parser.links:
    d=parse_label_date(label)
    if not d or d.year!=2021: continue
    url=urllib.parse.urljoin(ARCHIVE,href)
    if ".pdf" not in url.lower(): continue
    links[d]=(url,label)

manifest=[]
for d,(u,label) in sorted(links.items()):
    manifest.append({"date":str(d),"label":label,"url":u})
with (OUT/"archive_manifest.json").open("w") as f: json.dump(manifest,f,indent=2)

cache={}
rows=[]
for event_id,family,t0s in EVENTS:
    t0=datetime.fromisoformat(t0s.replace("Z","+00:00"))
    event_date=t0.date()
    candidates=[]
    # Strictly prior local calendar dates only: avoids same-day timestamp ambiguity.
    for d in sorted(links):
        if event_date-timedelta(days=8) <= d < event_date:
            candidates.append(d)
    for d in candidates:
        u,label=links[d]
        key=str(d)
        if key not in cache:
            rec={"date":str(d),"url":u,"label":label,"download_ok":False}
            try:
                b,h=get(u)
                p=PDF_DIR/f"{d}.pdf"; p.write_bytes(b)
                rec["bytes"]=len(b); rec["sha256"]=hashlib.sha256(b).hexdigest(); rec["download_ok"]=True
                txtp=TXT_DIR/f"{d}.txt"
                subprocess.run(["pdftotext","-layout",str(p),str(txtp)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                txt=txtp.read_text(errors="ignore")
                rec["text"]=txt
                try:
                    info=subprocess.run(["pdfinfo",str(p)],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
                except Exception:
                    info=""
                rec["pdfinfo"]=info
            except Exception as e:
                rec["error"]=repr(e)
            cache[key]=rec
        rec=cache[key]
        txt=rec.get("text","")
        low=txt.lower()
        if family=="CPI":
            family_hit=bool(re.search(r"\b(us\s+)?cpi\b|consumer price",txt,re.I))
            field_hit=bool(re.search(r"core\s+cpi|cpi\s+core|ex-food|headline",txt,re.I))
        else:
            family_hit=bool(re.search(r"nonfarm|payroll|employment situation",txt,re.I))
            field_hit=bool(re.search(r"unemployment|hourly earnings|wages",txt,re.I))
        consensus_hit=bool(re.search(r"consensus|forecast",txt,re.I))
        bloomberg_hit=bool(re.search(r"source\s*:\s*bloomberg|bloomberg",txt,re.I))
        # Preserve compact source-only snippets; do not interpret as accepted fields automatically.
        snippets=[]
        if family_hit:
            lines=[re.sub(r"\s+"," ",x).strip() for x in txt.splitlines()]
            for i,line in enumerate(lines):
                if (family=="CPI" and re.search(r"\bCPI\b|consumer price",line,re.I)) or (family=="NFP" and re.search(r"nonfarm|payroll|hourly earnings|unemployment",line,re.I)):
                    s=" | ".join(lines[max(0,i-2):min(len(lines),i+3)])
                    if s and s not in snippets:
                        snippets.append(s[:1500])
                    if len(snippets)>=8: break
        rows.append({
            "event_id":event_id,"family":family,"t0_utc":t0s,
            "candidate_doc_date":str(d),"candidate_url":u,
            "download_ok":rec.get("download_ok",False),
            "sha256":rec.get("sha256",""),
            "family_hit":family_hit,"field_context_hit":field_hit,
            "consensus_or_forecast_hit":consensus_hit,"bloomberg_hit":bloomberg_hit,
            "candidate_priority": bool(family_hit and consensus_hit),
            "snippets":" || ".join(snippets)
        })

with (OUT/"candidate_census.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

summary=[]
for event_id,family,t0s in EVENTS:
    rr=[r for r in rows if r["event_id"]==event_id]
    pri=[r for r in rr if r["candidate_priority"]]
    summary.append({
        "event_id":event_id,"family":family,"t0_utc":t0s,
        "prior_gmm_docs_scanned":len(rr),
        "priority_candidates":len(pri),
        "candidate_dates":[r["candidate_doc_date"] for r in pri],
        "status":"CANDIDATE_FOUND" if pri else "NO_GMM_CANDIDATE_FOUND"
    })
with (OUT/"event_summary.json").open("w") as f: json.dump(summary,f,indent=2)

audit={
 "probe_id":"NEWS-SHOCK-V03-IMF-GMM-PRE-T0-CENSUS-001",
 "generated_at_utc":datetime.now(timezone.utc).isoformat(),
 "source_only":True,
 "outcomes_opened":False,
 "selection":"For each frozen 2021 event, scan IMF GMM archive PDFs from the preceding 8 calendar days, strictly earlier calendar dates only.",
 "automatic_acceptance":False,
 "note":"CANDIDATE_FOUND means text relevance only. Scientific field acceptance requires manual/event-level provenance adjudication under the frozen source rules.",
 "archive_url":ARCHIVE,
 "archive_2021_pdf_links":len(links),
 "events":summary
}
download_errors=[{k:v.get(k) for k in ("date","url","error")} for v in cache.values() if not v.get("download_ok")]
audit["unique_candidate_docs_attempted"]=len(cache)
audit["unique_candidate_docs_downloaded"]=sum(1 for v in cache.values() if v.get("download_ok"))
audit["download_errors"]=download_errors[:20]
(OUT/"probe_receipt.json").write_text(json.dumps(audit,indent=2)+"\n")
print(json.dumps(audit,indent=2))
