#!/usr/bin/env python3
import html, json, math, re, time, urllib.parse, urllib.request, urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
U=json.loads((ROOT/"V013_FROZEN_ALPHA_FUTURES_SOURCE_UNIVERSE_2026-10-06.json").read_text())
OUT=ROOT/"results_v016_predictive_discovery"
OUT.mkdir(parents=True,exist_ok=True)

UA={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorDiscovery/1.6","Accept":"application/json,text/plain,*/*"}
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
CATALOG=48
END_2025_MS=1767225599999

def get_json(url,retries=5):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=30) as r:
                return r.status,json.load(r)
        except urllib.error.HTTPError as e:
            last=e
            if e.code in (429,403,502,503,504):
                time.sleep(1.5*(i+1))
                continue
            raise
        except Exception as e:
            last=e
            time.sleep(1.0*(i+1))
    raise last

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
alpha_syms=set(alpha_by)
duals=U["dual_source_candidates_2025"]
dual_time={x["symbol"]:x["t_dual_source_ms"] for x in duals}

def relevant_symbols_from_title(title):
    t=title.upper()
    found=set()
    for m in re.finditer(r"\(([A-Z0-9]{1,30})\)",t):
        s=m.group(1)
        if s in alpha_syms: found.add(s)
    for m in re.finditer(r"\b([A-Z0-9]{1,30})(?:USDT|USDC|FDUSD)\b",t):
        s=m.group(1)
        if s in alpha_syms: found.add(s)
    for s in alpha_syms:
        if len(s)>=3 and re.search(r"(?<![A-Z0-9])"+re.escape(s)+r"(?![A-Z0-9])",t):
            found.add(s)
    return sorted(found)

metadata=[]
for page in range(1,241):
    q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":CATALOG})
    _,j=get_json(LIST+"?"+q)
    arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []):
        arts.extend(cat.get("articles") or [])
    if not arts: break
    ys=[]
    for a in arts:
        rd=ems(a.get("releaseDate")); y=year(rd); ys.append(y)
        if not rd or y is None or y>2025: continue
        title=(a.get("title") or "").strip()
        lo=title.lower()
        if "futures" in lo or "options" in lo:
            continue
        if not any(k in lo for k in ("will list","hodler airdrops","launchpool","megadrop","listing")):
            continue
        syms=relevant_symbols_from_title(title)
        if syms:
            metadata.append({"code":str(a.get("code") or a.get("id")),"title":title,"releaseDate":rd,"year":y,"symbols":syms})
    yy=[x for x in ys if x]
    if yy and min(yy)<=2020: break
    time.sleep(0.02)

cand={}
for x in metadata:
    if x["code"] not in cand:
        cand[x["code"]]=x
    else:
        cand[x["code"]]["symbols"]=sorted(set(cand[x["code"]]["symbols"])|set(x["symbols"]))

incomplete=set()
detail_errors=[]
spot_events=[]

for idx,a in enumerate(sorted(cand.values(),key=lambda x:x["releaseDate"])):
    try:
        _,j=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":a["code"]}))
    except urllib.error.HTTPError as e:
        for s in a["symbols"]: incomplete.add(s)
        detail_errors.append({"code":a["code"],"http_status":e.code,"title":a["title"],"symbols":a["symbols"]})
        continue
    except Exception as e:
        for s in a["symbols"]: incomplete.add(s)
        detail_errors.append({"code":a["code"],"error":type(e).__name__,"title":a["title"],"symbols":a["symbols"]})
        continue

    body=norm_body(j)
    lo=body.lower()
    qualifies=("spot trading pair" in lo or "spot trading pairs" in lo) and (
        "will list" in lo or "will be the first platform to list" in lo or "spot trading will start" in lo
    )
    if not qualifies:
        continue

    body_syms=set()
    up=body.upper()
    for m in re.finditer(r"\b([A-Z0-9]{1,30})\s*/\s*(?:USDT|USDC|FDUSD|BNB|BTC|TRY)\b",up):
        if m.group(1) in alpha_syms: body_syms.add(m.group(1))
    for m in re.finditer(r"\(([A-Z0-9]{1,30})\)",a["title"].upper()):
        if m.group(1) in alpha_syms: body_syms.add(m.group(1))

    for s in sorted(body_syms & set(a["symbols"])):
        spot_events.append({
          "symbol":s,"article_code":a["code"],"title":a["title"],
          "releaseDate":a["releaseDate"],
          "releaseUtc":datetime.fromtimestamp(a["releaseDate"]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
        })
    if idx and idx%20==0: time.sleep(0.12)

first_spot={}
for r in spot_events:
    s=r["symbol"]
    if s not in first_spot or r["releaseDate"]<first_spot[s]["releaseDate"]:
        first_spot[s]=r

complete_alpha=[a for a in alpha if a["symbol"] not in incomplete]
complete_alpha_syms={a["symbol"] for a in complete_alpha}
complete_duals=[x for x in duals if x["symbol"] not in incomplete]

eligible_dual=[]
dual_exclusions=[]
for x in complete_duals:
    s=x["symbol"]; b=x["t_dual_source_ms"]; sp=first_spot.get(s)
    if sp and sp["releaseDate"]<=b:
        dual_exclusions.append({"symbol":s,"reason":"ALREADY_SPOT_AT_DUAL","spot_first":sp,"t_dual":b})
        continue
    comp7=b+7*86400000<=END_2025_MS
    comp30=b+30*86400000<=END_2025_MS
    comp90=b+90*86400000<=END_2025_MS
    d7=(1 if sp and 0<sp["releaseDate"]-b<=7*86400000 else 0) if comp7 else None
    d30=(1 if sp and 0<sp["releaseDate"]-b<=30*86400000 else 0) if comp30 else None
    d90=(1 if sp and 0<sp["releaseDate"]-b<=90*86400000 else 0) if comp90 else None
    eligible_dual.append({
      "symbol":s,"t_dual_ms":b,"t_dual_utc":x["t_dual_source_utc"],"t_dual_month":x["t_dual_source_utc"][:7],
      "spot_first":sp,"outcome_7d":d7,"outcome_30d":d30,"outcome_90d":d90
    })

bounds=sorted(set(x["t_dual_ms"] for x in eligible_dual))
controls=[]
for a in complete_alpha:
    s=a["symbol"]; at=a["listingTime"]; own=dual_time.get(s); sp=first_spot.get(s)
    chosen=None
    for b in bounds:
        if at>b: continue
        if sp and sp["releaseDate"]<=b: continue
        if own is not None and own<=b: continue
        chosen=b; break
    if chosen is None: continue
    comp7=chosen+7*86400000<=END_2025_MS
    comp30=chosen+30*86400000<=END_2025_MS
    comp90=chosen+90*86400000<=END_2025_MS
    c7=(1 if sp and 0<sp["releaseDate"]-chosen<=7*86400000 else 0) if comp7 else None
    c30=(1 if sp and 0<sp["releaseDate"]-chosen<=30*86400000 else 0) if comp30 else None
    c90=(1 if sp and 0<sp["releaseDate"]-chosen<=90*86400000 else 0) if comp90 else None
    controls.append({"symbol":s,"t_control_ms":chosen,"spot_first":sp,"own_t_dual_ms":own,
                     "outcome_7d":c7,"outcome_30d":c30,"outcome_90d":c90})

d7=[x for x in eligible_dual if x["outcome_7d"] is not None]
c7=[x for x in controls if x["outcome_7d"] is not None]
dn=len(d7); cn=len(c7); ds=sum(x["outcome_7d"] for x in d7); cs=sum(x["outcome_7d"] for x in c7)
dr=ds/dn if dn else None; cr=cs/cn if cn else None
absdiff=dr-cr if dr is not None and cr is not None else None
rr=(dr/cr if cr and dr is not None else ("INF" if cr==0 and dr and dr>0 else None))
loo=min((ds-(1 if x["outcome_7d"] else 0))/(dn-1) for x in d7) if dn>1 else None
succ_month=Counter(x["t_dual_month"] for x in d7 if x["outcome_7d"]==1)
month_conc=max(succ_month.values())/ds if ds>0 else 1.0

def fisher(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    lo=max(0,r1-(n-c1)); hi=min(r1,c1); den=math.comb(n,r1)
    def p(x): return math.comb(c1,x)*math.comb(n-c1,r1-x)/den
    po=p(a)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=po+1e-15)

fisher_p=fisher(ds,dn-ds,cs,cn-cs) if dn and cn else None

gates={
 "dual_n_ge_12":dn>=12,
 "control_n_ge_24":cn>=24,
 "dual_7d_rate_ge_25pct":dr is not None and dr>=0.25,
 "dual_rate_ge_3x_control":dr is not None and cr is not None and dr>=3*cr,
 "absolute_difference_ge_15pp":absdiff is not None and absdiff>=0.15,
 "loo_dual_rate_ge_20pct":loo is not None and loo>=0.20,
 "month_success_concentration_le_35pct":month_conc<=0.35,
}

if dn<12 or cn<24:
    verdict="SOURCE_BLOCKED"
elif all(gates.values()):
    verdict="SURVIVES_PREDICTIVE_DISCOVERY"
else:
    verdict="NO_PREDICTIVE_EDGE_DISCOVERY"

def hz(rows,key):
    z=[x for x in rows if x[key] is not None]
    return {"n":len(z),"successes":sum(x[key] for x in z),"rate":sum(x[key] for x in z)/len(z) if z else None}

summary={
 "lab_id":"BINANCE-DUAL-PRECURSOR-SPOT-HAZARD-003",
 "protocol":"V0.1 + V0.1.4 + V0.1.4.1 + V0.1.5",
 "frozen_alpha_unique":len(alpha),
 "source_complete_alpha":len(complete_alpha),
 "source_incomplete_symbol_count":len(incomplete),
 "source_incomplete_symbols":sorted(incomplete),
 "token_relevant_article_count":len(cand),
 "detail_error_count":len(detail_errors),
 "frozen_dual_source_candidates":len(duals),
 "source_complete_dual_candidates":len(complete_duals),
 "dual_excluded_already_spot":len(dual_exclusions),
 "dual_primary_n":dn,"dual_primary_successes":ds,"dual_7d_rate":dr,
 "control_primary_n":cn,"control_primary_successes":cs,"control_7d_rate":cr,
 "absolute_risk_difference":absdiff,"risk_ratio":rr,
 "loo_min_dual_7d_rate":loo,"dual_success_month_concentration":month_conc,
 "fisher_exact_two_sided":fisher_p,
 "dual_30d":hz(eligible_dual,"outcome_30d"),"control_30d":hz(controls,"outcome_30d"),
 "dual_90d":hz(eligible_dual,"outcome_90d"),"control_90d":hz(controls,"outcome_90d"),
 "gates":gates,"verdict":verdict,
 "2026_outcomes_opened":False,"market_returns_opened":False
}

(OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
(OUT/"detail_errors.json").write_text(json.dumps(detail_errors,indent=2,sort_keys=True)+"\n")
(OUT/"dual_observations.json").write_text(json.dumps(eligible_dual,indent=2,sort_keys=True)+"\n")
(OUT/"controls.json").write_text(json.dumps(controls,indent=2,sort_keys=True)+"\n")
(OUT/"dual_exclusions.json").write_text(json.dumps(dual_exclusions,indent=2,sort_keys=True)+"\n")
print("DUAL_PRECURSOR_V016_DISCOVERY_BEGIN")
print(json.dumps(summary,indent=2,sort_keys=True))
print("DUAL_PRECURSOR_V016_DISCOVERY_END")
