"""LICP-001 causal ignition/propagation detector.

No exchange actions. The detector refuses to initialize until the numeric
trigger configuration has been explicitly frozen.
"""
from dataclasses import dataclass
from typing import Iterable
import json


def load_config(path):
    with open(path,"r",encoding="utf-8") as f:
        cfg=json.load(f)
    if cfg.get("status")!="FROZEN":
        raise PermissionError("LICP_TRIGGER_CONFIG_NOT_FROZEN")
    required=[
      cfg["btc_ignition"].get("notional_threshold"),
      cfg["btc_ignition"].get("side_concentration_threshold"),
      cfg["binance_confirmation"].get("notional_threshold"),
      cfg["alt_propagation"]["notional_thresholds"].get("ETHUSDT"),
      cfg["alt_propagation"]["notional_thresholds"].get("SOLUSDT"),
    ]
    if any(x is None for x in required):
        raise ValueError("LICP_TRIGGER_THRESHOLD_MISSING")
    return cfg


def bybit_pressure(position_side: str) -> str:
    # Official Bybit semantics: Buy update => long position liquidated.
    if position_side=="Buy": return "SELL"
    if position_side=="Sell": return "BUY"
    raise ValueError("INVALID_BYBIT_POSITION_SIDE")


def side_concentration(sell_notional: float,buy_notional: float) -> float:
    total=sell_notional+buy_notional
    return abs(sell_notional-buy_notional)/total if total>0 else 0.0


@dataclass(frozen=True)
class Burst:
    source: str
    symbol: str
    start_ms: int
    end_ms: int
    pressure: str
    total_notional: float
    side_concentration: float


def aggregate_burst(events: Iterable[dict], source: str, symbol: str, end_ms: int, window_ms: int) -> Burst:
    es=[e for e in events if e["source"]==source and e["symbol"]==symbol
        and end_ms-window_ms < e["venue_ts"] <= end_ms]
    sell=sum(e["notional"] for e in es if e["pressure"]=="SELL")
    buy=sum(e["notional"] for e in es if e["pressure"]=="BUY")
    pressure="SELL" if sell>buy else ("BUY" if buy>sell else "FLAT")
    return Burst(source,symbol,end_ms-window_ms,end_ms,pressure,sell+buy,side_concentration(sell,buy))


def btc_ignition(events,end_ms,cfg):
    c=cfg["btc_ignition"]
    b=aggregate_burst(events,c["primary_source"],"BTCUSDT",end_ms,c["window_ms"])
    return (
        b.pressure!="FLAT" and
        b.total_notional>=float(c["notional_threshold"]) and
        b.side_concentration>=float(c["side_concentration_threshold"])
    ),b


def binance_confirms(events,end_ms,pressure,cfg):
    c=cfg["binance_confirmation"]
    b=aggregate_burst(events,"binance","BTCUSDT",end_ms,c["window_ms"])
    ok=b.total_notional>=float(c["notional_threshold"])
    if c.get("same_pressure_required",True):
        ok=ok and b.pressure==pressure
    return ok,b


def alt_propagation(events,btc_time_ms,now_ms,pressure,cfg):
    c=cfg["alt_propagation"]
    if now_ms<btc_time_ms or now_ms-btc_time_ms>c["window_ms_after_btc"]:
        return []
    hits=[]
    for sym in c["symbols"]:
        b=aggregate_burst(events,c["source"],sym,now_ms,c["burst_window_ms"])
        ok=b.total_notional>=float(c["notional_thresholds"][sym])
        if c.get("same_pressure_required",True):
            ok=ok and b.pressure==pressure
        if ok:hits.append(b)
    return hits
