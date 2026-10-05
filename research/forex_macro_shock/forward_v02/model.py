"""Frozen pure functions; tests use synthetic inputs only. No live runner."""
import math
import statistics
from decimal import Decimal, ROUND_FLOOR


def quantile(values, q):
    if not values or not 0 <= q <= 1 or not all(math.isfinite(x) for x in values):
        raise ValueError('INVALID_CALIBRATION')
    values = sorted(values)
    return values[max(0, math.ceil(q * len(values)) - 1)]


def calibrate(basis_bps, spread_bps):
    if len(basis_bps) < 21600 or len(spread_bps) != len(basis_bps):
        raise ValueError('INSUFFICIENT_BURN_IN')
    if not all(math.isfinite(x) for x in basis_bps + spread_bps) or min(spread_bps) < 0:
        raise ValueError('INVALID_CALIBRATION')
    baseline = statistics.median(basis_bps)
    noise = quantile([abs(x - baseline) for x in basis_bps], .995)
    floor = 16 + statistics.median(spread_bps) + 2
    return {'baseline_bps': baseline, 'noise_bps': noise,
            'economic_floor_bps': floor, 'threshold_bps': max(noise, floor)}


def signal(mexc_mid, binance_mid, baseline_bps, threshold_bps, valid):
    if not valid:
        return None
    if not all(math.isfinite(x) for x in [mexc_mid, binance_mid, baseline_bps, threshold_bps]) or min(mexc_mid, binance_mid, threshold_bps) <= 0:
        raise ValueError('INVALID_INPUT')
    excess = 10000 * math.log(mexc_mid / binance_mid) - baseline_bps
    if abs(excess) < threshold_bps:
        return None
    return 'SHORT' if excess > 0 else 'LONG'


def contracts(notional, worst_price, contract_size, vol_unit, min_vol):
    vals = [Decimal(str(x)) for x in [notional, worst_price, contract_size, vol_unit, min_vol]]
    if any(not x.is_finite() or x <= 0 for x in vals):
        raise ValueError('INVALID_CONTRACT_METADATA')
    n, price, size, unit, minimum = vals
    quantity = (n / price / size / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
    if quantity < minimum:
        raise ValueError('NOTIONAL_BELOW_MINIMUM')
    return quantity


def vwap(levels, qty, contract_size):
    qty, size = Decimal(str(qty)), Decimal(str(contract_size))
    if any(not x.is_finite() or x <= 0 for x in [qty, size]):
        raise ValueError('INVALID_QUANTITY')
    remaining = qty; cost = Decimal(0)
    for level in levels:
        price, available = Decimal(str(level[0])), Decimal(str(level[1]))
        if any(not x.is_finite() or x <= 0 for x in [price, available]):
            raise ValueError('INVALID_DEPTH')
        take = min(remaining, available)
        cost += take * size * price; remaining -= take
        if remaining == 0:
            return cost / (qty * size)
    raise ValueError('INSUFFICIENT_EXECUTABLE_DEPTH')


def net_bps(direction, entry, exit_price):
    entry, exit_price = float(entry), float(exit_price)
    if direction not in ['LONG', 'SHORT'] or not all(math.isfinite(x) and x > 0 for x in [entry, exit_price]):
        raise ValueError('INVALID_FILL')
    ratio = exit_price / entry
    gross = (ratio - 1) * 10000 * (1 if direction == 'LONG' else -1)
    # Fees on both actual fill notionals. Fixed slip is 1 bp per side.
    return gross - 8 * (1 + ratio) - 2


def economic_gate(event_net):
    if len(event_net) < 8:
        return {'verdict': 'FORWARD_COLLECTING'}
    if len(event_net) != 8 or not all(math.isfinite(x) for x in event_net):
        raise ValueError('INVALID_EVENT_SAMPLE')
    observed = sum(event_net)
    exceed = 0
    for mask in range(1 << 8):
        permuted = sum(x if mask & (1 << i) else -x for i, x in enumerate(event_net))
        exceed += permuted >= observed - 1e-12
    p = exceed / 256
    return {'verdict': 'FORWARD_PASS' if observed > 0 and p <= .05 else 'FORWARD_FAIL',
            'mean_net_bps': observed / 8, 'one_sided_signflip_p': p}
