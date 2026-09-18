#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_CEILING, getcontext
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

getcontext().prec = 60

LAB_ID = "STETH-REDEMPTION-BASIS-002"
MVE_ID = "STETH002-REDEEM-CONVERGENCE-H14-V01"
SOURCE_RUN_ID = 35386033845
SOURCE_ARTIFACT_ID = 10563803871
SOURCE_ARTIFACT_DIGEST = "sha256:d1c371d5dda3718bb044f9a6b2cd628d8c35cd55af8ba85040375ee903110f53"
SOURCE_HEAD_SHA = "dbc396c8d161bfd2ed097449d184d9fd0c69987b"
FINAL_PROTOCOL_COMMIT = "80c9a30d4abcedbc86a951228fb0105c1cd094e9"
IMPLEMENTATION_FREEZE_COMMIT = "06a0cfaa10b8d4d517e3b35bec076ed429c771fa"
TRANSPORT_REMEDIATION_COMMIT = "c7883d43e8977e4dca910cffa34a1cf419e0b967"

QUEUE = "0x889edc2edab5f40e902b864ad4d7ade8e412f9b1"
STETH = "0xae7ab96520de3a18e5e111b5eaab095312d7fe84"
CURVE = "0xdc24316b9ae028f1497c275eb9192a3ea0f67022"

ACTIVATION_BLOCK = 17_266_004
FIRST_SNAPSHOT_BLOCK = 17_272_128
LAST_SNAPSHOT_BLOCK = 21_522_315
HEADER_CEILING_BLOCK = 21_525_890

START_DT = datetime(2023, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
END_DT = datetime(2024, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
HEADER_CEILING_TS = int(datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())
EXPECTED_SNAPSHOTS = 596
ONE_DAY = 86_400
ETH = 10**18
E27 = 10**27
NOTIONAL_WEI = 10 * ETH
BASE_RISK_WEI = 10**16
STRESS_RISK_WEI = 25 * 10**15
MAX_WAIT_SECONDS = 14 * ONE_DAY

PROVIDERS = [
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]
SQD = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
TRANSIENT = {429, 500, 502, 503, 504, 529}
SQD_WINDOW = 40_000

FIN_SIG = "WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)"
REBASE_SIG = "TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
FIN_TOPIC = "0x" + keccak(FIN_SIG.encode()).hex()
REBASE_TOPIC = "0x" + keccak(REBASE_SIG.encode()).hex()

CHECKPOINTS_POSITION = int.from_bytes(keccak(b"lido.WithdrawalQueue.checkpoints"), "big")

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260918


def selector(sig: str) -> str:
    return "0x" + keccak(sig.encode())[:4].hex()


def enc_u(x: int) -> str:
    return int(x).to_bytes(32, "big", signed=False).hex()


def enc_i(x: int) -> str:
    return int(x).to_bytes(32, "big", signed=True).hex()


def calldata_uint(sig: str, x: int) -> str:
    return selector(sig) + enc_u(x)


def calldata_get_dy() -> str:
    return selector("get_dy(int128,int128,uint256)") + enc_i(0) + enc_i(1) + enc_u(NOTIONAL_WEI)


def as_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 16) if v.startswith("0x") else int(v)
    raise TypeError(f"bad int {type(v).__name__}")


def topic_uint(t: str) -> int:
    s = str(t)
    if not s.startswith("0x") or len(s) != 66:
        raise ValueError("bad uint topic")
    return int(s, 16)


def words(data: str, n: int) -> list[int]:
    s = str(data)
    h = s[2:] if s.startswith("0x") else ""
    if len(h) < 64 * n or len(h) % 64:
        raise ValueError(f"bad ABI data length {len(h)} for {n} words")
    return [int(h[i * 64:(i + 1) * 64], 16) for i in range(n)]


def dec_ceil(x: Decimal) -> int:
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def rpc_json(endpoint: str, payload: Any, stats: Counter[str], retries: int = 4) -> Any:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.post(
                endpoint,
                json=payload,
                timeout=(10, 60),
                headers={"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/discovery-v0.1"},
            )
            stats["rpc_http_attempts"] += 1
            if r.status_code in TRANSIENT:
                stats["rpc_transient"] += 1
                r.close()
                time.sleep(min(8.0, 1.25 * (attempt + 1)))
                continue
            r.raise_for_status()
            out = r.json()
            r.close()
            return out
        except Exception as exc:
            last = exc
            stats["rpc_exceptions"] += 1
            if attempt < retries - 1:
                time.sleep(min(8.0, 1.25 * (attempt + 1)))
    raise RuntimeError(f"RPC {endpoint} failed: {type(last).__name__}: {str(last)[:300]}")


def rpc_single(endpoint: str, method: str, params: list[Any], stats: Counter[str]) -> Any:
    out = rpc_json(endpoint, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, stats)
    if not isinstance(out, dict):
        raise RuntimeError("single RPC non-dict")
    if out.get("error") is not None:
        raise RuntimeError(f"RPC error {out['error']}")
    return out.get("result")


def rpc_batch(endpoint: str, requests_: list[tuple[str, list[Any]]], stats: Counter[str], depth: int = 0) -> list[Any]:
    if not requests_:
        return []
    transient_codes = {429, -32005, -32016, -32000}
    max_attempts = 6
    last_error = None

    for attempt in range(max_attempts):
        payload = [
            {"jsonrpc": "2.0", "id": i, "method": method, "params": params}
            for i, (method, params) in enumerate(requests_)
        ]
        out = rpc_json(endpoint, payload, stats)
        if not isinstance(out, list):
            last_error = RuntimeError("batch RPC non-list")
        else:
            byid = {x.get("id"): x for x in out if isinstance(x, dict)}
            vals = []
            transient_item_error = False
            terminal_item_error = None
            for i in range(len(payload)):
                x = byid.get(i)
                if not x:
                    terminal_item_error = RuntimeError(f"batch RPC item {i} missing")
                    break
                err = x.get("error")
                if err is not None:
                    code = err.get("code") if isinstance(err, dict) else None
                    msg = str(err.get("message", "")) if isinstance(err, dict) else str(err)
                    if code in transient_codes or "rate" in msg.lower() or "throughput" in msg.lower() or "compute units" in msg.lower():
                        transient_item_error = True
                        stats["rpc_batch_transient_item_errors"] += 1
                        break
                    terminal_item_error = RuntimeError(f"batch RPC item {i} failed: {err}")
                    break
                vals.append(x.get("result"))
            if terminal_item_error is None and not transient_item_error and len(vals) == len(payload):
                return vals
            if terminal_item_error is not None:
                raise terminal_item_error
            last_error = RuntimeError("transient batch item throttling")

        if attempt < max_attempts - 1:
            delay = min(20.0, 1.5 * (2 ** attempt))
            stats["rpc_batch_transient_retries"] += 1
            time.sleep(delay)

    if len(requests_) > 1 and depth < 8:
        mid = len(requests_) // 2
        stats["rpc_batch_recursive_splits"] += 1
        left = rpc_batch(endpoint, requests_[:mid], stats, depth + 1)
        right = rpc_batch(endpoint, requests_[mid:], stats, depth + 1)
        return left + right

    raise RuntimeError(f"batch RPC transient throttling exhausted after retries: {last_error}")


def decode_uint_results(vals: list[Any]) -> tuple[int, ...]:
    out = []
    for v in vals:
        if not isinstance(v, str) or not v.startswith("0x"):
            raise RuntimeError("invalid uint RPC result")
        out.append(int(v, 16))
    return tuple(out)


def exact_quorum_batch(requests_: list[tuple[str, list[Any]]], stats: Counter[str]) -> tuple[int, ...]:
    votes: dict[tuple[int, ...], list[str]] = defaultdict(list)
    errors = []
    for ep in PROVIDERS:
        try:
            vals = decode_uint_results(rpc_batch(ep, requests_, stats))
            votes[vals].append(ep)
            if len(votes[vals]) >= 2:
                stats["state_quorum_passes"] += 1
                return vals
        except Exception as exc:
            errors.append(f"{ep}: {type(exc).__name__}: {str(exc)[:220]}")
    raise RuntimeError(f"no exact state quorum; votes={{{', '.join(f'{k}:{len(v)}' for k,v in votes.items())}}}; errors={errors[:3]}")


def get_header(endpoint: str, block: int, stats: Counter[str]) -> dict[str, Any]:
    x = rpc_single(endpoint, "eth_getBlockByNumber", [hex(block), False], stats)
    if not isinstance(x, dict):
        raise RuntimeError(f"missing block header {block}")
    ts = int(x["timestamp"], 16)
    if ts > HEADER_CEILING_TS:
        raise RuntimeError("protected-period header rejected")
    return x


def first_block_at_or_after(target_ts: int, lo: int, hi: int, stats: Counter[str]) -> tuple[int, int, str]:
    ep = PROVIDERS[0]
    hlo = get_header(ep, lo, stats)
    hhi = get_header(ep, hi, stats)
    if int(hlo["timestamp"], 16) > target_ts or int(hhi["timestamp"], 16) < target_ts:
        raise RuntimeError(f"timestamp bracket failure target={target_ts} lo={lo} hi={hi}")
    while lo < hi:
        mid = (lo + hi) // 2
        h = get_header(ep, mid, stats)
        if int(h["timestamp"], 16) < target_ts:
            lo = mid + 1
        else:
            hi = mid
    h = get_header(ep, lo, stats)
    p = get_header(ep, lo - 1, stats)
    ts = int(h["timestamp"], 16)
    pts = int(p["timestamp"], 16)
    if ts < target_ts or pts >= target_ts:
        raise RuntimeError("first-block-at-or-after invariant failed")
    return lo, ts, str(h["hash"]).lower()


def verify_mapped_headers(mapped: list[dict[str, Any]], stats: Counter[str]) -> None:
    for verifier in PROVIDERS[1:]:
        try:
            for start in range(0, len(mapped), 80):
                chunk = mapped[start:start + 80]
                reqs = [("eth_getBlockByNumber", [hex(x["block"]), False]) for x in chunk]
                vals = rpc_batch(verifier, reqs, stats)
                for expected, got in zip(chunk, vals):
                    if not isinstance(got, dict):
                        raise RuntimeError("header verify missing block")
                    if int(got["number"], 16) != expected["block"]:
                        raise RuntimeError("header verify block mismatch")
                    if int(got["timestamp"], 16) != expected["timestamp"]:
                        raise RuntimeError("header verify timestamp mismatch")
                    if str(got["hash"]).lower() != expected["hash"]:
                        raise RuntimeError("header verify hash mismatch")
            stats["header_secondary_provider_passes"] += 1
            return
        except Exception:
            stats["header_secondary_provider_failures"] += 1
    raise RuntimeError("no second provider verified all mapped headers")


def headers_batch(endpoint: str, blocks: list[int], stats: Counter[str]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    unique = sorted(set(blocks))
    for start in range(0, len(unique), 80):
        chunk = unique[start:start + 80]
        vals = rpc_batch(endpoint, [("eth_getBlockByNumber", [hex(b), False]) for b in chunk], stats)
        for b, h in zip(chunk, vals):
            if not isinstance(h, dict):
                raise RuntimeError(f"missing batched header {b}")
            if int(h["number"], 16) != b:
                raise RuntimeError("batched header number mismatch")
            ts = int(h["timestamp"], 16)
            if ts > HEADER_CEILING_TS:
                raise RuntimeError("protected-period batched header rejected")
            out[b] = h
    return out


def map_daily_snapshots(stats: Counter[str]) -> list[dict[str, Any]]:
    targets = []
    dt = START_DT
    while dt <= END_DT:
        targets.append(int(dt.timestamp()))
        dt += timedelta(days=1)
    if len(targets) != EXPECTED_SNAPSHOTS:
        raise RuntimeError(f"snapshot target count mismatch {len(targets)}")

    primary = PROVIDERS[0]
    lower_block = FIRST_SNAPSHOT_BLOCK - 1
    upper_block = LAST_SNAPSHOT_BLOCK
    edge = headers_batch(primary, [lower_block, upper_block], stats)
    if int(edge[lower_block]["timestamp"], 16) >= targets[0]:
        raise RuntimeError("lower snapshot mapping bracket invalid")
    if int(edge[upper_block]["timestamp"], 16) < targets[-1]:
        raise RuntimeError("upper snapshot mapping bracket invalid")

    lo = [lower_block] * len(targets)
    hi = [upper_block] * len(targets)
    rounds = 0
    while True:
        active = [i for i in range(len(targets)) if lo[i] + 1 < hi[i]]
        if not active:
            break
        mids = sorted(set((lo[i] + hi[i]) // 2 for i in active))
        hdrs = headers_batch(primary, mids, stats)
        for i in active:
            mid = (lo[i] + hi[i]) // 2
            ts = int(hdrs[mid]["timestamp"], 16)
            if ts < targets[i]:
                lo[i] = mid
            else:
                hi[i] = mid
        rounds += 1
        if rounds > 32:
            raise RuntimeError("vectorized timestamp mapping exceeded 32 rounds")
        print(json.dumps({
            "progress": "snapshot_mapping_round",
            "round": rounds,
            "active": len(active),
            "unique_mid_headers": len(mids),
        }, sort_keys=True), flush=True)

    final_headers = headers_batch(primary, hi, stats)
    mapped = []
    for target, bn in zip(targets, hi):
        h = final_headers[bn]
        ts = int(h["timestamp"], 16)
        # Verify immediate predecessor invariant on primary in one batched pass later.
        mapped.append({
            "target_timestamp": target,
            "block": bn,
            "timestamp": ts,
            "hash": str(h["hash"]).lower(),
            "baseFeePerGas": int(h["baseFeePerGas"], 16),
        })

    prev_headers = headers_batch(primary, [x["block"] - 1 for x in mapped], stats)
    for x in mapped:
        pts = int(prev_headers[x["block"] - 1]["timestamp"], 16)
        if x["timestamp"] < x["target_timestamp"] or pts >= x["target_timestamp"]:
            raise RuntimeError("mapped first-block invariant failed")

    if mapped[0]["block"] != FIRST_SNAPSHOT_BLOCK:
        raise RuntimeError(f"first mapped block drift {mapped[0]['block']} != {FIRST_SNAPSHOT_BLOCK}")
    if mapped[-1]["block"] != LAST_SNAPSHOT_BLOCK:
        raise RuntimeError(f"last mapped block drift {mapped[-1]['block']} != {LAST_SNAPSHOT_BLOCK}")

    verify_mapped_headers(mapped, stats)
    return mapped


def sqd_post(body: dict[str, Any], stats: Counter[str]) -> requests.Response:
    last: Exception | None = None
    for attempt in range(8):
        try:
            r = requests.post(
                SQD,
                json=body,
                stream=True,
                timeout=(20, 180),
                headers={"Content-Type": "application/json", "Accept-Encoding": "gzip", "User-Agent": f"{LAB_ID}/discovery-sqd-v0.1"},
            )
            stats["sqd_http_attempts"] += 1
            if r.status_code in TRANSIENT:
                stats["sqd_transient"] += 1
                r.close()
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            stats["sqd_exceptions"] += 1
            if attempt < 7:
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
    raise RuntimeError(f"SQD failed: {type(last).__name__}: {str(last)[:300]}")


def acquire_event(address: str, topic0: str, start: int, end: int, data_words: int, stats: Counter[str]) -> list[dict[str, Any]]:
    cursor = start
    out = []
    seen: set[tuple[str, int]] = set()
    while cursor <= end:
        request_to = min(end, cursor + SQD_WINDOW - 1)
        body = {
            "type": "evm",
            "fromBlock": cursor,
            "toBlock": request_to,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": {"address": True, "topics": True, "data": True, "transactionHash": True, "logIndex": True},
            },
            "logs": [{"address": [address], "topic0": [topic0]}],
        }
        r = sqd_post(body, stats)
        page_last = None
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"SQD portal error {obj['error']}")
                h = obj.get("header") or obj.get("block") or {}
                bn = as_int(h.get("number"))
                bts = as_int(h.get("timestamp"))
                if not (cursor <= bn <= request_to):
                    raise RuntimeError("SQD row outside exact window")
                if page_last is not None and bn < page_last:
                    raise RuntimeError("SQD page non-monotonic")
                page_last = bn
                if bts > HEADER_CEILING_TS:
                    raise RuntimeError("protected-period event timestamp rejected")
                for log in obj.get("logs") or []:
                    txh = str(log.get("transactionHash", "")).lower()
                    li = as_int(log.get("logIndex"))
                    key = (txh, li)
                    if not txh or key in seen:
                        raise RuntimeError("missing/duplicate canonical event identity")
                    seen.add(key)
                    topics = [str(x).lower() for x in (log.get("topics") or [])]
                    if not topics or topics[0] != topic0:
                        raise RuntimeError("event topic mismatch")
                    d = words(log.get("data", ""), data_words)
                    out.append({
                        "block": bn, "block_timestamp": bts, "transactionHash": txh, "logIndex": li,
                        "topics": topics, "data_words": d,
                    })
        finally:
            r.close()
        stats["sqd_windows_completed"] += 1
        if page_last is None:
            stats["sqd_empty_windows"] += 1
            cursor = request_to + 1
        else:
            if page_last < cursor:
                raise RuntimeError("SQD continuation failed to advance")
            cursor = page_last + 1
    return out


def decode_finalizations(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for ordinal, r in enumerate(sorted(raw, key=lambda x: (x["block"], x["logIndex"], x["transactionHash"])), start=1):
        if len(r["topics"]) < 3 or len(r["data_words"]) < 3:
            raise RuntimeError("malformed WithdrawalsFinalized")
        amount, shares, event_ts = r["data_words"][:3]
        if event_ts > HEADER_CEILING_TS:
            raise RuntimeError("protected finalization event")
        rows.append({
            "ordinal": ordinal,
            "block": r["block"],
            "logIndex": r["logIndex"],
            "tx": r["transactionHash"],
            "from": topic_uint(r["topics"][1]),
            "to": topic_uint(r["topics"][2]),
            "amount_eth_locked": amount,
            "shares_to_burn": shares,
            "timestamp": event_ts,
        })
    prev_to = 0
    for x in rows:
        if x["from"] != prev_to + 1:
            raise RuntimeError(f"non-contiguous finalization queue {x['from']} vs {prev_to + 1}")
        if x["to"] < x["from"]:
            raise RuntimeError("invalid finalization range")
        prev_to = x["to"]
    return rows


def decode_rebases(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in sorted(raw, key=lambda x: (x["block"], x["logIndex"], x["transactionHash"])):
        if len(r["topics"]) < 2 or len(r["data_words"]) < 6:
            raise RuntimeError("malformed TokenRebased")
        time_elapsed, pre_shares, pre_eth, post_shares, post_eth, fee_shares = r["data_words"][:6]
        report_ts = topic_uint(r["topics"][1])
        if report_ts > HEADER_CEILING_TS:
            raise RuntimeError("protected rebase report timestamp")
        if pre_shares <= 0 or pre_eth <= 0 or post_shares <= 0 or post_eth <= 0:
            raise RuntimeError("non-positive TokenRebased totals")
        rows.append({
            "block": r["block"], "logIndex": r["logIndex"], "tx": r["transactionHash"],
            "report_timestamp": report_ts, "time_elapsed": time_elapsed,
            "pre_total_shares": pre_shares, "pre_total_eth": pre_eth,
            "post_total_shares": post_shares, "post_total_eth": post_eth,
            "shares_minted_as_fees": fee_shares,
        })
    return rows


def trailing_apr(ts: int, rebases: list[dict[str, Any]]) -> Decimal | None:
    lo = ts - 7 * ONE_DAY
    selected = [r for r in rebases if lo < r["report_timestamp"] <= ts]
    if not selected:
        return None
    g = Decimal(1)
    for r in selected:
        pre = Decimal(r["pre_total_eth"]) / Decimal(r["pre_total_shares"])
        post = Decimal(r["post_total_eth"]) / Decimal(r["post_total_shares"])
        g *= post / pre
    return (g ** (Decimal(365) / Decimal(7))) - Decimal(1)


def trailing_finalized(ts: int, finalizations: list[dict[str, Any]]) -> int:
    lo = ts - 14 * ONE_DAY
    return sum(x["amount_eth_locked"] for x in finalizations if lo < x["timestamp"] <= ts)


def snapshot_state(snapshot: dict[str, Any], stats: Counter[str]) -> dict[str, Any]:
    block = snapshot["block"]
    vals = exact_quorum_batch([
        ("eth_call", [{"to": CURVE, "data": calldata_get_dy()}, hex(block)]),
        ("eth_call", [{"to": QUEUE, "data": selector("getLastRequestId()")}, hex(block)]),
        ("eth_call", [{"to": QUEUE, "data": selector("unfinalizedStETH()")}, hex(block)]),
    ], stats)
    quote, last_request_id, unfinalized = vals
    acquired_base = quote * 9998 // 10000
    acquired_stress = quote * 9995 // 10000

    shares_base, shares_stress = exact_quorum_batch([
        ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", acquired_base)}, hex(block)]),
        ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", acquired_stress)}, hex(block)]),
    ], stats)

    next_block = block + 1
    if next_block > LAST_SNAPSHOT_BLOCK + 1:
        raise RuntimeError("next-block state beyond frozen boundary")
    request_steth_base, request_steth_stress = exact_quorum_batch([
        ("eth_call", [{"to": STETH, "data": calldata_uint("getPooledEthByShares(uint256)", shares_base)}, hex(next_block)]),
        ("eth_call", [{"to": STETH, "data": calldata_uint("getPooledEthByShares(uint256)", shares_stress)}, hex(next_block)]),
    ], stats)
    request_shares_base, request_shares_stress = exact_quorum_batch([
        ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", request_steth_base)}, hex(next_block)]),
        ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", request_steth_stress)}, hex(next_block)]),
    ], stats)

    if min(quote, acquired_base, shares_base, request_steth_base, request_shares_base) <= 0:
        raise RuntimeError("non-positive snapshot economic state")

    base_fee = int(snapshot["baseFeePerGas"])
    return {
        "quote_wei": quote,
        "last_request_id": last_request_id,
        "unfinalized_steth_wei": unfinalized,
        "acquired_base_wei": acquired_base,
        "acquired_stress_wei": acquired_stress,
        "request_steth_base_wei": request_steth_base,
        "request_steth_stress_wei": request_steth_stress,
        "request_shares_base": request_shares_base,
        "request_shares_stress": request_shares_stress,
        "base_fee_per_gas": base_fee,
    }



def bulk_snapshot_states(mapped: list[dict[str, Any]], stats: Counter[str]) -> list[dict[str, Any]]:
    n = len(mapped)
    states: list[dict[str, Any]] = [{} for _ in range(n)]
    chunk_size = 20

    # Stage 1: Curve quote + queue position + queue backlog.
    for start in range(0, n, chunk_size):
        chunk = list(range(start, min(n, start + chunk_size)))
        reqs: list[tuple[str, list[Any]]] = []
        for i in chunk:
            b = mapped[i]["block"]
            reqs.extend([
                ("eth_call", [{"to": CURVE, "data": calldata_get_dy()}, hex(b)]),
                ("eth_call", [{"to": QUEUE, "data": selector("getLastRequestId()")}, hex(b)]),
                ("eth_call", [{"to": QUEUE, "data": selector("unfinalizedStETH()")}, hex(b)]),
            ])
        vals = exact_quorum_batch(reqs, stats)
        p = 0
        for i in chunk:
            quote, last_request_id, unfinalized = vals[p:p + 3]
            p += 3
            states[i].update({
                "quote_wei": quote,
                "last_request_id": last_request_id,
                "unfinalized_steth_wei": unfinalized,
                "acquired_base_wei": quote * 9998 // 10000,
                "acquired_stress_wei": quote * 9995 // 10000,
                "base_fee_per_gas": mapped[i]["baseFeePerGas"],
            })
        print(json.dumps({"progress": "snapshot_state_stage1", "done": chunk[-1] + 1, "total": n}, sort_keys=True), flush=True)

    # Stage 2: acquired stETH -> shares at snapshot.
    for start in range(0, n, chunk_size):
        chunk = list(range(start, min(n, start + chunk_size)))
        reqs = []
        for i in chunk:
            b = mapped[i]["block"]
            reqs.extend([
                ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", states[i]["acquired_base_wei"])}, hex(b)]),
                ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", states[i]["acquired_stress_wei"])}, hex(b)]),
            ])
        vals = exact_quorum_batch(reqs, stats)
        p = 0
        for i in chunk:
            states[i]["snapshot_shares_base"], states[i]["snapshot_shares_stress"] = vals[p:p + 2]
            p += 2
        print(json.dumps({"progress": "snapshot_state_stage2", "done": chunk[-1] + 1, "total": n}, sort_keys=True), flush=True)

    # Stage 3: same acquired shares -> full stETH balance in next block.
    for start in range(0, n, chunk_size):
        chunk = list(range(start, min(n, start + chunk_size)))
        reqs = []
        for i in chunk:
            nb = mapped[i]["block"] + 1
            if nb > HEADER_CEILING_BLOCK:
                raise RuntimeError("next-block state exceeds protected block ceiling")
            reqs.extend([
                ("eth_call", [{"to": STETH, "data": calldata_uint("getPooledEthByShares(uint256)", states[i]["snapshot_shares_base"])}, hex(nb)]),
                ("eth_call", [{"to": STETH, "data": calldata_uint("getPooledEthByShares(uint256)", states[i]["snapshot_shares_stress"])}, hex(nb)]),
            ])
        vals = exact_quorum_batch(reqs, stats)
        p = 0
        for i in chunk:
            states[i]["request_steth_base_wei"], states[i]["request_steth_stress_wei"] = vals[p:p + 2]
            p += 2
        print(json.dumps({"progress": "snapshot_state_stage3", "done": chunk[-1] + 1, "total": n}, sort_keys=True), flush=True)

    # Stage 4: exact request shares in next block.
    for start in range(0, n, chunk_size):
        chunk = list(range(start, min(n, start + chunk_size)))
        reqs = []
        for i in chunk:
            nb = mapped[i]["block"] + 1
            reqs.extend([
                ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", states[i]["request_steth_base_wei"])}, hex(nb)]),
                ("eth_call", [{"to": STETH, "data": calldata_uint("getSharesByPooledEth(uint256)", states[i]["request_steth_stress_wei"])}, hex(nb)]),
            ])
        vals = exact_quorum_batch(reqs, stats)
        p = 0
        for i in chunk:
            states[i]["request_shares_base"], states[i]["request_shares_stress"] = vals[p:p + 2]
            p += 2
            required = [
                states[i]["quote_wei"], states[i]["acquired_base_wei"], states[i]["acquired_stress_wei"],
                states[i]["snapshot_shares_base"], states[i]["snapshot_shares_stress"],
                states[i]["request_steth_base_wei"], states[i]["request_steth_stress_wei"],
                states[i]["request_shares_base"], states[i]["request_shares_stress"],
            ]
            if min(required) <= 0:
                raise RuntimeError(f"non-positive snapshot economic state at index {i}")
        print(json.dumps({"progress": "snapshot_state_stage4", "done": chunk[-1] + 1, "total": n}, sort_keys=True), flush=True)

    return states

def checkpoint_at_finalization(fin: dict[str, Any], stats: Counter[str]) -> tuple[int, int]:
    idx = fin["ordinal"]
    key = idx.to_bytes(32, "big") + CHECKPOINTS_POSITION.to_bytes(32, "big")
    base_slot = int.from_bytes(keccak(key), "big")
    reqs = [
        ("eth_getStorageAt", [QUEUE, hex(base_slot), hex(fin["block"])]),
        ("eth_getStorageAt", [QUEUE, hex(base_slot + 1), hex(fin["block"])]),
    ]
    vals = exact_quorum_batch(reqs, stats)
    from_request_id, max_share_rate = vals
    if from_request_id != fin["from"]:
        raise RuntimeError(
            f"checkpoint provenance mismatch ordinal={idx} storage_from={from_request_id} event_from={fin['from']}"
        )
    if max_share_rate <= 0:
        raise RuntimeError("non-positive checkpoint maxShareRate")
    return from_request_id, max_share_rate


def exact_claim(request_steth: int, request_shares: int, max_share_rate: int) -> int:
    if request_shares <= 0:
        raise RuntimeError("zero request shares")
    request_share_rate = request_steth * E27 // request_shares
    if request_share_rate > max_share_rate:
        return request_shares * max_share_rate // E27
    return request_steth


def moving_block_bootstrap_lower(values: list[int]) -> float | None:
    n = len(values)
    if n == 0:
        return None
    block_len = max(2, math.ceil(n ** (1 / 3)))
    rng = random.Random(BOOTSTRAP_SEED)
    means: list[float] = []
    vals = [v / ETH for v in values]
    for _ in range(BOOTSTRAP_REPS):
        sample = []
        while len(sample) < n:
            start = rng.randrange(n)
            for k in range(block_len):
                sample.append(vals[(start + k) % n])
                if len(sample) == n:
                    break
        means.append(sum(sample) / n)
    means.sort()
    idx = max(0, min(len(means) - 1, math.floor(0.025 * (len(means) - 1))))
    return means[idx]


def pct_digest(mapped: list[dict[str, Any]]) -> str:
    blob = "\n".join(f"{x['target_timestamp']}|{x['block']}|{x['timestamp']}|{x['hash']}" for x in mapped)
    return hashlib.sha256(blob.encode()).hexdigest()


def self_test() -> None:
    assert exact_claim(1000, 1000, E27) == 1000
    assert exact_claim(1000, 1000, E27 - 1) == 999
    slot1 = int.from_bytes(keccak((1).to_bytes(32, "big") + CHECKPOINTS_POSITION.to_bytes(32, "big")), "big")
    slot2 = int.from_bytes(keccak((2).to_bytes(32, "big") + CHECKPOINTS_POSITION.to_bytes(32, "big")), "big")
    assert slot1 != slot2
    raw_fin = [{
        "block": 10, "logIndex": 1, "transactionHash": "0xabc",
        "topics": [FIN_TOPIC, "0x" + (1).to_bytes(32, "big").hex(), "0x" + (3).to_bytes(32, "big").hex()],
        "data_words": [100, 50, 1000],
    }, {
        "block": 11, "logIndex": 2, "transactionHash": "0xdef",
        "topics": [FIN_TOPIC, "0x" + (4).to_bytes(32, "big").hex(), "0x" + (5).to_bytes(32, "big").hex()],
        "data_words": [60, 30, 2000],
    }]
    d = decode_finalizations(raw_fin)
    assert d[0]["ordinal"] == 1 and d[1]["ordinal"] == 2 and d[1]["from"] == 4
    bs1 = moving_block_bootstrap_lower([1, 2, 3, 4, 5])
    bs2 = moving_block_bootstrap_lower([1, 2, 3, 4, 5])
    assert bs1 == bs2
    synthetic_rebases = [{
        "report_timestamp": 1_000_000,
        "pre_total_eth": 1000,
        "pre_total_shares": 1000,
        "post_total_eth": 1001,
        "post_total_shares": 1000,
    }]
    apr = trailing_apr(1_000_000, synthetic_rebases)
    assert apr is not None and apr > 0
    assert calldata_get_dy().startswith("0x") and len(calldata_get_dy()) == 2 + 8 + 64 * 3
    assert TRANSPORT_REMEDIATION_COMMIT == "c7883d43e8977e4dca910cffa34a1cf419e0b967"
    print(json.dumps({
        "classification": "STETH002_DISCOVERY_SELF_TEST_PASS",
        "checkpoint_slot_distinct": True,
        "claim_formula_pass": True,
        "bootstrap_deterministic": True,
    }, sort_keys=True))


def run_discovery() -> int:
    outdir = Path("out/steth_redemption_basis_002_discovery")
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = outdir / "STETH_REDEMPTION_BASIS_002_DISCOVERY_V0_1.json"
    stats: Counter[str] = Counter()
    receipt: dict[str, Any] = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "phase": "DISCOVERY_V0_1",
        "source_binding": {
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
            "source_head_sha": SOURCE_HEAD_SHA,
            "final_protocol_commit": FINAL_PROTOCOL_COMMIT,
            "implementation_freeze_commit": IMPLEMENTATION_FREEZE_COMMIT,
            "transport_remediation_commit": TRANSPORT_REMEDIATION_COMMIT,
        },
        "safety": {
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "wallet_access": False,
            "orders_created": False,
            "exchange_mutation": False,
            "leverage_deployed": False,
            "main_merge": False,
            "market_direction_returns_opened": False,
        },
    }
    try:
        # Source receipt binding.
        source_files = list(Path("downloaded_source_gate").rglob("*.json"))
        if len(source_files) != 1:
            raise RuntimeError(f"expected exactly one source receipt, got {len(source_files)}")
        source = json.loads(source_files[0].read_text())
        if source.get("lab_id") != LAB_ID or source.get("classification") != "SOURCE_DATA_PASS":
            raise RuntimeError("exact SOURCE_DATA_PASS not found")
        if source.get("agreed_start_block") != FIRST_SNAPSHOT_BLOCK or source.get("agreed_end_block") != LAST_SNAPSHOT_BLOCK:
            raise RuntimeError("source edge block binding mismatch")
        if source.get("expected_daily_snapshot_population") != EXPECTED_SNAPSHOTS:
            raise RuntimeError("source snapshot-count binding mismatch")

        # Full canonical events before snapshot economics.
        fin_raw = acquire_event(QUEUE, FIN_TOPIC, ACTIVATION_BLOCK, LAST_SNAPSHOT_BLOCK, 3, stats)
        finalizations = decode_finalizations(fin_raw)
        if not finalizations:
            raise RuntimeError("zero canonical WithdrawalsFinalized events")

        # Find a conservative block before seven-day lookback.
        lookback_ts = int((START_DT - timedelta(days=7)).timestamp())
        lookback_block, _, _ = first_block_at_or_after(lookback_ts, 17_150_000, FIRST_SNAPSHOT_BLOCK, stats)
        rebase_raw = acquire_event(STETH, REBASE_TOPIC, lookback_block, LAST_SNAPSHOT_BLOCK, 6, stats)
        rebases = decode_rebases(rebase_raw)
        if not rebases:
            raise RuntimeError("zero canonical TokenRebased events")

        mapped = map_daily_snapshots(stats)
        states = bulk_snapshot_states(mapped, stats)

        fin_froms = [x["from"] for x in finalizations]
        candidate_count = 0
        signal_count = 0
        ignored_overlap = 0
        no_signal_source = 0
        no_signal_queue = 0
        no_signal_edge = 0
        completed: list[dict[str, Any]] = []
        censored: list[dict[str, Any]] = []
        op_failures: list[dict[str, Any]] = []
        active_until: int | None = None
        capital_failed = False

        for idx, snap in enumerate(mapped):
            ts = snap["target_timestamp"]
            if active_until is not None and ts <= active_until:
                ignored_overlap += 1
                continue
            if capital_failed:
                break

            candidate_count += 1
            apr = trailing_apr(ts, rebases)
            if apr is None:
                no_signal_source += 1
                continue
            finalized_14d = trailing_finalized(ts, finalizations)
            if finalized_14d <= 0:
                no_signal_queue += 1
                continue

            st = states[idx]
            daily_throughput = Decimal(finalized_14d) / Decimal(14)
            queue_days = Decimal(st["unfinalized_steth_wei"]) / daily_throughput
            if queue_days < Decimal("0.25"):
                queue_days = Decimal("0.25")
            if queue_days > Decimal(14):
                no_signal_queue += 1
                continue

            base_gas = st["base_fee_per_gas"] * 1_000_000  # 800k * 1.25 exactly
            stress_gas = (base_gas * 3 + 1) // 2
            estimated_reward = dec_ceil(
                Decimal(st["acquired_base_wei"]) * apr * queue_days / Decimal(365)
            )
            estimated_edge = (
                st["acquired_base_wei"] - NOTIONAL_WEI - estimated_reward - base_gas - BASE_RISK_WEI
            )
            if estimated_edge <= 0:
                no_signal_edge += 1
                continue

            signal_count += 1
            qpos = st["last_request_id"] + 1

            # First finalization range containing the frozen queue position after entry.
            j = bisect.bisect_right(fin_froms, qpos) - 1
            fin = None
            if j >= 0:
                x = finalizations[j]
                if x["from"] <= qpos <= x["to"] and x["timestamp"] > ts:
                    fin = x
            if fin is None:
                # Search forward in case qpos had not yet entered the first bisected range.
                k = max(0, j + 1)
                while k < len(finalizations):
                    x = finalizations[k]
                    if x["timestamp"] > ts and x["from"] <= qpos <= x["to"]:
                        fin = x
                        break
                    if x["from"] > qpos:
                        break
                    k += 1

            entry = {
                "snapshot_index": idx,
                "entry_timestamp": ts,
                "entry_utc": iso(ts),
                "snapshot_block": snap["block"],
                "queue_position": qpos,
                "estimated_queue_days": float(queue_days),
                "entry_apr_7d": float(apr),
                "estimated_edge_eth": estimated_edge / ETH,
            }

            if fin is None:
                censored.append({**entry, "classification": "RIGHT_CENSORED_PROTECTED_BOUNDARY"})
                active_until = int(END_DT.timestamp())
                break

            holding_seconds = fin["timestamp"] - ts
            holding_days = Decimal(holding_seconds) / Decimal(ONE_DAY)
            if holding_seconds < 0:
                raise RuntimeError("negative holding time")
            if holding_seconds > MAX_WAIT_SECONDS:
                op_failures.append({
                    **entry,
                    "classification": "OPERATIONAL_WAIT_FAILURE",
                    "finalization_timestamp": fin["timestamp"],
                    "holding_days": float(holding_days),
                })
                active_until = fin["timestamp"]
                capital_failed = True
                break

            _, max_share_rate = checkpoint_at_finalization(fin, stats)
            claim_base = exact_claim(
                st["request_steth_base_wei"], st["request_shares_base"], max_share_rate
            )
            claim_stress = exact_claim(
                st["request_steth_stress_wei"], st["request_shares_stress"], max_share_rate
            )
            realized_reward_base = dec_ceil(
                Decimal(st["request_steth_base_wei"]) * apr * holding_days / Decimal(365)
            )
            realized_reward_stress = dec_ceil(
                Decimal(st["request_steth_stress_wei"]) * apr * holding_days / Decimal(365)
            )
            base_net = claim_base - NOTIONAL_WEI - realized_reward_base - base_gas - BASE_RISK_WEI
            stress_net = claim_stress - NOTIONAL_WEI - realized_reward_stress - stress_gas - STRESS_RISK_WEI

            trade = {
                **entry,
                "classification": "COMPLETED",
                "finalization_timestamp": fin["timestamp"],
                "finalization_utc": iso(fin["timestamp"]),
                "finalization_block": fin["block"],
                "checkpoint_index": fin["ordinal"],
                "checkpoint_max_share_rate": str(max_share_rate),
                "holding_days": float(holding_days),
                "curve_quote_eth": st["quote_wei"] / ETH,
                "base_claim_eth": claim_base / ETH,
                "stress_claim_eth": claim_stress / ETH,
                "base_reward_cost_eth": realized_reward_base / ETH,
                "stress_reward_cost_eth": realized_reward_stress / ETH,
                "base_gas_eth": base_gas / ETH,
                "stress_gas_eth": stress_gas / ETH,
                "base_net_eth": base_net / ETH,
                "stress_net_eth": stress_net / ETH,
                "_base_net_wei": base_net,
                "_stress_net_wei": stress_net,
            }
            completed.append(trade)
            active_until = fin["timestamp"]

            if len(completed) % 10 == 0:
                print(json.dumps({
                    "progress": "completed_trades",
                    "completed": len(completed),
                    "signals": signal_count,
                    "last_entry": iso(ts),
                }, sort_keys=True), flush=True)

        nets = [x["_base_net_wei"] for x in completed]
        stress_nets = [x["_stress_net_wei"] for x in completed]
        n = len(nets)
        mean_base = (sum(nets) / n / ETH) if n else None
        median_base = (statistics.median(nets) / ETH) if n else None
        positive_count = sum(1 for x in nets if x > 0)
        positive_rate = (positive_count / n) if n else None
        stress_mean = (sum(stress_nets) / n / ETH) if n else None
        bootstrap_lower = moving_block_bootstrap_lower(nets) if n else None

        by_year: dict[str, dict[str, Any]] = {}
        for year in (2023, 2024):
            yn = [x["_base_net_wei"] for x in completed if datetime.fromtimestamp(x["entry_timestamp"], timezone.utc).year == year]
            by_year[str(year)] = {
                "count": len(yn),
                "mean_base_net_eth": (sum(yn) / len(yn) / ETH) if yn else None,
            }

        positives = [x for x in nets if x > 0]
        largest_positive_share = (max(positives) / sum(positives)) if positives and sum(positives) > 0 else None

        gates = {
            "completed_ge_30": n >= 30,
            "mean_base_gt_0": mean_base is not None and mean_base > 0,
            "median_base_gt_0": median_base is not None and median_base > 0,
            "positive_rate_ge_70pct": positive_rate is not None and positive_rate >= 0.70,
            "bootstrap_95_lower_gt_0": bootstrap_lower is not None and bootstrap_lower > 0,
            "year_2023_ge_10_and_mean_nonnegative": by_year["2023"]["count"] >= 10 and by_year["2023"]["mean_base_net_eth"] is not None and by_year["2023"]["mean_base_net_eth"] >= 0,
            "year_2024_ge_10_and_mean_nonnegative": by_year["2024"]["count"] >= 10 and by_year["2024"]["mean_base_net_eth"] is not None and by_year["2024"]["mean_base_net_eth"] >= 0,
            "largest_positive_share_le_30pct": largest_positive_share is not None and largest_positive_share <= 0.30,
            "stress_mean_gt_0": stress_mean is not None and stress_mean > 0,
            "zero_operational_wait_failures": len(op_failures) == 0,
            "zero_provenance_leakage_violations": True,
        }

        if n < 30:
            classification = "DISCOVERY_INSUFFICIENT_SAMPLE"
        elif all(gates.values()):
            classification = "DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION"
        else:
            classification = "DISCOVERY_NO_REDEMPTION_EDGE"

        for x in completed:
            x.pop("_base_net_wei", None)
            x.pop("_stress_net_wei", None)

        receipt.update({
            "classification": classification,
            "snapshot_universe": {
                "expected": EXPECTED_SNAPSHOTS,
                "mapped": len(mapped),
                "first": mapped[0],
                "last": mapped[-1],
                "mapping_sha256": pct_digest(mapped),
            },
            "source_counts": {
                "withdrawals_finalized": len(finalizations),
                "token_rebased": len(rebases),
            },
            "candidate_counts": {
                "eligible_daily_candidates": candidate_count,
                "signals": signal_count,
                "ignored_due_to_overlap": ignored_overlap,
                "no_signal_missing_trailing_rebase": no_signal_source,
                "no_signal_queue_gate": no_signal_queue,
                "no_signal_nonpositive_estimated_edge": no_signal_edge,
                "completed": len(completed),
                "operational_wait_failures": len(op_failures),
                "right_censored_protected_boundary": len(censored),
            },
            "metrics": {
                "mean_base_net_eth": mean_base,
                "median_base_net_eth": median_base,
                "positive_rate": positive_rate,
                "bootstrap_95_lower_mean_base_net_eth": bootstrap_lower,
                "bootstrap_replications": BOOTSTRAP_REPS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_block_length": max(2, math.ceil(n ** (1 / 3))) if n else None,
                "stress_mean_net_eth": stress_mean,
                "largest_positive_contribution_share": largest_positive_share,
                "by_year": by_year,
            },
            "promotion_gates": gates,
            "completed_trades": completed,
            "operational_wait_failures": op_failures,
            "right_censored_positions": censored,
            "transport_stats": dict(stats),
            "next_authorized_phase": (
                "SEPARATE_REPLICATION_PROTOCOL_ONLY"
                if classification == "DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION"
                else "NONE_NO_RESCUE"
            ),
        })

        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "classification": classification,
            "completed": n,
            "signals": signal_count,
            "mean_base_net_eth": mean_base,
            "median_base_net_eth": median_base,
            "positive_rate": positive_rate,
            "bootstrap_lower": bootstrap_lower,
            "stress_mean_net_eth": stress_mean,
            "operational_wait_failures": len(op_failures),
            "right_censored": len(censored),
        }, sort_keys=True), flush=True)
        return 0

    except Exception as exc:
        receipt.update({
            "classification": "DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE",
            "failure": f"{type(exc).__name__}: {str(exc)[:2000]}",
            "transport_stats": dict(stats),
            "next_authorized_phase": "STOP_TECHNICAL_OR_PROVENANCE",
        })
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "classification": receipt["classification"],
            "failure": receipt["failure"],
        }, sort_keys=True), flush=True)
        return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    return run_discovery()


if __name__ == "__main__":
    sys.exit(main())
