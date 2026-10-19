"""Funding Hunter V04: real June-2025 source, rate-only *illustration*, NO trading PnL.

Fixed 28 daily BTC OKX inverse/linear episodes, 00:05 UTC, 02..29 June.
Never fetches 2026, no private API, no orders/keys. Historical model mark
valuation, collateral FX, contract sizes and execution are NOT established.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

CATALOGUE="https://www.okx.com/api/v5/public/market-data-history"
FAMILIES={"LINEAR":"BTC-USDT","INVERSE":"BTC-USD"}
CONTRACTS={"LINEAR":"BTC-USDT-SWAP","INVERSE":"BTC-USD-SWAP"}
MONTH="2025-06"
UTC=timezone.utc
ZERO=Decimal("0")
N=Decimal("1000")
SIGNAL_THRESHOLD_BPS_PER_HOUR=Decimal("0.5")
BASE_HURDLE_BPS=Decimal("30")
STRESS_HURDLE_BPS=Decimal("50")
MIN_INTERVALS={60,240,480}
DATE_FIRST=2
DATE_LAST=29

def millis(day):
    return str(int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=UTC).timestamp()*1000))
QUERY={"module":"3","instType":"SWAP",
       "instFamilyList":"BTC-USDT,BTC-USD","dateAggrType":"monthly",
       "begin":millis("2025-06-01"),"end":millis("2025-06-01")}
def get_json():
    req=urllib.request.Request(CATALOGUE+"?"+urllib.parse.urlencode(QUERY),
      headers={"Accept":"application/json","User-Agent":"CryptoLab-JuneFundingReadOnly/0.4"})
    with urllib.request.urlopen(req,timeout=19) as f:
        if f.status!=200 or "json" not in f.headers.get("Content-Type","").lower():
            raise ValueError("PUBLISHER_CATALOGUE_HTTP_OR_CONTENT_TYPE")
        raw=f.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError("METADATA_CAP")
    doc=json.loads(raw)
    if not isinstance(doc,dict) or str(doc.get("code"))!="0" or not isinstance(doc.get("data"),list):
        raise ValueError("CATALOGUE_CODE_OR_SCHEMA")
    return doc,hashlib.sha256(raw).hexdigest()

def archive_links(doc):
    hits={x:[] for x in CONTRACTS}
    def walk(obj,context=None,depth=0):
        if depth>10:raise ValueError("PUBLISHER_META_DEPTH")
        if isinstance(obj,list):
            for x in obj:walk(x,context,depth+1)
        elif isinstance(obj,dict):
            family=obj.get("instFamily") if isinstance(obj.get("instFamily"),str) else context
            fn=obj.get("filename");url=obj.get("url")
            if isinstance(fn,str) and isinstance(url,str) and fn.endswith(".zip"):
                if urlparse(url).scheme!="https" or urlparse(url).hostname!="static.okx.com":
                    raise ValueError("UNTRUSTED_ARCHIVE_HOST")
                for kind,contract in CONTRACTS.items():
                    matched=family==FAMILIES[kind] and MONTH in fn
                    if matched:hits[kind].append(url)
            for key,value in obj.items():
                if key not in ("filename","url"):walk(value,family,depth+1)
    walk(doc.get("data"))
    ret={}
    for kind,found in hits.items():
        unique=list(dict.fromkeys(found))
        if len(unique)!=1:raise ValueError(f"MISSING_OR_AMBIGUOUS_OFFICIAL_{kind}_ARCHIVE_{len(unique)}")
        ret[kind]=unique[0]
    return ret
def get_archive(url):
    if urlparse(url).hostname!="static.okx.com":
        raise ValueError("ARCHIVE_HOST_UNTRUSTED")
    request=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-JuneFundingReadOnly/0.4"})
    with urllib.request.urlopen(request,timeout=24) as f:
        if f.status!=200:raise ValueError("ARCHIVE_NOT_HTTP200")
        raw=f.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("COMPRESSED_ARCHIVE_TOO_LARGE")
    return raw

def utc_ms(v):
    text=str(v).strip()
    if text.isdigit():
        val=int(text)
        if 1_700_000_000_000<=val<1_800_000_000_000:return val
        if 1_700_000_000<=val<1_800_000_000:return val*1000
        raise ValueError("EPOCH_UNEXPECTED_2025")
    s=text.replace("Z","+00:00")
    dt=None
    try:dt=datetime.fromisoformat(s)
    except ValueError:pass
    if dt is None:raise ValueError("TIME_INVALID_ISO")
    if dt.tzinfo is None:dt=dt.replace(tzinfo=UTC)
    ts=int(dt.astimezone(UTC).timestamp()*1000)
    return ts

def parse_month(raw,contract):
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("NOT_OFFICIAL_ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.infolist() if not x.is_dir()]
        if len(files)!=1:raise ValueError("ZIP_MEMBER_COUNT")
        member=files[0]
        if member.file_size>500_000 or member.filename.startswith("/") or ".." in Path(member.filename).parts:
            raise ValueError("UNSAFE_MEMBER")
        contents=z.read(member)
    if len(contents)>500_000:raise ValueError("ZIP_UNCOMPRESSED_CAP")
    source=io.StringIO(contents.decode("utf-8-sig"))
    rdr=csv.DictReader(source)
    if rdr.fieldnames!=["instrument_name","funding_rate","funding_time"]:
        raise ValueError("FUNDING_COLUMNS_NOT_PUBLISHER_SCHEMA")
    rows=[]
    for row in rdr:
        if len(rows)>3000:raise ValueError("TOO_MANY_FUNDING_ROWS")
        if row.get("instrument_name")!=contract:raise ValueError("MISMATCH_INSTRUMENT")
        time=utc_ms(row["funding_time"])
        dt=datetime.fromtimestamp(time/1000,UTC)
        if not(datetime(2025,5,31,16,tzinfo=UTC)<=dt<datetime(2025,6,30,16,tzinfo=UTC)):\n            raise ValueError("OUTSIDE_FROZEN_UTC_PLUS8_ARCHIVE_MONTH:"+contract+":"+dt.isoformat())
        try:rate=Decimal(row["funding_rate"])
        except (InvalidOperation,TypeError) as e:raise ValueError("BAD_RATE_DECIMAL") from e
        if not rate.is_finite() or abs(rate)>Decimal("0.05"):
            raise ValueError("FUNDING_RATE_OUT_OF_BOUNDS")
        rows.append((time,rate))
    if not rows:raise ValueError("NO_FUNDING_ROWS")
    if any(a[0]>=b[0] for a,b in zip(rows,rows[1:])):raise ValueError("NONMONOTONIC_OR_DUPLICATE_SETTLEMENT_TIME")
    intervals=Counter()
    for first,last in zip(rows,rows[1:]):
        step=last[0]-first[0]
        if step not in (3_600_000,14_400_000,28_800_000):
            raise ValueError(f"UNEXPECTED_FUNDING_PERIOD_MIN_{step//60000}")
        intervals[step//60000]+=1
    return rows,{"rows":len(rows),
       "first_utc":datetime.fromtimestamp(rows[0][0]/1000,UTC).isoformat(),
       "last_utc":datetime.fromtimestamp(rows[-1][0]/1000,UTC).isoformat(),
       "observed_intervals_minutes":dict(intervals),
       "raw_member_sha256":hashlib.sha256(contents).hexdigest(),
       "settlement_timestamp_manifest_sha256":hashlib.sha256(
         ",".join(str(t) for t,r in rows).encode()).hexdigest()}

def prior_pair(rows,ms):
    historic=[(t,r) for t,r in rows if t<ms]
    if len(historic)<2:return None
    (pt,pr),(lt,lr)=historic[-2:]
    hours=Decimal(lt-pt)/Decimal(3600000)
    if lt>=ms or ms-lt>28_800_000 or hours not in (Decimal(1),Decimal(4),Decimal(8)):
        return None
    return lr/hours

def episode_for_day(linear,inverse,day):
    entry=int(datetime(2025,6,day,0,5,tzinfo=UTC).timestamp()*1000)
    exit_ms=entry+86400000
    lr=prior_pair(linear,entry);ir=prior_pair(inverse,entry)
    output={"entry_utc":datetime.fromtimestamp(entry/1000,UTC).isoformat(),
            "exit_utc":datetime.fromtimestamp(exit_ms/1000,UTC).isoformat()}
    if lr is None or ir is None:
        output.update(status="SOURCE_INSUFFICIENT_AT_DECISION",strategy_position="NONE")
        return output
    diff_bps_hour=(lr-ir)*Decimal(10000)
    output["pre_entry_normalized_funding_diff_bps_hour"]=str(diff_bps_hour)
    if abs(diff_bps_hour)<SIGNAL_THRESHOLD_BPS_PER_HOUR or diff_bps_hour==ZERO:
        output.update(status="FLAT_PREDECLARED_THRESHOLD",strategy_position="NONE")
        return output
    # Positive (linear - inverse) => short LINEAR, long INVERSE
    short="LINEAR" if diff_bps_hour>0 else "INVERSE"
    net=ZERO
    realized_counts={}
    reversed_events=0
    for kind,rows in (("LINEAR",linear),("INVERSE",inverse)):
        # constant 1000 quote notional placeholder, never actual cashflow
        events=[(t,r) for t,r in rows if entry<t<=exit_ms]
        if not events:output.update(status="SOURCE_INSUFFICIENT_FORWARD_SETTLEMENT",strategy_position="NONE");return output
        realized_counts[kind]=len(events)
        sign=Decimal(1) if kind==short else Decimal(-1)
        net+=sum((sign*N*r for _,r in events),ZERO)
        reversed_events+=sum(1 for _,r in events if (r<0 and sign>0) or (r>0 and sign<0))
    proxy_bps=net/N*Decimal(10000)
    output.update({"status":"RATE_ONLY_CONSTANT_NOTIONAL_PROXY",
      "strategy_position":f"SHORT_{short}_LONG_{'INVERSE' if short=='LINEAR' else 'LINEAR'}",
      "source_settlement_count":realized_counts,
      "reversal_or_negative_cashflow_settlements":reversed_events,
      "constant_notional_rate_only_proxy_USD":str(net),
      "constant_notional_rate_only_proxy_bps_per_one_leg":str(proxy_bps),
      "illustrative_after30bp_USD":str(net-N*BASE_HURDLE_BPS/Decimal(10000)),
      "illustrative_after50bp_USD":str(net-N*STRESS_HURDLE_BPS/Decimal(10000)),
      "proxy_clears_30bps":proxy_bps>BASE_HURDLE_BPS,
      "proxy_clears_50bps":proxy_bps>STRESS_HURDLE_BPS,
      "is_actual_inverse_or_linear_cashflow":False,
      "fills_exits_margin_fx_confirmed":False})
    return output

def evaluate(linear,inverse):
    days=[episode_for_day(linear,inverse,d) for d in range(DATE_FIRST,DATE_LAST+1)]
    ctr=Counter(x["status"] for x in days)
    selected=[x for x in days if x["status"]=="RATE_ONLY_CONSTANT_NOTIONAL_PROXY"]
    positive=sum(Decimal(x["constant_notional_rate_only_proxy_USD"])>0 for x in selected)
    nominal_proxy=sum((Decimal(x["constant_notional_rate_only_proxy_USD"]) for x in selected),ZERO)
    hurdle30=sum((Decimal(x["illustrative_after30bp_USD"]) for x in selected),ZERO)
    hurdle50=sum((Decimal(x["illustrative_after50bp_USD"]) for x in selected),ZERO)
    out={"study":"FUNDING_HUNTER_V04_BTC_USDT_LINEAR_VS_USD_INVERSE_JUNE_2025",
      "status":"RATE_ONLY_SCREEN_NOT_VENUE_EXECUTION",
      "original_3_asset_v01_hypothesis_replaced":False,
      "evaluation_days":28,"all_predeclared_days":days,
      "status_count":dict(ctr),"active_24h_rate_proxy_days":len(selected),
      "positive_rate_proxy_days":positive,"negative_or_zero_rate_proxy_days":len(selected)-positive,
      "illustrative_total_rate_only_proxy_USD":str(nominal_proxy),
      "illustrative_total_after30bps_each_active_day_USD":str(hurdle30),
      "illustrative_total_after50bps_each_active_day_USD":str(hurdle50),
      "days_proxy_clears_30bps":sum(x["proxy_clears_30bps"] for x in selected),
      "days_proxy_clears_50bps":sum(x["proxy_clears_50bps"] for x in selected),
      "historical_real_broker_economic_PNL_calculated":False,
      "protected_2026_opened":False,"trading_authority":"NONE"}
    return out

def run():
    doc,meta_hash=get_json()
    urls=archive_links(doc)
    records={};metadata={}
    for kind,contract in CONTRACTS.items():
        raw=get_archive(urls[kind])
        records[kind],receipts=parse_month(raw,contract)
        metadata[kind]={"archive_local_SHA256":hashlib.sha256(raw).hexdigest(),
           "archive_bytes":len(raw),**receipts}
    result=evaluate(records["LINEAR"],records["INVERSE"])
    result["source_catalogue_SHA256"]=meta_hash
    result["archive_source_receipts"]=metadata
    result["funding_outcomes_opened"]=True
    result["source_notice"]="Funding rates are actual archive rows. Not actual received payouts or executable PnL."
    result["scientific_verdict"]="ECONOMIC_EDGE_UNPROVEN_NO_LIVE_GO"
    return result

def main():
    try:result=run()
    except Exception as exc:
        result={"status":"SOURCE_BLOCKED_FAIL_CLOSED",
                "reason":type(exc).__name__+":"+str(exc)[:180],
                "actual_source_payouts_calculated":False,
                "scientific_verdict":"ECONOMIC_EDGE_UNPROVEN",
                "protected_2026_opened":False,"trading_authority":"NONE"}
    output=Path("research/funding_hunter_v04/receipts/V04_JUNE_BTC_TWO_REAL_FUNDING_ARCHIVES_RATE_ONLY.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    compact={key:result.get(key) for key in (
      "status","reason","status_count","active_24h_rate_proxy_days",
      "positive_rate_proxy_days","illustrative_total_rate_only_proxy_USD",
      "illustrative_total_after30bps_each_active_day_USD",
      "illustrative_total_after50bps_each_active_day_USD",
      "days_proxy_clears_30bps","days_proxy_clears_50bps",
      "scientific_verdict") if key in result}
    print("V04_REAL_FUNDING_RATE_SCREEN",json.dumps(compact,sort_keys=True))
    if result["status"].startswith("SOURCE_BLOCKED"):raise SystemExit(2)

if __name__=="__main__":main()
