#!/usr/bin/env python3
"""STETH-REDEMPTION-BASIS-001 source-only feasibility probe.

Hard safety boundary:
- Ethereum mainnet only.
- Never requests blocks/timestamps after 2024-12-31 23:59:59 UTC.
- Never fetches market price series, returns, PnL, win rate, PF or drawdown.
- Historical eth_call return values are validated for accessibility but never printed.
- Event payload values are never decoded/printed; only count + SHA256 receipt hashes.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "STETH-REDEMPTION-BASIS-001"
START_TS = int(datetime(2023, 5, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp())
END_TS = int(datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())
# Etherscan timestamp lookup for 2024-12-31 23:59:59 UTC. Keeping an explicit hard
# ceiling guarantees no accidental traversal into protected 2025/2026 blocks.
MAX_ALLOWED_BLOCK = 21_525_890
MIN_SEARCH_BLOCK = 17_000_000

STETH = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WITHDRAWAL_QUEUE = "0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1"
CURVE_STETH = "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"
WITHDRAWAL_QUEUE_DEPLOY_TX = "0x98c2170be034f750f5006cb69ea0aeeaf0858b11f6324ee53d582fa4dd49bc1a"

PROVIDERS = [
    p.strip()
    for p in os.environ.get(
        "ETH_SOURCE_GATE_RPCS",
        "https://ethereum-rpc.publicnode.com,https://eth.llamarpc.com,https://rpc.flashbots.net",
    ).split(",")
    if p.strip()
]

EVENTS = {
    "withdrawal_requested": (WITHDRAWAL_QUEUE, "WithdrawalRequested(uint256,address,address,uint256,uint256)"),
    "withdrawals_finalized": (WITHDRAWAL_QUEUE, "WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)"),
    "withdrawal_claimed": (WITHDRAWAL_QUEUE, "WithdrawalClaimed(uint256,address,address,uint256)"),
    "token_rebased": (STETH, "TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"),
    "curve_token_exchange": (CURVE_STETH, "TokenExchange(address,int128,uint256,int128,uint256)"),
}

STATE_CALLS = {
    "curve_get_dy": (CURVE_STETH, "get_dy(int128,int128,uint256)", [0, 1, 10**18]),
    "curve_fee": (CURVE_STETH, "fee()", []),
    "queue_last_request_id": (WITHDRAWAL_QUEUE, "getLastRequestId()", []),
    "queue_last_finalized_request_id": (WITHDRAWAL_QUEUE, "getLastFinalizedRequestId()", []),
    "queue_unfinalized_steth": (WITHDRAWAL_QUEUE, "unfinalizedStETH()", []),
}


def hex_int(x: int) -> str:
    return hex(int(x))


def selector(signature: str) -> str:
    return "0x" + keccak(signature.encode())[:4].hex()


def event_topic(signature: str) -> str:
    return "0x" + keccak(signature.encode()).hex()


def enc_u256(x: int) -> str:
    if x < 0:
        raise ValueError("negative uint")
    return int(x).to_bytes(32, "big").hex()


def enc_i128_as_abi_word(x: int) -> str:
    # ABI integers occupy 32-byte words and signed values are sign-extended.
    if x >= 0:
        return int(x).to_bytes(32, "big", signed=False).hex()
    return int(x).to_bytes(32, "big", signed=True).hex()


def encode_call(signature: str, args: list[int]) -> str:
    data = selector(signature)[2:]
    if signature.startswith("get_dy("):
        if len(args) != 3:
            raise ValueError("get_dy requires 3 args")
        data += enc_i128_as_abi_word(args[0])
        data += enc_i128_as_abi_word(args[1])
        data += enc_u256(args[2])
    elif args:
        data += "".join(enc_u256(a) for a in args)
    return "0x" + data


class RPCError(RuntimeError):
    pass


@dataclass
class RPC:
    url: str
    timeout: int = 25
    request_id: int = 0

    def call(self, method: str, params: list[Any], retries: int = 2) -> Any:
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            self.request_id += 1
            try:
                r = requests.post(
                    self.url,
                    json={"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params},
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json", "User-Agent": f"{LAB_ID}-source-gate/0.1"},
                )
                if r.status_code == 429:
                    raise RPCError("HTTP_429")
                r.raise_for_status()
                body = r.json()
                if "error" in body:
                    err = body["error"]
                    raise RPCError(f"RPC_{err.get('code')}_{str(err.get('message',''))[:120]}")
                return body.get("result")
            except Exception as e:  # transport/source failure only
                last_err = e
                if attempt < retries:
                    time.sleep(0.8 * (attempt + 1))
        raise RPCError(str(last_err))

    def block(self, number: int) -> dict[str, Any]:
        if number > MAX_ALLOWED_BLOCK:
            raise RPCError("PROTECTED_PERIOD_BLOCK_REQUEST_REJECTED")
        b = self.call("eth_getBlockByNumber", [hex_int(number), False])
        if not b:
            raise RPCError(f"missing block {number}")
        ts = int(b["timestamp"], 16)
        if ts > END_TS:
            raise RPCError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
        return b

    def block_number_at_or_after(self, target_ts: int) -> int:
        if target_ts > END_TS:
            raise RPCError("PROTECTED_PERIOD_TARGET_REJECTED")
        lo, hi = MIN_SEARCH_BLOCK, MAX_ALLOWED_BLOCK
        blo = self.block(lo)
        bhi = self.block(hi)
        if int(blo["timestamp"], 16) > target_ts or int(bhi["timestamp"], 16) < target_ts:
            raise RPCError("timestamp outside frozen block search bounds")
        while lo < hi:
            mid = (lo + hi) // 2
            b = self.block(mid)
            if int(b["timestamp"], 16) < target_ts:
                lo = mid + 1
            else:
                hi = mid
        b = self.block(lo)
        if int(b["timestamp"], 16) < target_ts:
            raise RPCError("timestamp mapping invariant failed")
        if lo > MIN_SEARCH_BLOCK:
            prev = self.block(lo - 1)
            if int(prev["timestamp"], 16) >= target_ts:
                raise RPCError("timestamp mapping not first block at/after target")
        return lo


def canonical_log_hash(logs: list[dict[str, Any]]) -> str:
    minimal = [
        {
            "blockNumber": x.get("blockNumber"),
            "blockHash": x.get("blockHash"),
            "transactionHash": x.get("transactionHash"),
            "logIndex": x.get("logIndex"),
            "address": x.get("address"),
            "topics": x.get("topics", []),
            "data_sha256": hashlib.sha256(str(x.get("data", "")).encode()).hexdigest(),
        }
        for x in logs
    ]
    payload = json.dumps(minimal, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def get_logs_chunked(rpc: RPC, address: str, topic0: str, ranges: list[tuple[int, int]]) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for start, end in ranges:
        start = max(MIN_SEARCH_BLOCK, start)
        end = min(MAX_ALLOWED_BLOCK, end)
        if start > end:
            continue
        cur = start
        while cur <= end:
            to = min(cur + 999, end)
            part = rpc.call(
                "eth_getLogs",
                [{"fromBlock": hex_int(cur), "toBlock": hex_int(to), "address": address, "topics": [topic0]}],
                retries=1,
            )
            if not isinstance(part, list):
                raise RPCError("eth_getLogs non-list response")
            logs.extend(part)
            cur = to + 1
    return logs


def validate_log_ids(logs: list[dict[str, Any]], allowed_ranges: list[tuple[int, int]]) -> None:
    seen: set[tuple[str, str]] = set()
    for x in logs:
        for f in ("blockNumber", "blockHash", "transactionHash", "logIndex"):
            if not x.get(f):
                raise RPCError(f"log missing {f}")
        bn = int(x["blockNumber"], 16)
        if bn > MAX_ALLOWED_BLOCK:
            raise RPCError("log escaped protected-period firewall")
        if not any(a <= bn <= b for a, b in allowed_ranges):
            raise RPCError("log outside requested bounded ranges")
        key = (x["transactionHash"], x["logIndex"])
        if key in seen:
            raise RPCError("duplicate log identifier")
        seen.add(key)


def historical_state_probe(rpc: RPC, block_number: int) -> list[str]:
    passed: list[str] = []
    for name, (address, sig, args) in STATE_CALLS.items():
        data = encode_call(sig, args)
        result = rpc.call("eth_call", [{"to": address, "data": data}, hex_int(block_number)])
        if not isinstance(result, str) or not result.startswith("0x") or len(result) <= 2:
            raise RPCError(f"historical eth_call unavailable: {name}")
        passed.append(name)
    return passed


def probe_provider(url: str) -> dict[str, Any]:
    rpc = RPC(url=url)
    provider_label = url.split("//", 1)[-1].split("/", 1)[0]
    receipt: dict[str, Any] = {"provider": provider_label, "status": "FAIL"}

    chain = rpc.call("eth_chainId", [])
    if int(chain, 16) != 1:
        raise RPCError("wrong chain id")

    start_block = rpc.block_number_at_or_after(START_TS)
    end_block = rpc.block_number_at_or_after(END_TS)
    if end_block > MAX_ALLOWED_BLOCK:
        raise RPCError("mapped end block exceeds firewall")

    # Identity / provenance without printing economic state.
    deploy_receipt = rpc.call("eth_getTransactionReceipt", [WITHDRAWAL_QUEUE_DEPLOY_TX])
    if not deploy_receipt or not deploy_receipt.get("blockNumber"):
        raise RPCError("withdrawal queue deployment receipt unavailable")
    deploy_block = int(deploy_receipt["blockNumber"], 16)
    if deploy_block > start_block:
        raise RPCError("withdrawal queue deployment occurs after frozen source start")

    for bn in (start_block, end_block):
        for name, addr in (("steth", STETH), ("withdrawal_queue", WITHDRAWAL_QUEUE), ("curve_steth", CURVE_STETH)):
            code = rpc.call("eth_getCode", [addr, hex_int(bn)])
            if not isinstance(code, str) or code in ("0x", "0x0"):
                raise RPCError(f"historical bytecode unavailable: {name}@{bn}")

    state_early = historical_state_probe(rpc, start_block)
    state_late = historical_state_probe(rpc, end_block)

    # Bounded event probes near both source-period edges. Payload values remain sealed.
    probe_span = 40_000
    ranges = [
        (start_block, min(start_block + probe_span, end_block)),
        (max(start_block, end_block - probe_span), end_block),
    ]
    event_receipts: dict[str, Any] = {}
    for name, (address, sig) in EVENTS.items():
        logs = get_logs_chunked(rpc, address, event_topic(sig), ranges)
        validate_log_ids(logs, ranges)
        if not logs:
            raise RPCError(f"no bounded historical logs recovered for {name}")
        event_receipts[name] = {"count": len(logs), "sha256": canonical_log_hash(logs)}

    receipt.update(
        {
            "status": "SOURCE_DATA_PASS",
            "chain_id": 1,
            "frozen_source_start_utc": "2023-05-15T00:00:00Z",
            "frozen_source_end_utc": "2024-12-31T23:59:59Z",
            "start_block": start_block,
            "end_block": end_block,
            "max_allowed_block": MAX_ALLOWED_BLOCK,
            "withdrawal_queue_deploy_block": deploy_block,
            "historical_state_calls_early": state_early,
            "historical_state_calls_late": state_late,
            "bounded_event_receipts": event_receipts,
            "protected_period_firewall": "PASS",
            "price_outcomes_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
        }
    )
    return receipt


def main() -> int:
    failures: list[dict[str, str]] = []
    winning_receipt: dict[str, Any] | None = None
    for url in PROVIDERS:
        label = url.split("//", 1)[-1].split("/", 1)[0]
        try:
            winning_receipt = probe_provider(url)
            break
        except Exception as e:
            failures.append({"provider": label, "error": str(e)[:240]})

    out = {
        "lab_id": LAB_ID,
        "probe_version": "0.1",
        "governance": "SOURCE_ONLY_OUTCOME_BLIND",
        "result": winning_receipt["status"] if winning_receipt else "SOURCE_ACQUISITION_TECHNICAL_FAILURE",
        "passing_provider_receipt": winning_receipt,
        "provider_failures": failures,
        "safety": {
            "price_outcomes_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "protected_period_end_utc": "2024-12-31T23:59:59Z",
            "max_allowed_block": MAX_ALLOWED_BLOCK,
        },
    }
    raw = json.dumps(out, indent=2, sort_keys=True)
    outdir = Path("source_gate_output")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "STETH_REDEMPTION_BASIS_001_SOURCE_GATE_RECEIPT_V0_1.json").write_text(raw + "\n", encoding="utf-8")
    # Safe console summary: no economic values or event payloads.
    print(json.dumps({
        "lab_id": LAB_ID,
        "result": out["result"],
        "passing_provider": (winning_receipt or {}).get("provider"),
        "providers_failed": len(failures),
        "protected_period_firewall": "PASS",
        "price_outcomes_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if winning_receipt else 1


if __name__ == "__main__":
    sys.exit(main())
