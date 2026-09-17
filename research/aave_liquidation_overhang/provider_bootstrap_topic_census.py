#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 PoolAddressesProvider bootstrap topic census.

Transport/provenance diagnostic only. Requests no log.data and decodes no economic values,
prices, health factors, overhang, outcomes, returns or PnL.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from eth_hash.auto import keccak
import reconstruction_preflight as rp

LAB_ID = rp.LAB_ID
PROVIDER = rp.PROVIDER
FROM_BLOCK = 16_291_071
TO_BLOCK = 16_489_999

KNOWN_SIGS = {
    "MarketIdSet": "MarketIdSet(string,string)",
    "PoolUpdated": "PoolUpdated(address,address)",
    "PoolConfiguratorUpdated": "PoolConfiguratorUpdated(address,address)",
    "PriceOracleUpdated": "PriceOracleUpdated(address,address)",
    "ACLManagerUpdated": "ACLManagerUpdated(address,address)",
    "ACLAdminUpdated": "ACLAdminUpdated(address,address)",
    "PriceOracleSentinelUpdated": "PriceOracleSentinelUpdated(address,address)",
    "PoolDataProviderUpdated": "PoolDataProviderUpdated(address,address)",
    "AddressSet": "AddressSet(bytes32,address,address)",
    "AddressSetAsProxy": "AddressSetAsProxy(bytes32,address,address,address)",
    "ProxyCreated": "ProxyCreated(bytes32,address,address)",
    "OwnershipTransferred": "OwnershipTransferred(address,address)",
}
TOPIC_TO_NAME = {"0x" + keccak(sig.encode()).hex(): name for name, sig in KNOWN_SIGS.items()}


def main() -> int:
    stats=Counter(); counts=Counter(); examples=defaultdict(list); h=hashlib.sha256(); failure=None
    try:
        # No topic0 filter: enumerate every provider log in the bootstrap provenance envelope.
        filters=[{"address":[PROVIDER]}]
        fields={"address":True,"topics":True,"transactionHash":True,"logIndex":True}
        for obj in rp.stream_query(FROM_BLOCK,TO_BLOCK,filters,fields,stats):
            bn=int((obj.get("header") or obj["block"])["number"])
            for log in obj.get("logs") or []:
                topics=[str(x).lower() for x in (log.get("topics") or [])]
                if not topics:
                    raise RuntimeError("provider log missing topic0")
                t0=topics[0]
                name=TOPIC_TO_NAME.get(t0, "UNKNOWN:"+t0)
                counts[name]+=1
                if len(examples[name])<5:
                    examples[name].append({"block":bn,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex"),"topics_count":len(topics)})
                h.update(f"{bn}|{log.get('transactionHash')}|{log.get('logIndex')}|{t0}\n".encode())
        classification="PROVIDER_TOPIC_CENSUS_PASS" if sum(counts.values())>0 else "RECONSTRUCTION_INSUFFICIENT_COVERAGE"
    except Exception as exc:
        classification="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure=f"{type(exc).__name__}: {str(exc)[:1000]}"

    receipt={
        "lab_id":LAB_ID,
        "phase":"PROVIDER_BOOTSTRAP_TOPIC_CENSUS_OUTCOME_BLIND",
        "classification":classification,
        "from_block":FROM_BLOCK,
        "to_block":TO_BLOCK,
        "provider":PROVIDER,
        "event_counts":dict(sorted(counts.items())),
        "event_examples":dict(examples),
        "structural_sha256":h.hexdigest(),
        "expected_price_oracle_topic":"0x"+keccak(KNOWN_SIGS["PriceOracleUpdated"].encode()).hex(),
        "transport_stats":dict(stats),
        "failure":failure,
        "safety":{
            "log_data_requested":False,
            "protocol_economic_values_decoded":False,
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
    out=Path("provider_topic_census_output"); out.mkdir(parents=True,exist_ok=True)
    (out/"AAVE_LIQUIDATION_OVERHANG_001_PROVIDER_BOOTSTRAP_TOPIC_CENSUS_V0_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"total_provider_logs":sum(counts.values()),"event_counts":dict(counts),"price_oracle_updated_present":counts.get("PriceOracleUpdated",0)>0,"health_factor_computed":False,"overhang_computed":False},sort_keys=True))
    return 0 if classification=="PROVIDER_TOPIC_CENSUS_PASS" else 2

if __name__=="__main__":
    sys.exit(main())
