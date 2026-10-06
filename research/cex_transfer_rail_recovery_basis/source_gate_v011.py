#!/usr/bin/env python3
"""
CTRRB V0.1.1 official-source gate.
No market outcome values are logged or persisted.
"""
from __future__ import annotations
import html, json, re, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup

BASE="https://status.exchange.coinbase.com"
S=requests.Session()
S.headers.update({"User-Agent":"CryptoLab-CTRRB-SourceGate/0.1.1 research-only"})
MONTHS={m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}

ALIASES=[
 ("BTC",[r"\bBTC\b",r"\bBitcoin(?: Network)?\b"]),
 ("ETH",[r"\bETH\b",r"\bEthereum(?: Network)?\b"]),
 ("LTC",[r"\bLTC\b",r"\bLitecoin\b"]),
 ("BCH",[r"\bBCH\b",r"\bBitcoin Cash\b"]),
 ("SOL",[r"\bSOL\b",r"\bSolana(?: Network)?\b"]),
 ("XRP",[r"\bXRP\b",r"\bXRPL\b",r"\bRipple\b"]),
 ("ADA",[r"\bADA\b",r"\bCardano\b"]),
 ("ALGO",[r"\bALGO\b",r"\bAlgorand\b"]),
 ("AVAX",[r"\bAVAX\b",r"\bAvalanche(?: C-Chain| Network)?\b"]),
 ("ATOM",[r"\bATOM\b",r"\bCosmos(?: Network)?\b"]),
 ("DOT",[r"\bDOT\b",r"\bPolkadot\b"]),
 ("XLM",[r"\bXLM\b",r"\bStellar(?: Network)?\b"]),
 ("FIL",[r"\bFIL\b",r"\bFilecoin(?: Network)?\b"]),
 ("NEAR",[r"\bNEAR\b"]),
 ("STX",[r"\bSTX\b",r"\bStacks\b"]),
 ("VET",[r"\bVET\b",r"\bVeChain\b"]),
 ("TIA",[r"\bTIA\b",r"\bCelestia(?: Network)?\b"]),
 ("SEI",[r"\bSEI\b"]),
 ("SUI",[r"\bSUI\b",r"\bSui(?: Network)?\b"]),
 ("ZEC",[r"\bZEC\b",r"\bZcash\b"]),
 ("OSMO",[r"\bOSMO\b",r"\bOsmosis(?: Network)?\b"]),
 ("KAVA",[r"\bKAVA\b",r"\bKava\b"]),
 ("TAO",[r"\bTAO\b",r"\bBittensor\b"]),
 ("ICP",[r"\bICP\b",r"\bInternet Computer\b"]),
 ("APT",[r"\bAPT\b",r"\bAptos\b"]),
 ("HBAR",[r"\bHBAR\b",r"\bHedera\b"]),
 ("XTZ",[r"\bXTZ\b",r"\bTezos\b"]),
 ("DOGE",[r"\bDOGE\b",r"\bDogecoin\b"]),
 ("EGLD",[r"\bEGLD\b",r"\bMultiversX\b"]),
 ("INJ",[r"\bINJ\b",r"\bInjective\b"]),
 ("MINA",[r"\bMINA\b",r"\bMina\b"]),
]

TRANSFER_RE=re.compile(r"send|receive|deposit|withdraw|transaction",re.I)
AMBIG_RE=re.compile(r"multiple networks|erc[- ]?20|\bMATIC\b|\bPOL\b|Polygon Network|Arbitrum Network|Base Network|Optimism Network",re.I)
MIGRATION_RE=re.compile(r"migration|token change|limit only|limit-only|trading suspension|delisting|markets? open",re.I)
SCHEDULED_RE=re.compile(r"scheduled maintenance|planned maintenance|scheduled network upgrade|due to a scheduled",re.I)
TRADE_OK_PATTERNS=[
 re.compile(r"buys?\s*,?\s*sells?.{0,180}(?:not affected|unaffected|remain unaffected|remain operational|are available)",re.I|re.S),
 re.compile(r"buys?.{0,80}sells?.{0,120}(?:not affected|unaffected|remain unaffected)",re.I|re.S),
 re.compile(r"(?:trading|spot trading).{0,100}(?:not affected|unaffected|operational|available)",re.I|re.S),
]
TRADE_BAD_RE=re.compile(r"(?:trading|buys?|sells?).{0,100}(?:suspended|unavailable|disabled|degraded|impacted|affected)",re.I|re.S)

def get(url,timeout=20,**kw):
    last=None
    for i in range(4):
        try:
            r=S.get(url,timeout=timeout,**kw)
            last=r
            if r.status_code==200: return r
        except Exception:
            pass
        time.sleep(0.5*(i+1))
    return last

def history_props(page):
    r=get(f"{BASE}/history?page={page}")
    if not r or r.status_code!=200: return None,None
    soup=BeautifulSoup(r.text,"html.parser")
    node=soup.find(attrs={"data-react-class":"HistoryIndex"})
    if not node: return None,None
    return json.loads(html.unescape(node.get("data-react-props","{}"))), len(r.content)

def infer_symbol(title):
    if AMBIG_RE.search(title): return None,"ambiguous_network_or_transition"
    matches=[]
    for sym,pats in ALIASES:
        if any(re.search(p,title,re.I) for p in pats): matches.append(sym)
    matches=list(dict.fromkeys(matches))
    if len(matches)==1: return matches[0],None
    if len(matches)>1: return None,"multiple_asset_matches"
    return None,"no_frozen_asset_mapping"

def parse_range(raw,year):
    txt=BeautifulSoup(str(raw),"html.parser").get_text(" ",strip=True)
    txt=re.sub(r"\s+"," ",txt).replace(" ,",",")
    # e.g. Dec 25, 18:43 - 21:14 PST
    pat=re.compile(r"^([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{1,2}:\d{2})\s+-\s+(?:(?:([A-Za-z]{3})\s+)?(\d{1,2}),?\s+)?(\d{1,2}:\d{2})\s+(PST|PDT)$")
    m=pat.match(txt)
    if not m: return None,None,txt
    sm,sd,st,em,ed,et,tz=m.groups()
    smn=MONTHS.get(next((k for k in MONTHS if k[:3].lower()==sm.lower()),""),None)
    if smn is None:return None,None,txt
    if em:
        em_full=next((k for k in MONTHS if k[:3].lower()==em.lower()),None)
        emn=MONTHS.get(em_full) if em_full else None
    else: emn=smn
    edn=int(ed) if ed else int(sd)
    tzinfo=timezone(timedelta(hours=-8 if tz=="PST" else -7))
    sh,si=map(int,st.split(":")); eh,ei=map(int,et.split(":"))
    sy=year; ey=year+1 if emn<smn else year
    try:
        a=datetime(sy,smn,int(sd),sh,si,tzinfo=tzinfo).astimezone(timezone.utc)
        b=datetime(ey,emn,edn,eh,ei,tzinfo=tzinfo).astimezone(timezone.utc)
        if b<a: b+=timedelta(days=1)
        return a,b,txt
    except Exception:return None,None,txt

def incident_detail(code):
    url=f"{BASE}/incidents/{code}"
    r=get(url,timeout=20)
    if not r or r.status_code!=200:
        return {"detail_http":getattr(r,"status_code",None),"detail_url":url,"detail_text":None}
    soup=BeautifulSoup(r.text,"html.parser")
    txt=" ".join(soup.stripped_strings)
    return {"detail_http":200,"detail_url":url,"detail_text":txt}

def cb_probe(symbol,end_dt):
    # Fetch only to establish source availability; never persist element values.
    a=end_dt-timedelta(minutes=10); b=end_dt+timedelta(minutes=10)
    try:
        r=S.get(f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles",
            params={"granularity":60,"start":a.isoformat().replace("+00:00","Z"),"end":b.isoformat().replace("+00:00","Z")},
            timeout=20)
        if r.status_code!=200:return {"http":r.status_code,"rows":0,"shape":"http_error"}
        obj=r.json()
        return {"http":200,"rows":len(obj) if isinstance(obj,list) else 0,"shape":type(obj).__name__}
    except Exception as e:return {"http":None,"rows":0,"shape":type(e).__name__}

def binance_probe(symbol,end_dt):
    ym=end_dt.strftime("%Y-%m")
    pair=f"{symbol}USDT"
    url=f"https://data.binance.vision/data/spot/monthly/klines/{pair}/1m/{pair}-1m-{ym}.zip"
    try:
        r=requests.head(url,timeout=20,allow_redirects=True,headers={"User-Agent":"CryptoLab-CTRRB-SourceGate/0.1.1"})
        return {"http":r.status_code,"content_length":r.headers.get("content-length"),"url":url}
    except Exception as e:return {"http":None,"content_length":None,"url":url,"error":type(e).__name__}

def main():
    month_seen=set(); page_receipts=[]; raw={}
    reached_2021=False
    for page in range(1,25):
        props,nbytes=history_props(page)
        if not props:
            page_receipts.append({"page":page,"ok":False}); continue
        months=props.get("months",[])
        yrs=[]
        for m in months:
            y=int(m.get("year",0) or 0); name=m.get("name"); yrs.append(y)
            if 2022<=y<=2025:
                month_seen.add((y,name))
                for x in m.get("incidents",[]):
                    code=str(x.get("code") or "")
                    if not code: continue
                    # code is canonical one-incident key
                    raw.setdefault(code,{"code":code,"name":str(x.get("name","")),
                        "message":str(x.get("message","")),"timestamp":str(x.get("timestamp","")),
                        "impact":x.get("impact"),"year":y,"month":name,"page":page})
        page_receipts.append({"page":page,"ok":True,"bytes":nbytes,"years":yrs,
                              "incident_rows":sum(len(m.get("incidents",[])) for m in months)})
        if yrs and min(yrs)<2022:
            reached_2021=True; break

    expected={(y,m) for y in range(2022,2026) for m in MONTHS}
    complete=(month_seen==expected and reached_2021)
    candidates=[]; rejected=[]
    for code,x in raw.items():
        title=x["name"]
        if not TRANSFER_RE.search(title+" "+x.get("message","")): continue
        if MIGRATION_RE.search(title):
            rejected.append({**x,"reject":"migration_or_trading_lifecycle"}); continue
        sym,why=infer_symbol(title)
        if not sym:
            rejected.append({**x,"reject":why}); continue
        a,b,norm=parse_range(x["timestamp"],x["year"])
        if not a or not b:
            rejected.append({**x,"symbol":sym,"reject":"timestamp_parse_failed","timestamp_normalized":norm}); continue
        candidates.append({**x,"symbol":sym,"start_utc":a.isoformat(),"end_utc":b.isoformat(),
                           "timestamp_normalized":norm})

    # Fetch official detail pages concurrently, source-only.
    details={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut={ex.submit(incident_detail,x["code"]):x["code"] for x in candidates}
        for f in as_completed(fut):
            code=fut[f]
            try: details[code]=f.result()
            except Exception as e: details[code]={"detail_http":None,"detail_url":f"{BASE}/incidents/{code}","detail_text":None,"error":type(e).__name__}

    mechanism=[]
    for x in candidates:
        d=details.get(x["code"],{})
        txt=d.get("detail_text") or ""
        reasons=[]
        if d.get("detail_http")!=200: reasons.append("official_detail_unavailable")
        if not TRANSFER_RE.search(txt): reasons.append("detail_transfer_impairment_not_proven")
        trade_ok=any(p.search(txt) for p in TRADE_OK_PATTERNS)
        if not trade_ok: reasons.append("trading_unaffected_not_explicit")
        if SCHEDULED_RE.search(txt): reasons.append("scheduled_or_planned")
        # If explicit bad-trading language exists and no unaffected proof, fail; if both, explicit unaffected governs only for buys/sells.
        if TRADE_BAD_RE.search(txt) and not trade_ok: reasons.append("trading_impairment_possible")
        if not re.search(r"resolved|fix has been implemented|operational",txt,re.I): reasons.append("recovery_not_proven")
        if reasons:
            rejected.append({k:x[k] for k in x if k!="message"}|{"detail_url":d.get("detail_url"),"reject":";".join(dict.fromkeys(reasons))})
        else:
            mechanism.append({k:x[k] for k in x if k!="message"}|{"detail_url":d.get("detail_url"),"detail_http":200})

    # Capability probe ALL mechanism-pass incidents, no output values retained.
    eligible=[]
    capability_rejected=[]
    for i,x in enumerate(mechanism):
        end_dt=datetime.fromisoformat(x["end_utc"])
        cb=cb_probe(x["symbol"],end_dt)
        bn=binance_probe(x["symbol"],end_dt)
        pass_cap=(cb.get("http")==200 and cb.get("rows",0)>0 and bn.get("http")==200)
        z={**x,"coinbase_candle_probe":cb,"binance_archive_probe":bn,"capability_pass":pass_cap}
        if pass_cap: eligible.append(z)
        else:
            z["reject"]="historical_market_data_capability_failed"
            capability_rejected.append(z)
        time.sleep(0.12)

    counts=Counter(x["symbol"] for x in eligible)
    n=len(eligible); unique=len(counts)
    maxconc=(max(counts.values())/n) if n else 1.0
    gate=(complete and n>=12 and unique>=4 and maxconc<=0.40)
    if gate: verdict="SOURCE_GATE_PASS"
    elif complete: verdict="INSUFFICIENT_SAMPLE"
    else: verdict="SOURCE_BLOCKED"

    report={
      "family":"CEX-TRANSFER-RAIL-RECOVERY-BASIS-001",
      "version":"V0.1.1",
      "outcome_access":"NONE",
      "calendar":"2022-2025; 2026 CLOSED",
      "history_complete_48_months":complete,
      "months_seen_2022_2025":len(month_seen),
      "reached_2021_boundary":reached_2021,
      "history_pages":page_receipts,
      "unique_status_incidents_2022_2025":len(raw),
      "mapped_transfer_candidates":len(candidates),
      "mechanism_pass":len(mechanism),
      "fully_eligible":n,
      "unique_assets":unique,
      "asset_counts":dict(sorted(counts.items())),
      "max_asset_concentration":maxconc,
      "gate_pass":gate,
      "verdict":verdict,
      "eligible_events":eligible,
      "capability_rejected":capability_rejected,
      "source_rejected_count":len(rejected),
      "source_rejected":rejected,
      "safety":{"historical_values_logged":False,"ohlcv_values_logged":False,"spreads_logged":False}
    }
    with open("ctrrb_v011_source_gate_report.json","w") as f: json.dump(report,f,indent=2,sort_keys=True)
    print("CTRRB_V011_VERDICT="+verdict)
    print("HISTORY_COMPLETE="+str(complete))
    print("MONTHS_SEEN="+str(len(month_seen)))
    print("UNIQUE_STATUS_INCIDENTS="+str(len(raw)))
    print("MAPPED_TRANSFER_CANDIDATES="+str(len(candidates)))
    print("MECHANISM_PASS="+str(len(mechanism)))
    print("FULLY_ELIGIBLE="+str(n))
    print("UNIQUE_ASSETS="+str(unique))
    print("ASSET_COUNTS="+json.dumps(dict(sorted(counts.items())),sort_keys=True))
    print("MAX_ASSET_CONCENTRATION="+str(maxconc))
    for x in eligible:
        print("ELIGIBLE_EVENT="+json.dumps({k:x.get(k) for k in ["code","name","symbol","start_utc","end_utc","detail_url","coinbase_candle_probe","binance_archive_probe"]},sort_keys=True))
    print("SAFETY_ASSERT=NO_MARKET_VALUES_LOGGED_OR_STORED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
