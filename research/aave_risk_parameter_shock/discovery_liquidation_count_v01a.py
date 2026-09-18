#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import random
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="AAVE-RISK-PARAMETER-SHOCK-001"
MVE_ID="ARPS-LT-DOWN-LIQCOUNT-H24-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
FROM_BLOCK=16_490_000
TO_BLOCK=21_525_890
MAX_TS=1_735_689_599
WINDOW=75_000
HORIZON_SECONDS=86_400
MIN_EPISODES=12
MIN_ASSETS=4
MIN_YEARS=2
EXPECTED_LIQUIDATION_CALLS=5_539
TRANSIENT={429,500,502,503,504,529}
LIQ_SIG="LiquidationCall(address,address,address,uint256,uint256,address,bool)"
LIQ_TOPIC="0x"+keccak(LIQ_SIG.encode()).hex()
RANDOMIZATION_SEED=20260918
BOOTSTRAP_SEED=20260919
MONTE_CARLO_N=100_000
BOOTSTRAP_N=10_000

def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad integer")

def topic_addr(v:str)->str:
    s=str(v).lower()
    if not s.startswith("0x") or len(s)!=66: raise ValueError("bad indexed address")
    return "0x"+s[-40:]

def load_one(root:str,predicate):
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text(encoding="utf-8"))
        if predicate(o): xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected exactly one matching receipt under {root}, found {len(xs)}")
    return xs[0]

def post(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={
                "Content-Type":"application/json","Accept-Encoding":"gzip",
                "User-Agent":f"{LAB_ID}/{MVE_ID}/v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}"); r.close()
                if attempt<7:
                    stats["transient_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
                raise last
            if r.status_code==204:
                r.close(); raise RuntimeError("unexpected Portal 204 inside frozen envelope")
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except (requests.RequestException,RuntimeError) as exc:
            last=exc
            if attempt<7:
                stats["network_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def treatment_clean_episodes(mech:dict[str,Any], source:dict[str,Any]):
    episodes=mech.get("independent_24h_episodes") or []
    clusters=mech.get("primary_decrease_clusters") or []
    all_cluster_times=[(int(x["timestamp"]),x["transactionHash"]) for x in clusters]
    first_source_ts=int(source["first_matching_timestamp"])
    clean=[]
    exclusions=[]
    for ep in episodes:
        start=int(ep["episode_start_timestamp"]); end=int(ep["episode_end_timestamp"])
        own=set(ep["transactionHashes"])
        pre_other=[tx for ts,tx in all_cluster_times if tx not in own and start-HORIZON_SECONDS <= ts < start]
        post_other=[tx for ts,tx in all_cluster_times if tx not in own and end < ts <= end+HORIZON_SECONDS]
        reasons=[]
        if pre_other: reasons.append("OTHER_THRESHOLD_DECREASE_IN_PRE24H")
        if post_other: reasons.append("OTHER_THRESHOLD_DECREASE_IN_POST24H")
        if start-HORIZON_SECONDS < first_source_ts: reasons.append("PRE_WINDOW_BEFORE_CONSERVATIVE_SOURCE_BOUNDARY")
        if end+HORIZON_SECONDS > MAX_TS: reasons.append("POST_WINDOW_AFTER_PROTECTED_BOUNDARY")
        if reasons:
            exclusions.append({"episode_id":ep["episode_id"],"reasons":reasons})
        else:
            clean.append(ep)
    assets=sorted({a for ep in clean for a in ep["affected_assets"]})
    years=sorted({int(ep["calendar_year"]) for ep in clean})
    return clean,exclusions,assets,years

def acquire_liquidations(stats:Counter[str]):
    rows=[]; seen=set(); cursor=FROM_BLOCK
    while cursor<=TO_BLOCK:
        rt=min(TO_BLOCK,cursor+WINDOW-1)
        body={
            "type":"evm","fromBlock":cursor,"toBlock":rt,
            "fields":{"block":{"number":True,"timestamp":True},
                      "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
            "logs":[{"address":[POOL],"topic0":[LIQ_TOPIC]}],
        }
        r=post(body,stats); n=0; page_last=None; response_rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                h=obj.get("header") or obj.get("block") or {}
                bn=as_int(h.get("number")); ts=as_int(h.get("timestamp"))
                if not(cursor<=bn<=rt): raise RuntimeError("liquidation row outside request window")
                if page_last is not None and bn<page_last: raise RuntimeError("liquidation SQD page non-monotonic")
                page_last=bn; response_rows+=1
                if ts>MAX_TS: raise RuntimeError("protected-period liquidation row")
                for log in obj.get("logs") or []:
                    addr=str(log.get("address","")).lower()
                    topics=[str(x).lower() for x in (log.get("topics") or [])]
                    tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex"))
                    if addr!=POOL or len(topics)<4 or topics[0]!=LIQ_TOPIC: raise RuntimeError("malformed LiquidationCall")
                    key=(tx,li)
                    if key in seen: raise RuntimeError("duplicate LiquidationCall identity")
                    seen.add(key)
                    rows.append({"block":bn,"timestamp":ts,"transactionHash":tx,"logIndex":li,
                                 "collateralAsset":topic_addr(topics[1])})
                    n+=1
        finally: r.close()
        stats["windows_completed"]+=1
        stats["matching_liquidation_calls"]+=n
        stats["portal_rows"]+=response_rows
        if page_last is None:
            stats["empty_matching_windows"]+=1
            stats["covered_through_block"]=rt
            cursor=rt+1
        else:
            if page_last<cursor: raise RuntimeError("LiquidationCall SQD continuation did not advance")
            stats["covered_through_block"]=page_last
            cursor=page_last+1
    return rows

def exact_or_mc_randomization(ds:list[int]):
    obs=sum(ds)/len(ds)
    n=len(ds)
    if n<=20:
        total=1<<n; ge=0
        for mask in range(total):
            stat=sum((d if (mask>>i)&1 else -d) for i,d in enumerate(ds))/n
            if stat>=obs-1e-15: ge+=1
        return ge/total,{"method":"EXACT_ALL_SWAPS","draws":total,"seed":None}
    rng=random.Random(RANDOMIZATION_SEED); ge=0
    for _ in range(MONTE_CARLO_N):
        stat=sum(d if rng.getrandbits(1) else -d for d in ds)/n
        if stat>=obs-1e-15: ge+=1
    return (ge+1)/(MONTE_CARLO_N+1),{"method":"MONTE_CARLO_SWAPS","draws":MONTE_CARLO_N,"seed":RANDOMIZATION_SEED}

def bootstrap_ci(ds:list[int]):
    rng=random.Random(BOOTSTRAP_SEED); n=len(ds); vals=[]
    for _ in range(BOOTSTRAP_N):
        vals.append(sum(ds[rng.randrange(n)] for __ in range(n))/n)
    vals.sort()
    lo=vals[math.floor(0.025*(BOOTSTRAP_N-1))]
    hi=vals[math.floor(0.975*(BOOTSTRAP_N-1))]
    return lo,hi

def main()->int:
    outdir=Path("out/aave_risk_parameter_shock"); outdir.mkdir(parents=True,exist_ok=True)
    outpath=outdir/"AAVE_RISK_PARAMETER_SHOCK_001_DISCOVERY_V0_1.json"
    stats=Counter()
    receipt={
      "frontier_id":LAB_ID,"mve_id":MVE_ID,"phase":"CAUSAL_ONCHAIN_DISCOVERY_OUTCOME_BLIND_TO_MARKETS",
      "classification":None,"failure":None,
      "safety":{"market_prices_opened":False,"market_returns_opened":False,"pnl_opened":False,
                "execution_costs_opened":False,"health_factor_computed":False,"liquidation_overhang_computed":False,
                "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    try:
        mech=load_one("downloaded_mechanism_census",lambda o:o.get("frontier_id")==LAB_ID and o.get("phase")=="PRIMARY_MECHANISM_CENSUS_OUTCOME_BLIND")
        if mech.get("classification")!="MECHANISM_CENSUS_PASS":
            raise RuntimeError(f"mechanism census not PASS: {mech.get('classification')}")
        source=load_one("downloaded_aave_source_census",lambda o:o.get("lab_id")=="AAVE-LIQUIDATION-OVERHANG-001" and o.get("classification")=="SOURCE_CENSUS_PASS")
        if int(source.get("frozen_from_block",-1))!=FROM_BLOCK or int(source.get("frozen_to_block",-1))!=TO_BLOCK:
            raise RuntimeError("canonical AAVE source envelope mismatch")
        if int((source.get("event_counts") or {}).get("LiquidationCall",-1))!=EXPECTED_LIQUIDATION_CALLS:
            raise RuntimeError("canonical LiquidationCall population mismatch")

        clean,exclusions,assets,years=treatment_clean_episodes(mech,source)
        receipt.update({"mechanism_episode_count":len(mech.get("independent_24h_episodes") or []),
                        "eligible_clean_episode_count":len(clean),"treatment_only_exclusions":exclusions,
                        "eligible_unique_assets":assets,"eligible_calendar_years":years})
        if len(clean)<MIN_EPISODES or len(assets)<MIN_ASSETS or len(years)<MIN_YEARS:
            receipt["classification"]="DISCOVERY_INSUFFICIENT_SAMPLE"
            receipt["failure"]="clean treatment-timing sample gate failed before LiquidationCall outcomes were opened"
        else:
            liqs=acquire_liquidations(stats)
            if len(liqs)!=EXPECTED_LIQUIDATION_CALLS:
                raise RuntimeError(f"LiquidationCall source count mismatch {len(liqs)} != {EXPECTED_LIQUIDATION_CALLS}")

            rows=[]
            for ep in clean:
                start=int(ep["episode_start_timestamp"]); end=int(ep["episode_end_timestamp"])
                affected=set(ep["affected_assets"])
                pre=sum(1 for x in liqs if x["collateralAsset"] in affected and start-HORIZON_SECONDS<=int(x["timestamp"])<start)
                post=sum(1 for x in liqs if x["collateralAsset"] in affected and end<int(x["timestamp"])<=end+HORIZON_SECONDS)
                rows.append({"episode_id":ep["episode_id"],"episode_start_timestamp":start,"episode_end_timestamp":end,
                             "calendar_year":int(ep["calendar_year"]),"affected_assets":sorted(affected),
                             "pre_liquidation_count":pre,"post_liquidation_count":post,"D":post-pre})
            ds=[int(x["D"]) for x in rows]
            mean_d=sum(ds)/len(ds); med=statistics.median(ds)
            p,randmeta=exact_or_mc_randomization(ds)
            ci_lo,ci_hi=bootstrap_ci(ds)
            yearly={}
            for y in sorted({x["calendar_year"] for x in rows}):
                yd=[x["D"] for x in rows if x["calendar_year"]==y]
                yearly[str(y)]={"N":len(yd),"mean_D":sum(yd)/len(yd)}
            positive=[max(0,d) for d in ds]; positive_sum=sum(positive)
            max_share=(max(positive)/positive_sum if positive_sum>0 else 1.0)
            gates={
              "sample_gate":len(rows)>=MIN_EPISODES and len(assets)>=MIN_ASSETS and len(years)>=MIN_YEARS,
              "mean_positive":mean_d>0,
              "median_nonnegative":med>=0,
              "randomization_p_lt_005":p<0.05,
              "bootstrap_lower_gt_zero":ci_lo>0,
              "year_gate":sum(1 for v in yearly.values() if v["mean_D"]>=0)>=2,
              "concentration_gate":max_share<=0.35,
            }
            passed=all(gates.values())
            receipt.update({"classification":"DISCOVERY_FORCED_FLOW_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE" if passed else "DISCOVERY_NO_FORCED_FLOW_MECHANISM",
                            "eligible_episodes":rows,"N":len(rows),"mean_D":mean_d,"median_D":med,
                            "randomization_p_one_sided":p,"randomization":randmeta,
                            "bootstrap_mean_D_ci95":[ci_lo,ci_hi],"bootstrap_resamples":BOOTSTRAP_N,"bootstrap_seed":BOOTSTRAP_SEED,
                            "yearly":yearly,"largest_positive_D_episode_share":max_share,
                            "promotion_gates":gates,"liquidation_call_source_count":len(liqs)})
    except Exception as exc:
        receipt["classification"]="DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1500]}"
    receipt["transport_stats"]=dict(stats)
    outpath.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"N":receipt.get("N"),
                      "mean_D":receipt.get("mean_D"),"p":receipt.get("randomization_p_one_sided"),
                      "market_prices_opened":False,"market_returns_opened":False,"pnl_opened":False,
                      "accessed_2025_or_2026":False},sort_keys=True))
    return 0 if receipt["classification"] in {
        "DISCOVERY_INSUFFICIENT_SAMPLE","DISCOVERY_NO_FORCED_FLOW_MECHANISM",
        "DISCOVERY_FORCED_FLOW_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE"
    } else 2

if __name__=="__main__":
    raise SystemExit(main())
