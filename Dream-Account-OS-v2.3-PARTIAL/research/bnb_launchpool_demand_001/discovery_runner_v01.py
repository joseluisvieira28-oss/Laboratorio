import hashlib
import json
import math
import os
import random
import statistics
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "FINAL_PRE_DISCOVERY_PROTOCOL_V0.1.json"
TECH = HERE / "PRE_DISCOVERY_TECHNICAL_AMENDMENT_V0.1.json"
SOURCE = HERE / "source_validation_v02" / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_VALIDATION_V0.2.json"
MARKET = HERE / "market_source_v01" / "BNB_LAUNCHPOOL_DEMAND_001_MARKET_SOURCE_AUDIT_V0.1.json"
OUTDIR = HERE / "discovery_v01"
OUT = OUTDIR / "BNB_LAUNCHPOOL_DEMAND_001_DISCOVERY_RESULT_V0.1.json"
LEDGER = OUTDIR / "BNB_LAUNCHPOOL_DEMAND_001_DISCOVERY_LEDGER_V0.1.json"

GUARDS = {
    "market_price_values_opened": True,
    "open_parsed": True,
    "high_parsed": False,
    "low_parsed": False,
    "close_parsed": False,
    "volume_parsed": False,
    "funding_opened": False,
    "open_interest_opened": False,
    "returns_computed": True,
    "pnl_computed": False,
    "year_2025_requested": False,
    "year_2026_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
    "alerts_or_webhooks": False,
    "merge_to_main": False,
    "deployment": False,
}


def parse_epoch(raw):
    s = raw.decode("ascii", "strict").strip()
    if not s.isdigit():
        return None
    x = int(s)
    if x > 10**14:
        sec = x / 1_000_000.0
    elif x > 10**11:
        sec = x / 1_000.0
    else:
        sec = float(x)
    return int(round(sec))


def epoch_iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def empirical_quantile(sorted_values, p):
    b = len(sorted_values)
    if b == 0:
        raise ValueError("EMPTY_BOOTSTRAP")
    h = (b - 1) * p
    lo = math.floor(h); hi = math.ceil(h)
    if lo == hi:
        return sorted_values[lo]
    w = h - lo
    return sorted_values[lo] * (1.0 - w) + sorted_values[hi] * w


def profit_factor(values):
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return math.inf if pos > 0 else 0.0
    return pos / neg


def pf_json(x):
    return "+Infinity" if math.isinf(x) else x


def mean_or_none(v):
    return statistics.fmean(v) if v else None


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    t = json.loads(TECH.read_text(encoding="utf-8"))
    s = json.loads(SOURCE.read_text(encoding="utf-8"))
    m = json.loads(MARKET.read_text(encoding="utf-8"))

    assert p["status"] == "FROZEN_PRE_MARKET_OUTCOME"
    assert t["status"] == "FROZEN_BEFORE_ANY_PRICE_VALUE_IS_PARSED"
    assert p["mve_id"] == t["mve_id"] == "BLP-BNBBTC-24H-001"
    assert s["classification"] == "SOURCE_DATA_PASS"
    assert m["classification"] == "MARKET_SOURCE_DATA_PASS"
    assert m["archive_manifest_sha256"] == t["market_source_binding"]["archive_manifest_sha256"]
    assert m["selected_trade_paths"] == 31
    assert p["execution_rule"]["round_trip_cost_base_bps"] == 20.0
    assert p["execution_rule"]["round_trip_cost_stress_bps"] == 30.0
    assert p["execution_rule"]["hold"] == "24 hours from entry timestamp"
    assert p["execution_rule"]["side"] == "LONG_BNBBTC"
    assert p["market_data_contract"]["high_low_close_volume_forbidden"] is True
    assert p["post_result_rules"]["2025_remains_locked"] is True
    assert p["post_result_rules"]["2026_remains_locked"] is True

    artifact_root = Path(os.environ.get("BLP_MARKET_SOURCE_DIR", "/tmp/blp_market_source"))
    if not artifact_root.exists():
        raise RuntimeError(f"MARKET_SOURCE_ARTIFACT_DIR_MISSING:{artifact_root}")
    zips = {x.name: x for x in artifact_root.rglob("BNBBTC-15m-*.zip")}
    if len(zips) != 27:
        raise RuntimeError(f"EXPECTED_27_RAW_ZIPS_GOT_{len(zips)}")

    expected_hashes = {x["archive"]: x["sha256"] for x in m["archive_manifest"]}
    if set(zips) != set(expected_hashes):
        raise RuntimeError("ARTIFACT_ARCHIVE_NAME_SET_MISMATCH")
    verified = []
    for name in sorted(zips):
        if "-2025-" in name:
            GUARDS["year_2025_requested"] = True
            raise RuntimeError("PROTECTED_2025_ARCHIVE_PRESENT")
        if "-2026-" in name:
            GUARDS["year_2026_requested"] = True
            raise RuntimeError("PROTECTED_2026_ARCHIVE_PRESENT")
        dg = sha256_file(zips[name])
        if dg != expected_hashes[name]:
            raise RuntimeError(f"PINNED_ARCHIVE_SHA256_MISMATCH:{name}")
        verified.append({"archive": name, "sha256": dg})

    selected = m["selected"]
    required = set()
    for x in selected:
        required.add(epoch_iso(x["entry_time_utc"]))
        required.add(epoch_iso(x["exit_time_utc"]))
    assert len(required) == 62

    opens = {}
    duplicate_required = []
    # Parse only CSV open_time. Parse open ONLY if that timestamp is one of the 62 frozen entry/exit rows.
    # All remaining fields stay in an opaque byte suffix and are never split or converted.
    for name in sorted(zips):
        with zipfile.ZipFile(zips[name]) as z:
            bad = z.testzip()
            if bad is not None:
                raise RuntimeError(f"ZIP_CRC_FAILURE:{name}:{bad}")
            members = [x for x in z.namelist() if not x.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(f"ZIP_MEMBER_COUNT_NOT_ONE:{name}")
            with z.open(members[0]) as f:
                for line in f:
                    if not line.strip():
                        continue
                    parts = line.split(b",", 2)
                    if len(parts) < 2:
                        raise RuntimeError(f"CSV_ROW_TOO_SHORT:{name}")
                    ts = parse_epoch(parts[0])
                    if ts is None:
                        continue
                    if ts not in required:
                        continue
                    try:
                        op = float(parts[1].decode("ascii", "strict"))
                    except Exception as ex:
                        raise RuntimeError(f"OPEN_PARSE_FAILURE:{name}:{ts}:{type(ex).__name__}") from ex
                    if not math.isfinite(op) or op <= 0:
                        raise RuntimeError(f"INVALID_OPEN:{name}:{ts}")
                    if ts in opens:
                        duplicate_required.append(ts)
                    opens[ts] = op

    missing = sorted(required - set(opens))
    if missing or duplicate_required:
        result = {
            "lab_id": p["lab_id"],
            "mve_id": p["mve_id"],
            "classification": "SOURCE_OR_EXECUTION_FAILURE",
            "missing_required_price_rows": missing,
            "duplicate_required_price_rows": sorted(set(duplicate_required)),
            "guards": GUARDS,
            "economic_metrics_opened": False,
        }
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    trades = []
    for i, x in enumerate(selected, start=1):
        ent_ts = epoch_iso(x["entry_time_utc"]); ex_ts = epoch_iso(x["exit_time_utc"])
        ent = opens[ent_ts]; ex = opens[ex_ts]
        gross_bps = 10000.0 * (ex / ent - 1.0)
        base = gross_bps - 20.0
        stress = gross_bps - 30.0
        trades.append({
            "trade_id": i,
            "project_numbers": x["project_numbers"],
            "symbols": x["symbols"],
            "signal_time_utc": x["signal_time_utc"],
            "entry_time_utc": x["entry_time_utc"],
            "exit_time_utc": x["exit_time_utc"],
            "entry_open_bnnbtc": ent,
            "exit_open_bnnbtc": ex,
            "gross_bps": gross_bps,
            "base_net_bps": base,
            "stress_net_bps": stress,
            "entry_year_utc": datetime.fromtimestamp(ent_ts, tz=timezone.utc).year,
        })

    base_vals = [x["base_net_bps"] for x in trades]
    stress_vals = [x["stress_net_bps"] for x in trades]
    gross_vals = [x["gross_bps"] for x in trades]
    n = len(trades)

    rng = random.Random(160916)
    boot = []
    for _ in range(5000):
        sample = [base_vals[rng.randrange(n)] for _ in range(n)]
        boot.append(statistics.fmean(sample))
    boot.sort()
    ci_lo = empirical_quantile(boot, 0.025)
    ci_hi = empirical_quantile(boot, 0.975)

    years = defaultdict(list)
    for tr in trades:
        years[tr["entry_year_utc"]].append(tr["base_net_bps"])
    cal = {str(y): {"n": len(v), "base_mean_net_bps": statistics.fmean(v)} for y, v in sorted(years.items())}

    pos_base = [x for x in base_vals if x > 0]
    concentration = (max(pos_base) / sum(pos_base)) if pos_base else None
    base_pf = profit_factor(base_vals)
    stress_pf = profit_factor(stress_vals)
    base_mean = statistics.fmean(base_vals)
    stress_mean = statistics.fmean(stress_vals)
    base_median = statistics.median(base_vals)

    gates = {
        "minimum_resolved_trades": n >= 25,
        "base_mean_net_bps_gt_zero": base_mean > 0,
        "base_profit_factor_gt_one": base_pf > 1,
        "stress_mean_net_bps_gt_zero": stress_mean > 0,
        "stress_profit_factor_gt_one": stress_pf > 1,
        "base_median_net_bps_gt_zero": base_median > 0,
        "bootstrap_95_ci_lower_base_mean_gt_zero": ci_lo > 0,
        "calendar_2023_base_mean_net_gt_zero": mean_or_none(years.get(2023, [])) is not None and statistics.fmean(years[2023]) > 0,
        "calendar_2024_base_mean_net_gt_zero": mean_or_none(years.get(2024, [])) is not None and statistics.fmean(years[2024]) > 0,
        "max_single_trade_share_of_total_positive_base_net_lte_0_40": concentration is not None and concentration <= 0.40,
        "unresolved_execution_paths_zero": True,
        "source_rule_deviations_zero": True,
        "trading_rule_deviations_zero": True,
    }

    if n < 25:
        classification = "INSUFFICIENT_SAMPLE"
    elif all(gates.values()):
        classification = "DISCOVERY_SURVIVES_OOS_ELIGIBLE"
    else:
        classification = "DISCOVERY_FAIL_NO_PROMOTION"

    ledger_obj = {
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "market_source_archive_manifest_sha256": m["archive_manifest_sha256"],
        "trades": trades,
    }
    ledger_bytes = (json.dumps(ledger_obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
    LEDGER.write_bytes(ledger_bytes)
    ledger_sha = hashlib.sha256(ledger_bytes).hexdigest()

    result = {
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "classification": classification,
        "promotion": classification == "DISCOVERY_SURVIVES_OOS_ELIGIBLE",
        "resolved_trades": n,
        "source_binding": {
            "market_source_run_id": 35131193961,
            "market_source_artifact_id": 10460668190,
            "market_source_artifact_zip_sha256": t["market_source_binding"]["artifact_zip_sha256"],
            "archive_manifest_sha256": m["archive_manifest_sha256"],
            "verified_archive_count": len(verified),
        },
        "economics": {
            "gross_mean_bps": statistics.fmean(gross_vals),
            "base_mean_net_bps": base_mean,
            "base_median_net_bps": base_median,
            "base_profit_factor": pf_json(base_pf),
            "base_win_rate": sum(x > 0 for x in base_vals) / n,
            "stress_mean_net_bps": stress_mean,
            "stress_profit_factor": pf_json(stress_pf),
            "stress_win_rate": sum(x > 0 for x in stress_vals) / n,
            "base_total_net_bps": sum(base_vals),
            "stress_total_net_bps": sum(stress_vals),
            "max_single_trade_positive_base_contribution_share": concentration,
        },
        "bootstrap_base_mean_bps": {
            "replications": 5000,
            "seed": 160916,
            "ci95_lower": ci_lo,
            "ci95_upper": ci_hi,
            "median_bootstrap_mean": statistics.median(boot),
        },
        "calendar_base": cal,
        "promotion_gate_checks": gates,
        "failed_promotion_gates": [k for k, v in gates.items() if not v],
        "ledger_sha256": ledger_sha,
        "guards": GUARDS,
        "access_2025": False,
        "access_2026": False,
        "live_trading_authorized": False,
        "next_step_if_pass": "Create a separate pre-outcome 2025 OOS freeze; this Discovery does not authorize 2025 access or live trading.",
        "post_outcome_rescue_allowed": False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "resolved_trades": n,
        "base_mean_net_bps": base_mean,
        "base_median_net_bps": base_median,
        "base_profit_factor": pf_json(base_pf),
        "stress_mean_net_bps": stress_mean,
        "stress_profit_factor": pf_json(stress_pf),
        "bootstrap_ci95": [ci_lo, ci_hi],
        "calendar_base": cal,
        "concentration": concentration,
        "failed_promotion_gates": result["failed_promotion_gates"],
        "ledger_sha256": ledger_sha,
    }, indent=2))

if __name__ == "__main__":
    main()
