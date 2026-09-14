#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LAB = "STABLECOIN-DEX-STRESS-001"
MVE = "SDS-CURVE3POOL-PEG-001"
BRANCH = "stablecoin-dex-stress-v0.1"

PRIMARY_RPC = "https://public.1rpc.io/eth"
FALLBACK_RPC = "https://ethereum-rpc.publicnode.com"
POOL = "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7"
TOPIC0 = "0x8b3e96f2b889fa771c53c981b40daf005f63f637f1869f707052d15a3dd97140"

# Warm-up-safe pre-2021 boundary; no protected-period access is permitted.
START_BLOCK = 11_565_000
# Etherscan-verified last Ethereum block of 2024: 2024-12-31 23:59:59 UTC.
END_BLOCK = 21_525_890
WINDOW_START_TS = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
WINDOW_END_TS = int(datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())
PROTECTED_2025_TS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
MIN_DAILY_SOURCE_OBSERVATIONS = 500

PROBES = [
    (12_000_000, 12_002_000, "early"),
    (16_820_000, 16_822_000, "stress_era"),
    (21_514_000, 21_516_000, "late"),
]

OUT = Path("stablecoin_dex_stress_source_gate_out")
RAW_BIN = OUT / "raw_rpc_responses.bin"
RAW_INDEX = OUT / "raw_rpc_index.jsonl"
LOGS_GZ = OUT / "curve3pool_tokenexchange_logs.jsonl.gz"
DECODED_GZ = OUT / "decoded_source_rows.jsonl.gz"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


class SourceAuthBlocked(RuntimeError):
    pass


class SourceTechnicalFailure(RuntimeError):
    pass


class DataFailure(RuntimeError):
    pass


class ProvenanceFailure(RuntimeError):
    pass


@dataclass
class RpcEvidenceWriter:
    body_fh: Any
    index_fh: Any
    seq: int = 0

    @classmethod
    def open(cls) -> "RpcEvidenceWriter":
        OUT.mkdir(parents=True, exist_ok=True)
        return cls(RAW_BIN.open("wb"), RAW_INDEX.open("w", encoding="utf-8"))

    def close(self) -> None:
        self.body_fh.close()
        self.index_fh.close()

    def record(self, endpoint: str, request_obj: Any, raw: bytes, http_status: int) -> None:
        self.seq += 1
        offset = self.body_fh.tell()
        self.body_fh.write(struct.pack(">Q", len(raw)))
        self.body_fh.write(raw)
        rec = {
            "seq": self.seq,
            "endpoint": endpoint,
            "request": request_obj,
            "http_status": http_status,
            "raw_offset_length_prefix": offset,
            "raw_bytes": len(raw),
            "raw_sha256": sha256(raw),
        }
        self.index_fh.write(json.dumps(rec, sort_keys=True) + "\n")
        self.index_fh.flush()
        self.body_fh.flush()


class RpcClient:
    def __init__(self, endpoint: str, evidence: RpcEvidenceWriter):
        self.endpoint = endpoint
        self.evidence = evidence
        self.request_id = 1000

    def _post(self, obj: Any, retries: int = 3) -> Any:
        payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        last_exc: Exception | None = None
        for attempt in range(retries):
            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "CryptoLab-SourceGate/1.0",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read()
                    status = int(resp.status)
                self.evidence.record(self.endpoint, obj, raw, status)
                parsed = json.loads(raw.decode("utf-8"))
                return parsed
            except urllib.error.HTTPError as exc:
                raw = exc.read() if hasattr(exc, "read") else b""
                self.evidence.record(self.endpoint, obj, raw, int(exc.code))
                if exc.code in (401, 402, 403):
                    raise SourceAuthBlocked(f"HTTP {exc.code} from {self.endpoint}") from exc
                if exc.code in (408, 425, 429, 500, 502, 503, 504):
                    last_exc = exc
                    if attempt + 1 < retries:
                        time.sleep(2 ** attempt)
                        continue
                raise SourceTechnicalFailure(f"HTTP {exc.code} from {self.endpoint}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_exc = exc
                if attempt + 1 < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise SourceTechnicalFailure(f"transport/decode failure at {self.endpoint}: {exc}") from exc
        raise SourceTechnicalFailure(f"RPC retries exhausted at {self.endpoint}: {last_exc}")

    def call(self, method: str, params: list[Any]) -> Any:
        self.request_id += 1
        req = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        parsed = self._post(req)
        if not isinstance(parsed, dict):
            raise SourceTechnicalFailure(f"non-object JSON-RPC response for {method}")
        if "error" in parsed:
            err = parsed.get("error")
            text = json.dumps(err, sort_keys=True).lower()
            if any(token in text for token in ("unauthorized", "forbidden", "api key", "payment required")):
                raise SourceAuthBlocked(f"RPC auth/access error for {method}: {err}")
            raise SourceTechnicalFailure(f"RPC error for {method}: {err}")
        if "result" not in parsed:
            raise SourceTechnicalFailure(f"missing JSON-RPC result for {method}")
        return parsed["result"]

    def batch(self, calls: list[tuple[str, list[Any]]]) -> list[Any]:
        reqs = []
        ids = []
        for method, params in calls:
            self.request_id += 1
            ids.append(self.request_id)
            reqs.append({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params})
        parsed = self._post(reqs)
        if not isinstance(parsed, list):
            raise SourceTechnicalFailure("batch RPC response is not a list")
        by_id = {item.get("id"): item for item in parsed if isinstance(item, dict)}
        out = []
        for rid in ids:
            item = by_id.get(rid)
            if not item:
                raise SourceTechnicalFailure(f"missing batch response id={rid}")
            if "error" in item:
                raise SourceTechnicalFailure(f"batch RPC item error id={rid}: {item['error']}")
            out.append(item.get("result"))
        return out


def hexint(x: str) -> int:
    return int(x, 16)


def canonical_logs(logs: list[dict[str, Any]]) -> str:
    keep = []
    for x in logs:
        keep.append({
            "address": str(x.get("address", "")).lower(),
            "blockNumber": str(x.get("blockNumber", "")).lower(),
            "transactionHash": str(x.get("transactionHash", "")).lower(),
            "logIndex": str(x.get("logIndex", "")).lower(),
            "topics": [str(t).lower() for t in x.get("topics", [])],
            "data": str(x.get("data", "")).lower(),
            "removed": bool(x.get("removed", False)),
        })
    keep.sort(key=lambda v: (v["blockNumber"], v["transactionHash"], v["logIndex"]))
    return json.dumps(keep, separators=(",", ":"), sort_keys=True)


def get_logs_once(client: RpcClient, start: int, end: int) -> list[dict[str, Any]]:
    filt = {
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "address": POOL,
        "topics": [TOPIC0],
    }
    result = client.call("eth_getLogs", [filt])
    if not isinstance(result, list):
        raise SourceTechnicalFailure(f"eth_getLogs returned non-list for {start}-{end}")
    return result


def probe_provider(client: RpcClient) -> dict[str, Any]:
    chain = client.call("eth_chainId", [])
    if str(chain).lower() != "0x1":
        raise ProvenanceFailure(f"wrong chain id: {chain}")
    code = client.call("eth_getCode", [POOL, hex(END_BLOCK)])
    if not isinstance(code, str) or code in ("0x", "0x0", ""):
        raise ProvenanceFailure("Curve 3pool code missing at fixed 2024 cap block")

    probes = []
    for start, end, label in PROBES:
        a = get_logs_once(client, start, end)
        b = get_logs_once(client, start, end)
        if not a:
            raise SourceTechnicalFailure(f"fixed {label} probe returned zero logs")
        ca, cb = canonical_logs(a), canonical_logs(b)
        if ca != cb:
            raise ProvenanceFailure(f"fixed {label} probe not reproducible")
        probes.append({"label": label, "start": start, "end": end, "logs": len(a), "canonical_sha256": sha256(ca.encode())})
    return {"chain_id": chain, "code_bytes": (len(code) - 2) // 2, "probes": probes}


def choose_provider(evidence: RpcEvidenceWriter) -> tuple[RpcClient, dict[str, Any], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    auth_failures = 0
    for endpoint in (PRIMARY_RPC, FALLBACK_RPC):
        client = RpcClient(endpoint, evidence)
        try:
            proof = probe_provider(client)
            return client, proof, failures
        except SourceAuthBlocked as exc:
            auth_failures += 1
            failures.append({"endpoint": endpoint, "classification": "SOURCE_AUTH_BLOCKED", "error": str(exc)})
        except (SourceTechnicalFailure, ProvenanceFailure) as exc:
            failures.append({"endpoint": endpoint, "classification": type(exc).__name__, "error": str(exc)})
    if auth_failures == 2:
        raise SourceAuthBlocked(json.dumps(failures, sort_keys=True))
    raise SourceTechnicalFailure(json.dumps(failures, sort_keys=True))


def range_logs(client: RpcClient, start: int, end: int, min_span: int = 250) -> list[dict[str, Any]]:
    try:
        return get_logs_once(client, start, end)
    except SourceAuthBlocked:
        raise
    except SourceTechnicalFailure as exc:
        if start >= end or (end - start + 1) <= min_span:
            raise SourceTechnicalFailure(f"range failed at minimum span {start}-{end}: {exc}") from exc
        mid = (start + end) // 2
        left = range_logs(client, start, mid, min_span=min_span)
        right = range_logs(client, mid + 1, end, min_span=min_span)
        return left + right


def acquire_all_logs(client: RpcClient) -> list[dict[str, Any]]:
    all_logs: list[dict[str, Any]] = []
    chunk = 20_000
    cursor = START_BLOCK
    while cursor <= END_BLOCK:
        stop = min(cursor + chunk - 1, END_BLOCK)
        logs = range_logs(client, cursor, stop)
        all_logs.extend(logs)
        print(f"SOURCE_PROGRESS blocks={cursor}-{stop} logs={len(logs)} total={len(all_logs)}", flush=True)
        cursor = stop + 1
    return all_logs


def dedupe_and_validate_logs(logs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[tuple[str, int]] = set()
    unique: list[dict[str, Any]] = []
    dupes = 0
    for log in logs:
        if not isinstance(log, dict):
            raise DataFailure("non-object log")
        if str(log.get("address", "")).lower() != POOL:
            raise ProvenanceFailure("log address mismatch")
        topics = log.get("topics")
        if not isinstance(topics, list) or not topics or str(topics[0]).lower() != TOPIC0:
            raise ProvenanceFailure("log topic0 mismatch")
        if bool(log.get("removed", False)):
            raise ProvenanceFailure("removed/reorg log present in historical result")
        tx = str(log.get("transactionHash", "")).lower()
        li = hexint(str(log.get("logIndex")))
        key = (tx, li)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        bn = hexint(str(log.get("blockNumber")))
        if bn < START_BLOCK or bn > END_BLOCK:
            raise ProvenanceFailure(f"log outside hard block firewall: {bn}")
        unique.append(log)
    unique.sort(key=lambda x: (hexint(x["blockNumber"]), hexint(x["transactionIndex"]), hexint(x["logIndex"])))
    return unique, dupes


def decode_word_int(word: bytes, signed: bool = False) -> int:
    return int.from_bytes(word, "big", signed=signed)


def decode_event(log: dict[str, Any]) -> dict[str, Any]:
    raw_hex = str(log.get("data", ""))
    if not raw_hex.startswith("0x"):
        raise DataFailure("event data missing 0x")
    raw = bytes.fromhex(raw_hex[2:])
    if len(raw) != 128:
        raise DataFailure(f"TokenExchange data length !=128: {len(raw)}")
    sold_id = decode_word_int(raw[0:32], signed=True)
    tokens_sold = decode_word_int(raw[32:64], signed=False)
    bought_id = decode_word_int(raw[64:96], signed=True)
    tokens_bought = decode_word_int(raw[96:128], signed=False)
    if sold_id not in (0, 1, 2) or bought_id not in (0, 1, 2) or sold_id == bought_id:
        raise DataFailure(f"invalid coin ids sold={sold_id} bought={bought_id}")
    if tokens_sold <= 0 or tokens_bought <= 0:
        raise DataFailure("non-positive swap quantity")
    return {
        "block_number": hexint(log["blockNumber"]),
        "transaction_hash": str(log["transactionHash"]).lower(),
        "transaction_index": hexint(log["transactionIndex"]),
        "log_index": hexint(log["logIndex"]),
        "sold_id": sold_id,
        "tokens_sold_raw": str(tokens_sold),
        "bought_id": bought_id,
        "tokens_bought_raw": str(tokens_bought),
    }


def fetch_timestamps(client: RpcClient, block_numbers: list[int]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    batch_size = 100
    for i in range(0, len(block_numbers), batch_size):
        batch_blocks = block_numbers[i:i + batch_size]
        calls = [("eth_getBlockByNumber", [hex(b), False]) for b in batch_blocks]
        try:
            results = client.batch(calls)
        except SourceTechnicalFailure:
            # Deterministic same-source fallback to individual fixed-block calls.
            results = [client.call("eth_getBlockByNumber", [hex(b), False]) for b in batch_blocks]
        for b, block in zip(batch_blocks, results):
            if not isinstance(block, dict):
                raise ProvenanceFailure(f"missing block object for {b}")
            if hexint(str(block.get("number"))) != b:
                raise ProvenanceFailure(f"block-number mismatch for {b}")
            ts = hexint(str(block.get("timestamp")))
            if ts >= PROTECTED_2025_TS:
                raise ProvenanceFailure(f"protected-period timestamp reached for block {b}: {ts}")
            mapping[b] = ts
        if i % 2000 == 0:
            print(f"TIMESTAMP_PROGRESS {min(i + len(batch_blocks), len(block_numbers))}/{len(block_numbers)}", flush=True)
    return mapping


def write_gzip_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")


def file_meta(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": sha256(data)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = RpcEvidenceWriter.open()
    receipt: dict[str, Any] = {
        "lab": LAB,
        "mve_id": MVE,
        "branch": BRANCH,
        "phase": "SOURCE_DATA_GATE_ONLY",
        "hard_start_block": START_BLOCK,
        "hard_end_block": END_BLOCK,
        "min_daily_source_observations": MIN_DAILY_SOURCE_OBSERVATIONS,
        "price_values_opened": False,
        "market_archive_accessed": False,
        "signal_series_computed": False,
        "discovery_event_count_computed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "performance_statistics_computed": False,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    exit_code = 4
    try:
        client, provider_proof, provider_failures = choose_provider(evidence)
        receipt["selected_rpc"] = client.endpoint
        receipt["provider_proof"] = provider_proof
        receipt["provider_failures_before_selection"] = provider_failures

        logs_raw = acquire_all_logs(client)
        logs, duplicate_count = dedupe_and_validate_logs(logs_raw)
        receipt["raw_log_count"] = len(logs_raw)
        receipt["unique_log_count"] = len(logs)
        receipt["duplicate_log_count"] = duplicate_count
        if not logs:
            raise InsufficientSample("zero canonical TokenExchange logs")

        write_gzip_jsonl(LOGS_GZ, logs)
        decoded = [decode_event(x) for x in logs]
        unique_blocks = sorted({row["block_number"] for row in decoded})
        timestamps = fetch_timestamps(client, unique_blocks)

        days = Counter()
        min_ts = None
        max_ts = None
        for row in decoded:
            ts = timestamps[row["block_number"]]
            row["block_timestamp_utc"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            row["utc_date"] = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
            if WINDOW_START_TS <= ts <= WINDOW_END_TS:
                days[row["utc_date"]] += 1
            min_ts = ts if min_ts is None else min(min_ts, ts)
            max_ts = ts if max_ts is None else max(max_ts, ts)

        write_gzip_jsonl(DECODED_GZ, decoded)
        daily_count = len(days)
        receipt.update({
            "unique_event_blocks": len(unique_blocks),
            "first_event_timestamp_utc": datetime.fromtimestamp(min_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z") if min_ts else None,
            "last_event_timestamp_utc": datetime.fromtimestamp(max_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z") if max_ts else None,
            "daily_source_observations_2021_2024": daily_count,
            "first_source_day_2021_2024": min(days) if days else None,
            "last_source_day_2021_2024": max(days) if days else None,
            "coin_pair_counts": dict(sorted(Counter(f"{r['sold_id']}->{r['bought_id']}" for r in decoded).items())),
        })
        if daily_count < MIN_DAILY_SOURCE_OBSERVATIONS:
            raise InsufficientSample(f"only {daily_count} UTC source days; gate requires >= {MIN_DAILY_SOURCE_OBSERVATIONS}")

        receipt["status"] = "SOURCE_DATA_PASS"
        receipt["reason"] = "Curve 3pool canonical event source passed fixed-provider probes, full pre-2025 acquisition, decode, timestamp and source-day coverage gates"
        exit_code = 0
    except SourceAuthBlocked as exc:
        receipt["status"] = "SOURCE_AUTH_BLOCKED"
        receipt["reason"] = str(exc)
        exit_code = 2
    except InsufficientSample as exc:
        receipt["status"] = "INSUFFICIENT_SAMPLE"
        receipt["reason"] = str(exc)
        exit_code = 3
    except DataFailure as exc:
        receipt["status"] = "DATA_FAILURE"
        receipt["reason"] = str(exc)
        exit_code = 3
    except ProvenanceFailure as exc:
        receipt["status"] = "PROVENANCE_FAILURE"
        receipt["reason"] = str(exc)
        exit_code = 3
    except SourceTechnicalFailure as exc:
        receipt["status"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["reason"] = str(exc)
        exit_code = 4
    except Exception as exc:
        receipt["status"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["reason"] = f"fail-closed unhandled {type(exc).__name__}: {exc}"
        exit_code = 4
    finally:
        evidence.close()
        manifest: dict[str, Any] = {"files": {}}
        for p in (RAW_BIN, RAW_INDEX, LOGS_GZ, DECODED_GZ):
            if p.exists():
                manifest["files"][p.name] = file_meta(p)
        manifest["rpc_response_count"] = evidence.seq
        atomic_json(OUT / "source_manifest.json", manifest)
        receipt["source_manifest_sha256"] = file_meta(OUT / "source_manifest.json")["sha256"]
        atomic_json(OUT / "source_gate_receipt.json", receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)
    return exit_code


class InsufficientSample(RuntimeError):
    pass


if __name__ == "__main__":
    sys.exit(main())
