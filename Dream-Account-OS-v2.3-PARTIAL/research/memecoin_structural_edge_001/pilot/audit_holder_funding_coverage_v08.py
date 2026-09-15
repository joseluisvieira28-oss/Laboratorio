#!/usr/bin/env python3
"""MSEL-001 holder-universe funding coverage audit V0.8.

LOCAL-ONLY / READ-ONLY / OUTCOMES LOCKED.

Purpose:
- reconstruct complete external holder owner balances at T+1/T+3/T+5 from the
  already-captured token_balance_changes.jsonl ledger;
- compare the HOLDER universe (not only economic traders) against V0.5 funding
  evidence and V0.7 snapshot-local cluster assignments;
- quantify how much holder supply is still outside the funding-evidence universe;
- emit full holder snapshot rows for the later Hidden Concentration pass;
- do NOT pretend uncovered or unresolved holders are independent.

Why this gate exists:
V0.5 anchored economic traders + creators. A transfer-only holder can own supply
without ever appearing as a Pump economic trader, so applying the V0.7 trade-wallet
cluster map directly to holders could silently miss linked ownership. This audit
measures that gap before final holder concentration is frozen.

No network. No prices. No graduation/outcomes. No trading.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import defaultdict
from statistics import median
from typing import Any, Dict, Iterable, List, Tuple

EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V01_SOURCE_MANIFEST_SHA256 = "f6990bd8728a092cbab28aa57026bfd72080460c9a3a191ce42e567be4f10414"
EXPECTED_V07_MANIFEST_SHA256 = "7516861dd86a2b302e4a1360acbaa68f3360b4ddd802352db93f2eccc3012090"
SNAPSHOTS = (60, 180, 300)
VERSION = "MSEL_HOLDER_FUNDING_COVERAGE_V08"


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


def concentration(base: Dict[str, int], n: int) -> float | None:
    total = sum(base.values())
    if total <= 0:
        return None
    return sum(sorted(base.values(), reverse=True)[:n]) / total


def hhi(base: Dict[str, int]) -> float | None:
    total = sum(base.values())
    if total <= 0:
        return None
    return sum((v / total) ** 2 for v in base.values())


def gini(values: List[int]) -> float | None:
    vals = sorted(v for v in values if v > 0)
    n = len(vals)
    if n == 0:
        return None
    total = sum(vals)
    if total <= 0:
        return None
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    d5 = here / "data" / "msel001_funding_v05"
    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    changes_path = d / "token_balance_changes.jsonl"
    v01_manifest_path = d / "source_manifest.json"
    status_path = d5 / "wallet_funding_status_v05.jsonl"
    v05_manifest_path = d5 / "funding_manifest_v05.json"
    assign_path = d5 / "cluster_assignments_v07.jsonl"
    v07_manifest_path = d5 / "cluster_manifest_v07.json"

    required = [
        cohort_path, changes_path, v01_manifest_path, status_path,
        v05_manifest_path, assign_path, v07_manifest_path,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")

    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha256_bytes(v01_manifest_path.read_bytes()) != EXPECTED_V01_SOURCE_MANIFEST_SHA256:
        raise RuntimeError("V01_SOURCE_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v07_manifest_path.read_bytes()) != EXPECTED_V07_MANIFEST_SHA256:
        raise RuntimeError("V07_MANIFEST_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    changes = load_jsonl(changes_path)
    m01 = load_json(v01_manifest_path)
    m05 = load_json(v05_manifest_path)
    m07 = load_json(v07_manifest_path)
    statuses = load_jsonl(status_path)
    assignments = load_jsonl(assign_path)

    if len(cohort) != 25:
        raise RuntimeError(f"COHORT_SIZE_MISMATCH {len(cohort)}/25")
    if m01.get("outcomes_opened") is not False or m05.get("outcomes_opened") is not False or m07.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    if m01.get("token_balance_changes_sha256") != sha256_bytes(changes_path.read_bytes()):
        raise RuntimeError("TOKEN_BALANCE_CHANGES_HASH_MISMATCH")
    if m05.get("wallet_funding_status_v05_sha256") != sha256_bytes(status_path.read_bytes()):
        raise RuntimeError("V05_STATUS_HASH_MISMATCH")
    if m07.get("cluster_assignments_v07_sha256") != sha256_bytes(assign_path.read_bytes()):
        raise RuntimeError("V07_ASSIGNMENT_HASH_MISMATCH")

    by_mint = {r["mint"]: r for r in cohort}
    if len(by_mint) != 25:
        raise RuntimeError("DUPLICATE_COHORT_MINT")

    status_by_wallet = {r["wallet"]: r for r in statuses}
    if len(status_by_wallet) != len(statuses):
        raise RuntimeError("DUPLICATE_V05_WALLET_STATUS")

    assignment_by_key: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
    for r in assignments:
        key = (str(r["mint"]), int(r["snapshot_horizon_seconds"]), str(r["wallet"]))
        if key in assignment_by_key:
            raise RuntimeError(f"DUPLICATE_V07_ASSIGNMENT {key}")
        assignment_by_key[key] = r

    # Ledger rows are target-mint token-account state transitions. Replay by snapshot
    # using post_amount_raw as the authoritative account balance after each transition.
    changes.sort(key=lambda r: (
        int(r["slot"]), int(r["transaction_index"]), str(r["signature"]), str(r["token_account"])
    ))

    holder_rows: List[Dict[str, Any]] = []
    snapshot_rows: List[Dict[str, Any]] = []

    for mint, launch in sorted(by_mint.items(), key=lambda kv: int(kv[1]["cohort_rank"])):
        launch_time = int(launch["block_time"])
        curve_owner = str(launch["bonding_curve"])
        creator = str(launch["origin_creator"])
        mint_changes = [r for r in changes if r["mint"] == mint]

        for horizon in SNAPSHOTS:
            deadline = launch_time + horizon
            account_state: Dict[str, Dict[str, Any]] = {}
            for r in mint_changes:
                bt = int(r["block_time"])
                if bt > deadline:
                    break
                if bt < launch_time:
                    raise RuntimeError(f"PRE_LAUNCH_TOKEN_CHANGE mint={mint} block_time={bt} launch={launch_time}")
                token_account = str(r["token_account"])
                owner = r.get("owner")
                post = int(r["post_amount_raw"])
                if post > 0 and not owner:
                    raise RuntimeError(f"POSITIVE_BALANCE_WITHOUT_OWNER mint={mint} token_account={token_account}")
                account_state[token_account] = {
                    "owner": str(owner) if owner else None,
                    "amount": post,
                }

            owner_balances: Dict[str, int] = defaultdict(int)
            for st in account_state.values():
                if int(st["amount"]) <= 0 or not st.get("owner"):
                    continue
                owner_balances[str(st["owner"])] += int(st["amount"])

            curve_balance = int(owner_balances.get(curve_owner, 0))
            external = {w: int(v) for w, v in owner_balances.items() if w != curve_owner and int(v) > 0}
            external_total = sum(external.values())
            creator_balance = int(external.get(creator, 0))

            covered_balance = 0
            resolved_balance = 0
            unresolved_balance = 0
            missing_balance = 0
            assigned_balance = 0
            covered_holders = resolved_holders = unresolved_holders = missing_holders = assigned_holders = 0

            raw_base = dict(external)
            partial_cluster_base: Dict[str, int] = defaultdict(int)

            for owner, balance in sorted(external.items()):
                status = status_by_wallet.get(owner)
                assign = assignment_by_key.get((mint, horizon, owner))
                in_v05 = status is not None
                funding_resolved = bool(status and status.get("funding_status") == "DIRECT_FUNDING_EVIDENCE_FOUND")
                funding_unresolved = bool(status and status.get("funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND")
                if in_v05:
                    covered_balance += balance
                    covered_holders += 1
                    if funding_resolved:
                        resolved_balance += balance
                        resolved_holders += 1
                    elif funding_unresolved:
                        unresolved_balance += balance
                        unresolved_holders += 1
                else:
                    missing_balance += balance
                    missing_holders += 1

                if assign:
                    assigned_balance += balance
                    assigned_holders += 1
                    cid = str(assign["cluster_id"])
                    reason = str(assign["assignment_reason"])
                else:
                    # No claim of independence: singleton id is only a bookkeeping bucket.
                    cid = "UNMAPPED_" + owner
                    reason = "NO_V07_ASSIGNMENT"
                partial_cluster_base[cid] += balance

                holder_rows.append({
                    "mint": mint,
                    "cohort_rank": launch["cohort_rank"],
                    "snapshot_horizon_seconds": horizon,
                    "snapshot_deadline": deadline,
                    "holder_owner": owner,
                    "balance_raw": balance,
                    "share_external": (balance / external_total) if external_total > 0 else None,
                    "is_origin_creator": owner == creator,
                    "in_v05_funding_universe": in_v05,
                    "v05_funding_status": status.get("funding_status") if status else "NOT_IN_V05_UNIVERSE",
                    "v05_primary_funder": status.get("primary_funder") if status else None,
                    "has_v07_cluster_assignment": assign is not None,
                    "v07_cluster_id_or_unmapped_bucket": cid,
                    "v07_assignment_reason_or_missing": reason,
                    "final_independence_claim": False,
                    "outcomes_opened": False,
                })

            uncovered_share = (missing_balance / external_total) if external_total > 0 else 0.0
            unresolved_share = (unresolved_balance / external_total) if external_total > 0 else 0.0
            assigned_share = (assigned_balance / external_total) if external_total > 0 else 0.0

            snapshot_rows.append({
                "mint": mint,
                "cohort_rank": launch["cohort_rank"],
                "origin_creator": creator,
                "snapshot_horizon_seconds": horizon,
                "snapshot_deadline": deadline,
                "bonding_curve_token_balance_raw": curve_balance,
                "external_token_balance_raw": external_total,
                "external_holder_count": len(external),
                "creator_external_balance_raw": creator_balance,
                "creator_share_external": (creator_balance / external_total) if external_total > 0 else None,
                "raw_top1_holder_share": concentration(raw_base, 1),
                "raw_top3_holder_share": concentration(raw_base, 3),
                "raw_top5_holder_share": concentration(raw_base, 5),
                "raw_top10_holder_share": concentration(raw_base, 10),
                "raw_holder_hhi": hhi(raw_base),
                "raw_holder_gini": gini(list(raw_base.values())),
                "holders_in_v05_funding_universe": covered_holders,
                "holders_with_resolved_v05_funding": resolved_holders,
                "holders_with_unresolved_v05_funding": unresolved_holders,
                "holders_absent_from_v05_funding_universe": missing_holders,
                "holders_with_v07_cluster_assignment": assigned_holders,
                "balance_in_v05_funding_universe_raw": covered_balance,
                "balance_resolved_v05_funding_raw": resolved_balance,
                "balance_unresolved_v05_funding_raw": unresolved_balance,
                "balance_absent_from_v05_funding_universe_raw": missing_balance,
                "balance_with_v07_assignment_raw": assigned_balance,
                "holder_balance_uncovered_share": uncovered_share,
                "holder_balance_unresolved_funding_share": unresolved_share,
                "holder_balance_with_v07_assignment_share": assigned_share,
                "partial_map_top1_share": concentration(dict(partial_cluster_base), 1),
                "partial_map_top3_share": concentration(dict(partial_cluster_base), 3),
                "partial_map_hhi": hhi(dict(partial_cluster_base)),
                "partial_map_is_final_hidden_concentration": False,
                "final_hidden_concentration_available": False,
                "outcomes_opened": False,
            })

    if len(snapshot_rows) != 75:
        raise RuntimeError(f"SNAPSHOT_COUNT_FAILURE {len(snapshot_rows)}/75")

    out_holders = d5 / "holder_snapshot_rows_v08.jsonl"
    out_snap = d5 / "holder_funding_coverage_snapshots_v08.jsonl"
    holders_sha = write_jsonl(out_holders, holder_rows)
    snap_sha = write_jsonl(out_snap, snapshot_rows)

    unique_holder_owners = len({r["holder_owner"] for r in holder_rows})
    missing_unique = len({r["holder_owner"] for r in holder_rows if not r["in_v05_funding_universe"]})
    t5 = [r for r in snapshot_rows if int(r["snapshot_horizon_seconds"]) == 300]
    t5_uncovered = [float(r["holder_balance_uncovered_share"]) for r in t5]
    t5_unresolved = [float(r["holder_balance_unresolved_funding_share"]) for r in t5]
    t5_with_missing = sum(1 for x in t5_uncovered if x > 0)
    t5_with_unresolved = sum(1 for x in t5_unresolved if x > 0)

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_cohort_sha256": EXPECTED_COHORT_SHA256,
        "source_v01_manifest_sha256": EXPECTED_V01_SOURCE_MANIFEST_SHA256,
        "source_v07_manifest_sha256": EXPECTED_V07_MANIFEST_SHA256,
        "holder_snapshot_rows": len(holder_rows),
        "snapshot_count": len(snapshot_rows),
        "unique_external_holder_owners_across_snapshots": unique_holder_owners,
        "unique_external_holder_owners_absent_from_v05": missing_unique,
        "t5_snapshots_with_uncovered_holder_balance": t5_with_missing,
        "t5_max_uncovered_holder_share": max(t5_uncovered) if t5_uncovered else None,
        "t5_median_uncovered_holder_share": median(t5_uncovered) if t5_uncovered else None,
        "t5_snapshots_with_unresolved_funding_balance": t5_with_unresolved,
        "t5_max_unresolved_funding_share": max(t5_unresolved) if t5_unresolved else None,
        "holder_snapshot_rows_v08_sha256": holders_sha,
        "holder_funding_coverage_snapshots_v08_sha256": snap_sha,
        "holder_funding_coverage_audited": True,
        "new_holder_funding_collection_needed": missing_unique > 0,
        "final_hidden_concentration_available": False,
        "final_feature_matrix_frozen": False,
        "outcomes_opened": False,
    }
    manifest_path = d5 / "holder_funding_coverage_manifest_v08.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: holder-universe funding coverage audit V08 complete")
    print(f"snapshots: {len(snapshot_rows)}")
    print(f"holder snapshot rows: {len(holder_rows)}")
    print(f"unique external holder owners: {unique_holder_owners}")
    print(f"unique holder owners absent from V05: {missing_unique}")
    print(f"T+5 snapshots with uncovered holder balance: {t5_with_missing}/25")
    print(f"T+5 max uncovered holder share: {max(t5_uncovered) if t5_uncovered else None}")
    print(f"T+5 median uncovered holder share: {median(t5_uncovered) if t5_uncovered else None}")
    print(f"T+5 snapshots with unresolved funding balance: {t5_with_unresolved}/25")
    print(f"T+5 max unresolved funding share: {max(t5_unresolved) if t5_unresolved else None}")
    print(f"manifest sha256: {manifest_sha}")
    if missing_unique > 0:
        print("ADDITIONAL HOLDER-ONLY FUNDING EVIDENCE REQUIRED BEFORE FINAL HIDDEN CONCENTRATION")
    else:
        print("HOLDER FUNDING UNIVERSE COVERAGE COMPLETE; FINAL CLUSTER APPLICATION MAY PROCEED")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
