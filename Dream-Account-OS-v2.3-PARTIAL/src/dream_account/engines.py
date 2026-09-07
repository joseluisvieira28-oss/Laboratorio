from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .config import Settings
from .models import Book, Candle, Candidate


def pct_change(old: float, new: float) -> float:
    return ((new / old) - 1) * 100 if old else 0.0


def rvol(candles: list[Candle], lookback: int = 20) -> float:
    if len(candles) < lookback + 1:
        return 0.0
    baseline = median(c.volume for c in candles[-lookback - 1 : -1])
    return candles[-1].volume / baseline if baseline else 0.0


def atr(candles: list[Candle], length: int = 14) -> float:
    if len(candles) < length + 1:
        return 0.0
    trs = []
    for previous, current in zip(candles[-length - 1 : -1], candles[-length:]):
        trs.append(max(current.high - current.low, abs(current.high - previous.close), abs(current.low - previous.close)))
    return sum(trs) / len(trs)


def depth_notional(book: Book, pct: float) -> tuple[float, float]:
    mid = book.mid
    bid_floor, ask_ceiling = mid * (1 - pct / 100), mid * (1 + pct / 100)
    bid_depth = sum(p * q for p, q in book.bids if p >= bid_floor)
    ask_depth = sum(p * q for p, q in book.asks if p <= ask_ceiling)
    return bid_depth, ask_depth


def estimated_slippage_pct(book: Book, side: str, notional: float) -> float | None:
    levels = book.asks if side.upper() == "BUY" else book.bids
    remaining, acquired, spent = notional, 0.0, 0.0
    for price, qty in levels:
        take_notional = min(remaining, price * qty)
        acquired += take_notional / price
        spent += take_notional
        remaining -= take_notional
        if remaining <= 1e-9:
            average = spent / acquired
            reference = book.ask if side.upper() == "BUY" else book.bid
            return abs(average - reference) / reference * 100
    return None


def confirmed_breakout_retest(candles: list[Candle], resistance: float, zone_low: float, zone_high: float) -> tuple[bool, dict]:
    closed = [c for c in candles if c.closed]
    if len(closed) < 3:
        return False, {"reason": "insufficient_closed_candles"}
    for index in range(max(1, len(closed) - 6), len(closed) - 1):
        breakout = closed[index]
        retest = closed[index + 1]
        if breakout.close > resistance and breakout.open <= breakout.close:
            defended = retest.low >= zone_low and retest.low <= zone_high and retest.close >= zone_high
            if defended:
                return True, {"breakout_close_time": breakout.close_time, "breakout_close": breakout.close, "retest_close_time": retest.close_time, "retest_close": retest.close}
    return False, {"reason": "no_confirmed_close_and_defended_retest"}


@dataclass
class CostResult:
    gross_rr: float
    net_rr: float
    estimated_cost_pct: float


def calculate_costs(entry: float, stop: float, target: float, fee_pct_each_side: float, spread_pct: float, slippage_pct_each_side: float, funding_pct: float = 0.0) -> CostResult:
    risk_pct = abs(entry - stop) / entry * 100
    reward_pct = abs(target - entry) / entry * 100
    total_cost = 2 * fee_pct_each_side + spread_pct + 2 * slippage_pct_each_side + abs(funding_pct)
    gross = reward_pct / risk_pct if risk_pct else 0.0
    net = max(0.0, reward_pct - total_cost) / (risk_pct + total_cost) if risk_pct else 0.0
    return CostResult(gross, net, total_cost)


def position_size(balance: float, risk_pct: float, entry: float, stop: float, max_notional: float | None = None) -> dict[str, float]:
    risk_chf = balance * risk_pct / 100
    stop_pct = abs(entry - stop) / entry
    if not stop_pct:
        raise ValueError("stop must differ from entry")
    theoretical = risk_chf / stop_pct
    capital = min(theoretical, max_notional if max_notional is not None else balance)
    actual_risk = capital * stop_pct
    return {"risk_chf_target": risk_chf, "position_notional_chf": capital, "actual_risk_chf": actual_risk, "stop_distance_pct": stop_pct * 100}


def pump_risk(candidate: Candidate) -> float:
    risk = 0.0
    risk += min(35, max(0, candidate.changes.get("1h", 0)) * 1.2)
    risk += min(25, max(0, candidate.changes.get("24h", 0)) * 0.25)
    risk += 15 if candidate.spread_pct > 0.2 else 0
    risk += 15 if candidate.rvol_15m > 2.0 else 0
    risk += 10 if candidate.volume_24h_usd < 500_000 else 0
    return min(100.0, risk)


def score_candidate(candidate: Candidate, settings: Settings, net_rr: float | None = None, catalyst_confirmed: bool = False, futures_available: bool = False) -> Candidate:
    candidate.pump_risk = pump_risk(candidate)
    liquidity = 15 if candidate.volume_24h_usd >= settings.strong_volume_usd and candidate.spread_pct < settings.preferred_spread_pct else 9 if candidate.volume_24h_usd >= settings.min_volume_usd else 2
    technical = 18 if candidate.setup == "BREAKOUT_RETEST" else 11 if candidate.setup != "NONE" else 4
    volume = 15 if candidate.rvol_15m >= 1.5 else 10 if candidate.rvol_15m >= 1.0 else 4
    regime = 10 if candidate.regime == "RISK_ON_TREND" and candidate.status != "SHORT_CANDIDATE" else 6 if candidate.regime in {"RANGE", "UNCLEAR"} else 3
    catalyst = 10 if catalyst_confirmed else 2
    futures = 8 if futures_available and candidate.funding is not None and candidate.oi_change_1h is not None else 0
    rr_score = 15 if net_rr is not None and net_rr >= 2.5 else 12 if net_rr is not None and net_rr >= 2 else 0
    safety = max(0.0, 5 * (1 - candidate.pump_risk / 100))
    candidate.subscores = {"liquidity": liquidity, "technical": technical, "volume": volume, "regime": regime, "catalyst": catalyst, "futures": futures, "risk_reward": rr_score, "manipulation_safety": round(safety, 2)}
    candidate.score = round(sum(candidate.subscores.values()), 2)
    candidate.tier = "A+" if candidate.score >= 85 else "A" if candidate.score >= 75 else "B" if candidate.score >= 65 else "REJECT"
    if candidate.volume_24h_usd < settings.min_volume_usd:
        candidate.rejection_reasons.append("volume_below_minimum")
    if candidate.spread_pct > settings.hard_spread_pct:
        candidate.rejection_reasons.append("spread_hard_reject")
    if candidate.pump_risk >= 70:
        candidate.rejection_reasons.append("pump_risk")
    if net_rr is None or net_rr < settings.min_net_rr:
        candidate.rejection_reasons.append("net_rr_below_2")
    if candidate.rejection_reasons:
        candidate.status = "NO_TRADE"
    return candidate


def classify_regime(btc_15m: list[Candle], btc_1h: list[Candle], eth_1h: list[Candle]) -> tuple[str, float, str]:
    b15 = pct_change(btc_15m[-5].close, btc_15m[-1].close)
    b1 = pct_change(btc_1h[-5].close, btc_1h[-1].close)
    e1 = pct_change(eth_1h[-5].close, eth_1h[-1].close)
    volatility = atr(btc_15m) / btc_15m[-1].close * 100
    if volatility > 1.5:
        return "HIGH_VOLATILITY", 0.8, f"BTC 15m ATR {volatility:.2f}%"
    if b15 > 0 and b1 > 0 and e1 > 0:
        return "RISK_ON_TREND", 0.75, f"BTC 15m {b15:.2f}%, BTC 1h {b1:.2f}%, ETH 1h {e1:.2f}%"
    if b15 < 0 and b1 < 0 and e1 < 0:
        return "RISK_OFF_TREND", 0.75, f"BTC 15m {b15:.2f}%, BTC 1h {b1:.2f}%, ETH 1h {e1:.2f}%"
    if abs(b1) < 1 and abs(e1) < 1:
        return "RANGE", 0.65, f"BTC 1h {b1:.2f}%, ETH 1h {e1:.2f}%"
    return "UNCLEAR", 0.45, "timeframes not aligned"
