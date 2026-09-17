#!/usr/bin/env python3
"""Full R1 reserve-state replay shard for AAVE-LIQUIDATION-OVERHANG-001.

Prepared before audit adjudication, but must only be executed after R1_AUDIT_PASS.
Reconstructs token-native scaled ledgers, collateral flags, reserve indices,
decimals and reserve-specific configuration history. No HF/overhang/outcomes.
"""
from __future__ import annotations

import hashlib
import json
import os
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
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
RAY = 10**27
WINDOW = 75_000
TRANSIENT = {429, 500, 502, 503, 504, 529}


def topic(sig: str) -> str:
    return "0x" + keccak(sig.encode()).hex()

T_MINT = topic("Mint(address,address,uint256,uint256,uint256)")
T_BURN = topic("Burn(address,address,uint256,uint256,uint256)")
T_BALANCE_TRANSFER = topic("BalanceTransfer(address,address,uint256,uint256)")
T_INITIALIZED = topic("Initialized(address,address,address,address,uint8,string,string,bytes)")
T_RDU = topic("ReserveDataUpdated(address,uint256,uint256,uint256,uint256,uint256)")
T_COLL_ON = topic("ReserveUsedAsCollateralEnabled(address,address)")
T_COLL_OFF = topic("ReserveUsedAsCollateralDisabled(address,address)")

CONFIG_SIGS = {
    "CollateralConfigurationChanged": "CollateralConfigurationChanged(address,uint256,uint256,uint256)",
    "ReserveActive": "ReserveActive(address,bool)",
    "ReserveFrozen": "ReserveFrozen(address,bool)",
    "ReservePaused": "ReservePaused(address,bool)",
    "EModeAssetCategoryChanged": "EModeAssetCategoryChanged(address,uint8,uint8)",
    "ATokenUpgraded": "ATokenUpgraded(address,address,address)",
    "VariableDebtTokenUpgraded": "VariableDebtTokenUpgraded(address,address,address)",
}
CONFIG_TOPICS = {topic(sig): name for name, sig in CONFIG_SIGS.items()}


def as_int(v: Any) -> int:
    if isinstance(v, int): return v
    if isinstance(v, str): return int(v, 16) if v.startswith("0x") else int(v)
    raise TypeError("bad integer")


def topic_addr(t: str) -> str:
    t = str(t).lower()
    if len(t) != 66 or not t.startswith("0x"):
        raise ValueError("bad address topic")
    return "0x" + t[-40:]


def addr_topic(a: str) -> str:
    a = a.lower()
    return "0x" + "0" * 24 + a[2:]


def words(data: str, n: int) -> list[int]:
    h = str(data)[2:] if str(data).startswith("0x") else ""
    if len(h) < 64*n or len(h) % 64:
        raise ValueError("bad ABI data")
    return [int(h[i*64:(i+1)*64], 16) for i in range(n)]


def ray_div(a: int, b: int) -> int:
    if b == 0: raise ZeroDivisionError("rayDiv zero")
    return (a * RAY + b//2)//b


def post(body: dict[str, Any], stats: Counter[str]) -> requests.Response:
    last = None
    for attempt in range(8):
        try:
            r = requests.post(PORTAL, json=body, timeout=(20,180), stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/r1-reserve-shard-v0.1"})
            stats["http_attempts"] += 1
            if r.status_code in TRANSIENT:
                last = RuntimeError(f"transient HTTP {r.status_code}")
                r.close()
                if attempt < 7:
                    stats["transient_retries"] += 1
                    time.sleep(min(20.0, 1.5*(2**attempt)))
                    continue
                raise last
            r.raise_for_status(); stats["successful_http_responses"] += 1
            return r
        except (requests.RequestException, RuntimeError) as exc:
            last = exc
            if attempt < 7:
                stats["network_retries"] += 1
                time.sleep(min(20.0, 1.5*(2**attempt)))
                continue
            raise
    raise RuntimeError(str(last))


def stream(filters: list[dict[str, Any]], stats: Counter[str]):
    cursor = FROM_BLOCK
    while cursor <= TO_BLOCK:
        request_to = min(TO_BLOCK, cursor + WINDOW - 1)
        body = {
            "type":"evm","fromBlock":cursor,"toBlock":request_to,
            "fields":{"block":{"number":True,"timestamp":True},
                      "log":{"address":True,"topics":True,"data":True,
                             "transactionHash":True,"logIndex":True}},
            "logs":filters,
        }
        r = post(body, stats); last = None; rows = 0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                h = obj.get("header") or obj.get("block") or {}
                bn = int(h["number"])
                if not (cursor <= bn <= request_to): raise RuntimeError("row outside window")
                if last is not None and bn < last: raise RuntimeError("non-monotonic page")
                last = bn; rows += 1
                yield obj
        finally:
            r.close()
        stats["portal_rows"] += rows
        if rows == 0 or last is None:
            cursor = request_to + 1
            stats["empty_windows"] += 1
        else:
            cursor = last + 1


def load_json_under(root: str, classification: str) -> dict[str, Any]:
    for p in Path(root).rglob("*.json"):
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("classification") == classification:
            return obj
    raise FileNotFoundError(f"receipt {classification} not found under {root}")


def main() -> int:
    shard_id = int(os.environ.get("R1_SHARD_ID", "0"))
    shard_count = int(os.environ.get("R1_SHARD_COUNT", "8"))
    out = Path("r1_reserve_shards"); out.mkdir(parents=True, exist_ok=True)
    outpath = out / f"r1_reserve_shard_{shard_id:02d}.json"
    stats: Counter[str] = Counter(); failure = None
    result: dict[str, Any] = {}
    try:
        audit = load_json_under("downloaded_r1_audit", "R1_AUDIT_PASS")
        bootstrap = load_json_under("downloaded_r0_bootstrap", "RECONSTRUCTION_R0_BOOTSTRAP_PASS")
        if int(bootstrap["frozen_from_block"]) != FROM_BLOCK or int(bootstrap["frozen_to_block"]) != TO_BLOCK:
            raise RuntimeError("R0 envelope mismatch")
        reserves_all = sorted((u.lower(), m) for u,m in bootstrap["reserves"].items())
        selected = [(u,m) for i,(u,m) in enumerate(reserves_all) if i % shard_count == shard_id]
        if not selected: raise RuntimeError("empty deterministic reserve shard")

        token_meta: dict[str, dict[str,str]] = {}
        atoken_for: dict[str,str] = {}
        vdebt_for: dict[str,str] = {}
        init_block: dict[str,int] = {}
        for u,m in selected:
            at = str(m["aToken"]).lower(); vd = str(m["variableDebtToken"]).lower()
            token_meta[at] = {"kind":"ATOKEN","reserve":u}
            token_meta[vd] = {"kind":"VARIABLE_DEBT","reserve":u}
            atoken_for[u] = at; vdebt_for[u] = vd; init_block[u] = int(m["init_block"])

        underlyings = [u for u,_ in selected]
        underlying_topics = [addr_topic(u) for u in underlyings]
        atokens = [atoken_for[u] for u in underlyings]
        all_tokens = list(token_meta)
        filters = [
            {"address":all_tokens,"topic0":[T_MINT,T_BURN,T_BALANCE_TRANSFER]},
            {"address":[POOL],"topic0":[T_RDU,T_COLL_ON,T_COLL_OFF],"topic1":underlying_topics},
            {"address":[CONFIGURATOR],"topic0":list(CONFIG_TOPICS),"topic1":underlying_topics},
            {"address":atokens,"topic0":[T_INITIALIZED]},
        ]

        balances: dict[str, dict[str,int]] = defaultdict(dict)
        flags: dict[tuple[str,str],bool] = {}
        last_liq = {u:RAY for u in underlyings}; last_var = {u:RAY for u in underlyings}
        decimals: dict[str,int] = {}
        cfg_last: dict[str,dict[str,Any]] = defaultdict(dict)
        counts: Counter[str] = Counter(); negative = []; index_decreases = []; flag_violations = []
        seen: set[tuple[str,int]] = set(); h = hashlib.sha256()
        current_tx: str | None = None; touched_tx: set[tuple[str,str]] = set()

        def bal(token: str, user: str) -> int:
            return balances[token].get(user,0)
        def setbal(token: str, user: str, value: int, bn: int, li: int):
            if value == 0: balances[token].pop(user, None)
            else: balances[token][user] = value
            if value < 0 and len(negative) < 100:
                negative.append({"block":bn,"logIndex":li,"token":token,"user":user,"balance":str(value)})
        def flush_tx():
            nonlocal touched_tx
            for reserve,user in touched_tx:
                if flags.get((reserve,user),False) and bal(atoken_for[reserve],user) == 0:
                    if len(flag_violations) < 100:
                        flag_violations.append({"reserve":reserve,"user":user,"reason":"collateral_flag_true_with_zero_scaled_atoken_at_tx_end"})
            touched_tx = set()

        for obj in stream(filters, stats):
            header = obj.get("header") or obj.get("block") or {}; bn = int(header["number"])
            logs = sorted(obj.get("logs") or [], key=lambda x: as_int(x.get("logIndex")))
            for log in logs:
                addr = str(log.get("address","")).lower(); topics = [str(x).lower() for x in (log.get("topics") or [])]
                if not topics: raise RuntimeError("log without topic0")
                txh = str(log.get("transactionHash","")).lower(); li = as_int(log.get("logIndex"))
                key = (txh,li)
                if key in seen: raise RuntimeError("duplicate canonical log identity")
                seen.add(key)
                if current_tx is not None and txh != current_tx: flush_tx()
                current_tx = txh
                t0 = topics[0]
                h.update(f"{bn}|{txh}|{li}|{addr}|{t0}\n".encode())

                if addr in token_meta:
                    meta = token_meta[addr]; reserve = meta["reserve"]; kind = meta["kind"]
                    if bn < init_block[reserve]: raise RuntimeError("scaled-token event before reserve initialization")
                    if t0 == T_MINT:
                        if len(topics)<3: raise RuntimeError("Mint ABI")
                        user = topic_addr(topics[2]); value,inc,index = words(log.get("data",""),3)[:3]
                        if value > inc: delta = ray_div(value-inc,index)
                        elif value < inc: delta = -ray_div(inc-value,index); counts[f"{kind}_MINT_BURN_PATH"] += 1
                        else: delta = 0; counts[f"{kind}_MINT_INTEREST_ONLY"] += 1
                        setbal(addr,user,bal(addr,user)+delta,bn,li); counts[f"{kind}_MINT"] += 1
                        if kind=="ATOKEN": touched_tx.add((reserve,user))
                    elif t0 == T_BURN:
                        if len(topics)<2: raise RuntimeError("Burn ABI")
                        user = topic_addr(topics[1]); value,inc,index = words(log.get("data",""),3)[:3]
                        delta = -ray_div(value+inc,index)
                        setbal(addr,user,bal(addr,user)+delta,bn,li); counts[f"{kind}_BURN"] += 1
                        if kind=="ATOKEN": touched_tx.add((reserve,user))
                    elif t0 == T_BALANCE_TRANSFER:
                        if kind=="VARIABLE_DEBT":
                            counts["VARIABLE_DEBT_BALANCE_TRANSFER"] += 1
                        else:
                            if len(topics)<3: raise RuntimeError("BalanceTransfer ABI")
                            fr = topic_addr(topics[1]); to = topic_addr(topics[2]); value,index = words(log.get("data",""),2)[:2]
                            setbal(addr,fr,bal(addr,fr)-value,bn,li); setbal(addr,to,bal(addr,to)+value,bn,li)
                            touched_tx.add((reserve,fr)); touched_tx.add((reserve,to)); counts["ATOKEN_BALANCE_TRANSFER"] += 1
                    elif t0 == T_INITIALIZED:
                        # Included by another filter on the same aToken address.
                        pass
                    else: raise RuntimeError("unexpected scaled-token topic")

                elif addr == POOL:
                    if len(topics)<2: raise RuntimeError("Pool event missing reserve")
                    reserve = topic_addr(topics[1])
                    if reserve not in atoken_for: raise RuntimeError("Pool reserve escaped shard filter")
                    if t0 == T_RDU:
                        lr,sr,vr,liq,var = words(log.get("data",""),5)[:5]
                        if liq < last_liq[reserve]: index_decreases.append({"reserve":reserve,"block":bn,"which":"liquidity","previous":str(last_liq[reserve]),"next":str(liq)})
                        if var < last_var[reserve]: index_decreases.append({"reserve":reserve,"block":bn,"which":"variableBorrow","previous":str(last_var[reserve]),"next":str(var)})
                        last_liq[reserve]=liq; last_var[reserve]=var; counts["ReserveDataUpdated"] += 1
                    elif t0 in (T_COLL_ON,T_COLL_OFF):
                        if len(topics)<3: raise RuntimeError("collateral flag ABI")
                        user = topic_addr(topics[2]); flags[(reserve,user)] = (t0==T_COLL_ON)
                        touched_tx.add((reserve,user)); counts["CollateralEnabled" if t0==T_COLL_ON else "CollateralDisabled"] += 1
                    else: raise RuntimeError("unexpected Pool topic")

                elif addr == CONFIGURATOR:
                    name = CONFIG_TOPICS.get(t0)
                    if name is None: raise RuntimeError("unexpected Configurator topic")
                    reserve = topic_addr(topics[1]) if len(topics)>1 else None
                    if reserve not in atoken_for: raise RuntimeError("Configurator reserve escaped shard filter")
                    counts[name] += 1
                    if name == "CollateralConfigurationChanged":
                        ltv,threshold,bonus = words(log.get("data",""),3)[:3]
                        cfg_last[reserve]["ltv"] = ltv; cfg_last[reserve]["liquidationThreshold"] = threshold; cfg_last[reserve]["liquidationBonus"] = bonus
                    elif name in ("ReserveActive","ReserveFrozen","ReservePaused"):
                        cfg_last[reserve][name] = bool(words(log.get("data",""),1)[0])
                    elif name == "EModeAssetCategoryChanged":
                        oldc,newc = words(log.get("data",""),2)[:2]; cfg_last[reserve]["eModeCategory"] = newc

                elif addr in atokens and t0 == T_INITIALIZED:
                    if len(topics)<3: raise RuntimeError("aToken Initialized ABI")
                    reserve = topic_addr(topics[1]); pool = topic_addr(topics[2])
                    if reserve not in atoken_for or atoken_for[reserve] != addr: raise RuntimeError("aToken Initialized reserve/token mismatch")
                    if pool != POOL: raise RuntimeError("aToken Initialized Pool mismatch")
                    dataw = words(log.get("data",""),3); dec = dataw[2]
                    if dec > 255: raise RuntimeError("invalid decimals")
                    if reserve in decimals and decimals[reserve] != dec: raise RuntimeError("decimals changed across Initialized events")
                    decimals[reserve]=dec; counts["ATokenInitialized"] += 1
                else:
                    raise RuntimeError(f"unexpected address/topic {addr} {t0}")
        flush_tx()

        missing_decimals = [u for u in underlyings if u not in decimals]
        debt_transfer_count = counts.get("VARIABLE_DEBT_BALANCE_TRANSFER",0)
        if negative or flag_violations or index_decreases:
            classification = "RECONSTRUCTION_RECONCILIATION_FAILURE"
            failure = f"negative={len(negative)} flag={len(flag_violations)} index_decrease={len(index_decreases)}"
        elif debt_transfer_count:
            classification = "RECONSTRUCTION_PROVENANCE_FAILURE"; failure = "variable debt token emitted BalanceTransfer"
        elif missing_decimals:
            classification = "RECONSTRUCTION_INSUFFICIENT_COVERAGE"; failure = f"missing aToken Initialized decimals for {missing_decimals}"
        else:
            classification = "R1_RESERVE_SHARD_PASS"

        result = {
            "shard_id":shard_id,"shard_count":shard_count,"selected_reserves":underlyings,
            "classification":classification,"failure":failure,
            "event_counts":dict(sorted(counts.items())),"decimals":decimals,
            "last_liquidity_index":{k:str(v) for k,v in last_liq.items()},
            "last_variable_borrow_index":{k:str(v) for k,v in last_var.items()},
            "last_reserve_config":cfg_last,"negative_states":negative,
            "collateral_flag_violations":flag_violations,"index_decreases":index_decreases,
            "nonzero_atoken_accounts":sum(len(balances[atoken_for[u]]) for u in underlyings),
            "nonzero_variable_debt_accounts":sum(len(balances[vdebt_for[u]]) for u in underlyings),
            "active_collateral_flags":sum(1 for v in flags.values() if v),
            "canonical_log_count":len(seen),"canonical_log_digest_sha256":h.hexdigest(),
            "transport_stats":dict(stats),
        }
    except Exception as exc:
        result = {"shard_id":shard_id,"shard_count":shard_count,
                  "classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
                  "failure":f"{type(exc).__name__}: {str(exc)[:1200]}","transport_stats":dict(stats)}

    result.update({"lab_id":LAB_ID,"phase":"R1_FULL_RESERVE_SHARD_OUTCOME_BLIND",
                   "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
                   "safety":{"health_factor_computed":False,"overhang_computed":False,
                             "future_liquidation_outcome_computed":False,"market_prices_opened":False,
                             "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                             "live_trading":False,"exchange_mutation":False}})
    outpath.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard":shard_id,"classification":result["classification"],
                      "reserves":len(result.get("selected_reserves",[])),
                      "canonical_logs":result.get("canonical_log_count"),
                      "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if result["classification"]=="R1_RESERVE_SHARD_PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
