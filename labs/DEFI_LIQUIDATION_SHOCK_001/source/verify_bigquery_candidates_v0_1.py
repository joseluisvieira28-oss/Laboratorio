#!/usr/bin/env python3
"""Verify BigQuery liquidation candidates against archival Solana RPC.

READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND.
Input is the CSV exported by BIGQUERY_LIQUIDATION_CANDIDATE_CENSUS_V0_1.sql.
The configured RPC URL is supplied by the existing lab environment. This file
contains no credential and never submits a transaction.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from collect_protocol_history_v0_1 import (
    LAB_ID, Rpc, extract_protocol_instructions, redact_rpc_url, rpc_url,
    sha256_bytes, write_json,
)

VERSION = "DLS_BIGQUERY_RAW_VERIFY_V01"
REQUIRED = {
    "protocol", "program_id", "match_name", "reference_prefix_hex",
    "block_slot", "block_timestamp", "tx_signature",
    "instruction_index", "parent_index",
}


def nullish(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in {"", "null", "none"})


def as_int(v: Any) -> Optional[int]:
    return None if nullish(v) else int(v)


def timestamp_unix(v: Any) -> Optional[int]:
    if nullish(v):
        return None
    text = str(v).strip().replace(" UTC", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.astimezone(timezone.utc).timestamp())


def append_jsonl(path: pathlib.Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")


def load_csv(path: pathlib.Path) -> list[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = [dict(x) for x in csv.DictReader(fh)]
    if not rows:
        raise RuntimeError("EMPTY_INPUT")
    missing = REQUIRED - set(rows[0])
    if missing:
        raise RuntimeError(f"MISSING_COLUMNS {sorted(missing)}")
    out = []
    seen = set()
    for n, row in enumerate(rows, 1):
        row["block_slot"] = as_int(row["block_slot"])
        row["instruction_index"] = as_int(row["instruction_index"])
        row["parent_index"] = as_int(row["parent_index"])
        row["block_timestamp_unix"] = timestamp_unix(row["block_timestamp"])
        row["reference_prefix_hex"] = row["reference_prefix_hex"].strip().lower()
        if row["block_slot"] is None or row["instruction_index"] is None:
            raise RuntimeError(f"BAD_ROW_IDENTITY row={n}")
        key = (
            row["protocol"], row["program_id"], row["match_name"],
            row["reference_prefix_hex"], row["block_slot"], row["tx_signature"],
            row["instruction_index"], row["parent_index"],
        )
        if key in seen:
            raise RuntimeError(f"EXACT_DUPLICATE_INPUT row={n}")
        seen.add(key)
        out.append(row)
    return out


def find_instruction(tx: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    all_ix = extract_protocol_instructions(tx, row["program_id"])
    if row["parent_index"] is None:
        location, outer, inner = "outer", row["instruction_index"], None
    else:
        location, outer, inner = "inner", row["parent_index"], row["instruction_index"]
    found = [x for x in all_ix if x["location"] == location
             and x["outer_index"] == outer and x["inner_index"] == inner]
    if len(found) != 1:
        raise RuntimeError(
            f"INSTRUCTION_LOCATION_MISMATCH signature={row['tx_signature']} found={len(found)}"
        )
    return found[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-unique-transactions", type=int, default=0)
    args = ap.parse_args()

    src = pathlib.Path(args.input).expanduser().resolve()
    out = pathlib.Path(args.out_dir).expanduser().resolve()
    if not src.exists():
        raise RuntimeError(f"INPUT_NOT_FOUND {src}")
    if (out / "RUN_MANIFEST.json").exists():
        raise RuntimeError("RUN_ALREADY_EXISTS_USE_NEW_OUT_DIR")
    if args.max_unique_transactions < 0:
        raise RuntimeError("NEGATIVE_SAFETY_CAP")

    rows = load_csv(src)
    by_sig: Dict[str, list[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_sig[row["tx_signature"]].append(row)
    signatures = sorted(by_sig, key=lambda s: min(x["block_slot"] for x in by_sig[s]))
    partial = False
    if args.max_unique_transactions and len(signatures) > args.max_unique_transactions:
        signatures = signatures[:args.max_unique_transactions]
        partial = True

    delay = float(os.environ.get("DLS_RPS_DELAY", "0.12"))
    if delay < 0:
        raise RuntimeError("NEGATIVE_RPS_DELAY")
    url = rpc_url()
    rpc = Rpc(url, out / "raw_rpc", delay)
    verify_path = out / "VERIFICATION_ROWS.jsonl"
    summary: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"rows": 0, "success": 0, "failed": 0, "outer": 0, "inner": 0}
    )
    started = int(time.time())
    status = "RAW_VERIFICATION_COMPLETE"

    try:
        for signature in signatures:
            tx = rpc.call(
                "getTransaction",
                [signature, {"encoding": "json", "commitment": "finalized",
                             "maxSupportedTransactionVersion": 0}],
                raw_subdir="candidate_transactions",
            )
            if not isinstance(tx, dict):
                raise RuntimeError(f"MISSING_TRANSACTION signature={signature}")
            meta = tx.get("meta")
            if not isinstance(meta, dict):
                raise RuntimeError(f"MISSING_META signature={signature}")
            success = meta.get("err") is None

            for row in by_sig[signature]:
                if tx.get("slot") != row["block_slot"]:
                    raise RuntimeError(f"SLOT_MISMATCH signature={signature}")
                if row["block_timestamp_unix"] is not None and tx.get("blockTime") != row["block_timestamp_unix"]:
                    raise RuntimeError(f"BLOCKTIME_MISMATCH signature={signature}")
                ix = find_instruction(tx, row)
                data_hex = ix.get("data_hex")
                if not isinstance(data_hex, str) or not data_hex.startswith(row["reference_prefix_hex"]):
                    raise RuntimeError(f"DISCRIMINATOR_MISMATCH signature={signature}")

                rec = {
                    "lab_id": LAB_ID,
                    "verifier_version": VERSION,
                    "protocol": row["protocol"],
                    "program_id": row["program_id"],
                    "match_name": row["match_name"],
                    "reference_prefix_hex": row["reference_prefix_hex"],
                    "tx_signature": signature,
                    "block_slot": tx.get("slot"),
                    "block_time": tx.get("blockTime"),
                    "success": success,
                    "tx_error": meta.get("err"),
                    "rpc_instruction": ix,
                    "raw_rpc_reconciled": True,
                    "historical_decoder_authoritative": False,
                    "classification": "RAW_VERIFIED_REFERENCE_CANDIDATE",
                    "prices_queried": False,
                    "returns_computed": False,
                    "pnl_computed": False,
                }
                append_jsonl(verify_path, rec)
                skey = row["protocol"] + "::" + row["match_name"]
                summary[skey]["rows"] += 1
                summary[skey]["success" if success else "failed"] += 1
                summary[skey][ix["location"]] += 1

        if partial:
            status = "RAW_VERIFICATION_PARTIAL_SAFETY_CAP"
    except Exception as exc:
        status = "RAW_VERIFICATION_FAILED"
        write_json(out / "RUN_ERROR.json", {
            "lab_id": LAB_ID, "verifier_version": VERSION,
            "error_type": type(exc).__name__, "error": str(exc),
            "prices_queried": False, "returns_computed": False, "pnl_computed": False,
        })
        raise
    finally:
        out.mkdir(parents=True, exist_ok=True)
        receipts = out / "RPC_RECEIPTS.json"
        write_json(receipts, rpc.receipts)
        write_json(out / "CANDIDATE_SUMMARY.json", [
            {"candidate": k, **v} for k, v in sorted(summary.items())
        ])
        write_json(out / "RUN_MANIFEST.json", {
            "lab_id": LAB_ID,
            "verifier_version": VERSION,
            "run_status": status,
            "input_sha256": sha256_bytes(src.read_bytes()),
            "input_candidate_rows": len(rows),
            "unique_candidate_transactions_total": len(by_sig),
            "unique_candidate_transactions_attempted": len(signatures),
            "partial_due_to_safety_cap": partial,
            "rpc_url": redact_rpc_url(url),
            "rpc_request_count": rpc.request_id,
            "started_unix": started,
            "finished_unix": int(time.time()),
            "governance": {
                "read_only": True, "source_only": True,
                "prices_queried": False, "returns_computed": False,
                "pnl_computed": False, "direction_tested": False,
                "historical_decoder_authority_implied": False,
                "source_data_pass_implied": False,
                "live_trading": False, "exchange_mutation": False,
            },
        })

    print(json.dumps({"status": status, "out_dir": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("INTERRUPTED: verification incomplete; no SOURCE_DATA_PASS", file=sys.stderr)
        raise SystemExit(130)
