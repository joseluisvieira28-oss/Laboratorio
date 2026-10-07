#!/usr/bin/env python3
from __future__ import annotations
import json,re,time,math,statistics,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

LAB="GATE-FUNDING-INTERVAL-BASIS-REPLICATION-001"
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
LIST="https://miniapp.gate.com/api/web/v1/portal/announcement/list_article"
ARTICLE="https://miniapp.gate.com/announcements/article/{}"
FUND="https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
OUT=Path("gfibr_v01_source_gate_report.json")
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-GFIBR/0.1","Accept-Language":"en-US,en;q=0.9"})
CANON=(1,2,4,8,12,24)
MONTH={m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
MONTH.update({k[:3]:v for k,v in list(MONTH.items())})

def req(method,url,**kwargs):
    last=None
    for i in range(7):
        try:
            r=S.request(method,url,timeout=40,**kwargs)
            if r.status_code==429:
                last=RuntimeError("429"); time.sleep(min(30,2**(i+1))); continue
            if 400 <= r.status_code < 500:
                raise RuntimeError(f"http_{r.status_code}")
            if r.status_code>=500:
                last=RuntimeError(f"http_{r.status_code}"); time.sleep(min(20,2**i)); continue
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i<6: time.sleep(min(20,2**i))
    raise RuntimeError(str(last))

def enumerate_fee():
    # Page 1 / total from official Next.js SSR. Page 2+ from the same
    # public list_article endpoint used by the Gate client.
    r=req("GET","https://miniapp.gate.com/announcements/fee")
    soup=BeautifulSoup(r.text,"html.parser")
    nd=soup.find("script",id="__NEXT_DATA__")
    if not nd or not nd.string:
        raise RuntimeError("missing_next_data")
    obj=json.loads(nd.string)
    pp=((obj.get("props") or {}).get("pageProps") or {})
    ld=pp.get("listData") or {}
    total=int(ld.get("total") or 0)
    first=ld.get("list") or []
    if total<1 or not first:
        raise RuntimeError("invalid_ssr_listdata")
    route_query=obj.get("query") or pp.get("query") or {}
    route_category=route_query.get("category") if isinstance(route_query,dict) else None
    def has_fee_id55(xs):
        for c in xs or []:
            if str(c.get("cate","")).lower()=="fee" and int(c.get("id") or 0)==55:
                return True
            if has_fee_id55(c.get("children") or []):
                return True
        return False
    if route_category!="fee" or not has_fee_id55(pp.get("categories") or []):
        raise RuntimeError(f"ssr_fee_identity_unresolved:{route_category}")
    rows=list(first)
    pages=[{"page":1,"source":"SSR","count":len(first),"ids":[x.get("id") for x in first]}]
    for page in range(2,100):
        p={"cate_name":"fee","page":page,"size":15,"tags":"","timer":"","cate_level":2}
        j=req("POST",LIST,json=p).json()
        if j.get("code")!=0:
            raise RuntimeError(f"list_code:{j.get('code')}")
        d=j.get("data") or {}; rr=d.get("list") or []
        if rr and not all(int(x.get("cate_id") or 0)==55 for x in rr):
            raise RuntimeError(f"non_fee_rows_page_{page}")
        pages.append({"page":page,"source":"API","count":len(rr),"ids":[x.get("id") for x in rr]})
        rows.extend(rr)
        dd={int(x["id"]):x for x in rows if x.get("id") is not None}
        if len(dd)>=total:
            rows=list(dd.values()); break
        if not rr:
            raise RuntimeError(f"archive_ended_before_total:{len(dd)}/{total}")
        time.sleep(0.15)
    dd={int(x["id"]):x for x in rows if x.get("id") is not None}
    rows=list(dd.values())
    if len(rows)!=total:
        raise RuntimeError(f"enumerated_total_mismatch:{len(rows)}/{total}")
    return sorted(rows,key=lambda x:int(x.get("release_timestamp") or 0),reverse=True),total,pages

def candidate(x):
    t=((x.get("title") or "")+" "+(x.get("brief") or "")).lower()
    return "funding" in t and ("interval" in t or "frequency" in t or "settlement" in t) and ("adjust" in t or "change" in t or "frequency" in t)

def monthnum(s):
    s=s.strip().title()
    return MONTH.get(s) or MONTH.get(s[:3])

def eff_datetimes(text):
    out=[]
    # time before date: 08:00 (UTC), April 24, 2025
    rx1=re.compile(r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*\(?UTC\)?[^A-Za-z0-9]{0,12}([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(20\d{2})",re.I)
    # date before time: April 24, 2025 at 08:00 (UTC)
    rx2=re.compile(r"([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(20\d{2}).{0,35}?(\d{1,2}):(\d{2})\s*(am|pm)?\s*\(?UTC\)?",re.I)
    for m in rx1.finditer(text):
        h=int(m.group(1)); mi=int(m.group(2)); ap=(m.group(3) or "").lower()
        if ap=="pm" and h<12: h+=12
        if ap=="am" and h==12: h=0
        mon=monthnum(m.group(4))
        if mon:
            try: out.append(datetime(int(m.group(6)),mon,int(m.group(5)),h,mi,tzinfo=timezone.utc))
            except: pass
    for m in rx2.finditer(text):
        h=int(m.group(4)); mi=int(m.group(5)); ap=(m.group(6) or "").lower()
        if ap=="pm" and h<12: h+=12
        if ap=="am" and h==12: h=0
        mon=monthnum(m.group(1))
        if mon:
            try: out.append(datetime(int(m.group(3)),mon,int(m.group(2)),h,mi,tzinfo=timezone.utc))
            except: pass
    return sorted({z.isoformat():z for z in out}.values())

def symbols(text,title):
    vals=set(re.findall(r"\b([A-Z0-9]{1,30})USDT\b",(text+" "+title).upper()))
    # Titles sometimes name symbols without USDT, but article body normally has USDT.
    return sorted(vals)

def announced_new_hours(text):
    pats=[
      re.compile(r"(?:funding(?:\s+rate)?\s+(?:settlement\s+)?(?:interval|frequency)|funding\s+interval).{0,180}?(?:to|be)\s+(?:every\s+)?(1|2|4|8|12|24)\s*hours?",re.I|re.S),
      re.compile(r"(?:adjusted|executed|settled)\s+(?:to\s+)?every\s+(1|2|4|8|12|24)\s*hours?",re.I|re.S),
    ]
    vals=[]
    for rx in pats:
        vals += [int(m.group(1)) for m in rx.finditer(text)]
    return sorted(set(vals))

def funding_ts(contract,eff):
    lo=int((eff-timedelta(days=5)).timestamp()); hi=int((eff+timedelta(days=5)).timestamp())
    r=req("GET",FUND,params={"contract":contract,"from":lo,"to":hi})
    arr=r.json()
    if not isinstance(arr,list): raise RuntimeError("funding_response_not_list")
    # SAFETY: intentionally never read field 'r'.
    return sorted({int(x["t"]) for x in arr if isinstance(x,dict) and str(x.get("t","")).isdigit()})

def gap_hour(a,b):
    h=(b-a)/3600
    best=min(CANON,key=lambda z:abs(z-h))
    return best if abs(best-h)<=0.05 else None

def infer(ts,eff_s,side):
    if side=="pre":
        z=[t for t in ts if t<eff_s]
        if len(z)<4: return None,[],False
        q=z[-4:]; gaps=[gap_hour(a,b) for a,b in zip(q[:-1],q[1:])]
    else:
        z=[t for t in ts if t>=eff_s]
        if len(z)<4: return None,[],False
        q=z[:4]; gaps=[gap_hour(a,b) for a,b in zip(q[:-1],q[1:])]
    if any(x is None for x in gaps): return None,gaps,False
    c=Counter(gaps); mode,n=c.most_common(1)[0]
    return mode,gaps,n>=2

def main():
    universe,total,pages=enumerate_fee()
    earliest=min((int(x.get("release_timestamp") or 0) for x in universe),default=0)
    crossed=datetime.fromtimestamp(earliest,tz=timezone.utc)<START if earliest else False
    inwin=[x for x in universe if x.get("release_timestamp") and START<=datetime.fromtimestamp(int(x["release_timestamp"]),tz=timezone.utc)<=END]
    cand=[x for x in inwin if candidate(x)]
    print("FEE_TOTAL="+str(total))
    print("ENUMERATED="+str(len(universe)))
    print("ARCHIVE_CROSSED_PRE2023="+str(crossed))
    print("IN_WINDOW="+str(len(inwin)))
    print("CANDIDATES="+str(len(cand)))

    inspected=[]; eligible=[]
    for i,x in enumerate(sorted(cand,key=lambda z:int(z["release_timestamp"]))):
        aid=int(x["id"]); pub=datetime.fromtimestamp(int(x["release_timestamp"]),tz=timezone.utc)
        r=req("GET",ARTICLE.format(aid))
        soup=BeautifulSoup(r.text,"html.parser")
        txt=" ".join(soup.get_text(" ",strip=True).split())
        title=x.get("title") or ""
        launch=bool(re.search(r"\b(list|listing|launch)\b",title,re.I))
        delist=bool(re.search(r"delist|automatic settlement",title+" "+txt,re.I))
        effs=[z for z in eff_datetimes(txt) if z>pub and START<=z<=END]
        syms=symbols(txt,title)
        nh=announced_new_hours(txt)
        rec={"id":aid,"title":title,"publish_utc":pub.isoformat().replace("+00:00","Z"),
             "url":ARTICLE.format(aid),"source_sha256":hashlib.sha256(r.content).hexdigest(),
             "launch":launch,"delist":delist,"effective_candidates":[z.isoformat().replace("+00:00","Z") for z in effs],
             "symbols":syms,"new_hour_candidates":nh,"asset_results":[]}
        if not launch and not delist and len(effs)==1 and len(nh)==1 and syms:
            eff=effs[0]; newh=nh[0]
            for base in syms:
                contract=base+"_USDT"
                try:
                    ts=funding_ts(contract,eff); es=int(eff.timestamp())
                    old,pg,ps=infer(ts,es,"pre"); post,qg,qs=infer(ts,es,"post")
                    ok=bool(old in CANON and post in CANON and ps and qs and old>newh and post==newh)
                    ar={"contract":contract,"old_interval_hours":old,"announced_new_hours":newh,
                        "post_interval_hours":post,"pre_gaps":pg,"post_gaps":qg,"pre_stable":ps,"post_stable":qs,"eligible":ok}
                    rec["asset_results"].append(ar)
                    if ok:
                        eligible.append({"article_id":aid,"official_title":title,
                          "publish_utc":pub.isoformat().replace("+00:00","Z"),
                          "effective_utc":eff.isoformat().replace("+00:00","Z"),
                          "contract":contract,"old_interval_hours":old,"new_interval_hours":newh})
                except Exception as e:
                    rec["asset_results"].append({"contract":contract,"eligible":False,"error":f"{type(e).__name__}:{e}"})
                time.sleep(0.08)
        inspected.append(rec)
        print(f"DETAIL_PROGRESS={i+1}/{len(cand)} id={aid} effs={len(effs)} syms={len(syms)} new={nh} eligible={sum(1 for a in rec['asset_results'] if a.get('eligible'))}")
        time.sleep(0.2)

    dd={}
    for e in eligible:
        dd[(e["article_id"],e["effective_utc"],e["contract"],e["old_interval_hours"],e["new_interval_hours"])]=e
    eligible=list(dd.values())
    clusters=defaultdict(list)
    for e in eligible:
        k=f"{e['article_id']}@{e['effective_utc']}@{e['old_interval_hours']}to{e['new_interval_hours']}"
        clusters[k].append(e)
    n=len(eligible); assets=sorted({e["contract"] for e in eligible})
    years=sorted({datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00")).year for e in eligible})
    maxcl=max((len(v) for v in clusters.values()),default=0); conc=maxcl/n if n else 1.0
    gates={
      "clusters_ge_12":len(clusters)>=12,
      "asset_events_ge_20":n>=20,
      "unique_contracts_ge_8":len(assets)>=8,
      "years_ge_2":len(years)>=2,
      "max_cluster_le_35pct":conc<=0.35,
      "archive_crossed_pre2023":crossed,
      "canonical_provenance_resolved":all(str(e["article_id"]).isdigit() for e in eligible) if eligible else False,
    }
    if crossed and all(gates.values()): verdict="EXTERNAL_SOURCE_PASS"
    elif crossed: verdict="EXTERNAL_INSUFFICIENT_SAMPLE"
    else: verdict="EXTERNAL_SOURCE_BLOCKED"
    report={"family":LAB,"verdict":verdict,"outcome_access":"NONE","calendar":"2023-2025",
      "fee_total":total,"enumerated":len(universe),"archive_pages":pages,"archive_crossed_pre2023":crossed,
      "articles_in_window":len(inwin),"candidate_articles":len(cand),
      "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
      "years":years,"max_cluster_concentration":conc,"sample_gates":gates,
      "eligible_events":sorted(eligible,key=lambda e:(e["effective_utc"],e["contract"])),
      "inspected_articles":inspected,
      "safety":{"mark_values_opened":False,"index_values_opened":False,"funding_rate_r_read_or_used":False,
                "returns_opened":False,"pnl_opened":False,"authenticated_api":False,"mutation":False}}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GFIBR_SOURCE_RESULT="+verdict)
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAMPLE_GATES="+json.dumps(gates,sort_keys=True))
    print("SAFETY: no mark/index/funding-r/return/PnL values opened")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
