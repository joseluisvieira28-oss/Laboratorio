#!/usr/bin/env python3
"""MSEL-001 holder-state PIT clustering V1.0.

LOCAL-ONLY / READ-ONLY / OUTCOMES LOCKED.

Implements HOLDER_CLUSTER_APPLICATION_ADDENDUM_V01.md and the already-frozen
FUNDER_CLUSTER_POLICY_FREEZE_V01.md.

Key anti-leakage rule:
- V09 completion evidence for a holder wallet becomes eligible only from that
  wallet's first frozen holder snapshot deadline onward.
- Before that point, global funder degree falls back to trusted V05 standard-
  transfer evidence if available.
- V05 TransferWithSeed/unverifiable primaries are treated as unresolved here.

No network. No prices. No future outcomes. No trading.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter, defaultdict
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple

EXPECTED_V05_MANIFEST_SHA256 = "0c787209d6a58ebd9cf190833dbcce7d807d26b144ee868c96a2cdff8323b580"
EXPECTED_V08_MANIFEST_SHA256 = "a04f8efd1a0a220f37592a45affdc16a725e3f4530e5a1bbbbe257ad318c6df8"
EXPECTED_V09_MANIFEST_SHA256 = "068f5f312918904f491e8d60f63eb6828ac0b3905ad9bdf84dd4c78744d6bd3a"
VERSION = "MSEL_HOLDER_PIT_CLUSTERING_V10"
MIN_HARD_DEGREE = 2
MAX_HARD_DEGREE = 5
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


def concentration(base: Dict[str, int], n: int) -> Optional[float]:
    total = sum(base.values())
    if total <= 0:
        return None
    return sum(sorted(base.values(), reverse=True)[:n]) / total


def hhi(base: Dict[str, int]) -> Optional[float]:
    total = sum(base.values())
    if total <= 0:
        return None
    return sum((v / total) ** 2 for v in base.values())


def gini(values: List[int]) -> Optional[float]:
    vals = sorted(v for v in values if v > 0)
    n = len(vals)
    if n == 0:
        return None
    total = sum(vals)
    if total <= 0:
        return None
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def cluster_id(mint: str, horizon: int, members: List[str]) -> str:
    raw = (mint + "|" + str(horizon) + "|" + "|".join(sorted(members))).encode("utf-8")
    return "HC_" + hashlib.sha256(raw).hexdigest()[:20]


def match_primary_edge(status: Dict[str, Any], edges_by_wallet: Dict[str, List[Dict[str, Any]]], final: bool) -> Optional[Dict[str, Any]]:
    wallet = str(status["wallet"])
    if final:
        if status.get("final_funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER":
            return None
        sig = status.get("final_primary_funding_signature")
        funder = status.get("final_primary_funder")
        lamports = status.get("final_primary_funding_lamports")
    else:
        if status.get("funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND":
            return None
        sig = status.get("primary_funding_signature")
        funder = status.get("primary_funder")
        lamports = status.get("primary_funding_lamports")
    if sig is None or funder is None or lamports is None:
        return None
    matches = [
        e for e in edges_by_wallet.get(wallet, [])
        if e.get("funding_signature") == sig
        and e.get("funder") == funder
        and int(e.get("lamports", -1)) == int(lamports)
        and e.get("instruction_class") == "SYSTEM_TRANSFER"
    ]
    return matches[0] if len(matches) == 1 else None


def canonical_from_v05(status: Dict[str, Any], edge: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if edge is None:
        return {
            "wallet": str(status["wallet"]), "resolved": False, "funder": None,
            "funding_time": None, "funding_lamports": None, "funding_signature": None,
            "anchor_time": int(status["anchor_block_time"]) if status.get("anchor_block_time") is not None else None,
            "source": "V05_UNTRUSTED_OR_UNRESOLVED",
        }
    return {
        "wallet": str(status["wallet"]), "resolved": True, "funder": str(edge["funder"]),
        "funding_time": int(edge["funding_block_time"]) if edge.get("funding_block_time") is not None else None,
        "funding_lamports": int(edge["lamports"]), "funding_signature": str(edge["funding_signature"]),
        "anchor_time": int(status["anchor_block_time"]) if status.get("anchor_block_time") is not None else None,
        "source": "V05_TRUSTED_STANDARD_TRANSFER",
    }


def canonical_from_v09(status: Dict[str, Any], edge: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    anchor_time = int(status["anchor_block_time"]) if status.get("anchor_block_time") is not None else None
    if edge is None:
        return {
            "wallet": str(status["wallet"]), "resolved": False, "funder": None,
            "funding_time": None, "funding_lamports": None, "funding_signature": None,
            "anchor_time": anchor_time, "source": "V09_UNRESOLVED_AFTER_FROZEN_COMPLETION",
        }
    return {
        "wallet": str(status["wallet"]), "resolved": True, "funder": str(edge["funder"]),
        "funding_time": int(edge["funding_block_time"]) if edge.get("funding_block_time") is not None else None,
        "funding_lamports": int(edge["lamports"]), "funding_signature": str(edge["funding_signature"]),
        "anchor_time": anchor_time, "source": "V09_FINAL_STANDARD_TRANSFER",
    }


def funding_eligible(c: Dict[str, Any], deadline: int) -> bool:
    if not c.get("resolved"):
        return False
    ft = c.get("funding_time"); at = c.get("anchor_time")
    if ft is None or at is None:
        return False
    ft = int(ft); at = int(at)
    if at > deadline or ft > at:
        return False
    return 0 <= at - ft <= MAX_FUNDING_LEAD_SECONDS


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d5 = here / "data" / "msel001_funding_v05"
    d9 = here / "data" / "msel001_holder_funding_v09"

    v05_manifest_path = d5 / "funding_manifest_v05.json"
    v05_status_path = d5 / "wallet_funding_status_v05.jsonl"
    v05_edges_path = d5 / "funding_edges_v05.jsonl"
    v08_manifest_path = d5 / "holder_funding_coverage_manifest_v08.json"
    holder_rows_path = d5 / "holder_snapshot_rows_v08.jsonl"
    v09_manifest_path = d9 / "holder_funding_manifest_v09.json"
    v09_status_path = d9 / "holder_funding_status_v09.jsonl"
    v09_edges_path = d9 / "holder_funding_edges_v09.jsonl"

    required = [v05_manifest_path, v05_status_path, v05_edges_path, v08_manifest_path,
                holder_rows_path, v09_manifest_path, v09_status_path, v09_edges_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")

    if sha256_bytes(v05_manifest_path.read_bytes()) != EXPECTED_V05_MANIFEST_SHA256:
        raise RuntimeError("V05_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v08_manifest_path.read_bytes()) != EXPECTED_V08_MANIFEST_SHA256:
        raise RuntimeError("V08_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v09_manifest_path.read_bytes()) != EXPECTED_V09_MANIFEST_SHA256:
        raise RuntimeError("V09_MANIFEST_HASH_MISMATCH")

    m05 = load_json(v05_manifest_path); m08 = load_json(v08_manifest_path); m09 = load_json(v09_manifest_path)
    if any(m.get("outcomes_opened") is not False for m in (m05, m08, m09)):
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")

    s05 = load_jsonl(v05_status_path); e05 = load_jsonl(v05_edges_path)
    holders = load_jsonl(holder_rows_path)
    s09 = load_jsonl(v09_status_path); e09 = load_jsonl(v09_edges_path)

    if m05.get("wallet_funding_status_v05_sha256") != sha256_bytes(v05_status_path.read_bytes()):
        raise RuntimeError("V05_STATUS_HASH_MISMATCH")
    if m05.get("funding_edges_v05_sha256") != sha256_bytes(v05_edges_path.read_bytes()):
        raise RuntimeError("V05_EDGES_HASH_MISMATCH")
    if m08.get("holder_snapshot_rows_v08_sha256") != sha256_bytes(holder_rows_path.read_bytes()):
        raise RuntimeError("V08_HOLDER_ROWS_HASH_MISMATCH")
    if m09.get("holder_funding_status_v09_sha256") != sha256_bytes(v09_status_path.read_bytes()):
        raise RuntimeError("V09_STATUS_HASH_MISMATCH")
    if m09.get("holder_funding_edges_v09_sha256") != sha256_bytes(v09_edges_path.read_bytes()):
        raise RuntimeError("V09_EDGES_HASH_MISMATCH")

    e05_by: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    e09_by: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in e05: e05_by[str(e["wallet"])].append(e)
    for e in e09: e09_by[str(e["wallet"])].append(e)

    s05_by = {str(s["wallet"]): s for s in s05}
    s09_by = {str(s["wallet"]): s for s in s09}
    if len(s05_by) != len(s05) or len(s09_by) != len(s09):
        raise RuntimeError("DUPLICATE_STATUS_WALLET")

    c05: Dict[str, Dict[str, Any]] = {}
    v05_nonstandard_or_unverifiable = 0
    v05_unresolved = 0
    for w, s in s05_by.items():
        edge = match_primary_edge(s, e05_by, final=False)
        c = canonical_from_v05(s, edge)
        c05[w] = c
        if s.get("funding_status") == "DIRECT_FUNDING_EVIDENCE_FOUND" and edge is None:
            v05_nonstandard_or_unverifiable += 1
        if s.get("funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND":
            v05_unresolved += 1

    c09: Dict[str, Dict[str, Any]] = {}
    for w, s in s09_by.items():
        edge = match_primary_edge(s, e09_by, final=True)
        c09[w] = canonical_from_v09(s, edge)
        if s.get("final_funding_status") == "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER" and edge is None:
            raise RuntimeError(f"V09_RESOLVED_EDGE_RECONCILIATION_FAILURE wallet={w}")

    first_holder_deadline: Dict[str, int] = {}
    for r in holders:
        w = str(r["holder_owner"]); d = int(r["snapshot_deadline"])
        first_holder_deadline[w] = min(first_holder_deadline.get(w, d), d)
    if set(first_holder_deadline) != set(c09):
        raise RuntimeError(f"V09_HOLDER_UNIVERSE_MISMATCH holders={len(first_holder_deadline)} v09={len(c09)}")

    groups: Dict[Tuple[str, int, int], List[Dict[str, Any]]] = defaultdict(list)
    for r in holders:
        key = (str(r["mint"]), int(r["snapshot_horizon_seconds"]), int(r["snapshot_deadline"]))
        groups[key].append(r)
    if len(groups) != 75:
        raise RuntimeError(f"SNAPSHOT_GROUP_COUNT_FAILURE {len(groups)}/75")

    assignments: List[Dict[str, Any]] = []
    snapshots: List[Dict[str, Any]] = []

    for (mint, horizon, deadline), rows in sorted(groups.items(), key=lambda kv: (int(kv[1][0]["cohort_rank"]), kv[0][1])):
        current = {str(r["holder_owner"]): r for r in rows}
        if len(current) != len(rows):
            raise RuntimeError(f"DUPLICATE_HOLDER_IN_SNAPSHOT mint={mint} horizon={horizon}")

        # Combined point-in-time evidence universe for funder degree.
        applicable: Dict[str, Dict[str, Any]] = dict(c05)
        for w, c in c09.items():
            if first_holder_deadline[w] <= deadline:
                applicable[w] = c

        degree = Counter()
        for c in applicable.values():
            if not c.get("resolved") or not c.get("funder"):
                continue
            at = c.get("anchor_time")
            if at is not None and int(at) <= deadline:
                degree[str(c["funder"])] += 1

        wallet_to_cluster = {w: "W_" + w for w in current}
        reason = {w: "SINGLETON" for w in current}
        by_funder: Dict[str, List[str]] = defaultdict(list)
        for w in current:
            c = c09[w]
            if c.get("resolved") and c.get("funder"):
                by_funder[str(c["funder"])].append(w)

        for funder, members in sorted(by_funder.items()):
            deg = int(degree.get(funder, 0))
            if not (MIN_HARD_DEGREE <= deg <= MAX_HARD_DEGREE):
                continue
            eligible = [w for w in members if funding_eligible(c09[w], deadline)]
            if len(eligible) < 2:
                continue
            merged: set[str] = set()

            sig_groups: Dict[str, List[str]] = defaultdict(list)
            for w in eligible:
                sig = c09[w].get("funding_signature")
                if sig:
                    sig_groups[str(sig)].append(w)
            for sig, grp in sorted(sig_groups.items()):
                grp = sorted(grp)
                if len(grp) < 2:
                    continue
                cid = cluster_id(mint, horizon, grp)
                for w in grp:
                    wallet_to_cluster[w] = cid
                    reason[w] = "HARD_SAME_FUNDING_TX"
                    merged.add(w)

            remaining = sorted(w for w in eligible if w not in merged)
            if len(remaining) >= 2:
                times = [int(c09[w]["funding_time"]) for w in remaining]
                amounts = [int(c09[w]["funding_lamports"]) for w in remaining]
                span = max(times) - min(times)
                ratio = max(amounts) / min(amounts) if min(amounts) > 0 else None
                if span <= MAX_TIGHT_SPAN_SECONDS and ratio is not None and ratio <= MAX_TIGHT_AMOUNT_RATIO:
                    cid = cluster_id(mint, horizon, remaining)
                    for w in remaining:
                        wallet_to_cluster[w] = cid
                        reason[w] = "HARD_TIGHT_SYNC"
                        merged.add(w)

        raw_base: Dict[str, int] = {}
        entity_base: Dict[str, int] = defaultdict(int)
        entity_creator: Dict[str, bool] = defaultdict(bool)
        total_balance = 0
        uncertainty = Counter()

        for w, r in current.items():
            bal = int(r["balance_raw"])
            raw_base[w] = bal
            total_balance += bal
            c = c09[w]
            f = c.get("funder")
            deg = int(degree.get(str(f), 0)) if f else 0

            if reason[w] == "SINGLETON":
                if not c.get("resolved") or not f:
                    reason[w] = "SINGLETON_UNRESOLVED_FUNDING"
                elif deg == 1:
                    reason[w] = "SINGLETON_FUNDER_DEGREE_1"
                elif 2 <= deg <= 5:
                    reason[w] = "SINGLETON_SMALL_FUNDER_FAILED_SYNC" if funding_eligible(c, deadline) else "SINGLETON_SMALL_FUNDER_INELIGIBLE_TIMING"
                elif 6 <= deg <= 9:
                    reason[w] = "SINGLETON_AMBIGUOUS_DEGREE_6_9"
                elif deg >= 10:
                    reason[w] = "SINGLETON_HUB_DEGREE_10_PLUS"
                else:
                    reason[w] = "SINGLETON_OTHER"

            cid = wallet_to_cluster[w]
            entity_base[cid] += bal
            if bool(r.get("is_origin_creator")):
                entity_creator[cid] = True

            if reason[w] == "SINGLETON_UNRESOLVED_FUNDING":
                uncertainty["unresolved"] += bal
            elif reason[w] == "SINGLETON_HUB_DEGREE_10_PLUS":
                uncertainty["hub10plus"] += bal
            elif reason[w] == "SINGLETON_AMBIGUOUS_DEGREE_6_9":
                uncertainty["ambig6to9"] += bal
            elif reason[w] in ("SINGLETON_SMALL_FUNDER_FAILED_SYNC", "SINGLETON_SMALL_FUNDER_INELIGIBLE_TIMING"):
                uncertainty["small_unmerged"] += bal

            assignments.append({
                "mint": mint,
                "cohort_rank": r["cohort_rank"],
                "snapshot_horizon_seconds": horizon,
                "snapshot_deadline": deadline,
                "wallet": w,
                "balance_raw": bal,
                "cluster_id": cid,
                "assignment_reason": reason[w],
                "is_origin_creator": bool(r.get("is_origin_creator")),
                "final_funding_status": s09_by[w].get("final_funding_status"),
                "primary_funder": f,
                "primary_funder_degree_asof": deg if f else None,
                "funding_time": c.get("funding_time"),
                "funding_lamports": c.get("funding_lamports"),
                "anchor_time": c.get("anchor_time"),
                "v09_evidence_eligible_from_first_holder_deadline": first_holder_deadline[w],
                "outcomes_opened": False,
            })

        hard_clusters = [cid for cid in entity_base if sum(1 for w in current if wallet_to_cluster[w] == cid) >= 2]
        hard_merged_wallets = sum(sum(1 for w in current if wallet_to_cluster[w] == cid) for cid in hard_clusters)
        largest = max((sum(1 for w in current if wallet_to_cluster[w] == cid) for cid in hard_clusters), default=1)
        creator_entity_balance = sum(v for cid, v in entity_base.items() if entity_creator.get(cid, False))

        def share(name: str) -> float:
            return uncertainty[name] / total_balance if total_balance > 0 else 0.0

        snapshots.append({
            "mint": mint,
            "cohort_rank": rows[0]["cohort_rank"],
            "snapshot_horizon_seconds": horizon,
            "snapshot_deadline": deadline,
            "external_holder_count": len(current),
            "external_entity_count": len(entity_base),
            "external_balance_raw": total_balance,
            "raw_top1_holder_share": concentration(raw_base, 1),
            "raw_top3_holder_share": concentration(raw_base, 3),
            "raw_top5_holder_share": concentration(raw_base, 5),
            "raw_top10_holder_share": concentration(raw_base, 10),
            "raw_holder_hhi": hhi(raw_base),
            "raw_holder_gini": gini(list(raw_base.values())),
            "entity_top1_share": concentration(dict(entity_base), 1),
            "entity_top3_share": concentration(dict(entity_base), 3),
            "entity_top5_share": concentration(dict(entity_base), 5),
            "entity_top10_share": concentration(dict(entity_base), 10),
            "entity_hhi": hhi(dict(entity_base)),
            "entity_gini": gini(list(entity_base.values())),
            "top1_cluster_adjustment_delta": ((concentration(dict(entity_base), 1) or 0.0) - (concentration(raw_base, 1) or 0.0)) if total_balance > 0 else None,
            "creator_entity_share": creator_entity_balance / total_balance if total_balance > 0 else None,
            "hard_cluster_count": len(hard_clusters),
            "hard_merged_wallet_count": hard_merged_wallets,
            "largest_hard_cluster_size": largest,
            "unresolved_funding_balance_share": share("unresolved"),
            "hub_degree_10_plus_balance_share": share("hub10plus"),
            "ambiguous_degree_6_9_balance_share": share("ambig6to9"),
            "small_degree_unmerged_balance_share": share("small_unmerged"),
            "remaining_uncertainty_present": any(uncertainty[k] > 0 for k in ("unresolved", "hub10plus", "ambig6to9", "small_unmerged")),
            "hidden_concentration_status": "CONSERVATIVE_HARD_CLUSTER_ESTIMATE_WITH_UNCERTAINTY",
            "outcomes_opened": False,
        })

    if len(assignments) != len(holders):
        raise RuntimeError(f"ASSIGNMENT_COUNT_FAILURE {len(assignments)}/{len(holders)}")
    if len(snapshots) != 75:
        raise RuntimeError(f"SNAPSHOT_COUNT_FAILURE {len(snapshots)}/75")

    out_assign = d9 / "holder_cluster_assignments_v10.jsonl"
    out_snap = d9 / "holder_hidden_concentration_v10.jsonl"
    assign_sha = write_jsonl(out_assign, assignments)
    snap_sha = write_jsonl(out_snap, snapshots)

    t5 = [r for r in snapshots if int(r["snapshot_horizon_seconds"]) == 300]
    t5_hard = sum(1 for r in t5 if int(r["hard_cluster_count"]) > 0)
    t5_hard_instances = sum(int(r["hard_cluster_count"]) for r in t5)
    t5_max_cluster = max(int(r["largest_hard_cluster_size"]) for r in t5)
    t5_unres = [float(r["unresolved_funding_balance_share"]) for r in t5]
    t5_hub = [float(r["hub_degree_10_plus_balance_share"]) for r in t5]
    t5_raw1 = [float(r["raw_top1_holder_share"] or 0.0) for r in t5]
    t5_ent1 = [float(r["entity_top1_share"] or 0.0) for r in t5]

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_v05_manifest_sha256": EXPECTED_V05_MANIFEST_SHA256,
        "source_v08_manifest_sha256": EXPECTED_V08_MANIFEST_SHA256,
        "source_v09_manifest_sha256": EXPECTED_V09_MANIFEST_SHA256,
        "snapshot_count": len(snapshots),
        "assignment_rows": len(assignments),
        "v05_nonstandard_or_unverifiable_primary_edges_treated_unresolved": v05_nonstandard_or_unverifiable,
        "v05_original_unresolved_wallets": v05_unresolved,
        "t5_snapshots_with_hard_merge": t5_hard,
        "t5_hard_cluster_instances": t5_hard_instances,
        "t5_max_hard_cluster_size": t5_max_cluster,
        "t5_median_unresolved_balance_share": median(t5_unres),
        "t5_max_unresolved_balance_share": max(t5_unres),
        "t5_median_hub10plus_balance_share": median(t5_hub),
        "t5_max_hub10plus_balance_share": max(t5_hub),
        "t5_median_raw_top1_share": median(t5_raw1),
        "t5_median_entity_top1_share": median(t5_ent1),
        "holder_cluster_assignments_v10_sha256": assign_sha,
        "holder_hidden_concentration_v10_sha256": snap_sha,
        "funding_lookback_rescue_closed": True,
        "v09_future_holder_selection_leakage_blocked": True,
        "transfer_with_seed_accepted": False,
        "hard_cluster_policy_thresholds_changed": False,
        "final_feature_matrix_frozen": False,
        "outcomes_opened": False,
    }
    out_manifest = d9 / "holder_cluster_manifest_v10.json"
    manifest_sha = write_json(out_manifest, manifest)

    print("PASS: holder-state PIT clustering V10 complete")
    print(f"snapshots: {len(snapshots)}")
    print(f"holder assignment rows: {len(assignments)}")
    print(f"V05 nonstandard/unverifiable primaries treated unresolved: {v05_nonstandard_or_unverifiable}")
    print(f"T+5 snapshots with >=1 hard merge: {t5_hard}/25")
    print(f"T+5 hard cluster instances: {t5_hard_instances}")
    print(f"T+5 max hard cluster size: {t5_max_cluster}")
    print(f"T+5 median unresolved balance share: {median(t5_unres)}")
    print(f"T+5 max unresolved balance share: {max(t5_unres)}")
    print(f"T+5 median hub10+ balance share: {median(t5_hub)}")
    print(f"T+5 max hub10+ balance share: {max(t5_hub)}")
    print(f"T+5 median raw top1 share: {median(t5_raw1)}")
    print(f"T+5 median entity top1 share: {median(t5_ent1)}")
    print(f"manifest sha256: {manifest_sha}")
    print("HIDDEN CONCENTRATION CONSERVATIVE ESTIMATE AVAILABLE WITH EXPLICIT UNCERTAINTY")
    print("NO FURTHER FUNDING COVERAGE RESCUE AUTHORIZED")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
