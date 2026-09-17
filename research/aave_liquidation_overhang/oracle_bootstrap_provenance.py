#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 oracle bootstrap provenance recovery.

Narrow reconstruction-only remediation authorized prospectively.
No health factor, overhang, future liquidation outcome, market returns or PnL.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import reconstruction_preflight as rp

LAB_ID = rp.LAB_ID
PROVIDER = rp.PROVIDER
EXPECTED_ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"
BOOTSTRAP_FROM = 16_291_123
BOOTSTRAP_TO = 16_489_999
SAMPLE_FROM = 16_490_000
SAMPLE_TO = 21_525_890


def decode_provider_oracle_updates(start: int, end: int, stats: Counter) -> list[dict]:
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    filters=[{"address":[PROVIDER],"topic0":[rp.TOPIC["PriceOracleUpdated"]]}]
    rows=[]
    for obj in rp.stream_query(start,end,filters,fields,stats):
        bn=int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics=log.get("topics") or []
            if len(topics)<3:
                raise RuntimeError("PriceOracleUpdated ABI mismatch")
            rows.append({
                "block":bn,
                "old":rp.addr_from_topic(str(topics[1])),
                "new":rp.addr_from_topic(str(topics[2])),
                "transactionHash":str(log.get("transactionHash") or "").lower(),
                "logIndex":log.get("logIndex"),
            })
    return sorted(rows,key=lambda x:(x["block"],str(x["transactionHash"]),str(x["logIndex"])))


def oracle_events(address: str, start: int, end: int, stats: Counter) -> tuple[Counter,list[dict],str]:
    names=["AssetSourceUpdated","FallbackOracleUpdated","BaseCurrencySet"]
    t2n={rp.TOPIC[n]:n for n in names}
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    filters=[{"address":[address],"topic0":[rp.TOPIC[n] for n in names]}]
    counts=Counter(); rows=[]; h=hashlib.sha256()
    for obj in rp.stream_query(start,end,filters,fields,stats):
        bn=int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics=[str(x).lower() for x in (log.get("topics") or [])]
            if not topics:
                raise RuntimeError("oracle provenance log missing topic0")
            name=t2n.get(topics[0])
            if not name:
                raise RuntimeError("unexpected oracle provenance topic")
            counts[name]+=1
            row={"block":bn,"event":name,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")}
            # Configuration values are allowed at reconstruction stage. Decode only identity/configuration,
            # never price observations or market outcomes.
            if name=="AssetSourceUpdated":
                if len(topics)<3: raise RuntimeError("AssetSourceUpdated ABI mismatch")
                row["asset"]=rp.addr_from_topic(topics[1]); row["source"]=rp.addr_from_topic(topics[2])
            elif name=="FallbackOracleUpdated":
                if len(topics)<2: raise RuntimeError("FallbackOracleUpdated ABI mismatch")
                row["fallbackOracle"]=rp.addr_from_topic(topics[1])
            elif name=="BaseCurrencySet":
                if len(topics)<2: raise RuntimeError("BaseCurrencySet ABI mismatch")
                words=rp.word_bytes(log.get("data") or "0x")
                if len(words)<1: raise RuntimeError("BaseCurrencySet ABI mismatch")
                row["baseCurrency"]=rp.addr_from_topic(topics[1]); row["baseCurrencyUnit"]=rp.uint_word(words[0])
            rows.append(row)
            h.update(json.dumps(row,sort_keys=True,separators=(",",":")).encode()+b"\n")
    return counts,rows,h.hexdigest()


def main()->int:
    stats=Counter(); failure=None
    bootstrap_updates=[]; in_window_updates=[]; bootstrap_counts=Counter(); bootstrap_rows=[]; bootstrap_hash=None
    active_oracle=None
    try:
        bootstrap_updates=decode_provider_oracle_updates(BOOTSTRAP_FROM,BOOTSTRAP_TO,stats)
        if not bootstrap_updates:
            raise RuntimeError("no PriceOracleUpdated in frozen bootstrap provenance envelope")
        active_oracle=bootstrap_updates[-1]["new"].lower()
        if active_oracle != EXPECTED_ORACLE:
            classification="RECONSTRUCTION_PROVENANCE_FAILURE"
            failure=f"active boundary oracle {active_oracle} != frozen canonical identity {EXPECTED_ORACLE}"
        else:
            bootstrap_counts,bootstrap_rows,bootstrap_hash=oracle_events(active_oracle,BOOTSTRAP_FROM,BOOTSTRAP_TO,stats)
            # Also prove whether provider changes after sample start. This is provenance/config only.
            in_window_updates=decode_provider_oracle_updates(SAMPLE_FROM,SAMPLE_TO,stats)
            required=(bootstrap_counts.get("AssetSourceUpdated",0)>0 and bootstrap_counts.get("BaseCurrencySet",0)>0)
            if not required:
                classification="RECONSTRUCTION_INSUFFICIENT_COVERAGE"
                failure="bootstrap oracle route lacks required AssetSourceUpdated/BaseCurrencySet evidence"
            else:
                classification="ORACLE_BOOTSTRAP_PROVENANCE_PASS"
    except Exception as exc:
        classification="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure=f"{type(exc).__name__}: {str(exc)[:1000]}"

    receipt={
        "lab_id":LAB_ID,
        "phase":"ORACLE_BOOTSTRAP_PROVENANCE_OUTCOME_BLIND",
        "classification":classification,
        "bootstrap_from_block":BOOTSTRAP_FROM,
        "bootstrap_to_block":BOOTSTRAP_TO,
        "scientific_sample_from_block":SAMPLE_FROM,
        "scientific_sample_to_block":SAMPLE_TO,
        "frozen_expected_oracle":EXPECTED_ORACLE,
        "active_oracle_at_sample_left_boundary":active_oracle,
        "provider_bootstrap_price_oracle_updates":bootstrap_updates,
        "provider_in_window_price_oracle_updates":in_window_updates,
        "bootstrap_oracle_event_counts":dict(sorted(bootstrap_counts.items())),
        "bootstrap_oracle_events":bootstrap_rows,
        "bootstrap_oracle_sha256":bootstrap_hash,
        "transport_stats":dict(stats),
        "failure":failure,
        "safety":{
            "protocol_configuration_values_decoded":True,
            "oracle_price_observations_decoded":False,
            "health_factor_computed":False,
            "overhang_computed":False,
            "future_liquidation_outcome_computed":False,
            "market_return_prices_opened":False,
            "returns_opened":False,
            "pnl_opened":False,
            "accessed_2025_or_2026":False,
            "live_trading":False,
            "exchange_mutation":False,
        },
    }
    out=Path("oracle_bootstrap_output"); out.mkdir(parents=True,exist_ok=True)
    (out/"AAVE_LIQUIDATION_OVERHANG_001_ORACLE_BOOTSTRAP_RECEIPT_V0_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "active_oracle_at_sample_left_boundary":active_oracle,
        "bootstrap_provider_updates":len(bootstrap_updates),
        "bootstrap_oracle_event_counts":dict(bootstrap_counts),
        "in_window_provider_oracle_updates":len(in_window_updates),
        "health_factor_computed":False,
        "overhang_computed":False,
        "returns_opened":False,
        "pnl_opened":False,
    },sort_keys=True))
    return 0 if classification=="ORACLE_BOOTSTRAP_PROVENANCE_PASS" else 2


if __name__=="__main__":
    sys.exit(main())
