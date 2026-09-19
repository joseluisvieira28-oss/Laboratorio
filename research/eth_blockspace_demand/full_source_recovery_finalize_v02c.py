#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, statistics, sys, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

LAB="ETH-BLOCKSPACE-DEMAND-001"
START=13_000_000; STOP=21_500_000; STRIDE=1_800
TARGETS=list(range(START,STOP+1,STRIDE)); EXPECTED=len(TARGETS)
AUDIT_IDX={i for i in range(EXPECTED) if i%20==0}
CUTOFF=1_735_689_600
EPS=("https://eth.drpc.org","https://rpc.flashbots.net")
ROOT=Path("parent_shards")
OUT=Path("eth_blockspace_full_source_v02c_final"); OUT.mkdir(parents=True,exist_ok=True)
FIELDS=["global_index","block_number","block_hash","parent_hash","timestamp","gas_limit","gas_used","base_fee_per_gas",
        "assigned_provider","provider_used","fallback_used","audit_required","audit_pass","gas_utilization","sample_block_base_fee_burn_wei"]
sessions={e:requests.Session() for e in EPS}

def rpc(ep:str,b:int,retries:int=5):
    last=None
    for i in range(retries):
        try:
            r=sessions[ep].post(ep,json={"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":[hex(b),False]},
                headers={"Content-Type":"application/json","User-Agent":f"{LAB}/source-recovery-v0.2c"},timeout=(8,25))
            if r.status_code in (429,500,502,503,504):
                raise RuntimeError(f"HTTP_{r.status_code}")
            r.raise_for_status(); o=r.json()
            if o.get("error") is not None: raise RuntimeError(f"rpc_error:{o['error']}")
            return o.get("result")
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(min(0.8*(2**i),8.0))
    raise RuntimeError(f"{type(last).__name__}:{str(last)[:180]}")

def qi(x): 
    if not isinstance(x,str) or not x.startswith("0x"): raise ValueError("quantity")
    return int(x,16)

def parse(ep,b):
    o=rpc(ep,b)
    if not isinstance(o,dict): raise RuntimeError("null_block")
    n=qi(o["number"]); ts=qi(o["timestamp"]); gl=qi(o["gasLimit"]); gu=qi(o["gasUsed"]); bf=qi(o["baseFeePerGas"])
    if n!=b: raise RuntimeError("identity_number")
    if ts>=CUTOFF: raise RuntimeError("PROTECTED_PERIOD")
    if gl<=0 or gu<0 or gu>gl or bf<=0: raise RuntimeError("header_sanity")
    return {"block_number":n,"block_hash":str(o["hash"]).lower(),"parent_hash":str(o["parentHash"]).lower(),
            "timestamp":ts,"gas_limit":gl,"gas_used":gu,"base_fee_per_gas":bf}

def boolv(x):
    if isinstance(x,bool): return x
    if x in (None,"","None"): return None
    return str(x).lower()=="true"

def load_parent():
    csvs=sorted(ROOT.rglob("ETH_BLOCKSPACE_SOURCE_SHARD_*.csv"))
    if len(csvs)!=8: raise RuntimeError(f"expected 8 parent csv, got {len(csvs)}")
    rows={}
    for p in csvs:
        with p.open("r",encoding="utf-8",newline="") as f:
            for x in csv.DictReader(f):
                i=int(x["global_index"])
                row={"global_index":i,"block_number":int(x["block_number"]),"block_hash":x["block_hash"],
                     "parent_hash":x["parent_hash"],"timestamp":int(x["timestamp"]),"gas_limit":int(x["gas_limit"]),
                     "gas_used":int(x["gas_used"]),"base_fee_per_gas":int(x["base_fee_per_gas"]),
                     "assigned_provider":x["assigned_provider"],"provider_used":x["provider_used"],
                     "fallback_used":boolv(x["fallback_used"]),"audit_required":boolv(x["audit_required"]),
                     "audit_pass":boolv(x["audit_pass"]),"gas_utilization":float(x["gas_utilization"]),
                     "sample_block_base_fee_burn_wei":int(x["sample_block_base_fee_burn_wei"])}
                if i in rows:
                    if rows[i]["block_hash"]!=row["block_hash"]: raise RuntimeError(f"duplicate_disagreement:{i}")
                else: rows[i]=row
    return rows

def main():
    assert EXPECTED==4723 and len(AUDIT_IDX)==237
    rows=load_parent()
    parent_count=len(rows)
    missing=[i for i in range(EXPECTED) if i not in rows]
    audit_retry=[i for i in sorted(AUDIT_IDX) if i not in rows or rows[i].get("audit_pass") is not True]
    recovery_set=sorted(set(missing)|set(audit_retry))
    errors=[]; recovered_new=0; recovered_audit=0; protected=False; one_provider_non_audit=0

    for k,i in enumerate(recovery_set,1):
        b=TARGETS[i]; got={}
        for ep in EPS:
            try: got[ep]=parse(ep,b)
            except Exception as e:
                if "PROTECTED_PERIOD" in str(e): protected=True
                errors.append({"index":i,"block_number":b,"provider":ep,"error":f"{type(e).__name__}:{str(e)[:160]}"})
        if i in AUDIT_IDX:
            if len(got)!=2: continue
            a,c=got[EPS[0]],got[EPS[1]]
            if a["block_hash"]!=c["block_hash"] or a["timestamp"]!=c["timestamp"]:
                errors.append({"index":i,"block_number":b,"provider":"BOTH","error":"PROVENANCE_DISAGREEMENT"}); continue
            recovered_audit+=1
        if i not in rows:
            if not got: continue
            if len(got)==1 and i not in AUDIT_IDX: one_provider_non_audit+=1
            ep=EPS[0] if EPS[0] in got else EPS[1]; a=got[ep]
            rows[i]={**a,"global_index":i,"assigned_provider":EPS[i%2],"provider_used":ep,
                     "fallback_used":ep!=EPS[i%2],"audit_required":i in AUDIT_IDX,
                     "audit_pass":True if i in AUDIT_IDX else None,
                     "gas_utilization":a["gas_used"]/a["gas_limit"],
                     "sample_block_base_fee_burn_wei":a["base_fee_per_gas"]*a["gas_used"]}
            recovered_new+=1
        elif i in AUDIT_IDX and len(got)==2:
            rows[i]["audit_pass"]=True
        time.sleep(0.08)

    ordered=[rows[i] for i in sorted(rows)]
    duplicate_blocks=len(ordered)-len({r["block_number"] for r in ordered})
    coverage=len(ordered)/EXPECTED
    audits=[rows[i] for i in sorted(AUDIT_IDX) if i in rows and rows[i].get("audit_pass") is True]
    protected_rows=sum(r["timestamp"]>=CUTOFF for r in ordered)

    raw=OUT/"ETH_BLOCKSPACE_DEMAND_001_SAMPLED_BLOCKS_V0_2C.csv"
    with raw.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(ordered)

    by=defaultdict(list)
    for r in ordered:
        d=datetime.fromtimestamp(r["timestamp"],tz=timezone.utc).date().isoformat(); by[d].append(r)
    dates=sorted(by); daily=[]; excluded=[]
    for d in dates:
        xs=by[d]
        if len(xs)<3: excluded.append({"date":d,"sample_count":len(xs)}); continue
        u=[r["gas_utilization"] for r in xs]
        fees=[r["base_fee_per_gas"]/1e9 for r in xs]
        burns=[r["sample_block_base_fee_burn_wei"]/1e18 for r in xs]
        daily.append({"date":d,"sample_count":len(xs),"mean_gas_utilization":sum(u)/len(u),
                      "median_base_fee_gwei":statistics.median(fees),
                      "mean_sample_block_base_fee_burn_eth":sum(burns)/len(burns),
                      "max_sample_block_base_fee_burn_eth":max(burns)})
    d0=datetime.fromisoformat(dates[0]).date(); d1=datetime.fromisoformat(dates[-1]).date()
    cal=(d1-d0).days+1; retention=len(daily)/cal
    dp=OUT/"ETH_BLOCKSPACE_DEMAND_001_DAILY_SOURCE_SERIES_V0_2C.csv"
    with dp.open("w",encoding="utf-8",newline="") as f:
        fn=["date","sample_count","mean_gas_utilization","median_base_fee_gwei","mean_sample_block_base_fee_burn_eth","max_sample_block_base_fee_burn_eth"]
        w=csv.DictWriter(f,fieldnames=fn);w.writeheader();w.writerows(daily)

    gates={"coverage_ge_99_5pct":coverage>=0.995,"all_237_audits_pass":len(audits)==237,
           "no_duplicate_blocks":duplicate_blocks==0,"no_protected_period":not protected and protected_rows==0,
           "daily_retention_ge_95pct":retention>=0.95}
    status="SOURCE_DATA_PASS" if all(gates.values()) else ("PROVENANCE_FAILURE" if protected or protected_rows else "SOURCE_DATA_FAILURE")
    receipt={"lab_id":LAB,"status":status,"parent_run_id":35445718239,"parent_rows_reused":parent_count,
             "recovery_targets":len(recovery_set),"missing_targets_before_recovery":len(missing),
             "incomplete_audits_before_recovery":len(audit_retry),"recovered_new_rows":recovered_new,
             "recovered_audits":recovered_audit,"one_provider_non_audit_recoveries":one_provider_non_audit,
             "final_rows":len(ordered),"coverage":coverage,"audit_pass_count":len(audits),
             "duplicate_blocks":duplicate_blocks,"protected_period_rows":protected_rows,
             "calendar_days":cal,"canonical_daily_rows":len(daily),"daily_retention":retention,
             "excluded_lt3_samples":excluded,"recovery_error_count":len(errors),"recovery_errors":errors[:100],
             "gates":gates,"artifacts":{"sampled_blocks_sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),
             "daily_series_sha256":hashlib.sha256(dp.read_bytes()).hexdigest()},
             "safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
                       "protected_period_accessed":protected or protected_rows>0,"live_trading":False,
                       "orders":False,"exchange_mutation":False,"merge_main":False}}
    rp=OUT/"ETH_BLOCKSPACE_DEMAND_001_FULL_SOURCE_DATA_GATE_V0_2C_RECEIPT.json"
    rp.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"status":status,"parent_rows_reused":parent_count,"recovery_targets":len(recovery_set),
                      "recovered_new_rows":recovered_new,"final_rows":len(ordered),"coverage":coverage,
                      "audit_pass_count":len(audits),"daily_retention":retention,
                      "recovery_error_count":len(errors),"market_prices_opened":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if status=="SOURCE_DATA_PASS" else 2

if __name__=="__main__": sys.exit(main())
