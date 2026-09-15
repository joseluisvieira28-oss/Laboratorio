#!/usr/bin/env python3
"""MSEL-001 frozen 25-launch cohort collector.

READ-ONLY / RESEARCH-ONLY.

Purpose:
  - query archival Solana transactions involving the Pump program,
  - start at the preregistered blind timestamp,
  - decode the historical Pump `create` instruction,
  - stop after the first 25 successful creates,
  - save immutable raw pages + hashes before derived cohort records.

This script DOES NOT:
  - query future token outcomes,
  - trade,
  - submit Solana transactions,
  - modify exchange or chain state,
  - select/reject launches based on performance.

Environment:
  HELIUS_API_KEY   required unless HELIUS_RPC_URL is supplied
  HELIUS_RPC_URL   optional full archival RPC URL
  MSEL_OUT_DIR     optional output directory
  MSEL_MAX_PAGES   optional safety cap, default 100

The collector is intentionally fail-closed. If canonical ordering is ambiguous
(e.g. selected creates share a slot but transaction indexes are unavailable),
it refuses to finalize a cohort manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import struct
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
FROZEN_START_UNIX = 1749817333  # 2025-06-13T12:22:13Z
FROZEN_START_ISO = "2025-06-13T12:22:13Z"
TARGET_CREATES = 25
CREATE_DISC = bytes([24, 30, 200, 40, 5, 28, 7, 119])
BUY_DISC = bytes([102, 6, 61, 18, 1, 218, 235, 234])
HISTORICAL_IDL_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"

B58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_INDEX = {c: i for i, c in enumerate(B58_ALPHABET)}


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s.encode("ascii"):
        if ch not in B58_INDEX:
            raise ValueError(f"invalid base58 character: {chr(ch)!r}")
        n = n * 58 + B58_INDEX[ch]
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    chars = bytearray()
    while n:
        n, r = divmod(n, 58)
        chars.append(B58_ALPHABET[r])
    chars.reverse()
    pad = len(raw) - len(raw.lstrip(b"\x00"))
    return (B58_ALPHABET[:1] * pad + (bytes(chars) if chars else b"")).decode("ascii") or "1"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def rpc_url() -> str:
    explicit = os.environ.get("HELIUS_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing HELIUS_API_KEY (or HELIUS_RPC_URL). No network request made.")
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


def rpc_call(url: str, method: str, params: list, request_id: int) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "MSEL-001/0.1 research-only"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"RPC HTTP {exc.code}: {detail[:1000]}") from exc
    parsed = json.loads(body)
    if parsed.get("error"):
        raise RuntimeError(f"RPC error: {parsed['error']}")
    return parsed.get("result"), body


def get_static_keys(message: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for k in message.get("accountKeys", []) or []:
        if isinstance(k, str):
            out.append(k)
        elif isinstance(k, dict):
            pk = k.get("pubkey")
            if pk:
                out.append(pk)
        else:
            out.append(str(k))
    return out


def get_all_keys(item: Dict[str, Any]) -> List[str]:
    tx = item.get("transaction") or {}
    message = tx.get("message") or {}
    keys = get_static_keys(message)
    meta = item.get("meta") or {}
    loaded = meta.get("loadedAddresses") or {}
    for k in loaded.get("writable", []) or []:
        keys.append(k if isinstance(k, str) else str(k))
    for k in loaded.get("readonly", []) or []:
        keys.append(k if isinstance(k, str) else str(k))
    return keys


def resolve_program_id(ix: Dict[str, Any], keys: Sequence[str]) -> Optional[str]:
    if ix.get("programId"):
        p = ix["programId"]
        return p.get("pubkey") if isinstance(p, dict) else str(p)
    idx = ix.get("programIdIndex")
    if isinstance(idx, int) and 0 <= idx < len(keys):
        return keys[idx]
    return None


def resolve_ix_accounts(ix: Dict[str, Any], keys: Sequence[str]) -> List[str]:
    out: List[str] = []
    for a in ix.get("accounts", []) or []:
        if isinstance(a, int):
            if not (0 <= a < len(keys)):
                raise ValueError(f"instruction account index out of bounds: {a}/{len(keys)}")
            out.append(keys[a])
        elif isinstance(a, str):
            out.append(a)
        elif isinstance(a, dict) and a.get("pubkey"):
            out.append(str(a["pubkey"]))
        else:
            raise ValueError(f"unsupported instruction account form: {a!r}")
    return out


def parse_borsh_string(buf: bytes, pos: int) -> Tuple[str, int]:
    if pos + 4 > len(buf):
        raise ValueError("truncated borsh string length")
    (n,) = struct.unpack_from("<I", buf, pos)
    pos += 4
    if pos + n > len(buf):
        raise ValueError("truncated borsh string data")
    text = buf[pos : pos + n].decode("utf-8")
    return text, pos + n


def decode_create_data(data_b58: str) -> Dict[str, str]:
    raw = b58decode(data_b58)
    if not raw.startswith(CREATE_DISC):
        raise ValueError("not historical create discriminator")
    pos = 8
    name, pos = parse_borsh_string(raw, pos)
    symbol, pos = parse_borsh_string(raw, pos)
    uri, pos = parse_borsh_string(raw, pos)
    if pos + 32 > len(raw):
        raise ValueError("truncated creator pubkey")
    creator = b58encode(raw[pos : pos + 32])
    pos += 32
    return {
        "name": name,
        "symbol": symbol,
        "uri": uri,
        "origin_creator": creator,
        "raw_data_sha256": sha256_bytes(raw),
        "trailing_bytes": str(len(raw) - pos),
    }


def get_ix_data(ix: Dict[str, Any]) -> Optional[str]:
    data = ix.get("data")
    if isinstance(data, str):
        return data
    return None


def outer_and_inner_instructions(item: Dict[str, Any]) -> Iterable[Tuple[str, int, Dict[str, Any]]]:
    tx = item.get("transaction") or {}
    msg = tx.get("message") or {}
    for i, ix in enumerate(msg.get("instructions", []) or []):
        if isinstance(ix, dict):
            yield "outer", i, ix
    meta = item.get("meta") or {}
    for inner_group in meta.get("innerInstructions", []) or []:
        parent = inner_group.get("index")
        for j, ix in enumerate(inner_group.get("instructions", []) or []):
            if isinstance(ix, dict):
                yield f"inner:{parent}", j, ix


def transaction_signature(item: Dict[str, Any]) -> Optional[str]:
    tx = item.get("transaction") or {}
    sigs = tx.get("signatures") or []
    if sigs:
        return sigs[0]
    return item.get("signature")


def fee_payer(item: Dict[str, Any], keys: Sequence[str]) -> Optional[str]:
    return keys[0] if keys else None


def tx_index(item: Dict[str, Any]) -> Optional[int]:
    for key in ("transactionIndex", "transaction_index", "index"):
        val = item.get(key)
        if isinstance(val, int):
            return val
    return None


def same_tx_has_buy(item: Dict[str, Any], keys: Sequence[str], mint: Optional[str]) -> bool:
    for _scope, _i, ix in outer_and_inner_instructions(item):
        if resolve_program_id(ix, keys) != PUMP_PROGRAM:
            continue
        data = get_ix_data(ix)
        if not data:
            continue
        try:
            raw = b58decode(data)
        except Exception:
            continue
        if not raw.startswith(BUY_DISC):
            continue
        if mint is None:
            return True
        try:
            accounts = resolve_ix_accounts(ix, keys)
        except Exception:
            return True
        # Historical buy account position 2 is mint. Fail open only for this
        # descriptive flag; the cohort inclusion itself does not depend on it.
        if len(accounts) > 2 and accounts[2] == mint:
            return True
    return False


def extract_creates(item: Dict[str, Any], source_order: int) -> List[Dict[str, Any]]:
    keys = get_all_keys(item)
    sig = transaction_signature(item)
    slot = item.get("slot")
    block_time = item.get("blockTime")
    out: List[Dict[str, Any]] = []

    if not isinstance(block_time, int) or block_time <= FROZEN_START_UNIX:
        return out

    for scope, ix_idx, ix in outer_and_inner_instructions(item):
        if resolve_program_id(ix, keys) != PUMP_PROGRAM:
            continue
        data = get_ix_data(ix)
        if not data:
            continue
        try:
            raw = b58decode(data)
        except Exception:
            continue
        if not raw.startswith(CREATE_DISC):
            continue

        decoded = decode_create_data(data)
        accounts = resolve_ix_accounts(ix, keys)
        if len(accounts) < 8:
            raise RuntimeError(f"CREATE_ACCOUNT_SHAPE_FAILURE signature={sig} accounts={len(accounts)}")

        mint = accounts[0]
        tx_user = accounts[7]
        rec: Dict[str, Any] = {
            "slot": slot,
            "block_time": block_time,
            "transaction_index": tx_index(item),
            "source_order": source_order,
            "signature": sig,
            "instruction_scope": scope,
            "instruction_index": ix_idx,
            "mint": mint,
            "bonding_curve": accounts[2] if len(accounts) > 2 else None,
            "tx_user": tx_user,
            "fee_payer": fee_payer(item, keys),
            **decoded,
        }
        rec["origin_creator_eq_tx_user"] = rec["origin_creator"] == tx_user
        rec["origin_creator_eq_fee_payer"] = rec["origin_creator"] == rec["fee_payer"]
        rec["same_tx_pump_buy"] = same_tx_has_buy(item, keys, mint)
        out.append(rec)
    return out


def verify_ordering(records: List[Dict[str, Any]]) -> None:
    by_slot: Dict[Any, List[Dict[str, Any]]] = {}
    for r in records:
        by_slot.setdefault(r["slot"], []).append(r)
    ambiguous = []
    for slot, group in by_slot.items():
        if len(group) > 1 and any(r.get("transaction_index") is None for r in group):
            ambiguous.append(slot)
    if ambiguous:
        raise RuntimeError(
            "ORDERING_AMBIGUITY: multiple selected CREATE events share slots "
            f"{ambiguous[:10]} but transaction_index is unavailable. Cohort not finalized."
        )


def main() -> int:
    out_dir = pathlib.Path(os.environ.get("MSEL_OUT_DIR", "data/msel001_pilot25")).resolve()
    raw_dir = out_dir / "raw_pages"
    raw_dir.mkdir(parents=True, exist_ok=True)
    max_pages = int(os.environ.get("MSEL_MAX_PAGES", "100"))
    url = rpc_url()

    records: List[Dict[str, Any]] = []
    pagination: Optional[str] = None
    source_order = 0
    page_hashes: List[Dict[str, Any]] = []

    for page_no in range(1, max_pages + 1):
        opts: Dict[str, Any] = {
            "transactionDetails": "full",
            "sortOrder": "asc",
            "limit": 100,
            "encoding": "json",
            "maxSupportedTransactionVersion": 0,
            "filters": {
                "blockTime": {"gte": FROZEN_START_UNIX},
                "status": "succeeded",
            },
        }
        if pagination:
            opts["paginationToken"] = pagination

        result, raw_http = rpc_call(url, "getTransactionsForAddress", [PUMP_PROGRAM, opts], page_no)
        page_blob = canonical_json_bytes(result)
        page_sha = sha256_bytes(page_blob)
        page_path = raw_dir / f"page_{page_no:04d}_{page_sha[:16]}.json"
        page_path.write_bytes(page_blob + b"\n")
        page_hashes.append({"page": page_no, "sha256": page_sha, "file": page_path.name})

        if not isinstance(result, dict):
            raise RuntimeError(f"unexpected gTFA result type: {type(result).__name__}")
        data = result.get("data") or []
        if not isinstance(data, list):
            raise RuntimeError("unexpected gTFA result.data shape")

        for item in data:
            source_order += 1
            if not isinstance(item, dict):
                continue
            for rec in extract_creates(item, source_order):
                records.append(rec)
                if len(records) >= TARGET_CREATES:
                    break
            if len(records) >= TARGET_CREATES:
                break

        if len(records) >= TARGET_CREATES:
            break

        pagination = result.get("paginationToken")
        if not pagination:
            break
        time.sleep(0.05)

    if len(records) < TARGET_CREATES:
        raise RuntimeError(
            f"INSUFFICIENT_SOURCE_WINDOW: decoded {len(records)}/{TARGET_CREATES} creates "
            f"within {len(page_hashes)} pages; cohort not finalized"
        )

    records = records[:TARGET_CREATES]
    verify_ordering(records)

    # Helius chronological source order is retained. When tx indexes are present,
    # use them as the canonical intra-slot key. Signature/ix index provide stable
    # tie-breakers. source_order is retained for audit but not used to cherry-pick.
    records.sort(
        key=lambda r: (
            int(r["slot"]),
            r["transaction_index"] if r["transaction_index"] is not None else 0,
            r["signature"] or "",
            r["instruction_index"],
        )
    )

    cohort_path = out_dir / "cohort_25.jsonl"
    with cohort_path.open("w", encoding="utf-8") as f:
        for rank, rec in enumerate(records, 1):
            rec = dict(rec)
            rec["cohort_rank"] = rank
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    cohort_sha = sha256_bytes(cohort_path.read_bytes())
    manifest = {
        "lab": "MSEL-001",
        "status": "FEATURE_SOURCE_ONLY_OUTCOMES_LOCKED",
        "frozen_start_utc": FROZEN_START_ISO,
        "frozen_start_unix": FROZEN_START_UNIX,
        "program_id": PUMP_PROGRAM,
        "historical_idl_commit": HISTORICAL_IDL_COMMIT,
        "create_discriminator_hex": CREATE_DISC.hex(),
        "cohort_size": len(records),
        "cohort_sha256": cohort_sha,
        "raw_pages": page_hashes,
        "raw_page_count": len(page_hashes),
        "outcomes_opened": False,
    }
    manifest_path = out_dir / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"PASS: frozen cohort decoded: {len(records)} launches")
    print(f"cohort: {cohort_path}")
    print(f"cohort sha256: {cohort_sha}")
    print(f"manifest: {manifest_path}")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
