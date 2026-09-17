#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 oracle bootstrap provenance V0.2.1.

Identity-corrected rerun after provider-address erratum. Source-only/outcome-blind.
Accepted registry routes remain frozen from V0.2:
  1) PriceOracleUpdated(old,new)
  2) AddressSet(bytes32('PRICE_ORACLE'),old,new)
No HF, overhang, future liquidation outcome, market return or PnL.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
PROVIDER = "0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
EXPECTED_ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"
PROVIDER_CREATION_BLOCK = 16_291_071
ORACLE_CREATION_BLOCK = 16_291_123
ACTIVATION_BLOCK = 16_496_792
SAMPLE_FROM = 16_490_000
SAMPLE_TO = 21_525_890
MAX_TS = 1_735_689_599
TRANSIENT = {429, 500, 502, 503, 504, 529}
WINDOW = 25_000


def topic(sig: str) -> str:
    return "0x" + keccak(sig.encode()).hex()

T_PRICE_ORACLE_UPDATED = topic("PriceOracleUpdated(address,address)")
T_ADDRESS_SET = topic("AddressSet(bytes32,address,address)")
T_RESERVE_INITIALIZED = topic("ReserveInitialized(address,address,address,address,address)")
T_ASSET_SOURCE_UPDATED = topic("AssetSourceUpdated(address,address)")
T_FALLBACK_ORACLE_UPDATED = topic("FallbackOracleUpdated(address)")
T_BASE_CURRENCY_SET = topic("BaseCurrencySet(address,uint256)")
PRICE_ORACLE_ID = "0x" + b"PRICE_ORACLE".ljust(32, b"\x00").hex()


def addr_from_topic(t: str) -> str:
    if not isinstance(t, str) or len(t) != 66:
        raise ValueError(f"bad address topic length={len(t) if isinstance(t,str) else 'n/a'}")
    return "0x" + t[-40:].lower()


def post(body: dict[str, Any], stats: Counter) -> requests.Response:
    last = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL, json=body, timeout=(20, 180), stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/oracle-bootstrap-v0.2.1"},
            )
            stats["http_attempts"] += 1
            if r.status_code in TRANSIENT:
                last = RuntimeError(f"transient HTTP {r.status_code}")
                r.close()
                if attempt < 7:
                    stats["transient_retries"] += 1
                    time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                    continue
                raise last
            r.raise_for_status()
            stats["successful_http_responses"] += 1
            return r
        except (requests.RequestException, RuntimeError) as exc:
            last = exc
            if attempt < 7:
                stats["network_retries"] += 1
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
            raise
    raise RuntimeError(str(last))


def query_logs(start: int, end: int, filters: list[dict[str, Any]], fields: dict[str, bool], stats: Counter):
    """Fixed-window sparse-safe SQD query. Empty windows are valid and advance deterministically."""
    cursor = start
    while cursor <= end:
        request_to = min(end, cursor + WINDOW - 1)
        body = {
            "type": "evm",
            "fromBlock": cursor,
            "toBlock": request_to,
            "fields": {"block": {"number": True, "timestamp": True}, "log": fields},
            "logs": filters,
        }
        r = post(body, stats)
        last = None
        rows = 0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                h = obj.get("header") or obj.get("block") or {}
                bn = int(h["number"])
                ts = int(h["timestamp"])
                if not (cursor <= bn <= request_to):
                    raise RuntimeError("row outside fixed request window")
                if ts > MAX_TS:
                    raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
                if last is not None and bn < last:
                    raise RuntimeError("non-monotonic SQD rows")
                last = bn
                rows += 1
                yield obj
        finally:
            r.close()
        stats["portal_rows"] += rows
        stats["fixed_windows"] += 1
        stats["empty_fixed_windows"] += int(rows == 0)
        cursor = request_to + 1


def event_order(row: dict[str, Any]):
    li = row.get("logIndex")
    if isinstance(li, str):
        li = int(li, 16) if li.startswith("0x") else int(li)
    return (int(row["block"]), str(row.get("transactionHash") or ""), int(li or 0))


def provider_transitions(stats: Counter) -> list[dict[str, Any]]:
    fields = {"address":True,"topics":True,"transactionHash":True,"logIndex":True}
    filters = [
        {"address":[PROVIDER],"topic0":[T_PRICE_ORACLE_UPDATED]},
        {"address":[PROVIDER],"topic0":[T_ADDRESS_SET],"topic1":[PRICE_ORACLE_ID]},
    ]
    rows = []
    for obj in query_logs(PROVIDER_CREATION_BLOCK, ACTIVATION_BLOCK, filters, fields, stats):
        bn = int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics = [str(x).lower() for x in (log.get("topics") or [])]
            if not topics:
                raise RuntimeError("provider transition missing topic0")
            if topics[0] == T_PRICE_ORACLE_UPDATED:
                if len(topics) < 3:
                    raise RuntimeError("PriceOracleUpdated ABI mismatch")
                route = "PriceOracleUpdated"
                old = addr_from_topic(topics[1]); new = addr_from_topic(topics[2])
            elif topics[0] == T_ADDRESS_SET:
                if len(topics) < 4 or topics[1] != PRICE_ORACLE_ID:
                    raise RuntimeError("AddressSet PRICE_ORACLE ABI/filter mismatch")
                route = "AddressSet"
                old = addr_from_topic(topics[2]); new = addr_from_topic(topics[3])
            else:
                raise RuntimeError("unexpected provider transition")
            rows.append({
                "block":bn,"route":route,"old":old,"new":new,
                "transactionHash":str(log.get("transactionHash") or "").lower(),
                "logIndex":log.get("logIndex"),
            })
    return sorted(rows, key=event_order)


def first_reserve_initialized(stats: Counter) -> dict[str, Any]:
    fields = {"address":True,"topics":True,"transactionHash":True,"logIndex":True}
    filters = [{"address":[CONFIGURATOR],"topic0":[T_RESERVE_INITIALIZED]}]
    rows = []
    for obj in query_logs(SAMPLE_FROM, ACTIVATION_BLOCK, filters, fields, stats):
        bn = int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            rows.append({"block":bn,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")})
    if not rows:
        raise RuntimeError("first ReserveInitialized not recovered through frozen activation block")
    return sorted(rows, key=event_order)[0]


def oracle_config(stats: Counter) -> tuple[Counter, list[dict[str, Any]], str]:
    names = {
        T_ASSET_SOURCE_UPDATED:"AssetSourceUpdated",
        T_FALLBACK_ORACLE_UPDATED:"FallbackOracleUpdated",
        T_BASE_CURRENCY_SET:"BaseCurrencySet",
    }
    fields = {"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
    filters = [{"address":[EXPECTED_ORACLE],"topic0":list(names)}]
    counts = Counter(); rows = []; h = hashlib.sha256()
    for obj in query_logs(ORACLE_CREATION_BLOCK, ACTIVATION_BLOCK, filters, fields, stats):
        bn = int((obj.get("header") or obj["block"])["number"])
        for log in obj.get("logs") or []:
            topics = [str(x).lower() for x in (log.get("topics") or [])]
            if not topics or topics[0] not in names:
                raise RuntimeError("unexpected oracle config log")
            name = names[topics[0]]
            row = {"block":bn,"event":name,"transactionHash":str(log.get("transactionHash") or "").lower(),"logIndex":log.get("logIndex")}
            if name == "AssetSourceUpdated":
                if len(topics) < 3: raise RuntimeError("AssetSourceUpdated ABI mismatch")
                row["asset"] = addr_from_topic(topics[1]); row["source"] = addr_from_topic(topics[2])
            counts[name] += 1
            rows.append(row)
            h.update(json.dumps(row, sort_keys=True, separators=(",",":")).encode() + b"\n")
    return counts, sorted(rows, key=event_order), h.hexdigest()


def main() -> int:
    stats = Counter(); failure = None
    transitions = []; activation = None; counts = Counter(); oracle_rows = []; oracle_hash = None; active = None
    try:
        activation = first_reserve_initialized(stats)
        if int(activation["block"]) != ACTIVATION_BLOCK:
            raise RuntimeError(f"activation block changed: {activation['block']} != {ACTIVATION_BLOCK}")
        transitions = provider_transitions(stats)
        if not transitions:
            classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
            failure = "no canonical PRICE_ORACLE registry transition recovered using corrected provider identity"
        else:
            active = transitions[-1]["new"].lower()
            counts, oracle_rows, oracle_hash = oracle_config(stats)
            if active != EXPECTED_ORACLE:
                classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
                failure = f"active oracle at activation {active} != frozen expected {EXPECTED_ORACLE}"
            elif counts.get("AssetSourceUpdated",0) < 1 or counts.get("BaseCurrencySet",0) < 1:
                classification = "RECONSTRUCTION_INSUFFICIENT_COVERAGE"
                failure = "required oracle bootstrap configuration events not recovered"
            else:
                classification = "ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_1"
    except Exception as exc:
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1200]}"

    receipt = {
        "lab_id":LAB_ID,
        "phase":"ORACLE_BOOTSTRAP_PROVENANCE_V0_2_1_OUTCOME_BLIND",
        "classification":classification,
        "identity_erratum_applied":True,
        "corrected_provider":PROVIDER,
        "provider_creation_block":PROVIDER_CREATION_BLOCK,
        "first_reserve_initialized":activation,
        "provider_oracle_registry_transitions":transitions,
        "active_oracle_at_activation":active,
        "expected_oracle":EXPECTED_ORACLE,
        "oracle_bootstrap_event_counts":dict(sorted(counts.items())),
        "oracle_bootstrap_events":oracle_rows,
        "oracle_bootstrap_sha256":oracle_hash,
        "transport_stats":dict(stats),
        "failure":failure,
        "safety":{
            "protocol_configuration_values_decoded":True,
            "health_factor_computed":False,"overhang_computed":False,
            "future_liquidation_outcome_computed":False,"market_return_prices_opened":False,
            "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
            "live_trading":False,"exchange_mutation":False,
        },
    }
    out = Path("oracle_bootstrap_v021_output"); out.mkdir(parents=True, exist_ok=True)
    (out/"AAVE_LIQUIDATION_OVERHANG_001_ORACLE_BOOTSTRAP_RECEIPT_V0_2_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "corrected_provider":PROVIDER,
        "transition_count":len(transitions),
        "routes":dict(Counter(x["route"] for x in transitions)),
        "active_oracle_at_activation":active,
        "oracle_bootstrap_event_counts":dict(counts),
        "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False,
    }, sort_keys=True))
    return 0 if classification == "ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_1" else 2

if __name__ == "__main__":
    sys.exit(main())
