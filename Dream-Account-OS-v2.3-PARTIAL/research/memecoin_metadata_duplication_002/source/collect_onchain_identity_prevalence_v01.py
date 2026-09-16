#!/usr/bin/env python3
"""MSEL-002 frozen on-chain immutable-identity source/prevalence collector.

READ-ONLY / RESEARCH-ONLY / ECONOMIC OUTCOMES LOCKED.

This program implements MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_FREEZE_V01.md.
It selects a deterministic 12h source window (6h warmup + 6h candidates),
retrieves transactions involving pump.fun's Token Mint Authority, decodes only
successful Pump CREATE instructions using the pinned 2025-08-29 schema, and
computes source/prevalence diagnostics for exact immutable identity reuse.

It DOES NOT query candidate future prices, post-launch trade paths, migration,
graduation, returns, liquidity survival, winner/catastrophe labels, or MSEL-001
outcomes. It never submits a transaction.
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
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
TOKEN_MINT_AUTHORITY = "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"
CREATE_DISC = bytes([24, 30, 200, 40, 5, 28, 7, 119])
PINNED_IDL_COMMIT = "7645c16c68ae9dd3a7487b543edcdc94adf7b5e0"
PINNED_IDL_BLOB_SHA = "5ef1cbb696a0957cc7e4e191652d439d797982e9"

SEED = "MSEL-002-URI-REUSE-V1|blind|source-prevalence|2026-09-16"
REGIME_START = 1756684800  # 2025-09-01T00:00:00Z
REGIME_SECONDS = 5_270_400  # through 2025-11-01T00:00:00Z
PILOT_SECONDS = 43_200
WARMUP_SECONDS = 21_600
CANDIDATE_SECONDS = 21_600
LOOKBACK_SECONDS = 21_600

MIN_CANDIDATES = 2_000
MIN_IMMUTABLE_CANDIDATES = 500
MIN_EXPOSED = 30
MIN_EXPOSED_IDENTITIES = 10
MIN_EXPOSED_CREATORS = 20
MAX_LARGEST_IDENTITY_SHARE = 0.50

B58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_INDEX = {c: i for i, c in enumerate(B58_ALPHABET)}

HERE = pathlib.Path(__file__).resolve().parent
OUT_DIR = pathlib.Path(os.environ.get("MSEL002_OUT_DIR", str(HERE / "data" / "onchain_identity_source_v01"))).resolve()
RAW_DIR = OUT_DIR / "raw_rpc"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: pathlib.Path) -> str:
    return sha256_bytes(p.read_bytes())


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def dump_json_new(path: pathlib.Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"OUTPUT_ALREADY_EXISTS {path}")
    blob = (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(blob)
    return sha256_bytes(blob)


def dump_jsonl_new(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"OUTPUT_ALREADY_EXISTS {path}")
    h = hashlib.sha256()
    with path.open("wb") as f:
        for r in rows:
            blob = canonical_json_bytes(r) + b"\n"
            f.write(blob)
            h.update(blob)
    return h.hexdigest()


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s.encode("ascii"):
        if ch not in B58_INDEX:
            raise ValueError(f"invalid base58 character {chr(ch)!r}")
        n = n * 58 + B58_INDEX[ch]
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    chars = bytearray()
    while n:
        n, rem = divmod(n, 58)
        chars.append(B58_ALPHABET[rem])
    chars.reverse()
    pad = len(raw) - len(raw.lstrip(b"\x00"))
    out = B58_ALPHABET[:1] * pad + (bytes(chars) if chars else b"")
    return out.decode("ascii") or "1"


def parse_borsh_string(buf: bytes, pos: int) -> Tuple[str, int]:
    if pos + 4 > len(buf):
        raise ValueError("TRUNCATED_STRING_LENGTH")
    (n,) = struct.unpack_from("<I", buf, pos)
    pos += 4
    if n < 0 or pos + n > len(buf):
        raise ValueError("TRUNCATED_STRING_DATA")
    return buf[pos:pos+n].decode("utf-8"), pos + n


def decode_create_data(data_b58: str) -> Dict[str, str]:
    raw = b58decode(data_b58)
    if not raw.startswith(CREATE_DISC):
        raise ValueError("NOT_CREATE")
    pos = 8
    name, pos = parse_borsh_string(raw, pos)
    symbol, pos = parse_borsh_string(raw, pos)
    uri, pos = parse_borsh_string(raw, pos)
    if pos + 32 > len(raw):
        raise ValueError("TRUNCATED_CREATOR")
    creator = b58encode(raw[pos:pos+32])
    pos += 32
    return {
        "name": name,
        "symbol": symbol,
        "uri": uri,
        "origin_creator": creator,
        "create_raw_sha256": sha256_bytes(raw),
        "create_trailing_bytes": str(len(raw) - pos),
    }


def canonical_immutable_uri(uri: str) -> Optional[str]:
    """Frozen canonicalizer. No network dereference."""
    if not isinstance(uri, str) or not uri:
        return None
    if uri.startswith("ipfs://"):
        rest = uri[len("ipfs://"):]
        if not rest or rest.startswith("/"):
            return None
        return "ipfs://" + rest
    if uri.startswith("ar://"):
        rest = uri[len("ar://"):]
        if not rest or rest.startswith("/"):
            return None
        return "ar://" + rest
    try:
        u = urllib.parse.urlsplit(uri)
    except Exception:
        return None
    if u.scheme not in ("http", "https") or not u.hostname:
        return None
    path_parts = [p for p in u.path.split("/") if p != ""]
    # Standard IPFS path gateway: https://gateway.example/ipfs/CID/path
    for i, p in enumerate(path_parts):
        if p == "ipfs" and i + 1 < len(path_parts):
            cid = path_parts[i+1]
            tail = path_parts[i+2:]
            if not cid:
                return None
            return "ipfs://" + cid + (("/" + "/".join(tail)) if tail else "")
    # IPFS subdomain gateway: https://CID.ipfs.gateway.example/path
    labels = u.hostname.split(".")
    if len(labels) >= 3 and "ipfs" in labels[1:]:
        ipfs_i = labels.index("ipfs")
        if ipfs_i >= 1:
            cid = labels[0]
            tail = [p for p in u.path.split("/") if p]
            if cid:
                return "ipfs://" + cid + (("/" + "/".join(tail)) if tail else "")
    # Arweave canonical gateway only.
    if u.hostname.lower() == "arweave.net" and path_parts:
        txid = path_parts[0]
        tail = path_parts[1:]
        return "ar://" + txid + (("/" + "/".join(tail)) if tail else "")
    return None


def identity_key(name: str, symbol: str, canonical_uri: str) -> str:
    return sha256_bytes((name + "\0" + symbol + "\0" + canonical_uri).encode("utf-8"))


def frozen_window() -> Dict[str, int | str]:
    d = hashlib.sha256(SEED.encode("utf-8")).digest()
    r = int.from_bytes(d[:8], "big", signed=False)
    offset = r % (REGIME_SECONDS - PILOT_SECONDS)
    source_start = REGIME_START + offset
    candidate_start = source_start + WARMUP_SECONDS
    source_end = source_start + PILOT_SECONDS
    return {
        "seed": SEED,
        "seed_sha256": d.hex(),
        "offset_seconds": offset,
        "source_start": source_start,
        "candidate_start": candidate_start,
        "source_end": source_end,
    }


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if key:
        return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return "https://api.mainnet-beta.solana.com"


class Rpc:
    def __init__(self, url: str) -> None:
        self.url = url
        self.request_id = 0
        self.raw_seq = 0
        self.receipts: List[Dict[str, Any]] = []
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.delay = float(os.environ.get("MSEL_RPS_DELAY", "0.15"))
        self.max_retries = int(os.environ.get("MSEL_RPC_RETRIES", "7"))

    def _post(self, payload: Any, label: str) -> bytes:
        request_bytes = canonical_json_bytes(payload)
        backoff = 1.0
        last = None
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(
                self.url,
                data=request_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "MSEL-002/0.1 source-only"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    blob = resp.read()
                if self.delay:
                    time.sleep(self.delay)
                self.raw_seq += 1
                fname = f"{self.raw_seq:06d}_{label}_{sha256_bytes(blob)[:16]}.json"
                (RAW_DIR / fname).write_bytes(blob)
                self.receipts.append({
                    "raw_seq": self.raw_seq,
                    "label": label,
                    "request_sha256": sha256_bytes(request_bytes),
                    "response_sha256": sha256_bytes(blob),
                    "response_bytes": len(blob),
                    "raw_file": fname,
                    "attempt": attempt,
                })
                return blob
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last = f"HTTP_{exc.code}:{detail[:500]}"
                if exc.code not in (429, 500, 502, 503, 504) or attempt >= self.max_retries:
                    raise RuntimeError(f"RPC_{last} label={label}") from exc
            except urllib.error.URLError as exc:
                last = f"NETWORK:{exc}"
                if attempt >= self.max_retries:
                    raise RuntimeError(f"RPC_{last} label={label}") from exc
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 30.0)
        raise RuntimeError(f"RPC_RETRY_EXHAUSTED {label} {last}")

    def call(self, method: str, params: list, label: Optional[str] = None) -> Any:
        self.request_id += 1
        payload = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        blob = self._post(payload, label or method)
        obj = json.loads(blob)
        if obj.get("error") is not None:
            raise RuntimeError(f"RPC_ERROR method={method} error={obj['error']}")
        return obj.get("result")

    def batch(self, calls: List[Tuple[str, list]], label: str) -> List[Any]:
        payload = []
        ids = []
        for method, params in calls:
            self.request_id += 1
            ids.append(self.request_id)
            payload.append({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params})
        blob = self._post(payload, label)
        obj = json.loads(blob)
        if not isinstance(obj, list):
            raise RuntimeError(f"BATCH_RESPONSE_NOT_LIST {label}")
        by_id = {int(x.get("id")): x for x in obj if isinstance(x, dict) and x.get("id") is not None}
        out = []
        for rid in ids:
            if rid not in by_id:
                raise RuntimeError(f"BATCH_MISSING_ID {rid} {label}")
            item = by_id[rid]
            if item.get("error") is not None:
                raise RuntimeError(f"BATCH_RPC_ERROR id={rid} error={item['error']}")
            out.append(item.get("result"))
        return out


def next_confirmed_slot(rpc: Rpc, start: int) -> Optional[int]:
    r = rpc.call("getBlocksWithLimit", [start, 1], "getBlocksWithLimit")
    if not isinstance(r, list):
        raise RuntimeError("BAD_GETBLOCKSWITHLIMIT")
    return int(r[0]) if r else None


def block_time(rpc: Rpc, slot: int) -> int:
    r = rpc.call("getBlockTime", [slot], "getBlockTime")
    if not isinstance(r, int):
        raise RuntimeError(f"MISSING_BLOCKTIME slot={slot}")
    return r


def find_first_confirmed_at_or_after(rpc: Rpc, ts: int) -> Tuple[int, int, int, int]:
    lo_raw = rpc.call("getFirstAvailableBlock", [], "getFirstAvailableBlock")
    hi_raw = rpc.call("getSlot", [{"commitment": "finalized"}], "getSlot")
    if not isinstance(lo_raw, int) or not isinstance(hi_raw, int):
        raise RuntimeError("BAD_PROVIDER_SLOT_BOUNDS")
    lo, hi = int(lo_raw), int(hi_raw)
    first = next_confirmed_slot(rpc, lo)
    if first is None or block_time(rpc, first) > ts:
        raise RuntimeError("PROVIDER_HISTORY_START_AFTER_TARGET")
    while lo < hi:
        mid = (lo + hi) // 2
        s = next_confirmed_slot(rpc, mid)
        if s is None:
            hi = mid
            continue
        t = block_time(rpc, s)
        if t < ts:
            lo = s + 1
        else:
            hi = mid
    candidate = next_confirmed_slot(rpc, lo)
    if candidate is None:
        raise RuntimeError("NO_BOUNDARY_CANDIDATE")
    # Prove local before/after with confirmed blocks.
    slots = rpc.call("getBlocks", [max(0, candidate - 512), candidate + 32], "getBlocks_boundary")
    if not isinstance(slots, list) or not slots:
        raise RuntimeError("BOUNDARY_WINDOW_EMPTY")
    times = [(int(s), block_time(rpc, int(s))) for s in slots]
    before = [(s, t) for s, t in times if t < ts]
    after = [(s, t) for s, t in times if t >= ts]
    if not before or not after:
        raise RuntimeError("BOUNDARY_NOT_PROVEN")
    first_after = min(after, key=lambda x: x[0])
    last_before = max(before, key=lambda x: x[0])
    if not (last_before[1] < ts <= first_after[1]) or last_before[0] >= first_after[0]:
        raise RuntimeError("BOUNDARY_ORDER_FAILURE")
    return first_after[0], first_after[1], last_before[0], last_before[1]


def static_account_keys(tx_result: Dict[str, Any]) -> List[str]:
    msg = ((tx_result.get("transaction") or {}).get("message") or {})
    out = []
    for k in msg.get("accountKeys") or []:
        if isinstance(k, str):
            out.append(k)
        elif isinstance(k, dict) and isinstance(k.get("pubkey"), str):
            out.append(k["pubkey"])
        else:
            raise RuntimeError("ACCOUNT_KEY_SHAPE_FAILURE")
    loaded = ((tx_result.get("meta") or {}).get("loadedAddresses") or {})
    out.extend(str(x) for x in (loaded.get("writable") or []))
    out.extend(str(x) for x in (loaded.get("readonly") or []))
    return out


def transaction_mentions(result: Dict[str, Any], key: str) -> bool:
    return key in static_account_keys(result)


def first_signature(result: Dict[str, Any]) -> Optional[str]:
    sigs = ((result.get("transaction") or {}).get("signatures") or [])
    return str(sigs[0]) if sigs else None


def fetch_full_block(rpc: Rpc, slot: int, label: str) -> Dict[str, Any]:
    r = rpc.call("getBlock", [slot, {
        "encoding": "json",
        "transactionDetails": "full",
        "rewards": False,
        "maxSupportedTransactionVersion": 0,
        "commitment": "finalized",
    }], label)
    if not isinstance(r, dict):
        raise RuntimeError(f"BLOCK_MISSING slot={slot}")
    return r


def find_authority_anchor_after(rpc: Rpc, start_slot: int, min_time: int) -> Dict[str, Any]:
    cursor = start_slot
    scanned = 0
    max_blocks = 4096
    while scanned < max_blocks:
        end = cursor + min(511, max_blocks - scanned)
        slots = rpc.call("getBlocks", [cursor, end], "getBlocks_anchor")
        if not isinstance(slots, list):
            raise RuntimeError("BAD_ANCHOR_BLOCK_LIST")
        if not slots:
            cursor = end + 1
            continue
        for s0 in slots:
            slot = int(s0)
            block = fetch_full_block(rpc, slot, "getBlock_anchor")
            scanned += 1
            bt = block.get("blockTime")
            if not isinstance(bt, int) or bt < min_time:
                continue
            for item in block.get("transactions") or []:
                if not isinstance(item, dict):
                    continue
                meta = item.get("meta") or {}
                if meta.get("err") is not None:
                    continue
                # adapt block transaction shape to helper expected by transaction result
                candidate = {"transaction": item.get("transaction"), "meta": meta}
                if transaction_mentions(candidate, TOKEN_MINT_AUTHORITY):
                    sig = first_signature(candidate)
                    if sig:
                        return {"signature": sig, "slot": slot, "block_time": bt, "blocks_scanned": scanned}
            if scanned >= max_blocks:
                break
        cursor = int(slots[-1]) + 1
    raise RuntimeError("AUTHORITY_ANCHOR_NOT_FOUND")


def collect_authority_signatures(rpc: Rpc, before_signature: str, start_ts: int, end_ts: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    before = before_signature
    page = 0
    while True:
        page += 1
        if page > 100:
            raise RuntimeError("SIGNATURE_PAGINATION_SAFETY_CAP")
        result = rpc.call("getSignaturesForAddress", [TOKEN_MINT_AUTHORITY, {
            "before": before,
            "limit": 1000,
            "commitment": "finalized",
        }], f"getSignaturesForAddress_p{page:03d}")
        if not isinstance(result, list):
            raise RuntimeError("BAD_SIGNATURE_PAGE")
        if not result:
            break
        stop = False
        for r in result:
            if not isinstance(r, dict) or not isinstance(r.get("signature"), str):
                raise RuntimeError("BAD_SIGNATURE_ROW")
            bt = r.get("blockTime")
            if not isinstance(bt, int):
                raise RuntimeError("SIGNATURE_MISSING_BLOCKTIME")
            if bt < start_ts:
                stop = True
                continue
            if start_ts <= bt < end_ts and r.get("err") is None:
                rows.append({
                    "signature": r["signature"],
                    "slot": int(r["slot"]),
                    "block_time": bt,
                    "confirmation_status": r.get("confirmationStatus"),
                })
        before = str(result[-1]["signature"])
        if stop:
            break
    dedup = {r["signature"]: r for r in rows}
    return sorted(dedup.values(), key=lambda x: (x["slot"], x["signature"]))


def instruction_stream(result: Dict[str, Any]) -> Iterable[Tuple[str, int, Dict[str, Any]]]:
    msg = ((result.get("transaction") or {}).get("message") or {})
    for i, ix in enumerate(msg.get("instructions") or []):
        if isinstance(ix, dict):
            yield "outer", i, ix
    for group in ((result.get("meta") or {}).get("innerInstructions") or []):
        parent = group.get("index")
        for j, ix in enumerate(group.get("instructions") or []):
            if isinstance(ix, dict):
                yield f"inner:{parent}", j, ix


def resolve_program_id(ix: Dict[str, Any], keys: Sequence[str]) -> Optional[str]:
    if isinstance(ix.get("programId"), str):
        return ix["programId"]
    if isinstance(ix.get("programId"), dict) and isinstance(ix["programId"].get("pubkey"), str):
        return ix["programId"]["pubkey"]
    idx = ix.get("programIdIndex")
    if isinstance(idx, int) and 0 <= idx < len(keys):
        return keys[idx]
    return None


def resolve_accounts(ix: Dict[str, Any], keys: Sequence[str]) -> List[str]:
    out = []
    for a in ix.get("accounts") or []:
        if isinstance(a, int):
            if not (0 <= a < len(keys)):
                raise RuntimeError("INSTRUCTION_ACCOUNT_INDEX_OOB")
            out.append(keys[a])
        elif isinstance(a, str):
            out.append(a)
        elif isinstance(a, dict) and isinstance(a.get("pubkey"), str):
            out.append(a["pubkey"])
        else:
            raise RuntimeError("INSTRUCTION_ACCOUNT_SHAPE_FAILURE")
    return out


def decode_creates_from_transaction(sig_row: Dict[str, Any], result: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = result.get("meta") or {}
    if meta.get("err") is not None:
        return []
    keys = static_account_keys(result)
    out = []
    for scope, ix_index, ix in instruction_stream(result):
        if resolve_program_id(ix, keys) != PUMP_PROGRAM:
            continue
        data = ix.get("data")
        if not isinstance(data, str):
            continue
        try:
            raw = b58decode(data)
        except Exception:
            continue
        if not raw.startswith(CREATE_DISC):
            continue
        # Any CREATE-shape decode error is fatal: primary rows must have zero schema ambiguity.
        dec = decode_create_data(data)
        accounts = resolve_accounts(ix, keys)
        if len(accounts) < 1:
            raise RuntimeError(f"CREATE_WITHOUT_MINT signature={sig_row['signature']}")
        mint = accounts[0]
        bt = result.get("blockTime")
        slot = result.get("slot")
        if not isinstance(bt, int) or not isinstance(slot, int):
            raise RuntimeError("TRANSACTION_MISSING_SLOT_OR_TIME")
        row = {
            **dec,
            "mint": mint,
            "signature": sig_row["signature"],
            "slot": int(slot),
            "block_time": int(bt),
            "instruction_scope": scope,
            "instruction_index": int(ix_index),
            "fee_payer": keys[0] if keys else None,
        }
        canon = canonical_immutable_uri(dec["uri"])
        row["immutable_uri"] = canon
        row["immutable_uri_eligible"] = canon is not None
        row["identity_key"] = identity_key(dec["name"], dec["symbol"], canon) if canon else None
        out.append(row)
    return out


def fetch_transactions(rpc: Rpc, sig_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    batch_size = int(os.environ.get("MSEL_TX_BATCH_SIZE", "20"))
    if batch_size <= 0 or batch_size > 100:
        raise RuntimeError("INVALID_BATCH_SIZE")
    creates: List[Dict[str, Any]] = []
    missing = 0
    for i in range(0, len(sig_rows), batch_size):
        chunk = sig_rows[i:i+batch_size]
        calls = [("getTransaction", [r["signature"], {
            "encoding": "json",
            "maxSupportedTransactionVersion": 0,
            "commitment": "finalized",
        }]) for r in chunk]
        results = rpc.batch(calls, f"getTransaction_batch_{i//batch_size+1:04d}")
        for sr, result in zip(chunk, results):
            if not isinstance(result, dict):
                missing += 1
                continue
            creates.extend(decode_creates_from_transaction(sr, result))
        if (i // batch_size + 1) % 25 == 0:
            print(f"progress transaction_batches={i//batch_size+1} signatures={min(i+batch_size,len(sig_rows))}/{len(sig_rows)} creates={len(creates)}")
    return creates, missing


def build_features(creates: List[Dict[str, Any]], candidate_start: int, source_end: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # Same-slot predecessors are deliberately unavailable by frozen design.
    ordered = sorted(creates, key=lambda r: (int(r["slot"]), str(r["signature"]), str(r["instruction_scope"]), int(r["instruction_index"])))
    prior: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    candidates: List[Dict[str, Any]] = []
    for row in ordered:
        key = row.get("identity_key")
        bt = int(row["block_time"])
        if key:
            hist = [p for p in prior[key] if 0 < bt - int(p["block_time"]) <= LOOKBACK_SECONDS and int(p["slot"]) < int(row["slot"])]
        else:
            hist = []
        if candidate_start <= bt < source_end:
            x = dict(row)
            x["candidate"] = True
            x["same_creator_clone_6h"] = False
            x["prior_exact_immutable_identity_reuse_6h"] = False
            x["predecessor_mint"] = None
            x["predecessor_signature"] = None
            x["predecessor_creator"] = None
            x["predecessor_age_seconds"] = None
            if key and hist:
                same = [p for p in hist if p["origin_creator"] == row["origin_creator"]]
                cross = [p for p in hist if p["origin_creator"] != row["origin_creator"]]
                x["same_creator_clone_6h"] = bool(same)
                if cross:
                    p = max(cross, key=lambda q: (int(q["block_time"]), int(q["slot"]), str(q["signature"])))
                    x["prior_exact_immutable_identity_reuse_6h"] = True
                    x["predecessor_mint"] = p["mint"]
                    x["predecessor_signature"] = p["signature"]
                    x["predecessor_creator"] = p["origin_creator"]
                    x["predecessor_age_seconds"] = bt - int(p["block_time"])
            candidates.append(x)
        if key:
            # Keep only enough history for future rows; same-slot entries remain but are filtered above.
            prior[key] = [p for p in prior[key] if bt - int(p["block_time"]) <= LOOKBACK_SECONDS]
            prior[key].append(row)

    exposed = [r for r in candidates if r["prior_exact_immutable_identity_reuse_6h"]]
    immutable = [r for r in candidates if r["immutable_uri_eligible"]]
    clone = [r for r in candidates if r["same_creator_clone_6h"]]
    group_counts = Counter(str(r["identity_key"]) for r in exposed)
    creator_count = len({r["origin_creator"] for r in exposed})
    max_group = max(group_counts.values(), default=0)
    max_share = (max_group / len(exposed)) if exposed else None
    scheme_counts = Counter()
    for r in immutable:
        cu = str(r["immutable_uri"])
        scheme_counts["ipfs"] += int(cu.startswith("ipfs://"))
        scheme_counts["ar"] += int(cu.startswith("ar://"))
    summary = {
        "candidate_create_count": len(candidates),
        "immutable_uri_candidate_count": len(immutable),
        "immutable_uri_candidate_rate": (len(immutable)/len(candidates)) if candidates else None,
        "primary_cross_creator_exposed_count": len(exposed),
        "primary_cross_creator_exposed_rate_all": (len(exposed)/len(candidates)) if candidates else None,
        "primary_cross_creator_exposed_rate_immutable": (len(exposed)/len(immutable)) if immutable else None,
        "primary_unique_identity_groups": len(group_counts),
        "primary_unique_candidate_creators": creator_count,
        "largest_identity_group_count": max_group,
        "largest_identity_group_share": max_share,
        "same_creator_clone_candidate_count": len(clone),
        "uri_scheme_counts": dict(scheme_counts),
    }
    return candidates, summary


def source_gates(summary: Dict[str, Any], missing_tx: int, boundary_ok: bool, unique_rows_ok: bool) -> Dict[str, Any]:
    largest = summary["largest_identity_group_share"]
    gates = {
        "candidate_create_count_ge_2000": summary["candidate_create_count"] >= MIN_CANDIDATES,
        "immutable_uri_candidate_count_ge_500": summary["immutable_uri_candidate_count"] >= MIN_IMMUTABLE_CANDIDATES,
        "primary_cross_creator_exposed_count_ge_30": summary["primary_cross_creator_exposed_count"] >= MIN_EXPOSED,
        "primary_unique_identity_groups_ge_10": summary["primary_unique_identity_groups"] >= MIN_EXPOSED_IDENTITIES,
        "primary_unique_candidate_creators_ge_20": summary["primary_unique_candidate_creators"] >= MIN_EXPOSED_CREATORS,
        "largest_identity_group_share_le_0p50": largest is not None and largest <= MAX_LARGEST_IDENTITY_SHARE,
        "source_boundaries_proven": boundary_ok,
        "unique_create_rows": unique_rows_ok,
        "zero_missing_transaction_results": missing_tx == 0,
        "zero_primary_decode_ambiguity": True,
    }
    all_pass = all(gates.values())
    return {"gates": gates, "all_pass": all_pass, "classification": "SOURCE_PREVALENCE_PASS" if all_pass else "INSUFFICIENT_SAMPLE_OR_SOURCE_FAILURE"}


def main() -> int:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise RuntimeError(f"OUTPUT_DIR_NOT_EMPTY {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    w = frozen_window()
    print("MSEL-002 source/prevalence only; ECONOMIC OUTCOMES LOCKED")
    print(json.dumps(w, sort_keys=True))

    rpc = Rpc(rpc_url())
    start_slot, start_bt, start_prev_slot, start_prev_bt = find_first_confirmed_at_or_after(rpc, int(w["source_start"]))
    end_slot, end_bt, end_prev_slot, end_prev_bt = find_first_confirmed_at_or_after(rpc, int(w["source_end"]))
    boundary = {
        "source_start_target": int(w["source_start"]),
        "source_start_first_slot": start_slot,
        "source_start_first_time": start_bt,
        "source_start_prev_slot": start_prev_slot,
        "source_start_prev_time": start_prev_bt,
        "source_end_target": int(w["source_end"]),
        "source_end_first_slot": end_slot,
        "source_end_first_time": end_bt,
        "source_end_prev_slot": end_prev_slot,
        "source_end_prev_time": end_prev_bt,
    }
    boundary_ok = start_prev_bt < int(w["source_start"]) <= start_bt and end_prev_bt < int(w["source_end"]) <= end_bt
    if not boundary_ok:
        raise RuntimeError("BOUNDARY_PROOF_FAILURE")
    print(f"boundary PASS start_slot={start_slot} end_slot={end_slot}")

    anchor = find_authority_anchor_after(rpc, end_slot, int(w["source_end"]))
    print(f"end anchor signature={anchor['signature']} slot={anchor['slot']} time={anchor['block_time']}")
    sig_rows = collect_authority_signatures(rpc, str(anchor["signature"]), int(w["source_start"]), int(w["source_end"]))
    print(f"successful authority signatures in frozen 12h={len(sig_rows)}")
    if not sig_rows:
        raise RuntimeError("ZERO_AUTHORITY_SIGNATURES")

    creates, missing_tx = fetch_transactions(rpc, sig_rows)
    if missing_tx:
        # Fail closed: transaction-history coverage cannot be proven.
        raise RuntimeError(f"MISSING_TRANSACTION_RESULTS count={missing_tx}")
    if not creates:
        raise RuntimeError("ZERO_DECODED_CREATES")

    unique_keys = [(r["signature"], r["instruction_scope"], r["instruction_index"], r["mint"]) for r in creates]
    unique_rows_ok = len(unique_keys) == len(set(unique_keys)) and len({r["mint"] for r in creates}) == len(creates)
    if not unique_rows_ok:
        raise RuntimeError("CREATE_UNIQUENESS_FAILURE")

    candidates, summary = build_features(creates, int(w["candidate_start"]), int(w["source_end"]))
    gates = source_gates(summary, missing_tx, boundary_ok, unique_rows_ok)

    sig_sha = dump_jsonl_new(OUT_DIR / "authority_signatures_v01.jsonl", sig_rows)
    create_sha = dump_jsonl_new(OUT_DIR / "decoded_creates_v01.jsonl", sorted(creates, key=lambda r: (r["slot"], r["signature"], r["instruction_scope"], r["instruction_index"])))
    candidate_sha = dump_jsonl_new(OUT_DIR / "candidate_identity_features_v01.jsonl", candidates)
    summary_sha = dump_json_new(OUT_DIR / "source_prevalence_summary_v01.json", summary)
    gates_sha = dump_json_new(OUT_DIR / "source_prevalence_gates_v01.json", gates)
    receipt_sha = dump_json_new(OUT_DIR / "rpc_receipts_v01.json", rpc.receipts)
    boundary_sha = dump_json_new(OUT_DIR / "boundary_proof_v01.json", {"window": w, "boundary": boundary, "anchor": anchor})

    manifest = {
        "artifact": "MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_PREVALENCE_V01",
        "economic_outcomes_opened": False,
        "future_candidate_paths_opened": False,
        "pump_program": PUMP_PROGRAM,
        "token_mint_authority": TOKEN_MINT_AUTHORITY,
        "pinned_idl_commit": PINNED_IDL_COMMIT,
        "pinned_idl_blob_sha": PINNED_IDL_BLOB_SHA,
        "window": w,
        "authority_signature_count": len(sig_rows),
        "decoded_create_count": len(creates),
        "missing_transaction_results": missing_tx,
        "summary": summary,
        "gates": gates,
        "hashes": {
            "authority_signatures_v01.jsonl": sig_sha,
            "decoded_creates_v01.jsonl": create_sha,
            "candidate_identity_features_v01.jsonl": candidate_sha,
            "source_prevalence_summary_v01.json": summary_sha,
            "source_prevalence_gates_v01.json": gates_sha,
            "rpc_receipts_v01.json": receipt_sha,
            "boundary_proof_v01.json": boundary_sha,
        },
        "raw_rpc_file_count": len(list(RAW_DIR.glob("*.json"))),
    }
    man_sha = dump_json_new(OUT_DIR / "source_prevalence_manifest_v01.json", manifest)

    print("SOURCE/PREVALENCE COMPLETE")
    print(json.dumps(summary, sort_keys=True))
    print(json.dumps(gates, sort_keys=True))
    print(f"manifest_sha256={man_sha}")
    print("NO PRICE / RETURN / GRADUATION / MIGRATION / FUTURE OUTCOME OPENED")
    # Scientific fail is represented in the manifest, not as a technical process failure.
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
