#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — Discovery core, PREP-ONLY.

Pure deterministic functions implementing the frozen Discovery math:
- instrument-level median IV
- side-level median IV
- CALL_IV - PUT_IV skew
- t -> t+1/t+2 BTC daily outcome alignment
- sign strategy with frozen 10/20 bps costs
- OLS beta with Newey-West/HAC(7) covariance
- frozen MVE-0 gate diagnostics

This module performs NO network access, NO file discovery, NO exchange actions,
and contains no automatic Discovery execution path.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import median
from typing import Iterable, Mapping, Sequence

HAC_LAGS = 7
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
MIN_DISTINCT_PER_SIDE = 5
MIN_VALID_DAYS = 500


@dataclass(frozen=True)
class EligibleTrade:
    day: str
    instrument: str
    side: str
    iv: float


@dataclass(frozen=True)
class DailySignal:
    day: str
    call_iv: float
    put_iv: float
    skew: float
    call_instruments: int
    put_instruments: int


@dataclass(frozen=True)
class AlignedObservation:
    day: str
    skew: float
    forward_log_return: float
    year: int


def _finite_positive(x: float) -> bool:
    return math.isfinite(x) and x > 0


def construct_daily_signals(
    trades: Iterable[EligibleTrade],
    min_distinct_per_side: int = MIN_DISTINCT_PER_SIDE,
) -> list[DailySignal]:
    by_day_instrument: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for t in trades:
        if t.side not in {"C", "P"}:
            raise ValueError(f"invalid side: {t.side}")
        if not _finite_positive(float(t.iv)):
            raise ValueError(f"invalid IV for {t.instrument}: {t.iv}")
        date.fromisoformat(t.day)
        by_day_instrument[(t.day, t.side, t.instrument)].append(float(t.iv))

    inst_daily: dict[tuple[str, str], list[float]] = defaultdict(list)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for (day, side, instrument), ivs in by_day_instrument.items():
        inst_daily[(day, side)].append(float(median(ivs)))
        counts[(day, side)] += 1

    days = sorted({day for day, _, _ in by_day_instrument})
    out: list[DailySignal] = []
    for day in days:
        nc = counts[(day, "C")]
        np = counts[(day, "P")]
        if nc < min_distinct_per_side or np < min_distinct_per_side:
            continue
        call_iv = float(median(inst_daily[(day, "C")]))
        put_iv = float(median(inst_daily[(day, "P")]))
        out.append(
            DailySignal(
                day=day,
                call_iv=call_iv,
                put_iv=put_iv,
                skew=call_iv - put_iv,
                call_instruments=nc,
                put_instruments=np,
            )
        )
    return out


def align_daily_outcomes(
    signals: Sequence[DailySignal],
    btc_open_utc: Mapping[str, float],
) -> list[AlignedObservation]:
    from datetime import timedelta

    out: list[AlignedObservation] = []
    for s in signals:
        d = date.fromisoformat(s.day)
        entry_day = (d + timedelta(days=1)).isoformat()
        exit_day = (d + timedelta(days=2)).isoformat()
        if entry_day not in btc_open_utc or exit_day not in btc_open_utc:
            continue
        entry = float(btc_open_utc[entry_day])
        exit_ = float(btc_open_utc[exit_day])
        if not (_finite_positive(entry) and _finite_positive(exit_)):
            raise ValueError(f"invalid BTC open for {s.day}")
        ret = math.log(exit_ / entry)
        out.append(
            AlignedObservation(
                day=s.day,
                skew=float(s.skew),
                forward_log_return=ret,
                year=d.year,
            )
        )
    return out


def _inv2(a: float, b: float, c: float, d: float) -> tuple[tuple[float, float], tuple[float, float]]:
    det = a * d - b * c
    if abs(det) < 1e-18:
        raise ValueError("singular 2x2 matrix")
    return ((d / det, -b / det), (-c / det, a / det))


def hac_regression_beta(
    obs: Sequence[AlignedObservation],
    lags: int = HAC_LAGS,
) -> dict[str, float]:
    n = len(obs)
    if n < 3:
        raise ValueError("need at least 3 observations")
    x = [float(o.skew) for o in obs]
    y = [float(o.forward_log_return) for o in obs]
    if any(not math.isfinite(v) for v in x + y):
        raise ValueError("non-finite regression input")

    sx = sum(x)
    sxx = sum(v * v for v in x)
    sy = sum(y)
    sxy = sum(a * b for a, b in zip(x, y))
    inv = _inv2(float(n), sx, sx, sxx)
    alpha = inv[0][0] * sy + inv[0][1] * sxy
    beta = inv[1][0] * sy + inv[1][1] * sxy
    resid = [yy - alpha - beta * xx for xx, yy in zip(x, y)]

    score = [(u, xx * u) for xx, u in zip(x, resid)]
    s00 = sum(a * a for a, _ in score)
    s01 = sum(a * b for a, b in score)
    s11 = sum(b * b for _, b in score)

    max_lag = min(int(lags), n - 1)
    for lag in range(1, max_lag + 1):
        w = 1.0 - lag / (max_lag + 1.0)
        g00 = g01 = g10 = g11 = 0.0
        for t in range(lag, n):
            a0, a1 = score[t]
            b0, b1 = score[t - lag]
            g00 += a0 * b0
            g01 += a0 * b1
            g10 += a1 * b0
            g11 += a1 * b1
        s00 += w * (g00 + g00)
        s01 += w * (g01 + g10)
        s11 += w * (g11 + g11)

    i00, i01 = inv[0]
    i10, i11 = inv[1]
    m10 = i10 * s00 + i11 * s01
    m11 = i10 * s01 + i11 * s11
    var_beta = m10 * i01 + m11 * i11
    if var_beta < -1e-15:
        raise ValueError(f"negative HAC variance: {var_beta}")
    se_beta = math.sqrt(max(var_beta, 0.0))
    if se_beta == 0:
        z = math.inf if beta > 0 else (-math.inf if beta < 0 else 0.0)
    else:
        z = beta / se_beta
    one_sided_p = 0.5 * math.erfc(z / math.sqrt(2.0))

    return {
        "n": float(n),
        "alpha": alpha,
        "beta": beta,
        "hac_lags": float(max_lag),
        "se_beta_hac": se_beta,
        "z_beta": z,
        "one_sided_p_beta_gt_0": one_sided_p,
    }


def strategy_metrics(
    obs: Sequence[AlignedObservation],
    cost_bps: float,
) -> dict[str, object]:
    gross_bps: list[float] = []
    net_bps: list[float] = []
    years_gross: dict[int, list[float]] = defaultdict(list)
    years_net: dict[int, list[float]] = defaultdict(list)
    long_count = short_count = 0

    for o in obs:
        if o.skew > 0:
            sign = 1.0
            long_count += 1
        elif o.skew < 0:
            sign = -1.0
            short_count += 1
        else:
            continue
        g = sign * float(o.forward_log_return) * 10000.0
        n = g - float(cost_bps)
        gross_bps.append(g)
        net_bps.append(n)
        years_gross[o.year].append(g)
        years_net[o.year].append(n)

    count = len(net_bps)
    mean_gross = sum(gross_bps) / count if count else math.nan
    mean_net = sum(net_bps) / count if count else math.nan
    wins = [v for v in net_bps if v > 0]
    losses = [v for v in net_bps if v < 0]
    if losses:
        pf = sum(wins) / abs(sum(losses))
    elif wins:
        pf = math.inf
    else:
        pf = math.nan
    win_rate = len(wins) / count if count else math.nan

    wealth = 1.0
    peak = 1.0
    max_dd = 0.0
    for bps in net_bps:
        wealth *= math.exp(bps / 10000.0)
        peak = max(peak, wealth)
        dd = wealth / peak - 1.0
        max_dd = min(max_dd, dd)

    annual_net_mean = {
        str(y): (sum(v) / len(v) if v else math.nan)
        for y, v in sorted(years_net.items())
    }
    annual_gross_sum = {
        str(y): sum(v) for y, v in sorted(years_gross.items())
    }
    positive_year_gross = {y: max(0.0, sum(v)) for y, v in years_gross.items()}
    total_positive = sum(positive_year_gross.values())
    max_positive_year_share = (
        max(positive_year_gross.values()) / total_positive
        if total_positive > 0 and positive_year_gross
        else math.nan
    )

    return {
        "n_positions": count,
        "gross_mean_bps": mean_gross,
        "net_mean_bps": mean_net,
        "cumulative_net_return": wealth - 1.0,
        "profit_factor": pf,
        "win_rate": win_rate,
        "max_drawdown": max_dd,
        "long_count": long_count,
        "short_count": short_count,
        "annual_net_mean_bps": annual_net_mean,
        "annual_gross_sum_bps": annual_gross_sum,
        "max_single_year_positive_gross_pnl_share": max_positive_year_share,
    }


def mve0_gate(
    obs: Sequence[AlignedObservation],
    regression: Mapping[str, float],
    base_metrics: Mapping[str, object],
    provenance_gate_pass: bool,
) -> dict[str, object]:
    annual = dict(base_metrics["annual_net_mean_bps"])
    non_negative_years = sum(
        1 for y in ("2021", "2022", "2023", "2024")
        if y in annual and float(annual[y]) >= 0.0
    )
    share = float(base_metrics["max_single_year_positive_gross_pnl_share"])
    gates = {
        "A_min_500_valid_signal_days": len(obs) >= MIN_VALID_DAYS,
        "B_beta_positive_and_one_sided_hac_p_le_0_10":
            float(regression["beta"]) > 0.0
            and float(regression["one_sided_p_beta_gt_0"]) <= 0.10,
        "C_net_mean_10bps_positive": float(base_metrics["net_mean_bps"]) > 0.0,
        "D_profit_factor_10bps_gt_1": float(base_metrics["profit_factor"]) > 1.0,
        "E_at_least_3_of_4_years_non_negative_net_mean": non_negative_years >= 3,
        "F_single_year_positive_gross_pnl_share_le_0_60":
            math.isfinite(share) and share <= 0.60,
        "G_provenance_timestamp_leakage_coverage_pass": bool(provenance_gate_pass),
    }
    return {
        "gates": gates,
        "non_negative_year_count": non_negative_years,
        "mve0_pass": all(gates.values()),
    }
