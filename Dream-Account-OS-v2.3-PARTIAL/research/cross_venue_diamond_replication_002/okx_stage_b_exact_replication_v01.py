#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, importlib, io, json, math, random, statistics, sys, tempfile, time, urllib.parse, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "cross_venue_diamond_replication_002_okx_stage_b"
OUT.mkdir(parents=True, exist_ok=True)

V03_ZIP = ROOT / "research" / "ced_1d_v3" / "recovered_authority" / "CED-1D-V1-RUNNER-FREEZE-V0.3.zip"
V03_ZIP_SHA = "df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958"
HYPOTHESES_SHA = "dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693"

INST = "AVAX-USDT-SWAP"
CFG = {"family":"A_MOMENTUM","symbol":"AVAXUSDT","lookback":20,"horizon":1,"direction":"CONTINUATION"}
FIRST_SIGNAL_WEEK = date(2025,1,6)
END_SIGNAL_WEEK_EXCLUSIVE = date(2025,12,29)
BASE_COST = 14.0
STRESS_COST = 20.0
BOOT_REPS = 9999
BOOT_SEED = 20260908
BULK = "https://www.okx.com/api/v5/public/market-data-history"
MARK = "https://www.okx.com/api/v5/market/history-mark-price-candles"
UA = "CROSS-VENUE-DIAMOND-REPLICATION-002 stage-b/1.0"

EXPECTED = {
"AVAX-USDT-SWAP-candlesticks-2024-09.zip":"852832a46fe08af78c1f6dd0e333d9c2d077bf67770b9ab155db55bc940060c8",
"AVAX-USDT-SWAP-candlesticks-2024-10.zip":"662d1b898707dfa67348eedc875f4a19ae10907251e33662e03de747c4749441",
"AVAX-USDT-SWAP-candlesticks-2024-11.zip":"48967ba96c70bc859bdb7a307511e6c5ed2650930780834ef534db575f96ff02",
"AVAX-USDT-SWAP-candlesticks-2024-12.zip":"7e1c4c29c3be09b517732a70058321fb06bc4d3d7b40612336daa598f747cdfa",
"AVAX-USDT-SWAP-candlesticks-2025-01.zip":"3990132d74c9bfc34ab908974c934dd1ebe70e6fc51592d9c209c9aec4165803",
"AVAX-USDT-SWAP-candlesticks-2025-02.zip":"efb25ed5cb34a7059710fbd548af71524cde908dea04ffd295e417126a47a861",
"AVAX-USDT-SWAP-candlesticks-2025-03.zip":"55d2bdab7571e4147e59530a9629b5a87973f4b4a1135c0fc27c807349707801",
"AVAX-USDT-SWAP-candlesticks-2025-04.zip":"a5841c1a082371aeb250637bcf420f0cc71df9b141f992a3205c980b42a333a4",
"AVAX-USDT-SWAP-candlesticks-2025-05.zip":"18ab0a2c5c6b101c21b4f4d2fe5bf4ff38076c3fc23fb5f254d7214a07755388",
"AVAX-USDT-SWAP-candlesticks-2025-06.zip":"9af1cf29912fad01b724ad7fb9deb868fd5a26d2acb1ef0d9012e86ded61d86d",
"AVAX-USDT-SWAP-candlesticks-2025-07.zip":"5912ea4cc112dd70d4b48a4d12175b207d25d6bdece7eb2f371ad22e66ec5763",
"AVAX-USDT-SWAP-candlesticks-2025-08.zip":"22a230cfbe9bf114214465b52378d1a887324c1c2783fa411e7d6837e67c2ff7",
"AVAX-USDT-SWAP-candlesticks-2025-09.zip":"cd4a2211545f53a948a7bb36891f850681160d00b9779556313ed11d3b534007",
"AVAX-USDT-SWAP-candlesticks-2025-10.zip":"d98a7f3eca440dea40e52993b88245c69740e8752b6be45004b63e60dd91b0c9",
"AVAX-USDT-SWAP-candlesticks-2025-11.zip":"3d2a71100ddbd98999b21fc16adf3b25f412aa4e6a083acdb69d4618cedfeec7",
"AVAX-USDT-SWAP-candlesticks-2025-12.zip":"ec1307d6da8e89a64bed52afd2dd11f267f7c0bc7c496f26dafd5bf6f9ae504d",
"AVAX-USDT-SWAP-fundingrates-2025-01.zip":"35fc508327f5f3c7b9ea183818760ac88037dd51b1f13ced2ef1165c36b8b35a",
"AVAX-USDT-SWAP-fundingrates-2025-02.zip":"eeeae487ea582a7df2fa9a3b56af54a4e1112373dbde8d4312745b50659863cd",
"AVAX-USDT-SWAP-fundingrates-2025-03.zip":"d0ed20c4dafd574f9efaefaaca573cc522366b0f82e37b03d8617eb37a653965",
"AVAX-USDT-SWAP-fundingrates-2025-04.zip":"70090acdbfbeae896e90d563978f09d7e6f46b3a583b6082a77eb175608b14c8",
"AVAX-USDT-SWAP-fundingrates-2025-05.zip":"cdc55b91bf1aa9b006a57d6383f77f999f33d993f35923162246dcabfaced574",
"AVAX-USDT-SWAP-fundingrates-2025-06.zip":"3790373ab15545680caefeafc569c609eff8a6ebeaf2d6f42d732ba0c33bd4d4",
"AVAX-USDT-SWAP-fundingrates-2025-07.zip":"945e7d31890f0b9c88425bc3c3d4fb8fc041791c31d266800734ff039e6f73f7",
"AVAX-USDT-SWAP-fundingrates-2025-08.zip":"58a63d1dada5e376230637b472f3382e707498b30bf1c86318b8e35333726a78",
"AVAX-USDT-SWAP-fundingrates-2025-09.zip":"dcd3d8b94107fccf383be6049d08e95c5c8888ff79c3170335df06923b99ef6c",
"AVAX-USDT-SWAP-fundingrates-2025-10.zip":"141fba097acd8abb8429e4922672798ad66faa761cbddb27f491591dc0eb70b5",
"AVAX-USDT-SWAP-fundingrates-2025-11.zip":"698bc240cdf0dc8ab83b82201478fc062ef91dbe3fe9df7cb076e0f60c221d23",
"AVAX-USDT-SWAP-fundingrates-2025-12.zip":"0be2b2e309a03325a7f10ed376d920f5e9c4d5fa1e70ad691962259114e80341"
}

SEGMENTS = {
2:[("2024-09-01T00:00:00Z","2025-06-01T00:00:00Z"),("2025-07-01T00:00:00Z","2025-12-01T00:00:00Z")],
3:[("2025-01-01T00:00:00Z","2025-10-01T00:00:00Z"),("2025-11-01T00:00:00Z","2025-12-01T00:00:00Z")]
}

def ms(x:str)->int:
    return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def sha_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def week_start(d:date)->date:
    return d-timedelta(days=d.weekday())

def complete_signal_week(d:date)->bool:
    return FIRST_SIGNAL_WEEK<=week_start(d)<END_SIGNAL_WEEK_EXCLUSIVE

def pct(vals,p):
    a=sorted(vals)
    if not a:return None
    pos=(len(a)-1)*p; lo=math.floor(pos); hi=math.ceil(pos)
    return a[lo]+(a[hi]-a[lo])*(pos-lo)

def request_json(base,params,timeout=30):
    req=urllib.request.Request(base+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def bulk_refs(module,beg,end):
    body=request_json(BULK,{"module":str(module),"instType":"SWAP","dateAggrType":"monthly","begin":ms(beg),"end":ms(end),"instFamilyList":"AVAX-USDT"})
    if body.get("code")!="0": raise RuntimeError(f"BULK_PROVIDER:{body.get('code')}:{body.get('msg')}")
    out=[]
    for d in body.get("data") or []:
        for detail in d.get("details") or []:
            for g in detail.get("groupDetails") or []:
                if g.get("filename") and g.get("url"): out.append((Path(g["filename"]).name,g["url"]))
    return out

def download(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=120) as r:
        return r.read()

def acquire_frozen_sources():
    got={}
    for module in (2,3):
        for beg,end in SEGMENTS[module]:
            for name,url in bulk_refs(module,beg,end):
                if name not in EXPECTED: continue
                b=download(url); digest=sha_bytes(b)
                if digest!=EXPECTED[name]: raise RuntimeError(f"SOURCE_SHA_MISMATCH:{name}:{digest}")
                if name in got and sha_bytes(got[name])!=digest: raise RuntimeError(f"SOURCE_CONFLICT:{name}")
                got[name]=b
            time.sleep(.5)
    missing=sorted(set(EXPECTED)-set(got))
    if missing: raise RuntimeError(f"SOURCE_MISSING:{missing}")
    return got

def load_hypotheses():
    if sha_file(V03_ZIP)!=V03_ZIP_SHA: raise RuntimeError("V03_ZIP_SHA_MISMATCH")
    td=tempfile.TemporaryDirectory()
    z=zipfile.ZipFile(V03_ZIP)
    if z.testzip() is not None: raise RuntimeError("V03_ZIP_CRC_FAIL")
    member="CED_1D_V1_RUNNER_FREEZE_V0.3/ced1d/hypotheses.py"
    if hashlib.sha256(z.read(member)).hexdigest()!=HYPOTHESES_SHA: raise RuntimeError("HYPOTHESES_SHA_MISMATCH")
    z.extractall(td.name)
    root=Path(td.name)/"CED_1D_V1_RUNNER_FREEZE_V0.3"
    sys.path.insert(0,str(root))
    return importlib.import_module("ced1d.hypotheses"),td

def parse_candles(got):
    per={}
    duplicates=0
    for name in sorted(n for n in got if "candlesticks" in n):
        with zipfile.ZipFile(io.BytesIO(got[name])) as z:
            members=[x for x in z.namelist() if x.lower().endswith(".csv")]
            if len(members)!=1: raise RuntimeError(f"CANDLE_MEMBER_COUNT:{name}")
            rdr=csv.DictReader(io.TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",newline=""))
            for row in rdr:
                ts=int(row["open_time"])
                if ts>=ms("2026-01-01T00:00:00Z"): raise RuntimeError("HARD_BLOCK_2026_PRICE")
                o,h,l,c=map(float,(row["open"],row["high"],row["low"],row["close"]))
                dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); day=dt.date().isoformat(); minute=dt.hour*60+dt.minute
                d=per.get(day)
                if d is None:
                    d={"date":day,"open":o,"high":h,"low":l,"close":c,"first_ts":ts,"last_ts":ts,"minutes_seen":set(),"duplicates":0,"open_0001":None}
                    per[day]=d
                if minute in d["minutes_seen"]: d["duplicates"]+=1; duplicates+=1
                else: d["minutes_seen"].add(minute)
                if ts<d["first_ts"]: d["first_ts"]=ts; d["open"]=o
                if ts>=d["last_ts"]: d["last_ts"]=ts; d["close"]=c
                d["high"]=max(d["high"],h); d["low"]=min(d["low"],l)
                if minute==1: d["open_0001"]=o
    arr=[]
    for day in sorted(per):
        d=per[day]
        item={k:v for k,v in d.items() if k!="minutes_seen"}
        item["minutes"]=len(d["minutes_seen"])
        item["valid_day"]=item["minutes"]==1440 and d["duplicates"]==0 and d["open_0001"] is not None
        arr.append(item)
    return arr,duplicates

def parse_funding(got):
    out={}
    for name in sorted(n for n in got if "fundingrates" in n):
        with zipfile.ZipFile(io.BytesIO(got[name])) as z:
            members=[x for x in z.namelist() if x.lower().endswith(".csv")]
            if len(members)!=1: raise RuntimeError(f"FUND_MEMBER_COUNT:{name}")
            rdr=csv.DictReader(io.TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",newline=""))
            for row in rdr:
                ft=int(row["funding_time"]); rate=float(row["funding_rate"])
                if ft>=ms("2026-01-01T00:00:00Z"): raise RuntimeError("HARD_BLOCK_2026_FUNDING")
                if ft in out and out[ft]!=rate: raise RuntimeError(f"FUNDING_CONFLICT:{ft}")
                out[ft]=rate
    return out

def generate_events(hyp,bars):
    series=hyp.Series(bars)
    cache={"daily_rets":series.completed_daily_log_returns(),"rv20":series.rv20_map()}
    active_exit=None; out=[]
    for d in series.valid_dates:
        sd=date.fromisoformat(d)
        if sd.year!=2025: continue
        direction=hyp.signal_for(series,CFG,d,cache)
        if direction is None: continue
        ex,status=series.execution(d,CFG["horizon"])
        if status!="OK":
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE"}); continue
        entry=date.fromisoformat(ex["entry_day"]); exitd=date.fromisoformat(ex["exit_day"])
        if exitd.year>=2026:
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]}); continue
        if active_exit is not None and entry<active_exit:
            out.append({"signal_day":d,"status":"OVERLAP_BLOCKED","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]}); continue
        active_exit=exitd
        out.append({"signal_day":d,"status":"TRADE","direction":direction,**ex,"signed_return":direction*ex["raw_return"]})
    return out

_mark_cache={}
_last_mark_request=0.0

def mark_bounds(ft):
    global _last_mark_request
    if ft in _mark_cache:return _mark_cache[ft]
    elapsed=time.monotonic()-_last_mark_request
    if elapsed<0.13: time.sleep(0.13-elapsed)
    body=request_json(MARK,{"instId":INST,"bar":"1m","after":str(ft+2*60_000),"limit":"10"},timeout=20)
    _last_mark_request=time.monotonic()
    if body.get("code")!="0": raise RuntimeError(f"MARK_PROVIDER:{body.get('code')}:{body.get('msg')}")
    for row in body.get("data") or []:
        if int(row[0])==ft:
            if len(row)>5 and str(row[5])!="1": raise RuntimeError(f"MARK_UNCONFIRMED:{ft}")
            lo=float(row[3]); hi=float(row[2])
            _mark_cache[ft]=(lo,hi)
            return lo,hi
    raise RuntimeError(f"MARK_EXACT_TIMESTAMP_MISSING:{ft}")

def attach_funding(event,funding):
    if event["status"]!="TRADE":return event
    entry_ts=ms(event["entry_day"]+"T00:01:00Z")
    exit_ts=ms(event["exit_day"]+"T00:01:00Z")
    ep=float(event["entry_open"]); direction=int(event["direction"])
    lo=hi=0.0; settlements=0
    try:
        for ft in sorted(t for t in funding if entry_ts<t<exit_ts):
            rate=float(funding[ft]); ml,mh=mark_bounds(ft)
            coeff=-direction*rate/ep
            a=coeff*ml*10000.0; b=coeff*mh*10000.0
            lo+=min(a,b); hi+=max(a,b); settlements+=1
    except Exception as e:
        return {**event,"source_unresolved":True,"source_error":str(e),"funding_settlements":settlements}
    gross=float(event["signed_return"])*10000.0
    return {**event,"source_unresolved":False,"gross_bps":gross,
            "funding_lower_bps":lo,"funding_upper_bps":hi,"funding_settlements":settlements,
            "base_lower_bps":gross-BASE_COST+lo,"base_upper_bps":gross-BASE_COST+hi,
            "stress_lower_bps":gross-STRESS_COST+lo,"stress_upper_bps":gross-STRESS_COST+hi}

def mean(xs):return math.fsum(xs)/len(xs) if xs else None

def path_metrics(events,base_field,stress_field):
    vals=[float(e[base_field]) for e in events]; stress=[float(e[stress_field]) for e in events]
    months=defaultdict(list); quarters=defaultdict(list); days=defaultdict(list)
    for e,v in zip(events,vals):
        d=date.fromisoformat(e["entry_day"]); months[d.strftime("%Y-%m")].append(v); quarters[f"{d.year}-Q{(d.month-1)//3+1}"].append(v); days[d.isoformat()].append(abs(v))
    gains=math.fsum(v for v in vals if v>0); losses=-math.fsum(v for v in vals if v<0)
    absvals=[abs(v) for v in vals]; total=math.fsum(absvals)
    month_share=max((math.fsum(abs(x) for x in v) for v in months.values()),default=0)/total if total else None
    day_share=max((math.fsum(v) for v in days.values()),default=0)/total if total else None
    top5=math.fsum(sorted(absvals,reverse=True)[:5])/total if total else None
    concentration=max(month_share/.30,day_share/.10,top5/.20) if total else None
    lomo=all(mean([v for e,v in zip(events,vals) if date.fromisoformat(e["entry_day"]).strftime("%Y-%m")!=m])>0 for m in months) if len(months)>1 else False
    return {"n":len(vals),"mean_base_bps":mean(vals),"mean_stress_bps":mean(stress),
            "median_base_bps":statistics.median(vals) if vals else None,
            "win_rate_base":sum(v>0 for v in vals)/len(vals) if vals else None,
            "profit_factor_base":gains/losses if losses>0 else None,
            "positive_active_months":sum(math.fsum(v)>0 for v in months.values()),
            "active_months":len(months),
            "positive_active_month_fraction":sum(math.fsum(v)>0 for v in months.values())/len(months) if months else None,
            "positive_quarters":sum(math.fsum(v)>0 for v in quarters.values()),
            "leave_one_month_out_all_positive":lomo,
            "month_abs_pnl_share":month_share,"day_abs_pnl_share":day_share,"top5_abs_pnl_share":top5,
            "concentration_ratio":concentration}

def bootstrap_ci(events,field):
    weeks=[]; w=FIRST_SIGNAL_WEEK
    while w<END_SIGNAL_WEEK_EXCLUSIVE:weeks.append(w);w+=timedelta(days=7)
    idx={w:i for i,w in enumerate(weeks)}; bins=[[] for _ in weeks]
    for e in events:
        ws=week_start(date.fromisoformat(e["signal_day"]))
        if ws not in idx: raise RuntimeError("BOOT_WEEK_OUTSIDE_FREEZE")
        bins[idx[ws]].append(float(e[field]))
    rng=random.Random(BOOT_SEED); vals=[]; n=len(weeks)
    for _ in range(BOOT_REPS):
        draw=[rng.randrange(n) for _ in range(n)]
        flat=[v for i in draw for v in bins[i]]
        if flat: vals.append(mean(flat))
    return {"repetitions":BOOT_REPS,"seed":BOOT_SEED,"ci_low":pct(vals,.025),"ci_high":pct(vals,.975),"valid_resamples":len(vals)}

def main():
    got=acquire_frozen_sources()
    bars,price_dups=parse_candles(got)
    if price_dups: raise RuntimeError(f"PRICE_DUPLICATES:{price_dups}")
    funding=parse_funding(got)
    hyp,tmp=load_hypotheses()
    try:
        raw_events=generate_events(hyp,bars)
        events=[attach_funding(e,funding) for e in raw_events]
    finally:
        tmp.cleanup()
    inference=[e for e in events if e["status"]=="TRADE" and complete_signal_week(date.fromisoformat(e["signal_day"]))]
    unresolved=[e for e in inference if e.get("source_unresolved")]
    resolved=[e for e in inference if not e.get("source_unresolved")]
    lower=path_metrics(resolved,"base_lower_bps","stress_lower_bps")
    upper=path_metrics(resolved,"base_upper_bps","stress_upper_bps")
    lower["bootstrap"]=bootstrap_ci(resolved,"base_lower_bps") if resolved else {"ci_low":None,"ci_high":None}
    upper["bootstrap"]=bootstrap_ci(resolved,"base_upper_bps") if resolved else {"ci_low":None,"ci_high":None}

    pf=lower["profit_factor_base"]
    hard=(not unresolved and lower["mean_base_bps"] is not None and lower["mean_base_bps"]>0 and pf is not None and pf>1
          and lower["mean_stress_bps"] is not None and lower["mean_stress_bps"]>0
          and lower["positive_active_month_fraction"] is not None and lower["positive_active_month_fraction"]>=.5)
    if not hard:
        label="CROSS_VENUE_FAIL"
    else:
        robust=(lower["bootstrap"].get("ci_low") is not None and lower["bootstrap"]["ci_low"]>0
                and lower["positive_active_month_fraction"]>=2/3 and lower["positive_quarters"]>=3
                and lower["leave_one_month_out_all_positive"] and lower["concentration_ratio"] is not None and lower["concentration_ratio"]<=1)
        label="CROSS_VENUE_SURVIVES" if robust else "CROSS_VENUE_FRAGILE_SURVIVAL"

    status_counts={s:sum(e["status"]==s for e in events) for s in ("TRADE","OVERLAP_BLOCKED","DATA_UNAVAILABLE")}
    receipt={
      "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002",
      "candidate":"CED1D-0031-AVAX20-CONTINUATION-H1",
      "venue":"OKX_AVAX_USDT_SWAP",
      "stage":"STAGE_B_EXACT_REPLICATION",
      "classification":label,
      "source_gate_run_id":35364301053,
      "mark_source_gate_run_id":35364619561,
      "v03_zip_sha256":V03_ZIP_SHA,
      "hypotheses_sha256":HYPOTHESES_SHA,
      "config":CFG,
      "costs":{"base_bps":BASE_COST,"stress_bps":STRESS_COST},
      "ledger_status_counts":status_counts,
      "inference_trade_count":len(inference),
      "resolved_inference_count":len(resolved),
      "source_execution_unresolved_count":len(unresolved),
      "funding_event_count_2025":len(funding),
      "mark_settlement_count_used":len(_mark_cache),
      "lower":lower,
      "upper_diagnostic_only":upper,
      "upper_cannot_rescue_lower":True,
      "source_hash_deviations":0,
      "governance":{"2026_plus_accessed":False,"post_outcome_tuning":False,"live_trading":False,"orders":False,"exchange_mutation":False,"main_merge":False}
    }
    rec_bytes=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(rec_bytes).hexdigest()
    (OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_STAGE_B_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    ledger=OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_LEDGER_V0.1.csv"
    fields=sorted({k for e in events for k in e})
    with ledger.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(events)
    print(json.dumps({
      "classification":label,
      "inference_n":len(inference),
      "resolved_n":len(resolved),
      "unresolved":len(unresolved),
      "lower_mean_base_bps":lower["mean_base_bps"],
      "lower_pf":lower["profit_factor_base"],
      "lower_mean_stress_bps":lower["mean_stress_bps"],
      "positive_months":[lower["positive_active_months"],lower["active_months"]],
      "positive_quarters":lower["positive_quarters"],
      "lomo":lower["leave_one_month_out_all_positive"],
      "bootstrap_ci_low":lower["bootstrap"].get("ci_low"),
      "concentration_ratio":lower["concentration_ratio"],
      "funding_events":len(funding),
      "mark_settlements_used":len(_mark_cache),
      "fingerprint":receipt["fingerprint"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
