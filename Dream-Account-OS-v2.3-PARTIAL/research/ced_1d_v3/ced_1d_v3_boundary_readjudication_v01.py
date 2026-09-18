#!/usr/bin/env python3
"""CED-1D-V1 V3 boundary-week survivor re-adjudication V0.1.

Purpose: apply the already-frozen signal-completion UTC boundary-week rule to
exactly three historical CED-1D Momentum SCOUT_SURVIVOR cells. This program
reuses the canonical V0.2 mapped closeout implementation for input validation,
metrics, scoring, neighbour definitions and bootstrap arithmetic. It does not
open 2025/2026, alter the hypothesis, create new candidates, or route non-target
cells.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import tempfile
import zipfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

FROZEN_CLOSEOUT_ZIP_SHA256 = "d590b2fe3b86baa9b9b0c1e092cf53c6cb0067ebcafb9fd7a21002dd2df50841"
FROZEN_CLOSEOUT_SOURCE_SHA256 = "71525ab74c926c72c94e952e2d193255901be296f1d0cd32f9bfa90118ba01f8"
EXPECTED_DAILY_SHA256 = "b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20"
EXPECTED_CONTRACT_SHA256 = "4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4"
EXPECTED_DATASET_SHA256 = "0b3de834cf5a126cb348596a466ce191e956640f4e7c3d8d3fbc8f38e1c5ad93"
BOUNDARY_AUTHORITY_DRIVE_ID = "1i06x1R1iFerQYEtKSoJvhD9ONtR6y_qx-j1k8Uj_79w"
BOUNDARY_ADDENDUM_COMMIT = "96d783275e8474dc4a30a14eed16f5f23c29e9b9"
TARGETS = ("CED1D-0031", "CED1D-0241", "CED1D-0251")
FIRST_COMPLETE_WEEK = date(2021, 1, 4)
END_COMPLETE_WEEK_EXCLUSIVE = date(2024, 12, 30)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def signal_week_eligible(signal_day: date) -> bool:
    w = week_start(signal_day)
    return FIRST_COMPLETE_WEEK <= w < END_COMPLETE_WEEK_EXCLUSIVE


def load_frozen_module(extracted_root: Path):
    src = extracted_root / "src" / "closeout.py"
    if sha256_file(src) != FROZEN_CLOSEOUT_SOURCE_SHA256:
        raise RuntimeError("FROZEN_CLOSEOUT_SOURCE_SHA256_MISMATCH")
    spec = importlib.util.spec_from_file_location("ced1d_frozen_closeout", src)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def package_root(extract_dir: Path) -> Path:
    candidates = [p for p in extract_dir.iterdir() if p.is_dir()]
    if len(candidates) != 1:
        raise RuntimeError("FROZEN_PACKAGE_ROOT_NOT_UNIQUE")
    return candidates[0]


def read_raw_blobs(raw_dir: Path, mod, pins: dict[str, str]) -> dict[str, bytes]:
    blobs = {}
    for name in mod.INPUTS:
        p = raw_dir / name
        if not p.is_file():
            raise RuntimeError(f"MISSING_RAW_INPUT:{name}")
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != pins[name]:
            raise RuntimeError(f"RAW_PIN_MISMATCH:{name}")
        blobs[name] = data
    return blobs


def validate_exact_raw(mod, root: Path, blobs: dict[str, bytes], pins: dict[str, str]):
    mod.require(set(blobs) == set(mod.INPUTS), "INPUT_SET_MISMATCH")
    mod.require(all(mod.digest(blobs[n]) == pins[n] for n in mod.INPUTS), "SOURCE_HASH_MISMATCH")
    mod.validate_metadata(blobs)
    expected_registry = json.loads((root / "authority" / "primary_atomic_registry.json").read_text(encoding="utf-8-sig"))
    expected_identities = json.loads((root / "authority" / "cell_identity_map.json").read_text(encoding="utf-8-sig"))
    cells = mod.validate_registry(mod.decode(blobs["primary_atomic_registry.json"]),
                                  mod.parse_csv(blobs["results_raw.csv"]),
                                  expected_registry, expected_identities)
    events, counts = mod.ledger(blobs["event_ledger.csv"], cells)
    for r in mod.parse_csv(blobs["results_raw.csv"]):
        tid = r["test_id"]
        for field, status in [("trade_count", "TRADE"), ("overlap_blocked_count", "OVERLAP_BLOCKED"),
                              ("data_unavailable_count", "DATA_UNAVAILABLE")]:
            mod.require(int(r[field]) == counts[tid][status], "RAW_LEDGER_COUNT_MISMATCH")
    return cells, events, counts


def filtered_events(events: list[dict]) -> tuple[list[dict], list[dict]]:
    eligible, boundary = [], []
    for e in events:
        (eligible if signal_week_eligible(e["signal_day"]) else boundary).append(e)
    return eligible, boundary


def sample_gate_signal_week(mod, events: list[dict], rules: dict) -> dict:
    entry_days = {e["day"] for e in events}
    months = {(d.year, d.month) for d in entry_days}
    signal_weeks = {week_start(e["signal_day"]) for e in events}
    measures = {
        "events": len(events),
        "active_days": len(entry_days),
        "active_week_clusters": len(signal_weeks),
        "active_months": len(months),
    }
    failures = [k for k, v in measures.items() if v < rules["min_" + k]]
    annual = {y: sum(yy == y for yy, mm in months) for y in mod.YEARS}
    failures += ["months_in_" + str(y) for y in mod.YEARS if annual[y] < rules["min_months_per_calendar_year"]]
    measures.update({"months_" + str(y): annual[y] for y in mod.YEARS})
    measures["minimum_floor_ratio"] = min(
        measures[k] / rules["min_" + k]
        for k in ("events", "active_days", "active_week_clusters", "active_months")
    )
    measures["sample_pass"] = not failures
    measures["failed_gates"] = "|".join(failures)
    return measures


def metrics_for_cell(mod, es: list[dict], contract: dict) -> dict:
    base = contract["costs"]["scout_bands"]["BASE"]
    groups = mod.temporal(es, base)
    months = groups["month"]
    years = {str(y): mod.mean(groups["year"].get(str(y), [])) for y in mod.YEARS}
    annual = list(years.values())
    nets = [e["gross"] - base for e in es]
    co = mod.concentration(es, base, contract["stability"])
    return {
        "gate": sample_gate_signal_week(mod, es, contract["sample_rules"]["scout"]),
        "groups": groups,
        "years": years,
        "mean": mod.mean(nets),
        "gross_mean": mod.mean([e["gross"] for e in es]),
        "concentration": co,
        "minimum_temporal_net": min(annual) if all(v is not None for v in annual) else None,
        "positive_month_fraction": (sum(math.fsum(v) > 0 for v in months.values()) / len(months) if months else None),
        "positive_quarters": sum(math.fsum(v) > 0 for v in groups["quarter"].values()),
        "lomo_all_positive": (
            all(mod.mean([e["gross"] - base for e in es if e["day"].strftime("%Y-%m") != month]) > 0
                for month in months) if len(months) > 1 else None
        ),
    }


def bootstrap_signal_week(mod, es: list[dict], base: float, plan) -> dict:
    remapped = [{**e, "day": e["signal_day"]} for e in es]
    result = mod.bootstrap(remapped, base, plan)
    result["week_anchor"] = "signal_completion_day"
    return result


def profit_factor(net_values: list[float]) -> tuple[float | None, str]:
    gains = math.fsum(v for v in net_values if v > 0)
    losses = -math.fsum(v for v in net_values if v < 0)
    if losses == 0:
        return None, "NO_NEGATIVE_BASE_NET_EVENTS"
    return gains / losses, "FINITE"


def max_drawdown(net_values: list[float]) -> float:
    cumulative = peak = 0.0
    max_dd = 0.0
    for v in net_values:
        cumulative += v
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)
    return max_dd


def dependency_scope(mod, cells: dict) -> tuple[str, ...]:
    dep = set(TARGETS)
    for tid in TARGETS:
        dep.update(mod.neighbors(tid, cells))
    return tuple(sorted(dep))


def boundary_signal_status_counts(blob: bytes, target_ids: set[str]) -> dict[str, Counter]:
    counts = {tid: Counter() for tid in target_ids}
    for r in csv.DictReader(blob.decode("utf-8-sig").splitlines()):
        tid = r["test_id"]
        if tid not in target_ids:
            continue
        sd = date.fromisoformat(r["signal_day"])
        if not signal_week_eligible(sd):
            counts[tid][r["status"]] += 1
    return counts


def run(raw_dir: Path, frozen_zip: Path, output: Path) -> dict:
    if output.exists():
        raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    if sha256_file(frozen_zip) != FROZEN_CLOSEOUT_ZIP_SHA256:
        raise RuntimeError("FROZEN_CLOSEOUT_ZIP_SHA256_MISMATCH")

    with tempfile.TemporaryDirectory(prefix="ced1d_v3_") as td:
        td = Path(td)
        with zipfile.ZipFile(frozen_zip) as zf:
            if zf.testzip() is not None:
                raise RuntimeError("FROZEN_CLOSEOUT_ZIP_CRC_FAIL")
            zf.extractall(td)
        root = package_root(td)
        mod = load_frozen_module(root)
        pins = json.loads((root / "authority" / "input_pins.json").read_text(encoding="utf-8-sig"))
        blobs = read_raw_blobs(raw_dir, mod, pins)
        cells, raw_events, raw_counts = validate_exact_raw(mod, root, blobs, pins)
        if tuple(sorted(TARGETS)) != TARGETS:
            raise RuntimeError("TARGET_ORDER_NOT_FROZEN")
        if any(t not in cells for t in TARGETS):
            raise RuntimeError("FROZEN_TARGET_MISSING")
        expected_target_configs = {
            "CED1D-0031": {"family": "A_MOMENTUM", "symbol": "AVAXUSDT", "lookback": 20, "horizon": 1, "direction": "CONTINUATION"},
            "CED1D-0241": {"family": "A_MOMENTUM", "symbol": "SOLUSDT", "lookback": 20, "horizon": 1, "direction": "CONTINUATION"},
            "CED1D-0251": {"family": "A_MOMENTUM", "symbol": "SOLUSDT", "lookback": 60, "horizon": 1, "direction": "CONTINUATION"},
        }
        for tid, expected in expected_target_configs.items():
            actual = {k: cells[tid].get(k) for k in expected}
            if actual != expected:
                raise RuntimeError(f"TARGET_CONFIG_DRIFT:{tid}:{actual}")

        contract = mod.load_contract((root / "authority" / "contract.json").read_bytes())
        if mod.CONTRACT_SHA != EXPECTED_CONTRACT_SHA256 or mod.DATASET_SHA != EXPECTED_DATASET_SHA256 or mod.DAILY_SHA != EXPECTED_DAILY_SHA256:
            raise RuntimeError("FROZEN_AUTHORITY_CONSTANT_DRIFT")

        deps = dependency_scope(mod, cells)
        eligible = {}
        boundary = {}
        metrics = {}
        for tid in deps:
            eligible[tid], boundary[tid] = filtered_events(raw_events[tid])
            metrics[tid] = metrics_for_cell(mod, eligible[tid], contract)

        for tid in TARGETS:
            m = metrics[tid]
            adj = mod.neighbors(tid, cells)
            good = [k for k in adj if metrics[k]["gate"]["sample_pass"] and metrics[k]["mean"] is not None
                    and metrics[k]["mean"] > 0 and m["mean"] is not None and metrics[k]["mean"] >= .5 * m["mean"]]
            m.update(neighbors=adj, neighbor_count=len(adj),
                     neighbor_fraction=len(good) / len(adj) if adj else None,
                     qualifying_neighbors=good)

        base = contract["costs"]["scout_bands"]["BASE"]
        plan = mod.WeekPlan(contract["statistics"]["bootstrap_resamples"], contract["statistics"]["seed"])
        boundary_status = boundary_signal_status_counts(blobs["event_ledger.csv"], set(TARGETS))
        rows, dep_rows = [], []
        for tid in TARGETS:
            c, m, es = cells[tid], metrics[tid], eligible[tid]
            boot = bootstrap_signal_week(mod, es, base, plan)
            component, score, vetoes = mod.score_components(m, contract)
            state = mod.route(score, vetoes, not es and raw_counts[tid]["DATA_UNAVAILABLE"] > 0)
            nets = [e["gross"] - base for e in es]
            pf, pf_status = profit_factor(nets)
            s = sorted(nets)
            rows.append({
                "combination_id": tid,
                "symbol": c["symbol"],
                "family": c["family"],
                "lookback": c["lookback"],
                "direction": c["direction"],
                "horizon": c["horizon"],
                "historical_state": "SCOUT_SURVIVOR",
                "ledger_trade_count": len(raw_events[tid]),
                "inference_trade_count": len(es),
                "boundary_trade_count_excluded": len(boundary[tid]),
                "boundary_overlap_blocked_rows": boundary_status[tid]["OVERLAP_BLOCKED"],
                "boundary_data_unavailable_rows": boundary_status[tid]["DATA_UNAVAILABLE"],
                "sample_pass": m["gate"]["sample_pass"],
                "active_days": m["gate"]["active_days"],
                "active_signal_week_clusters": m["gate"]["active_week_clusters"],
                "active_months": m["gate"]["active_months"],
                "gross_mean_bps": m["gross_mean"],
                "base_mean_net_bps": m["mean"],
                "stress14_mean_net_bps": (m["gross_mean"] - 14 if m["gross_mean"] is not None else None),
                "severe20_mean_net_bps": (m["gross_mean"] - 20 if m["gross_mean"] is not None else None),
                "profit_factor_base": pf,
                "profit_factor_status": pf_status,
                "base_win_rate": (sum(v > 0 for v in nets) / len(nets) if nets else None),
                "base_median_net_bps": (statistics.median(nets) if nets else None),
                "base_p05_net_bps": (mod.percentile(s, .05) if s else None),
                "base_p95_net_bps": (mod.percentile(s, .95) if s else None),
                "max_drawdown_cumulative_base_bps": max_drawdown(nets),
                "bootstrap_status": boot["status"],
                "p_raw": boot["p_raw"],
                "ci_low": boot["ci_low"],
                "ci_high": boot["ci_high"],
                "invalid_bootstrap_fraction": boot["invalid_fraction"],
                "positive_active_month_fraction": m["positive_month_fraction"],
                "positive_quarters": m["positive_quarters"],
                "minimum_year_base_net_bps": m["minimum_temporal_net"],
                "leave_one_month_out_all_positive": m["lomo_all_positive"],
                "concentration_ratio": m["concentration"]["concentration_ratio"],
                "neighbor_ids": "|".join(m["neighbors"]),
                "qualifying_neighbor_ids": "|".join(m["qualifying_neighbors"]),
                "neighbor_positive_effect_fraction": m["neighbor_fraction"],
                "scout_score_v02": score,
                "scout_components_json": json.dumps(component, sort_keys=True, separators=(",", ":")),
                "hard_vetoes": "|".join(vetoes),
                "v3_discovery_routing_state": state,
                "funded_claim_status": "NOT_TESTABLE",
                "execution_claim": "NONFUNDING_REFERENCE_PRICE_SENSITIVITY_ONLY",
                "bh_q_status": "NOT_RECOMPUTED_TARGET_SCOPE_LOCKED_DIAGNOSTIC_ONLY",
                "2025_accessed": False,
                "2026_plus_accessed": False,
            })
            for nid in m["neighbors"]:
                nm = metrics[nid]
                dep_rows.append({
                    "target_id": tid,
                    "dependency_id": nid,
                    "dependency_role": "PARAMETER_NEIGHBOR_ONLY_NOT_ROUTED",
                    "inference_trade_count": len(eligible[nid]),
                    "sample_pass": nm["gate"]["sample_pass"],
                    "base_mean_net_bps": nm["mean"],
                    "qualifies_for_target": nid in m["qualifying_neighbors"],
                })

        output.mkdir(parents=True)
        def write_csv(name, data):
            with (output / name).open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
                w.writeheader(); w.writerows(data)
        write_csv("CED1D_V3_TARGET_READJUDICATION.csv", rows)
        write_csv("CED1D_V3_NEIGHBOR_DEPENDENCIES.csv", dep_rows)
        manifest = {
            "lab": "CED-1D-V1",
            "stage": "V3_BOUNDARY_WEEK_SURVIVOR_READJUDICATION",
            "implementation_version": "0.1.0",
            "target_ids": list(TARGETS),
            "non_target_routing_computed": False,
            "dependency_scope_ids": list(deps),
            "boundary_authority_drive_id": BOUNDARY_AUTHORITY_DRIVE_ID,
            "boundary_addendum_commit": BOUNDARY_ADDENDUM_COMMIT,
            "boundary_rule": {
                "week": "Monday 00:00 UTC to next Monday 00:00 UTC",
                "anchor": "signal_completion_day",
                "first_complete_week": FIRST_COMPLETE_WEEK.isoformat(),
                "complete_week_end_exclusive": END_COMPLETE_WEEK_EXCLUSIVE.isoformat(),
                "ledger_rows_preserved": True,
                "boundary_rows_inference_eligible": False,
            },
            "frozen_closeout_zip_sha256": FROZEN_CLOSEOUT_ZIP_SHA256,
            "frozen_closeout_source_sha256": FROZEN_CLOSEOUT_SOURCE_SHA256,
            "raw_input_pins": pins,
            "derived_daily_sha256": EXPECTED_DAILY_SHA256,
            "contract_sha256": EXPECTED_CONTRACT_SHA256,
            "dataset_sha256": EXPECTED_DATASET_SHA256,
            "base_nonfunding_cost_bps": base,
            "funding_status": "NOT_TESTABLE",
            "bootstrap": {
                "resamples": contract["statistics"]["bootstrap_resamples"],
                "seed": contract["statistics"]["seed"],
                "arithmetic": "FROZEN_V0.2_MAPPED_UNCHANGED",
                "week_anchor_override": "SIGNAL_COMPLETION_PER_PROSPECTIVE_BOUNDARY_AUTHORITY",
            },
            "bh_q": "NOT_RECOMPUTED_TARGET_SCOPE_LOCKED_DIAGNOSTIC_ONLY",
            "promotion_decision_made": False,
            "confirmation_2025_accessed": False,
            "access_2026_plus": False,
            "candidate_emitted": False,
            "promoted_emitted": False,
        }
        (output / "CED1D_V3_READJUDICATION_MANIFEST.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        hashes = {p.name: sha256_file(p) for p in sorted(output.iterdir()) if p.is_file()}
        (output / "CED1D_V3_OUTPUT_HASHES.json").write_text(
            json.dumps(hashes, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        return manifest


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", required=True)
    p.add_argument("--frozen-closeout-zip", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args(argv)
    m = run(Path(a.raw_dir), Path(a.frozen_closeout_zip), Path(a.output))
    print(json.dumps({"status": "V3_READJUDICATION_COMPLETE", **m}, sort_keys=True))


if __name__ == "__main__":
    main()
