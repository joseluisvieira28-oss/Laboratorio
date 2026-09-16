from __future__ import annotations

from dataclasses import dataclass

from radar.models import Direction


CFTC_CONTRACT_CODE = "133741"
INFORMATION_LAG_DAYS = 8
HOLD_DAYS = 7
BASE_COST_BPS_ROUND_TRIP = 10
STRESS_COST_BPS_ROUND_TRIP = 20


@dataclass(frozen=True)
class CFTCObservation:
    as_of_date: str
    open_interest: float
    noncommercial_long: float
    noncommercial_short: float

    @property
    def net_noncommercial(self) -> float:
        return self.noncommercial_long - self.noncommercial_short


@dataclass(frozen=True)
class FrozenSignal:
    strategy_id: str
    contract_code: str
    predecessor_as_of_date: str
    as_of_date: str
    signal_value: float
    direction: Direction
    information_lag_days: int
    hold_days: int
    base_cost_bps_round_trip: int
    stress_cost_bps_round_trip: int


STRATEGY_ID = "ETF-CME-INSTFLOW-001"


def compute_frozen_signal(
    previous: CFTCObservation,
    current: CFTCObservation,
) -> FrozenSignal:
    """Reproduce the prospectively frozen MVE signal only.

    signal = delta(noncommercial_long - noncommercial_short) / current open interest
    positive -> LONG BTC; negative -> SHORT BTC; zero -> FLAT.

    This function intentionally contains no threshold, z-score, volatility filter,
    regime filter, price filter, ETF filter, basis filter, sizing or order logic.
    """

    if current.open_interest <= 0:
        raise ValueError("current open_interest must be > 0")

    delta_net = current.net_noncommercial - previous.net_noncommercial
    signal_value = delta_net / current.open_interest

    if signal_value > 0:
        direction = Direction.LONG
    elif signal_value < 0:
        direction = Direction.SHORT
    else:
        direction = Direction.NONE

    return FrozenSignal(
        strategy_id=STRATEGY_ID,
        contract_code=CFTC_CONTRACT_CODE,
        predecessor_as_of_date=previous.as_of_date,
        as_of_date=current.as_of_date,
        signal_value=signal_value,
        direction=direction,
        information_lag_days=INFORMATION_LAG_DAYS,
        hold_days=HOLD_DAYS,
        base_cost_bps_round_trip=BASE_COST_BPS_ROUND_TRIP,
        stress_cost_bps_round_trip=STRESS_COST_BPS_ROUND_TRIP,
    )
