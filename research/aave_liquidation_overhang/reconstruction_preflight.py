#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 reconstruction R0 preflight.

Activated only after SOURCE_CENSUS_PASS.
Allowed under the frozen reconstruction authority:
- decode historical protocol-source values needed to prove reconstruction feasibility;
- enumerate reserve/token addresses, configuration/upgrades and Borrow rate modes;
- inspect deterministic token-event windows and provider/oracle provenance.

Still forbidden and not performed:
- health factor;
- liquidation-distance / overhang predictor;
- any future liquidation outcome;
- market returns / PnL;
- 2025/2026.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
PROVIDER = "0x2f39d218133afb8f2b819b1066c7e434ad94e9e"
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
MAX_TS = 1_735_689_599
MAX_HTTP_WINDOW = 100_000
TRANSIENT = {429,500,502,503,504,529}

# Deterministic token-event schema windows selected before seeing token-event payloads.
TOKEN_PROBE_WINDOWS = [
    (16_490_000, 16_520_000),
    (18_000_000, 18_030_000),
    (19_500_000, 19_530_000),
    (21_450_000, 21_480_000),
]

SIG = {
    # Configurator / reserve identity and configuration
    "ReserveInitialized": "ReserveInitialized(address,address,address,address,address)",
    "ATokenUpgraded": "ATokenUpgraded(address,address,address)",
    "StableDebtTokenUpgraded": "StableDebtTokenUpgraded(address,address,address)",
    "VariableDebtTokenUpgraded": "VariableDebtTokenUpgraded(address,address,address)",
    "ReserveBorrowing": "ReserveBorrowing(address,bool)",
    "ReserveStableRateBorrowing": "ReserveStableRateBorrowing(address,bool)",
    "ReserveActive": "ReserveActive(address,bool)",
    "ReserveFrozen": "ReserveFrozen(address,bool)",
    "ReservePaused": "ReservePaused(address,bool)",
    "CollateralConfigurationChanged": "CollateralConfigurationChanged(address,uint256,uint256,uint256)",
    "ReserveFactorChanged": "ReserveFactorChanged(address,uint256,uint256)",
    "BorrowCapChanged": "BorrowCapChanged(address,uint256,uint256)",
    "SupplyCapChanged": "SupplyCapChanged(address,uint256,uint256)",
    "DebtCeilingChanged": "DebtCeilingChanged(address,uint256,uint256)",
    "EModeCategoryAdded": "EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)",
    # Provider provenance
    "PoolUpdated": "PoolUpdated(address,address)",
    "PoolConfiguratorUpdated": "PoolConfiguratorUpdated(address,address)",
    "PriceOracleUpdated": "PriceOracleUpdated(address,address)",
    "ProxyCreated": "ProxyCreated(bytes32,address,address)",
    "AddressSetAsProxy": "AddressSetAsProxy(bytes32,address,address,address)",
    # Pool mode audit
    "Borrow": "Borrow(address,address,address,uint256,uint8,uint256,uint16)",
    # token replay primitives
    "BalanceTransfer": "BalanceTransfer(address,address,uint256,uint256)",
    "Mint": "Mint(address,address,uint256,uint256,uint256)",
    "Burn": "Burn(address,address,uint256,uint256,uint256)",
    # oracle-source mapping (queried only if oracle addresses are recovered)
    "AssetSourceUpdated": "AssetSourceUpdated(address,address)",
    "FallbackOracleUpdated": "FallbackOracleUpdated(address)",
    "BaseCurrencySet": "BaseCurrencySet(address,uint256)",
}
TOPIC = {name: "0x" + keccak(sig.encode()).hex() for name,sig in SIG.items()}


def word_bytes(data: str) -> list[bytes]:
    if not isinstance(data,str) or not data.startswith("0x"):
        raise ValueError("bad event data")
    b=bytes.fromhex(data[2:])
    if len(b)%32:
        raise ValueError("non-word-aligned event data")
    return [b[i:i+32] for i in range(0,len(b),32)]


def addr_from_word(w: bytes) -> str:
    if len(w)!=32: raise ValueError("bad word")
    return "0x"+w[-20:].hex()


def addr_from_topic(t: str) -> str:
    if not isinstance(t,str) or len(t)!=66: raise ValueError("bad address topic")
    return "0x"+t[-40:].lower()


def uint_word(w: bytes) -> int:
    return int.from_bytes(w,"big")


def post(body: dict[str,Any], stats: Counter) -> requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/reconstruction-preflight-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}")
                ra=r.headers.get("Retry-After")
                r.close()
                if attempt<7:
                    stats["transient_retries"]+=1
                    try: delay=float(ra) if ra else min(20.0,1.5*(2**attempt))
                    except ValueError: delay=min(20.0,1.5*(2**attempt))
                    time.sleep(delay); continue
                raise last
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except (requests.RequestException,RuntimeError) as exc:
            last=exc
            if attempt<7:
                stats["network_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))


def stream_query(start:int,end:int,logs_filters:list[dict[str,Any]],fields_log:dict[str,bool],stats:Counter):
    cursor=start
    while cursor<=end:
        request_to=min(end,cursor+MAX_HTTP_WINDOW-1)
        body={
            "type":"evm","fromBlock":cursor,"toBlock":request_to,
            "fields":{"block":{"number":True,"timestamp":True},"log":fields_log},
            "logs":logs_filters,
        }
        r=post(body,stats); last=None; rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                h=obj.get("header") or obj.get("block") or {}
                bn=int(h["number"]); ts=int(h["timestamp"])
                if not (cursor<=bn<=request_to): raise RuntimeError("row outside request window")
                if ts>MAX_TS: raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
                if last is not None and bn<last: raise RuntimeError("non-monotonic Portal rows")
                last=bn; rows+=1; yield obj
        finally:
            r.close()
        if not rows or last is None: raise RuntimeError("empty Portal page inside frozen range")
        stats["portal_rows"]+=rows
        cursor=last+1


def collect_rare_source(stats:Counter):
    config_names=[
        "ReserveInitialized","ATokenUpgraded","StableDebtTokenUpgraded","VariableDebtTokenUpgraded",
        "ReserveBorrowing","ReserveStableRateBorrowing","ReserveActive","ReserveFrozen","ReservePaused",
        "CollateralConfigurationChanged","ReserveFactorChanged","BorrowCapChanged","SupplyCapChanged",
        "DebtCeilingChanged","EModeCategoryAdded",
    ]
    provider_names=["PoolUpdated","PoolConfiguratorUpdated","PriceOracleUpdated","ProxyCreated","AddressSetAsProxy"]
    t2n={TOPIC[n]:n for n in config_names+provider_names}
    counts=Counter(); reserves={}; provider_transitions=defaultdict(list); hashes=hashlib.sha256()
    filters=[
        {"address":[CONFIGURATOR],"topic0":[TOPIC[n] for n in config_names]},
        {"address":[PROVIDER],"topic0":[TOPIC[n] for n in provider_names]},
    ]
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    for obj in stream_query(FROM_BLOCK,TO_BLOCK,filters,fields,stats):
        bn=int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics=[str(x).lower() for x in (log.get("topics") or [])]
            if not topics: raise RuntimeError("rare source log missing topic0")
            name=t2n.get(topics[0]);
            if not name: raise RuntimeError("unexpected rare source topic")
            counts[name]+=1
            data=word_bytes(log.get("data") or "0x")
            if name=="ReserveInitialized":
                if len(topics)<3 or len(data)<3: raise RuntimeError("ReserveInitialized ABI mismatch")
                asset=addr_from_topic(topics[1]); atoken=addr_from_topic(topics[2])
                stable=addr_from_word(data[0]); variable=addr_from_word(data[1]); strategy=addr_from_word(data[2])
                reserves[asset]={"aToken":atoken,"stableDebtToken":stable,"variableDebtToken":variable,
                                 "interestRateStrategy":strategy,"init_block":bn}
            elif name in ("PoolUpdated","PoolConfiguratorUpdated","PriceOracleUpdated"):
                if len(topics)<3: raise RuntimeError(f"{name} ABI mismatch")
                provider_transitions[name].append({"block":bn,"old":addr_from_topic(topics[1]),"new":addr_from_topic(topics[2])})
            hashes.update(f"{bn}|{log.get('transactionHash')}|{log.get('logIndex')}|{name}\n".encode())
    return counts,reserves,provider_transitions,hashes.hexdigest()


def audit_borrow_modes(stats:Counter):
    counts=Counter(); examples={}
    filters=[{"address":[POOL],"topic0":[TOPIC["Borrow"]]}]
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    total=0
    for obj in stream_query(FROM_BLOCK,TO_BLOCK,filters,fields,stats):
        for log in obj.get("logs") or []:
            w=word_bytes(log.get("data") or "0x")
            # non-indexed: user, amount, interestRateMode, borrowRate
            if len(w)<4: raise RuntimeError("Borrow ABI mismatch")
            mode=uint_word(w[2]); counts[str(mode)]+=1; total+=1
            examples.setdefault(str(mode),{"tx":log.get("transactionHash"),"logIndex":log.get("logIndex")})
    return total,dict(counts),examples


def probe_token_primitives(reserves:dict[str,dict[str,Any]],stats:Counter):
    atokens=sorted({x["aToken"] for x in reserves.values() if int(x["aToken"],16)!=0})
    vdebts=sorted({x["variableDebtToken"] for x in reserves.values() if int(x["variableDebtToken"],16)!=0})
    counts=Counter(); bad=0
    t2n={TOPIC["BalanceTransfer"]:"aToken_BalanceTransfer",TOPIC["Mint"]:"Mint",TOPIC["Burn"]:"Burn"}
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    for a,b in TOKEN_PROBE_WINDOWS:
        filters=[
            {"address":atokens,"topic0":[TOPIC["BalanceTransfer"],TOPIC["Mint"],TOPIC["Burn"]]},
            {"address":vdebts,"topic0":[TOPIC["Mint"],TOPIC["Burn"]]},
        ]
        for obj in stream_query(a,b,filters,fields,stats):
            for log in obj.get("logs") or []:
                addr=str(log.get("address") or "").lower(); t0=str((log.get("topics") or [""])[0]).lower()
                if addr in atokens and t0==TOPIC["BalanceTransfer"]:
                    name="aToken_BalanceTransfer"
                    if len(word_bytes(log.get("data") or "0x"))!=2: bad+=1
                elif addr in atokens and t0 in (TOPIC["Mint"],TOPIC["Burn"]):
                    name="aToken_"+("Mint" if t0==TOPIC["Mint"] else "Burn")
                    if len(word_bytes(log.get("data") or "0x"))!=3: bad+=1
                elif addr in vdebts and t0 in (TOPIC["Mint"],TOPIC["Burn"]):
                    name="vDebt_"+("Mint" if t0==TOPIC["Mint"] else "Burn")
                    if len(word_bytes(log.get("data") or "0x"))!=3: bad+=1
                else:
                    raise RuntimeError("unexpected token primitive")
                counts[name]+=1
    return {"aToken_count":len(atokens),"variableDebtToken_count":len(vdebts),
            "event_counts":dict(counts),"abi_shape_failures":bad,"probe_windows":TOKEN_PROBE_WINDOWS}


def probe_oracle_events(provider_transitions:dict[str,list[dict[str,Any]]],stats:Counter):
    oracles=[]
    for x in provider_transitions.get("PriceOracleUpdated",[]):
        if int(x["new"],16)!=0: oracles.append(x["new"])
    oracles=sorted(set(oracles))
    if not oracles:
        return {"oracle_addresses_from_provider_events":[],"status":"BOOTSTRAP_ORACLE_ADDRESS_NOT_RECOVERED_FROM_FROZEN_WINDOW",
                "event_counts":{}}
    names=["AssetSourceUpdated","FallbackOracleUpdated","BaseCurrencySet"]
    t2n={TOPIC[n]:n for n in names}; counts=Counter()
    filters=[{"address":oracles,"topic0":[TOPIC[n] for n in names]}]
    fields={"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    for obj in stream_query(FROM_BLOCK,TO_BLOCK,filters,fields,stats):
        for log in obj.get("logs") or []:
            ts=log.get("topics") or []
            if not ts: raise RuntimeError("oracle log missing topic0")
            n=t2n.get(str(ts[0]).lower())
            if not n: raise RuntimeError("unexpected oracle event")
            counts[n]+=1
    return {"oracle_addresses_from_provider_events":oracles,"status":"EVENT_ROUTE_RECOVERED",
            "event_counts":dict(counts)}


def main()->int:
    stats=Counter(); failure=None
    try:
        rare_counts,reserves,provider_transitions,rare_hash=collect_rare_source(stats)
        borrow_total,borrow_modes,borrow_examples=audit_borrow_modes(stats)
        token_probe=probe_token_primitives(reserves,stats)
        oracle_probe=probe_oracle_events(provider_transitions,stats)

        required_config=["ReserveInitialized","CollateralConfigurationChanged"]
        required_ok=all(rare_counts[x]>0 for x in required_config)
        mode_ok=(borrow_total>0 and set(borrow_modes).issubset({"2"}) and "2" in borrow_modes)
        token_ok=(token_probe["event_counts"].get("aToken_BalanceTransfer",0)>0 and
                  token_probe["event_counts"].get("aToken_Mint",0)>0 and
                  token_probe["event_counts"].get("aToken_Burn",0)>0 and
                  token_probe["event_counts"].get("vDebt_Mint",0)>0 and
                  token_probe["event_counts"].get("vDebt_Burn",0)>0 and
                  token_probe["abi_shape_failures"]==0)
        # Oracle event absence is not silently rescued: it becomes explicit bootstrap requirement.
        oracle_route_ok=(oracle_probe["status"]=="EVENT_ROUTE_RECOVERED")
        if not required_ok or len(reserves)<1:
            classification="RECONSTRUCTION_INSUFFICIENT_COVERAGE"
        elif not mode_ok:
            classification="RECONSTRUCTION_PROVENANCE_FAILURE"
        elif not token_ok:
            classification="RECONSTRUCTION_RECONCILIATION_FAILURE"
        elif not oracle_route_ok:
            classification="RECONSTRUCTION_BOOTSTRAP_SOURCE_REQUIRED"
        else:
            classification="RECONSTRUCTION_PREFLIGHT_PASS"
    except Exception as exc:
        classification="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"; failure=f"{type(exc).__name__}: {str(exc)[:800]}"
        rare_counts=Counter(); reserves={}; provider_transitions={}; rare_hash=None
        borrow_total=0; borrow_modes={}; borrow_examples={}; token_probe={}; oracle_probe={}

    receipt={
        "lab_id":LAB_ID,"phase":"RECONSTRUCTION_R0_PREFLIGHT_OUTCOME_BLIND","classification":classification,
        "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,"hard_timestamp_ceiling":MAX_TS,
        "config_provider_event_counts":dict(sorted(rare_counts.items())),"reserve_count":len(reserves),
        "reserves":reserves,"provider_transitions":provider_transitions,"rare_source_sha256":rare_hash,
        "borrow_event_count":borrow_total,"borrow_interest_rate_mode_counts":borrow_modes,
        "borrow_mode_examples":borrow_examples,"token_primitive_probe":token_probe,"oracle_probe":oracle_probe,
        "transport_stats":dict(stats),"failure":failure,
        "safety":{"source_values_decoded":True,"health_factor_computed":False,"overhang_computed":False,
                  "future_liquidation_outcome_computed":False,"market_return_prices_opened":False,
                  "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                  "live_trading":False,"exchange_mutation":False},
    }
    out=Path("reconstruction_output"); out.mkdir(parents=True,exist_ok=True)
    (out/"AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_PREFLIGHT_RECEIPT_V0_1.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"lab_id":LAB_ID,"classification":classification,"reserve_count":len(reserves),
                      "borrow_event_count":borrow_total,"borrow_interest_rate_modes":borrow_modes,
                      "token_event_counts":token_probe.get("event_counts",{}),
                      "oracle_status":oracle_probe.get("status"),"health_factor_computed":False,
                      "overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if classification=="RECONSTRUCTION_PREFLIGHT_PASS" else 2

if __name__=="__main__":
    sys.exit(main())
