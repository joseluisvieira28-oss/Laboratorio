import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_classifier import (
    ACCEPTANCE,
    REJECTION,
    ABSTAIN,
    classify_venue_state,
    confirm_cross_venue_state,
)


def state(**overrides):
    row = {
        "flow_imbalance": 0.4,
        "decision_return_bps": 12.0,
        "displacement_in_pre_spreads": 2.0,
        "alignment_sign": 1.0,
        "retracement_fraction": 0.2,
        "spread_vs_max_to_decision": 0.4,
        "bid_depth_vs_pre": 0.8,
        "ask_depth_vs_pre": 0.7,
    }
    row.update(overrides)
    return row


class H02ClassifierTests(unittest.TestCase):
    def test_classifier_spec_fingerprint_and_constants_match(self):
        spec_path = MODULE_DIR / "H02_CLASSIFIER_SPEC_V01.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        claimed = spec["spec_sha256"]
        spec["spec_sha256"] = None
        canonical = json.dumps(
            spec,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            claimed,
        )
        from h02_classifier import (
            MIN_DISPLACEMENT_IN_PRE_SPREADS,
            MAX_SPREAD_VS_MAX_TO_DECISION,
            MAX_ACCEPTANCE_RETRACEMENT,
            MAX_ACCEPTANCE_RESISTANCE_DEPTH,
        )
        self.assertEqual(
            MIN_DISPLACEMENT_IN_PRE_SPREADS,
            spec["quality_gates"]["min_displacement_in_pre_spreads"],
        )
        self.assertEqual(
            MAX_SPREAD_VS_MAX_TO_DECISION,
            spec["quality_gates"]["max_spread_vs_max_to_decision"],
        )
        self.assertEqual(
            MAX_ACCEPTANCE_RETRACEMENT,
            spec["acceptance"]["retracement_fraction_lt"],
        )
        self.assertEqual(
            MAX_ACCEPTANCE_RESISTANCE_DEPTH,
            spec["acceptance"]["directional_resistance_depth_vs_pre_lt"],
        )

    def test_acceptance_long(self):
        out = classify_venue_state(state())
        self.assertEqual(out.state, ACCEPTANCE)
        self.assertEqual(out.direction, 1)
        self.assertAlmostEqual(out.directional_resistance_depth_vs_pre, 0.7)

    def test_acceptance_short_uses_bid_resistance(self):
        out = classify_venue_state(state(
            flow_imbalance=-0.4,
            decision_return_bps=-12.0,
            bid_depth_vs_pre=0.6,
            ask_depth_vs_pre=1.4,
        ))
        self.assertEqual(out.state, ACCEPTANCE)
        self.assertEqual(out.direction, -1)
        self.assertAlmostEqual(out.directional_resistance_depth_vs_pre, 0.6)

    def test_flow_price_opposition_is_rejection(self):
        out = classify_venue_state(state(alignment_sign=-1.0))
        self.assertEqual(out.state, REJECTION)

    def test_retraced_and_replenished_is_rejection(self):
        out = classify_venue_state(state(
            retracement_fraction=0.5,
            ask_depth_vs_pre=1.0,
        ))
        self.assertEqual(out.state, REJECTION)

    def test_sub_spread_displacement_abstains(self):
        out = classify_venue_state(state(displacement_in_pre_spreads=0.99))
        self.assertEqual(out.state, ABSTAIN)

    def test_unrecovered_spread_abstains(self):
        out = classify_venue_state(state(spread_vs_max_to_decision=0.51))
        self.assertEqual(out.state, ABSTAIN)

    def test_cross_venue_requires_same_state_and_direction(self):
        a = classify_venue_state(state())
        b = classify_venue_state(state())
        confirmed = confirm_cross_venue_state({
            "BINANCE_SPOT": a,
            "COINBASE_ADVANCED_SPOT": b,
        })
        self.assertEqual(confirmed.state, ACCEPTANCE)
        self.assertEqual(confirmed.direction, 1)

        rejected = confirm_cross_venue_state({
            "BINANCE_SPOT": a,
            "COINBASE_ADVANCED_SPOT": classify_venue_state(
                state(alignment_sign=-1.0)
            ),
        })
        self.assertEqual(rejected.state, ABSTAIN)


if __name__ == "__main__":
    unittest.main()
