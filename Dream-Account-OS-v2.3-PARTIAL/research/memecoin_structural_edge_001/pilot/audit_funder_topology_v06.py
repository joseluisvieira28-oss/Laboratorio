#!/usr/bin/env python3
"""MSEL-001 funding-topology audit V0.6.

READ-ONLY / LOCAL-ONLY / OUTCOMES LOCKED.

Purpose:
- consume V0.5 primary-funder evidence and V0.4 wallet activity;
- describe the degree structure of observed primary funders;
- identify obvious high-degree service-hub candidates WITHOUT merging wallets;
- quantify timing/amount similarity and same-target co-participation inside shared-funder groups;
- emit the evidence needed to freeze a conservative clustering policy in the NEXT step.

Important:
- degree bands in this audit are descriptive only, NOT merge rules;
- unresolved funding remains unresolved, never "independent";
- no wallet clusters are created here;
- no prices, outcomes, graduation status or trading data are opened.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter, defaultdict
from statistics import median
from typing import Any, Dict, Iterable, List

EXPECTED_V05_MANIFEST_SHA256 = "0c787209d6a58ebd9cf190833dbcce7d807d26b144ee868c96a2cdff8323b580"
EXPECTED_V04_MANIFEST_SHA256 = "ecbc8fa22b885f87984b5cbc4ca39908558a487fa4e36e916574b85f3a2e76c3"
VERSION = "MSEL_FUNDER_TOPOLOGY_AUDIT_V06"


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


def band(degree: int) -> str:
    # DESCRIPTIVE ONLY. These bands are not a hard clustering policy.
    if degree <= 1:
        return "SINGLETON"
    if degree <= 3:
        return "LOW_DEGREE_SHARED"
    if degree <= 9:
        return "MEDIUM_DEGREE_SHARED"
    return "HIGH_DEGREE_HUB_CANDIDATE"


def safe_median(vals: List[int]) -> int | None:
    return int(median(vals)) if vals else None


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d5 = here / "data" / "msel001_funding_v05"
    d4 = here / "data" / "msel001_t5_forensics"

    v05_manifest_path = d5 / "funding_manifest_v05.json"
    status_path = d5 / "wallet_funding_status_v05.jsonl"
    edges_path = d5 / "funding_edges_v05.jsonl"
    v04_manifest_path = d4 / "precluster_wallet_manifest_v04.json"
    wallet_path = d4 / "wallet_activity_precluster_v04.jsonl"

    required = [v05_manifest_path, status_path, edges_path, v04_manifest_path, wallet_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")

    if sha256_bytes(v05_manifest_path.read_bytes()) != EXPECTED_V05_MANIFEST_SHA256:
        raise RuntimeError("V05_MANIFEST_HASH_MISMATCH")
    if sha256_bytes(v04_manifest_path.read_bytes()) != EXPECTED_V04_MANIFEST_SHA256:
        raise RuntimeError("V04_MANIFEST_HASH_MISMATCH")

    m5 = load_json(v05_manifest_path)
    m4 = load_json(v04_manifest_path)
    if m5.get("outcomes_opened") is not False or m4.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    if m5.get("same_funder_clustering_applied") is not False:
        raise RuntimeError("UNEXPECTED_CLUSTERING_STATE")

    statuses = load_jsonl(status_path)
    edges = load_jsonl(edges_path)
    wallet_rows = load_jsonl(wallet_path)

    if m5.get("wallet_funding_status_v05_sha256") != sha256_bytes(status_path.read_bytes()):
        raise RuntimeError("V05_STATUS_HASH_MISMATCH")
    if m5.get("funding_edges_v05_sha256") != sha256_bytes(edges_path.read_bytes()):
        raise RuntimeError("V05_EDGES_HASH_MISMATCH")
    if m4.get("wallet_activity_precluster_v04_sha256") != sha256_bytes(wallet_path.read_bytes()):
        raise RuntimeError("V04_WALLET_HASH_MISMATCH")

    resolved = [r for r in statuses if r.get("primary_funder")]
    unresolved = [r for r in statuses if not r.get("primary_funder")]
    degree = Counter(r["primary_funder"] for r in resolved)

    # Point-in-time target-cohort participation map from V0.4 rows.
    mints_by_wallet: Dict[str, set[str]] = defaultdict(set)
    for r in wallet_rows:
        mints_by_wallet[str(r["wallet"])].add(str(r["mint"]))

    by_funder: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in resolved:
        by_funder[str(r["primary_funder"])].append(r)

    funder_rows: List[Dict[str, Any]] = []
    for funder, members in by_funder.items():
        deg = len(members)
        funding_times = [int(r["primary_funding_block_time"]) for r in members if r.get("primary_funding_block_time") is not None]
        anchor_times = [int(r["anchor_block_time"]) for r in members if r.get("anchor_block_time") is not None]
        lead_secs = [
            int(r["anchor_block_time"]) - int(r["primary_funding_block_time"])
            for r in members
            if r.get("anchor_block_time") is not None and r.get("primary_funding_block_time") is not None
        ]
        amounts = [int(r["primary_funding_lamports"]) for r in members if r.get("primary_funding_lamports") is not None]
        creator_members = sum(1 for r in members if r.get("is_origin_creator_any_target"))

        mint_counts: Counter[str] = Counter()
        for r in members:
            for mint in mints_by_wallet.get(str(r["wallet"]), set()):
                mint_counts[mint] += 1
        co_participated_mints = sum(1 for c in mint_counts.values() if c >= 2)
        max_wallets_same_mint = max(mint_counts.values()) if mint_counts else 0

        funder_rows.append({
            "funder": funder,
            "target_wallet_degree": deg,
            "descriptive_band": band(deg),
            "origin_creator_member_count": creator_members,
            "funding_time_span_seconds": (max(funding_times) - min(funding_times)) if len(funding_times) >= 2 else 0,
            "anchor_time_span_seconds": (max(anchor_times) - min(anchor_times)) if len(anchor_times) >= 2 else 0,
            "funding_lead_seconds_median": safe_median(lead_secs),
            "funding_lead_seconds_min": min(lead_secs) if lead_secs else None,
            "funding_lead_seconds_max": max(lead_secs) if lead_secs else None,
            "funding_amount_lamports_median": safe_median(amounts),
            "funding_amount_lamports_min": min(amounts) if amounts else None,
            "funding_amount_lamports_max": max(amounts) if amounts else None,
            "funding_amount_max_to_min_ratio": (max(amounts) / min(amounts)) if amounts and min(amounts) > 0 else None,
            "distinct_target_mints_traded_by_group": len(mint_counts),
            "target_mints_with_2plus_group_wallets": co_participated_mints,
            "max_group_wallets_on_same_target_mint": max_wallets_same_mint,
            "hard_merge_applied": False,
            "service_hub_final_classification": "UNCLASSIFIED",
        })

    funder_rows.sort(key=lambda r: (-int(r["target_wallet_degree"]), r["funder"]))
    band_counts = Counter(r["descriptive_band"] for r in funder_rows)
    wallet_band_counts = Counter()
    for r in funder_rows:
        wallet_band_counts[r["descriptive_band"]] += int(r["target_wallet_degree"])

    out_rows = d5 / "funder_topology_v06.jsonl"
    rows_sha = write_jsonl(out_rows, funder_rows)

    manifest = {
        "artifact": VERSION,
        "version": VERSION,
        "source_v05_manifest_sha256": EXPECTED_V05_MANIFEST_SHA256,
        "source_v04_manifest_sha256": EXPECTED_V04_MANIFEST_SHA256,
        "wallet_universe": len(statuses),
        "resolved_wallets": len(resolved),
        "unresolved_wallets": len(unresolved),
        "unique_primary_funders": len(funder_rows),
        "descriptive_funder_band_counts": dict(sorted(band_counts.items())),
        "wallet_counts_by_descriptive_funder_band": dict(sorted(wallet_band_counts.items())),
        "max_observed_primary_funder_degree": max(degree.values()) if degree else 0,
        "funder_topology_v06_sha256": rows_sha,
        "degree_bands_are_merge_rules": False,
        "hard_cluster_merges_applied": False,
        "service_hub_policy_frozen": False,
        "final_organicity_ratio_available": False,
        "outcomes_opened": False,
    }
    manifest_path = d5 / "funder_topology_manifest_v06.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: funding topology audit V06 complete")
    print(f"wallet universe: {len(statuses)}")
    print(f"resolved wallets: {len(resolved)}")
    print(f"unresolved wallets: {len(unresolved)}")
    print(f"unique primary funders: {len(funder_rows)}")
    print(f"funder bands: {dict(sorted(band_counts.items()))}")
    print(f"wallets by bands: {dict(sorted(wallet_band_counts.items()))}")
    print(f"max primary-funder degree: {max(degree.values()) if degree else 0}")
    print("top funder degrees: " + ", ".join(str(r["target_wallet_degree"]) for r in funder_rows[:10]))
    print(f"manifest sha256: {manifest_sha}")
    print("NO HARD CLUSTER MERGES APPLIED")
    print("SERVICE-HUB / CLUSTER POLICY NOT YET FROZEN")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
