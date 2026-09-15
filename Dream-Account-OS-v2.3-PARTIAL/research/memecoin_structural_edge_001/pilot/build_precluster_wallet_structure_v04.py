#!/usr/bin/env python3
"""MSEL-001 point-in-time wallet structure V0.4.

READ-ONLY / LOCAL-ONLY / OUTCOMES LOCKED.

Purpose:
- consume V0.3 historical TradeEvent economics;
- keep only economically delivered, non-atomic Pump trades;
- compute point-in-time wallet activity at T+1/T+3/T+5;
- exclude origin creator from provisional independent-flow metrics;
- quantify buy-notional concentration and repeated multi-launch actor presence;
- emit wallet-level rows that can seed the later funding/same-funder clustering pass;
- expose only a PRECLUSTER organicity upper-bound proxy. FINAL Organicity stays blocked.

No network calls. No future prices. No graduation data. No trading.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

EXPECTED_COHORT_SHA256 = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_TRADE_EVENTS = 1081
EXPECTED_SNAPSHOTS = 75
SNAPSHOTS = (60, 180, 300)
VERSION = "MSEL_PRECLUSTER_WALLET_STRUCTURE_V04"

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


def concentration(shares_base: Dict[str, int], n: int) -> float | None:
    total = sum(shares_base.values())
    if total <= 0:
        return None
    return sum(sorted(shares_base.values(), reverse=True)[:n]) / total


def hhi(shares_base: Dict[str, int]) -> float | None:
    total = sum(shares_base.values())
    if total <= 0:
        return None
    return sum((v / total) ** 2 for v in shares_base.values())


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d = here / "data" / "msel001_t5_forensics"
    cohort_path = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    events_path = d / "trade_events_economic_v03.jsonl"
    v03_manifest_path = d / "economic_manifest_v03.json"

    required = [cohort_path, events_path, v03_manifest_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_INPUTS {missing}")
    if sha256_bytes(cohort_path.read_bytes()) != EXPECTED_COHORT_SHA256:
        raise RuntimeError("COHORT_HASH_MISMATCH")

    cohort = load_jsonl(cohort_path)
    events = load_jsonl(events_path)
    v03_manifest = load_json(v03_manifest_path)

    if len(cohort) != 25:
        raise RuntimeError(f"COHORT_SIZE_MISMATCH {len(cohort)}/25")
    if len(events) != EXPECTED_TRADE_EVENTS:
        raise RuntimeError(f"TRADE_EVENT_COUNT_MISMATCH {len(events)}/{EXPECTED_TRADE_EVENTS}")
    if v03_manifest.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")
    if v03_manifest.get("economic_clustering_applied") is not False:
        raise RuntimeError("UNEXPECTED_CLUSTERING_STATE")

    expected_event_sha = v03_manifest.get("trade_events_economic_v03_sha256") or v03_manifest.get("events_sha256")
    actual_event_sha = sha256_bytes(events_path.read_bytes())
    if expected_event_sha and expected_event_sha != actual_event_sha:
        raise RuntimeError(f"V03_EVENT_HASH_MISMATCH expected={expected_event_sha} actual={actual_event_sha}")

    by_mint = {r["mint"]: r for r in cohort}
    target_mints = set(by_mint)

    # Only delivered/non-atomic economic candidates participate in the provisional wallet structure.
    economic = [r for r in events if r.get("semantic_class") in ECON_CLASSES]
    excluded = [r for r in events if r.get("semantic_class") not in ECON_CLASSES]

    # Global chronological event index used only point-in-time: each snapshot can see events whose block_time <= deadline.
    economic.sort(key=lambda r: (int(r["block_time"]), int(r["slot"]), int(r["transaction_index"]), int(r.get("log_index", 0))))

    snapshots: List[Dict[str, Any]] = []
    wallet_rows: List[Dict[str, Any]] = []

    for mint, launch in sorted(by_mint.items(), key=lambda kv: int(kv[1]["cohort_rank"])):
        launch_time = int(launch["block_time"])
        creator = launch["origin_creator"]

        for horizon in SNAPSHOTS:
            deadline = launch_time + horizon
            rows = [r for r in economic if r["mint"] == mint and int(r["block_time"]) <= deadline]
            all_seen = [r for r in economic if r["mint"] in target_mints and int(r["block_time"]) <= deadline]

            # Per-wallet activity in current mint.
            w: Dict[str, Dict[str, int]] = defaultdict(lambda: {
                "buy_sol_raw": 0,
                "sell_sol_raw": 0,
                "buy_token_raw": 0,
                "sell_token_raw": 0,
                "buy_count": 0,
                "sell_count": 0,
            })
            for r in rows:
                user = r["user"]
                sol = int(r["sol_amount_raw"])
                tok = int(r["token_amount_raw"])
                if r["side"] == "buy":
                    w[user]["buy_sol_raw"] += sol
                    w[user]["buy_token_raw"] += tok
                    w[user]["buy_count"] += 1
                else:
                    w[user]["sell_sol_raw"] += sol
                    w[user]["sell_token_raw"] += tok
                    w[user]["sell_count"] += 1

            # Point-in-time cross-launch activity: only target launches/trades already observed by this deadline.
            mints_by_wallet: Dict[str, set[str]] = defaultdict(set)
            for r in all_seen:
                mints_by_wallet[r["user"]].add(r["mint"])

            buy_by_independent: Dict[str, int] = {}
            creator_gross = 0
            independent_buy = independent_sell = 0
            all_buy = all_sell = 0
            repeated_independent_buy = 0

            for user, stats in w.items():
                all_buy += stats["buy_sol_raw"]
                all_sell += stats["sell_sol_raw"]
                gross = stats["buy_sol_raw"] + stats["sell_sol_raw"]
                is_creator = user == creator
                other_mints = len(mints_by_wallet.get(user, set()) - {mint})
                if is_creator:
                    creator_gross += gross
                else:
                    independent_buy += stats["buy_sol_raw"]
                    independent_sell += stats["sell_sol_raw"]
                    if stats["buy_sol_raw"] > 0:
                        buy_by_independent[user] = stats["buy_sol_raw"]
                        if other_mints > 0:
                            repeated_independent_buy += stats["buy_sol_raw"]

                wallet_rows.append({
                    "mint": mint,
                    "cohort_rank": launch["cohort_rank"],
                    "snapshot_horizon_seconds": horizon,
                    "snapshot_deadline": deadline,
                    "wallet": user,
                    "is_origin_creator": is_creator,
                    "buy_sol_raw": stats["buy_sol_raw"],
                    "sell_sol_raw": stats["sell_sol_raw"],
                    "net_sol_raw": stats["buy_sol_raw"] - stats["sell_sol_raw"],
                    "gross_sol_raw": gross,
                    "buy_token_raw": stats["buy_token_raw"],
                    "sell_token_raw": stats["sell_token_raw"],
                    "buy_count": stats["buy_count"],
                    "sell_count": stats["sell_count"],
                    "distinct_target_mints_traded_asof": len(mints_by_wallet.get(user, set())),
                    "other_target_mints_traded_asof": other_mints,
                    "repeated_cross_launch_actor_asof": other_mints > 0,
                })

            gross_all = all_buy + all_sell
            gross_independent = independent_buy + independent_sell
            net_independent = independent_buy - independent_sell
            provisional_ratio = (net_independent / gross_independent) if gross_independent > 0 else None
            creator_gross_share = (creator_gross / gross_all) if gross_all > 0 else None
            repeated_buy_share = (repeated_independent_buy / independent_buy) if independent_buy > 0 else None

            snapshots.append({
                "mint": mint,
                "cohort_rank": launch["cohort_rank"],
                "origin_creator": creator,
                "snapshot_horizon_seconds": horizon,
                "snapshot_deadline": deadline,
                "economic_trade_count": len(rows),
                "economic_wallet_count": len(w),
                "economic_buy_sol_raw": all_buy,
                "economic_sell_sol_raw": all_sell,
                "economic_gross_sol_raw": gross_all,
                "creator_gross_sol_raw": creator_gross,
                "creator_gross_share": creator_gross_share,
                "provisional_independent_buy_sol_raw": independent_buy,
                "provisional_independent_sell_sol_raw": independent_sell,
                "provisional_independent_gross_sol_raw": gross_independent,
                "provisional_independent_net_inflow_raw": net_independent,
                "precluster_net_to_gross_ratio_upper_bound": provisional_ratio,
                "unique_provisional_independent_buyers": len(buy_by_independent),
                "independent_buy_notional_top1_share": concentration(buy_by_independent, 1),
                "independent_buy_notional_top3_share": concentration(buy_by_independent, 3),
                "independent_buy_notional_hhi": hhi(buy_by_independent),
                "repeated_cross_launch_independent_buy_sol_raw": repeated_independent_buy,
                "repeated_cross_launch_independent_buy_share": repeated_buy_share,
                "final_organicity_ratio_available": False,
                "economic_clustering_applied": False,
            })

    if len(snapshots) != EXPECTED_SNAPSHOTS:
        raise RuntimeError(f"SNAPSHOT_COUNT_FAILURE {len(snapshots)}/{EXPECTED_SNAPSHOTS}")

    out_snapshots = d / "snapshots_precluster_wallet_v04.jsonl"
    out_wallets = d / "wallet_activity_precluster_v04.jsonl"
    snap_sha = write_jsonl(out_snapshots, snapshots)
    wallet_sha = write_jsonl(out_wallets, wallet_rows)

    # Compact counts that should remain stable under rerun.
    unique_wallets = len({r["wallet"] for r in wallet_rows})
    repeat_rows = sum(1 for r in wallet_rows if r["repeated_cross_launch_actor_asof"])
    creator_rows = sum(1 for r in wallet_rows if r["is_origin_creator"])

    manifest = {
        "artifact": VERSION,
        "source_cohort_sha256": EXPECTED_COHORT_SHA256,
        "source_trade_events_v03_sha256": actual_event_sha,
        "source_v03_manifest_sha256": sha256_bytes(v03_manifest_path.read_bytes()),
        "snapshot_count": len(snapshots),
        "wallet_snapshot_rows": len(wallet_rows),
        "unique_wallets_across_wallet_snapshot_rows": unique_wallets,
        "repeated_cross_launch_wallet_snapshot_rows": repeat_rows,
        "creator_wallet_snapshot_rows": creator_rows,
        "economic_trade_event_count": len(economic),
        "excluded_non_economic_trade_event_count": len(excluded),
        "snapshots_precluster_wallet_v04_sha256": snap_sha,
        "wallet_activity_precluster_v04_sha256": wallet_sha,
        "precluster_ratio_status": "AVAILABLE_AS_UPPER_BOUND_ONLY",
        "funding_graph_applied": False,
        "same_funder_clustering_applied": False,
        "service_hub_flags_applied": False,
        "final_organicity_ratio_available": False,
        "outcomes_opened": False,
    }
    manifest_path = d / "precluster_wallet_manifest_v04.json"
    manifest_sha = write_json(manifest_path, manifest)

    print("PASS: point-in-time precluster wallet structure V04 complete")
    print(f"economic trade events: {len(economic)}")
    print(f"excluded non-economic trade events: {len(excluded)}")
    print(f"snapshots: {len(snapshots)}")
    print(f"wallet snapshot rows: {len(wallet_rows)}")
    print(f"unique wallets: {unique_wallets}")
    print(f"repeated cross-launch wallet rows: {repeat_rows}")
    print(f"manifest sha256: {manifest_sha}")
    print("PRECLUSTER ORGANICITY UPPER-BOUND NOW AVAILABLE")
    print("FINAL ORGANICITY REMAINS BLOCKED PENDING FUNDING/SAME-FUNDER CLUSTERING")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
