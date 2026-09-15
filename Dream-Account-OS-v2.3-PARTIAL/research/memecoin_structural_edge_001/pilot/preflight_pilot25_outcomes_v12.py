#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

EXPECTED_V11_MANIFEST_SHA256 = "ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8"
EXPECTED_MATRIX_SHA256 = "226c64d9683702e81c5f2b2b871b4d8971e761914c999a0d2e6c257328005d72"
EXPECTED_RISK_ORDER_SHA256 = "5857267a7d0203fa0e8e70eeafc34017d225a84a7809c97accce8bbb76f7fb8e"
HISTORICAL_IDL_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMPSWAP_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
PUMPSWAP_IDL_GIT_BLOB = "7a1cf37270f6015f5af53b9ce58d8a6890254020"
ENTRY_FRESHNESS_SECONDS = 60
MIN_QUOTE_LAMPORTS = 10_000_000
OUTCOME_WINDOWS = [900, 3600, 21600, 86400]
ROUNDTRIP_STRESS = 0.03


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))

def load_jsonl(p: pathlib.Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def write_json(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    d11 = here / "data" / "msel001_pilot25_feature_v11"
    manp = d11 / "pilot25_feature_manifest_v11.json"
    mp = d11 / "pilot25_feature_matrix_v11.jsonl"
    rp = d11 / "pilot25_primary_risk_order_v11.jsonl"
    for p in (manp, mp, rp):
        if not p.exists():
            raise RuntimeError(f"MISSING_V11_INPUT {p}")
    if sha(manp) != EXPECTED_V11_MANIFEST_SHA256:
        raise RuntimeError("V11_MANIFEST_HASH_MISMATCH")
    m = load_json(manp)
    if m.get("outcomes_opened") is not False:
        raise RuntimeError("V11_OUTCOME_LOCK_FAILURE")
    if m.get("feature_matrix_sha256") != EXPECTED_MATRIX_SHA256 or sha(mp) != EXPECTED_MATRIX_SHA256:
        raise RuntimeError("V11_MATRIX_HASH_MISMATCH")
    if m.get("risk_order_sha256") != EXPECTED_RISK_ORDER_SHA256 or sha(rp) != EXPECTED_RISK_ORDER_SHA256:
        raise RuntimeError("V11_RISK_ORDER_HASH_MISMATCH")
    matrix = load_jsonl(mp)
    order = load_jsonl(rp)
    if len(matrix) != 25 or len(order) != 25:
        raise RuntimeError(f"V11_ROW_COUNT_FAILURE {len(matrix)}/{len(order)}")
    if any(r.get("outcomes_opened") is not False for r in matrix):
        raise RuntimeError("V11_ROW_OUTCOME_LOCK_FAILURE")

    out_dir = here / "data" / "msel001_pilot25_outcomes_v12"
    forbidden = [
        out_dir / "pilot25_outcomes_v12.jsonl",
        out_dir / "pilot25_outcome_events_v12.jsonl",
        out_dir / "pilot25_outcome_manifest_v12.json",
    ]
    existing = [str(p) for p in forbidden if p.exists()]
    if existing:
        raise RuntimeError(f"OUTCOME_ARTIFACT_ALREADY_EXISTS {existing}")

    preflight = {
        "artifact": "MSEL_PILOT25_OUTCOME_PREFLIGHT_V12",
        "pilot_only": True,
        "full_mve_verdict_authorized": False,
        "source_v11_manifest_sha256": EXPECTED_V11_MANIFEST_SHA256,
        "source_feature_matrix_sha256": EXPECTED_MATRIX_SHA256,
        "source_risk_order_sha256": EXPECTED_RISK_ORDER_SHA256,
        "historical_idl_commit": HISTORICAL_IDL_COMMIT,
        "pump_program": PUMP_PROGRAM,
        "pumpswap_program": PUMPSWAP_PROGRAM,
        "historical_pumpswap_idl_git_blob": PUMPSWAP_IDL_GIT_BLOB,
        "decision_horizon_seconds": 300,
        "entry_freshness_seconds": ENTRY_FRESHNESS_SECONDS,
        "min_quote_lamports": MIN_QUOTE_LAMPORTS,
        "future_windows_seconds": OUTCOME_WINDOWS,
        "catastrophic_threshold": -0.80,
        "winner_threshold": 1.00,
        "roundtrip_cost_stress": ROUNDTRIP_STRESS,
        "primary_future_side": "SELL_ONLY",
        "buy_only_spike_counts_as_winner": False,
        "no_valid_sell_with_complete_24h_coverage_is_liquidity_catastrophe": True,
        "outcomes_opened": False,
    }
    pp = d11 / "pilot25_outcome_preflight_v12.json"
    psha = write_json(pp, preflight)

    print("PASS: Pilot25 outcome preflight V12 complete")
    print("V11 rows: 25")
    print("entry freshness seconds: 60")
    print("minimum quote notional: 0.01 SOL")
    print("future windows seconds: 900/3600/21600/86400")
    print("primary future evidence: SELL executions only")
    print("catastrophe/winner thresholds: -80% / +100%")
    print("secondary round-trip stress: 3.00%")
    print(f"preflight sha256: {psha}")
    print("NO OUTCOME DATA READ")
    print("OUTCOMES REMAIN LOCKED")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
