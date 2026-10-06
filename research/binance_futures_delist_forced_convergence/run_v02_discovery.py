#!/usr/bin/env python3
import csv, hashlib, io, json, math, statistics, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
UNIVERSE=json.loads((ROOT/"V02_FROZEN_DEVELOPMENT_UNIVERSE_2026-10-06.json").read_text())
OUTDIR=ROOT/"results_v02_mechanism_discovery"
OUTDIR.mkdir(parents=True,exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 CryptoLabForcedDelistDiscovery/2.0"}
BASE="https://data.binance.vision/data/futures/um/daily"
CACHE={}

def dt(s): return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)
def ms(x): return int(x.timestamp()*1000)

def get(url,retries=4):
    if url in CACHE: return CACHE[url]
    err=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=45) as r:
                b=r.read(); CACHE[url]=b; return b
        except Exception as e:
            err=e; time.sleep(0.8*(i+1))
    raise err

def verified_zip(url):
    z=get(url)
    chk=get(url+".CHECKSUM").decode("utf-8","replace").strip()
    expected=chk.split()[0].lower()
    got=hashlib.sha256(z).hexdigest()
    if expected!=got: raise RuntimeError(f"checksum mismatch {url}")
    return z,got

def normalize_epoch(v):
    n=int(float(v))
    if n>10**14: n//=1000
    if n<10**11: n*=1000
    return n

def parse_kline_zip(sym,kind,day):
    key=("k",sym,kind,day)
    if key in CACHE: return CACHE[key]
    url=f"{BASE}/{kind}/{sym}/1m/{sym}-1m-{day}.zip"
    raw,digest=verified_zip(url)
    z=zipfile.ZipFile(io.BytesIO(raw))
    name=z.namelist()[0]
    rows=csv.reader(io.StringIO(z.read(name).decode("utf-8-sig","replace")))
    out={}
    for row in rows:
        if len(row)<5: continue
        try:
            t=normalize_epoch(row[0]); close=float(row[4])
        except Exception: continue
        out[t]=close
    CACHE[key]=(out,digest)
    return out,digest

def parse_metrics_zip(sym,day):
    key=("m",sym,day)
    if key in CACHE: return CACHE[key]
    url=f"{BASE}/metrics/{sym}/{sym}-metrics-{day}.zip"
    raw,digest=verified_zip(url)
    z=zipfile.ZipFile(io.BytesIO(raw))
    name=z.namelist()[0]
    text=z.read(name).decode("utf-8-sig","replace")
    dr=csv.DictReader(io.StringIO(text))
    out=[]
    for row in dr:
        try:
            s=(row.get("create_time") or "").strip()
            if s.isdigit():
                t=normalize_epoch(s)
            else:
                parsed=None
                for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d"):
                    try:
                        parsed=datetime.strptime(s,fmt).replace(tzinfo=timezone.utc); break
                    except Exception: pass
                if parsed is None: continue
                t=ms(parsed)
            oi=float(row["sum_open_interest"])
            if not math.isfinite(oi) or oi<=0: continue
            out.append((t,oi))
        except Exception: continue
    out.sort()
    CACHE[key]=(out,digest)
    return out,digest

def close_at(sym,kind,clock):
    day=clock.date().isoformat()
    mp,_=parse_kline_zip(sym,kind,day)
    return mp.get(ms(clock))

def oi_at_or_before(sym,clock,max_age_min=5):
    day=clock.date().isoformat()
    rows,_=parse_metrics_zip(sym,day)
    target=ms(clock)
    cand=[(t,v) for t,v in rows if t<=target and target-t<=max_age_min*60_000]
    if not cand: return None,None
    t,v=max(cand,key=lambda x:x[0])
    return v,t

def premium(mark,index): return 10000.0*(mark/index-1.0)
def signed_conv(p0,p1):
    if p0>0: return p0-p1
    if p0<0: return p1-p0
    return 0.0
def med(xs): return statistics.median(xs) if xs else None

rows=[]
for ev in UNIVERSE["events"]:
    sym=ev["symbol"]; T=dt(ev["settlement_utc"])
    clocks={
      "e0":T-timedelta(minutes=60),
      "e1":T-timedelta(minutes=1),
      "c0":T-timedelta(hours=25),
      "c1":T-timedelta(hours=24,minutes=1),
      "oi_e1":T-timedelta(minutes=5),
      "oi_c1":T-timedelta(hours=24,minutes=5),
      "s6":T-timedelta(hours=6),
      "s24":T-timedelta(hours=24),
    }
    rec={**ev,"valid":False,"invalid_reasons":[]}
    try:
        vals={}
        for tag in ("e0","e1","c0","c1","s6","s24"):
            clk=clocks[tag]
            vals[f"mark_{tag}"]=close_at(sym,"markPriceKlines",clk)
            vals[f"index_{tag}"]=close_at(sym,"indexPriceKlines",clk)
        required=[f"{k}_{tag}" for tag in ("e0","e1","c0","c1") for k in ("mark","index")]
        miss=[x for x in required if vals.get(x) is None]
        if miss: rec["invalid_reasons"].append("missing_exact_mark_index:"+",".join(miss))
        oi_e0,t_e0=oi_at_or_before(sym,clocks["e0"])
        oi_e1,t_e1=oi_at_or_before(sym,clocks["oi_e1"])
        oi_c0,t_c0=oi_at_or_before(sym,clocks["c0"])
        oi_c1,t_c1=oi_at_or_before(sym,clocks["oi_c1"])
        if any(x is None for x in (oi_e0,oi_e1,oi_c0,oi_c1)):
            rec["invalid_reasons"].append("missing_oi_clock")
        if rec["invalid_reasons"]:
            rows.append(rec); continue
        pe0=premium(vals["mark_e0"],vals["index_e0"])
        pe1=premium(vals["mark_e1"],vals["index_e1"])
        pc0=premium(vals["mark_c0"],vals["index_c0"])
        pc1=premium(vals["mark_c1"],vals["index_c1"])
        ce=signed_conv(pe0,pe1); cc=signed_conv(pc0,pc1)
        oi_decay_e=100.0*(1.0-oi_e1/oi_e0)
        oi_decay_c=100.0*(1.0-oi_c1/oi_c0)
        rec.update({
          "valid":True,
          "event_entry_premium_bps":pe0,"event_exit_premium_bps":pe1,
          "event_abs_entry_premium_bps":abs(pe0),"event_abs_exit_premium_bps":abs(pe1),
          "event_conv_bps":ce,
          "control_entry_premium_bps":pc0,"control_exit_premium_bps":pc1,
          "control_conv_bps":cc,"excess_conv_bps":ce-cc,
          "event_oi_decay_pct":oi_decay_e,"control_oi_decay_pct":oi_decay_c,
          "excess_oi_decay_pp":oi_decay_e-oi_decay_c,
          "oi_event_entry_timestamp_ms":t_e0,"oi_event_exit_timestamp_ms":t_e1,
          "oi_control_entry_timestamp_ms":t_c0,"oi_control_exit_timestamp_ms":t_c1,
        })
        for tag,label in (("s6","conv_6h_to_1m_bps"),("s24","conv_24h_to_1m_bps")):
            if vals.get(f"mark_{tag}") is not None and vals.get(f"index_{tag}") is not None:
                pp=premium(vals[f"mark_{tag}"],vals[f"index_{tag}"])
                rec[label]=signed_conv(pp,pe1)
            else: rec[label]=None
    except Exception as e:
        rec["invalid_reasons"].append(type(e).__name__+":"+str(e)[:180])
    rows.append(rec)

valid=[r for r in rows if r.get("valid")]
n=len(valid)
event_conv=[r["event_conv_bps"] for r in valid]
excess_conv=[r["excess_conv_bps"] for r in valid]
oi_event=[r["event_oi_decay_pct"] for r in valid]
oi_excess=[r["excess_oi_decay_pp"] for r in valid]
hit=(sum(1 for x in event_conv if x>0)/n if n else 0.0)
loo=[]
if n>1:
    for i in range(n): loo.append(statistics.median(event_conv[:i]+event_conv[i+1:]))
loo_min=min(loo) if loo else None
pos=[max(0.0,x) for x in event_conv]; pos_sum=sum(pos)
obs_conc=(max(pos)/pos_sum if pos_sum>0 else 1.0)
cluster=defaultdict(float)
for r in valid: cluster[r["source_article_code"]]+=max(0.0,r["event_conv_bps"])
cluster_sum=sum(cluster.values())
cluster_conc=(max(cluster.values())/cluster_sum if cluster_sum>0 else 1.0)
distinct_clusters=len(set(r["source_article_code"] for r in valid))
gates={
 "n_ge_12": n>=12,
 "median_event_conv_gt_15bps": (med(event_conv) is not None and med(event_conv)>15.0),
 "hit_rate_ge_65pct": hit>=0.65,
 "median_excess_conv_gt_10bps": (med(excess_conv) is not None and med(excess_conv)>10.0),
 "loo_median_positive": (loo_min is not None and loo_min>0),
 "observation_positive_concentration_le_35pct": obs_conc<=0.35,
 "median_event_oi_decay_ge_20pct": (med(oi_event) is not None and med(oi_event)>=20.0),
 "median_excess_oi_decay_ge_10pp": (med(oi_excess) is not None and med(oi_excess)>=10.0),
 "distinct_article_clusters_ge_10": distinct_clusters>=10,
 "article_cluster_positive_concentration_le_35pct": cluster_conc<=0.35,
}
if n<12: verdict="SOURCE_BLOCKED"
elif all(gates.values()): verdict="SURVIVES_MECHANISM_DISCOVERY"
else: verdict="NO_EDGE_DISCOVERY"
by_year={}
for y in (2024,2025):
    yy=[r for r in valid if r["settlement_utc"].startswith(str(y))]
    by_year[str(y)]={
      "n":len(yy),
      "median_event_conv_bps":med([r["event_conv_bps"] for r in yy]),
      "hit_rate":(sum(1 for r in yy if r["event_conv_bps"]>0)/len(yy) if yy else None),
      "median_event_oi_decay_pct":med([r["event_oi_decay_pct"] for r in yy]),
    }
summary={
 "lab_id":"BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001",
 "protocol":"V0.2 + V0.2.1",
 "universe_count":len(UNIVERSE["events"]),
 "valid_n":n,"source_invalid_n":len(rows)-n,
 "distinct_article_clusters":distinct_clusters,
 "median_event_conv_bps":med(event_conv),"event_conv_hit_rate":hit,
 "median_excess_conv_bps":med(excess_conv),
 "loo_min_median_event_conv_bps":loo_min,
 "observation_positive_concentration":obs_conc,
 "article_cluster_positive_concentration":cluster_conc,
 "median_event_oi_decay_pct":med(oi_event),
 "median_excess_oi_decay_pp":med(oi_excess),
 "median_abs_entry_premium_bps":med([r["event_abs_entry_premium_bps"] for r in valid]),
 "median_abs_exit_premium_bps":med([r["event_abs_exit_premium_bps"] for r in valid]),
 "median_conv_6h_to_1m_bps":med([r["conv_6h_to_1m_bps"] for r in valid if r.get("conv_6h_to_1m_bps") is not None]),
 "median_conv_24h_to_1m_bps":med([r["conv_24h_to_1m_bps"] for r in valid if r.get("conv_24h_to_1m_bps") is not None]),
 "by_year":by_year,"gates":gates,"verdict":verdict,
 "2026_market_outcomes_opened":False,"live_trading":False,
}
(OUTDIR/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
(OUTDIR/"observations.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
print("FORCED_DELIST_DISCOVERY_BEGIN")
print(json.dumps(summary,indent=2,sort_keys=True))
print("FORCED_DELIST_DISCOVERY_END")
