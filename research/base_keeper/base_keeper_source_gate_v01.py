#!/usr/bin/env python3
"""Base Aave V3 public-only liquidation event census. Never signs, trades, or fetches accounts."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import statistics
import sys
import time
from urllib.request import Request, urlopen

RPC = "https://mainnet.base.org"
POOL = "0xa238dd80c259a72e81d7e4664a9801593f98d1c5"
TOPIC = "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
CHAIN_ID = 8453
FROZEN_BLOCK_SPAN = 24000
MAX_CHUNK = 1500
FINALITY_LAG_BLOCKS = 12
MAX_RECEIPTS = 20
MAX_SECONDS = 85
MAX_CALLS = 60
REQUEST_PAUSE = 0.30


class GateBlocked(RuntimeError):
    pass


class BaseRPC:
    def __init__(self):
        self.calls = 0
        self.started = time.monotonic()

    def call(self, method: str, params: list) -> object:
        if method not in {"eth_chainId", "eth_blockNumber", "eth_getLogs", "eth_getTransactionReceipt"}:
            raise GateBlocked("RPC_METHOD_NOT_READ_ONLY_ALLOWED")
        if self.calls >= MAX_CALLS or time.monotonic() - self.started > MAX_SECONDS:
            raise GateBlocked("PUBLIC_RPC_BUDGET_EXCEEDED")
        self.calls += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.calls, "method": method, "params": params}).encode()
        request = Request(RPC, data=body, headers={"Content-Type": "application/json",
                            "User-Agent": "CryptoLab-ResearchOnly-BaseKeeper-V01"}, method="POST")
        try:
            with urlopen(request, timeout=9) as response:
                result = json.load(response)
        except Exception as e:
            raise GateBlocked("PUBLIC_RPC_TRANSPORT:" + type(e).__name__) from e
        if not isinstance(result, dict) or "error" in result or "result" not in result:
            raise GateBlocked("PUBLIC_RPC_MALFORMED_OR_ERROR")
        time.sleep(REQUEST_PAUSE)
        return result["result"]


def uint_hex(value: object) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError("invalid hex")
    return int(value, 16)


def decode_liquidation(log: dict) -> dict:
    if not isinstance(log, dict) or str(log.get("address", "")).lower() != POOL:
        raise ValueError("emitting contract mismatch")
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) != 4 or str(topics[0]).lower() != TOPIC:
        raise ValueError("event signature/index mismatch")
    data = str(log.get("data") or "")
    if not data.startswith("0x") or len(data) != 2 + 4 * 64:
        raise ValueError("ABI data length mismatch")
    indexed = topics[1:4]
    for topic in indexed:
        if not isinstance(topic, str) or len(topic) != 66 or not topic.startswith("0x"):
            raise ValueError("invalid indexed address encoding")
        if any(z != "0" for z in topic[2:26]):
            raise ValueError("indexed address prefix invalid")
    words = [int(data[2+i*64:2+(i+1)*64], 16) for i in range(4)]
    if words[3] not in (0,1) or words[0] <= 0 or words[1] <= 0:
        raise ValueError("bad event amount or bool")
    liq_raw = words[2]
    if liq_raw >= (1 << 160):
        raise ValueError("invalid liquidator address")
    return {
        "tx_hash": str(log["transactionHash"]).lower(),
        "log_index": uint_hex(log["logIndex"]),
        "block": uint_hex(log["blockNumber"]),
        "liquidator": "0x" + f"{liq_raw:040x}",
        "receive_atoken": bool(words[3]),
        "debt_repaid_raw": str(words[0]),
        "collateral_received_raw": str(words[1]),
    }


def cost_wei(receipt: dict) -> tuple[int, bool]:
    used = uint_hex(receipt["gasUsed"])
    unit_price = uint_hex(receipt["effectiveGasPrice"])
    l1raw = receipt.get("l1Fee")
    if l1raw is None:
        return used * unit_price, False
    return used * unit_price + uint_hex(l1raw), True


def decide(records: list[dict], complete: bool, receipt_costs_wei: list[int], explicit_l1_fee: int) -> dict:
    unique = set()
    for x in records:
        key=(x["tx_hash"],x["log_index"])
        if key in unique: raise GateBlocked("DUPLICATE_EVENT_IDENTITY")
        unique.add(key)
    cnt = Counter(x["liquidator"] for x in records)
    tops = sorted(cnt.values(), reverse=True)
    count = len(records)
    concentration = round(tops[0] / count, 5) if count else None
    top3 = round(sum(tops[:3]) / count, 5) if count else None
    verdict = ("SOURCE_PASS" if receipt_costs_wei and count and complete else
               "SOURCE_EMPTY" if not count and complete else "SOURCE_BLOCKED")
    return {
        "source_verdict": verdict,
        "economic_verdict": "UNPROVEN_NOT_A_LIVE_EDGE",
        "liquidation_events": count,
        "distinct_liquidators": len(cnt),
        "distinct_blocks_with_events": len(set(x["block"] for x in records)),
        "largest_liquidator_event_share": concentration,
        "top3_liquidator_event_share": top3,
        "high_concentration_barrier": bool(concentration is not None and concentration > 0.9),
        "sampled_receipts": len(receipt_costs_wei),
        "sampled_explicit_l1_fee_receipts": explicit_l1_fee,
        "sampled_median_gas_fee_eth": (
            str(Decimal(statistics.median(receipt_costs_wei)) / Decimal(10**18))
            if receipt_costs_wei else None),
        "gas_cost_completeness": ("INCOMPLETE_MISSING_L1_FEE"
                                  if explicit_l1_fee != len(receipt_costs_wei) else "ALL_SAMPLED_L1_FIELD_PRESENT"),
        "net_profit_usd": None,
        "liquidation_bonus_usd": None,
        "execution_win_rate": None,
        "limits": "One onchain historical discovery sample; no profit/competition/quote execution inference",
    }


def collect() -> dict:
    api=BaseRPC()
    try:
        if uint_hex(api.call("eth_chainId", [])) != CHAIN_ID:
            raise GateBlocked("INCORRECT_CHAIN_ID")
        tip=uint_hex(api.call("eth_blockNumber", []))
        end=tip-FINALITY_LAG_BLOCKS
        start=end-FROZEN_BLOCK_SPAN+1
        if start < 1: raise GateBlocked("CHAIN_HEIGHT_INSUFFICIENT")
        logs=[]
        for low in range(start,end+1,MAX_CHUNK):
            hi=min(end,low+MAX_CHUNK-1)
            out=api.call("eth_getLogs", [{
                "address": POOL, "fromBlock":hex(low),"toBlock":hex(hi),"topics":[TOPIC]}])
            if not isinstance(out,list): raise GateBlocked("LOGS_NOT_LIST")
            logs.extend(out)
        records=[]
        for raw in logs:
            try:
                rec=decode_liquidation(raw)
            except Exception as e:
                raise GateBlocked("LIQUIDATION_ABI_MISMATCH:"+type(e).__name__) from e
            if not(start <= rec["block"] <= end):raise GateBlocked("LOG_OUTSIDE_FROZEN_RANGE")
            records.append(rec)
        unique_tx=list(dict.fromkeys(x["tx_hash"] for x in reversed(records)))[:MAX_RECEIPTS]
        fees=[];l1count=0
        for tx in unique_tx:
            receipt=api.call("eth_getTransactionReceipt", [tx])
            if not isinstance(receipt,dict) or str(receipt.get("transactionHash","")).lower()!=tx:
                raise GateBlocked("RECEIPT_TX_IDENTITY_MISMATCH")
            fee,has_l1=cost_wei(receipt)
            if fee <= 0: raise GateBlocked("RECEIPT_GAS_INVALID")
            fees.append(fee); l1count+=int(has_l1)
        decision=decide(records,True,fees,l1count)
        decision.update({"chain_id":CHAIN_ID,"pool":POOL,"topic":TOPIC,
                          "tip_block":tip,"from_block":start,"to_block":end,
                          "requested_block_count":FROZEN_BLOCK_SPAN,
                          "complete_block_count":FROZEN_BLOCK_SPAN,
                          "rpc_calls":api.calls,
                          "observed_at_utc":datetime.now(timezone.utc).isoformat()})
        return decision
    except GateBlocked as e:
        return {"source_verdict":"SOURCE_BLOCKED","reason":str(e),
                "economic_verdict":"UNPROVEN_NOT_A_LIVE_EDGE",
                "complete_block_count":0,"rpc_calls":api.calls,
                "no_trading":True,
                "observed_at_utc":datetime.now(timezone.utc).isoformat()}


if __name__=="__main__":
    report=collect()
    output=Path(os.environ.get("BASE_KEEPER_RECEIPT_PATH","BASE_KEEPER_001_SOURCE_RECEIPT.json"))
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    sys.exit(0)
