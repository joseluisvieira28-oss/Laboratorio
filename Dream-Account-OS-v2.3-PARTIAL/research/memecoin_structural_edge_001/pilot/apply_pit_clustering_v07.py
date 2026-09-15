#!/usr/bin/env python3
"""MSEL-001 snapshot-local economic entity clustering V0.7.

LOCAL-ONLY / READ-ONLY / OUTCOMES LOCKED.

Implements FUNDER_CLUSTER_POLICY_FREEZE_V01.md exactly:
- recompute primary-funder degree AS OF each token snapshot;
- degree 2..5 only may hard-merge;
- Tier A: exact same primary funding transaction;
- Tier B: remaining same-funder wallets merge only if group-wide funding span <=60s
  and max/min funding amount <=1.05;
- every merged wallet must have direct funding <= anchor and funding lead <=3600s;
- degree 6..9 and >=10 never hard-merge;
- unresolved funding never means independent;
- creator-linked clusters are excluded from external Organicity candidate;
- no future token outcomes are read.

This stage emits cluster-adjusted trade-structure features and a reusable snapshot-local
wallet->cluster map. Holder-state Hidden Concentration remains a later stage.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple

EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V03_MANIFEST_SHA256 = "107f6a8c7eff6d98db6af6916e531b0f43a001704898440904452956e9294cea"
EXPECTED_V05_MANIFEST_SHA256 = "0c787209d6a58ebd9cf190833dbcce7d807d26b144ee868c96a2cdff8323b580"
EXPECTED_V06_MANIFEST_SHA256 = "6be47d8fecb3a344fcb1bde105d369535c102caa3455c72e444d69fcaed16933"
VERSION = "MSEL_PIT_CLUSTERING_V07"
SNAPSHOTS = (60, 180, 300)
ECON_CLASSES = {"ECONOMIC_BUY_CANDIDATE", "ECONOMIC_SELL_CANDIDATE"}
MAX_HARD_DEGREE = 5
MIN_HARD_DEGREE = 2
MAX_FUNDING_LEAD_SECONDS = 3600
MAX_TIGHT_SPAN_SECONDS = 60
MAX_TIGHT_AMOUNT_RATIO = 1.05


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


def cluster_id(mint: str, horizon: int, members: List[str]) -> str:
    raw = (mint + "|" + str(horizon) + "|" + "|".join(sorted(members))).encode("utf-8")
    return "C_" + hashlib.sha256(raw).hexdigest()[:20]


def status_funding_eligible(s: Dict[str, Any], deadline: int) -> bool:
    if not s or s.get("funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND":
        return False
    ft = s.get("primary_funding_block_time")
    at = s.get("anchor_block_time")
    if ft is None or at is None:
        return False
    ft = int(ft); at = int(at)
    if at > deadline or ft > at:
        return False
    lead = at - ft
    return 0 <= lead <= MAX_FUNDING_LEAD_SECONDS


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    d5 = here / "data" / "msel001_funding_v05"
    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    events_path = d / "trade_events_economic_v03.jsonl"
    v03_manifest_path = d / "economic_manifest_v03.json"
    status_path = d5 / "wallet_funding_status_v05.jsonl"
    v05_manifest_path = d5 / "funding_manifest_v05.json"
    v06_manifest_path = d5 / "funder_topology_manifest_v06.json"

    required = [cohort_path, events_path, v03_manifest_path, status_path, v05_manifest_path, v06_manifest_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")
    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha256_bytes(v03_manifest_path.read_bytes()) != EXPECTED_V03_MANIFEST_SHA256:
        raise RuntimeError("V03_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v05_manifest_path.read_bytes()) != EXPECTED_V05_MANIFEST_SHA256:
        raise RuntimeError("V05_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v06_manifest_path.read_bytes()) != EXPECTED_V06_MANIFEST_SHA256:
        raise RuntimeError("V06_MANIFEST_HASH_MISMATCH")

    m03 = load_json(v03_manifest_path)
    m05 = load_json(v05_manifest_path)
    m06 = load_json(v06_manifest_path)
    if any(m.get("outcomes_opened") is not False for m in (m03, m05, m06)):
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    if m05.get("wallet_funding_status_v05_sha256") != sha256_bytes(status_path.read_bytes()):
        raise RuntimeError("V05_STATUS_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    events = [r for r in load_jsonl(events_path) if r.get("semantic_class") in ECON_CLASSES]
    statuses = load_jsonl(status_path)
    if len(cohort) != 25:
        raise RuntimeError(f"COHORT_SIZE_MISMATCH {len(cohort)}/25")

    by_mint = {r["mint"]: r for r in cohort}
    status_by_wallet = {r["wallet"]: r for r in statuses}
    if len(status_by_wallet) != len(statuses):
        raise RuntimeError("DUPLICATE_WALLET_STATUS")

    assignments: List[Dict[str, Any]] = []
    snapshots: List[Dict[str, Any]] = []

    for mint, launch in sorted(by_mint.items(), key=lambda kv: int(kv[1]["cohort_rank"])):
        creator = launch["origin_creator"]
        launch_time = int(launch["block_time"])
        for horizon in SNAPSHOTS:
            deadline = launch_time + horizon
            rows = [r for r in events if r["mint"] == mint and int(r["block_time"]) <= deadline]

            wallet_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"buy": 0, "sell": 0, "count": 0})
            for r in rows:
                w = r["user"]
                sol = int(r["sol_amount_raw"])
                if r["side"] == "buy":
                    wallet_stats[w]["buy"] += sol
                else:
                    wallet_stats[w]["sell"] += sol
                wallet_stats[w]["count"] += 1
            current_wallets = sorted(wallet_stats)

            # Snapshot-local primary-funder degrees. Wallets anchored after this deadline cannot affect degree.
            degree_asof = Counter()
            for s in statuses:
                f = s.get("primary_funder")
                at = s.get("anchor_block_time")
                if f and at is not None and int(at) <= deadline:
                    degree_asof[str(f)] += 1

            # Default singleton assignment.
            wallet_to_cluster = {w: "W_" + w for w in current_wallets}
            wallet_reason = {w: "SINGLETON" for w in current_wallets}

            by_funder_current: Dict[str, List[str]] = defaultdict(list)
            for w in current_wallets:
                s = status_by_wallet.get(w) or {}
                f = s.get("primary_funder")
                if f:
                    by_funder_current[str(f)].append(w)

            # Hard merge under frozen policy.
            for funder, members in sorted(by_funder_current.items()):
                deg = int(degree_asof.get(funder, 0))
                if not (MIN_HARD_DEGREE <= deg <= MAX_HARD_DEGREE):
                    continue
                eligible = [w for w in members if status_funding_eligible(status_by_wallet.get(w) or {}, deadline)]
                if len(eligible) < 2:
                    continue

                merged: set[str] = set()
                # Tier A: same exact primary funding tx.
                sig_groups: Dict[str, List[str]] = defaultdict(list)
                for w in eligible:
                    sig = status_by_wallet[w].get("primary_funding_signature")
                    if sig:
                        sig_groups[str(sig)].append(w)
                for sig, grp in sorted(sig_groups.items()):
                    grp = sorted(grp)
                    if len(grp) < 2:
                        continue
                    cid = cluster_id(mint, horizon, grp)
                    for w in grp:
                        wallet_to_cluster[w] = cid
                        wallet_reason[w] = "HARD_SAME_FUNDING_TX"
                        merged.add(w)

                # Tier B: all remaining eligible members must be tightly synchronized group-wide.
                remaining = sorted(w for w in eligible if w not in merged)
                if len(remaining) >= 2:
                    times = [int(status_by_wallet[w]["primary_funding_block_time"]) for w in remaining]
                    amounts = [int(status_by_wallet[w]["primary_funding_lamports"]) for w in remaining]
                    span = max(times) - min(times)
                    ratio = (max(amounts) / min(amounts)) if min(amounts) > 0 else None
                    if span <= MAX_TIGHT_SPAN_SECONDS and ratio is not None and ratio <= MAX_TIGHT_AMOUNT_RATIO:
                        cid = cluster_id(mint, horizon, remaining)
                        for w in remaining:
                            wallet_to_cluster[w] = cid
                            wallet_reason[w] = "HARD_TIGHT_SYNC"
                            merged.add(w)

            # Assign explicit singleton/ambiguity reasons and emit per-wallet cluster map.
            for w in current_wallets:
                s = status_by_wallet.get(w) or {}
                f = s.get("primary_funder")
                deg = int(degree_asof.get(str(f), 0)) if f else 0
                if wallet_reason[w] == "SINGLETON":
                    if not f:
                        reason = "SINGLETON_UNRESOLVED_FUNDING"
                    elif deg == 1:
                        reason = "SINGLETON_FUNDER_DEGREE_1"
                    elif 2 <= deg <= 5:
                        if not status_funding_eligible(s, deadline):
                            reason = "SINGLETON_SMALL_FUNDER_INELIGIBLE_TIMING"
                        else:
                            reason = "SINGLETON_SMALL_FUNDER_FAILED_SYNC"
                    elif 6 <= deg <= 9:
                        reason = "SINGLETON_AMBIGUOUS_DEGREE_6_9"
                    elif deg >= 10:
                        reason = "SINGLETON_HUB_DEGREE_10_PLUS"
                    else:
                        reason = "SINGLETON_OTHER"
                    wallet_reason[w] = reason

                assignments.append({
                    "mint": mint,
                    "cohort_rank": launch["cohort_rank"],
                    "snapshot_horizon_seconds": horizon,
                    "snapshot_deadline": deadline,
                    "wallet": w,
                    "cluster_id": wallet_to_cluster[w],
                    "assignment_reason": wallet_reason[w],
                    "is_origin_creator": w == creator,
                    "primary_funder": f,
                    "primary_funder_degree_asof": deg if f else None,
                    "funding_status": s.get("funding_status", "NO_V05_STATUS"),
                    "primary_funding_block_time": s.get("primary_funding_block_time"),
                    "primary_funding_lamports": s.get("primary_funding_lamports"),
                    "anchor_block_time": s.get("anchor_block_time"),
                })

            # Aggregate economic flows by snapshot-local cluster.
            cluster_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                "buy": 0, "sell": 0, "wallets": set(), "creator_linked": False
            })
            for w, st in wallet_stats.items():
                cid = wallet_to_cluster[w]
                cs = cluster_stats[cid]
                cs["buy"] += st["buy"]
                cs["sell"] += st["sell"]
                cs["wallets"].add(w)
                if w == creator:
                    cs["creator_linked"] = True

            external = {cid: cs for cid, cs in cluster_stats.items() if not cs["creator_linked"]}
            external_gross = sum(int(cs["buy"] + cs["sell"]) for cs in external.values())
            external_positive_net = sum(max(int(cs["buy"] - cs["sell"]), 0) for cs in external.values())
            external_signed_net = sum(int(cs["buy"] - cs["sell"]) for cs in external.values())
            organ = (external_positive_net / external_gross) if external_gross > 0 else None
            signed_ratio = (external_signed_net / external_gross) if external_gross > 0 else None
            buy_base = {cid: int(cs["buy"]) for cid, cs in external.items() if int(cs["buy"]) > 0}

            total_gross = sum(int(st["buy"] + st["sell"]) for st in wallet_stats.values())
            uncertainty_gross = Counter()
            for w, st in wallet_stats.items():
                gross = int(st["buy"] + st["sell"])
                reason = wallet_reason[w]
                if reason == "SINGLETON_UNRESOLVED_FUNDING":
                    uncertainty_gross["unresolved"] += gross
                elif reason == "SINGLETON_HUB_DEGREE_10_PLUS":
                    uncertainty_gross["hub10plus"] += gross
                elif reason == "SINGLETON_AMBIGUOUS_DEGREE_6_9":
                    uncertainty_gross["ambig6to9"] += gross
                elif reason in ("SINGLETON_SMALL_FUNDER_FAILED_SYNC", "SINGLETON_SMALL_FUNDER_INELIGIBLE_TIMING"):
                    uncertainty_gross["small_unmerged"] += gross

            hard_clusters = [cs for cs in cluster_stats.values() if len(cs["wallets"]) >= 2]
            hard_merged_wallets = sum(len(cs["wallets"]) for cs in hard_clusters)
            max_cluster_size = max((len(cs["wallets"]) for cs in hard_clusters), default=1)

            snapshots.append({
                "mint": mint,
                "cohort_rank": launch["cohort_rank"],
                "origin_creator": creator,
                "snapshot_horizon_seconds": horizon,
                "snapshot_deadline": deadline,
                "economic_wallet_count": len(current_wallets),
                "economic_cluster_count": len(cluster_stats),
                "hard_cluster_count": len(hard_clusters),
                "hard_merged_wallet_count": hard_merged_wallets,
                "largest_hard_cluster_size": max_cluster_size,
                "external_cluster_count": len(external),
                "external_gross_sol_raw": external_gross,
                "external_positive_net_inflow_raw": external_positive_net,
                "external_signed_net_inflow_raw": external_signed_net,
                "cluster_adjusted_organicity_candidate": organ,
                "cluster_adjusted_signed_net_to_gross": signed_ratio,
                "external_buy_cluster_top1_share": concentration(buy_base, 1),
                "external_buy_cluster_top3_share": concentration(buy_base, 3),
                "external_buy_cluster_hhi": hhi(buy_base),
                "unresolved_funding_gross_share": (uncertainty_gross["unresolved"] / total_gross) if total_gross > 0 else None,
                "hub10plus_gross_share": (uncertainty_gross["hub10plus"] / total_gross) if total_gross > 0 else None,
                "ambiguous_degree6to9_gross_share": (uncertainty_gross["ambig6to9"] / total_gross) if total_gross > 0 else None,
                "small_degree_nonmerged_gross_share": (uncertainty_gross["small_unmerged"] / total_gross) if total_gross > 0 else None,
                "hard_cluster_policy_applied": True,
                "cluster_adjusted_candidate_available": True,
                "final_organicity_ratio_available": False,
                "outcomes_opened": False,
            })

    if len(snapshots) != 75:
        raise RuntimeError(f"SNAPSHOT_COUNT_FAILURE {len(snapshots)}/75")

    out_assign = d5 / "cluster_assignments_v07.jsonl"
    out_snap = d5 / "snapshots_clustered_v07.jsonl"
    assign_sha = write_jsonl(out_assign, assignments)
    snap_sha = write_jsonl(out_snap, snapshots)

    t5 = [r for r in snapshots if int(r["snapshot_horizon_seconds"]) == 300]
    t5_with_merge = sum(1 for r in t5 if int(r["hard_cluster_count"]) > 0)
    t5_hard_clusters = sum(int(r["hard_cluster_count"]) for r in t5)
    t5_merged_wallets = sum(int(r["hard_merged_wallet_count"]) for r in t5)
    max_hard = max(int(r["largest_hard_cluster_size"]) for r in t5) if t5 else 1

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_cohort_sha256": EXPECTED_COHORT_SHA256,
        "source_v03_manifest_sha256": EXPECTED_V03_MANIFEST_SHA256,
        "source_v05_manifest_sha256": EXPECTED_V05_MANIFEST_SHA256,
        "source_v06_manifest_sha256": EXPECTED_V06_MANIFEST_SHA256,
        "policy_freeze": "FUNDER_CLUSTER_POLICY_FREEZE_V01.md",
        "policy": {
            "hard_degree_min": MIN_HARD_DEGREE,
            "hard_degree_max": MAX_HARD_DEGREE,
            "max_funding_lead_seconds": MAX_FUNDING_LEAD_SECONDS,
            "tier_b_max_funding_span_seconds": MAX_TIGHT_SPAN_SECONDS,
            "tier_b_max_amount_ratio": MAX_TIGHT_AMOUNT_RATIO,
            "degree_6_9_hard_merge": False,
            "degree_10_plus_hard_merge": False,
            "missing_funding_means_independent": False,
        },
        "snapshot_count": len(snapshots),
        "cluster_assignment_rows": len(assignments),
        "t5_snapshots_with_hard_merge": t5_with_merge,
        "t5_hard_cluster_instances": t5_hard_clusters,
        "t5_hard_merged_wallet_assignments": t5_merged_wallets,
        "t5_max_hard_cluster_size": max_hard,
        "cluster_assignments_v07_sha256": assign_sha,
        "snapshots_clustered_v07_sha256": snap_sha,
        "same_funder_clustering_applied": True,
        "service_hub_policy_frozen": True,
        "cluster_adjusted_organicity_candidate_available": True,
        "holder_hidden_concentration_clustered": False,
        "final_feature_matrix_frozen": False,
        "final_organicity_ratio_available": False,
        "outcomes_opened": False,
    }
    manifest_path = d5 / "cluster_manifest_v07.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: snapshot-local conservative clustering V07 complete")
    print(f"snapshots: {len(snapshots)}")
    print(f"cluster assignment rows: {len(assignments)}")
    print(f"T+5 snapshots with >=1 hard merge: {t5_with_merge}/25")
    print(f"T+5 hard cluster instances: {t5_hard_clusters}")
    print(f"T+5 hard merged wallet assignments: {t5_merged_wallets}")
    print(f"T+5 max hard cluster size: {max_hard}")
    print(f"manifest sha256: {manifest_sha}")
    print("SERVICE-HUB / CLUSTER POLICY FROZEN AND APPLIED POINT-IN-TIME")
    print("CLUSTER-ADJUSTED ORGANICITY CANDIDATE NOW AVAILABLE")
    print("HOLDER HIDDEN CONCENTRATION STILL REQUIRES CLUSTER MAP APPLICATION")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
