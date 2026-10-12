"""Immutable Parent V5 close-to-close transition and contract-size economics.
No exchange calls. 20x is a leverage ceiling, NEVER substituted for account risk.
"""
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_DOWN
from math import isfinite

SYMBOLS = ('ETH_USDT','SOL_USDT','BNB_USDT')
STOP_FRAC = .04
TRAIL_ACTIVATION = .05
TRAIL_DISTANCE = .12

@dataclass(frozen=True)
class TrailPosition:
    symbol: str
    position_id: int
    filled_entry: float
    peak_high: float
    active_stop: float
    volume_contracts: int
    last_closed_boundary: int
    stop_order_id: str


def initial_position(symbol, position_id, entry_price, contracts, close_boundary, stop_order_id):
    if symbol not in SYMBOLS or position_id <= 0 or contracts <= 0 or entry_price <= 0 or not stop_order_id:
        raise ValueError('INVALID_INITIAL_POSITION')
    return TrailPosition(symbol, position_id, entry_price, entry_price, entry_price*.96,
                         contracts, close_boundary, str(stop_order_id))


def evaluate_closed_bar(p: TrailPosition, *, boundary: int, open_price: float,
                        high: float, low: float, close: float) -> dict:
    if boundary <= p.last_closed_boundary: return {'action':'DUPLICATE_OR_OLD_BAR', 'position':p}
    if not all(isfinite(v) and v>0 for v in (open_price, high, low, close, p.active_stop)):
        raise ValueError('BAD_PRICES')
    if high<max(open_price, close) or low>min(open_price,close):raise ValueError('BAD_OHLC')
    # The exchange-side stop can have executed during this bar; NEVER infer an actual fill.
    if open_price <= p.active_stop or low <= p.active_stop:
        return {'action':'EXCHANGE_STOP_RECONCILIATION_REQUIRED', 'position':p}
    peak=max(p.peak_high,high)
    next_stop=max(p.filled_entry*.96, peak*(1-TRAIL_DISTANCE)) if close/p.filled_entry-1>=TRAIL_ACTIVATION else p.filled_entry*.96
    return {'action':'CHANGE_STOP' if abs(next_stop-p.active_stop)>1e-10 else 'HOLD',
            'next_stop':next_stop,
            'position':TrailPosition(p.symbol,p.position_id,p.filled_entry,peak,next_stop,
                                    p.volume_contracts,boundary,p.stop_order_id)}


def size_for_risk(*, equity_usdt, market_ask, contract_size, min_vol, vol_unit,
                  max_vol, per_trade_risk=.0025, per_side_fee_bps=8, slippage_bps=5,
                  leverage=20, max_notional_fraction=.25):
    """Conservative intended-loss sizing, not a max-loss guarantee (gaps/liquidations exist)."""
    a=[equity_usdt,market_ask,contract_size,min_vol,vol_unit,max_vol]
    if any(float(x)<=0 for x in a) or leverage<1 or leverage>20:
        raise ValueError('INVALID_SIZING_INPUT')
    if not (0<per_trade_risk<=.05 and 0<max_notional_fraction<=1):raise ValueError('INVALID_RISK')
    risk_per_dollar=STOP_FRAC+(2*per_side_fee_bps+slippage_bps)/1e4
    desired_notional = min(equity_usdt*per_trade_risk/risk_per_dollar,
                           equity_usdt*leverage*max_notional_fraction)
    per_contract = market_ask*contract_size
    step=Decimal(str(vol_unit))
    count=Decimal(str(desired_notional)) / Decimal(str(per_contract))
    rounded=(count/step).to_integral_value(rounding=ROUND_DOWN)*step
    if rounded<Decimal(str(min_vol)) or rounded>Decimal(str(max_vol)):
        return {'status':'BLOCKED_LOT_RISK_MISMATCH','minimum_notional_usdt':per_contract*min_vol,
                'desired_notional_usdt':desired_notional,'contracts':0}
    if rounded!=int(rounded):return {'status':'BLOCKED_NONINTEGRAL_CONTRACT_UNIT','contracts':0}
    notional=float(rounded)*per_contract
    return {'status':'SIZED','contracts':int(rounded),'notional_usdt':notional,
            'margin_estimate_usdt':notional/leverage,'estimated_loss_budget_usdt':notional*risk_per_dollar,
            'account_risk_budget_usdt':equity_usdt*per_trade_risk}