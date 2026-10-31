#!/usr/bin/env python3
"""BTC10M HISTORICAL FLOW: preregistered fixed 2024/2025 Binance public 1m kline source.
READ ONLY, NOT the original OKX/MEXC order-book hypothesis, NEVER trading or private API.
"""
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import random
import re
import statistics
import urllib.request
import zipfile
from collections import defaultdict
from datetime import timezone

ROOT=pathlib.Path("artifacts/btc10m_historical_flow_v01")
RAW=ROOT/"official_zip"
MONTHS=[f"{year}-{month:02d}" for year in (2024,2025) for month in (1,3,5,7,9,11)]
MARKETS=("spot","um")
SYMBOL="BTCUSDT"
BASE="https://data.binance.vision/data"
ZIP_MAX=15_000_000
TIMEOUT=22
BOOT_SEED=20261031
BOOT_DRAWS=2000
SCHEMES={"FLOW55":(.55,.45),"FLOW60":(.60,.40)}
SHA_RE=re.compile(r"^[a-f0-9]{64}$")
PRICE_TIE_EPS=0.0
def utc():return dt.datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(b):return hashlib.sha256(b).hexdigest()
class GateError(Exception):pass
def url_for(market,month):
    prefix=("spot" if market=="spot" else "futures/um")
    return f"{BASE}/{prefix}/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{month}.zip"
def get(url,limit):
    request=urllib.request.Request(url,method="GET",headers={
        "User-Agent":"CryptoLab-Historic-Flow-ReadOnly/1.0","Accept":"application/zip,text/plain,*/*"})
    try:
        with urllib.request.urlopen(request,timeout=TIMEOUT) as resp:
            if resp.status!=200:raise GateError("HTTP_NOT_200")
            body=resp.read(limit+1)
    except Exception as exc:
        raise GateError("OFFICIAL_ARCHIVE_REQUEST_FAILED_"+type(exc).__name__+"_"+url[-70:]) from exc
    if not body or len(body)>limit:raise GateError("ARCHIVE_FILE_EMPTY_OR_TOO_LARGE")
    return body
def one_source(market,month):
    url=url_for(market,month)
    z=get(url,ZIP_MAX)
    c=get(url+".CHECKSUM",2000)
    checksum_line=c.decode("ascii",errors="strict").strip()
    if not SHA_RE.fullmatch(checksum_line[:64].lower()):
        raise GateError("OFFICIAL_CHECKSUM_NOT_HEX")
    expected=checksum_line[:64].lower()
    if sha(z)!=expected:raise GateError("OFFICIAL_SHA256_MISMATCH")
    if not zipfile.is_zipfile(io.BytesIO(z)):raise GateError("ZIP_INVALID")
    out=f"{market}_{month}.zip"
    (RAW/out).write_bytes(z)
    (RAW/(out+".CHECKSUM")).write_bytes(c)
    return (market,month),{"venue":market,"month":month,
        "official_zip_url":url,"official_checksum_url":url+".CHECKSUM",
        "archive_zip_sha256":sha(z),"verified_official_checksum":expected,
        "bytes_zip":len(z),"zip_file":out,"observed_at_utc":utc()}
def normalized_ts(raw):
    v=int(raw)
    if 10**15<=v<10**17 and v%1000==0:
        return v//1000
    if 10**12<=v<10**14:return v
    if 10**15<=v<10**17:raise GateError("MICROSECOND_TIMESTAMP_NOT_ALIGNED_TO_MILLISECOND")
    raise GateError("TIMESTAMP_SCALE_UNRECOGNIZED")
def parse_month(market,month,manifest):
    src=RAW/manifest["zip_file"]
    raw=src.read_bytes()
    if sha(raw)!=manifest["verified_official_checksum"]:
        raise GateError("ARCHIVED_SOURCE_SHA_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        fns=[n for n in z.namelist() if n.endswith(".csv") and "/" not in n and not n.startswith("__MACOSX")]
        if len(fns)!=1:raise GateError("ARCHIVE_CSV_MEMBERS_NOT_ONE")
        with z.open(fns[0]) as stream:
            text_stream=io.TextIOWrapper(stream,encoding="utf-8-sig",newline="")
            rows=csv.reader(text_stream)
            month_start=dt.datetime.strptime(month+"-01","%Y-%m-%d").replace(tzinfo=timezone.utc)
            if month.endswith("-12"):
                next_month=dt.datetime(month_start.year+1,1,1,tzinfo=timezone.utc)
            else:
                next_month=dt.datetime(month_start.year,month_start.month+1,1,tzinfo=timezone.utc)
            lo=int(month_start.timestamp()*1000);hi=int(next_month.timestamp()*1000)
            expected=(hi-lo)//60000
            candles={}
            headers=0
            for i,row in enumerate(rows):
                if not row:continue
                if not row[0].strip().isdigit() and i==0:
                    headers+=1;continue
                if len(row)<11:raise GateError("KLINE_SCHEMA_COLS_LT_11")
                try:
                    t=normalized_ts(row[0])
                    op=float(row[1]);quote=float(row[7]);tb=float(row[10])
                except Exception as exc:
                    raise GateError("KLINE_NUMERIC_OR_TS_ERROR") from exc
                if not(lo<=t<hi and t%60000==0):
                    raise GateError("KLINE_TIME_OUTSIDE_MONTH_OR_NOT_1MIN")
                if not(all(math.isfinite(v) for v in (op,quote,tb)) and op>0 and quote>=0
                       and tb>=0 and tb<=quote*(1+1e-9)+1e-6):
                    raise GateError("KLINE_PRICE_VOLUME_INVALID")
                if t in candles:raise GateError("KLINE_DUPLICATE_MINUTE")
                candles[t]=(op,quote,min(tb,quote))
            missing=expected-len(candles)
            if missing<0:raise GateError("KLINE_MORE_THAN_MINUTES")
            completeness=len(candles)/expected
            if completeness<0.9995:
                raise GateError(f"KLINE_MONTH_COVERAGE_BELOW_99.95PCT_{market}_{month}_{missing}")
            return candles,{"market":market,"month":month,"row_count":len(candles),
                "expected_count":expected,"missing_minutes":missing,
                "coverage":completeness,"csv_header_rows":headers,
                "first_utc":utc_from_ms(min(candles)) if candles else None,
                "last_utc":utc_from_ms(max(candles)) if candles else None}
def utc_from_ms(t):return dt.datetime.fromtimestamp(t/1000,timezone.utc).isoformat()
def payoff(side,truth,q):
    if truth=="TIE":return 0.0
    return float(q) if side==truth else -1.0
def decide(bspot,bperp,threshold):
    high,low=threshold
    if bspot>=high and bperp<=low:return "UP"
    if bspot<=low and bperp>=high:return "DOWN"
    return "ABSTAIN"
def open_price(rows,t):
    x=rows.get(t)
    return x[0] if x is not None else None
def evaluate(month,spot,perp):
    year=int(month[:4])
    dt0=dt.datetime.strptime(month+"-01","%Y-%m-%d").replace(tzinfo=timezone.utc)
    start=int(dt0.timestamp()*1000)
    nmin=(dt.datetime(year+1,1,1,tzinfo=timezone.utc)-dt0).total_seconds()/60 if dt0.month==12 else (dt.datetime(year,dt0.month+1,1,tzinfo=timezone.utc)-dt0).total_seconds()/60
    slot_end=start+int(nmin)*60000
    by_strategy=defaultdict(list)
    total_slots=0
    eligible=0
    blocked=0
    for t in range(start+600000,slot_end-600000+1,600000):
        total_slots+=1
        feat=[t-180000,t-120000,t-60000]
        # All features must be fully closed BEFORE the forward label begins.
        s=[spot.get(x) for x in feat]
        p=[perp.get(x) for x in feat]
        o=open_price(spot,t);target=open_price(spot,t+600000)
        if any(x is None for x in s+p) or o is None or target is None:
            blocked+=1;continue
        sq=sum(x[1] for x in s);pq=sum(x[1] for x in p)
        if sq<=0 or pq<=0:blocked+=1;continue
        bspot=sum(x[2] for x in s)/sq
        bperp=sum(x[2] for x in p)/pq
        if not (0<=bspot<=1 and 0<=bperp<=1):
            raise GateError("BUY_SHARE_INVALID")
        eligible+=1
        truth="UP" if target>o else "DOWN" if target<o else "TIE"
        # Conditional pure-spot momentum from available preceding 3m, not future current OHLC.
        spot_momentum="UP" if o>=s[0][0] else "DOWN"
        spot_only="UP" if bspot>=.55 else "DOWN" if bspot<=.45 else spot_momentum
        date=dt.datetime.fromtimestamp(t/1000,timezone.utc).date().isoformat()
        for strategy,threshold in SCHEMES.items():
            side=decide(bspot,bperp,threshold)
            if side!="ABSTAIN":
                by_strategy[strategy].append({"date":date,"month":month,"time_ms":t,
                    "side":side,"truth":truth,"price_t":o,"price_t_10m":target,
                    "spot_aggressive_buy_share":round(bspot,8),
                    "perp_aggressive_buy_share":round(bperp,8),
                    "signed_return_bps":(1 if side=="UP" else -1)*(target/o-1)*10000,
                    "always_up_side":"UP","spot_only_side":spot_only})
    return by_strategy,{"month":month,"potential_10m_slots":total_slots,
                        "source_feature_and_label_eligible":eligible,"missing_or_zero_slots":blocked}
def wilson_lower(wins,losses,z=1.95996398454):
    n=wins+losses
    if not n:return None
    phat=wins/n
    return (phat+z*z/(2*n)-z*math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)
def boot_lower(rows,q,key="side",versus=None,seed=BOOT_SEED):
    if not rows:return None
    days=defaultdict(list)
    for row in rows:days[row["date"]].append(row)
    days=list(days.values())
    rng=random.Random(seed+int(q*1000)+(123 if versus else 0)+(1 if key=="always_up_side" else 2 if key=="spot_only_side" else 0))
    vals=[]
    for _ in range(BOOT_DRAWS):
        total=0.;n=0
        for _ in range(len(days)):
            sample=days[rng.randrange(len(days))]
            for row in sample:
                k=payoff(row[key],row["truth"],q)
                if versus:
                    k-=payoff(row[versus],row["truth"],q)
                total+=k;n+=1
        vals.append(total/n if n else -999)
    vals.sort()
    return vals[int(0.025*BOOT_DRAWS)]
def summarize(rows):
    n=len(rows);wins=sum(r["side"]==r["truth"] for r in rows)
    ties=sum(r["truth"]=="TIE" for r in rows)
    losses=n-wins-ties
    non=n-ties
    days=len({r["date"] for r in rows if r["truth"]!="TIE"})
    months=sorted({r["month"] for r in rows})
    m_month=[]
    for m in months:
        mrows=[r for r in rows if r["month"]==m]
        m_month.append({"month":m,"n":len(mrows),"wins":sum(x["side"]==x["truth"] for x in mrows),
                        "win_rate_no_ties":sum(x["side"]==x["truth"] for x in mrows)/
                           max(1,sum(x["truth"]!="TIE" for x in mrows)),
                        "illustrative_mean_payout_q070":sum(payoff(x["side"],x["truth"],.70) for x in mrows)/len(mrows)})
    d={"signals":n,"wins":wins,"losses":losses,"ties":ties,"non_tie_signals":non,
        "distinct_signal_days":days,"non_tie_win_rate":wins/non if non else None,
        "one_sided_bonferroni_wilson_97p5_lower":wilson_lower(wins,losses),
        "up_signals":sum(x["side"]=="UP" for x in rows),
        "down_signals":sum(x["side"]=="DOWN" for x in rows),
        "mean_signed_10m_spot_open_to_open_bps":statistics.mean(x["signed_return_bps"] for x in rows) if rows else None,
        "by_month":m_month}
    for q in (.70,.80,1.0):
        name=str(q).replace(".","p")
        d["synthetic_payoff_per_stake_q_"+name]=statistics.mean(payoff(x["side"],x["truth"],q) for x in rows) if rows else None
        d["daily_block_boot_97p5_lower_q_"+name]=boot_lower(rows,q) if rows else None
        d["always_up_same_slots_q_"+name]=statistics.mean(payoff("UP",x["truth"],q) for x in rows) if rows else None
        d["spot_only_same_slots_q_"+name]=statistics.mean(payoff(x["spot_only_side"],x["truth"],q) for x in rows) if rows else None
        d["daily_block_boot_97p5_lower_vs_always_up_q_"+name]=boot_lower(rows,q,versus="always_up_side") if rows else None
        d["daily_block_boot_97p5_lower_vs_spot_only_q_"+name]=boot_lower(rows,q,versus="spot_only_side") if rows else None
    d["positive_2025_months_q070"]=sum(x["illustrative_mean_payout_q070"]>0 for x in m_month) if rows else 0
    return d
def tests():
    assert decide(.56,.44,SCHEMES["FLOW55"])=="UP"
    assert decide(.44,.56,SCHEMES["FLOW55"])=="DOWN"
    assert decide(.52,.48,SCHEMES["FLOW55"])=="ABSTAIN"
    assert decide(.59,.41,SCHEMES["FLOW60"])=="ABSTAIN"
    assert payoff("UP","DOWN",.7)==-1 and payoff("UP","UP",.7)==.7 and payoff("UP","TIE",.7)==0
    assert normalized_ts("1704067200000")==1704067200000
    assert normalized_ts("1735689600000000")==1735689600000
    assert wilson_lower(70,30)<.7
    fake=[{"date":"2024-01-01","month":"2024-01","side":"UP","truth":"UP",
        "signed_return_bps":10.0,"spot_only_side":"UP"} for _ in range(10)]
    d=summarize(fake)
    assert d["wins"]==10 and d["losses"]==0
    assert abs(d["synthetic_payoff_per_stake_q_0p7"]-.7)<1e-9
def main():
    ROOT.mkdir(parents=True,exist_ok=True);RAW.mkdir(parents=True,exist_ok=True)
    receipt={"study":"BTC10M_HISTORICAL_EXECUTED_FLOW_DIVERGENCE_V01",
        "started_utc":utc(),"status":"SOURCE_BLOCKED_FAIL_CLOSED",
        "preoutcome_freeze":"research/btc10m_historical_flow/BTC10M_HISTORICAL_EXECUTED_FLOW_PREOUTCOME_FREEZE_2026_10_31.md",
        "proxy_not_original_L2_OKX_MEXC":True,"data_provider":"Binance official vision spot+USDT-M",
        "months":MONTHS,"archive_manifest":[],"quality_by_source":[],"quality_by_month":[],
        "actual_trades":0,"private_account_calls":0,"wallet":False,"main_merge":False,
        "event_futures_actual_payout_parity_proven":False,
        "event_futures_actual_winrate_claimed":False}
    try:
        tests()
        expected={(market,month) for month in MONTHS for market in MARKETS}
        manifest={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            fs={executor.submit(one_source,market,month):(market,month)
                for market,month in sorted(expected)}
            errors=[]
            for f in concurrent.futures.as_completed(fs):
                pair=fs[f]
                try:
                    key,record=f.result()
                    manifest[key]=record
                    receipt["archive_manifest"].append(record)
                    print("SOURCE_PASS",key,record["bytes_zip"],flush=True)
                except Exception as exc:
                    errors.append((pair,type(exc).__name__,str(exc)[:180]))
            if errors:raise GateError("DOWNLOAD_OR_CHECKSUM_ERRORS_"+json.dumps(errors)[:950])
        if set(manifest)!=expected:raise GateError("INCOMPLETE_ARCHIVE_PAIR_SET")
        receipt["archive_manifest"].sort(key=lambda x:(x["month"],x["venue"]))
        recs={"2024":defaultdict(list),"2025":defaultdict(list)}
        for month in MONTHS:
            s,qa=parse_month("spot",month,manifest[("spot",month)])
            p,qb=parse_month("um",month,manifest[("um",month)])
            receipt["quality_by_source"].extend([qa,qb])
            rows,quality=evaluate(month,s,p)
            receipt["quality_by_month"].append(quality)
            for name,items in rows.items():
                recs[month[:4]][name].extend(items)
            print("EVALUATED",month,quality,"qualified", {x:len(y) for x,y in rows.items()},flush=True)
        report={"years":{}}
        for year in ("2024","2025"):
            total=sum(x["source_feature_and_label_eligible"] for x in receipt["quality_by_month"] if x["month"].startswith(year))
            report["years"][year]={"evaluable_10m_slots":total}
            for name in SCHEMES:
                report["years"][year][name]=summarize(recs[year].get(name,[]))
                report["years"][year][name]["coverage_fraction"]=len(recs[year].get(name,[]))/total if total else None
        receipt["year_economic_and_science_metrics"]=report
        oos=report["years"]["2025"]
        primary=oos["FLOW55"]
        n=primary["non_tie_signals"]
        days=primary["distinct_signal_days"]
        boot=primary["daily_block_boot_97p5_lower_q_0p7"]
        a=primary["daily_block_boot_97p5_lower_vs_always_up_q_0p7"]
        b=primary["daily_block_boot_97p5_lower_vs_spot_only_q_0p7"]
        if n<300 or days<20:
            verdict="INSUFFICIENT_HISTORICAL_SIGNAL_FREQUENCY"
        elif boot is None or boot<=0:
            verdict="NO_HISTORICAL_PAYOUT_EDGE_WITH_DAY_CLUSTER_UNCERTAINTY"
        elif a is None or b is None or a<=0 or b<=0:
            verdict="NO_INCREMENTAL_EDGE_OVER_BASELINES"
        elif primary["positive_2025_months_q070"]<4 or primary["mean_signed_10m_spot_open_to_open_bps"]<=0:
            verdict="FAILED_REGIME_CONSISTENCY_OR_SIGNED_RETURN"
        else:
            verdict="HISTORICAL_PROXY_CANDIDATE_SURVIVES_ONLY_NOT_MEXC_PARITY"
        receipt["primary_FLOW55_2025_OOS_verdict"]=verdict
        receipt["secondary_FLOW60_2025_OOS_eligible_for_promotion"]=False
        receipt["status"]="HISTORICAL_SOURCE_AND_EXECUTION_COMPLETE"
        receipt["economic_edge_certified"]=False
        receipt["manual_trading_GO"]=False
        receipt["archived_original_1m_sources"]=len(manifest)
        for year in ("2024","2025"):
            for name in SCHEMES:
                out=ROOT/f"{year}_{name.lower()}_signal_events.jsonl"
                with out.open("w",encoding="utf8") as f:
                    for row in recs[year].get(name,[]):
                        f.write(json.dumps(row,separators=(",",":"))+"\n")
    except Exception as exc:
        receipt["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        receipt["blocked_reason"]=type(exc).__name__+":"+str(exc)[:1450]
    finally:
        receipt["finished_utc"]=utc()
        (ROOT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
        excerpt={k:receipt.get(k) for k in
            ("study","status","blocked_reason","archived_original_1m_sources",
             "primary_FLOW55_2025_OOS_verdict","economic_edge_certified")}
        excerpt["year_metrics"]=receipt.get("year_economic_and_science_metrics")
        print("FINAL_RECEIPT",json.dumps(excerpt,sort_keys=True),flush=True)
    if receipt["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":
    main()
