#!/usr/bin/env python3
"""Offline, deterministic cost hurdle for hypothetical asymmetric futures trades.

No market requests, account access, orders, trading signals, or edge verdicts.
This is a necessary-condition calculator, not a backtest.
"""
from __future__ import annotations

import argparse
import json
import math


def economic_hurdle(
    stop_bps: float,
    target_r: float,
    *,
    fee_roundtrip_bps: float = 16.0,
    extra_execution_bps: float = 0.0,
    funding_bps: float = 0.0,
    assumed_win_rate: float | None = None,
) -> dict:
    values = {
        "stop_bps": stop_bps,
        "target_r": target_r,
        "fee_roundtrip_bps": fee_roundtrip_bps,
        "extra_execution_bps": extra_execution_bps,
        "funding_bps": funding_bps,
    }
    if not all(math.isfinite(float(v)) for v in values.values()):
        raise ValueError("NON_FINITE_INPUT")
    if stop_bps <= 0 or target_r <= 0:
        raise ValueError("STOP_AND_TARGET_MUST_BE_POSITIVE")
    if min(fee_roundtrip_bps, extra_execution_bps, funding_bps) < 0:
        raise ValueError("NEGATIVE_COST_NOT_ALLOWED")
    if assumed_win_rate is not None and (
        not math.isfinite(assumed_win_rate) or not 0 <= assumed_win_rate <= 1
    ):
        raise ValueError("WIN_RATE_OUT_OF_RANGE")
    total_cost_bps = fee_roundtrip_bps + extra_execution_bps + funding_bps
    cost_r = total_cost_bps / stop_bps
    win_r = target_r - cost_r
    loss_r = -1.0 - cost_r
    threshold = (1.0 + cost_r) / (1.0 + target_r)
    out = {
        "schema": "crypto_lab.asymmetric_economic_hurdle.v1",
        "status": "SENSITIVITY_ONLY_NO_EDGE_VERDICT",
        "fee_roundtrip_bps": fee_roundtrip_bps,
        "extra_execution_bps": extra_execution_bps,
        "funding_bps": funding_bps,
        "stop_bps": stop_bps,
        "target_r": target_r,
        "total_cost_bps": total_cost_bps,
        "cost_in_r": cost_r,
        "net_win_r_if_target_filled": win_r,
        "net_loss_r_if_stop_filled": loss_r,
        "breakeven_win_rate": threshold,
        "target_net_positive_after_costs": win_r > 0,
        "breakeven_feasible": threshold <= 1.0,
        "assumptions": [
            "Full stop/target fills, fixed initial risk, no gap through stop",
            "Same charged round-trip costs for wins and losses",
            "No claim of signal success, order-fill probability, or observed returns",
            "Additional spread/slippage and adverse funding must be measured separately",
        ],
        "live_trading": False,
    }
    if assumed_win_rate is not None:
        out["assumed_win_rate"] = assumed_win_rate
        out["hypothetical_expected_r"] = (
            assumed_win_rate * win_r + (1.0 - assumed_win_rate) * loss_r
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop-bps", type=float, required=True)
    parser.add_argument("--target-r", type=float, required=True)
    parser.add_argument("--fee-rt-bps", type=float, default=16.0)
    parser.add_argument("--extra-bps", type=float, default=0.0)
    parser.add_argument("--funding-bps", type=float, default=0.0)
    parser.add_argument("--assumed-win-rate", type=float)
    args = parser.parse_args()
    print(json.dumps(economic_hurdle(
        args.stop_bps, args.target_r,
        fee_roundtrip_bps=args.fee_rt_bps,
        extra_execution_bps=args.extra_bps,
        funding_bps=args.funding_bps,
        assumed_win_rate=args.assumed_win_rate,
    ), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
