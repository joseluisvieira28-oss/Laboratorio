#!/usr/bin/env python3
"""
CEX-TRANSFER-RAIL-RECOVERY-BASIS-001 — V0.1 SOURCE GATE
OUTCOME BLIND by construction.

Allowed:
- Coinbase Status history/incident HTML
- public product metadata
- candle endpoint HTTP status + ROW COUNT ONLY

Forbidden:
- logging/storing any OHLC/price/volume/basis values
- 2026 incidents/outcomes
"""
from __future__ import annotations
import hashlib, json, re, sys, time
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

UA={"User-Agent":"CryptoLab-SourceGate/0.1 research-only"}
S=requests.Session(); S.headers.update(UA)
BASE="https://status.coinbase.com"
START_YEAR=2022
END_YEAR=2025
MAX_HISTORY_PAGES=80

# Native/single-primary-rail assets only. Multi-asset L2/network incidents are intentionally
# not mapped unless title names the native asset itself.
ALIASES={
 "bitcoin":"BTC","btc":"BTC","solana":"SOL","sol":"SOL","xrp":"XRP","ripple":"XRP",
 "algorand":"ALGO","algo":"ALGO","sei":"SEI","sui":"SUI","cardano":"ADA","ada":"ADA",
 "polkadot":"DOT","dot":"DOT","cosmos":"ATOM","atom":"ATOM","avalanche":"AVAX","avax":"AVAX",
 "stellar":"XLM","xlm":"XLM","litecoin":"LTC","ltc":"LTC","bitcoin cash":"BCH","bch":"BCH",
 "ethereum classic":"ETC","etc":"ETC","filecoin":"FIL","fil":"FIL","near":"NEAR",
 "internet computer":"ICP","icp":"ICP","stacks":"STX","stx":"STX","aptos":"APT","apt":"APT",
 "hedera":"HBAR","hbar":"HBAR","tezos":"XTZ","xtz":"XTZ","dogecoin":"DOGE","doge":"DOGE",
 "celestia":"TIA","tia":"TIA","injective":"INJ","inj":"INJ","mina":"MINA","vechain":"VET",
 "vet":"VET","multiversx":"EGLD","egld":"EGLD","osmosis":"OSMO","osmo":"OSMO"
}
# avoid accidental ticker substring matches by preferring longest aliases
ALIAS_KEYS=sorted(ALIASES,key=len,reverse=True)

TRANSFER_RE=re.compile(r"(delayed|paused|degraded|failed).{0,30}(send|receive|deposit|withdraw|transaction)|(send|receive|deposit|withdraw|transaction).{0,30}(delayed|paused|degraded|failed)",re.I|re.S)
TRADING_OK_RE=re.compile(r"(buys?.{0,20}sells?.{0,80}(not affected|remain unaffected|unaffected|processing as usual))|(trading.{0,40}(not affected|not impacted|unaffected))",re.I|re.S)
SCHEDULED_RE=re.compile(r"scheduled maintenance|planned maintenance|scheduled network upgrade",re.I)
TRADING_BAD_RE=re.compile(r"(trading|buys?|sells?).{0,50}(unavailable|disabled|paused|degraded|affected)",re.I|re.S)

def get(url, **kw):
    for i in range(4):
        try:
            r=S.get(url,timeout=30,**kw)
            if r.status_code==200: return r
            time.sleep(1+i)
        except Exception:
            time.sleep(1+i)
    return r if 'r' in locals() else None

def text_hash(txt):
    return hashlib.sha256(txt.encode("utf-8","ignore")).hexdigest()

def parse_dt(s):
    if not s: return None
    s=s.strip().replace("Z","+00:00")
    try:
        d=datetime.fromisoformat(s)
        if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def extract_times(soup):
    out=[]
    for t in soup.find_all("time"):
        for key in ("datetime","data-datetime"):
            d=parse_dt(t.get(key))
            if d: out.append(d)
    # Statuspage also embeds ISO timestamps in attributes/scripts.
    html=str(soup)
    for m in re.finditer(r"20(?:2[0-6])-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-][0-2]\d:[0-5]\d)",html):
        d=parse_dt(m.group(0))
        if d: out.append(d)
    # de-duplicate
    uniq={d.isoformat():d for d in out}
    return sorted(uniq.values())

def infer_symbol(title):
    lo=title.lower()
    for k in ALIAS_KEYS:
        if re.search(r"(?<![a-z0-9])"+re.escape(k)+r"(?![a-z0-9])",lo):
            return ALIASES[k]
    return None

def history_census():
    incidents={}
    page_meta=[]
    saw_pre2022=False
    for page in range(1,MAX_HISTORY_PAGES+1):
        u=f"{BASE}/history?page={page}"
        r=get(u)
        if not r or r.status_code!=200:
            page_meta.append({"page":page,"http":getattr(r,"status_code",None),"links":0})
            break
        soup=BeautifulSoup(r.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            href=a["href"]
            m=re.search(r"/incidents/([a-z0-9]+)",href)
            if not m: continue
            iid=m.group(1)
            title=" ".join(a.stripped_strings).strip()
            if not title:
                title=a.get("title","").strip()
            incidents.setdefault(iid,{"incident_id":iid,"title":title,"url":urljoin(BASE,href)})
            links.append(iid)
        years=[int(x) for x in re.findall(r"\b(20(?:1\d|2[0-6]))\b",soup.get_text(" ",strip=True))]
        if years and min(years)<START_YEAR: saw_pre2022=True
        page_meta.append({"page":page,"http":r.status_code,"links":len(set(links)),
                          "sha256":text_hash(r.text),"years_min":min(years) if years else None,
                          "years_max":max(years) if years else None})
        if page>2 and len(set(links))==0: break
        if saw_pre2022 and page>3: break
    return incidents,page_meta,saw_pre2022

def inspect_incident(meta):
    r=get(meta["url"])
    if not r or r.status_code!=200:
        return {**meta,"fetch_http":getattr(r,"status_code",None),"eligible":False,"reject":"incident_fetch_failed"}
    soup=BeautifulSoup(r.text,"html.parser")
    txt=" ".join(soup.stripped_strings)
    title=meta["title"] or (soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else "")
    symbol=infer_symbol(title)
    times=extract_times(soup)
    times_2022_25=[d for d in times if START_YEAR<=d.year<=END_YEAR]
    # exact title/body evidence only; no market data.
    transfer=bool(TRANSFER_RE.search(title+" "+txt))
    trading_ok=bool(TRADING_OK_RE.search(txt))
    scheduled=bool(SCHEDULED_RE.search(title+" "+txt))
    trading_bad=bool(TRADING_BAD_RE.search(txt)) and not trading_ok
    resolved=("resolved" in txt.lower())
    start=min(times_2022_25).isoformat() if times_2022_25 else None
    end=max(times_2022_25).isoformat() if times_2022_25 else None
    year=(min(times_2022_25).year if times_2022_25 else None)
    reasons=[]
    if not symbol: reasons.append("no_frozen_native_asset_mapping")
    if not transfer: reasons.append("no_transfer_rail_evidence")
    if not trading_ok: reasons.append("trading_unaffected_not_proven")
    if scheduled: reasons.append("planned_or_scheduled")
    if trading_bad: reasons.append("trading_also_affected")
    if not resolved: reasons.append("resolution_not_proven")
    if year is None: reasons.append("timestamp_2022_2025_not_proven")
    eligible=(len(reasons)==0)
    return {**meta,"title":title,"symbol":symbol,"fetch_http":r.status_code,
            "source_sha256":text_hash(r.text),"start_utc":start,"resolved_utc":end,
            "transfer_evidence":transfer,"trading_unaffected":trading_ok,
            "scheduled":scheduled,"resolved_text":resolved,
            "eligible_mechanism":eligible,"reject":";".join(reasons) if reasons else None}

def safe_count_json(url, params=None, list_path=None):
    """Fetch data but return only HTTP/schema/count; NEVER persist element values."""
    try:
        r=S.get(url,params=params,timeout=30)
        info={"http":r.status_code,"content_type":r.headers.get("content-type")}
        if r.status_code!=200:
            info["count"]=None; return info
        obj=r.json()
        cur=obj
        if list_path:
            for k in list_path: cur=cur[k]
        info["count"]=len(cur) if isinstance(cur,list) else None
        info["shape"]=type(cur).__name__
        return info
    except Exception as e:
        return {"http":None,"count":None,"error":type(e).__name__}

def product_metadata(symbol):
    # metadata endpoints contain no historical price outcomes.
    cb=safe_count_json(f"https://api.exchange.coinbase.com/products/{symbol}-USD")
    bn=safe_count_json("https://api.binance.com/api/v3/exchangeInfo",{"symbol":f"{symbol}USDT"})
    ok=safe_count_json("https://www.okx.com/api/v5/public/instruments",{"instType":"SPOT","instId":f"{symbol}-USDT"},["data"])
    return {"coinbase_product":cb,"binance_product":bn,"okx_product":ok}

def coverage_probe(symbol, start_iso):
    """Only row counts are returned. OHLCV arrays never leave this function."""
    d=parse_dt(start_iso)
    if not d: return {}
    a=d-timedelta(minutes=20); b=d+timedelta(minutes=20)
    cb=safe_count_json(f"https://api.exchange.coinbase.com/products/{symbol}-USD/candles",
        {"granularity":60,"start":a.isoformat().replace("+00:00","Z"),"end":b.isoformat().replace("+00:00","Z")})
    start_ms=int(a.timestamp()*1000); end_ms=int(b.timestamp()*1000)
    bn=safe_count_json("https://api.binance.com/api/v3/klines",
        {"symbol":f"{symbol}USDT","interval":"1m","startTime":start_ms,"endTime":end_ms,"limit":1000})
    # OKX probe: count only, values never logged.
    ok=safe_count_json("https://www.okx.com/api/v5/market/history-candles",
        {"instId":f"{symbol}-USDT","bar":"1m","before":str(start_ms),"after":str(end_ms),"limit":"100"},["data"])
    return {"coinbase_candle_rows":cb,"binance_kline_rows":bn,"okx_history_rows":ok}

def main():
    incidents,pages,saw_pre2022=history_census()
    inspected=[]
    # Only transfer-like titles are fetched for details.
    for m in incidents.values():
        if re.search(r"send|receive|transaction|deposit|withdraw",m["title"],re.I):
            inspected.append(inspect_incident(m))
    eligible=[x for x in inspected if x.get("eligible_mechanism")]
    # 2022-2025 only
    eligible=[x for x in eligible if x.get("start_utc") and START_YEAR<=parse_dt(x["start_utc"]).year<=END_YEAR]
    # Deduplicate by incident id.
    eligible={x["incident_id"]:x for x in eligible}.values()
    eligible=list(eligible)

    for x in eligible:
        x["product_metadata"]=product_metadata(x["symbol"])
        x["coverage_probe"]=coverage_probe(x["symbol"],x["resolved_utc"] or x["start_utc"])
        cbn=x["coverage_probe"].get("coinbase_candle_rows",{}).get("count") or 0
        bnn=x["coverage_probe"].get("binance_kline_rows",{}).get("count") or 0
        x["market_data_capability_pass"]=cbn>0 and bnn>0

    full=[x for x in eligible if x.get("market_data_capability_pass")]
    by_asset={}
    for x in full: by_asset[x["symbol"]]=by_asset.get(x["symbol"],0)+1
    n=len(full)
    concentration=max(by_asset.values())/n if n else 1.0
    gate_pass=(n>=12 and len(by_asset)>=4 and concentration<=0.40)
    complete_archive=saw_pre2022

    if gate_pass:
        verdict="SOURCE_GATE_PASS"
    elif complete_archive:
        verdict="INSUFFICIENT_SAMPLE"
    else:
        verdict="SOURCE_BLOCKED"

    report={
      "family":"CEX-TRANSFER-RAIL-RECOVERY-BASIS-001",
      "outcome_access":"NONE",
      "calendar":"2022-2025; 2026 CLOSED",
      "history_pages":pages,
      "archive_reached_pre2022":complete_archive,
      "unique_incident_links":len(incidents),
      "transfer_like_incidents_inspected":len(inspected),
      "mechanism_eligible":len(eligible),
      "fully_source_and_market_capability_eligible":n,
      "unique_assets":len(by_asset),
      "asset_counts":by_asset,
      "max_asset_concentration":concentration,
      "gate_pass":gate_pass,
      "verdict":verdict,
      "eligible_events":full,
      "rejected_events":[x for x in inspected if not x.get("eligible_mechanism")],
      "safety":{"prices_logged":False,"ohlcv_logged":False,"volumes_logged":False,"basis_logged":False}
    }
    with open("ctrrb_v01_source_gate_report.json","w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True)
    print("CTRRB_SOURCE_GATE_RESULT="+verdict)
    print("unique_incident_links="+str(len(incidents)))
    print("mechanism_eligible="+str(len(eligible)))
    print("fully_eligible="+str(n))
    print("unique_assets="+str(len(by_asset)))
    print("max_asset_concentration="+str(concentration))
    print("archive_reached_pre2022="+str(complete_archive))
    print("SAFETY: no OHLC/price/volume/basis values logged or stored")
    # Do not fail workflow for scientific negative verdict.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
