#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 historical state provenance V0.3.

Outcome-blind source remediation only. Queries exact historical Ethereum blocks to
prove PoolAddressesProvider oracle/pool/configurator state independently of SQD.
No health factor, overhang, future liquidation outcome, market return or PnL.
"""
from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PROVIDER = "0x2f39d218133afb8f2b819b1066c7e434ad94e9e"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"
ORACLE_CREATION_BLOCK = 16_291_123
PRE_ACTIVATION_BLOCK = 16_496_791
ACTIVATION_BLOCK = 16_496_792
MAX_ALLOWED_TS = 1_735_689_599

ENDPOINTS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.llamarpc.com",
    "https://1rpc.io/eth",
    "https://eth.drpc.org",
    "https://rpc.ankr.com/eth",
]


def topic(sig: str) -> str:
    return "0x" + keccak(sig.encode()).hex()


def selector(sig: str) -> str:
    return "0x" + keccak(sig.encode())[:4].hex()


SEL_PRICE_ORACLE = selector("getPriceOracle()")
SEL_POOL = selector("getPool()")
SEL_CONFIGURATOR = selector("getPoolConfigurator()")
T_RESERVE_INITIALIZED = topic("ReserveInitialized(address,address,address,address,address)")
T_ASSET_SOURCE_UPDATED = topic("AssetSourceUpdated(address,address)")
T_BASE_CURRENCY_SET = topic("BaseCurrencySet(address,uint256)")
T_PRICE_ORACLE_UPDATED = topic("PriceOracleUpdated(address,address)")
T_ADDRESS_SET = topic("AddressSet(bytes32,address,address)")
PRICE_ORACLE_ID = "0x" + b"PRICE_ORACLE".ljust(32, b"\x00").hex()


def hblock(n: int) -> str:
    return hex(n)


def as_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 16) if v.startswith("0x") else int(v)
    raise ValueError(f"cannot parse integer {v!r}")


def decode_address(v: str) -> str:
    if not isinstance(v, str) or not v.startswith("0x"):
        raise ValueError("bad eth_call result")
    raw = bytes.fromhex(v[2:])
    if len(raw) < 32:
        raise ValueError("short eth_call result")
    return "0x" + raw[-20:].hex()


def normalize_log(log: dict[str, Any]) -> dict[str, Any]:
    return {
        "address": str(log.get("address") or "").lower(),
        "topics": [str(x).lower() for x in (log.get("topics") or [])],
        "data": str(log.get("data") or "0x").lower(),
        "blockNumber": str(log.get("blockNumber") or "").lower(),
        "blockHash": str(log.get("blockHash") or "").lower(),
        "transactionHash": str(log.get("transactionHash") or "").lower(),
        "transactionIndex": str(log.get("transactionIndex") or "").lower(),
        "logIndex": str(log.get("logIndex") or "").lower(),
    }


def logs_digest(logs: list[dict[str, Any]]) -> str:
    norm = [normalize_log(x) for x in logs]
    norm.sort(key=lambda x: (as_int(x["transactionIndex"] or "0x0"), as_int(x["logIndex"] or "0x0")))
    b = (json.dumps(norm, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(b).hexdigest()


class Rpc:
    def __init__(self, url: str):
        self.url = url
        self.i = 0
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/historical-state-v0.3"})

    def call(self, method: str, params: list[Any]) -> Any:
        self.i += 1
        body = {"jsonrpc": "2.0", "id": self.i, "method": method, "params": params}
        r = self.session.post(self.url, json=body, timeout=(12, 35))
        r.raise_for_status()
        obj = r.json()
        if obj.get("error") is not None:
            raise RuntimeError(f"{method}: {obj['error']}")
        if "result" not in obj:
            raise RuntimeError(f"{method}: missing result")
        return obj["result"]

    def eth_call_address(self, to: str, data: str, block: int) -> str:
        return decode_address(self.call("eth_call", [{"to": to, "data": data}, hblock(block)]))

    def logs(self, address: str, block: int, topics: list[Any]) -> list[dict[str, Any]]:
        out = self.call("eth_getLogs", [{
            "address": address,
            "fromBlock": hblock(block),
            "toBlock": hblock(block),
            "topics": topics,
        }])
        if not isinstance(out, list):
            raise RuntimeError("eth_getLogs result not a list")
        return out


def probe_endpoint(url: str) -> dict[str, Any]:
    rpc = Rpc(url)
    result: dict[str, Any] = {"endpoint": url, "state_ok": False, "logs_ok": False, "errors": []}

    try:
        chain_id = rpc.call("eth_chainId", [])
        if str(chain_id).lower() != "0x1":
            raise RuntimeError(f"unexpected chainId {chain_id}")
        block = rpc.call("eth_getBlockByNumber", [hblock(ACTIVATION_BLOCK), False])
        if not isinstance(block, dict) or not block.get("hash"):
            raise RuntimeError("activation block unavailable")
        ts = as_int(block.get("timestamp"))
        if ts > MAX_ALLOWED_TS:
            raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
        provider_code = rpc.call("eth_getCode", [PROVIDER, hblock(ACTIVATION_BLOCK)])
        oracle_code = rpc.call("eth_getCode", [ORACLE, hblock(ACTIVATION_BLOCK)])
        if not isinstance(provider_code, str) or provider_code in ("0x", "0x0"):
            raise RuntimeError("provider code missing at activation")
        if not isinstance(oracle_code, str) or oracle_code in ("0x", "0x0"):
            raise RuntimeError("oracle code missing at activation")

        result["state"] = {
            "chain_id": str(chain_id).lower(),
            "activation_block_hash": str(block["hash"]).lower(),
            "activation_timestamp": ts,
            "provider_code_sha256": hashlib.sha256(bytes.fromhex(provider_code[2:])).hexdigest(),
            "oracle_code_sha256": hashlib.sha256(bytes.fromhex(oracle_code[2:])).hexdigest(),
            "price_oracle_pre_activation": rpc.eth_call_address(PROVIDER, SEL_PRICE_ORACLE, PRE_ACTIVATION_BLOCK),
            "price_oracle_activation": rpc.eth_call_address(PROVIDER, SEL_PRICE_ORACLE, ACTIVATION_BLOCK),
            "pool_activation": rpc.eth_call_address(PROVIDER, SEL_POOL, ACTIVATION_BLOCK),
            "configurator_activation": rpc.eth_call_address(PROVIDER, SEL_CONFIGURATOR, ACTIVATION_BLOCK),
        }
        result["state_ok"] = True
    except Exception as exc:
        result["errors"].append(f"state:{type(exc).__name__}:{str(exc)[:500]}")

    try:
        reserve_logs = rpc.logs(CONFIGURATOR, ACTIVATION_BLOCK, [T_RESERVE_INITIALIZED])
        source_logs = rpc.logs(ORACLE, ACTIVATION_BLOCK, [T_ASSET_SOURCE_UPDATED])
        base_logs = rpc.logs(ORACLE, ORACLE_CREATION_BLOCK, [T_BASE_CURRENCY_SET])
        price_update_logs = rpc.logs(PROVIDER, ACTIVATION_BLOCK, [T_PRICE_ORACLE_UPDATED])
        address_set_logs = rpc.logs(PROVIDER, ACTIVATION_BLOCK, [T_ADDRESS_SET, PRICE_ORACLE_ID])
        result["logs"] = {
            "reserve_initialized_count": len(reserve_logs),
            "reserve_initialized_digest": logs_digest(reserve_logs),
            "reserve_initialized": [normalize_log(x) for x in reserve_logs],
            "asset_source_updated_count": len(source_logs),
            "asset_source_updated_digest": logs_digest(source_logs),
            "asset_source_updated": [normalize_log(x) for x in source_logs],
            "base_currency_set_count": len(base_logs),
            "base_currency_set_digest": logs_digest(base_logs),
            "base_currency_set": [normalize_log(x) for x in base_logs],
            "price_oracle_updated_count": len(price_update_logs),
            "price_oracle_updated_digest": logs_digest(price_update_logs),
            "price_oracle_updated": [normalize_log(x) for x in price_update_logs],
            "address_set_price_oracle_count": len(address_set_logs),
            "address_set_price_oracle_digest": logs_digest(address_set_logs),
            "address_set_price_oracle": [normalize_log(x) for x in address_set_logs],
        }
        result["logs_ok"] = True
    except Exception as exc:
        result["errors"].append(f"logs:{type(exc).__name__}:{str(exc)[:500]}")

    return result


def state_fingerprint(r: dict[str, Any]) -> tuple[Any, ...]:
    s = r["state"]
    return (
        s["chain_id"], s["activation_block_hash"], s["activation_timestamp"],
        s["price_oracle_pre_activation"].lower(), s["price_oracle_activation"].lower(),
        s["pool_activation"].lower(), s["configurator_activation"].lower(),
    )


def log_fingerprint(r: dict[str, Any]) -> tuple[Any, ...]:
    x = r["logs"]
    return (
        x["reserve_initialized_count"], x["reserve_initialized_digest"],
        x["asset_source_updated_count"], x["asset_source_updated_digest"],
        x["base_currency_set_count"], x["base_currency_set_digest"],
        x["price_oracle_updated_count"], x["price_oracle_updated_digest"],
        x["address_set_price_oracle_count"], x["address_set_price_oracle_digest"],
    )


def transition_before_first_reserve(logs_result: dict[str, Any]) -> bool:
    reserves = logs_result["reserve_initialized"]
    if not reserves:
        return False
    first = min(reserves, key=lambda x: (as_int(x["transactionIndex"]), as_int(x["logIndex"])))
    transitions = list(logs_result["price_oracle_updated"]) + list(logs_result["address_set_price_oracle"])
    valid = []
    for x in transitions:
        topics = x.get("topics") or []
        if not topics:
            continue
        t0 = topics[0].lower()
        new_addr = None
        if t0 == T_PRICE_ORACLE_UPDATED and len(topics) >= 3:
            new_addr = "0x" + topics[2][-40:]
        elif t0 == T_ADDRESS_SET and len(topics) >= 4 and topics[1].lower() == PRICE_ORACLE_ID:
            new_addr = "0x" + topics[3][-40:]
        if new_addr and new_addr.lower() == ORACLE:
            valid.append(x)
    return any(
        (as_int(x["transactionIndex"]), as_int(x["logIndex"])) <
        (as_int(first["transactionIndex"]), as_int(first["logIndex"]))
        for x in valid
    )


def main() -> int:
    with ThreadPoolExecutor(max_workers=len(ENDPOINTS)) as ex:
        futs = {ex.submit(probe_endpoint, u): u for u in ENDPOINTS}
        results = []
        for f in as_completed(futs):
            try:
                results.append(f.result())
            except Exception as exc:
                results.append({"endpoint": futs[f], "state_ok": False, "logs_ok": False, "errors": [f"worker:{type(exc).__name__}:{str(exc)[:500]}"]})
    results.sort(key=lambda x: ENDPOINTS.index(x["endpoint"]))

    state_ok = [x for x in results if x.get("state_ok")]
    logs_ok = [x for x in results if x.get("logs_ok")]
    failure = None

    if len(state_ok) < 2 or len(logs_ok) < 2:
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"usable endpoints below frozen minimum: state={len(state_ok)}, logs={len(logs_ok)}"
    elif len({state_fingerprint(x) for x in state_ok}) != 1:
        classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
        failure = "successful historical-state endpoints disagree"
    elif len({log_fingerprint(x) for x in logs_ok}) != 1:
        classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
        failure = "successful exact-block log endpoints disagree"
    else:
        s = state_ok[0]["state"]
        l = logs_ok[0]["logs"]
        activation_identity_ok = (
            s["price_oracle_activation"].lower() == ORACLE and
            s["pool_activation"].lower() == POOL and
            s["configurator_activation"].lower() == CONFIGURATOR
        )
        log_route_ok = (
            int(l["reserve_initialized_count"]) > 0 and
            int(l["asset_source_updated_count"]) > 0 and
            int(l["base_currency_set_count"]) > 0
        )
        pre = s["price_oracle_pre_activation"].lower()
        boundary_ok = pre == ORACLE
        if not boundary_ok:
            boundary_ok = transition_before_first_reserve(l)
        if not activation_identity_ok:
            classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
            failure = "provider activation identities do not match frozen canonical identities"
        elif not log_route_ok:
            classification = "RECONSTRUCTION_INSUFFICIENT_COVERAGE"
            failure = "required exact-block oracle/reserve configuration logs missing"
        elif not boundary_ok:
            classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
            failure = "oracle boundary state not proven before first reserve initialization"
        else:
            classification = "HISTORICAL_STATE_PROVENANCE_PASS_V0_3"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "HISTORICAL_STATE_PROVENANCE_V0_3_OUTCOME_BLIND",
        "classification": classification,
        "activation_block": ACTIVATION_BLOCK,
        "pre_activation_block": PRE_ACTIVATION_BLOCK,
        "oracle_creation_block": ORACLE_CREATION_BLOCK,
        "frozen_endpoints": ENDPOINTS,
        "usable_state_endpoints": len(state_ok),
        "usable_log_endpoints": len(logs_ok),
        "endpoint_results": results,
        "failure": failure,
        "safety": {
            "historical_protocol_state_only": True,
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_return_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026_market_source": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("historical_state_v03_output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "AAVE_LIQUIDATION_OVERHANG_001_HISTORICAL_STATE_PROVENANCE_V0_3.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "classification": classification,
        "usable_state_endpoints": len(state_ok),
        "usable_log_endpoints": len(logs_ok),
        "activation_price_oracle": None if not state_ok else state_ok[0]["state"]["price_oracle_activation"],
        "pre_activation_price_oracle": None if not state_ok else state_ok[0]["state"]["price_oracle_pre_activation"],
        "reserve_initialized_count": None if not logs_ok else logs_ok[0]["logs"]["reserve_initialized_count"],
        "asset_source_updated_count": None if not logs_ok else logs_ok[0]["logs"]["asset_source_updated_count"],
        "base_currency_set_count": None if not logs_ok else logs_ok[0]["logs"]["base_currency_set_count"],
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "HISTORICAL_STATE_PROVENANCE_PASS_V0_3" else 2


if __name__ == "__main__":
    sys.exit(main())
