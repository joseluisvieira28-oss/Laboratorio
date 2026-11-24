#!/usr/bin/env python3
"""
Canonical protected 2025 Economic Discovery runner.
LAB: COMPOUND-REALIZED-DISPOSAL-FLOW-001
Authority: 30m freeze commit 2191bbf741ced5f801d8ae4034bd126c3b91cbc8

FAIL-CLOSED:
Real-data execution requires BOTH the exact authority environment token and an
exact repository authority-marker file. The marker is intentionally absent
until separate explicit protected-outcome authority is granted.
"""
import csv, hashlib, io, json, math, os, random, statistics, subprocess, sys, time, zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.request import Request, urlopen

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)

LAB_ID="COMPOUND-REALIZED-DISPOSAL-FLOW-001"
AUTH_TOKEN="COMPOUND-REALIZED-DISPOSAL-FLOW-001::PROTECTED-2025-ECONOMIC-DISCOVERY::30M::V0.1"
AUTH_MARKER=".github/authorities/compound-realized-disposal-flow-001-2025.authorized"
FREEZE_REL="pressure_mining_v0_1/labs/COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md"
EXPECTED_FREEZE_BLOB="d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430"
EXPECTED_FREEZE_COMMIT="2191bbf741ced5f801d8ae4034bd126c3b91cbc8"

COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
BUY_TOPIC="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BLOCKSCOUT="https://eth.blockscout.com"
START_TS=1735689600
END_TS=1767225599
Y2026_TS=1767225600
Y2026_MS=Y2026_TS*1000
BINANCE="https://data.binance.vision/data/spot/monthly/klines"

ASSET_MAP={
 "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
 "0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
 "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
 "0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT",
}
BENCHMARK="BTCUSDT"
HORIZON_MINUTES=30
BASE_COST_BPS=20.0
STRESS_COST_BPS=30.0
BOOTSTRAP_SEED=20260927
BOOTSTRAP_REPS=10000

EXPECTED_SOURCE_FINGERPRINT={
 "eligible_raw_logs":1157,
 "aggregated_tx_asset_events":1148,
 "kept_pre_boundary":373,
 "unique_iso_weeks_pre_boundary":35,
 "kept_by_proxy_pre_boundary":{"COMPUSDT":35,"ETHUSDT":167,"LINKUSDT":93,"UNIUSDT":78},
}

def sha256(b): return hashlib.sha256(b).hexdigest()

def fetch(url, method="GET", timeout=180):
    req=Request(url,method=method,headers={"User-Agent":"CryptoLab-Compound30m-Discovery-V0.1","Accept":"*/*"})
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return b,r.status,dict(r.headers)

def fetch_json(url,timeout=120):
    b,s,h=fetch(url,timeout=timeout)
    return json.loads(b.decode()),sha256(b),s,h

def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)

def addr(v):
    s=str(v or "").lower()
    return "0x"+s[-40:] if len(s)>=40 else None

def words(data):
    s=str(data or ""); s=s[2:] if s.startswith("0x") else s
    if len(s)%64: raise ValueError("malformed event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]

def normalize_epoch_ms(v):
    t=int(v)
    if t>=10**17: return t//1_000_000
    if t>=10**14: return t//1_000
    if t>=10**11: return t
    if t>=10**9: return t*1000
    raise ValueError(f"unsupported epoch timestamp {t}")

def month_key(ms):
    d=datetime.fromtimestamp(ms/1000,tz=timezone.utc)
    return f"{d.year}-{d.month:02d}"

def quarter_key(ms):
    d=datetime.fromtimestamp(ms/1000,tz=timezone.utc)
    return f"{d.year}-Q{((d.month-1)//3)+1}"

def iso_week_from_seconds(ts):
    d=datetime.fromtimestamp(ts,tz=timezone.utc); iso=d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

def first_complete_minute_open_ms(block_ts_seconds):
    return ((int(block_ts_seconds)//60)+1)*60*1000

def exit_open_ms(entry_open_ms):
    return int(entry_open_ms)+HORIZON_MINUTES*60*1000

def rel_log_bps(asset_entry,asset_exit,btc_entry,btc_exit):
    if min(asset_entry,asset_exit,btc_entry,btc_exit)<=0: raise ValueError("prices must be positive")
    return 10000.0*(math.log(asset_exit/asset_entry)-math.log(btc_exit/btc_entry))

def net_short_rel_bps(rel_bps,cost_bps):
    return -float(rel_bps)-float(cost_bps)

def require_authority(repo_root=ROOT):
    token=os.environ.get("CRYPTO_LAB_PROTECTED_OUTCOME_AUTHORITY","")
    marker=os.path.join(repo_root,AUTH_MARKER)
    if token!=AUTH_TOKEN or not os.path.isfile(marker):
        raise PermissionError("PROTECTED_OUTCOME_LOCKED: exact authority token and repository marker are both required")
    content=open(marker,encoding="utf-8").read().strip()
    if content!=AUTH_TOKEN:
        raise PermissionError("PROTECTED_OUTCOME_LOCKED: authority marker content mismatch")

def verify_freeze_identity():
    actual=subprocess.check_output(["git","hash-object",FREEZE_REL],cwd=ROOT,text=True).strip()
    if actual!=EXPECTED_FREEZE_BLOB:
        raise RuntimeError(f"CANONICAL_FREEZE_IDENTITY_MISMATCH expected={EXPECTED_FREEZE_BLOB} actual={actual}")
    return actual

def block_by_time(ts,closest):
    o,h,_,_=fetch_json(f"{BLOCKSCOUT}/api?module=block&action=getblocknobytime&timestamp={ts}&closest={closest}")
    r=o.get("result")
    if isinstance(r,dict):
        for k in ("blockNumber","block_number","block"):
            if r.get(k) is not None:return iv(r[k]),h
    if r is not None and not isinstance(r,(dict,list)):return iv(r),h
    raise RuntimeError(f"block-by-time failure: {o!r}")

def get_buy_logs(b0,b1):
    out=[];seen=set();pages=[];a=b0
    while a<=b1:
        z=min(b1,a+1_999_999)
        o,h,_,_=fetch_json(f"{BLOCKSCOUT}/api/?module=logs&action=getLogs&fromBlock={a}&toBlock={z}&address={COMET}&topic0={BUY_TOPIC}")
        xs=o.get("result") if isinstance(o,dict) else None
        if not isinstance(xs,list):raise RuntimeError(f"invalid log page {a}-{z}")
        if len(xs)>=1000:raise RuntimeError(f"possible source truncation {a}-{z}: {len(xs)}")
        pages.append({"from":a,"to":z,"count":len(xs),"sha256":h})
        for x in xs:
            k=(str(x.get("blockNumber")),str(x.get("transactionHash","")).lower(),str(x.get("logIndex")))
            if k not in seen:seen.add(k);out.append(x)
        a=z+1
        time.sleep(1.05)
    return out,pages

def build_predictor_population():
    b0,h0=block_by_time(START_TS,"after"); b1,h1=block_by_time(END_TS,"before")
    raw,pages=get_buy_logs(b0,b1)
    grouped=defaultdict(lambda:{"ts":None,"block":None,"base_raw":0,"coll_raw":0,"proxy":None,"asset":None})
    raw_n=0
    for x in raw:
        t=x.get("topics") or []
        asset=addr(t[2]) if len(t)>=3 else None
        if asset not in ASSET_MAP:continue
        w=words(x.get("data"))
        if len(w)<2:raise RuntimeError("BuyCollateral data words missing")
        raw_n+=1
        tx=str(x.get("transactionHash","")).lower()
        k=(asset,tx);g=grouped[k]
        g["ts"]=iv(x.get("timeStamp"));g["block"]=iv(x.get("blockNumber"))
        g["base_raw"]+=w[0];g["coll_raw"]+=w[1];g["proxy"]=ASSET_MAP[asset];g["asset"]=asset
    events=[{"tx":tx,**g} for (_,tx),g in grouped.items()]
    events.sort(key=lambda e:(e["asset"],e["ts"],e["tx"]))

    kept=[];suppressed=[];last_exit={}
    for e in events:
        cutoff=last_exit.get(e["asset"])
        if cutoff is not None and e["ts"]<cutoff:
            suppressed.append(e);continue
        kept.append(e);last_exit[e["asset"]]=e["ts"]+HORIZON_MINUTES*60

    weeks_pre=Counter(iso_week_from_seconds(e["ts"]) for e in kept)
    by_pre=Counter(e["proxy"] for e in kept)
    fingerprint={
      "eligible_raw_logs":raw_n,
      "aggregated_tx_asset_events":len(events),
      "kept_pre_boundary":len(kept),
      "unique_iso_weeks_pre_boundary":len(weeks_pre),
      "kept_by_proxy_pre_boundary":dict(sorted(by_pre.items())),
    }
    if fingerprint!=EXPECTED_SOURCE_FINGERPRINT:
        raise RuntimeError(f"SOURCE_FINGERPRINT_DRIFT expected={EXPECTED_SOURCE_FINGERPRINT} actual={fingerprint}")

    boundary=[e for e in kept if exit_open_ms(first_complete_minute_open_ms(e["ts"]))>=Y2026_MS]
    final=[e for e in kept if exit_open_ms(first_complete_minute_open_ms(e["ts"]))<Y2026_MS]
    for e in final:
        e["entry_ms"]=first_complete_minute_open_ms(e["ts"])
        e["exit_ms"]=exit_open_ms(e["entry_ms"])
        e["iso_week"]=iso_week_from_seconds(e["ts"])
        e["quarter"]=quarter_key(e["entry_ms"])
        e["flow_usdc"]=e["base_raw"]/1e6

    return final,{
      "start_block":b0,"end_block":b1,"start_lookup_sha256":h0,"end_lookup_sha256":h1,
      "source_pages":pages,"fingerprint":fingerprint,
      "overlap_suppressed":len(suppressed),"protected_boundary_exclusions":len(boundary),
      "boundary_events":[{"asset":e["asset"],"proxy":e["proxy"],"tx":e["tx"],"timestamp":e["ts"]} for e in boundary],
    }

archive_cache={}
archive_receipts=[]

def load_archive(symbol,ym):
    key=(symbol,ym)
    if key in archive_cache:return archive_cache[key]
    if not ym.startswith("2025-"):raise RuntimeError(f"PROTECTED_2026_ARCHIVE_BLOCKED {symbol} {ym}")
    url=f"{BINANCE}/{symbol}/1m/{symbol}-1m-{ym}.zip"
    cb,_,_=fetch(url+".CHECKSUM",timeout=60)
    token=cb.decode(errors="replace").strip().split()[0].lower()
    if len(token)!=64 or any(c not in "0123456789abcdef" for c in token):
        raise RuntimeError(f"bad checksum token {symbol} {ym}")
    zb,_,_=fetch(url,timeout=240)
    actual=sha256(zb)
    if actual!=token:raise RuntimeError(f"checksum mismatch {symbol} {ym}")
    z=zipfile.ZipFile(io.BytesIO(zb));names=z.namelist()
    if len(names)!=1:raise RuntimeError(f"unexpected zip members {symbol} {ym}: {names}")
    bars={}
    with z.open(names[0]) as raw:
        txt=io.TextIOWrapper(raw,encoding="utf-8")
        for row in csv.reader(txt):
            if len(row)<2:continue
            try:
                t=normalize_epoch_ms(row[0]);op=float(row[1])
            except Exception:
                continue
            bars[t]=op
    archive_receipts.append({"symbol":symbol,"month":ym,"zip_sha256":actual,"checksum_token":token,"rows":len(bars)})
    archive_cache[key]=bars
    return bars

def price_open(symbol,ms):
    return load_archive(symbol,month_key(ms)).get(ms)

def pf(vals):
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0)
    if neg>0:return pos/neg
    if pos>0:return "INF"
    return None

def pf_gate(v):
    return v=="INF" or (isinstance(v,(int,float)) and v>1.0)

def mean(xs):return sum(xs)/len(xs) if xs else None

def bootstrap_ci(rows):
    weeks=sorted({r["iso_week"] for r in rows})
    groups={w:[r["base_net_bps"] for r in rows if r["iso_week"]==w] for w in weeks}
    rnd=random.Random(BOOTSTRAP_SEED);vals=[]
    for _ in range(BOOTSTRAP_REPS):
        drawn=[rnd.choice(weeks) for __ in weeks];sample=[]
        for w in drawn:sample.extend(groups[w])
        vals.append(mean(sample))
    vals.sort();n=len(vals)
    return [vals[int(0.025*(n-1))],vals[int(0.975*(n-1))]]

def evaluate(events):
    rows=[];invalid=[]
    for e in events:
        ae=price_open(e["proxy"],e["entry_ms"]);ax=price_open(e["proxy"],e["exit_ms"])
        be=price_open(BENCHMARK,e["entry_ms"]);bx=price_open(BENCHMARK,e["exit_ms"])
        if None in (ae,ax,be,bx) or min(x for x in (ae,ax,be,bx) if x is not None)<=0:
            invalid.append({"tx":e["tx"],"asset":e["asset"],"proxy":e["proxy"],"reason":"MISSING_EXACT_REQUIRED_BAR",
                            "entry_ms":e["entry_ms"],"exit_ms":e["exit_ms"]})
            continue
        rel=rel_log_bps(ae,ax,be,bx);gross=-rel
        rows.append({**e,"asset_entry":ae,"asset_exit":ax,"btc_entry":be,"btc_exit":bx,
                     "rel_30m_bps":rel,"gross_short_rel_bps":gross,
                     "base_net_bps":gross-BASE_COST_BPS,"stress_net_bps":gross-STRESS_COST_BPS})

    N=len(rows);weeks=sorted({r["iso_week"] for r in rows});assets=sorted({r["proxy"] for r in rows})
    base=[r["base_net_bps"] for r in rows];stress=[r["stress_net_bps"] for r in rows];gross=[r["gross_short_rel_bps"] for r in rows]
    base_pf=pf(base);stress_pf=pf(stress)
    ci=bootstrap_ci(rows) if rows and weeks else [None,None]

    by_asset={}
    for a in ["ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]:
        rr=[r for r in rows if r["proxy"]==a]
        by_asset[a]={"n":len(rr),"gross_mean_bps":mean([x["gross_short_rel_bps"] for x in rr]),
                     "base_net_mean_bps":mean([x["base_net_bps"] for x in rr]),
                     "stress_net_mean_bps":mean([x["stress_net_bps"] for x in rr]),
                     "base_pf":pf([x["base_net_bps"] for x in rr]),"stress_pf":pf([x["stress_net_bps"] for x in rr])}

    quarters={}
    for q in sorted({r["quarter"] for r in rows}):
        rr=[r for r in rows if r["quarter"]==q]
        quarters[q]={"n":len(rr),"gross_mean_bps":mean([x["gross_short_rel_bps"] for x in rr]),
                     "base_net_mean_bps":mean([x["base_net_bps"] for x in rr])}

    loo={}
    for a in ["ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]:
        x=[r["base_net_bps"] for r in rows if r["proxy"]!=a]
        loo[a]=mean(x)

    positives=[x for x in base if x>0];pos_total=sum(positives)
    largest_event_share=(max(positives)/pos_total) if positives and pos_total>0 else None
    week_pos=Counter()
    for r in rows:
        if r["base_net_bps"]>0:week_pos[r["iso_week"]]+=r["base_net_bps"]
    largest_week_share=(max(week_pos.values())/pos_total) if week_pos and pos_total>0 else None

    counts=Counter(r["proxy"] for r in rows)
    gates={
      "n_ge_100":N>=100,
      "iso_weeks_ge_20":len(weeks)>=20,
      "all_four_assets_ge_10":all(counts[a]>=10 for a in ["ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]),
      "pooled_base_net_mean_gt_0":mean(base) is not None and mean(base)>0,
      "pooled_base_pf_gt_1":pf_gate(base_pf),
      "pooled_stress_net_mean_gt_0":mean(stress) is not None and mean(stress)>0,
      "pooled_stress_pf_gt_1":pf_gate(stress_pf),
      "bootstrap_lower_95_gt_0":ci[0] is not None and ci[0]>0,
      "every_asset_base_net_mean_gt_0":all(by_asset[a]["base_net_mean_bps"] is not None and by_asset[a]["base_net_mean_bps"]>0 for a in by_asset),
      "every_leave_one_asset_out_base_mean_gt_0":all(v is not None and v>0 for v in loo.values()),
      "largest_positive_event_share_le_25pct":largest_event_share is not None and largest_event_share<=0.25,
      "largest_positive_week_share_le_35pct":largest_week_share is not None and largest_week_share<=0.35,
    }
    verdict="DISCOVERY_PASS_NOT_YET_TIER2" if all(gates.values()) else "DISCOVERY_FAIL_NO_PROMOTION"

    return {
      "verdict":verdict,
      "sample":{"n":N,"invalid_missing_bar":len(invalid),"unique_iso_weeks":len(weeks),"by_asset":dict(sorted(counts.items()))},
      "primary":{"gross_mean_bps":mean(gross),"gross_median_bps":statistics.median(gross) if gross else None,
                 "base_net_mean_bps":mean(base),"base_net_median_bps":statistics.median(base) if base else None,
                 "stress_net_mean_bps":mean(stress),"stress_net_median_bps":statistics.median(stress) if stress else None,
                 "base_pf":base_pf,"stress_pf":stress_pf,
                 "base_win_rate":(sum(x>0 for x in base)/N) if N else None,
                 "bootstrap_95_base_mean_bps":ci,"bootstrap_clusters":"UTC_ISO_WEEK",
                 "bootstrap_resamples":BOOTSTRAP_REPS,"bootstrap_seed":BOOTSTRAP_SEED,
                 "largest_positive_event_share":largest_event_share,
                 "largest_positive_iso_week_share":largest_week_share},
      "gates":gates,"by_asset":by_asset,"by_quarter":quarters,"leave_one_asset_out_base_mean_bps":loo,
      "invalid_events":invalid,"events":rows,
    }

def synthetic_overlap(events):
    rows=sorted(events,key=lambda e:(e["asset"],e["ts"],e["tx"]));kept=[];last={}
    for e in rows:
        if e["asset"] in last and e["ts"]<last[e["asset"]]:continue
        kept.append(e);last[e["asset"]]=e["ts"]+1800
    return kept

def synthetic_self_test():
    assert set(ASSET_MAP.values())=={"ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"}
    assert BENCHMARK=="BTCUSDT" and HORIZON_MINUTES==30
    assert BASE_COST_BPS==20.0 and STRESS_COST_BPS==30.0
    t=1_800_000_012;e=first_complete_minute_open_ms(t)
    assert e==((t//60)+1)*60*1000 and exit_open_ms(e)-e==30*60*1000
    r=rel_log_bps(100,99,100,100);assert r<0 and net_short_rel_bps(r,0)>0
    assert abs((net_short_rel_bps(r,20)-net_short_rel_bps(r,30))-10)<1e-12
    s=[{"asset":"a","ts":1000,"tx":"1"},{"asset":"a","ts":2000,"tx":"2"},{"asset":"a","ts":2800,"tx":"3"},
       {"asset":"b","ts":1100,"tx":"4"}]
    k=synthetic_overlap(s)
    assert [(x["asset"],x["tx"]) for x in k]==[("a","1"),("a","3"),("b","4")]
    assert normalize_epoch_ms(1735689600000)==1735689600000
    assert normalize_epoch_ms(1735689600000000)==1735689600000
    assert pf_gate("INF") and pf_gate(1.1) and not pf_gate(0.9)
    failed=False
    try:require_authority(ROOT)
    except PermissionError:failed=True
    assert failed
    return True

def main():
    if "--synthetic-self-test" in sys.argv:
        synthetic_self_test();print("SYNTHETIC_SELF_TEST_PASS");print("PROTECTED_OUTCOME_LOCK_PASS");return 0

    require_authority(ROOT)
    freeze_blob=verify_freeze_identity()

    # Source-only predictor reconstruction occurs before any Binance ZIP is opened.
    events,source=build_predictor_population()
    source_counts=Counter(e["proxy"] for e in events);source_weeks={e["iso_week"] for e in events}
    if len(events)<100 or len(source_weeks)<20 or not all(source_counts[x]>=10 for x in ["ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]):
        raise RuntimeError("CANONICAL_SAMPLE_GATE_FAILED_PRE_PRICE")

    result=evaluate(events)
    receipt={
      "lab_id":LAB_ID,
      "protocol":"COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1",
      "canonical_freeze_commit":EXPECTED_FREEZE_COMMIT,
      "canonical_freeze_git_blob":freeze_blob,
      "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
      **result,
      "source":{"predictor":source,"binance_archives":sorted(archive_receipts,key=lambda x:(x["symbol"],x["month"]))},
      "interpretation":{"discovery_only":True,"tier2_claim":False,"live_trading_authority":False,
                        "no_rescue_if_failed":True},
      "firewall":{"protected_2025_market_outcomes_opened":True,"protected_2026_market_outcomes_opened":False,
                  "live_trading":False,"orders":False,"exchange_mutation":False,"capital":False,
                  "paid_data":False,"main_merge":False,"post_outcome_tuning":False}
    }
    pre=json.dumps(receipt,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    receipt["receipt_sha256_pre_self_field"]=sha256(pre)
    p=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_DISCOVERY_RECEIPT_V0.1.json")
    with open(p,"w",encoding="utf-8") as f:json.dump(receipt,f,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    summary={k:v for k,v in receipt.items() if k not in ("events","source","invalid_events")}
    print(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False))
    print("receipt="+p)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
