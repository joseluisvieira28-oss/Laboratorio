#!/usr/bin/env python3
from __future__ import annotations

import math
import random
from collections import defaultdict

LAB_ID = "ABSORPTION-FAILED-AUCTION-001"
BASELINE = 2016
Q_EXTREME = 0.95
Q_VOLUME = 0.75
Q_LOW = 0.25
Q_HIGH = 0.75
COOLDOWN_BARS = 12
HORIZONS = (5, 15, 30, 60, 240)
MIN_GROUP = 100
MIN_DATES = 30
MIN_COVERAGE = 0.99
BOOT_N = 10000
BOOT_SEED = 20260924


class LabError(ValueError):
    pass


def q(vals, p):
    vals = sorted(v for v in vals if isinstance(v, (int, float)) and math.isfinite(v))
    if not vals:
        return math.nan
    x = (len(vals) - 1) * p
    lo = int(math.floor(x))
    hi = int(math.ceil(x))
    if lo == hi:
        return vals[lo]
    w = x - lo
    return vals[lo] * (1 - w) + vals[hi] * w


def median(vals):
    return q(vals, 0.5)


def wilson_lower(k, n, z=1.959963984540054):
    if n <= 0:
        return math.nan
    ph = k / n
    den = 1 + z * z / n
    centre = ph + z * z / (2 * n)
    adj = z * math.sqrt((ph * (1 - ph) + z * z / (4 * n)) / n)
    return (centre - adj) / den


def validate_structure(row):
    required = (
        "agg_delta_pct",
        "agg_base_volume",
        "ltf_path_efficiency",
        "bar_return_bps",
        "poc_migration_bps",
        "poc_mid",
        "vah",
        "val",
        "buy_imbalance_rows",
        "sell_imbalance_rows",
        "footprint_rows",
        "ltf_intrabars",
    )
    for k in required:
        if k not in row:
            raise LabError(f"missing structural field: {k}")
    if not (row["val"] <= row["poc_mid"] <= row["vah"]):
        raise LabError("VAL/POC/VAH invariant failed")
    if row["buy_imbalance_rows"] < 0 or row["sell_imbalance_rows"] < 0:
        raise LabError("negative imbalance count")
    if row["buy_imbalance_rows"] > row["footprint_rows"] or row["sell_imbalance_rows"] > row["footprint_rows"]:
        raise LabError("imbalance count exceeds footprint rows")
    if not (0 <= row["ltf_intrabars"] <= 5):
        raise LabError("ltf_intrabars outside 0..5")


def classify(rows, parent_pass_bar_close_ms):
    """Outcome-blind event classification.

    rows must be chronological. Any outcome-like R* field is rejected here.
    Bars <= parent_pass_bar_close_ms may seed the rolling baseline but can never
    become events.
    """
    out = []
    cooldown_until_index = -1

    for i, row in enumerate(rows):
        if any(str(k).startswith("R") and str(k)[1:].isdigit() for k in row):
            raise LabError("outcome field present in outcome-blind classifier")
        validate_structure(row)

        rec = dict(row)
        rec["event_class"] = "WARMUP"

        if i < BASELINE:
            out.append(rec)
            continue

        hist = rows[i - BASELINE:i]
        for h in hist:
            validate_structure(h)

        thr_d = q([abs(r["agg_delta_pct"]) for r in hist], Q_EXTREME)
        thr_v = q([r["agg_base_volume"] for r in hist], Q_VOLUME)
        thr_lo = q([r["ltf_path_efficiency"] for r in hist], Q_LOW)
        thr_hi = q([r["ltf_path_efficiency"] for r in hist], Q_HIGH)
        thr_ret = q([abs(r["bar_return_bps"]) for r in hist], Q_LOW)

        rec.update({
            "q95_abs_delta_pct": thr_d,
            "q75_agg_base_volume": thr_v,
            "q25_path_efficiency": thr_lo,
            "q75_path_efficiency": thr_hi,
            "q25_abs_bar_return_bps": thr_ret,
        })

        if row["bar_close_ms"] <= parent_pass_bar_close_ms:
            rec["event_class"] = "PRE_OPEN_BASELINE_ONLY"
            out.append(rec)
            continue

        d = 1 if row["agg_delta_pct"] > 0 else -1 if row["agg_delta_pct"] < 0 else 0
        rec["direction"] = d

        extreme = (
            d != 0
            and abs(row["agg_delta_pct"]) >= thr_d
            and row["agg_base_volume"] >= thr_v
        )
        if not extreme:
            rec["event_class"] = "NON_EXTREME"
            out.append(rec)
            continue

        weak = (
            d * row["bar_return_bps"] <= 0
            or abs(row["bar_return_bps"]) <= thr_ret
        )
        candidate = None
        if (
            row["ltf_path_efficiency"] <= thr_lo
            and d * row["poc_migration_bps"] <= 0
            and weak
        ):
            candidate = "FAILED_AUCTION"
        elif (
            row["ltf_path_efficiency"] >= thr_hi
            and d * row["poc_migration_bps"] > 0
            and d * row["bar_return_bps"] > 0
        ):
            candidate = "EFFICIENT_ACCEPTANCE"
        else:
            rec["event_class"] = "UNCLASSIFIED_EXTREME"
            out.append(rec)
            continue

        if i <= cooldown_until_index:
            rec["event_class"] = "COOLDOWN_SUPPRESSED"
            rec["suppressed_candidate"] = candidate
        else:
            rec["event_class"] = candidate
            cooldown_until_index = i + COOLDOWN_BARS

        out.append(rec)

    return out


def bootstrap_ci(failed, efficient, n=BOOT_N, seed=BOOT_SEED):
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        a = [failed[rng.randrange(len(failed))] for __ in range(len(failed))]
        b = [efficient[rng.randrange(len(efficient))] for __ in range(len(efficient))]
        diffs.append(median(b) - median(a))
    return q(diffs, 0.025), q(diffs, 0.975)


def adjudicate(rows, parent_state, transport_coverage=1.0, unresolved_conflicts=0):
    if parent_state != "PASS_STRONG":
        return {
            "lab_id": LAB_ID,
            "classification": "SENSOR_BLOCKED",
            "parent_state": parent_state,
            "live_trading_authority": "NONE",
        }
    if unresolved_conflicts:
        return {
            "lab_id": LAB_ID,
            "classification": "SOURCE_BLOCKED",
            "reason": "UNRESOLVED_EVIDENCE_CONFLICTS",
            "live_trading_authority": "NONE",
        }
    if transport_coverage < MIN_COVERAGE:
        return {
            "lab_id": LAB_ID,
            "classification": "SOURCE_BLOCKED",
            "reason": "TRANSPORT_COVERAGE_BELOW_99_PERCENT",
            "transport_coverage": transport_coverage,
            "live_trading_authority": "NONE",
        }

    groups = defaultdict(list)
    for r in rows:
        if r.get("event_class") in ("FAILED_AUCTION", "EFFICIENT_ACCEPTANCE"):
            groups[r["event_class"]].append(r)

    fa = groups["FAILED_AUCTION"]
    ea = groups["EFFICIENT_ACCEPTANCE"]
    dates = {r["utc_date"] for r in fa + ea}

    def coverage(group):
        if not group:
            return 0.0
        good = sum(
            1 for r in group
            if isinstance(r.get("R60"), (int, float)) and math.isfinite(r["R60"])
        )
        return good / len(group)

    fa_cov = coverage(fa)
    ea_cov = coverage(ea)

    if (
        len(fa) < MIN_GROUP
        or len(ea) < MIN_GROUP
        or len(dates) < MIN_DATES
        or fa_cov < MIN_COVERAGE
        or ea_cov < MIN_COVERAGE
    ):
        return {
            "lab_id": LAB_ID,
            "classification": "INSUFFICIENT_SAMPLE",
            "failed_auction_n": len(fa),
            "efficient_acceptance_n": len(ea),
            "distinct_utc_dates": len(dates),
            "failed_R60_coverage": fa_cov,
            "efficient_R60_coverage": ea_cov,
            "live_trading_authority": "NONE",
        }

    fa60 = [r["R60"] for r in fa if math.isfinite(r["R60"])]
    ea60 = [r["R60"] for r in ea if math.isfinite(r["R60"])]
    mfa = median(fa60)
    mea = median(ea60)
    lo, hi = bootstrap_ci(fa60, ea60)

    fa_rev = sum(x < 0 for x in fa60)
    ea_cont = sum(x > 0 for x in ea60)
    fa_rate = fa_rev / len(fa60)
    ea_rate = ea_cont / len(ea60)
    fa_wlo = wilson_lower(fa_rev, len(fa60))
    ea_wlo = wilson_lower(ea_cont, len(ea60))

    survive = (
        mfa < 0
        and mea > 0
        and mea - mfa > 0
        and lo > 0
        and fa_rate > 0.5
        and fa_wlo > 0.5
        and ea_rate > 0.5
        and ea_wlo > 0.5
    )

    return {
        "lab_id": LAB_ID,
        "classification": "MECHANISM_SURVIVES" if survive else "NO_MECHANISM",
        "failed_auction_n": len(fa),
        "efficient_acceptance_n": len(ea),
        "distinct_utc_dates": len(dates),
        "failed_R60_coverage": fa_cov,
        "efficient_R60_coverage": ea_cov,
        "failed_median_R60_bps": mfa,
        "efficient_median_R60_bps": mea,
        "median_contrast_R60_bps": mea - mfa,
        "bootstrap95_contrast_bps": [lo, hi],
        "failed_reversal_rate_R60": fa_rate,
        "failed_reversal_wilson_lower95": fa_wlo,
        "efficient_continuation_rate_R60": ea_rate,
        "efficient_continuation_wilson_lower95": ea_wlo,
        "live_trading_authority": "NONE",
    }
