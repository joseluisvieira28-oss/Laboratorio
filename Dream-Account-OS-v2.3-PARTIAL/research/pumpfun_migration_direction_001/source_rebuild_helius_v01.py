#!/usr/bin/env python3
"""PMD-001 archival pre-migration source rebuild collector.

OUTCOME-BLIND. This script never reads post-migration prices or outcome labels.
It reconstructs raw Solana transaction evidence for the mint-specific Pump
bonding-curve PDA over [T0-300s, T0).

Input JSONL: one object per candidate with at least {"mint": ..., "t0": ...}.
Production source: Helius archival RPC using HELIUS_API_KEY from environment.
A generic --rpc-url is allowed only for outcome-blind source-access probes.
Optional --block-remediate-missing uses getBlock only to repair missing
getTransaction bodies, as permitted by SOURCE_REBUILD_AUTHORITY_V01.md.
Credentials are never written to disk.

Dependencies:
    pip install requests solders
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import requests
from solders.pubkey import Pubkey

PUMP_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
WINDOW_SECONDS = 300
SIG_LIMIT = 1000
TX_BATCH = 50
MAX_RETRIES = 8


def parse_ts(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("Z", "+00:00")
    x = dt.datetime.fromisoformat(s)
    if x.tzinfo is None:
        x = x.replace(tzinfo=dt.timezone.utc)
    return x.timestamp()


def json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json_bytes(obj)).hexdigest()


def bonding_curve_pda(mint: str) -> str:
    m = Pubkey.from_string(mint)
    pda, _bump = Pubkey.find_program_address([b"bonding-curve", bytes(m)], PUMP_PROGRAM)
    return str(pda)


def body_missing(tx: Any) -> bool:
    return (
        not isinstance(tx, dict)
        or bool(tx.get("_rpc_error"))
        or bool(tx.get("_missing_batch_response"))
    )


class Rpc:
    def __init__(self, url: str, source_name: str, timeout: int = 45):
        self.url = url
        self.source_name = source_name
        self.timeout = timeout
        self.session = requests.Session()
        self.counter = 0

    def _post(self, payload: Any) -> Any:
        for attempt in range(MAX_RETRIES):
            try:
                r = self.session.post(self.url, json=payload, timeout=self.timeout)
                if r.status_code == 429 or r.status_code >= 500:
                    raise RuntimeError(f"retryable http {r.status_code}")
                r.raise_for_status()
                return r.json()
            except Exception:
                if attempt + 1 >= MAX_RETRIES:
                    raise
                time.sleep(min(30.0, (2 ** attempt) + random.random()))
        raise AssertionError("unreachable")

    def call(self, method: str, params: list[Any]) -> Any:
        self.counter += 1
        req = {"jsonrpc": "2.0", "id": self.counter, "method": method, "params": params}
        out = self._post(req)
        if "error" in out:
            raise RuntimeError(f"RPC {method} error: {out['error']}")
        return out.get("result")

    def get_signatures(self, address: str, before: str | None = None) -> list[dict[str, Any]]:
        cfg: dict[str, Any] = {"limit": SIG_LIMIT, "commitment": "finalized"}
        if before:
            cfg["before"] = before
        return self.call("getSignaturesForAddress", [address, cfg]) or []

    def get_transactions(self, signatures: list[str]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for i in range(0, len(signatures), TX_BATCH):
            chunk = signatures[i:i + TX_BATCH]
            reqs = []
            ids = {}
            for sig in chunk:
                self.counter += 1
                rid = self.counter
                ids[rid] = sig
                reqs.append({
                    "jsonrpc": "2.0",
                    "id": rid,
                    "method": "getTransaction",
                    "params": [sig, {
                        "commitment": "finalized",
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0,
                    }],
                })
            resp = self._post(reqs)
            if not isinstance(resp, list):
                raise RuntimeError("batch getTransaction response is not a list")
            seen = set()
            for item in resp:
                rid = item.get("id")
                sig = ids.get(rid)
                if not sig:
                    continue
                seen.add(sig)
                if "error" in item:
                    out[sig] = {"_rpc_error": item["error"]}
                else:
                    out[sig] = item.get("result")
            for sig in chunk:
                if sig not in seen:
                    out[sig] = {"_missing_batch_response": True}
        return out

    def get_block(self, slot: int) -> Any:
        return self.call("getBlock", [int(slot), {
            "commitment": "finalized",
            "encoding": "jsonParsed",
            "transactionDetails": "full",
            "rewards": False,
            "maxSupportedTransactionVersion": 0,
        }])


def load_manifest(path: Path) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            mint = obj.get("mint")
            t0 = obj.get("t0") or obj.get("migrated_at")
            if not mint or t0 is None:
                raise ValueError(f"line {ln}: missing mint/t0")
            if mint in seen:
                raise ValueError(f"duplicate mint in input manifest: {mint}")
            seen.add(mint)
            rows.append({**obj, "mint": mint, "t0": t0})
    rows.sort(key=lambda x: (parse_ts(x["t0"]), x["mint"]))
    return rows


def tx_has_target(tx: Any, mint: str, pda: str) -> bool:
    if not isinstance(tx, dict):
        return False
    if tx.get("meta", {}).get("err") is not None:
        return False
    s = json.dumps(tx, separators=(",", ":"), ensure_ascii=False)
    return str(PUMP_PROGRAM) in s and mint in s and pda in s


def find_tx_in_block(block: Any, signature: str) -> Any:
    if not isinstance(block, dict):
        return None
    for item in block.get("transactions") or []:
        tx = item.get("transaction") if isinstance(item, dict) else None
        sigs = tx.get("signatures") if isinstance(tx, dict) else None
        if isinstance(sigs, list) and signature in sigs:
            return item
    return None


def remediate_from_blocks(rpc: Rpc, tx_map: dict[str, Any], inwin_meta: list[dict[str, Any]], block_dir: Path) -> dict[str, int]:
    missing_meta = [m for m in inwin_meta if body_missing(tx_map.get(m["signature"]))]
    by_slot: dict[int, list[dict[str, Any]]] = {}
    for m in missing_meta:
        slot = m.get("slot")
        if slot is None:
            continue
        by_slot.setdefault(int(slot), []).append(m)

    blocks_ok = 0
    blocks_missing = 0
    bodies_recovered = 0
    block_dir.mkdir(parents=True, exist_ok=True)
    for slot in sorted(by_slot):
        try:
            block = rpc.get_block(slot)
        except Exception as exc:
            block = {"_rpc_error": f"{type(exc).__name__}: {exc}"}
        evidence = {
            "lab": "PMD-001",
            "stage": "SOURCE_REBUILD_BLOCK_REMEDIATION_V01",
            "outcomes_opened": False,
            "source_name": rpc.source_name,
            "slot": slot,
            "block": block,
            "canonical_sha256": sha256_json(block),
        }
        with gzip.open(block_dir / f"slot_{slot}.json.gz", "wt", encoding="utf-8") as gf:
            json.dump(evidence, gf, sort_keys=True, ensure_ascii=False)
        if not isinstance(block, dict) or block.get("_rpc_error"):
            blocks_missing += 1
            continue
        blocks_ok += 1
        for m in by_slot[slot]:
            sig = m["signature"]
            recovered = find_tx_in_block(block, sig)
            if recovered is not None:
                tx_map[sig] = recovered
                bodies_recovered += 1
    return {
        "fallback_blocks_requested": len(by_slot),
        "fallback_blocks_ok": blocks_ok,
        "fallback_blocks_missing": blocks_missing,
        "fallback_bodies_recovered": bodies_recovered,
    }


def collect_one(rpc: Rpc, row: dict[str, Any], raw_dir: Path, block_remediate: bool) -> dict[str, Any]:
    mint = row["mint"]
    t0 = parse_ts(row["t0"])
    lo = t0 - WINDOW_SECONDS
    pda = bonding_curve_pda(mint)

    all_sigs: list[dict[str, Any]] = []
    before: str | None = None
    crossed_lower = False
    history_exhausted = False
    page_count = 0
    null_time_seen = False

    while True:
        page = rpc.get_signatures(pda, before=before)
        page_count += 1
        if not page:
            history_exhausted = True
            break
        all_sigs.extend(page)
        times = [x.get("blockTime") for x in page]
        if any(x is None for x in times):
            null_time_seen = True
        nonnull = [float(x) for x in times if x is not None]
        if nonnull and min(nonnull) < lo:
            crossed_lower = True
            break
        if len(page) < SIG_LIMIT:
            history_exhausted = True
            break
        before = page[-1].get("signature")
        if not before:
            break
        if page_count > 100:
            raise RuntimeError(f"pagination safety stop for {mint}")

    by_sig: dict[str, dict[str, Any]] = {}
    conflicts = 0
    for x in all_sigs:
        sig = x.get("signature")
        if not sig:
            continue
        if sig in by_sig and by_sig[sig] != x:
            conflicts += 1
        else:
            by_sig[sig] = x

    inwin_meta = []
    for _sig, x in by_sig.items():
        bt = x.get("blockTime")
        if bt is None:
            continue
        bt = float(bt)
        if lo <= bt < t0:
            inwin_meta.append(x)
    inwin_meta.sort(key=lambda x: (x.get("slot") or -1, x.get("signature") or ""))

    tx_map = rpc.get_transactions([x["signature"] for x in inwin_meta]) if inwin_meta else {}
    fallback_stats = {
        "fallback_blocks_requested": 0,
        "fallback_blocks_ok": 0,
        "fallback_blocks_missing": 0,
        "fallback_bodies_recovered": 0,
    }
    if block_remediate and any(body_missing(tx_map.get(x["signature"])) for x in inwin_meta):
        fallback_stats = remediate_from_blocks(rpc, tx_map, inwin_meta, raw_dir.parent / "block_evidence" / mint)

    raw_records = []
    missing_bodies = 0
    target_txs = 0
    for meta in inwin_meta:
        sig = meta["signature"]
        tx = tx_map.get(sig)
        if body_missing(tx):
            missing_bodies += 1
        target = tx_has_target(tx, mint, pda)
        if target:
            target_txs += 1
        rec = {
            "lab": "PMD-001",
            "stage": "SOURCE_REBUILD_V01",
            "outcomes_opened": False,
            "source_name": rpc.source_name,
            "mint": mint,
            "t0": row["t0"],
            "bonding_curve_pda": pda,
            "signature_meta": meta,
            "feature_eligible_by_time": True,
            "target_pump_mint_pda_present": target,
            "transaction": tx,
            "raw_response_sha256": sha256_json(tx),
        }
        raw_records.append(rec)

    raw_path = raw_dir / f"{mint}.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for rec in raw_records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    complete = (
        conflicts == 0
        and missing_bodies == 0
        and (crossed_lower or history_exhausted)
        and not null_time_seen
    )
    return {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_V01",
        "outcomes_opened": False,
        "source_name": rpc.source_name,
        "mint": mint,
        "t0": row["t0"],
        "bonding_curve_pda": pda,
        "window_seconds": WINDOW_SECONDS,
        "signature_pages": page_count,
        "signatures_unique_seen": len(by_sig),
        "in_window_signatures": len(inwin_meta),
        "valid_target_pump_transactions": target_txs,
        "missing_transaction_bodies": missing_bodies,
        "signature_conflicts": conflicts,
        "null_block_time_seen": null_time_seen,
        "crossed_lower_bound": crossed_lower,
        "history_exhausted": history_exhausted,
        "source_complete": complete,
        **fallback_stats,
        "raw_file": str(raw_path),
        "raw_file_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="outcome-blind candidate JSONL with mint,t0")
    ap.add_argument("--out-dir", default="pmd_source_rebuild_v01")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="0 = all remaining rows")
    ap.add_argument("--rpc-url", default=None, help="generic RPC endpoint for source-access probes only")
    ap.add_argument("--source-name", default=None)
    ap.add_argument("--block-remediate-missing", action="store_true")
    args = ap.parse_args()

    if args.rpc_url:
        rpc_url = args.rpc_url
        source_name = args.source_name or "generic_rpc_probe"
    else:
        api_key = os.environ.get("HELIUS_API_KEY")
        if not api_key:
            print("HELIUS_API_KEY is required for the primary archival source; credential must not be committed", file=sys.stderr)
            return 3
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        source_name = "helius_archival_rpc"

    rows = load_manifest(Path(args.manifest))
    if args.start < 0 or args.start >= len(rows):
        raise ValueError("--start out of range")
    rows = rows[args.start:]
    if args.limit > 0:
        rows = rows[:args.limit]

    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "source_rebuild_summary.jsonl"
    rpc = Rpc(rpc_url, source_name)

    done = set()
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["mint"])

    attempted = 0
    with summary_path.open("a", encoding="utf-8") as sf:
        for row in rows:
            if row["mint"] in done:
                continue
            attempted += 1
            try:
                res = collect_one(rpc, row, raw_dir, args.block_remediate_missing)
            except Exception as exc:
                res = {
                    "lab": "PMD-001",
                    "stage": "SOURCE_REBUILD_V01",
                    "outcomes_opened": False,
                    "source_name": source_name,
                    "mint": row["mint"],
                    "t0": row["t0"],
                    "source_complete": False,
                    "collector_error": f"{type(exc).__name__}: {exc}",
                }
            sf.write(json.dumps(res, sort_keys=True, ensure_ascii=False) + "\n")
            sf.flush()
            print(json.dumps({k: res.get(k) for k in (
                "source_name", "mint", "source_complete", "in_window_signatures",
                "valid_target_pump_transactions", "missing_transaction_bodies",
                "fallback_blocks_requested", "fallback_bodies_recovered", "collector_error") if k in res},
                sort_keys=True))

    print(json.dumps({
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_V01",
        "outcomes_opened": False,
        "source_name": source_name,
        "attempted_this_run": attempted,
        "rpc_request_counter": rpc.counter,
        "summary_path": str(summary_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
