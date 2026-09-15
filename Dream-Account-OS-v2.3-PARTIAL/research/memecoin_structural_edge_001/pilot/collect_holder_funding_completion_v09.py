#!/usr/bin/env python3
"""MSEL-001 holder funding completeness collector V0.9.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

Implements HOLDER_FUNDING_COMPLETENESS_ESCALATION_FREEZE_V01.md.

Frozen behavior:
- holder universe comes from V0.8 holder snapshots;
- carry V0.5 primary funding evidence only when its chosen edge is a verified
  standard System Program Transfer (enum variant 2 / SYSTEM_TRANSFER);
- target all holder owners that are absent from V0.5, unresolved in V0.5, or
  whose V0.5 primary edge is not verified standard-transfer evidence;
- inspect at most 50 immediately-prior signatures per targeted wallet;
- accept only direct inbound native SOL System Program Transfer variant 2;
- no TransferWithSeed parsing in this stage;
- no hard clustering; no outcome access; no trading.

For a holder-only wallet absent from V0.5, the earliest positive target-token
balance-change transaction is used as an anchor candidate. It is accepted as an
address-history anchor only if getTransaction shows the holder wallet in the
transaction account keys. Otherwise the wallet remains unresolved and no later
history is browsed to manufacture an anchor.
"""
from __future__ import annotations

import json
import pathlib
import struct
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import collect_funding_graph_evidence_v05 as v05
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
EXPECTED_V05_MANIFEST_SHA256 = "0c787209d6a58ebd9cf190833dbcce7d807d26b144ee868c96a2cdff8323b580"
EXPECTED_V08_MANIFEST_SHA256 = "a04f8efd1a0a220f37592a45affdc16a725e3f4530e5a1bbbbe257ad318c6df8"
EXPECTED_V02_SOURCE_MANIFEST_SHA256 = "11c296c98baa5a7005db5d0e72dd0151668799dafb007a02e68985841c9b3e48"
LOOKBACK = 50
VERSION = "MSEL_HOLDER_FUNDING_COMPLETION_V09"


def sha256_bytes(b: bytes) -> str:
    return v05.sha256_bytes(b)


def load_json(path: pathlib.Path) -> Any:
    return v05.load_json(path)


def load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    return v05.load_jsonl(path)


def write_json(path: pathlib.Path, obj: Any) -> str:
    return v05.write_json(path, obj)


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    return v05.write_jsonl(path, rows)


def parse_standard_system_transfer(ix: Dict[str, Any], keys: Sequence[str]) -> Optional[Dict[str, Any]]:
    """Accept only SystemInstruction::Transfer enum variant 2."""
    if resolve_program_id(ix, keys) != SYSTEM_PROGRAM:
        return None
    data = get_ix_data(ix)
    if not data:
        return None
    try:
        raw = b58decode(data)
    except Exception:
        return None
    if len(raw) < 12:
        return None
    variant = struct.unpack_from("<I", raw, 0)[0]
    if variant != 2:
        return None
    accounts = resolve_ix_accounts(ix, keys)
    if len(accounts) < 2:
        return None
    lamports = struct.unpack_from("<Q", raw, 4)[0]
    return {
        "instruction_class": "SYSTEM_TRANSFER",
        "source": accounts[0],
        "destination": accounts[1],
        "lamports": int(lamports),
    }


def direct_standard_inbound(item: Dict[str, Any], wallet: str) -> List[Dict[str, Any]]:
    keys = get_all_keys(item)
    if not keys:
        return []
    out: List[Dict[str, Any]] = []
    for scope, ix_idx, ix in outer_and_inner_instructions(item):
        parsed = parse_standard_system_transfer(ix, keys)
        if not parsed:
            continue
        if parsed["destination"] != wallet:
            continue
        if parsed["source"] == wallet:
            continue
        if int(parsed["lamports"]) <= 0:
            continue
        row = dict(parsed)
        row.update({"scope": scope, "instruction_index": ix_idx})
        out.append(row)
    return out


def primary_v05_edge_by_wallet(statuses: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
    by_wallet: Dict[str, List[Dict[str, Any]]] = {}
    for e in edges:
        by_wallet.setdefault(str(e["wallet"]), []).append(e)
    out: Dict[str, Optional[Dict[str, Any]]] = {}
    for s in statuses:
        wallet = str(s["wallet"])
        if s.get("funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND":
            out[wallet] = None
            continue
        sig = s.get("primary_funding_signature")
        funder = s.get("primary_funder")
        lamports = s.get("primary_funding_lamports")
        matches = [
            e for e in by_wallet.get(wallet, [])
            if e.get("funding_signature") == sig
            and e.get("funder") == funder
            and int(e.get("lamports", -1)) == int(lamports)
        ]
        out[wallet] = matches[0] if len(matches) == 1 else None
    return out


def earliest_absent_holder_anchor(
    wallet: str,
    changes: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    candidates = [
        r for r in changes
        if str(r.get("owner") or "") == wallet and int(r.get("post_amount_raw") or 0) > 0
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda r: (
        int(r["block_time"]), int(r["slot"]), int(r["transaction_index"]), str(r["signature"]), str(r["token_account"])
    ))
    r = candidates[0]
    return {
        "wallet": wallet,
        "anchor_signature": str(r["signature"]),
        "anchor_block_time": int(r["block_time"]),
        "anchor_slot": int(r["slot"]),
        "anchor_source": "FIRST_POSITIVE_TARGET_TOKEN_BALANCE_CHANGE",
        "anchor_mint": str(r["mint"]),
        "is_origin_creator_any_target": False,
    }


def scan_before_anchor(
    rpc: v05.Rpc,
    wallet: str,
    anchor: Dict[str, Any],
    tag_prefix: str,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    sigs = rpc.call(
        "getSignaturesForAddress",
        [wallet, {"before": anchor["anchor_signature"], "limit": LOOKBACK, "commitment": "finalized"}],
        f"{tag_prefix}_signatures",
    ) or []

    inspected = 0
    all_direct: List[Dict[str, Any]] = []
    chosen: Optional[Dict[str, Any]] = None

    for sidx, s in enumerate(sigs, start=1):
        if not isinstance(s, dict) or s.get("err") is not None:
            continue
        sig = s.get("signature")
        if not sig:
            continue
        bt = s.get("blockTime")
        if bt is not None and int(bt) > int(anchor["anchor_block_time"]):
            raise RuntimeError(f"PIT_TIME_ORDER_FAILURE wallet={wallet} prior_sig={sig}")
        tx = rpc.call(
            "getTransaction",
            [sig, {"encoding": "json", "commitment": "finalized", "maxSupportedTransactionVersion": 0}],
            f"{tag_prefix}_tx_{sidx:02d}",
        )
        inspected += 1
        if not isinstance(tx, dict):
            continue
        meta = tx.get("meta") or {}
        if meta.get("err") is not None:
            continue
        transfers = direct_standard_inbound(tx, wallet)
        if not transfers:
            continue
        tx_sig = transaction_signature(tx) or sig
        tx_block_time = tx.get("blockTime")
        tx_slot = tx.get("slot")
        nearest_tx_edges: List[Dict[str, Any]] = []
        for tr in transfers:
            edge = {
                "wallet": wallet,
                "funder": tr["source"],
                "lamports": int(tr["lamports"]),
                "funding_signature": tx_sig,
                "funding_block_time": int(tx_block_time) if tx_block_time is not None else None,
                "funding_slot": int(tx_slot) if tx_slot is not None else None,
                "instruction_class": "SYSTEM_TRANSFER",
                "scope": tr["scope"],
                "instruction_index": tr["instruction_index"],
                "anchor_signature": anchor["anchor_signature"],
                "anchor_block_time": anchor["anchor_block_time"],
                "anchor_slot": anchor["anchor_slot"],
                "anchor_source": anchor["anchor_source"],
                "anchor_mint": anchor.get("anchor_mint"),
                "is_origin_creator_any_target": bool(anchor.get("is_origin_creator_any_target", False)),
                "evidence_class": "DIRECT_NATIVE_SOL_STANDARD_TRANSFER_BEFORE_ANCHOR",
                "source_stage": VERSION,
            }
            all_direct.append(edge)
            nearest_tx_edges.append(edge)
        if nearest_tx_edges:
            chosen = max(nearest_tx_edges, key=lambda e: int(e["lamports"]))
            break

    return chosen, all_direct, inspected, len(sigs)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    d5 = here / "data" / "msel001_funding_v05"
    out_dir = here / "data" / "msel001_holder_funding_v09"
    raw_dir = out_dir / "raw_rpc"
    out_dir.mkdir(parents=True, exist_ok=True)

    v05_manifest_path = d5 / "funding_manifest_v05.json"
    v05_status_path = d5 / "wallet_funding_status_v05.jsonl"
    v05_edges_path = d5 / "funding_edges_v05.jsonl"
    v08_manifest_path = d5 / "holder_funding_coverage_manifest_v08.json"
    holder_rows_path = d5 / "holder_snapshot_rows_v08.jsonl"
    source_manifest_path = d / "source_manifest.json"
    changes_path = d / "token_balance_changes.jsonl"

    required = [
        v05_manifest_path, v05_status_path, v05_edges_path,
        v08_manifest_path, holder_rows_path, source_manifest_path, changes_path,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")

    if sha256_bytes(v05_manifest_path.read_bytes()) != EXPECTED_V05_MANIFEST_SHA256:
        raise RuntimeError("V05_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v08_manifest_path.read_bytes()) != EXPECTED_V08_MANIFEST_SHA256:
        raise RuntimeError("V08_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(source_manifest_path.read_bytes()) != EXPECTED_V02_SOURCE_MANIFEST_SHA256:
        raise RuntimeError("V02_SOURCE_MANIFEST_HASH_MISMATCH")

    m05 = load_json(v05_manifest_path)
    m08 = load_json(v08_manifest_path)
    m02 = load_json(source_manifest_path)
    statuses05 = load_jsonl(v05_status_path)
    edges05 = load_jsonl(v05_edges_path)
    holder_rows = load_jsonl(holder_rows_path)
    changes = load_jsonl(changes_path)

    if m05.get("outcomes_opened") is not False or m08.get("outcomes_opened") is not False or m02.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    if m05.get("wallet_funding_status_v05_sha256") != sha256_bytes(v05_status_path.read_bytes()):
        raise RuntimeError("V05_STATUS_HASH_MISMATCH")
    if m05.get("funding_edges_v05_sha256") != sha256_bytes(v05_edges_path.read_bytes()):
        raise RuntimeError("V05_EDGES_HASH_MISMATCH")
    if m08.get("holder_snapshot_rows_v08_sha256") != sha256_bytes(holder_rows_path.read_bytes()):
        raise RuntimeError("V08_HOLDER_ROWS_HASH_MISMATCH")
    if m02.get("token_balance_changes_sha256") != sha256_bytes(changes_path.read_bytes()):
        raise RuntimeError("TOKEN_BALANCE_CHANGES_HASH_MISMATCH")

    holder_owners = sorted({str(r["holder_owner"]) for r in holder_rows})
    status05_by_wallet = {str(r["wallet"]): r for r in statuses05}
    if len(status05_by_wallet) != len(statuses05):
        raise RuntimeError("DUPLICATE_V05_STATUS")
    primary05 = primary_v05_edge_by_wallet(statuses05, edges05)

    final_status: List[Dict[str, Any]] = []
    final_edges: List[Dict[str, Any]] = []
    targets: List[Tuple[str, Dict[str, Any], str]] = []
    carried = 0
    invalidated_nonstandard = 0
    absent_anchor_candidates = 0
    absent_anchor_not_indexed = 0
    absent_anchor_missing = 0

    # First decide carry-vs-target without RPC.
    for wallet in holder_owners:
        s05 = status05_by_wallet.get(wallet)
        p05 = primary05.get(wallet) if s05 else None
        if s05 and s05.get("funding_status") == "DIRECT_FUNDING_EVIDENCE_FOUND" and p05 and p05.get("instruction_class") == "SYSTEM_TRANSFER":
            carried += 1
            final_edges.append({**p05, "source_stage": "V05_VERIFIED_STANDARD_TRANSFER_CARRY"})
            final_status.append({
                **s05,
                "holder_universe_member": True,
                "completion_stage": VERSION,
                "completion_action": "CARRIED_VERIFIED_V05_STANDARD_TRANSFER",
                "final_primary_funder": s05.get("primary_funder"),
                "final_primary_funding_lamports": s05.get("primary_funding_lamports"),
                "final_primary_funding_signature": s05.get("primary_funding_signature"),
                "final_funding_status": "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER",
                "lookback_ceiling": LOOKBACK,
                "absence_means_independent": False,
                "outcomes_opened": False,
            })
            continue

        if s05:
            anchor = {
                "wallet": wallet,
                "anchor_signature": s05["anchor_signature"],
                "anchor_block_time": int(s05["anchor_block_time"]),
                "anchor_slot": int(s05["anchor_slot"]),
                "anchor_source": s05["anchor_source"],
                "anchor_mint": s05.get("anchor_mint"),
                "is_origin_creator_any_target": bool(s05.get("is_origin_creator_any_target", False)),
            }
            reason = "V05_UNRESOLVED_ESCALATION"
            if s05.get("funding_status") == "DIRECT_FUNDING_EVIDENCE_FOUND":
                reason = "V05_PRIMARY_EDGE_NOT_VERIFIED_STANDARD_TRANSFER"
                invalidated_nonstandard += 1
            targets.append((wallet, anchor, reason))
        else:
            anchor = earliest_absent_holder_anchor(wallet, changes)
            if anchor is None:
                absent_anchor_missing += 1
                final_status.append({
                    "wallet": wallet,
                    "holder_universe_member": True,
                    "completion_stage": VERSION,
                    "completion_action": "ABSENT_V05_NO_ANCHOR_CANDIDATE",
                    "final_primary_funder": None,
                    "final_primary_funding_lamports": None,
                    "final_primary_funding_signature": None,
                    "final_funding_status": "UNRESOLVED_NO_POINT_IN_TIME_ADDRESS_ANCHOR",
                    "lookback_ceiling": LOOKBACK,
                    "absence_means_independent": False,
                    "outcomes_opened": False,
                })
            else:
                absent_anchor_candidates += 1
                targets.append((wallet, anchor, "HOLDER_ONLY_ABSENT_V05"))

    rpc = v05.Rpc(v05.rpc_url(), raw_dir, float(__import__("os").environ.get("MSEL_RPS_DELAY", "0.12")))
    newly_resolved = 0
    unresolved_after = 0

    for idx, (wallet, anchor, reason) in enumerate(targets, start=1):
        # Holder-only absent V05 anchor must be address-indexed. Check without
        # browsing later wallet history.
        if reason == "HOLDER_ONLY_ABSENT_V05":
            anchor_tx = rpc.call(
                "getTransaction",
                [anchor["anchor_signature"], {"encoding": "json", "commitment": "finalized", "maxSupportedTransactionVersion": 0}],
                f"target_{idx:04d}_anchor_tx",
            )
            if not isinstance(anchor_tx, dict) or wallet not in set(get_all_keys(anchor_tx)):
                absent_anchor_not_indexed += 1
                unresolved_after += 1
                final_status.append({
                    **anchor,
                    "holder_universe_member": True,
                    "completion_stage": VERSION,
                    "completion_action": "HOLDER_ONLY_ANCHOR_NOT_ADDRESS_INDEXED",
                    "completion_reason": reason,
                    "prior_signature_candidates_returned": 0,
                    "prior_successful_transactions_inspected": 0,
                    "final_primary_funder": None,
                    "final_primary_funding_lamports": None,
                    "final_primary_funding_signature": None,
                    "final_funding_status": "UNRESOLVED_ANCHOR_NOT_ADDRESS_INDEXED",
                    "lookback_ceiling": LOOKBACK,
                    "absence_means_independent": False,
                    "outcomes_opened": False,
                })
                continue

        chosen, edges, inspected, returned = scan_before_anchor(
            rpc, wallet, anchor, f"target_{idx:04d}"
        )
        final_edges.extend(edges)
        if chosen:
            newly_resolved += 1
            final_status.append({
                **anchor,
                "holder_universe_member": True,
                "completion_stage": VERSION,
                "completion_action": "TARGETED_STANDARD_TRANSFER_LOOKBACK_50",
                "completion_reason": reason,
                "prior_signature_candidates_returned": returned,
                "prior_successful_transactions_inspected": inspected,
                "final_primary_funder": chosen["funder"],
                "final_primary_funding_lamports": chosen["lamports"],
                "final_primary_funding_signature": chosen["funding_signature"],
                "final_funding_status": "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER",
                "lookback_ceiling": LOOKBACK,
                "absence_means_independent": False,
                "outcomes_opened": False,
            })
        else:
            unresolved_after += 1
            final_status.append({
                **anchor,
                "holder_universe_member": True,
                "completion_stage": VERSION,
                "completion_action": "TARGETED_STANDARD_TRANSFER_LOOKBACK_50",
                "completion_reason": reason,
                "prior_signature_candidates_returned": returned,
                "prior_successful_transactions_inspected": inspected,
                "final_primary_funder": None,
                "final_primary_funding_lamports": None,
                "final_primary_funding_signature": None,
                "final_funding_status": "UNRESOLVED_AFTER_FROZEN_50_SIGNATURE_LOOKBACK",
                "lookback_ceiling": LOOKBACK,
                "absence_means_independent": False,
                "outcomes_opened": False,
            })

    # Ensure one final status per holder owner.
    by_wallet: Dict[str, Dict[str, Any]] = {}
    for r in final_status:
        w = str(r["wallet"])
        if w in by_wallet:
            raise RuntimeError(f"DUPLICATE_FINAL_STATUS wallet={w}")
        by_wallet[w] = r
    if set(by_wallet) != set(holder_owners):
        raise RuntimeError(f"FINAL_STATUS_COVERAGE_FAILURE got={len(by_wallet)} expected={len(holder_owners)}")

    degree = Counter(r.get("final_primary_funder") for r in final_status if r.get("final_primary_funder"))
    for r in final_status:
        f = r.get("final_primary_funder")
        r["final_primary_funder_holder_degree"] = int(degree.get(f, 0)) if f else None
        r["shared_final_primary_funder_observed"] = bool(f and degree.get(f, 0) >= 2)
        r["eligible_for_hard_cluster_merge"] = False
        r["service_hub_status"] = "UNCLASSIFIED_PENDING_POLICY_APPLICATION"

    status_path = out_dir / "holder_funding_status_v09.jsonl"
    edge_path = out_dir / "holder_funding_edges_v09.jsonl"
    receipts_path = out_dir / "rpc_receipts_v09.json"
    status_sha = write_jsonl(status_path, sorted(final_status, key=lambda r: r["wallet"]))
    edge_sha = write_jsonl(edge_path, sorted(final_edges, key=lambda r: (r["wallet"], -(r.get("funding_block_time") or 0), r["funding_signature"], str(r.get("instruction_index")))))
    receipts_sha = write_json(receipts_path, rpc.receipts)

    resolved_total = sum(1 for r in final_status if r["final_funding_status"] == "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER")
    unresolved_total = len(final_status) - resolved_total
    shared_wallets = sum(1 for r in final_status if r.get("shared_final_primary_funder_observed"))
    max_degree = max(degree.values()) if degree else 0

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_v05_manifest_sha256": EXPECTED_V05_MANIFEST_SHA256,
        "source_v08_manifest_sha256": EXPECTED_V08_MANIFEST_SHA256,
        "source_v02_source_manifest_sha256": EXPECTED_V02_SOURCE_MANIFEST_SHA256,
        "holder_universe_size": len(holder_owners),
        "frozen_lookback_prior_signatures": LOOKBACK,
        "carried_verified_v05_standard_transfer_wallets": carried,
        "targeted_wallets": len(targets),
        "v05_nonstandard_or_unverifiable_primary_edges_retargeted": invalidated_nonstandard,
        "holder_only_absent_v05_anchor_candidates": absent_anchor_candidates,
        "holder_only_anchor_not_address_indexed": absent_anchor_not_indexed,
        "holder_only_anchor_missing": absent_anchor_missing,
        "newly_resolved_wallets": newly_resolved,
        "resolved_holder_wallets_final": resolved_total,
        "unresolved_holder_wallets_final": unresolved_total,
        "unique_final_primary_funders": len(degree),
        "holder_wallets_with_shared_primary_funder": shared_wallets,
        "max_final_primary_funder_holder_degree": max_degree,
        "rpc_request_count": rpc.request_id,
        "holder_funding_status_v09_sha256": status_sha,
        "holder_funding_edges_v09_sha256": edge_sha,
        "rpc_receipts_v09_sha256": receipts_sha,
        "accepted_instruction_class": "SYSTEM_TRANSFER_ONLY",
        "transfer_with_seed_accepted": False,
        "lookback_escalation_closed": True,
        "absence_means_independent": False,
        "hard_cluster_merges_applied": False,
        "final_hidden_concentration_available": False,
        "outcomes_opened": False,
    }
    manifest_path = out_dir / "holder_funding_manifest_v09.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: holder funding completeness V09 complete")
    print(f"holder universe: {len(holder_owners)}")
    print(f"carried verified V05 standard-transfer evidence: {carried}")
    print(f"targeted wallets: {len(targets)}")
    print(f"newly resolved under frozen lookback 50: {newly_resolved}")
    print(f"resolved holder wallets final: {resolved_total}")
    print(f"unresolved holder wallets final: {unresolved_total}")
    print(f"holder-only anchor not address-indexed: {absent_anchor_not_indexed}")
    print(f"unique final primary funders: {len(degree)}")
    print(f"wallets sharing final primary funder: {shared_wallets}")
    print(f"max final primary-funder holder degree: {max_degree}")
    print(f"rpc requests: {rpc.request_id}")
    print(f"manifest sha256: {manifest_sha}")
    print("FROZEN FUNDING LOOKBACK ESCALATION CLOSED AT 50; NO FURTHER COVERAGE RESCUE")
    print("NO HARD CLUSTER MERGES APPLIED")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
