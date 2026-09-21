from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

EQUITY_USDT = 112.3763
ETF_MAX_FRACTION = 0.001
BNB_MAX_NOTIONAL_CHF = 25.0

SPOT_BASE = "https://api.mexc.com"
FUTURES_BASE = "https://api.mexc.com"


def get_json(url: str, timeout: int = 15):
    req = Request(url, headers={"User-Agent": "crypto-lab-capital-compatibility-audit/0.1"}, method="GET")
    with urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}: {url}")
        return json.loads(r.read().decode("utf-8"))


def spot_exchange_info(symbol: str) -> dict:
    url = f"{SPOT_BASE}/api/v3/exchangeInfo?{urlencode({'symbol': symbol})}"
    payload = get_json(url)
    rows = payload.get("symbols") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        return {"symbol": symbol, "present": False, "raw": payload}
    row = rows[0]
    filters = {f.get("filterType"): f for f in row.get("filters", []) if isinstance(f, dict)}
    return {
        "symbol": symbol,
        "present": True,
        "status": row.get("status"),
        "base_asset": row.get("baseAsset"),
        "quote_asset": row.get("quoteAsset"),
        "base_asset_precision": row.get("baseAssetPrecision"),
        "quote_asset_precision": row.get("quoteAssetPrecision"),
        "quote_amount_precision": row.get("quoteAmountPrecision"),
        "quote_amount_precision_market": row.get("quoteAmountPrecisionMarket"),
        "max_quote_amount": row.get("maxQuoteAmount"),
        "max_quote_amount_market": row.get("maxQuoteAmountMarket"),
        "base_size_precision": row.get("baseSizePrecision"),
        "permissions": row.get("permissions"),
        "order_types": row.get("orderTypes"),
        "is_spot_trading_allowed": row.get("isSpotTradingAllowed"),
        "filters": filters,
        "raw_selected": {
            k: row.get(k) for k in (
                "symbol","status","baseAsset","quoteAsset","baseAssetPrecision",
                "quoteAssetPrecision","quoteAmountPrecision","quoteAmountPrecisionMarket",
                "maxQuoteAmount","maxQuoteAmountMarket","baseSizePrecision",
                "isSpotTradingAllowed","permissions","orderTypes"
            )
        },
    }


def spot_ticker(symbol: str) -> dict:
    payload = get_json(f"{SPOT_BASE}/api/v3/ticker/bookTicker?{urlencode({'symbol': symbol})}")
    return {
        "symbol": symbol,
        "bid": float(payload["bidPrice"]),
        "ask": float(payload["askPrice"]),
    }


def futures_contract(symbol: str) -> dict:
    payload = get_json(f"{FUTURES_BASE}/api/v1/contract/detail")
    if payload.get("success") is not True:
        raise RuntimeError("futures contract/detail did not return success=true")
    rows = payload.get("data")
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows or []:
        if str(row.get("symbol", "")).upper() == symbol:
            return row
    raise RuntimeError(f"futures contract missing: {symbol}")


def futures_ticker(symbol: str) -> dict:
    payload = get_json(f"{FUTURES_BASE}/api/v1/contract/ticker?{urlencode({'symbol': symbol})}")
    if payload.get("success") is not True:
        raise RuntimeError("futures ticker failed")
    row = payload.get("data")
    if isinstance(row, list):
        row = next((x for x in row if x.get("symbol") == symbol), None)
    if not isinstance(row, dict):
        raise RuntimeError("futures ticker missing row")
    return row


def decimal_or_none(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except (TypeError,ValueError):
        return None


def extract_spot_minimum(info: dict, book: dict) -> dict:
    if not info.get("present"):
        return {"determinable": False, "reason": "SYMBOL_NOT_PRESENT"}

    f=info.get("filters") or {}
    lot=f.get("LOT_SIZE") or {}
    market_lot=f.get("MARKET_LOT_SIZE") or {}
    min_notional_filter=f.get("MIN_NOTIONAL") or f.get("NOTIONAL") or {}

    min_qty = decimal_or_none(market_lot.get("minQty"))
    if min_qty in (None,0.0):
        min_qty = decimal_or_none(lot.get("minQty"))
    step = decimal_or_none(market_lot.get("stepSize"))
    if step in (None,0.0):
        step = decimal_or_none(lot.get("stepSize"))

    min_notional = decimal_or_none(
        min_notional_filter.get("minNotional")
        if isinstance(min_notional_filter,dict)
        else None
    )
    # MEXC Spot V3 documents quoteAmountPrecision as min order amount,
    # and quoteAmountPrecisionMarket as the market-order minimum when present.
    documented_min_quote = decimal_or_none(info.get("quote_amount_precision"))
    documented_market_min_quote = decimal_or_none(info.get("quote_amount_precision_market"))
    ask=book["ask"]
    quantity_implied = min_qty * ask if min_qty is not None else None
    candidates=[
        x for x in (
            min_notional,
            documented_min_quote,
            documented_market_min_quote,
            quantity_implied,
        )
        if x is not None and x>0
    ]
    min_quote=max(candidates) if candidates else None
    return {
        "determinable": min_quote is not None,
        "minimum_quantity": min_qty,
        "quantity_step": step,
        "minimum_notional_filter_quote": min_notional,
        "documented_min_order_quote": documented_min_quote,
        "documented_market_min_order_quote": documented_market_min_quote,
        "minimum_quote_from_quantity_at_ask": quantity_implied,
        "minimum_executable_quote_estimate": min_quote,
        "quote_asset": info.get("quote_asset"),
        "ask": ask,
    }


def main():
    checked=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    out={
        "audit_id":"MEXC_CAPITAL_COMPATIBILITY_AUDIT_V0.1",
        "checked_at_utc":checked,
        "account_equity_usdt_from_authenticated_receipt":EQUITY_USDT,
        "science_or_risk_rules_changed":False,
        "orders_created":False,
        "authenticated_exchange_api_used":False,
        "exchange_mutation_performed":False,
        "markets":{},
        "candidates":{},
    }

    for symbol in ("BTCUSDT","BNBBTC"):
        try:
            info=spot_exchange_info(symbol)
            book=spot_ticker(symbol) if info.get("present") else None
            out["markets"][f"spot_{symbol}"]={
                "info":info,
                "book":book,
                "minimum":extract_spot_minimum(info,book) if book else {"determinable":False,"reason":"NO_BOOK"},
            }
        except Exception as exc:
            out["markets"][f"spot_{symbol}"]={"error":f"{type(exc).__name__}:{exc}"}

    try:
        c=futures_contract("BTC_USDT")
        t=futures_ticker("BTC_USDT")
        price=float(t.get("lastPrice"))
        min_vol=float(c["minVol"])
        contract_size=float(c["contractSize"])
        min_notional=min_vol*contract_size*price
        out["markets"]["futures_BTC_USDT"]={
            "api_allowed":c.get("apiAllowed"),
            "state":c.get("state"),
            "future_type":c.get("futureType"),
            "position_open_type":c.get("positionOpenType"),
            "min_leverage":c.get("minLeverage"),
            "max_leverage":c.get("maxLeverage"),
            "min_vol":min_vol,
            "vol_unit":c.get("volUnit"),
            "contract_size":contract_size,
            "price_unit":c.get("priceUnit"),
            "last_price":price,
            "minimum_executable_notional_estimate_usdt":min_notional,
        }
    except Exception as exc:
        out["markets"]["futures_BTC_USDT"]={"error":f"{type(exc).__name__}:{exc}"}

    etf_budget=EQUITY_USDT*ETF_MAX_FRACTION
    fut=out["markets"].get("futures_BTC_USDT",{})
    fut_min=fut.get("minimum_executable_notional_estimate_usdt")
    btcspot=out["markets"].get("spot_BTCUSDT",{})
    spot_min=((btcspot.get("minimum") or {}).get("minimum_executable_quote_estimate"))

    out["candidates"]["ETF-CME-INSTFLOW-001"]={
        "tier":2,
        "current_authority":"READINESS_ONLY_NOT_EXECUTION_AUTHORITY",
        "frozen_validation_fraction_of_equity":ETF_MAX_FRACTION,
        "frozen_validation_budget_usdt":etf_budget,
        "long_mapping":"MEXC BTCUSDT SPOT",
        "short_mapping":"MEXC BTC_USDT USDT PERPETUAL ISOLATED 1X AUTO_MARGIN_ADD_OFF",
        "long_spot_minimum_usdt":spot_min,
        "long_capital_compatible_now": bool(spot_min is not None and spot_min <= etf_budget),
        "short_futures_minimum_usdt":fut_min,
        "short_capital_compatible_now": bool(fut_min is not None and fut_min <= etf_budget),
        "equity_required_for_short_minimum_at_frozen_fraction_usdt": (
            fut_min/ETF_MAX_FRACTION if fut_min is not None else None
        ),
        "equity_required_for_long_minimum_at_frozen_fraction_usdt": (
            spot_min/ETF_MAX_FRACTION if spot_min is not None else None
        ),
        "live_order_now":False,
        "reason":"No current canonical executable signal/authority; venue minimum must not force risk increase.",
    }

    bnb=out["markets"].get("spot_BNBBTC",{})
    bnb_info=bnb.get("info") or {}
    bnb_min=(bnb.get("minimum") or {}).get("minimum_executable_quote_estimate")
    btc_book=(out["markets"].get("spot_BTCUSDT",{}).get("book") or {})
    btc_usdt_mid=None
    if btc_book.get("bid") and btc_book.get("ask"):
        btc_usdt_mid=(btc_book["bid"]+btc_book["ask"])/2
    bnb_min_usdt=(bnb_min*btc_usdt_mid) if bnb_min is not None and btc_usdt_mid else None
    out["candidates"]["BNB-LAUNCHPOOL-DEMAND-001"]={
        "tier":2,
        "current_authority":"READINESS_ONLY_NOT_EXECUTION_AUTHORITY",
        "mapping":"BNBBTC SPOT",
        "leverage":"FORBIDDEN",
        "max_notional_chf":BNB_MAX_NOTIONAL_CHF,
        "pair_present":bnb_info.get("present"),
        "spot_trading_allowed":bnb_info.get("is_spot_trading_allowed"),
        "minimum_quote_btc_estimate":bnb_min,
        "minimum_notional_usdt_estimate_via_btcusdt":bnb_min_usdt,
        "requires_chf_conversion_at_preorder":True,
        "requires_spot_btc_quote_balance_or_authorized_asset_conversion":True,
        "live_order_now":False,
        "reason":"No eligible prospective Launchpool event; separate BNB micro-live authority still absent.",
    }

    out["candidates"]["OPTIONS-SPOTPERP-001-V2.1"]={
        "tier":2,
        "capital_compatibility":"NOT_RELEVANT_WHILE_SOURCE_FAIL_CLOSED_AND_FORWARD_GATE_UNMET",
        "resolved_forward_minimum_for_operational_milestone":10,
        "live_order_now":False,
    }
    out["candidates"]["TFG-DONCHIAN-REGIME-ADAPTATION-V1"]={
        "tier":3,"capital_compatibility":"SHADOW_ONLY","live_order_now":False
    }
    out["candidates"]["EMA6H-50X200-REGIME-DEPENDENCY-001"]={
        "tier":3,"capital_compatibility":"SHADOW_ONLY","live_order_now":False
    }
    out["candidates"]["HTF-DH03-12H-STANDALONE-FORWARD-V1"]={
        "tier":"UNRANKED_PROSPECTIVE","capital_compatibility":"SHADOW_ONLY","live_order_now":False
    }
    out["candidates"]["CED1D-0031"]={
        "tier":2,"capital_compatibility":"NOT_RELEVANT_WHILE_COLLECTOR_FAIL_CLOSED","live_order_now":False
    }

    print(json.dumps(out,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
