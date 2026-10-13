"""Exact ideal two-barrier payoff hurdle for frozen F2, not a forecast."""
from engine import BASE_FEE, TP, STOP


def ideal_net_outcomes(slip_bps=2.0, funding_fraction=0.0):
    """Returns per-notional ideal roundtrip PnL fractions and break-even win rate.

    Conditional on exact barrier fills; ignores time exits, gaps, spread,
    mark liquidation, impact and future funding variability.
    """
    if slip_bps < 0:
        raise ValueError("negative slippage")
    slip = slip_bps / 10000
    def net(exit_raw_ratio):
        executed = exit_raw_ratio * (1-slip)
        return (executed-1) - BASE_FEE*(1+executed) + funding_fraction
    win = net(1+TP)
    loss = net(1-STOP)
    if win <= 0 or loss >= 0:
        return {"win_fraction": win, "loss_fraction": loss, "break_even_win_rate": None}
    breakeven = -loss/(win-loss)
    return {"win_fraction": win, "loss_fraction": loss,
            "break_even_win_rate": breakeven}


if __name__ == "__main__":
    import json
    print(json.dumps({"BASE_2bps": ideal_net_outcomes(2),
                      "STRESS_5bps": ideal_net_outcomes(5)}, indent=2))
