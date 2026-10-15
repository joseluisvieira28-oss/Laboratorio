"""MEXC V06 public market feasibility evidence; neither signals nor order authority.

Official MEXC docs: GET /api/v1/contract/detail/country and
GET /api/v1/contract/ticker. An authentic recent quote does NOT guarantee
an executable fill or exact stop coverage.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, InvalidOperation

FEE_TAKER_BPS_FLOOR = Decimal("8")
SLIP_BPS_ASSUMPTION = Decimal("2")
FUNDING_RESERVE_BPS_ASSUMPTION = Decimal("5")
MAX_PER_SLOT_USDT = Decimal("0.50")
LEVERAGE = Decimal("10")
LONG_STOP_FRACTION = Decimal(".04")
MAX_TICKER_AGE_MS = 15_000


class MarketGateHalt(ValueError):
    pass


def d(v, label):
    if v is None or isinstance(v,bool):
        raise MarketGateHalt("MISSING_"+label)
    try:
        out=Decimal(str(v))
    except (ValueError,InvalidOperation,TypeError) as exc:
        raise MarketGateHalt("NONNUMERIC_"+label) from exc
    if not out.is_finite():
        raise MarketGateHalt("NONFINITE_"+label)
    return out


def positive(row,key):
    val=d(row.get(key),key.upper())
    if val<=0:
        raise MarketGateHalt("NONPOSITIVE_"+key.upper())
    return val


def risk_one_contract(spec, quote, symbol, now_ms):
    if symbol not in ("SOL_USDT","BNB_USDT") or spec.get("symbol")!=symbol or quote.get("symbol")!=symbol:
        raise MarketGateHalt("VENUE_SYMBOL_MISMATCH")
    if spec.get("apiAllowed") is not True:
        raise MarketGateHalt("API_TRADING_NOT_EXPLICITLY_ALLOWED")
    if spec.get("settleCoin")!="USDT" or spec.get("quoteCoin")!="USDT":
        raise MarketGateHalt("NOT_USDT_SETTLED")
    if spec.get("positionOpenType") not in (1,3):
        raise MarketGateHalt("ISOLATED_MARGIN_NOT_SUPPORTED")
    leverage_min=positive(spec,"minLeverage")
    leverage_max=positive(spec,"maxLeverage")
    country_limit=d(spec.get("countryConfigContractMaxLeverage",0),"COUNTRY_LEVERAGE")
    if country_limit<0:
        raise MarketGateHalt("INVALID_COUNTRY_LEVERAGE")
    if leverage_min>LEVERAGE or leverage_max<LEVERAGE or (country_limit>0 and country_limit<LEVERAGE):
        raise MarketGateHalt("TEN_X_NOT_SUPPORTED_BY_CONTRACT")
    min_vol=positive(spec,"minVol")
    vol_unit=positive(spec,"volUnit")
    max_vol=positive(spec,"maxVol")
    if min_vol>1 or max_vol<1 or Decimal("1")%vol_unit:
        raise MarketGateHalt("ONE_CONTRACT_NOT_ALLOWED")
    contract_size=positive(spec,"contractSize")
    tick=positive(spec,"priceUnit")
    ask=positive(quote,"ask1")
    bid=positive(quote,"bid1")
    mark=positive(quote,"fairPrice")
    if ask<bid:
        raise MarketGateHalt("CROSSED_PUBLIC_BBO")
    t=quote.get("timestamp")
    if type(t) is not int or type(now_ms) is not int:
        raise MarketGateHalt("TICKER_CLOCK_NOT_INTEGERS")
    age=now_ms-t
    if age<0 or age>MAX_TICKER_AGE_MS:
        raise MarketGateHalt("PUBLIC_TICKER_STALE")
    if not (spec.get("state") in (None,0) or spec.get("state") is True):
        # MEXC uses 0 for enabled on some contract versions. Explicit
        # apiAllowed is still required, and unexpected states are rejected.
        raise MarketGateHalt("UNSUPPORTED_CONTRACT_STATE")
    pre_stop=ask*(Decimal("1")-LONG_STOP_FRACTION)
    stop=(pre_stop/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
    if stop<=0 or stop>=ask or mark<=stop:
        raise MarketGateHalt("INVALID_MARK_TRIGGER_STOP_GEOMETRY")
    stress_entry=ask*(Decimal("1")+SLIP_BPS_ASSUMPTION/10000)
    stress_exit=stop*(Decimal("1")-SLIP_BPS_ASSUMPTION/10000)
    unit_loss=stress_entry-stress_exit
    risk=contract_size*(unit_loss+(stress_entry+stress_exit)*FEE_TAKER_BPS_FLOOR/10000+
                        stress_entry*FUNDING_RESERVE_BPS_ASSUMPTION/10000)
    margin=contract_size*stress_entry/LEVERAGE
    worst_assumed=risk<=MAX_PER_SLOT_USDT
    return {
        "symbol":symbol,
        "api_trading_contract_allowed":True,
        "isolated_supported":True,
        "hedge_account_mode_from_separate_private_probe_required":True,
        "contract_size_base":str(contract_size),
        "min_contract_vol":str(min_vol),
        "volume_unit":str(vol_unit),
        "price_tick":str(tick),
        "one_contract_notional_at_ask_usdt":str(contract_size*ask),
        "one_contract_initial_margin_model_usdt":str(margin),
        "public_bid_usdt":str(bid),
        "public_ask_usdt":str(ask),
        "public_mark_usdt":str(mark),
        "public_quote_age_ms":age,
        "public_spread_bps":str((ask-bid)/ask*10000),
        "original_stop_four_pct_rounded_down":str(stop),
        "one_contract_modeled_loss_usdt":str(risk),
        "one_contract_model_risk_budget_pass":worst_assumed,
        "real_margin_current_account_verified":False,
        "real_liquidation_mark_buffer_verified":False,
        "original_nonlatched_trailing_safely_broker_managed":False,
        "order_book_depth_slippage_proven":False,
        "maker_taker_fee_model_source":"CONSERVATIVE_API_FLOOR_8BPS_TAKER_SIDE",
        "not_a_hard_loss_cap":True,
        "actual_order_execution_authority":"NONE",
    }
