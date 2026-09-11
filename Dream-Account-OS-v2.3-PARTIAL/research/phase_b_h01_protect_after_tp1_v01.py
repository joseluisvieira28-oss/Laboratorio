from __future__ import annotations

"""H01 managed-outcome semantics for synthetic/offline research tests only.

This module does not load market data, access a network, classify H01, unlock a stage,
or submit anything to an exchange. It changes only trade-management outcome semantics
relative to the frozen P00 geometry: after a surviving bar touches TP1 (+1R), a
protective stop at the original entry price becomes active from the NEXT bar.
"""

from typing import Iterable

from dream_account.models import Candle
from research.phase_b_signal_formation_v01 import (
    CostAssumptions,
    SignalGeometry,
    TradeOutcome,
    validate_candles,
)


HYPOTHESIS_ID = "H01_PROTECT_AFTER_TP1_NEXT_BAR"
FAMILY_ID = "PBR02_MANAGED_BREAKOUT_RETEST_LONG"
LIVE_AUTHORIZED = False
VALIDATION_2025_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False


def simulate_h01_managed_outcome(
    signal: SignalGeometry,
    candles: Iterable[Candle],
    costs: CostAssumptions,
    *,
    max_holding_bars: int,
    require_regular_spacing: bool = True,
) -> TradeOutcome:
    """Simulate the frozen H01 management rule on an already-defined P00 signal.

    Frozen H01 semantics:
    - initial stop, TP1, TP2 and max hold are inherited from P00;
    - TP1 is still not a partial exit;
    - a TP1 touch on a bar that survives activates an entry-price protective stop
      only after that bar closes, so the protection is effective from the next bar;
    - if initial stop and TP1/TP2 are touched on the same pre-protection bar, STOP wins;
    - if the active protective stop and TP2 are touched on the same later bar, the
      protective stop wins conservatively;
    - a gap through the active stop exits at the adverse open;
    - entry-price protection is price breakeven, not cost breakeven, so net R is
      negative by the configured round-trip cost when exit_price == entry.

    The function has no data-loader, classifier, network or exchange route.
    """

    costs.validate()
    if not isinstance(max_holding_bars, int) or isinstance(max_holding_bars, bool) or max_holding_bars <= 0:
        raise ValueError("max_holding_bars must be a positive integer")

    series = validate_candles(candles, require_regular_spacing=require_regular_spacing)
    entry_index = next((i for i, candle in enumerate(series) if candle.open_time == signal.entry_open_time), None)
    if entry_index is None:
        raise ValueError("entry candle is missing from series")
    if abs(series[entry_index].open - signal.entry) > max(1e-12, abs(signal.entry) * 1e-12):
        raise ValueError("entry price does not match entry candle open")
    if not (signal.stop < signal.entry < signal.tp1 < signal.tp2):
        raise ValueError("signal has invalid ordered geometry")

    cost_fraction = costs.round_trip_cost_pct / 100.0
    stop_fraction = (signal.entry - signal.stop) / signal.entry
    total_risk_fraction = stop_fraction + cost_fraction
    if stop_fraction <= 0 or total_risk_fraction <= 0:
        raise ValueError("signal has invalid risk geometry")

    def finish(
        reason: str,
        open_time: int,
        price: float,
        bars_held: int,
        tp1_reached: bool,
        ambiguity: bool,
    ) -> TradeOutcome:
        gross_fraction = (price - signal.entry) / signal.entry
        net_r = (gross_fraction - cost_fraction) / total_risk_fraction
        return TradeOutcome(
            setup_fingerprint=signal.fingerprint,
            exit_reason=reason,
            exit_open_time=open_time,
            exit_price=price,
            bars_held=bars_held,
            gross_return_pct=gross_fraction * 100.0,
            net_r=net_r,
            tp1_reached=tp1_reached,
            same_bar_stop_target_ambiguity=ambiguity,
            submitted_to_exchange=False,
        )

    tp1_reached = False
    protective_stop_active = False
    last_index = min(len(series) - 1, entry_index + max_holding_bars - 1)

    for index in range(entry_index, last_index + 1):
        candle = series[index]
        bars_held = index - entry_index + 1
        active_stop = signal.entry if protective_stop_active else signal.stop
        bar_touches_tp1 = candle.open >= signal.tp1 or candle.high >= signal.tp1

        # Opening gaps are resolved before any same-bar high/low inference.
        if candle.open <= active_stop:
            reason = "PROTECTIVE_STOP_GAP" if protective_stop_active else "STOP_GAP"
            return finish(reason, candle.open_time, candle.open, bars_held, tp1_reached, False)
        if candle.open >= signal.tp2:
            return finish("TP2", candle.open_time, signal.tp2, bars_held, True, False)

        stop_hit = candle.low <= active_stop
        target_hit = candle.high >= signal.tp2

        # OHLC cannot resolve path. The active stop wins conservatively whenever both
        # stop and TP2 are inside the same bar.
        if stop_hit and target_hit:
            reason = (
                "PROTECTIVE_STOP_AMBIGUOUS_SAME_BAR"
                if protective_stop_active
                else "STOP_AMBIGUOUS_SAME_BAR"
            )
            return finish(reason, candle.open_time, active_stop, bars_held, tp1_reached, True)
        if stop_hit:
            reason = "PROTECTIVE_STOP" if protective_stop_active else "STOP"
            return finish(reason, candle.open_time, active_stop, bars_held, tp1_reached, False)
        if target_hit:
            return finish("TP2", candle.open_time, signal.tp2, bars_held, True, False)

        # Activation happens only after a surviving TP1-touch bar. Therefore the
        # entry-price protective stop cannot affect the bar that first touches TP1.
        if bar_touches_tp1:
            tp1_reached = True
            protective_stop_active = True

    time_exit_index = entry_index + max_holding_bars
    if time_exit_index >= len(series):
        return TradeOutcome(
            setup_fingerprint=signal.fingerprint,
            exit_reason="UNRESOLVED_END_OF_DATA",
            exit_open_time=None,
            exit_price=None,
            bars_held=max_holding_bars,
            gross_return_pct=None,
            net_r=None,
            tp1_reached=tp1_reached,
            same_bar_stop_target_ambiguity=False,
            submitted_to_exchange=False,
        )

    time_exit = series[time_exit_index]
    return finish(
        "TIME_EXIT_NEXT_OPEN",
        time_exit.open_time,
        time_exit.open,
        max_holding_bars,
        tp1_reached,
        False,
    )
