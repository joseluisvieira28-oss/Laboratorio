"""V0.4.3A outcome-blind Hyperliquid historical funding semantic probe.

This is a semantic-identification remediation only. It expands the fixed
venue-level sample from BTC/ETH to a pre-registered eight-asset panel while
preserving the V0.4.3 windows, candidate formula, clamps, divisors, tolerance,
and pass thresholds. It never computes strategy economics or cross-venue carry.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any

getcontext().prec = 40

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
AMENDMENT_ID = "CROSS_VENUE_FUNDING_BASIS_SEMANTIC_IDENTIFICATION_REMEDIATION_V043A"
HL_INFO = "https://api.hyperliquid.xyz/info"

ASSETS = ("BTC", "ETH", "ARB", "AVAX", "SOL", "MATIC", "LINK", "ATOM")
TOL = Decimal("1e-12")
INTEREST_8H = Decimal("0.0001")
CANDIDATE_CLAMPS = (Decimal("0.0003"), Decimal("0.0005"))
CANDIDATE_DIVISORS = (1, 8)

WINDOWS = {
    "hourly_scale_check": ("2023-09-01T00:00:00Z", "2023-09-07T23:59:59Z"),
    "early_clamp_check": ("2023-12-01T00:00:00Z", "2023-12-11T22:59:59Z"),
    "late_clamp_check": ("2023-12-11T23:00:00Z", "2023-12-22T23:59:59Z"),
}

PARENT_FAILURE = {
    "workflow_run_id": 34725362349,
    "workflow_job_id": 103638429814,
    "head_sha": "b9b940387b81e22b5547e464243c6ef5787908cc",
    "status": "FAIL_CLOSED_SEMANTICS_UNRESOLVED",
}

carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False
cross_venue_rate_comparison_computed = False
price_values_output = False


class ProbeFailure(RuntimeError):
    pass


def _require(ok: bool, msg: str) -> None:
    if not ok:
        raise ProbeFailure(msg)


def _ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def _post_json(url: str, body: dict[str, Any], timeout: int = 30) -> Any:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "cvfb-semantic-v043a"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_hl_window(coin: str, start_iso: str, end_iso: str, max_attempts: int = 4) -> list[dict[str, Any]]:
    body = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": _ms(start_iso),
        "endTime": _ms(end_iso),
    }
    for attempt in range(1, max_attempts + 1):
        try:
            rows = _post_json(HL_INFO, body)
            _require(isinstance(rows, list), f"Hyperliquid {coin}: non-list response")
            return rows
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == max_attempts:
                raise
            time.sleep(15.0)
    raise ProbeFailure(f"Hyperliquid {coin}: retry loop exhausted")


def _dec(x: Any) -> Decimal | None:
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError):
        return None
    if not d.is_finite():
        return None
    return d


def _clamp(x: Decimal, c: Decimal) -> Decimal:
    return min(max(x, -c), c)


def _expected(premium: Decimal, clamp_bound: Decimal, divisor: int) -> Decimal:
    f8 = premium + _clamp(INTEREST_8H - premium, clamp_bound)
    return f8 / Decimal(divisor)


def _semantic_matches(rows: list[dict[str, Any]], clamp_bound: Decimal, divisor: int) -> tuple[int, int]:
    finite = 0
    matches = 0
    for row in rows:
        p = _dec(row.get("premium"))
        f = _dec(row.get("fundingRate"))
        if p is None or f is None:
            continue
        finite += 1
        if abs(f - _expected(p, clamp_bound, divisor)) <= TOL:
            matches += 1
    return matches, finite


def _discriminating_clamp_counts(rows: list[dict[str, Any]], divisor: int = 8) -> dict[str, int]:
    old_c, new_c = CANDIDATE_CLAMPS
    out = {
        "discriminating_rows": 0,
        "old_clamp_matches": 0,
        "new_clamp_matches": 0,
        "neither_matches": 0,
    }
    for row in rows:
        p = _dec(row.get("premium"))
        f = _dec(row.get("fundingRate"))
        if p is None or f is None:
            continue
        e_old = _expected(p, old_c, divisor)
        e_new = _expected(p, new_c, divisor)
        if abs(e_old - e_new) <= TOL:
            continue
        out["discriminating_rows"] += 1
        old_match = abs(f - e_old) <= TOL
        new_match = abs(f - e_new) <= TOL
        if old_match:
            out["old_clamp_matches"] += 1
        if new_match:
            out["new_clamp_matches"] += 1
        if not old_match and not new_match:
            out["neither_matches"] += 1
    return out


def _ratio(n: int, d: int) -> float:
    return 0.0 if d == 0 else n / d


def classify_semantics(fetched: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    scale_rows = fetched["hourly_scale_check"]
    scale_candidates: dict[str, dict[str, Any]] = {}
    for c in CANDIDATE_CLAMPS:
        for divisor in CANDIDATE_DIVISORS:
            matches, finite = _semantic_matches(scale_rows, c, divisor)
            key = f"clamp_{c}_divisor_{divisor}"
            scale_candidates[key] = {
                "matches": matches,
                "finite_rows": finite,
                "match_ratio": _ratio(matches, finite),
            }

    best_div8 = max(v["match_ratio"] for k, v in scale_candidates.items() if k.endswith("divisor_8"))
    best_div1 = max(v["match_ratio"] for k, v in scale_candidates.items() if k.endswith("divisor_1"))
    hourly_scale_pass = best_div8 >= 0.95 and best_div8 >= best_div1 + 0.50

    early = _discriminating_clamp_counts(fetched["early_clamp_check"])
    late = _discriminating_clamp_counts(fetched["late_clamp_check"])
    early_ratio = _ratio(early["old_clamp_matches"], early["discriminating_rows"])
    late_ratio = _ratio(late["new_clamp_matches"], late["discriminating_rows"])

    clamp_transition_pass = (
        early["discriminating_rows"] >= 10
        and late["discriminating_rows"] >= 10
        and early_ratio >= 0.75
        and late_ratio >= 0.75
        and early["old_clamp_matches"] > early["new_clamp_matches"]
        and late["new_clamp_matches"] > late["old_clamp_matches"]
    )

    return {
        "scale_candidate_match_summary": scale_candidates,
        "best_divisor_8_match_ratio": best_div8,
        "best_divisor_1_match_ratio": best_div1,
        "hourly_scale_pass": hourly_scale_pass,
        "detected_scale_label": "HOURLY_ONE_EIGHTH_OF_8H_FORMULA" if hourly_scale_pass else "UNRESOLVED",
        "early_clamp_discriminating_summary": early,
        "late_clamp_discriminating_summary": late,
        "early_clamp_match_ratio": early_ratio,
        "late_clamp_match_ratio": late_ratio,
        "clamp_transition_pass": clamp_transition_pass,
        "detected_clamp_regime": (
            "0.0003_BEFORE_2023-12-11T23Z__0.0005_AT_AND_AFTER"
            if clamp_transition_pass
            else "UNRESOLVED"
        ),
        "semantic_probe_pass": hourly_scale_pass and clamp_transition_pass,
    }


def run() -> dict[str, Any]:
    fetched: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, dict[str, int]] = {}
    for name, (start, end) in WINDOWS.items():
        rows_all: list[dict[str, Any]] = []
        counts[name] = {}
        for coin in ASSETS:
            rows = _fetch_hl_window(coin, start, end)
            counts[name][coin] = len(rows)
            rows_all.extend(rows)
            time.sleep(1.0)
        fetched[name] = rows_all

    semantic = classify_semantics(fetched)
    passed = semantic["semantic_probe_pass"]
    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "amendment_id": AMENDMENT_ID,
        "status": "PASS_SEMANTIC_IDENTIFICATION" if passed else "FAIL_CLOSED_SEMANTICS_UNRESOLVED",
        "parent_failure_preserved": PARENT_FAILURE,
        "classification": "SEMANTIC_PROBE_ONLY_NOT_STRATEGY_ECONOMICS",
        "fixed_assets": list(ASSETS),
        "fixed_windows": WINDOWS,
        "row_counts_by_window_and_asset": counts,
        "hyperliquid_funding_semantics": semantic,
        "gate_interpretation": {
            "G03": "SEMANTIC_COMPONENT_PASS" if passed else "FAIL_CLOSED_SEMANTICS_UNRESOLVED",
            "G04": "BLOCKED_HYPERLIQUID_ASSET_CTX_PENDING",
            "G10": "PROVISIONAL_ONLY_NOT_MATERIALIZED",
            "G12": "BLOCKED",
        },
        "raw_values_output": False,
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "cross_venue_rate_comparison_computed": False,
        "price_values_output": False,
        "discovery_authorized": False,
        "trading_authorized": False,
    }


def main() -> int:
    path = Path(os.environ.get("PREFREEZE_V043A_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_V043A_RECEIPT.json"))
    result = run()
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sem = result["hyperliquid_funding_semantics"]
    print(json.dumps({
        "status": result["status"],
        "semantic_probe_pass": sem["semantic_probe_pass"],
        "hourly_scale_pass": sem["hourly_scale_pass"],
        "clamp_transition_pass": sem["clamp_transition_pass"],
        "early_discriminating_rows": sem["early_clamp_discriminating_summary"]["discriminating_rows"],
        "late_discriminating_rows": sem["late_clamp_discriminating_summary"]["discriminating_rows"],
        "receipt": str(path),
    }, sort_keys=True))
    return 0 if result["status"] == "PASS_SEMANTIC_IDENTIFICATION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
