"""Causal sweep-continuation feature helpers.

All windows are strictly backward-looking. No future returns are used here.
"""
import bisect


def trailing_side_notionals(anchor_t, window_ms, times, prefix_buy, prefix_sell):
    right=bisect.bisect_left(times, anchor_t)  # strictly before t
    left=bisect.bisect_left(times, anchor_t-window_ms, 0, right)
    buy=prefix_buy[right]-prefix_buy[left]
    sell=prefix_sell[right]-prefix_sell[left]
    return buy,sell


def sweep_features(anchor_t, prev_bid, prev_ask, prev_bid_depth, prev_ask_depth,
                   bid, ask, bid_depth, ask_depth,
                   trade_times, prefix_buy, prefix_sell,
                   burst_window_ms=1000, baseline_window_ms=60000):
    buy_now,sell_now=trailing_side_notionals(
        anchor_t,burst_window_ms,trade_times,prefix_buy,prefix_sell)

    # Baseline excludes the current burst window.
    right=bisect.bisect_left(trade_times,anchor_t-burst_window_ms)
    left=bisect.bisect_left(
        trade_times,anchor_t-burst_window_ms-baseline_window_ms,0,right)
    buy_base=prefix_buy[right]-prefix_buy[left]
    sell_base=prefix_sell[right]-prefix_sell[left]

    net=buy_now-sell_now
    direction=1 if net>0 else (-1 if net<0 else 0)
    if direction==0:
        return None

    same_now=buy_now if direction>0 else sell_now
    same_base=buy_base if direction>0 else sell_base
    baseline_per_burst=(same_base/baseline_window_ms)*burst_window_ms
    burst_ratio=(same_now/baseline_per_burst) if baseline_per_burst>0 else None

    if direction>0:
        displacement=max(0.0,(ask-prev_ask)/prev_ask*10000.0)
        replenishment_failure=max(
            0.0,(prev_ask_depth-ask_depth)/prev_ask_depth
        ) if prev_ask_depth>0 else 0.0
    else:
        displacement=max(0.0,(prev_bid-bid)/prev_bid*10000.0)
        replenishment_failure=max(
            0.0,(prev_bid_depth-bid_depth)/prev_bid_depth
        ) if prev_bid_depth>0 else 0.0

    total_now=buy_now+sell_now
    flow_purity=(same_now/total_now) if total_now>0 else 0.0

    return {
        "direction":direction,
        "buy_notional_1s":buy_now,
        "sell_notional_1s":sell_now,
        "burst_ratio":burst_ratio,
        "displacement_bps":displacement,
        "replenishment_failure":replenishment_failure,
        "flow_purity":flow_purity,
    }
