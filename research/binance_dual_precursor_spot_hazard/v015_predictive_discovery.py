#!/usr/bin/env python3
import json, math, re, time, urllib.parse, urllib.request, html
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
U=json.loads((ROOT/"V013_FROZEN_ALPHA_FUTURES_SOURCE_UNIVERSE_2026-10-06.json").read_text())
OUT=ROOT/"results_v01_predictive_discovery"
OUT.mkdir(parents=True,exist_ok=True)

UA={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorDiscovery/1.0","Accept":"application/json,text/plain,*/*"}
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
CATALOG=48
END_2025_MS=1767225599999

def get_json(url,retries=4):
    err=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=30) as r:
                return r.status,json.load(r)
        except Exception as e:
            err=e; time.sleep(0.5*(i+1))
    raise err

def ems(v):
    try:
        n=int(v)
        if n<10**11:n*=1000
        return n
    except:return None

def year(v):
    n=ems(v)
    return datetime.fromtimestamp(n/1000,tz=timezone.utc).year if n else None

def norm_body(j):
    d=(j or {}).get("data") or {}
    raw=d.get("body") or d.get("content") or d.get("articleBody") or ""
    if not isinstance(raw,str): raw=json.dumps(raw,ensure_ascii=False)
    raw=html.unescape(raw)
    raw=re.sub(r"<[^>]+>"," ",raw)
    return re.sub(r"\s+"," ",raw).strip()

alpha=U["alpha_unique_2025"]
alpha_by={x["symbol"]:x for x in alpha}
alpha_symbols=set(alpha_by)
duals=U["dual_source_candidates_2025"]
dual_by={x["symbol"]:x for x in duals}
dual_time={x["symbol"]:x["t_dual_source_ms"] for x in duals}

# Scan metadata through historical pages, but never use 2026 articles as outcomes.
candidates=[]
seen_old=False
for page in range(1,221):
    q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":CATALOG})
    try:
        _,j=get_json(LIST+"?"+q)
    except Exception as e:
        raise SystemExit("SOURCE_BLOCKED_CMS_LIST:"+type(e).__name__)
    arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []):
        arts.extend(cat.get("articles") or [])
    if not arts:break
    ys=[]
    for a in arts:
        rd=ems(a.get("releaseDate")); y=year(rd); ys.append(y)
        if not rd or y is None or y>2025: continue
        t=(a.get("title") or "").strip(); lo=t.lower()
        relevant=(
          "will list" in lo or
          "hodler airdrops" in lo or
          "launchpool" in lo or
          "megadrop" in lo or
          ("listing" in lo and "binance alpha" not in lo)
        )
        if relevant:
            candidates.append({"code":str(a.get("code") or a.get("id")),"title":t,"releaseDate":rd,"year":y})
    yy=[x for x in ys if x]
    if yy and min(yy)<=2020:
        seen_old=True; break
    time.sleep(.01)

# Dedupe candidate articles.
cand={x["code"]:x for x in candidates if x["code"]}
detail_failures=[]
spot_events=[]
for i,a in enumerate(sorted(cand.values(),key=lambda x:x["releaseDate"])):
    try:
        _,j=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":a["code"]}))
        body=norm_body(j)
    except Exception as e:
        detail_failures.append({"code":a["code"],"title":a["title"],"error":type(e).__name__})
        continue
    lo=body.lower()
    # Official body must explicitly announce a Binance Spot listing/trading launch.
    if "spot trading pair" not in lo and "spot trading pairs" not in lo:
        continue
    if "will list" not in lo and "will be the first platform to list" not in lo and "spot trading will start" not in lo:
        continue

    syms=set()
    # Strongest evidence: exact spot pair in body.
    for m in re.finditer(r"\b([A-Z0-9]{1,30})\s*/\s*(?:USDT|USDC|FDUSD|BNB|BTC|TRY)\b",body.upper()):
        if m.group(1) in alpha_symbols: syms.add(m.group(1))
    # Exact ticker in title parentheses, intersected with frozen Alpha universe.
    for m in re.finditer(r"\(([A-Z0-9]{1,30})\)",a["title"].upper()):
        if m.group(1) in alpha_symbols: syms.add(m.group(1))

    for s in sorted(syms):
        spot_events.append({
          "symbol":s,"article_code":a["code"],"title":a["title"],
          "releaseDate":a["releaseDate"],
          "releaseUtc":datetime.fromtimestamp(a["releaseDate"]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
        })
    if i and i%50==0: time.sleep(.03)

first_spot={}
for r in spot_events:
    s=r["symbol"]
    if s not in first_spot or r["releaseDate"]<first_spot[s]["releaseDate"]:
        first_spot[s]=r

if detail_failures:
    summary={
      "verdict":"SOURCE_BLOCKED",
      "reason":"CMS_DETAIL_FAILURES_ON_LISTING_RELEVANT_ARTICLES",
      "detail_failure_count":len(detail_failures),
      "detail_failures":detail_failures[:50],
      "2026_outcomes_opened":False
    }
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("DUAL_PRECURSOR_DISCOVERY_BEGIN")
    print(json.dumps(summary,indent=2,sort_keys=True))
    print("DUAL_PRECURSOR_DISCOVERY_END")
    raise SystemExit(2)

# DUAL baseline eligibility.
eligible_dual=[]
dual_exclusions=[]
for x in duals:
    s=x["symbol"]; b=x["t_dual_source_ms"]
    sp=first_spot.get(s)
    if sp and sp["releaseDate"]<=b:
        dual_exclusions.append({"symbol":s,"reason":"ALREADY_SPOT_AT_DUAL","spot_first":sp,"t_dual":b})
        continue
    complete7=b+7*86400000<=END_2025_MS
    complete30=b+30*86400000<=END_2025_MS
    complete90=b+90*86400000<=END_2025_MS
    d7=(1 if sp and 0<sp["releaseDate"]-b<=7*86400000 else 0) if complete7 else None
    d30=(1 if sp and 0<sp["releaseDate"]-b<=30*86400000 else 0) if complete30 else None
    d90=(1 if sp and 0<sp["releaseDate"]-b<=90*86400000 else 0) if complete90 else None
    eligible_dual.append({
      "symbol":s,"t_dual_ms":b,"t_dual_utc":x["t_dual_source_utc"],
      "t_dual_month":x["t_dual_source_utc"][:7],
      "spot_first":sp,"outcome_7d":d7,"outcome_30d":d30,"outcome_90d":d90,
      "complete_7d_2025":complete7,"complete_30d_2025":complete30,"complete_90d_2025":complete90
    })

retained_boundaries=sorted(set(x["t_dual_ms"] for x in eligible_dual))

# One ITT control observation per unique Alpha identity.
controls=[]
for a in alpha:
    s=a["symbol"]; at=a["listingTime"]
    own_dual=dual_time.get(s)
    sp=first_spot.get(s)
    chosen=None
    for b in retained_boundaries:
        if at>b: continue
        if sp and sp["releaseDate"]<=b: continue
        if own_dual is not None and own_dual<=b: continue
        chosen=b; break
    if chosen is None: continue
    complete7=chosen+7*86400000<=END_2025_MS
    complete30=chosen+30*86400000<=END_2025_MS
    complete90=chosen+90*86400000<=END_2025_MS
    c7=(1 if sp and 0<sp["releaseDate"]-chosen<=7*86400000 else 0) if complete7 else None
    c30=(1 if sp and 0<sp["releaseDate"]-chosen<=30*86400000 else 0) if complete30 else None
    c90=(1 if sp and 0<sp["releaseDate"]-chosen<=90*86400000 else 0) if complete90 else None
    controls.append({
      "symbol":s,"t_control_ms":chosen,
      "t_control_utc":datetime.fromtimestamp(chosen/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "spot_first":sp,"own_t_dual_ms":own_dual,
      "outcome_7d":c7,"outcome_30d":c30,"outcome_90d":c90,
      "complete_7d_2025":complete7,"complete_30d_2025":complete30,"complete_90d_2025":complete90
    })

d7=[x for x in eligible_dual if x["outcome_7d"] is not None]
c7=[x for x in controls if x["outcome_7d"] is not None]
ds=sum(x["outcome_7d"] for x in d7); cs=sum(x["outcome_7d"] for x in c7)
dn=len(d7); cn=len(c7)
dr=ds/dn if dn else None; cr=cs/cn if cn else None
absdiff=(dr-cr) if dr is not None and cr is not None else None
rr=(dr/cr) if dr is not None and cr not in (None,0) else (None if dr is None else ("INF" if dr>0 and cr==0 else None))
loo=(min((ds-(1 if x["outcome_7d"] else 0))/(dn-1) for x in d7) if dn>1 else None)

succ_month=Counter(x["t_dual_month"] for x in d7 if x["outcome_7d"]==1)
month_conc=(max(succ_month.values())/ds if ds>0 else 1.0)

def fisher_two_sided(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    lo=max(0,r1-(n-c1)); hi=min(r1,c1)
    den=math.comb(n,r1)
    def p(x):
        return math.comb(c1,x)*math.comb(n-c1,r1-x)/den
    po=p(a)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=po+1e-15)

fisher=fisher_two_sided(ds,dn-ds,cs,cn-cs) if dn and cn else None
gates={
 "dual_n_ge_12":dn>=12,
 "control_n_ge_24_or_all_available":cn>=24 or cn==len(c7),
 "dual_7d_rate_ge_25pct":dr is not None and dr>=0.25,
 "dual_rate_ge_3x_control":dr is not None and cr is not None and dr>=3*cr,
 "absolute_difference_ge_15pp":absdiff is not None and absdiff>=0.15,
 "loo_dual_rate_ge_20pct":loo is not None and loo>=0.20,
 "month_success_concentration_le_35pct":month_conc<=0.35,
}
verdict="SURVIVES_PREDICTIVE_DISCOVERY" if all(gates.values()) else "NO_PREDICTIVE_EDGE_DISCOVERY"

def hz_rate(rows,k):
    z=[x for x in rows if x[k] is not None]
    return {"n":len(z),"successes":sum(x[k] for x in z),"rate":(sum(x[k] for x in z)/len(z) if z else None)}

summary={
 "lab_id":"BINANCE-DUAL-PRECURSOR-SPOT-HAZARD-003",
 "protocol":"V0.1 + V0.1.4 + V0.1.4.1",
 "alpha_unique_2025":len(alpha),
 "frozen_dual_source_candidates":len(duals),
 "dual_excluded_already_spot":len(dual_exclusions),
 "dual_primary_n":dn,"dual_primary_successes":ds,"dual_7d_rate":dr,
 "control_primary_n":cn,"control_primary_successes":cs,"control_7d_rate":cr,
 "absolute_risk_difference":absdiff,"risk_ratio":rr,
 "loo_min_dual_7d_rate":loo,
 "dual_success_month_concentration":month_conc,
 "fisher_exact_two_sided":fisher,
 "dual_30d":hz_rate(eligible_dual,"outcome_30d"),
 "control_30d":hz_rate(controls,"outcome_30d"),
 "dual_90d":hz_rate(eligible_dual,"outcome_90d"),
 "control_90d":hz_rate(controls,"outcome_90d"),
 "spot_events_found_for_alpha_symbols":len(spot_events),
 "first_spot_symbols":len(first_spot),
 "gates":gates,
 "verdict":verdict,
 "2026_outcomes_opened":False,
 "market_returns_opened":False
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
(OUT/"dual_observations.json").write_text(json.dumps(eligible_dual,indent=2,sort_keys=True)+"\n")
(OUT/"controls.json").write_text(json.dumps(controls,indent=2,sort_keys=True)+"\n")
(OUT/"dual_exclusions.json").write_text(json.dumps(dual_exclusions,indent=2,sort_keys=True)+"\n")
(OUT/"spot_first.json").write_text(json.dumps(first_spot,indent=2,sort_keys=True)+"\n")
print("DUAL_PRECURSOR_DISCOVERY_BEGIN")
print(json.dumps(summary,indent=2,sort_keys=True))
print("DUAL_PRECURSOR_DISCOVERY_END")
