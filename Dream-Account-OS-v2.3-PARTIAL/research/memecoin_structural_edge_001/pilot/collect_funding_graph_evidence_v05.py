#!/usr/bin/env python3
"""MSEL-001 point-in-time funding graph evidence collector V0.5.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

Purpose:
- take the V0.4 economic wallet universe plus cohort origin creators;
- for each wallet, anchor at its earliest target-cohort participation known point-in-time;
- query only signatures strictly BEFORE that anchor;
- inspect a bounded number of immediately-prior successful transactions;
- extract direct native-SOL System Program inbound transfers to the wallet;
- preserve exact RPC responses + SHA-256 receipts;
- emit evidence edges only. NO wallet merge/clustering is performed here.

Why evidence-only:
- a shared funder can be an exchange/service hub;
- absence of a direct funding transfer within the bounded lookback is NOT evidence of independence;
- service-hub flags and cluster rules must be frozen in a later stage before outcomes open.

No prices. No DEX quotes. No future token outcomes. No trading. No mutation.

Environment:
  HELIUS_API_KEY          required unless MSEL_RPC_URL supplied
  MSEL_RPC_URL            optional Solana archival RPC endpoint
  MSEL_FUNDING_LOOKBACK   max prior signatures per wallet, default 12
  MSEL_RPS_DELAY          delay between RPC requests, default 0.12 seconds
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import struct
import time
import urllib.request
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from collect_25_creates import (
    b58decode,
    get_all_keys,
    get_ix_data,
    outer_and_inner_instructions,
    resolve_ix_accounts,
    resolve_program_id,
    transaction_signature,
)

SYSTEM_PROGRAM = "11111111111111111111111111111111"
EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V03_MANIFEST_SHA256 = "107f6a8c7eff6d98db6af6916e531b0f43a001704898440904452956e9294cea"
EXPECTED_V04_MANIFEST_SHA256 = "ecbc8fa22b885f87984b5cbc4ca39908558a487fa4e36e916574b85f3a2e76c3"
VERSION = "MSEL_FUNDING_GRAPH_EVIDENCE_V05"
ECON_CLASSES = {"ECONOMIC_BUY_CANDIDATE", "ECONOMIC_SELL_CANDIDATE"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(path: pathlib.Path, obj: Any) -> str:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return sha256_bytes(path.read_bytes())


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing HELIUS_API_KEY (or MSEL_RPC_URL)")
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


class Rpc:
    def __init__(self, url: str, raw_dir: pathlib.Path, delay: float):
        self.url = url
        self.raw_dir = raw_dir
        self.delay = delay
        self.request_id = 0
        self.receipts: List[Dict[str, Any]] = []
        raw_dir.mkdir(parents=True, exist_ok=True)

    def call(self, method: str, params: List[Any], tag: str) -> Any:
        self.request_id += 1
        rid = self.request_id
        payload = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(self.url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        safe_tag = "".join(c if c.isalnum() or c in "-_" else "_" for c in tag)[:80]
        raw_file = f"rpc_{rid:06d}_{method}_{safe_tag}.json"
        (self.raw_dir / raw_file).write_bytes(raw)
        digest = sha256_bytes(raw)
        obj = json.loads(raw)
        if obj.get("error") is not None:
            raise RuntimeError(f"RPC_ERROR method={method} tag={tag} error={obj['error']}")
        self.receipts.append({
            "request_id": rid,
            "method": method,
            "tag": tag,
            "raw_file": raw_file,
            "response_sha256": digest,
        })
        if self.delay > 0:
            time.sleep(self.delay)
        return obj.get("result")


def parse_system_transfer(ix: Dict[str, Any], keys: Sequence[str]) -> Optional[Dict[str, Any]]:
    if resolve_program_id(ix, keys) != SYSTEM_PROGRAM:
        return None
    data = get_ix_data(ix)
    if not data:
        return None
    try:
        raw = b58decode(data)
    except Exception:
        return None
    if len(raw) < 4:
        return None
    variant = struct.unpack_from("<I", raw, 0)[0]
    accounts = resolve_ix_accounts(ix, keys)
    if variant == 2:  # SystemInstruction::Transfer { lamports }
        if len(raw) < 12 or len(accounts) < 2:
            return None
        lamports = struct.unpack_from("<Q", raw, 4)[0]
        return {
            "instruction_class": "SYSTEM_TRANSFER",
            "source": accounts[0],
            "destination": accounts[1],
            "lamports": int(lamports),
        }
    if variant == 11:  # TransferWithSeed; lamports is first field after enum tag.
        if len(raw) < 12 or len(accounts) < 3:
            return None
        lamports = struct.unpack_from("<Q", raw, 4)[0]
        return {
            "instruction_class": "SYSTEM_TRANSFER_WITH_SEED",
            "source": accounts[0],
            "base": accounts[1],
            "destination": accounts[2],
            "lamports": int(lamports),
        }
    return None


def direct_inbound_transfers(item: Dict[str, Any], wallet: str) -> List[Dict[str, Any]]:
    keys = get_all_keys(item)
    if not keys:
        return []
    out: List[Dict[str, Any]] = []
    for scope, ix_idx, ix in outer_and_inner_instructions(item):
        parsed = parse_system_transfer(ix, keys)
        if not parsed:
            continue
        if parsed.get("destination") != wallet:
            continue
        if parsed.get("source") == wallet:
            continue
        if int(parsed.get("lamports", 0)) <= 0:
            continue
        row = dict(parsed)
        row.update({"scope": scope, "instruction_index": ix_idx})
        out.append(row)
    return out


def anchor_universe(
    cohort: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    anchors: Dict[str, Dict[str, Any]] = {}

    # Economic users: earliest economic target-cohort event is a valid wallet-involved anchor.
    econ = [r for r in events if r.get("semantic_class") in ECON_CLASSES]
    econ.sort(key=lambda r: (int(r["block_time"]), int(r["slot"]), int(r["transaction_index"]), int(r.get("log_index", 0))))
    for r in econ:
        w = r["user"]
        candidate = {
            "wallet": w,
            "anchor_signature": r["signature"],
            "anchor_block_time": int(r["block_time"]),
            "anchor_slot": int(r["slot"]),
            "anchor_source": "EARLIEST_ECONOMIC_TRADE",
            "anchor_mint": r["mint"],
            "is_origin_creator_any_target": False,
        }
        if w not in anchors:
            anchors[w] = candidate

    # Origin creators: use CREATE only when creator is the tx_user, so the anchor signature
    # is guaranteed to be in that wallet's address history. Earlier anchor wins.
    creators = {r["origin_creator"] for r in cohort}
    for r in cohort:
        creator = r["origin_creator"]
        if creator != r.get("tx_user"):
            continue
        candidate = {
            "wallet": creator,
            "anchor_signature": r["signature"],
            "anchor_block_time": int(r["block_time"]),
            "anchor_slot": int(r["slot"]),
            "anchor_source": "TARGET_CREATE_TX",
            "anchor_mint": r["mint"],
            "is_origin_creator_any_target": True,
        }
        prev = anchors.get(creator)
        if prev is None or (candidate["anchor_block_time"], candidate["anchor_slot"]) < (prev["anchor_block_time"], prev["anchor_slot"]):
            anchors[creator] = candidate

    for w, a in anchors.items():
        if w in creators:
            a["is_origin_creator_any_target"] = True
    return anchors


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    out_dir = here / "data" / "msel001_funding_v05"
    raw_dir = out_dir / "raw_rpc"
    out_dir.mkdir(parents=True, exist_ok=True)

    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    events_path = d / "trade_events_economic_v03.jsonl"
    v03_manifest_path = d / "economic_manifest_v03.json"
    v04_manifest_path = d / "precluster_wallet_manifest_v04.json"
    v04_wallet_path = d / "wallet_activity_precluster_v04.jsonl"

    required = [cohort_path, events_path, v03_manifest_path, v04_manifest_path, v04_wallet_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")
    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha256_bytes(v03_manifest_path.read_bytes()) != EXPECTED_V03_MANIFEST_SHA256:
        raise RuntimeError("V03_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v04_manifest_path.read_bytes()) != EXPECTED_V04_MANIFEST_SHA256:
        raise RuntimeError("V04_MANIFEST_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    events = load_jsonl(events_path)
    v04_wallet_rows = load_jsonl(v04_wallet_path)
    v04_manifest = load_json(v04_manifest_path)
    if v04_manifest.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    expected_wallet_sha = v04_manifest.get("wallet_activity_precluster_v04_sha256")
    if expected_wallet_sha and expected_wallet_sha != sha256_bytes(v04_wallet_path.read_bytes()):
        raise RuntimeError("V04_WALLET_FILE_HASH_MISMATCH")

    anchors = anchor_universe(cohort, events)
    v04_wallets = {r["wallet"] for r in v04_wallet_rows}
    missing_v04 = sorted(v04_wallets - set(anchors))
    if missing_v04:
        raise RuntimeError(f"ANCHOR_COVERAGE_FAILURE missing_v04={missing_v04[:10]} count={len(missing_v04)}")

    lookback = int(os.environ.get("MSEL_FUNDING_LOOKBACK", "12"))
    if lookback < 1 or lookback > 50:
        raise RuntimeError("MSEL_FUNDING_LOOKBACK must be between 1 and 50")
    delay = float(os.environ.get("MSEL_RPS_DELAY", "0.12"))
    rpc = Rpc(rpc_url(), raw_dir, delay)

    funding_edges: List[Dict[str, Any]] = []
    statuses: List[Dict[str, Any]] = []

    for idx, wallet in enumerate(sorted(anchors), start=1):
        a = anchors[wallet]
        sigs = rpc.call(
            "getSignaturesForAddress",
            [wallet, {"before": a["anchor_signature"], "limit": lookback, "commitment": "finalized"}],
            f"wallet_{idx:04d}_signatures",
        ) or []

        inspected = 0
        chosen: Optional[Dict[str, Any]] = None
        all_direct: List[Dict[str, Any]] = []

        for sidx, s in enumerate(sigs, start=1):
            if not isinstance(s, dict):
                continue
            if s.get("err") is not None:
                continue
            sig = s.get("signature")
            if not sig:
                continue
            bt = s.get("blockTime")
            if bt is not None and int(bt) > int(a["anchor_block_time"]):
                raise RuntimeError(f"PIT_TIME_ORDER_FAILURE wallet={wallet} prior_sig={sig}")
            tx = rpc.call(
                "getTransaction",
                [sig, {"encoding": "json", "commitment": "finalized", "maxSupportedTransactionVersion": 0}],
                f"wallet_{idx:04d}_tx_{sidx:02d}",
            )
            inspected += 1
            if not isinstance(tx, dict):
                continue
            meta = tx.get("meta") or {}
            if meta.get("err") is not None:
                continue
            transfers = direct_inbound_transfers(tx, wallet)
            if not transfers:
                continue
            tx_sig = transaction_signature(tx) or sig
            tx_block_time = tx.get("blockTime")
            tx_slot = tx.get("slot")
            for tr in transfers:
                edge = {
                    "wallet": wallet,
                    "funder": tr["source"],
                    "lamports": int(tr["lamports"]),
                    "funding_signature": tx_sig,
                    "funding_block_time": int(tx_block_time) if tx_block_time is not None else None,
                    "funding_slot": int(tx_slot) if tx_slot is not None else None,
                    "instruction_class": tr["instruction_class"],
                    "scope": tr["scope"],
                    "instruction_index": tr["instruction_index"],
                    "anchor_signature": a["anchor_signature"],
                    "anchor_block_time": a["anchor_block_time"],
                    "anchor_slot": a["anchor_slot"],
                    "anchor_source": a["anchor_source"],
                    "anchor_mint": a["anchor_mint"],
                    "is_origin_creator_any_target": a["is_origin_creator_any_target"],
                    "evidence_class": "DIRECT_NATIVE_SOL_INBOUND_BEFORE_ANCHOR",
                }
                all_direct.append(edge)
            # Nearest prior tx with direct inbound evidence is enough for the primary funding edge.
            if all_direct:
                # If several inbound transfers exist in the same nearest tx, choose largest as primary,
                # but preserve every edge in funding_edges.
                nearest_tx_edges = [e for e in all_direct if e["funding_signature"] == tx_sig]
                chosen = max(nearest_tx_edges, key=lambda e: int(e["lamports"]))
                break

        funding_edges.extend(all_direct)
        statuses.append({
            **a,
            "prior_signature_candidates_returned": len(sigs),
            "prior_successful_transactions_inspected": inspected,
            "direct_inbound_edge_count": len(all_direct),
            "primary_funder": chosen["funder"] if chosen else None,
            "primary_funding_lamports": chosen["lamports"] if chosen else None,
            "primary_funding_signature": chosen["funding_signature"] if chosen else None,
            "funding_status": "DIRECT_FUNDING_EVIDENCE_FOUND" if chosen else "UNRESOLVED_WITHIN_BOUNDED_LOOKBACK",
            "absence_means_independent": False,
        })

    # Degree counts are descriptive evidence only. They are NOT auto-merge rules.
    primary_degree = Counter(r["primary_funder"] for r in statuses if r.get("primary_funder"))
    for r in statuses:
        f = r.get("primary_funder")
        r["primary_funder_target_wallet_degree"] = int(primary_degree.get(f, 0)) if f else None
        r["shared_primary_funder_observed"] = bool(f and primary_degree.get(f, 0) >= 2)
        r["service_hub_status"] = "UNCLASSIFIED"
        r["eligible_for_hard_cluster_merge"] = False

    edge_path = out_dir / "funding_edges_v05.jsonl"
    status_path = out_dir / "wallet_funding_status_v05.jsonl"
    receipts_path = out_dir / "rpc_receipts_v05.json"
    edges_sha = write_jsonl(edge_path, sorted(funding_edges, key=lambda r: (r["wallet"], -(r["funding_block_time"] or 0), r["funding_signature"], str(r["instruction_index"]))))
    status_sha = write_jsonl(status_path, sorted(statuses, key=lambda r: r["wallet"]))
    receipts_sha = write_json(receipts_path, rpc.receipts)

    resolved = sum(1 for r in statuses if r["funding_status"] == "DIRECT_FUNDING_EVIDENCE_FOUND")
    unresolved = len(statuses) - resolved
    shared_wallets = sum(1 for r in statuses if r.get("shared_primary_funder_observed"))
    unique_primary_funders = len(primary_degree)
    max_degree = max(primary_degree.values()) if primary_degree else 0

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_cohort_sha256": EXPECTED_COHORT_SHA256,
        "source_v03_manifest_sha256": EXPECTED_V03_MANIFEST_SHA256,
        "source_v04_manifest_sha256": EXPECTED_V04_MANIFEST_SHA256,
        "funding_lookback_prior_signatures": lookback,
        "wallet_universe_size": len(statuses),
        "direct_funding_evidence_found_wallets": resolved,
        "unresolved_within_bounded_lookback_wallets": unresolved,
        "unique_primary_funders": unique_primary_funders,
        "wallets_with_shared_primary_funder_observed": shared_wallets,
        "max_observed_primary_funder_degree": max_degree,
        "rpc_request_count": rpc.request_id,
        "funding_edges_v05_sha256": edges_sha,
        "wallet_funding_status_v05_sha256": status_sha,
        "rpc_receipts_v05_sha256": receipts_sha,
        "shared_funder_is_not_automatic_cluster": True,
        "service_hub_flags_applied": False,
        "same_funder_clustering_applied": False,
        "economic_clustering_applied": False,
        "final_organicity_ratio_available": False,
        "outcomes_opened": False,
    }
    manifest_path = out_dir / "funding_manifest_v05.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: point-in-time funding graph evidence V05 complete")
    print(f"wallet universe: {len(statuses)}")
    print(f"direct funding evidence found: {resolved}")
    print(f"unresolved within lookback: {unresolved}")
    print(f"unique primary funders: {unique_primary_funders}")
    print(f"wallets sharing a primary funder: {shared_wallets}")
    print(f"max observed primary-funder degree: {max_degree}")
    print(f"rpc requests: {rpc.request_id}")
    print(f"manifest sha256: {manifest_sha}")
    print("NO HARD CLUSTER MERGES APPLIED")
    print("FINAL ORGANICITY REMAINS BLOCKED PENDING HUB/CLUSTER POLICY FREEZE")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
