#!/usr/bin/env python3
"""
DEFI-LIQUIDATION-SHOCK-001 raw Solana protocol-history collector.

READ-ONLY / RESEARCH-ONLY / OUTCOME-BLIND.

Purpose:
  Acquire source transaction evidence only for the frozen 2021-01-01 through
  2024-12-31 DeFi liquidation source census. This collector never queries
  prices, computes returns/PnL, or labels economic outcomes.

Primary route:
  getSignaturesForAddress(program_id) -> getTransaction(signature)

Environment:
  HELIUS_API_KEY                 required unless DLS_RPC_URL is supplied
  DLS_RPC_URL                    optional full archival Solana RPC URL
  DLS_OUT_DIR                    optional output directory
  DLS_PROTOCOLS                  optional comma-separated protocol names
  DLS_RPS_DELAY                  optional delay between requests (default 0.12)
  DLS_MAX_PAGES_PER_PROTOCOL     optional safety cap; 0 means no cap
  DLS_FETCH_FAILED               1 to fetch failed tx bodies too (default 1)
  DLS_MAX_SUPPORTED_TX_VERSION   frozen default 0; version errors fail closed

A capped run is always classified PARTIAL and can never establish SOURCE_DATA_PASS.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

LAB_ID = "DEFI-LIQUIDATION-SHOCK-001"
COLLECTOR_VERSION = "DLS_PROTOCOL_HISTORY_SOURCE_V01"
SOURCE_START_UNIX = 1609459200  # 2021-01-01T00:00:00Z
SOURCE_END_UNIX = 1735689599    # 2024-12-31T23:59:59Z
SOURCE_START_ISO = "2021-01-01T00:00:00Z"
SOURCE_END_ISO = "2024-12-31T23:59:59Z"

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_INDEX = {c: i for i, c in enumerate(BASE58_ALPHABET)}


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_iso(ts: Optional[int]) -> Optional[str]:
    if ts is None:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def b58decode(value: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError("base58 value must be str")
    n = 0
    for ch in value:
        try:
            digit = BASE58_INDEX[ch]
        except KeyError as exc:
            raise ValueError(f"invalid base58 character: {ch!r}") from exc
        n = n * 58 + digit
    payload = b"" if n == 0 else n.to_bytes((n.bit_length() + 7) // 8, "big")
    leading_zeroes = len(value) - len(value.lstrip("1"))
    return b"\x00" * leading_zeroes + payload


def load_registry(path: pathlib.Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("lab_id") != LAB_ID:
        raise RuntimeError("REGISTRY_LAB_ID_MISMATCH")
    window = obj.get("source_window_utc") or {}
    if window.get("start") != SOURCE_START_ISO or window.get("end") != SOURCE_END_ISO:
        raise RuntimeError("REGISTRY_SOURCE_WINDOW_MISMATCH")
    protocols = obj.get("protocols")
    if not isinstance(protocols, list) or not protocols:
        raise RuntimeError("REGISTRY_PROTOCOLS_MISSING")
    names = [p.get("protocol") for p in protocols]
    if any(not isinstance(x, str) or not x for x in names) or len(set(names)) != len(names):
        raise RuntimeError("REGISTRY_PROTOCOL_NAMES_INVALID")
    return obj


def rpc_url() -> str:
    explicit = os.environ.get("DLS_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "Missing HELIUS_API_KEY (or DLS_RPC_URL). "
            "No paid route is required by this collector; supply an archival read-only RPC endpoint."
        )
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


def redact_rpc_url(url: str) -> str:
    if "api-key=" in url:
        return url.split("api-key=", 1)[0] + "api-key=<REDACTED>"
    return "<EXPLICIT_RPC_URL_REDACTED>"


class Rpc:
    def __init__(self, url: str, raw_dir: pathlib.Path, delay: float) -> None:
        self.url = url
        self.raw_dir = raw_dir
        self.delay = delay
        self.request_id = 0
        self.receipts: List[Dict[str, Any]] = []

    def call(self, method: str, params: list, *, raw_subdir: str) -> Any:
        self.request_id += 1
        payload = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        request_bytes = canonical_json_bytes(payload)
        req = urllib.request.Request(
            self.url,
            data=request_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{LAB_ID}/{COLLECTOR_VERSION} source-only",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_bytes = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"RPC_HTTP_{exc.code} method={method}: {detail[:1200]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"RPC_NETWORK_FAILURE method={method}: {exc}") from exc

        try:
            parsed = json.loads(response_bytes)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"RPC_INVALID_JSON method={method}") from exc
        if parsed.get("error"):
            raise RuntimeError(f"RPC_ERROR method={method}: {parsed['error']}")

        response_hash = sha256_bytes(response_bytes)
        target = self.raw_dir / raw_subdir
        target.mkdir(parents=True, exist_ok=True)
        raw_name = f"{self.request_id:08d}_{method}_{response_hash[:16]}.json"
        (target / raw_name).write_bytes(response_bytes)
        self.receipts.append(
            {
                "request_id": self.request_id,
                "method": method,
                "request_sha256": sha256_bytes(request_bytes),
                "response_sha256": response_hash,
                "response_bytes": len(response_bytes),
                "raw_file": str((pathlib.Path(raw_subdir) / raw_name).as_posix()),
            }
        )
        if self.delay:
            time.sleep(self.delay)
        return parsed.get("result")


def resolve_block_time(rpc: Rpc, protocol: str, row: Dict[str, Any]) -> int:
    value = row.get("blockTime")
    if isinstance(value, int):
        return value
    slot = row.get("slot")
    if not isinstance(slot, int):
        raise RuntimeError(f"SIGNATURE_ROW_MISSING_SLOT protocol={protocol}")
    result = rpc.call("getBlockTime", [slot], raw_subdir=f"{protocol}/blocktime")
    if not isinstance(result, int):
        raise RuntimeError(f"MISSING_BLOCK_TIME protocol={protocol} slot={slot}")
    return result


def normalize_account_keys(tx_result: Dict[str, Any]) -> List[str]:
    tx = tx_result.get("transaction")
    if not isinstance(tx, dict):
        raise RuntimeError("TX_MISSING_TRANSACTION_OBJECT")
    message = tx.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("TX_MISSING_MESSAGE")
    raw_keys = message.get("accountKeys")
    if not isinstance(raw_keys, list):
        raise RuntimeError("TX_MISSING_ACCOUNT_KEYS")

    keys: List[str] = []
    for item in raw_keys:
        if isinstance(item, str):
            keys.append(item)
        elif isinstance(item, dict) and isinstance(item.get("pubkey"), str):
            keys.append(item["pubkey"])
        else:
            raise RuntimeError("UNSUPPORTED_ACCOUNT_KEY_SHAPE")

    meta = tx_result.get("meta")
    if isinstance(meta, dict):
        loaded = meta.get("loadedAddresses")
        if isinstance(loaded, dict):
            for bucket in ("writable", "readonly"):
                values = loaded.get(bucket) or []
                if not isinstance(values, list):
                    raise RuntimeError("BAD_LOADED_ADDRESSES")
                for value in values:
                    if not isinstance(value, str):
                        raise RuntimeError("BAD_LOADED_ADDRESS_VALUE")
                    keys.append(value)
    return keys


def _compiled_instruction_record(
    ix: Dict[str, Any],
    keys: List[str],
    *,
    location: str,
    outer_index: int,
    inner_index: Optional[int],
) -> Dict[str, Any]:
    if not isinstance(ix, dict):
        raise RuntimeError("BAD_INSTRUCTION_SHAPE")

    if isinstance(ix.get("programId"), str):
        program_id = ix["programId"]
    else:
        pidx = ix.get("programIdIndex")
        if not isinstance(pidx, int) or pidx < 0 or pidx >= len(keys):
            raise RuntimeError("BAD_PROGRAM_ID_INDEX")
        program_id = keys[pidx]

    account_values = ix.get("accounts") or []
    if not isinstance(account_values, list):
        raise RuntimeError("BAD_INSTRUCTION_ACCOUNTS")
    resolved_accounts: List[str] = []
    account_indices: List[int] = []
    for value in account_values:
        if isinstance(value, int):
            account_indices.append(value)
            if value < 0 or value >= len(keys):
                raise RuntimeError("BAD_ACCOUNT_INDEX")
            resolved_accounts.append(keys[value])
        elif isinstance(value, str):
            resolved_accounts.append(value)
        else:
            raise RuntimeError("UNSUPPORTED_INSTRUCTION_ACCOUNT_SHAPE")

    data_b58 = ix.get("data")
    data_hex: Optional[str] = None
    prefix_8_hex: Optional[str] = None
    first_byte_hex: Optional[str] = None
    if isinstance(data_b58, str):
        decoded = b58decode(data_b58)
        data_hex = decoded.hex()
        prefix_8_hex = decoded[:8].hex() if decoded else ""
        first_byte_hex = decoded[:1].hex() if decoded else ""

    return {
        "location": location,
        "outer_index": outer_index,
        "inner_index": inner_index,
        "program_id": program_id,
        "account_indices": account_indices,
        "accounts": resolved_accounts,
        "data_base58": data_b58 if isinstance(data_b58, str) else None,
        "data_hex": data_hex,
        "prefix_8_hex": prefix_8_hex,
        "first_byte_hex": first_byte_hex,
        "parsed_present": "parsed" in ix,
    }


def extract_protocol_instructions(tx_result: Dict[str, Any], target_program: str) -> List[Dict[str, Any]]:
    keys = normalize_account_keys(tx_result)
    tx = tx_result["transaction"]
    message = tx["message"]
    outer = message.get("instructions")
    if not isinstance(outer, list):
        raise RuntimeError("TX_MISSING_OUTER_INSTRUCTIONS")

    records: List[Dict[str, Any]] = []
    for outer_index, ix in enumerate(outer):
        rec = _compiled_instruction_record(
            ix, keys, location="outer", outer_index=outer_index, inner_index=None
        )
        if rec["program_id"] == target_program:
            records.append(rec)

    meta = tx_result.get("meta")
    inner_groups = meta.get("innerInstructions") if isinstance(meta, dict) else None
    if inner_groups is None:
        return records
    if not isinstance(inner_groups, list):
        raise RuntimeError("BAD_INNER_INSTRUCTIONS")

    for group in inner_groups:
        if not isinstance(group, dict):
            raise RuntimeError("BAD_INNER_GROUP")
        outer_index = group.get("index")
        instructions = group.get("instructions")
        if not isinstance(outer_index, int) or not isinstance(instructions, list):
            raise RuntimeError("BAD_INNER_GROUP_FIELDS")
        for inner_index, ix in enumerate(instructions):
            rec = _compiled_instruction_record(
                ix,
                keys,
                location="inner",
                outer_index=outer_index,
                inner_index=inner_index,
            )
            if rec["program_id"] == target_program:
                records.append(rec)
    return records


def reference_matches(protocol_cfg: Dict[str, Any], instruction: Dict[str, Any]) -> List[str]:
    matches: List[str] = []
    first_byte = instruction.get("first_byte_hex")
    prefix_8 = instruction.get("prefix_8_hex")
    for spec in protocol_cfg.get("reference_liquidation_encodings") or []:
        enc = spec.get("encoding")
        prefix = spec.get("prefix_hex")
        if enc == "native_u8_tag" and first_byte == prefix:
            matches.append(str(spec.get("name")))
        elif enc == "anchor_discriminator_8" and prefix_8 == prefix:
            matches.append(str(spec.get("name")))
    return matches


def write_json(path: pathlib.Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return sha256_bytes(path.read_bytes())


def append_jsonl(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")


def select_protocols(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    protocols = registry["protocols"]
    requested_raw = os.environ.get("DLS_PROTOCOLS", "").strip()
    if not requested_raw:
        return protocols
    requested = [x.strip() for x in requested_raw.split(",") if x.strip()]
    by_name = {p["protocol"]: p for p in protocols}
    unknown = [x for x in requested if x not in by_name]
    if unknown:
        raise RuntimeError(f"UNKNOWN_PROTOCOLS {unknown}")
    return [by_name[x] for x in requested]


def collect_protocol(
    rpc: Rpc,
    protocol_cfg: Dict[str, Any],
    out_dir: pathlib.Path,
    *,
    max_pages: int,
    fetch_failed: bool,
    max_tx_version: int,
) -> Dict[str, Any]:
    protocol = protocol_cfg["protocol"]
    program_id = protocol_cfg["program_id"]
    sig_path = out_dir / "derived" / protocol / "signature_index.jsonl"
    tx_path = out_dir / "derived" / protocol / "transactions.jsonl"
    ix_path = out_dir / "derived" / protocol / "protocol_instructions.jsonl"

    for path in (sig_path, tx_path, ix_path):
        if path.exists():
            raise RuntimeError(
                f"OUTPUT_ALREADY_EXISTS protocol={protocol} path={path}; "
                "use a new DLS_OUT_DIR to preserve immutability"
            )

    before: Optional[str] = None
    page_no = 0
    seen_signatures: set[str] = set()
    previous_slot: Optional[int] = None
    stats: Dict[str, int] = {
        "signature_rows_seen": 0,
        "duplicate_signatures": 0,
        "newer_than_window": 0,
        "older_than_window": 0,
        "in_window": 0,
        "in_window_success_signature": 0,
        "in_window_failed_signature": 0,
        "full_transactions_fetched": 0,
        "full_transactions_missing": 0,
        "target_program_instruction_rows": 0,
        "reference_decoder_matches": 0,
        "target_program_zero_instruction_transactions": 0,
    }
    stop_reason = "UNKNOWN"
    partial_due_to_cap = False

    while True:
        if max_pages > 0 and page_no >= max_pages:
            partial_due_to_cap = True
            stop_reason = "MAX_PAGES_SAFETY_CAP"
            break

        config: Dict[str, Any] = {"limit": 1000, "commitment": "finalized"}
        if before:
            config["before"] = before
        page = rpc.call(
            "getSignaturesForAddress",
            [program_id, config],
            raw_subdir=f"{protocol}/signatures",
        )
        page_no += 1
        if not isinstance(page, list):
            raise RuntimeError(f"BAD_SIGNATURE_PAGE protocol={protocol}")
        if not page:
            stop_reason = "ADDRESS_HISTORY_EXHAUSTED"
            break

        page_all_older = True
        for row in page:
            if not isinstance(row, dict) or not isinstance(row.get("signature"), str):
                raise RuntimeError(f"BAD_SIGNATURE_ROW protocol={protocol}")
            signature = row["signature"]
            slot = row.get("slot")
            if not isinstance(slot, int):
                raise RuntimeError(f"SIGNATURE_ROW_MISSING_SLOT protocol={protocol}")
            if previous_slot is not None and slot > previous_slot:
                raise RuntimeError(
                    f"SIGNATURE_ORDER_REGRESSION protocol={protocol} "
                    f"previous_slot={previous_slot} slot={slot}"
                )
            previous_slot = slot

            if signature in seen_signatures:
                stats["duplicate_signatures"] += 1
                raise RuntimeError(f"DUPLICATE_SIGNATURE protocol={protocol} signature={signature}")
            seen_signatures.add(signature)
            stats["signature_rows_seen"] += 1

            block_time = resolve_block_time(rpc, protocol, row)
            if block_time >= SOURCE_START_UNIX:
                page_all_older = False

            sig_record = {
                "protocol": protocol,
                "program_id": program_id,
                "signature": signature,
                "slot": slot,
                "block_time": block_time,
                "block_time_utc": utc_iso(block_time),
                "signature_err": row.get("err"),
                "confirmation_status": row.get("confirmationStatus"),
                "memo": row.get("memo"),
                "source_window_member": SOURCE_START_UNIX <= block_time <= SOURCE_END_UNIX,
            }
            append_jsonl(sig_path, sig_record)

            if block_time > SOURCE_END_UNIX:
                stats["newer_than_window"] += 1
                continue
            if block_time < SOURCE_START_UNIX:
                stats["older_than_window"] += 1
                continue

            stats["in_window"] += 1
            failed_sig = row.get("err") is not None
            if failed_sig:
                stats["in_window_failed_signature"] += 1
                if not fetch_failed:
                    continue
            else:
                stats["in_window_success_signature"] += 1

            tx_result = rpc.call(
                "getTransaction",
                [
                    signature,
                    {
                        "encoding": "json",
                        "commitment": "finalized",
                        "maxSupportedTransactionVersion": max_tx_version,
                    },
                ],
                raw_subdir=f"{protocol}/transactions",
            )
            if tx_result is None:
                stats["full_transactions_missing"] += 1
                raise RuntimeError(
                    f"MISSING_FULL_TRANSACTION protocol={protocol} signature={signature}"
                )
            if not isinstance(tx_result, dict):
                raise RuntimeError(
                    f"BAD_TRANSACTION_RESULT protocol={protocol} signature={signature}"
                )
            stats["full_transactions_fetched"] += 1

            result_slot = tx_result.get("slot")
            result_time = tx_result.get("blockTime")
            if result_slot != slot:
                raise RuntimeError(
                    f"TX_SLOT_MISMATCH protocol={protocol} signature={signature} "
                    f"index_slot={slot} tx_slot={result_slot}"
                )
            if not isinstance(result_time, int) or result_time != block_time:
                raise RuntimeError(
                    f"TX_BLOCKTIME_MISMATCH protocol={protocol} signature={signature}"
                )

            meta = tx_result.get("meta")
            meta_err = meta.get("err") if isinstance(meta, dict) else None
            if (meta_err is None) != (row.get("err") is None):
                raise RuntimeError(
                    f"TX_STATUS_MISMATCH protocol={protocol} signature={signature}"
                )

            instructions = extract_protocol_instructions(tx_result, program_id)
            if not instructions:
                stats["target_program_zero_instruction_transactions"] += 1

            tx_record = {
                "protocol": protocol,
                "program_id": program_id,
                "signature": signature,
                "slot": slot,
                "block_time": block_time,
                "block_time_utc": utc_iso(block_time),
                "success": meta_err is None,
                "transaction_version": tx_result.get("version"),
                "target_program_instruction_count": len(instructions),
                "economic_outcome_fields_added": False,
            }
            append_jsonl(tx_path, tx_record)

            for ix in instructions:
                matches = reference_matches(protocol_cfg, ix)
                rec = {
                    "protocol": protocol,
                    "program_id": program_id,
                    "signature": signature,
                    "slot": slot,
                    "block_time": block_time,
                    "block_time_utc": utc_iso(block_time),
                    "success": meta_err is None,
                    **ix,
                    "reference_liquidation_matches": matches,
                    "reference_match_is_authoritative": False,
                }
                append_jsonl(ix_path, rec)
                stats["target_program_instruction_rows"] += 1
                stats["reference_decoder_matches"] += len(matches)

        before = page[-1]["signature"]
        if page_all_older:
            stop_reason = "CROSSED_FROZEN_START"
            break

    return {
        "protocol": protocol,
        "program_id": program_id,
        "pages_fetched": page_no,
        "partial_due_to_safety_cap": partial_due_to_cap,
        "stop_reason": stop_reason,
        "stats": stats,
        "derived_files": {
            "signature_index": str(sig_path.relative_to(out_dir).as_posix()),
            "transactions": str(tx_path.relative_to(out_dir).as_posix()),
            "protocol_instructions": str(ix_path.relative_to(out_dir).as_posix()),
        },
    }


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    registry_path = here / "protocol_registry_v0_1.json"
    registry = load_registry(registry_path)
    protocols = select_protocols(registry)

    out_dir = pathlib.Path(
        os.environ.get("DLS_OUT_DIR", "data/defi_liquidation_shock_001/source_v01")
    ).resolve()
    if (out_dir / "RUN_MANIFEST.json").exists():
        raise RuntimeError(
            f"RUN_MANIFEST_ALREADY_EXISTS {out_dir}; use a new DLS_OUT_DIR to preserve immutability"
        )
    raw_dir = out_dir / "raw_rpc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    delay = float(os.environ.get("DLS_RPS_DELAY", "0.12"))
    max_pages = int(os.environ.get("DLS_MAX_PAGES_PER_PROTOCOL", "0"))
    fetch_failed = os.environ.get("DLS_FETCH_FAILED", "1").strip() not in {"0", "false", "False"}
    max_tx_version = int(os.environ.get("DLS_MAX_SUPPORTED_TX_VERSION", "0"))
    if delay < 0 or max_pages < 0 or max_tx_version != 0:
        raise RuntimeError(
            "INVALID_OR_UNFROZEN_CONFIGURATION: delay>=0, max_pages>=0, "
            "DLS_MAX_SUPPORTED_TX_VERSION must remain 0 in V0.1"
        )

    url = rpc_url()
    rpc = Rpc(url, raw_dir, delay)
    started = int(time.time())
    protocol_results: List[Dict[str, Any]] = []
    run_status = "SOURCE_ACQUISITION_COMPLETE"

    try:
        for cfg in protocols:
            result = collect_protocol(
                rpc,
                cfg,
                out_dir,
                max_pages=max_pages,
                fetch_failed=fetch_failed,
                max_tx_version=max_tx_version,
            )
            protocol_results.append(result)
            if result["partial_due_to_safety_cap"]:
                run_status = "SOURCE_ACQUISITION_PARTIAL"
    except Exception as exc:
        run_status = "SOURCE_ACQUISITION_FAILED"
        error_path = out_dir / "RUN_ERROR.json"
        write_json(
            error_path,
            {
                "lab_id": LAB_ID,
                "collector_version": COLLECTOR_VERSION,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "outcome_fields_queried": False,
                "prices_queried": False,
                "returns_computed": False,
                "pnl_computed": False,
            },
        )
        raise
    finally:
        receipts_path = out_dir / "RPC_RECEIPTS.json"
        write_json(receipts_path, rpc.receipts)

        manifest = {
            "lab_id": LAB_ID,
            "collector_version": COLLECTOR_VERSION,
            "run_status": run_status,
            "started_unix": started,
            "finished_unix": int(time.time()),
            "rpc_url": redact_rpc_url(url),
            "source_window_utc": {"start": SOURCE_START_ISO, "end": SOURCE_END_ISO},
            "selected_protocols": [p["protocol"] for p in protocols],
            "configuration": {
                "rps_delay": delay,
                "max_pages_per_protocol": max_pages,
                "fetch_failed_transactions": fetch_failed,
                "max_supported_transaction_version": max_tx_version,
            },
            "protocol_results": protocol_results,
            "rpc_request_count": rpc.request_id,
            "rpc_receipts_sha256": sha256_bytes(receipts_path.read_bytes())
            if receipts_path.exists()
            else None,
            "governance": {
                "read_only": True,
                "prices_queried": False,
                "returns_computed": False,
                "pnl_computed": False,
                "direction_tested": False,
                "live_trading": False,
                "exchange_mutation": False,
                "source_data_pass_implied": False,
            },
        }
        if max_pages > 0:
            manifest["warning"] = (
                "DLS_MAX_PAGES_PER_PROTOCOL was set. Any protocol that hits the cap is PARTIAL "
                "and cannot establish population completeness or SOURCE_DATA_PASS."
            )
        write_json(out_dir / "RUN_MANIFEST.json", manifest)

    print(json.dumps({"status": run_status, "out_dir": str(out_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("INTERRUPTED: source acquisition incomplete; no Source Data PASS", file=sys.stderr)
        raise SystemExit(130)
