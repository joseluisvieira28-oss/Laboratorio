from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FINAL_PROV = ROOT / "NEWS_SHOCK_LAB_V03A_FINAL_CONSENSUS_PROVENANCE_FREEZE_V0.1.json"
PREDISC = ROOT / "NEWS_SHOCK_LAB_V03A_PRE_DISCOVERY_SIGNAL_STATISTICAL_FREEZE_V0.1.json"


def canonical_fingerprint(doc: dict) -> str:
    payload = dict(doc)
    payload.pop("fingerprint", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_and_verify(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    expected = doc.get("fingerprint")
    actual = canonical_fingerprint(doc)
    if expected != actual:
        raise SystemExit(f"FINGERPRINT_MISMATCH {path.name}: expected={expected} actual={actual}")
    return doc


def fail(message: str) -> None:
    raise SystemExit(f"NEWS_SHOCK_V03A_PREDISCOVERY_GATE_FAIL: {message}")


def main() -> int:
    final_prov = load_and_verify(FINAL_PROV)
    pre = load_and_verify(PREDISC)

    if final_prov["status"] != "FROZEN_FINAL_PRE_OUTCOME_CORPUS_35_COMPLETE_A_9_INCOMPLETE":
        fail("final provenance status drift")
    corpus = final_prov["corpus"]
    if (corpus["events_total"], corpus["complete_a_count"], corpus["incomplete_count"], corpus["complete_b_count"]) != (44, 35, 9, 0):
        fail("final corpus count drift")
    if len(corpus["complete_a_event_ids"]) != 35 or len(corpus["frozen_incomplete_exclusions"]) != 9:
        fail("event list count drift")
    if set(corpus["complete_a_event_ids"]) & set(corpus["frozen_incomplete_exclusions"]):
        fail("complete and incomplete event overlap")
    if not final_prov["bounded_stop_rule"]["provenance_sweep_closed_for_v03a_discovery"]:
        fail("provenance sweep not closed")
    if not final_prov["bounded_stop_rule"]["do_not_chase_44_of_44"]:
        fail("bounded stop rule drift")
    for key, value in final_prov["governance"].items():
        if value is not False:
            fail(f"pre-outcome governance drift: {key}")

    if pre["bindings"]["final_provenance_freeze_fingerprint"] != final_prov["fingerprint"]:
        fail("pre-discovery freeze not bound to final provenance")
    if pre["status"] != "FROZEN_PRE_OUTCOME_DISCOVERY_CONTRACT":
        fail("pre-discovery status drift")

    discovery = pre["partitions"]["discovery"]
    validation = pre["partitions"]["validation"]
    d_ids = discovery["event_ids"]
    v_ids = validation["event_ids"]
    if discovery["event_count"] != 27 or len(d_ids) != 27:
        fail("discovery partition count drift")
    if validation["event_count"] != 8 or len(v_ids) != 8:
        fail("validation partition count drift")
    if set(d_ids) & set(v_ids):
        fail("discovery-validation overlap")
    if set(d_ids) | set(v_ids) != set(corpus["complete_a_event_ids"]):
        fail("partitions do not exactly cover COMPLETE_A corpus")
    if any(not event_id.startswith(("US_CPI_2022-", "US_CPI_2023-", "US_CPI_2024-")) for event_id in d_ids):
        fail("discovery contains non-2022-2024 event")
    if any(not event_id.startswith("US_CPI_2025-") for event_id in v_ids):
        fail("validation contains non-2025 event")
    if discovery["market_outcomes_authorized_by_this_document"] is not False:
        fail("freeze self-authorized market outcomes")

    signal = pre["signal_freeze"]
    if signal["magnitude_threshold"] != "NONE":
        fail("unexpected surprise threshold")
    if signal["return_based_thresholds_forbidden"] is not True:
        fail("return-based thresholds not forbidden")
    if signal["full_sample_standardization_forbidden"] is not True:
        fail("full-sample standardization guard drift")
    if signal["signed_direction_multiplier"] != {"COOL": 1, "HOT": -1, "NEUTRAL": 0}:
        fail("direction mapping drift")

    market = pre["market_data_freeze"]
    if market["symbols"] != ["BTCUSDT", "ETHUSDT"]:
        fail("symbol drift")
    if market["primary_horizon_minutes"] != 15:
        fail("primary horizon drift")
    if market["release_candle"].startswith("08:30") is False:
        fail("release candle policy missing")

    stats = pre["statistics_freeze"]
    primary = stats["primary_hypothesis"]
    if primary["alpha"] != 0.05 or primary["permutations"] != 100000 or primary["random_seed"] != 20260912:
        fail("primary statistical contract drift")
    if pre["economic_screen"]["round_trip_cost_bps"] != 20:
        fail("primary cost haircut drift")

    before = pre["sequential_access_policy"]["before_gate_pass"]
    if any(before.values()):
        fail("outcome partition opened before gate")
    after = pre["sequential_access_policy"]["after_prediscovery_gate_pass"]
    if after["discovery_2022_2024_market_outcomes"] is not True:
        fail("discovery not authorized after gate")
    for key in ("validation_2025_01_through_2025_08_market_outcomes", "mexc_2025_09_through_2025_12", "holdout_2026"):
        if after[key] is not False:
            fail(f"protected partition opened after gate: {key}")

    gov = pre["governance"]
    for key in (
        "research_only",
        "no_tuning_after_outcomes",
        "no_cherry_picking",
        "no_live_trading",
        "no_exchange_mutation",
        "no_main_merge",
        "no_render_deployment",
        "mexc_2025_09_through_2025_12_locked",
        "holdout_2026_locked",
        "no_outcome_based_event_symbol_window_or_threshold_selection",
    ):
        if gov[key] is not True:
            fail(f"governance guard drift: {key}")

    receipt = {
        "document_type": "NEWS_SHOCK_LAB_V03A_PREDISCOVERY_GATE_RECEIPT_V0.1",
        "status": "PASS",
        "final_provenance_fingerprint": final_prov["fingerprint"],
        "prediscovery_contract_fingerprint": pre["fingerprint"],
        "corpus_counts": {"total": 44, "complete_a": 35, "incomplete": 9, "complete_b": 0},
        "partitions": {"discovery_2022_2024": 27, "validation_2025_01_2025_08": 8},
        "authorized_after_pass": "DISCOVERY_2022_2024_MARKET_OUTCOMES_ONLY",
        "still_locked": ["VALIDATION_2025_01_THROUGH_2025_08", "MEXC_2025_09_THROUGH_2025_12", "HOLDOUT_2026"],
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
    }

    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("NEWS SHOCK V0.3A PRE-DISCOVERY GATE PASS")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
