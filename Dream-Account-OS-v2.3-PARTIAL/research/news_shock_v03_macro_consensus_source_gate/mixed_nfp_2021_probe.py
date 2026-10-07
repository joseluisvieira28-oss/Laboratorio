#!/usr/bin/env python3
import io, json, hashlib, re, time
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pdfplumber

EVENTS=[
("US_NFP_2021-01-08","2021-01-08","2021-01-08T13:30:00Z","wk201231-1.pdf","Dec"),
("US_NFP_2021-02-05","2021-02-05","2021-02-05T13:30:00Z","wk210129-1.pdf","Jan"),
("US_NFP_2021-03-05","2021-03-05","2021-03-05T13:30:00Z","wk210226-1.pdf","Feb"),
("US_NFP_2021-04-02","2021-04-02","2021-04-02T12:30:00Z","wk210326-1.pdf","Mar"),
("US_NFP_2021-05-07","2021-05-07","2021-05-07T12:30:00Z","wk210430-1.pdf","Apr"),
("US_NFP_2021-06-04","2021-06-04","2021-06-04T12:30:00Z","wk210528-1.pdf","May"),
("US_NFP_2021-07-02","2021-07-02","2021-07-02T12:30:00Z","wk210625-1.pdf","Jun"),
("US_NFP_2021-08-06","2021-08-06","2021-08-06T12:30:00Z","wk210730-1.pdf","Jul"),
("US_NFP_2021-09-03","2021-09-03","2021-09-03T12:30:00Z","wk210827-1.pdf","Aug"),
("US_NFP_2021-10-08","2021-10-08","2021-10-08T12:30:00Z","wk211001-1.pdf","Sep"),
("US_NFP_2021-11-05","2021-11-05","2021-11-05T12:30:00Z","wk211029-1.pdf","Oct"),
("US_NFP_2021-12-03","2021-12-03","2021-12-03T13:30:00Z","wk211126-1.pdf","Nov"),
]
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; CryptoLabSourceAudit/1.0)"}
BAKER="https://creditunions.com/wp-content/uploads/2022/04/"
LOCALES=["uk","vi","sr","en"]

def get(url, timeout=6):
    r=requests.get(url,headers=HEADERS,timeout=timeout,allow_redirects=True)
    return r

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_iso(s):
    if not s: return None
    s=s.strip()
    try:
        if s.endswith("Z"): return datetime.fromisoformat(s[:-1]+"+00:00")
        return datetime.fromisoformat(s)
    except: return None

def extract_published(soup, text):
    candidates=[]
    for key in [("property","article:published_time"),("name","article:published_time"),("itemprop","datePublished")]:
        el=soup.find(attrs={key[0]:key[1]})
        if el:
            v=el.get("content") or el.get_text(" ",strip=True)
            if v: candidates.append(v)
    for sc in soup.find_all("script",attrs={"type":"application/ld+json"}):
        try:
            obj=json.loads(sc.string or sc.get_text())
            objs=obj if isinstance(obj,list) else [obj]
            for o in objs:
                if isinstance(o,dict) and o.get("datePublished"): candidates.append(str(o["datePublished"]))
        except: pass
    m=re.search(r"(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})",text)
    if m: candidates.append(m.group(1)+" "+m.group(2))
    return list(dict.fromkeys(candidates))

def tt_article_for_date(date):
    d=datetime.fromisoformat(date)
    token=d.strftime("%d-%m-%Y")
    attempts=[]
    article_candidates=[]
    for loc in LOCALES:
        u=f"https://www.teletrade.org/{loc}/analytics/market-analysis/market-news/date-{token}"
        try:
            r=get(u)
            attempts.append({"url":u,"status":r.status_code,"final_url":r.url,"bytes":len(r.content)})
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.find_all("a",href=True):
                href=a["href"]
                label=" ".join(a.get_text(" ",strip=True).split())
                if re.search(r"/analytics/market-analysis/market-news/\d+$",href):
                    if "schedule for today" in label.lower() or ("schedule" in label.lower() and date[:4] in r.text):
                        article_candidates.append(urljoin(r.url,href))
            # also accept any article link whose nearby parent says Schedule for today
            for a in soup.find_all("a",href=True):
                href=a["href"]
                if not re.search(r"/analytics/market-analysis/market-news/\d+$",href): continue
                parent=" ".join((a.parent.get_text(" ",strip=True) if a.parent else "").split())
                if "schedule for today" in parent.lower(): article_candidates.append(urljoin(r.url,href))
        except Exception as e:
            attempts.append({"url":u,"error":repr(e)})
    article_candidates=list(dict.fromkeys(article_candidates))
    # If archive discovery failed, no guessing article IDs.
    best=None
    for u in article_candidates[:20]:
        try:
            r=get(u)
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text,"html.parser")
            title=" ".join((soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else "").split())
            text=" ".join(soup.get_text(" ",strip=True).split())
            if "schedule for today" not in (title+" "+text[:500]).lower(): continue
            pub=extract_published(soup,text)
            rows=[]
            fields={}
            for tr in soup.find_all("tr"):
                cells=[" ".join(x.get_text(" ",strip=True).split()) for x in tr.find_all(["td","th"])]
                if len(cells)<4: continue
                row=" | ".join(cells)
                rows.append(row)
                low=row.lower()
                # prefer US/U.S. rows only
                if not ("u.s." in low or "| us " in low or "united states" in low): continue
                forecast=cells[-1].strip() if cells else ""
                if "nonfarm payroll" in low and "private" not in low:
                    fields["nfp_change_k"]={"forecast":forecast,"row":row}
                elif "unemployment rate" in low:
                    fields["unemployment_rate"]={"forecast":forecast,"row":row}
                elif "average hourly earnings" in low:
                    fields["ahe_mom"]={"forecast":forecast,"row":row}
            # fallback regex on normalized text for known table layout if soup table lost structure
            if len(fields)<3:
                for name,pat in [
                    ("nfp_change_k",r"U\.S\.\s+\|\s+Nonfarm Payrolls\s+\|[^|]*\|[^|]*\|\s*([^|\s]+)"),
                    ("unemployment_rate",r"U\.S\.\s+\|\s+Unemployment Rate\s+\|[^|]*\|[^|]*\|\s*([^|\s]+)"),
                    ("ahe_mom",r"U\.S\.\s+\|\s+Average hourly earnings\s+\|[^|]*\|[^|]*\|\s*([^|\s]+)")
                ]:
                    m=re.search(pat,text,re.I)
                    if m and name not in fields: fields[name]={"forecast":m.group(1),"row":"regex_fallback"}
            rec={"url":r.url,"status":r.status_code,"sha256":sha(r.content),"title":title,"published_candidates":pub,"fields":fields,
                 "relevant_rows":[x for x in rows if any(k in x.lower() for k in ["nonfarm payroll","unemployment rate","average hourly earnings"])][:20]}
            if len(fields)>len(best["fields"]) if best else True: best=rec
            if len(fields)>=3: break
        except Exception as e:
            attempts.append({"url":u,"error":repr(e)})
    return best,attempts,article_candidates

def baker_yoy(filename, month):
    u=BAKER+filename
    try:
        r=get(u)
        if r.status_code!=200 or not (r.content[:4]==b"%PDF" or "pdf" in (r.headers.get("content-type") or "").lower()):
            return {"ok":False,"url":u,"status":r.status_code}
        reader=PdfReader(io.BytesIO(r.content))
        text=" ".join(" ".join((p.extract_text() or "").split()) for p in reader.pages)
        printed=re.search(r"This report was printed as of:\\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}\\s+[0-9]{1,2}:[0-9]{2}(?:AM|PM))",text,re.I)

        val=None
        match_text=None
        table_evidence=[]
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    for block in table or []:
                        if len(block) < 4:
                            continue
                        # Baker table is often returned as a single block whose cells are whole columns:
                        # Date | Release | Per. | Est. | Actual | Prior | Revised.
                        cols=[[(z or "").strip() for z in (cell or "").splitlines() if (z or "").strip()] for cell in block]
                        if len(cols) < 4:
                            continue
                        releases=cols[1]
                        ests=cols[3]
                        periods=cols[2] if len(cols)>2 else []
                        for i,rel in enumerate(releases):
                            if "Average Hourly Earnings YoY" not in rel:
                                continue
                            est=ests[i] if i < len(ests) else None
                            per=periods[i] if i < len(periods) else None
                            table_evidence.append({"row_index":i,"release":rel,"period":per,"est":est})
                            if est and re.fullmatch(r"[-+]?\\d+(?:\\.\\d+)?%",est):
                                val=est
                                match_text=f"{rel} | {per} | Est={est}"
                                break
                        if val:
                            break
                    if val:
                        break
                if val:
                    break

        # Conservative fallback only when table geometry is unavailable.
        if val is None:
            pats=[
                rf"Average Hourly Earnings YoY\\s+{month}\\s+([-+]?\\d+(?:\\.\\d+)?%)",
                rf"{month}\\s*Average Hourly Earnings YoY\\s+([-+]?\\d+(?:\\.\\d+)?%)",
                r"Average Hourly Earnings YoY\\s+([-+]?\\d+(?:\\.\\d+)?%)"
            ]
            for pat in pats:
                m=re.search(pat,text,re.I)
                if m:
                    val=m.group(1); match_text=m.group(0); break

        return {"ok":True,"url":r.url,"sha256":sha(r.content),"last_modified":r.headers.get("last-modified"),"etag":r.headers.get("etag"),
                "printed_as_of":printed.group(1).strip() if printed else None,"ahe_yoy":val,"match":match_text,
                "table_evidence":table_evidence[:8]}
    except Exception as e:
        return {"ok":False,"url":u,"error":repr(e)}

def published_pre_t0(cands,t0):
    t=parse_iso(t0)
    parsed=[]
    for s in cands or []:
        d=parse_iso(s)
        if d is None:
            # Technical clock-resolution amendment: 2021 TeleTrade historical market-news
            # feed clock was independently resolved as GMT by exact alignment of same-feed
            # release posts with the page's explicit GMT schedule and frozen BLS T0.
            m=re.fullmatch(r"(\\d{2})\\.(\\d{2})\\.(\\d{4})\\s+(\\d{2}):(\\d{2})",s.strip())
            if m:
                d=datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),int(m.group(4)),int(m.group(5)),tzinfo=timezone.utc)
        if d:
            if d.tzinfo is None: continue
            parsed.append((s,d.astimezone(timezone.utc)))
    good=[(s,d) for s,d in parsed if d<t]
    return good[-1] if good else None

def main():
    results=[]
    for eid,date,t0,baker_fn,month in EVENTS:
        tt,attempts,cands=tt_article_for_date(date)
        by=baker_yoy(baker_fn,month)
        tt_pre=published_pre_t0(tt.get("published_candidates",[]) if tt else [],t0)
        tt_fields=tt.get("fields",{}) if tt else {}
        vals={
          "nfp_change_k":tt_fields.get("nfp_change_k",{}).get("forecast"),
          "unemployment_rate":tt_fields.get("unemployment_rate",{}).get("forecast"),
          "ahe_mom":tt_fields.get("ahe_mom",{}).get("forecast"),
          "ahe_yoy":by.get("ahe_yoy")
        }
        value_ok=all(v not in [None,"","--","—"] for v in vals.values())
        complete=bool(tt and tt_pre and value_ok and by.get("ok") and by.get("printed_as_of"))
        results.append({"event_id":eid,"date":date,"t0_utc":t0,"teletrade":tt,"teletrade_pre_t0":str(tt_pre) if tt_pre else None,
                        "teletrade_archive_attempts":attempts,"teletrade_article_candidates":cands,"baker":by,
                        "values":vals,"candidate_complete":complete})
        print(eid, "COMPLETE" if complete else "INCOMPLETE", vals)
        if tt:
            print("  TT",tt.get("url"),tt.get("published_candidates"),tt.get("relevant_rows"))
        else:
            print("  TT NONE candidates",cands,"attempts",attempts)
        print("  BAKER",by)
        time.sleep(.2)
    n=sum(1 for r in results if r["candidate_complete"])
    verdict="MIXED_NFP_SOURCE_CENSUS_PASS" if n>=10 else "MIXED_NFP_COVERAGE_BLOCKED"
    out={"probe_id":"NEWS-SHOCK-V03-MIXED-NFP-2021-PROBE-001","generated_at_utc":datetime.now(timezone.utc).isoformat(),
         "scope":"SOURCE_ONLY","complete_nfp":n,"gate_min":10,"verdict":verdict,"results":results,"outcomes_opened":False}
    open("mixed_nfp_2021_probe.json","w",encoding="utf-8").write(json.dumps(out,indent=2,ensure_ascii=False))
    with open("mixed_nfp_2021_probe.md","w",encoding="utf-8") as f:
        f.write(f"# Mixed NFP 2021 source census\n\n**Verdict:** {verdict}\n\nComplete: **{n}/12** (gate >=10).\n\n")
        for r in results:
            f.write(f"## {r['event_id']} — {'COMPLETE' if r['candidate_complete'] else 'INCOMPLETE'}\n")
            f.write(f"- Values: `{json.dumps(r['values'],ensure_ascii=False)}`\n")
            if r['teletrade']:
                f.write(f"- TeleTrade: {r['teletrade'].get('url')}\n- Publication candidates: {r['teletrade'].get('published_candidates')}\n")
            f.write(f"- Baker: {r['baker'].get('url')} | printed-as-of={r['baker'].get('printed_as_of')} | AHE YoY={r['baker'].get('ahe_yoy')}\n\n")
    print(json.dumps({"verdict":verdict,"complete_nfp":n},indent=2))

if __name__=="__main__": main()
