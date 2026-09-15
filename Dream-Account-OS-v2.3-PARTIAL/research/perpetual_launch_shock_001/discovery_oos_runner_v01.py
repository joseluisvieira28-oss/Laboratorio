import csv, hashlib, io, json, math, random, statistics, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "FINAL_PRE_DISCOVERY_PROTOCOL_V01.json"
SOURCE_PATH = HERE / "source_evidence" / "PLS_SOURCE_DATA_GATE_V01.json"
OUTDIR = HERE / "discovery_evidence"
OUT = OUTDIR / "PLS_DISCOVERY_OOS_RESULT_V01.json"
DATA_BASE = "https://data.binance.vision"
UA = {"User-Agent": "Mozilla/5.0 PERPETUAL-LAUNCH-SHOCK-001-DISCOVERY/1.0"}

GUARDS = {
    "research_only": True, "live_trading": False, "exchange_mutation": False,
    "orders": False, "alerts_or_webhooks": False, "merge_to_main": False,
    "render_deployment": False, "year_2025_archive_requested": False,
    "year_2026_archive_requested": False, "year_2025_market_values_opened": False,
    "year_2026_market_values_opened": False, "mve_a_2023_market_values_opened": False,
    "mve_b_2024_market_values_opened": False, "directional_return_search_in_mve_a": False,
    "post_outcome_tuning": False,
}
CACHE = {}
MANIFEST = {}

def get(url, attempts=4):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(0.5 * (2 ** i))
    raise last

def parse_ts(raw):
    x = int(float(raw))
    if x > 10**14: sec = x / 1_000_000.0
    elif x > 10**11: sec = x / 1_000.0
    else: sec = float(x)
    return datetime.fromtimestamp(sec, tz=timezone.utc)

def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def qualified_events(source):
    found = []
    def walk(x):
        if isinstance(x, dict):
            if x.get("kind") == "qualified" and "symbol" in x and "event_timestamp_utc" in x:
                found.append({"symbol": str(x["symbol"]), "event_timestamp_utc": str(x["event_timestamp_utc"])})
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(source)
    uniq = {(e["symbol"], e["event_timestamp_utc"]): e for e in found}
    return sorted(uniq.values(), key=lambda z: (z["event_timestamp_utc"], z["symbol"]))

def days_between(start, end):
    d = start.date(); out = []
    while d <= end.date():
        if d.year >= 2025: raise RuntimeError("protected-period day generation attempted")
        out.append(d.isoformat()); d += timedelta(days=1)
    return out

def archive_url(venue, symbol, day):
    if day.startswith("2025-") or day.startswith("2026-"):
        raise RuntimeError("protected-period archive URL attempted")
    root = "data/spot/daily/klines" if venue == "spot" else "data/futures/um/daily/klines"
    return f"{DATA_BASE}/{root}/{symbol}/1m/{symbol}-1m-{day}.zip"

def load_day(venue, symbol, day):
    key = (venue, symbol, day)
    if key in CACHE: return CACHE[key]
    url = archive_url(venue, symbol, day)
    zb = get(url); cb = get(url + ".CHECKSUM").decode("utf-8", "replace").strip().split()
    if not cb: raise RuntimeError(f"empty checksum {venue} {symbol} {day}")
    official = cb[0].lower(); actual = hashlib.sha256(zb).hexdigest().lower()
    if len(official) != 64 or official != actual: raise RuntimeError(f"checksum mismatch {venue} {symbol} {day}")
    rows = []
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        if len(names) != 1: raise RuntimeError(f"unexpected member count {venue} {symbol} {day}")
        raw = z.read(names[0]).decode("utf-8-sig", "replace")
    for row in csv.reader(io.StringIO(raw)):
        if not row: continue
        try: ts = parse_ts(row[0])
        except Exception:
            if str(row[0]).strip().lower() in {"open_time", "opentime"}: continue
            raise
        if len(row) < 8: raise RuntimeError(f"short kline row {venue} {symbol} {day}")
        o,h,l,c,qv = [float(row[i]) for i in (1,2,3,4,7)]
        if not all(math.isfinite(v) for v in (o,h,l,c,qv)) or min(o,h,l,c) <= 0 or qv < 0 or h < l:
            raise RuntimeError(f"invalid kline value {venue} {symbol} {day}")
        rows.append({"ts":ts,"open":o,"high":h,"low":l,"close":c,"qv":qv})
    rows.sort(key=lambda r:r["ts"]); CACHE[key] = rows
    MANIFEST[key] = {"venue":venue,"symbol":symbol,"day":day,"sha256":actual,"row_count":len(rows)}
    return rows

def load_interval(venue, symbol, start, end):
    rows = []
    for day in days_between(start, end): rows.extend(load_day(venue, symbol, day))
    return [r for r in rows if start <= r["ts"] < end]

def contiguous(rows, start, count):
    return len(rows) == count and all(r["ts"] == start + timedelta(minutes=i) for i,r in enumerate(rows))

def realized_variance(rows):
    return sum(math.log(b["close"]/a["close"])**2 for a,b in zip(rows, rows[1:])) if len(rows) >= 2 else None

def cluster_bootstrap_mean(values, clusters, reps, seed):
    groups = defaultdict(list)
    for v,c in zip(values,clusters): groups[c].append(v)
    keys = sorted(groups); rng = random.Random(seed); means = []
    if not keys: raise RuntimeError("no clusters")
    for _ in range(reps):
        arr = []
        for k in [rng.choice(keys) for _ in keys]: arr.extend(groups[k])
        means.append(sum(arr)/len(arr))
    means.sort(); n = len(means)
    return {"replications":reps,"seed":seed,"cluster_count":len(keys),
            "ci95_lower":means[max(0,int(math.floor(.025*n)))],
            "ci95_upper":means[min(n-1,int(math.ceil(.975*n))-1)],
            "median_bootstrap_mean":statistics.median(means)}

def run_mve_a(events, p):
    GUARDS["mve_a_2023_market_values_opened"] = True
    rows=[]; exclusions=[]
    for e in [x for x in events if iso(x["event_timestamp_utc"]).year == 2023]:
        sym=e["symbol"]; t0=iso(e["event_timestamp_utc"]); pre0=t0-timedelta(minutes=p["pre_window_minutes"]); post1=t0+timedelta(minutes=p["post_window_minutes"])
        try:
            tok=load_interval("spot",sym,pre0,post1); btc=load_interval("spot","BTCUSDT",pre0,post1)
            tok_pre=[r for r in tok if pre0<=r["ts"]<t0]; tok_post=[r for r in tok if t0<=r["ts"]<post1]
            btc_pre=[r for r in btc if pre0<=r["ts"]<t0]; btc_post=[r for r in btc if t0<=r["ts"]<post1]
            if not (contiguous(tok_pre,pre0,p["pre_window_minutes"]) and contiguous(tok_post,t0,p["post_window_minutes"]) and contiguous(btc_pre,pre0,p["pre_window_minutes"]) and contiguous(btc_post,t0,p["post_window_minutes"])):
                exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"INCOMPLETE_OR_NONCONTIGUOUS_1M_WINDOW"}); continue
            tr0,tr1,br0,br1=realized_variance(tok_pre),realized_variance(tok_post),realized_variance(btc_pre),realized_variance(btc_post)
            tq0,tq1,bq0,bq1=sum(r["qv"] for r in tok_pre),sum(r["qv"] for r in tok_post),sum(r["qv"] for r in btc_pre),sum(r["qv"] for r in btc_post)
            if min(tr0,tr1,br0,br1,tq0,tq1,bq0,bq1)<=0:
                exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"NONPOSITIVE_RV_OR_VOLUME"}); continue
            rows.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"launch_date_utc":t0.date().isoformat(),
                         "excess_log_rv_ratio":math.log(tr1/tr0)-math.log(br1/br0),
                         "excess_log_quote_volume_ratio":math.log(tq1/tq0)-math.log(bq1/bq0)})
        except Exception as ex:
            exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"DATA_UNAVAILABLE_OR_INVALID","detail":f"{type(ex).__name__}: {ex}"})
    req=p["promotion_gate"]["minimum_eligible_events"]
    if len(rows)<req:
        return {"classification":"INSUFFICIENT_DISCOVERY_SAMPLE","eligible_events":len(rows),"required_eligible_events":req,"event_results":rows,"exclusions":exclusions,"all_promotion_conditions_pass":False}
    rv=[r["excess_log_rv_ratio"] for r in rows]; qv=[r["excess_log_quote_volume_ratio"] for r in rows]; cl=[r["launch_date_utc"] for r in rows]
    brv=cluster_bootstrap_mean(rv,cl,p["bootstrap"]["replications"],p["bootstrap"]["seed"]); bqv=cluster_bootstrap_mean(qv,cl,p["bootstrap"]["replications"],p["bootstrap"]["seed"]+1)
    frac=sum(x>0 for x in rv)/len(rv)
    checks={"minimum_eligible_events":len(rows)>=req,"mean_excess_log_rv_ratio_gt_zero":statistics.mean(rv)>0,
            "cluster_bootstrap_rv_ci95_lower_gt_zero":brv["ci95_lower"]>0,"median_excess_log_rv_ratio_gt_zero":statistics.median(rv)>0,
            "fraction_positive_excess_log_rv_ratio":frac>=p["promotion_gate"]["minimum_fraction_positive_excess_log_rv_ratio"],
            "mean_excess_log_quote_volume_ratio_gt_zero":statistics.mean(qv)>0,
            "cluster_bootstrap_volume_ci95_lower_gt_zero":bqv["ci95_lower"]>0}
    passed=all(checks.values())
    return {"classification":"MECHANISM_SURVIVES_DISCOVERY" if passed else "NO_CAUSAL_LAUNCH_INTENSITY_EDGE","eligible_events":len(rows),"excluded_events":len(exclusions),
            "mean_excess_log_rv_ratio":statistics.mean(rv),"median_excess_log_rv_ratio":statistics.median(rv),"fraction_positive_excess_log_rv_ratio":frac,
            "mean_excess_log_quote_volume_ratio":statistics.mean(qv),"median_excess_log_quote_volume_ratio":statistics.median(qv),"rv_bootstrap":brv,"quote_volume_bootstrap":bqv,
            "promotion_gate_checks":checks,"all_promotion_conditions_pass":passed,"event_results":rows,"exclusions":exclusions}

def run_mve_b(events,p):
    GUARDS["mve_b_2024_market_values_opened"] = True
    eligible=[]; exclusions=[]
    for e in [x for x in events if iso(x["event_timestamp_utc"]).year == 2024]:
        sym=e["symbol"]; t0=iso(e["event_timestamp_utc"]); end=t0+timedelta(minutes=p["opening_range_minutes"]+p["entry_search_minutes"]+p["hold_minutes"]+2)
        try:
            tok=load_interval("futures_um",sym,t0,end); btc=load_interval("futures_um","BTCUSDT",t0,end)
            oe=t0+timedelta(minutes=p["opening_range_minutes"]); opening=[r for r in tok if t0<=r["ts"]<oe]
            if not contiguous(opening,t0,p["opening_range_minutes"]): exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"INCOMPLETE_OPENING_RANGE"}); continue
            upper=max(r["high"] for r in opening); lower=min(r["low"] for r in opening); se=oe+timedelta(minutes=p["entry_search_minutes"]); search=[r for r in tok if oe<=r["ts"]<se]
            if not contiguous(search,oe,p["entry_search_minutes"]): exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"INCOMPLETE_ENTRY_SEARCH"}); continue
            trigger=None; direction=0
            for r in search:
                if r["close"]>upper: trigger=r; direction=1; break
                if r["close"]<lower: trigger=r; direction=-1; break
            if trigger is None:
                eligible.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"executed":False,"cluster_date_utc":t0.date().isoformat(),"gross_pair_return_bps":0.0,"base_net_bps":0.0,"stress_net_bps":0.0}); continue
            entry_ts=trigger["ts"]+timedelta(minutes=1); exit_ts=entry_ts+timedelta(minutes=p["hold_minutes"]); tm={r["ts"]:r for r in tok}; bm={r["ts"]:r for r in btc}
            te,tx,be,bx=tm.get(entry_ts),tm.get(exit_ts),bm.get(entry_ts),bm.get(exit_ts)
            if not all((te,tx,be,bx)): exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"MISSING_ENTRY_OR_EXIT_BAR"}); continue
            gross=direction*10000.0*(math.log(tx["open"]/te["open"])-math.log(bx["open"]/be["open"])); base=gross-p["costs_bps"]["BASE"]; stress=gross-p["costs_bps"]["STRESS"]
            eligible.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"executed":True,"direction":"LONG_TOKEN_SHORT_BTC" if direction==1 else "SHORT_TOKEN_LONG_BTC",
                             "trigger_timestamp_utc":trigger["ts"].isoformat().replace("+00:00","Z"),"entry_timestamp_utc":entry_ts.isoformat().replace("+00:00","Z"),"exit_timestamp_utc":exit_ts.isoformat().replace("+00:00","Z"),
                             "cluster_date_utc":entry_ts.date().isoformat(),"gross_pair_return_bps":gross,"base_net_bps":base,"stress_net_bps":stress})
        except Exception as ex:
            exclusions.append({"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],"reason":"DATA_UNAVAILABLE_OR_INVALID","detail":f"{type(ex).__name__}: {ex}"})
    min_e=p["promotion_gate"]["minimum_eligible_events"]; trades=[r for r in eligible if r["executed"]]; min_t=p["promotion_gate"]["minimum_executed_pair_trades"]
    if len(eligible)<min_e or len(trades)<min_t:
        return {"classification":"INSUFFICIENT_OOS_SAMPLE","eligible_events":len(eligible),"executed_pair_trades":len(trades),"required_eligible_events":min_e,"required_executed_pair_trades":min_t,"event_results":eligible,"exclusions":exclusions,"all_promotion_conditions_pass":False}
    stress_all=[r["stress_net_bps"] for r in eligible]; base_all=[r["base_net_bps"] for r in eligible]; clusters=[r["cluster_date_utc"] for r in eligible]
    boot=cluster_bootstrap_mean(stress_all,clusters,p["bootstrap"]["replications"],p["bootstrap"]["seed"]); st=[r["stress_net_bps"] for r in trades]; hit=sum(x>0 for x in st)/len(st); pos=sum(x for x in st if x>0); neg=-sum(x for x in st if x<0); pf=pos/neg if neg>0 else (999999.0 if pos>0 else 0.0)
    checks={"minimum_eligible_events":len(eligible)>=min_e,"minimum_executed_pair_trades":len(trades)>=min_t,"mean_stress_net_all_eligible_gt_zero":statistics.mean(stress_all)>0,
            "cluster_bootstrap_stress_mean_ci95_lower_gt_zero":boot["ci95_lower"]>0,"median_stress_net_executed_gt_zero":statistics.median(st)>0,
            "stress_hit_rate_executed":hit>p["promotion_gate"]["minimum_stress_hit_rate_executed"],"stress_profit_factor_executed":pf>p["promotion_gate"]["minimum_stress_profit_factor_executed"],
            "mean_base_net_all_eligible_gt_zero":statistics.mean(base_all)>0}
    passed=all(checks.values())
    return {"classification":"OOS_EXECUTABLE_EDGE_SURVIVES" if passed else "NO_EXECUTABLE_OOS_EDGE","eligible_events":len(eligible),"executed_pair_trades":len(trades),"no_trade_events":len(eligible)-len(trades),
            "mean_gross_all_eligible_bps":statistics.mean([r["gross_pair_return_bps"] for r in eligible]),"mean_base_net_all_eligible_bps":statistics.mean(base_all),"mean_stress_net_all_eligible_bps":statistics.mean(stress_all),
            "median_stress_net_executed_bps":statistics.median(st),"stress_hit_rate_executed":hit,"stress_profit_factor_executed":pf,"stress_bootstrap":boot,
            "promotion_gate_checks":checks,"all_promotion_conditions_pass":passed,"event_results":eligible,"exclusions":exclusions}

def source_pass(x):
    if isinstance(x,dict): return x.get("classification")=="SOURCE_DATA_PASS" or any(source_pass(v) for v in x.values())
    if isinstance(x,list): return any(source_pass(v) for v in x)
    return False

def main():
    protocol=json.loads(PROTOCOL_PATH.read_text(encoding="utf-8")); source=json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if protocol["status"]!="FROZEN_FINAL_PRE_DISCOVERY_OUTCOME_BLIND": raise RuntimeError("protocol not frozen")
    if not source_pass(source): raise RuntimeError("source gate not PASS")
    events=qualified_events(source); ycounts={y:sum(iso(e["event_timestamp_utc"]).year==y for e in events) for y in (2023,2024)}
    if len(events)!=170 or ycounts!={2023:83,2024:87}: raise RuntimeError(f"source population mismatch events={len(events)} ycounts={ycounts}")
    result={"lab_id":protocol["lab_id"],"source_mve_id":protocol["source_mve_id"],"mechanism_mve_id":protocol["mechanism_mve_id"],"strategy_mve_id":protocol["strategy_mve_id"],
            "mode":"FROZEN_SEQUENTIAL_DISCOVERY_THEN_OOS_IF_PROMOTED","guards":GUARDS.copy(),"source_population":{"qualified_events":len(events),"year_counts":ycounts},"mve_a":None,"mve_b":None,"final_classification":None}
    a=run_mve_a(events,protocol["mve_a"]); result["mve_a"]=a; result["guards"]=GUARDS.copy()
    if a.get("classification")!="MECHANISM_SURVIVES_DISCOVERY":
        result["mve_b"]={"classification":"NOT_OPENED_DISCOVERY_GATE_FAILED","year_2024_market_values_opened":False}; result["final_classification"]=a["classification"]; result["archive_manifest"]=list(MANIFEST.values())
    else:
        b=run_mve_b(events,protocol["mve_b"]); result["mve_b"]=b; result["guards"]=GUARDS.copy(); result["final_classification"]=b["classification"]; result["archive_manifest"]=list(MANIFEST.values())
    OUTDIR.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"final_classification":result["final_classification"],"mve_a":result["mve_a"]["classification"],"mve_b":result["mve_b"]["classification"],"guards":result["guards"]},indent=2,sort_keys=True))

if __name__=="__main__":
    try: main()
    except Exception as e:
        OUTDIR.mkdir(parents=True,exist_ok=True); fallback={"lab_id":"PERPETUAL-LAUNCH-SHOCK-001","final_classification":"TECHNICAL_OR_DATA_FAILURE","error":f"{type(e).__name__}: {e}","guards":GUARDS}; OUT.write_text(json.dumps(fallback,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(fallback,indent=2,sort_keys=True))
