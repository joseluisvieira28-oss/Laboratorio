"""V06 authenticated MEXC Futures READ-ONLY preflight, no trading authority.

Unlike the original shape-only receipt, validates concrete USDT equity,
fee-band data, 10x API-fee leverage eligibility, Hedge Mode and *all* open-order
pages. All results represent one fleeting account snapshot; NOT LIVE_GO.
Only emit allowlisted fields, never raw sensitive broker replies.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
import sys

from engine.three_convex_v06.mexc_futures_live_transport import (
    FuturesV06Transport, PrivateKey, MEXCTransportHalt,
)

MAKER_API_FLOOR = Decimal("0.0006")  # MEXC API Futures notice effective 2026-06-01
TAKER_API_FLOOR = Decimal("0.0008")
ORDER_PAGE_SIZE = 100
MAX_PAGES = 100


class ReadonlyGate(ValueError):
    pass


def amount(value, field):
    if value is None or isinstance(value, bool):
        raise ReadonlyGate("MISSING_OR_INVALID_" + field)
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ReadonlyGate("MISSING_OR_INVALID_" + field) from exc
    if not out.is_finite() or out < 0:
        raise ReadonlyGate("MISSING_OR_INVALID_" + field)
    return out


def count_list(v, field):
    if not isinstance(v, list) or any(not isinstance(x, dict) for x in v):
        raise ReadonlyGate("UNVERIFIED_" + field + "_RESPONSE_SHAPE")
    return len(v)


def strict_order_pages(client):
    """Fail closed when page metadata and first-page size leave ambiguity."""
    rows = client.open_orders()
    if rows is None:
        raise ReadonlyGate("UNVERIFIED_OPEN_ORDERS_NULL")
    if isinstance(rows, list):
        first = count_list(rows, "ORDERS")
        if first >= ORDER_PAGE_SIZE:
            raise ReadonlyGate("OPEN_ORDERS_PAGINATION_NOT_PROVEN")
        return first, 1
    if not isinstance(rows, dict) or not isinstance(rows.get("resultList"), list):
        raise ReadonlyGate("UNVERIFIED_OPEN_ORDERS_RESPONSE_SHAPE")
    pages = 1
    first_rows = count_list(rows["resultList"], "ORDERS")
    meta = next((rows[k] for k in
                 ("totalPage","total_page","pageCount","page_count") if rows.get(k) is not None), None)
    if meta is None:
        if first_rows >= ORDER_PAGE_SIZE:
            raise ReadonlyGate("OPEN_ORDERS_PAGINATION_NOT_PROVEN")
        raw_count = rows.get("totalCount")
        if raw_count is not None and amount(raw_count, "ORDER_TOTAL_COUNT") != first_rows:
            raise ReadonlyGate("OPEN_ORDERS_TOTAL_INCONSISTENT")
        return first_rows, pages
    try:
        maxpage = int(meta)
    except (ValueError, TypeError) as exc:
        raise ReadonlyGate("OPEN_ORDERS_INVALID_TOTAL_PAGES") from exc
    if maxpage < 0 or maxpage > MAX_PAGES:
        raise ReadonlyGate("OPEN_ORDERS_INVALID_TOTAL_PAGES")
    if maxpage == 0 and first_rows:
        raise ReadonlyGate("OPEN_ORDERS_PAGINATION_CONFLICT")
    if maxpage <= 1:
        if rows.get("totalCount") is not None and amount(rows["totalCount"], "TOTAL_COUNT") != first_rows:
            raise ReadonlyGate("OPEN_ORDERS_TOTAL_INCONSISTENT")
        return first_rows, 1
    total = first_rows
    for p in range(2,maxpage+1):
        next_page = client._exchange(
            "GET", "/api/v1/private/order/list/open_orders",
            {"page_num":p, "page_size":ORDER_PAGE_SIZE}
        )
        if not isinstance(next_page, dict) or not isinstance(next_page.get("resultList"), list):
            raise ReadonlyGate("OPEN_ORDERS_SUBSEQUENT_PAGE_UNKNOWN")
        total += count_list(next_page["resultList"], "ORDERS")
        pages += 1
    if rows.get("totalCount") is not None and amount(rows["totalCount"], "TOTAL_COUNT") != total:
        raise ReadonlyGate("OPEN_ORDERS_TOTAL_INCONSISTENT")
    return total, pages


def usdt_balance(assets):
    if not isinstance(assets, list):
        raise ReadonlyGate("ASSETS_NOT_LIST")
    usdt = [v for v in assets if isinstance(v, dict) and v.get("currency")=="USDT"]
    if len(usdt)!=1:
        raise ReadonlyGate("USDT_ASSET_NOT_UNIQUE")
    row = usdt[0]
    balance = amount(row.get("equity"), "USDT_EQUITY")
    available = amount(row.get("availableBalance"), "USDT_AVAILABLE")
    return {"usdt_equity":str(balance),"usdt_available":str(available)}


def fee_summary(raw):
    if not isinstance(raw, dict):
        raise ReadonlyGate("FEES_NOT_DICT")
    if not any(k in raw for k in ("realMakerFee","originalMakerFee")) or not any(
        k in raw for k in ("realTakerFee","originalTakerFee")
    ):
        raise ReadonlyGate("MISSING_MAKER_TAKER_FEE_DETAILS")
    maker = [MAKER_API_FLOOR]
    taker = [TAKER_API_FLOOR]
    for key, rates in (("maker", maker),("taker",taker)):
        for label in ("original"+key.title()+"Fee", "real"+key.title()+"Fee"):
            if label in raw:
                rates.append(amount(raw[label],label))
        for bands in ("tieredFeeRates","leverageFeeRates"):
            options=raw.get(bands) or []
            if not isinstance(options,list):
                raise ReadonlyGate("MALFORMED_FEE_TIERS")
            for row in options:
                if not isinstance(row,dict):
                    raise ReadonlyGate("MALFORMED_FEE_TIERS")
                for label in (key+"FeeRate","real"+key.title()+"Fee"):
                    if label in row:
                        rates.append(amount(row[label],label))
    return {
        "api_fee_model_maker_bps":str(max(maker)*10000),
        "api_fee_model_taker_bps":str(max(taker)*10000),
        "maker_taker_fee_floor_applied": True,
        "fee_mode":str(raw.get("feeRateMode","NOT_SPECIFIED")),
        "ten_x_eligible_from_reported_api_fee_bounds":leverage_eligible(raw)
    }


def leverage_eligible(raw):
    if "minLeverage" not in raw or "maxLeverage" not in raw:
        return "UNKNOWN_API_LIMITS_MISSING"
    try:
        low = int(raw["minLeverage"])
        high = int(raw["maxLeverage"])
    except (TypeError,ValueError) as exc:
        raise ReadonlyGate("INVALID_LEVERAGE_LIMITS") from exc
    if low < 1 or high < low:
        raise ReadonlyGate("INVALID_LEVERAGE_LIMITS")
    return low <= 10 <= high


def inspect(client):
    try:
        positions = count_list(client.open_positions(), "OPEN_POSITIONS")
        orders, pages = strict_order_pages(client)
        stops = count_list(client.open_stops(), "OPEN_STOPS")
        mode = client.position_mode()
        if type(mode) is not int or mode not in (1,2):
            raise ReadonlyGate("UNKNOWN_BROKER_POSITION_MODE")
        balance = usdt_balance(client.account_assets())
        fees = {sym:fee_summary(client.account_fees(sym))
                for sym in ("SOL_USDT","BNB_USDT")}
        now = datetime.now(timezone.utc).isoformat()
        return {
            "checked_at_utc": now,
            "status":"AUTHENTICATED_ACCOUNT_VALUES_READ_NO_LIVE_GO",
            "private_api_read_only":True,
            "open_positions_count":positions,
            "open_orders_count_all_pages":orders,
            "open_order_pages_checked":pages,
            "open_stops_count":stops,
            "broker_account_flat_observed_once":positions==0 and orders==0 and stops==0,
            "position_mode_code":mode,
            "position_mode": "HEDGE" if mode==1 else "ONE_WAY",
            **balance,
            "fees_by_symbol": fees,
            "account_usdt_equity_authenticated_read": True,
            "account_equity_independently_reconciled": False,
            "exchange_contract_tick_lot_verified": False,
            "isolated_10x_configured_on_position": False,
            "broker_order_transport_present_in_library":True,
            "broker_order_execution_path_armed":False,
            "position_stop_lifecycle_proven":False,
            "trading_authority":"NONE"
        }
    except (MEXCTransportHalt,ReadonlyGate,ValueError,TypeError) as exc:
        return {
            "status":"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED",
            "reason":str(exc) if isinstance(exc,ReadonlyGate) else type(exc).__name__,
            "trading_authority":"NONE",
            "broker_order_execution_path_armed":False
        }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--account-check",action="store_true")
    opts=p.parse_args(argv)
    if not opts.account_check:
        print(json.dumps({"status":"NO_COMMAND_REQUESTED","trading_authority":"NONE"}))
        return 2
    try:
        creds=PrivateKey(os.environ.get("MEXC_API_KEY",""),
                         os.environ.get("MEXC_API_SECRET",""))
        report=inspect(FuturesV06Transport(creds))
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0 if report["status"]=="AUTHENTICATED_ACCOUNT_VALUES_READ_NO_LIVE_GO" else 2
    except Exception as exc:
        print(json.dumps({"status":"NO_ORDER_FAIL_CLOSED",
                          "exception_type":type(exc).__name__,
                          "trading_authority":"NONE"}))
        return 2


if __name__=="__main__":
    sys.exit(main())
