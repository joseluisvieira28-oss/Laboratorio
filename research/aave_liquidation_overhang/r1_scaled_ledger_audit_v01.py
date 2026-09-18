#!/usr/bin/env python3
"""Deterministic R1 scaled-ledger audit for AAVE-LIQUIDATION-OVERHANG-001.

This script is reconstruction-only and outcome-blind. It:
- selects the frozen borrower audit sample from Borrow.onBehalfOf identities;
- replays sample-user scaled aToken and variable-debt balances from token-native
  Mint/Burn/BalanceTransfer events using exact Aave ray rounding;
- validates every touched sample user/token pair at the four frozen audit blocks
  using independent historical scaledBalanceOf() calls;
- never computes health factor, liquidation overhang, future outcomes, returns or PnL.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
AUDIT_BLOCKS = [17_748_972, 19_007_945, 20_266_917, 21_525_890]
SAMPLE_SIZE = 16
MAX_HTTP_BLOCK_WINDOW = 75_000
TRANSIENT = {429, 500, 502, 503, 504, 529}
RAY = 10**27

RPC_ENDPOINTS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.drpc.org",
    "https://1rpc.io/eth",
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
]

BORROW_TOPIC = "0x" + keccak(b"Borrow(address,address,address,uint256,uint8,uint256,uint16)").hex()
MINT_TOPIC = "0x" + keccak(b"Mint(address,address,uint256,uint256,uint256)").hex()
BURN_TOPIC = "0x" + keccak(b"Burn(address,address,uint256,uint256,uint256)").hex()
BALANCE_TRANSFER_TOPIC = "0x" + keccak(b"BalanceTransfer(address,address,uint256,uint256)").hex()
SCALED_BALANCE_SELECTOR = keccak(b"scaledBalanceOf(address)")[:4].hex()


def topic_address(topic: str) -> str:
    t = str(topic).lower()
    if not t.startswith("0x") or len(t) != 66:
        raise ValueError("invalid indexed address topic")
    return "0x" + t[-40:]


def address_topic(addr: str) -> str:
    a = addr.lower()
    if not a.startswith("0x") or len(a) != 42:
        raise ValueError("invalid address")
    return "0x" + "0" * 24 + a[2:]


def as_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 16) if v.startswith("0x") else int(v)
    raise TypeError(f"cannot convert to int: {type(v).__name__}")


def ray_div(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError("rayDiv denominator zero")
    return (a * RAY + b // 2) // b


def decode_words(data: str, n: int) -> list[int]:
    d = str(data)
    if not d.startswith("0x"):
        raise ValueError("log data missing 0x")
    h = d[2:]
    if len(h) < 64 * n or len(h) % 64 != 0:
        raise ValueError(f"invalid ABI data length for {n} words")
    return [int(h[i * 64:(i + 1) * 64], 16) for i in range(n)]


def post_portal(body: dict[str, Any], stats: Counter[str]) -> requests.Response:
    last: Exception | None = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL,
                json=body,
                timeout=(20, 180),
                stream=True,
                headers={
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip",
                    "User-Agent": f"{LAB_ID}/r1-scaled-ledger-audit-v0.1",
                },
            )
            stats["http_attempts"] += 1
            if r.status_code in TRANSIENT:
                last = RuntimeError(f"transient HTTP {r.status_code}")
                retry_after = r.headers.get("Retry-After")
                r.close()
                if attempt < 7:
                    stats["transient_retries"] += 1
                    try:
                        delay = float(retry_after) if retry_after else min(20.0, 1.5 * (2**attempt))
                    except ValueError:
                        delay = min(20.0, 1.5 * (2**attempt))
                    time.sleep(delay)
                    continue
                raise last
            if r.status_code == 204:
                r.close()
                raise RuntimeError("unexpected Portal 204 inside frozen range")
            r.raise_for_status()
            stats["successful_http_responses"] += 1
            return r
        except (requests.RequestException, RuntimeError) as exc:
            last = exc
            if attempt < 7:
                stats["network_retries"] += 1
                time.sleep(min(20.0, 1.5 * (2**attempt)))
                continue
            raise
    raise RuntimeError(str(last))


def stream_portal(log_filters: list[dict[str, Any]], include_data: bool, stats: Counter[str]) -> Iterable[dict[str, Any]]:
    cursor = FROM_BLOCK
    while cursor <= TO_BLOCK:
        request_to = min(TO_BLOCK, cursor + MAX_HTTP_BLOCK_WINDOW - 1)
        log_fields: dict[str, bool] = {
            "address": True,
            "topics": True,
            "transactionHash": True,
            "logIndex": True,
        }
        if include_data:
            log_fields["data"] = True
        body = {
            "type": "evm",
            "fromBlock": cursor,
            "toBlock": request_to,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": log_fields,
            },
            "logs": log_filters,
        }

        # V0.3.1 transport-only hardening:
        # Never yield a partially-read Portal window. If the HTTP body stream is
        # interrupted, discard that incomplete buffer and retry the exact same
        # request body/boundaries. Semantic/JSON/provenance errors still fail closed.
        page_objects: list[dict[str, Any]] | None = None
        page_last: int | None = None
        rows = 0
        for stream_attempt in range(8):
            r = post_portal(body, stats)
            stats["stream_window_attempts"] += 1
            local_objects: list[dict[str, Any]] = []
            local_last: int | None = None
            local_rows = 0
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    obj = json.loads(raw)
                    if isinstance(obj, dict) and obj.get("error"):
                        raise RuntimeError(f"portal error: {obj['error']}")
                    header = obj.get("header") or obj.get("block") or {}
                    bn = header.get("number")
                    if bn is None:
                        raise RuntimeError("Portal row missing continuation block number")
                    bn = int(bn)
                    if not (cursor <= bn <= request_to):
                        raise RuntimeError("Portal row outside requested window")
                    if local_last is not None and bn < local_last:
                        raise RuntimeError("Portal page non-monotonic")
                    local_last = bn
                    local_rows += 1
                    local_objects.append(obj)
            except requests.RequestException:
                stats["stream_read_failures"] += 1
                if stream_attempt < 7:
                    stats["stream_read_retries"] += 1
                    time.sleep(min(20.0, 1.5 * (2**stream_attempt)))
                    continue
                raise
            finally:
                r.close()

            if local_rows == 0 or local_last is None:
                raise RuntimeError("Portal returned empty page inside frozen range")
            page_objects = local_objects
            page_last = local_last
            rows = local_rows
            stats["stream_window_successes"] += 1
            break

        if page_objects is None or page_last is None:
            raise RuntimeError("Portal stream window exhausted retry budget")
        stats["portal_rows"] += rows
        for obj in page_objects:
            yield obj
        cursor = page_last + 1

def load_bootstrap() -> dict[str, Any]:
    explicit = os.environ.get("R0_BOOTSTRAP_PATH")
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(Path("downloaded_r0_bootstrap").rglob("*.json"))
    candidates.extend(Path("r0_parts/bootstrap").rglob("*.json"))
    for p in candidates:
        if p.is_file():
            obj = json.loads(p.read_text(encoding="utf-8"))
            if obj.get("classification") == "RECONSTRUCTION_R0_BOOTSTRAP_PASS":
                return obj
    raise FileNotFoundError("canonical R0 bootstrap receipt not found")


def select_borrowers(stats: Counter[str]) -> tuple[list[str], int]:
    borrowers: set[str] = set()
    seen: set[tuple[str, int]] = set()
    filters = [{"address": [POOL], "topic0": [BORROW_TOPIC]}]
    for obj in stream_portal(filters, False, stats):
        for log in obj.get("logs") or []:
            topics = log.get("topics") or []
            if len(topics) < 3 or str(topics[0]).lower() != BORROW_TOPIC:
                raise RuntimeError("malformed Borrow log")
            txh = str(log.get("transactionHash", "")).lower()
            li = as_int(log.get("logIndex"))
            key = (txh, li)
            if key in seen:
                raise RuntimeError("duplicate Borrow canonical log identity")
            seen.add(key)
            borrowers.add(topic_address(topics[2]))
    if len(seen) != 204_952:
        raise RuntimeError(f"Borrow count mismatch vs canonical R0: {len(seen)} != 204952")
    if len(borrowers) < SAMPLE_SIZE:
        raise RuntimeError("insufficient unique borrowers for frozen sample")
    ranked = sorted(
        borrowers,
        key=lambda a: (keccak(bytes.fromhex(a[2:])), a),
    )
    return ranked[:SAMPLE_SIZE], len(borrowers)


def build_token_maps(bootstrap: dict[str, Any]) -> tuple[dict[str, dict[str, str]], list[str], list[str]]:
    reserves = bootstrap.get("reserves") or {}
    if len(reserves) != 37:
        raise RuntimeError(f"reserve count mismatch: {len(reserves)} != 37")
    token_meta: dict[str, dict[str, str]] = {}
    atokens: list[str] = []
    debts: list[str] = []
    for underlying, meta in reserves.items():
        u = underlying.lower()
        at = str(meta["aToken"]).lower()
        vd = str(meta["variableDebtToken"]).lower()
        if len(at) != 42 or len(vd) != 42:
            raise RuntimeError("invalid token identity in R0 bootstrap")
        if at in token_meta or vd in token_meta:
            raise RuntimeError("duplicate scaled-token identity across reserves")
        token_meta[at] = {"kind": "ATOKEN", "underlying": u}
        token_meta[vd] = {"kind": "VARIABLE_DEBT", "underlying": u}
        atokens.append(at)
        debts.append(vd)
    return token_meta, atokens, debts


def acquire_sample_token_deltas(
    sample: list[str],
    token_meta: dict[str, dict[str, str]],
    atokens: list[str],
    debts: list[str],
    stats: Counter[str],
) -> tuple[dict[tuple[str, str], dict[int, int]], Counter[str], int]:
    sample_set = set(sample)
    sample_topics = [address_topic(a) for a in sample]
    all_tokens = atokens + debts
    filters = [
        {"address": all_tokens, "topic0": [MINT_TOPIC], "topic2": sample_topics},
        {"address": all_tokens, "topic0": [BURN_TOPIC], "topic1": sample_topics},
        {"address": atokens, "topic0": [BALANCE_TRANSFER_TOPIC], "topic1": sample_topics},
        {"address": atokens, "topic0": [BALANCE_TRANSFER_TOPIC], "topic2": sample_topics},
        {"address": debts, "topic0": [BALANCE_TRANSFER_TOPIC]},
    ]
    block_deltas: dict[tuple[str, str], dict[int, int]] = defaultdict(lambda: defaultdict(int))
    counts: Counter[str] = Counter()
    seen: set[tuple[str, int]] = set()
    debt_balance_transfer_count = 0

    for obj in stream_portal(filters, True, stats):
        header = obj.get("header") or obj.get("block") or {}
        bn = int(header["number"])
        if not (FROM_BLOCK <= bn <= TO_BLOCK):
            raise RuntimeError("token event outside frozen envelope")
        for log in obj.get("logs") or []:
            addr = str(log.get("address", "")).lower()
            if addr not in token_meta:
                raise RuntimeError("unexpected token address in token query")
            topics = [str(x).lower() for x in (log.get("topics") or [])]
            if not topics:
                raise RuntimeError("token log without topics")
            txh = str(log.get("transactionHash", "")).lower()
            li = as_int(log.get("logIndex"))
            keyid = (txh, li)
            if keyid in seen:
                # Multiple OR filters can match the same canonical transfer (e.g. sample->sample).
                # Ignore exact filter overlap but never apply the state transition twice.
                counts["filter_overlap_duplicates"] += 1
                continue
            seen.add(keyid)
            t0 = topics[0]
            meta = token_meta[addr]

            if t0 == MINT_TOPIC:
                if len(topics) < 3:
                    raise RuntimeError("Mint missing indexed participant")
                user = topic_address(topics[2])
                if user not in sample_set:
                    raise RuntimeError("Mint participant escaped frozen sample filter")
                value, balance_increase, index = decode_words(str(log.get("data", "")), 3)[:3]
                if index == 0:
                    raise RuntimeError("Mint index zero")
                if value > balance_increase:
                    delta = ray_div(value - balance_increase, index)
                    counts[f"{meta['kind']}_MINT_POSITIVE"] += 1
                elif value < balance_increase:
                    delta = -ray_div(balance_increase - value, index)
                    counts[f"{meta['kind']}_MINT_BURN_PATH"] += 1
                else:
                    delta = 0
                    counts[f"{meta['kind']}_MINT_INTEREST_ONLY"] += 1
                block_deltas[(user, addr)][bn] += delta
                counts[f"{meta['kind']}_MINT"] += 1

            elif t0 == BURN_TOPIC:
                if len(topics) < 2:
                    raise RuntimeError("Burn missing indexed participant")
                user = topic_address(topics[1])
                if user not in sample_set:
                    raise RuntimeError("Burn participant escaped frozen sample filter")
                value, balance_increase, index = decode_words(str(log.get("data", "")), 3)[:3]
                if index == 0:
                    raise RuntimeError("Burn index zero")
                delta = -ray_div(value + balance_increase, index)
                block_deltas[(user, addr)][bn] += delta
                counts[f"{meta['kind']}_BURN"] += 1

            elif t0 == BALANCE_TRANSFER_TOPIC:
                if meta["kind"] == "VARIABLE_DEBT":
                    debt_balance_transfer_count += 1
                    counts["VARIABLE_DEBT_BALANCE_TRANSFER"] += 1
                    continue
                if len(topics) < 3:
                    raise RuntimeError("BalanceTransfer missing indexed participants")
                from_user = topic_address(topics[1])
                to_user = topic_address(topics[2])
                value, index = decode_words(str(log.get("data", "")), 2)[:2]
                if index == 0:
                    raise RuntimeError("BalanceTransfer index zero")
                if from_user in sample_set:
                    block_deltas[(from_user, addr)][bn] -= value
                if to_user in sample_set:
                    block_deltas[(to_user, addr)][bn] += value
                if from_user not in sample_set and to_user not in sample_set:
                    raise RuntimeError("BalanceTransfer escaped frozen sample filters")
                counts["ATOKEN_BALANCE_TRANSFER"] += 1
            else:
                raise RuntimeError(f"unexpected token event topic0 {t0}")

    return block_deltas, counts, debt_balance_transfer_count


def replay_targets(
    block_deltas: dict[tuple[str, str], dict[int, int]],
    token_meta: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    targets: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    for (user, token), by_block in sorted(block_deltas.items()):
        balance = 0
        touched = False
        blocks_sorted = sorted(by_block.items())
        pos = 0
        for audit_block in AUDIT_BLOCKS:
            while pos < len(blocks_sorted) and blocks_sorted[pos][0] <= audit_block:
                bn, delta = blocks_sorted[pos]
                balance += delta
                touched = True
                if balance < 0:
                    negatives.append({
                        "user": user,
                        "token": token,
                        "kind": token_meta[token]["kind"],
                        "underlying": token_meta[token]["underlying"],
                        "block": bn,
                        "balance": str(balance),
                        "delta": str(delta),
                    })
                pos += 1
            if touched:
                targets.append({
                    "user": user,
                    "token": token,
                    "kind": token_meta[token]["kind"],
                    "underlying": token_meta[token]["underlying"],
                    "block": audit_block,
                    "replayed_scaled_balance": str(balance),
                })
    return targets, negatives


def rpc_batch(endpoint: str, items: list[dict[str, Any]], endpoint_stats: Counter[str]) -> dict[int, int]:
    out: dict[int, int] = {}
    batch_size = 40
    session = requests.Session()
    headers = {"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/r1-audit-v0.1"}
    for start in range(0, len(items), batch_size):
        chunk = items[start:start + batch_size]
        payload = []
        for idx, target in enumerate(chunk, start=start):
            calldata = "0x" + SCALED_BALANCE_SELECTOR + "0" * 24 + target["user"][2:]
            payload.append({
                "jsonrpc": "2.0",
                "id": idx,
                "method": "eth_call",
                "params": [
                    {"to": target["token"], "data": calldata},
                    hex(int(target["block"])),
                ],
            })
        last: Exception | None = None
        response_obj: Any = None
        for attempt in range(3):
            try:
                r = session.post(endpoint, json=payload, headers=headers, timeout=(10, 45))
                endpoint_stats["http_attempts"] += 1
                if r.status_code in TRANSIENT:
                    endpoint_stats["transient_retries"] += 1
                    r.close()
                    time.sleep(1.5 * (attempt + 1))
                    continue
                r.raise_for_status()
                response_obj = r.json()
                r.close()
                break
            except Exception as exc:
                last = exc
                endpoint_stats["errors"] += 1
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        if response_obj is None:
            endpoint_stats["failed_batches"] += 1
            continue
        if not isinstance(response_obj, list):
            endpoint_stats["non_batch_responses"] += 1
            # Some providers may return a single JSON-RPC error for a rejected batch.
            continue
        by_id = {x.get("id"): x for x in response_obj if isinstance(x, dict)}
        for idx in range(start, start + len(chunk)):
            obj = by_id.get(idx)
            if not obj or obj.get("error") is not None:
                endpoint_stats["rpc_errors"] += 1
                continue
            result = obj.get("result")
            if not isinstance(result, str) or not result.startswith("0x"):
                endpoint_stats["invalid_results"] += 1
                continue
            try:
                val = int(result, 16)
            except ValueError:
                endpoint_stats["invalid_results"] += 1
                continue
            out[idx] = val
            endpoint_stats["usable_results"] += 1
    session.close()
    return out


def validate_targets(targets: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    endpoint_values: dict[str, dict[int, int]] = {}
    endpoint_stats: dict[str, dict[str, int]] = {}
    for endpoint in RPC_ENDPOINTS:
        stats: Counter[str] = Counter()
        endpoint_values[endpoint] = rpc_batch(endpoint, targets, stats)
        endpoint_stats[endpoint] = dict(stats)

    failures: list[dict[str, Any]] = []
    technical = provenance = reconciliation = False
    for idx, target in enumerate(targets):
        vals = {ep: values[idx] for ep, values in endpoint_values.items() if idx in values}
        unique = sorted(set(vals.values()))
        expected = int(target["replayed_scaled_balance"])
        failure: str | None = None
        if len(vals) < 2:
            failure = "INSUFFICIENT_ARCHIVE_RPC_QUORUM"
            technical = True
        elif len(unique) != 1:
            failure = "ARCHIVE_RPC_DISAGREEMENT"
            provenance = True
        elif unique[0] != expected:
            failure = "REPLAY_MISMATCH"
            reconciliation = True
        if failure:
            failures.append({
                **target,
                "failure": failure,
                "usable_endpoint_values": {k: str(v) for k, v in vals.items()},
            })

    if provenance:
        classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
    elif reconciliation:
        classification = "RECONSTRUCTION_RECONCILIATION_FAILURE"
    elif technical:
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
    else:
        classification = "R1_AUDIT_PASS"
    return classification, failures, endpoint_stats


def main() -> int:
    output_dir = Path("r1_scaled_ledger_audit_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / "AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_1.json"

    transport_stats: Counter[str] = Counter()
    receipt: dict[str, Any] = {
        "lab_id": LAB_ID,
        "phase": "R1_SCALED_LEDGER_AUDIT_OUTCOME_BLIND",
        "protocol": "AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2",
        "frozen_from_block": FROM_BLOCK,
        "frozen_to_block": TO_BLOCK,
        "audit_blocks": AUDIT_BLOCKS,
        "classification": None,
        "failure": None,
        "safety": {
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }

    try:
        bootstrap = load_bootstrap()
        if int(bootstrap.get("frozen_from_block")) != FROM_BLOCK or int(bootstrap.get("frozen_to_block")) != TO_BLOCK:
            raise RuntimeError("canonical R0 bootstrap envelope mismatch")
        token_meta, atokens, debts = build_token_maps(bootstrap)
        sample, unique_borrower_count = select_borrowers(transport_stats)
        block_deltas, event_counts, debt_transfer_count = acquire_sample_token_deltas(
            sample, token_meta, atokens, debts, transport_stats
        )
        targets, negatives = replay_targets(block_deltas, token_meta)

        receipt["unique_borrower_count"] = unique_borrower_count
        receipt["sample_borrowers"] = sample
        receipt["sample_sha256"] = hashlib.sha256("\n".join(sample).encode()).hexdigest()
        receipt["scaled_event_counts"] = dict(sorted(event_counts.items()))
        receipt["touched_user_token_pairs"] = len(block_deltas)
        receipt["validation_target_count"] = len(targets)
        receipt["negative_replay_states"] = negatives[:100]
        receipt["variable_debt_balance_transfer_count"] = debt_transfer_count

        if debt_transfer_count != 0:
            receipt["classification"] = "RECONSTRUCTION_PROVENANCE_FAILURE"
            receipt["failure"] = "variable-debt BalanceTransfer observed despite non-transferability"
        elif negatives:
            receipt["classification"] = "RECONSTRUCTION_RECONCILIATION_FAILURE"
            receipt["failure"] = f"negative scaled replay state(s): {len(negatives)}"
        elif not targets:
            receipt["classification"] = "RECONSTRUCTION_INSUFFICIENT_COVERAGE"
            receipt["failure"] = "no deterministic historical validation targets"
        else:
            classification, failures, endpoint_stats = validate_targets(targets)
            receipt["classification"] = classification
            receipt["validation_failures"] = failures[:250]
            receipt["validation_failure_count"] = len(failures)
            receipt["archive_rpc_stats"] = endpoint_stats
            receipt["validated_target_count"] = len(targets) - len(failures)
            receipt["target_digest_sha256"] = hashlib.sha256(
                "\n".join(
                    f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in targets
                ).encode()
            ).hexdigest()
            # Store the deterministic targets for reproducibility without any market/outcome data.
            receipt["validation_targets"] = targets

    except Exception as exc:
        receipt["classification"] = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1000]}"

    receipt["transport_stats"] = dict(transport_stats)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "unique_borrowers": receipt.get("unique_borrower_count"),
        "sample_size": len(receipt.get("sample_borrowers", [])),
        "touched_pairs": receipt.get("touched_user_token_pairs"),
        "validation_targets": receipt.get("validation_target_count"),
        "validation_failures": receipt.get("validation_failure_count"),
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] == "R1_AUDIT_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
