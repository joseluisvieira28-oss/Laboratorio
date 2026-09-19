#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, math, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

LAB="ETH-BLOCKSPACE-DEMAND-001"
EXPECTED_TARGETS=4723
EXPECTED_AUDITS=237
CUTOFF=1_735_689_600
ROOT=Path("source_shards")
OUT=Path("eth_blockspace_full_source_v02a_final")
OUT.mkdir(parents=True,exist_ok=True)

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->int:
    csvs=sorted(ROOT.rglob("ETH_BLOCKSPACE_SOURCE_SHARD_*.csv"))
    recs=sorted(ROOT.rglob("ETH_BLOCKSPACE_SOURCE_SHARD_*_RECEIPT.json"))
    if len(csvs)!=8 or len(recs)!=8:
        raise SystemExit(f"expected 8 shard csv/receipts, got {len(csvs)}/{len(recs)}")
    receipts=[json.loads(p.read_text()) for p in recs]
    protected=any(r.get("protected_period_accessed") for r in receipts)
    market=any(r.get("market_prices_opened") for r in receipts)
    returns=any(r.get("returns_opened") for r in receipts)
    pnl=any(r.get("pnl_opened") for r in receipts)
    rows=[]
    for p in csvs:
        with p.open("r",encoding="utf-8",newline="") as f:
            for x in csv.DictReader(f):
                rows.append({
                    "global_index":int(x["global_index"]),"block_number":int(x["block_number"]),"block_hash":x["block_hash"],
                    "parent_hash":x["parent_hash"],"timestamp":int(x["timestamp"]),"gas_limit":int(x["gas_limit"]),
                    "gas_used":int(x["gas_used"]),"base_fee_per_gas":int(x["base_fee_per_gas"]),
                    "assigned_provider":x["assigned_provider"],"provider_used":x["provider_used"],
                    "fallback_used":x["fallback_used"].lower()=="true","audit_required":x["audit_required"].lower()=="true",
                    "audit_pass":(None if x["audit_pass"] in ("","None") else x["audit_pass"].lower()=="true"),
                    "gas_utilization":float(x["gas_utilization"]),
                    "sample_block_base_fee_burn_wei":int(x["sample_block_base_fee_burn_wei"])
                })
    rows.sort(key=lambda x:x["global_index"])
    idx=[r["global_index"] for r in rows]; blocks=[r["block_number"] for r in rows]
    duplicate_indices=len(idx)-len(set(idx)); duplicate_blocks=len(blocks)-len(set(blocks))
    coverage=len(rows)/EXPECTED_TARGETS
    audits=[r for r in rows if r["audit_required"]]
    audit_pass=sum(1 for r in audits if r["audit_pass"] is True)
    protected_rows=sum(1 for r in rows if r["timestamp"]>=CUTOFF)

    rawp=OUT/"ETH_BLOCKSPACE_DEMAND_001_SAMPLED_BLOCKS_V0_2A.csv"
    fields=list(rows[0].keys()) if rows else []
    with rawp.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

    byday=defaultdict(list)
    for r in rows:
        d=datetime.fromtimestamp(r["timestamp"],tz=timezone.utc).date().isoformat()
        byday[d].append(r)
    dates=sorted(byday)
    daily=[]
    excluded=[]
    for d in dates:
        xs=byday[d]
        if len(xs)<3:
            excluded.append({"date":d,"sample_count":len(xs)});continue
        util=[r["gas_utilization"] for r in xs]
        fees=[r["base_fee_per_gas"]/1e9 for r in xs]
        burns=[r["sample_block_base_fee_burn_wei"]/1e18 for r in xs]
        daily.append({"date":d,"sample_count":len(xs),"mean_gas_utilization":sum(util)/len(util),
                      "median_base_fee_gwei":statistics.median(fees),
                      "mean_sample_block_base_fee_burn_eth":sum(burns)/len(burns),
                      "max_sample_block_base_fee_burn_eth":max(burns)})
    dailyp=OUT/"ETH_BLOCKSPACE_DEMAND_001_DAILY_SOURCE_SERIES_V0_2A.csv"
    dfields=["date","sample_count","mean_gas_utilization","median_base_fee_gwei","mean_sample_block_base_fee_burn_eth","max_sample_block_base_fee_burn_eth"]
    with dailyp.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=dfields);w.writeheader();w.writerows(daily)

    if dates:
        d0=datetime.fromisoformat(dates[0]).date();d1=datetime.fromisoformat(dates[-1]).date()
        calendar_days=(d1-d0).days+1
    else: calendar_days=0
    daily_retention=(len(daily)/calendar_days) if calendar_days else 0.0
    gates={
      "shard_count_8":len(recs)==8,
      "coverage_ge_99_5pct":coverage>=0.995,
      "all_cross_audits_present":len(audits)==EXPECTED_AUDITS,
      "all_cross_audits_pass":len(audits)==EXPECTED_AUDITS and audit_pass==EXPECTED_AUDITS,
      "no_duplicate_indices":duplicate_indices==0,
      "no_duplicate_blocks":duplicate_blocks==0,
      "no_protected_period":not protected and protected_rows==0,
      "daily_retention_ge_95pct":daily_retention>=0.95,
      "market_prices_closed":not market,
      "returns_closed":not returns,
      "pnl_closed":not pnl
    }
    status="SOURCE_DATA_PASS" if all(gates.values()) else ("PROVENANCE_FAILURE" if protected or protected_rows else "SOURCE_DATA_FAILURE")
    receipt={"lab_id":LAB,"status":status,"grid":{"expected_targets":EXPECTED_TARGETS,"accepted_rows":len(rows),"coverage":coverage,
                 "first_block":rows[0]["block_number"] if rows else None,"last_block":rows[-1]["block_number"] if rows else None,
                 "first_timestamp":rows[0]["timestamp"] if rows else None,"last_timestamp":rows[-1]["timestamp"] if rows else None},
             "cross_provider_audit":{"expected":EXPECTED_AUDITS,"present":len(audits),"pass":audit_pass},
             "duplicates":{"global_index":duplicate_indices,"block_number":duplicate_blocks},
             "daily":{"calendar_days_between_first_last_sample":calendar_days,"represented_dates":len(dates),
                      "canonical_days":len(daily),"excluded_lt3_samples":excluded,"retention":daily_retention},
             "fallback_count":sum(int(r.get("fallback_count",0)) for r in receipts),
             "shard_error_count":sum(int(r.get("error_count",0)) for r in receipts),
             "gates":gates,
             "artifacts":{"sampled_blocks_sha256":sha(rawp),"daily_series_sha256":sha(dailyp)},
             "safety":{"protected_period_accessed":protected or protected_rows>0,"market_prices_opened":market,
                       "returns_opened":returns,"pnl_opened":pnl,"live_trading":False,"orders":False,
                       "exchange_mutation":False,"merge_main":False}}
    recp=OUT/"ETH_BLOCKSPACE_DEMAND_001_FULL_SOURCE_DATA_GATE_V0_2A_RECEIPT.json"
    recp.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"status":status,"accepted_rows":len(rows),"coverage":coverage,"cross_audit_pass":audit_pass,
                      "canonical_days":len(daily),"calendar_days":calendar_days,"daily_retention":daily_retention,
                      "fallback_count":receipt["fallback_count"],"shard_error_count":receipt["shard_error_count"],
                      "protected_period_accessed":receipt["safety"]["protected_period_accessed"],
                      "market_prices_opened":market,"returns_opened":returns,"pnl_opened":pnl},sort_keys=True))
    return 0 if status=="SOURCE_DATA_PASS" else 2

if __name__=="__main__":sys.exit(main())
