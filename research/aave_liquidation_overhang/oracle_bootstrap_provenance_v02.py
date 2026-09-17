#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 oracle bootstrap provenance V0.2.

Prospective source-route remediation frozen before execution.
Accepted registry routes are strictly:
  1) PriceOracleUpdated(old,new); or
  2) AddressSet(id,old,new) where id == bytes32('PRICE_ORACLE').

No health factor, overhang, adverse-shock selection, future liquidation outcome,
market returns, PnL or 2025/2026 access.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from eth_hash.auto import keccak
import reconstruction_preflight as rp

LAB_ID = rp.LAB_ID
PROVIDER = rp.PROVIDER
CONFIGURATOR = rp.CONFIGURATOR
EXPECTED_ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"
PROVIDER_CREATION_BLOCK = 16_291_071
ORACLE_CREATION_BLOCK = 16_291_123
SAMPLE_FROM = 16_490_000
SAMPLE_TO = 21_525_890

PRICE_ORACLE_ID = "0x" + b"PRICE_ORACLE".ljust(32, b"\x00").hex()
ADDRESS_SET_TOPIC = "0x" + keccak(b"AddressSet(bytes32,address,address)").hex()
PRICE_ORACLE_UPDATED_TOPIC = rp.TOPIC["PriceOracleUpdated"]
RESERVE_INITIALIZED_TOPIC = rp.TOPIC["ReserveInitialized"]


def event_order_key(row: dict) -> tuple[int, str, int]:
    li = row.get("logIndex")
    if isinstance(li, str):
        li = int(li, 16) if li.startswith("0x") else int(li)
    return (int(row["block"]), str(row.get("transactionHash") or ""), int(li or 0))


def first_reserve_initialized(stats: Counter) -> dict:
    # The source census proved ReserveInitialized exists. Search only the first
    # 100k frozen blocks; fail closed if activation is not found there.
    fields={"address":True,"topics":True,"transactionHash":True,"logIndex":True}
    filters=[{"address":[CONFIGURATOR],"topic0":[RESERVE_INITIALIZED_TOPIC]}]
    found=[]
    for obj in rp.stream_query(SAMPLE_FROM, min(SAMPLE_TO, SAMPLE_FROM + 99_999), filters, fields, stats):
        bn=int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            found.append({"block":bn,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")})
    if not found:
        raise RuntimeError("first ReserveInitialized not recovered in frozen activation search window")
    return sorted(found,key=event_order_key)[0]


def provider_oracle_transitions(start: int, end: int, stats: Counter) -> list[dict]:
    fields={"address":True,"topics":True,"transactionHash":True,"logIndex":True}
    filters=[
        {"address":[PROVIDER],"topic0":[PRICE_ORACLE_UPDATED_TOPIC]},
        {"address":[PROVIDER],"topic0":[ADDRESS_SET_TOPIC],"topic1":[PRICE_ORACLE_ID]},
    ]
    rows=[]
    for obj in rp.stream_query(start,end,filters,fields,stats):
        bn=int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics=[str(x).lower() for x in (log.get("topics") or [])]
            if not topics:
                raise RuntimeError("provider transition missing topic0")
            t0=topics[0]
            if t0 == PRICE_ORACLE_UPDATED_TOPIC:
                if len(topics)<3:
                    raise RuntimeError("PriceOracleUpdated ABI mismatch")
                route="PriceOracleUpdated"
                old=rp.addr_from_topic(topics[1]); new=rp.addr_from_topic(topics[2])
                registry_id=PRICE_ORACLE_ID
            elif t0 == ADDRESS_SET_TOPIC:
                if len(topics)<4:
                    raise RuntimeError("AddressSet ABI mismatch")
                if topics[1] != PRICE_ORACLE_ID:
                    raise RuntimeError("non-PRICE_ORACLE AddressSet escaped exact topic1 filter")
                route="AddressSet"
                registry_id=topics[1]
                old=rp.addr_from_topic(topics[2]); new=rp.addr_from_topic(topics[3])
            else:
                raise RuntimeError("unexpected provider oracle transition topic")
            rows.append({
                "block":bn,"route":route,"registry_id":registry_id,"old":old,"new":new,
                "transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")
            })
    return sorted(rows,key=event_order_key)


def oracle_config_events(address: str, start: int, end: int, stats: Counter) -> tuple[Counter,list[dict],str]:
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
                raise RuntimeError("oracle config log missing topic0")
            name=t2n.get(topics[0])
            if not name:
                raise RuntimeError("unexpected oracle config topic")
            counts[name]+=1
            row={"block":bn,"event":name,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")}
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
    return counts,sorted(rows,key=event_order_key),h.hexdigest()


def main()->int:
    stats=Counter(); failure=None
    activation=None; transitions=[]; bootstrap_counts=Counter(); bootstrap_rows=[]; bootstrap_hash=None
    active_oracle=None
    try:
        activation=first_reserve_initialized(stats)
        activation_block=int(activation["block"])
        transitions=provider_oracle_transitions(PROVIDER_CREATION_BLOCK,activation_block,stats)
        if not transitions:
            classification="RECONSTRUCTION_PROVENANCE_FAILURE"
            failure="no canonical PRICE_ORACLE registry transition recovered by activation"
        else:
            active_oracle=transitions[-1]["new"].lower()
            if active_oracle != EXPECTED_ORACLE:
                classification="RECONSTRUCTION_PROVENANCE_FAILURE"
                failure=f"active oracle at first ReserveInitialized {active_oracle} != frozen canonical identity {EXPECTED_ORACLE}"
            else:
                bootstrap_counts,bootstrap_rows,bootstrap_hash=oracle_config_events(active_oracle,ORACLE_CREATION_BLOCK,activation_block,stats)
                required=(bootstrap_counts.get("AssetSourceUpdated",0)>0 and bootstrap_counts.get("BaseCurrencySet",0)>0)
                if not required:
                    classification="RECONSTRUCTION_INSUFFICIENT_COVERAGE"
                    failure="oracle bootstrap lacks required AssetSourceUpdated/BaseCurrencySet evidence by activation"
                else:
                    classification="ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2"
    except Exception as exc:
        classification="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure=f"{type(exc).__name__}: {str(exc)[:1200]}"

    receipt={
        "lab_id":LAB_ID,
        "phase":"ORACLE_BOOTSTRAP_PROVENANCE_V0_2_OUTCOME_BLIND",
        "classification":classification,
        "provider_creation_block":PROVIDER_CREATION_BLOCK,
        "oracle_creation_block":ORACLE_CREATION_BLOCK,
        "scientific_sample_from_block":SAMPLE_FROM,
        "scientific_sample_to_block":SAMPLE_TO,
        "price_oracle_registry_id":PRICE_ORACLE_ID,
        "frozen_expected_oracle":EXPECTED_ORACLE,
        "first_reserve_initialized":activation,
        "provider_oracle_registry_transitions_through_activation":transitions,
        "active_oracle_at_activation":active_oracle,
        "oracle_bootstrap_event_counts":dict(sorted(bootstrap_counts.items())),
        "oracle_bootstrap_events":bootstrap_rows,
        "oracle_bootstrap_sha256":bootstrap_hash,
        "transport_stats":dict(stats),
        "failure":failure,
        "safety":{
            "protocol_configuration_values_decoded":True,
            "oracle_price_observations_decoded":False,
            "health_factor_computed":False,"overhang_computed":False,
            "adverse_shock_selected":False,"future_liquidation_outcome_computed":False,
            "market_return_prices_opened":False,"returns_opened":False,"pnl_opened":False,
            "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False,
        },
    }
    out=Path("oracle_bootstrap_v02_output"); out.mkdir(parents=True,exist_ok=True)
    (out/"AAVE_LIQUIDATION_OVERHANG_001_ORACLE_BOOTSTRAP_RECEIPT_V0_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "first_reserve_initialized_block":None if not activation else activation["block"],
        "oracle_registry_transition_count":len(transitions),
        "oracle_registry_routes":dict(Counter(x["route"] for x in transitions)),
        "active_oracle_at_activation":active_oracle,
        "oracle_bootstrap_event_counts":dict(bootstrap_counts),
        "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False,
    },sort_keys=True))
    return 0 if classification=="ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2" else 2

if __name__=="__main__":
    sys.exit(main())
