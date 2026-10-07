#!/usr/bin/env python3
import io, json, hashlib, re, sys, time
from datetime import datetime, timezone
import requests
from pypdf import PdfReader

CPI = [
("US_CPI_2021-01-13","2021-01-13T13:30:00Z","2021-01-08",[
"https://research.danskebank.com/link/WeeklyFocus080120/$file/WeeklyFocus_080120.pdf",
"https://research.danskebank.com/link/WeeklyFocus080121/$file/WeeklyFocus_080121.pdf"]),
("US_CPI_2021-02-10","2021-02-10T13:30:00Z","2021-02-05",["https://research.danskebank.com/link/WeeklyFocus050221/$file/WeeklyFocus_050221.pdf"]),
("US_CPI_2021-03-10","2021-03-10T13:30:00Z","2021-03-05",["https://research.danskebank.com/link/WeeklyFocus050321/$file/WeeklyFocus_050321.pdf"]),
("US_CPI_2021-04-13","2021-04-13T12:30:00Z","2021-04-09",["https://research.danskebank.com/link/WeeklyFocus090421/$file/WeeklyFocus_090421.pdf"]),
("US_CPI_2021-05-12","2021-05-12T12:30:00Z","2021-05-07",["https://research.danskebank.com/link/WeeklyFocus070521/$file/WeeklyFocus_070521.pdf"]),
("US_CPI_2021-06-10","2021-06-10T12:30:00Z","2021-06-04",["https://research.danskebank.com/link/WeeklyFocus040621/$file/WeeklyFocus_040621.pdf"]),
("US_CPI_2021-07-13","2021-07-13T12:30:00Z","2021-07-09",["https://research.danskebank.com/link/WeeklyFocus090721/$file/WeeklyFocus_090721.pdf"]),
("US_CPI_2021-08-11","2021-08-11T12:30:00Z","2021-08-06",["https://research.danskebank.com/link/WeeklyFocus060821/$file/WeeklyFocus_060821.pdf"]),
("US_CPI_2021-09-14","2021-09-14T12:30:00Z","2021-09-10",["https://research.danskebank.com/link/WeeklyFocus100921/$file/WeeklyFocus_100921.pdf"]),
("US_CPI_2021-10-13","2021-10-13T12:30:00Z","2021-10-08",["https://research.danskebank.com/link/WeeklyFocus081021/$file/WeeklyFocus_081021.pdf"]),
("US_CPI_2021-11-10","2021-11-10T13:30:00Z","2021-11-05",["https://research.danskebank.com/link/WeeklyFocus051121/$file/WeeklyFocus_051121.pdf"]),
("US_CPI_2021-12-10","2021-12-10T13:30:00Z","2021-12-03",["https://research.danskebank.com/link/WeeklyFocus031221/$file/WeeklyFocus_031221.pdf"]),
]

NFP = [
("US_NFP_2021-01-08","2021-01-08T13:30:00Z","2020-12-31","wk201231-1.pdf"),
("US_NFP_2021-02-05","2021-02-05T13:30:00Z","2021-01-29","wk210129-1.pdf"),
("US_NFP_2021-03-05","2021-03-05T13:30:00Z","2021-02-26","wk210226-1.pdf"),
("US_NFP_2021-04-02","2021-04-02T12:30:00Z","2021-03-26","wk210326-1.pdf"),
("US_NFP_2021-05-07","2021-05-07T12:30:00Z","2021-04-30","wk210430-1.pdf"),
("US_NFP_2021-06-04","2021-06-04T12:30:00Z","2021-05-28","wk210528-1.pdf"),
("US_NFP_2021-07-02","2021-07-02T12:30:00Z","2021-06-25","wk210625-1.pdf"),
("US_NFP_2021-08-06","2021-08-06T12:30:00Z","2021-07-30","wk210730-1.pdf"),
("US_NFP_2021-09-03","2021-09-03T12:30:00Z","2021-08-27","wk210827-1.pdf"),
("US_NFP_2021-10-08","2021-10-08T12:30:00Z","2021-10-01","wk211001-1.pdf"),
("US_NFP_2021-11-05","2021-11-05T12:30:00Z","2021-10-29","wk211029-1.pdf"),
("US_NFP_2021-12-03","2021-12-03T13:30:00Z","2021-11-26","wk211126-1.pdf"),
]

BASE_BAKER="https://creditunions.com/wp-content/uploads/2022/04/"

HEADERS={"User-Agent":"Mozilla/5.0 (compatible; CryptoLabSourceAudit/1.0)"}

def fetch_pdf(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=30,allow_redirects=True)
        ct=(r.headers.get("content-type") or "").lower()
        ok=r.status_code==200 and (r.content[:4]==b"%PDF" or "pdf" in ct)
        return {
            "ok":ok,"status":r.status_code,"final_url":r.url,"content_type":ct,
            "bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest() if ok else None,
            "last_modified":r.headers.get("last-modified"),"etag":r.headers.get("etag"),
            "data":r.content if ok else None
        }
    except Exception as e:
        return {"ok":False,"error":repr(e)}

def pdf_text(data):
    reader=PdfReader(io.BytesIO(data))
    pages=[]
    for i,p in enumerate(reader.pages):
        try: t=p.extract_text() or ""
        except Exception as e: t=f"[EXTRACT_ERROR {e!r}]"
        pages.append(t)
    return "\n\n===PAGE===\n\n".join(pages), len(pages)

def normalized_lines(text):
    return [" ".join(x.split()) for x in text.splitlines() if x.strip()]

def cpi_probe(event_id,t0,issue_date,urls):
    best=None
    attempts=[]
    for url in urls:
        f=fetch_pdf(url); attempts.append({k:v for k,v in f.items() if k!="data"})
        if f.get("ok"):
            text,pages=pdf_text(f["data"])
            lines=normalized_lines(text)
            hits=[ln for ln in lines if re.search(r"\bCPI\s+(headline|core)\b",ln,re.I)]
            date_hits=[ln for ln in lines if issue_date in ln or datetime.fromisoformat(issue_date).strftime("%d %B %Y").lstrip("0") in ln]
            rec={k:v for k,v in f.items() if k!="data"}
            rec.update({"pages":pages,"issue_date":issue_date,"hits":hits[:12],"date_hits":date_hits[:8]})
            best=rec
            break
    complete=False
    if best:
        has_h=any(re.search(r"CPI\s+headline",x,re.I) and len(re.findall(r"[-+]?\d+(?:\.\d+)?%",x))>=4 for x in best["hits"])
        has_c=any(re.search(r"CPI\s+core",x,re.I) and len(re.findall(r"[-+]?\d+(?:\.\d+)?%",x))>=4 for x in best["hits"])
        complete=has_h and has_c
    return {"event_id":event_id,"family":"CPI","t0_utc":t0,"source_family":"Danske Bank Weekly Focus","attempts":attempts,"selected":best,"candidate_complete":complete}

def nfp_probe(event_id,t0,issue_date,filename):
    url=BASE_BAKER+filename
    f=fetch_pdf(url)
    base={k:v for k,v in f.items() if k!="data"}
    best=None; complete=False
    if f.get("ok"):
        text,pages=pdf_text(f["data"])
        lines=normalized_lines(text)
        keys=[
          r"non.?farm.*payroll", r"unemployment\s+rate",
          r"average\s+hourly\s+earnings.*m/m", r"average\s+hourly\s+earnings.*y/y",
          r"avg\.?\s*hourly\s*earnings.*m/m", r"avg\.?\s*hourly\s*earnings.*y/y"
        ]
        hits=[ln for ln in lines if any(re.search(k,ln,re.I) for k in keys)]
        printed=[ln for ln in lines if re.search(r"printed\s+as\s+of",ln,re.I)]
        flat=" ".join(text.split())
        keyword_snippets=[]
        seen=set()
        for pat in [r"hourly", r"earnings", r"non.?farm", r"unemployment"]:
            for m in re.finditer(pat,flat,re.I):
                a=max(0,m.start()-220); b=min(len(flat),m.end()+320)
                sn=flat[a:b]
                if sn not in seen:
                    seen.add(sn); keyword_snippets.append(sn)
                if len(keyword_snippets)>=20: break
        # Conservative completeness remains unchanged in this diagnostic run.
        payroll=bool(re.search(r"non.?farm.{0,120}payroll",flat,re.I))
        unemp=bool(re.search(r"unemployment.{0,80}rate",flat,re.I))
        ahe_mom=bool(re.search(r"(average|avg\.?).{0,40}hourly.{0,40}earnings.{0,120}(m/m|mom)",flat,re.I))
        ahe_yoy=bool(re.search(r"(average|avg\.?).{0,40}hourly.{0,40}earnings.{0,120}(y/y|yoy)",flat,re.I))
        complete=payroll and unemp and ahe_mom and ahe_yoy
        best=base|{"pages":pages,"issue_date":issue_date,"hits":hits[:20],"keyword_snippets":keyword_snippets[:20],"printed_as_of":printed[:8],
                   "diagnostic_flags":{"payroll":payroll,"unemployment":unemp,"ahe_mom":ahe_mom,"ahe_yoy":ahe_yoy}}
    return {"event_id":event_id,"family":"NFP","t0_utc":t0,"source_family":"The Baker Group weekly report","attempts":[base],"selected":best,"candidate_complete":complete}

def main():
    results=[]
    for x in CPI:
        results.append(cpi_probe(*x)); time.sleep(.2)
    for eid,t0,d,fn in NFP:
        results.append(nfp_probe(eid,t0,d,fn)); time.sleep(.2)
    cpi=sum(1 for r in results if r["family"]=="CPI" and r["candidate_complete"])
    nfp=sum(1 for r in results if r["family"]=="NFP" and r["candidate_complete"])
    total=cpi+nfp
    verdict="SOURCE_CENSUS_PASS" if (total>=20 and cpi>=10 and nfp>=10) else "COVERAGE_BLOCKED"
    out={
      "probe_id":"NEWS-SHOCK-V03-STATIC-CONSENSUS-2021-CENSUS-PROBE-001",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"SOURCE_ONLY",
      "gate":{"min_total":20,"min_cpi":10,"min_nfp":10},
      "counts":{"complete_total":total,"complete_cpi":cpi,"complete_nfp":nfp},
      "verdict":verdict,
      "results":results,
      "outcomes_opened":False
    }
    with open("static_consensus_2021_probe.json","w",encoding="utf-8") as f: json.dump(out,f,indent=2,ensure_ascii=False)
    with open("static_consensus_2021_probe.md","w",encoding="utf-8") as f:
        f.write(f"# Static consensus 2021 source census probe\n\n**Verdict:** {verdict}\n\n")
        f.write(f"Complete total: **{total}/24**; CPI: **{cpi}/12**; NFP: **{nfp}/12**.\n\n")
        for r in results:
            s=r.get("selected")
            f.write(f"## {r['event_id']} — {'COMPLETE' if r['candidate_complete'] else 'INCOMPLETE'}\n")
            if s:
                f.write(f"- URL: {s.get('final_url')}\n- SHA256: {s.get('sha256')}\n- Last-Modified: {s.get('last_modified')}\n- ETag: {s.get('etag')}\n")
                if s.get("printed_as_of"): f.write("- Printed-as-of: "+repr(s.get("printed_as_of"))+"\n")
                f.write("- Hits:\n")
                for h in s.get("hits",[]): f.write(f"  - {h}\n")
            else:
                f.write("- No qualifying PDF fetched.\n")
            f.write("\n")
    print(json.dumps({"verdict":verdict,"complete_total":total,"complete_cpi":cpi,"complete_nfp":nfp},indent=2))
    for r in results:
        print(r["event_id"], "COMPLETE" if r["candidate_complete"] else "INCOMPLETE")
        s=r.get("selected")
        if s:
            for h in s.get("hits",[]): print("  ",h)
            for h in s.get("keyword_snippets",[]): print("  SNIP",h)
            if s.get("diagnostic_flags"): print("  FLAGS",s.get("diagnostic_flags"))
            for h in s.get("printed_as_of",[]): print("  PRINTED",h)

if __name__=="__main__":
    main()
