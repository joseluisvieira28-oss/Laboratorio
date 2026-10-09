"""Frozen MRCR H02 decision-time classifier.

No future outcomes, PnL or trading actions are accepted by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ACCEPTANCE = "ACCEPTANCE"
REJECTION = "REJECTION"
ABSTAIN = "ABSTAIN"

EXPECTED_VENUES = ("BINANCE_SPOT", "COINBASE_ADVANCED_SPOT")

MIN_DISPLACEMENT_IN_PRE_SPREADS = 1.0
MAX_SPREAD_VS_MAX_TO_DECISION = 0.5
MAX_ACCEPTANCE_RETRACEMENT = 0.5
MAX_ACCEPTANCE_RESISTANCE_DEPTH = 1.0


@dataclass(frozen=True)
class VenueClassification:
    state: str
    direction: int | None
    reason: str
    directional_resistance_depth_vs_pre: float | None


@dataclass(frozen=True)
class AssetClassification:
    state: str
    direction: int | None
    reason: str


def _number(state: Mapping[str, float | None], key: str) -> float | None:
    value = state.get(key)
    if value is None:
        return None
    return float(value)


def classify_venue_state(
    state: Mapping[str, float | None],
) -> VenueClassification:
    flow = _number(state, "flow_imbalance")
    ret = _number(state, "decision_return_bps")
    displacement = _number(state, "displacement_in_pre_spreads")
    alignment = _number(state, "alignment_sign")
    retracement = _number(state, "retracement_fraction")
    spread_vs_max = _number(state, "spread_vs_max_to_decision")
    bid_depth = _number(state, "bid_depth_vs_pre")
    ask_depth = _number(state, "ask_depth_vs_pre")

    if flow is None or flow == 0:
        return VenueClassification(ABSTAIN, None, "NO_DIRECTIONAL_FLOW", None)
    direction = 1 if flow > 0 else -1

    if ret is None or ret == 0:
        return VenueClassification(ABSTAIN, direction, "NO_DECISION_DISPLACEMENT", None)
    if displacement is None or displacement < MIN_DISPLACEMENT_IN_PRE_SPREADS:
        return VenueClassification(ABSTAIN, direction, "DISPLACEMENT_BELOW_ONE_PRE_SPREAD", None)
    if spread_vs_max is None or spread_vs_max > MAX_SPREAD_VS_MAX_TO_DECISION:
        return VenueClassification(ABSTAIN, direction, "SPREAD_NOT_RECOVERED_HALF_FROM_MAX", None)
    if retracement is None:
        return VenueClassification(ABSTAIN, direction, "RETRACEMENT_UNDEFINED", None)

    resistance_depth = ask_depth if direction > 0 else bid_depth
    if resistance_depth is None:
        return VenueClassification(ABSTAIN, direction, "DIRECTIONAL_DEPTH_UNDEFINED", None)

    if (
        alignment == 1.0
        and retracement < MAX_ACCEPTANCE_RETRACEMENT
        and resistance_depth < MAX_ACCEPTANCE_RESISTANCE_DEPTH
    ):
        return VenueClassification(
            ACCEPTANCE,
            direction,
            "ALIGNED_LOW_RETRACEMENT_INCOMPLETE_RESISTANCE_REPLENISHMENT",
            resistance_depth,
        )

    if alignment == -1.0:
        return VenueClassification(
            REJECTION,
            direction,
            "FLOW_PRICE_OPPOSITION",
            resistance_depth,
        )

    if (
        alignment == 1.0
        and retracement >= MAX_ACCEPTANCE_RETRACEMENT
        and resistance_depth >= MAX_ACCEPTANCE_RESISTANCE_DEPTH
    ):
        return VenueClassification(
            REJECTION,
            direction,
            "ALIGNED_BUT_RETRACED_AND_RESISTANCE_REPLENISHED",
            resistance_depth,
        )

    return VenueClassification(
        ABSTAIN,
        direction,
        "MIXED_RESPONSE_STATE",
        resistance_depth,
    )


def confirm_cross_venue_state(
    by_venue: Mapping[str, VenueClassification],
) -> AssetClassification:
    if set(by_venue) != set(EXPECTED_VENUES):
        return AssetClassification(ABSTAIN, None, "MISSING_OR_EXTRA_VENUE")

    first = by_venue[EXPECTED_VENUES[0]]
    second = by_venue[EXPECTED_VENUES[1]]

    if first.state not in {ACCEPTANCE, REJECTION}:
        return AssetClassification(ABSTAIN, None, "BINANCE_NOT_CLASSIFIED")
    if second.state not in {ACCEPTANCE, REJECTION}:
        return AssetClassification(ABSTAIN, None, "COINBASE_NOT_CLASSIFIED")
    if first.state != second.state:
        return AssetClassification(ABSTAIN, None, "CROSS_VENUE_STATE_DISAGREEMENT")
    if first.direction != second.direction:
        return AssetClassification(ABSTAIN, None, "CROSS_VENUE_DIRECTION_DISAGREEMENT")

    return AssetClassification(
        first.state,
        first.direction,
        "CROSS_VENUE_CONFIRMED",
    )
