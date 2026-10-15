"""Read-after-write LIVE-BROKER receipt reconciliation, no order placement.

A true MEXC authenticated position+order+stop snapshot is required AFTER a
fill and stop POST ACK, not inferred from POST success. This pure validator
cannot authenticate the provenance of its inputs. No LIVE_GO token produced.
Official MEXC get/order, open_positions and stoporder/list/orders fields.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_FLOOR, InvalidOperation


class ProtectHalt(ValueError): pass


def d(value, field):
    if value is None or isinstance(value,bool):
        raise ProtectHalt("MISSING_" + field)
    try:
        out=Decimal(str(value))
    except (ValueError,TypeError,InvalidOperation) as exc:
        raise ProtectHalt("BAD_" + field) from exc
    if not out.is_finite(): raise ProtectHalt("BAD_" + field)
    return out


def ident(value, field):
    if value is None or isinstance(value,bool) or not str(value).isdigit() or int(value)<=0:
        raise ProtectHalt("BAD_" + field)
    return str(value)


def same_symbol(symbol):
    if symbol not in ("SOL_USDT","BNB_USDT"):
        raise ProtectHalt("UNKNOWN_FUTURES_SYMBOL")
    return symbol


def reconcile_native_stop(
    *, order, positions, stops, symbol, external_oid, tick_size,
    mark_price, now_ms, order_read_ms, position_read_ms, stop_read_ms,
    stop_submit_ack_ms, stop_order_id=None, max_cash_risk="0.50",
    minimum_liquidation_buffer_frac="0.005",
):
    """Structural proof for one filled 10x isolated 1-contract long.

    NO network or trading. All timestamps in UTC milliseconds. Strict
    close-quantity equality, mark trigger (2), initial 4% stop based on
    *actual fill*, and read-after-ack. Designed for nonlatched initial stop;
    trailing updates need separate state-machine evidence.
    """
    same_symbol(symbol)
    if not isinstance(order,dict) or not isinstance(positions,list) or not isinstance(stops,list):
        raise ProtectHalt("INCOMPLETE_BROKER_READ_SNAPSHOT")
    for name,t in (("ORDER",order_read_ms),("POSITION",position_read_ms),("STOP",stop_read_ms)):
        if type(t) is not int or type(now_ms) is not int or not 0<=now_ms-t<=5000:
            raise ProtectHalt("STALE_"+name+"_READ")
    if type(stop_submit_ack_ms) is not int or stop_submit_ack_ms<=0 or stop_read_ms<=stop_submit_ack_ms:
        raise ProtectHalt("STOP_NOT_READ_AFTER_SUBMISSION_ACK")
    if order.get("symbol")!=symbol or str(order.get("externalOid"))!=str(external_oid):
        raise ProtectHalt("ENTRY_ORDER_IDENTITY_MISMATCH")
    if not external_oid or len(str(external_oid))>32:
        raise ProtectHalt("ENTRY_EXTERNAL_ID_MALFORMED")
    oid=ident(order.get("orderId"),"ORDER_ID")
    posid=ident(order.get("positionId"),"FILLED_POSITION_ID")
    if order.get("state")!=3 or order.get("side")!=1 or order.get("openType")!=1 or order.get("leverage")!=10 or order.get("positionMode")!=1:
        raise ProtectHalt("ENTRY_NOT_CONFIRMED_AS_FILLED_LONG_10X_HEDGE_ISOLATED")
    if d(order.get("dealVol"),"ORDER_FILLED_VOLUME")!=1:
        raise ProtectHalt("ENTRY_FILL_QUANTITY_NOT_EXACTLY_ONE")
    fill=d(order.get("dealAvgPrice"),"ORDER_FILLED_AVERAGE")
    if fill<=0:raise ProtectHalt("BAD_ENTRY_FILL_PRICE")
    pos_matches=[p for p in positions if isinstance(p,dict) and str(p.get("positionId"))==posid]
    if len(pos_matches)!=1:
        raise ProtectHalt("FILLED_POSITION_ABSENT_OR_AMBIGUOUS")
    p=pos_matches[0]
    if p.get("symbol")!=symbol or p.get("positionType")!=1 or p.get("openType")!=1 or p.get("leverage")!=10 or p.get("state")!=1 or p.get("autoAddIm") is not False:
        raise ProtectHalt("POSITION_ISOLATED_10X_LONG_OR_STATE_UNVERIFIED")
    if d(p.get("holdVol"),"POSITION_HOLD_VOLUME")!=1:
        raise ProtectHalt("POSITION_SIZE_DIFFERENT_FROM_ORDER_FILL")
    avg=d(p.get("holdAvgPrice"),"POSITION_AVERAGE_PRICE")
    if avg<=0 or abs(avg-fill)/fill>Decimal("0.0000001"):
        raise ProtectHalt("FILL_AVERAGE_POSITION_PRICE_MISMATCH")
    liquidation=d(p.get("liquidatePrice"),"LIQUIDATION_PRICE")
    if liquidation<=0:
        raise ProtectHalt("LIQUIDATION_NOT_ESTABLISHED")
    tick=d(tick_size,"TICK_SIZE")
    if tick<=0:raise ProtectHalt("BAD_TICK_SIZE")
    expected_stop=(fill*Decimal("0.96")/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
    m=d(mark_price,"MARK_PRICE")
    if m<=expected_stop:
        raise ProtectHalt("MARK_ALREADY_BELOW_OR_AT_STOP")
    if expected_stop-liquidation < fill*d(minimum_liquidation_buffer_frac,"LIQUIDATION_BUFFER_FRAC"):
        raise ProtectHalt("LIQUIDATION_TOO_NEAR_OR_ABOVE_STOP")
    if len(positions)!=1:
        # A second BNB/SOL position must be independently reconciled in an
        # account-wide risk ledger; never label this single-position gate global GO.
        raise ProtectHalt("EXTRA_ACCOUNT_POSITION_UNRECONCILED")
    eligible=[]
    for s in stops:
        if not isinstance(s,dict):raise ProtectHalt("MALFORMED_STOP_ENTRY")
        if str(s.get("positionId"))==posid:
            eligible.append(s)
    if len(eligible)!=1:
        raise ProtectHalt("NOT_EXACTLY_ONE_POSITION_STOP")
    st=eligible[0]
    stopid=ident(st.get("id"),"STOP_ORDER_ID")
    if stop_order_id is not None and stopid!=ident(stop_order_id,"EXPECTED_STOP_ID"):
        raise ProtectHalt("POST_ACK_AND_READBACK_STOP_ID_MISMATCH")
    if st.get("symbol")!=symbol or st.get("positionType")!=1:
        raise ProtectHalt("STOP_POSITION_SYMBOL_OR_SIDE_MISMATCH")
    if st.get("state")!=1 or st.get("isFinished")!=0:
        raise ProtectHalt("STOP_NOT_ACTIVE_UNTRIGGERED")
    if d(st.get("vol"),"STOP_VOLUME")!=1:
        raise ProtectHalt("STOP_DOES_NOT_PROTECT_EXACT_POSITION_VOLUME")
    if "lossTrend" in st and st["lossTrend"]!=2:
        raise ProtectHalt("STOP_NOT_USING_FAIR_MARK_TRIGGER")
    current_stop=d(st.get("stopLossPrice"),"BROKER_STOP_PRICE")
    if current_stop!=expected_stop:
        raise ProtectHalt("BROKER_STOP_NOT_EXACT_4PCT_FILLED_ENTRY_TICK_ROUNDED")
    if st.get("takeProfitPrice") not in (None,0,0.0,"0","0.0",""):
        raise ProtectHalt("EXTRANEOUS_TAKE_PROFIT_CHANGES_ORIGINAL_STRATEGY")
    base_qty=Decimal("0.1") if symbol=="SOL_USDT" else Decimal("0.01")
    # Conservative costs scenario: taker 8bps each, slippage 2bps each,
    # 5bps funding reserve. No proof of actual future stop fill.
    slip=Decimal("0.0002")
    taker=Decimal("0.0008")
    funding=Decimal("0.0005")
    entry_stress=fill*(1+slip)
    exit_stress=current_stop*(1-slip)
    at_stop=base_qty*(entry_stress-exit_stress+taker*(entry_stress+exit_stress)+funding*entry_stress)
    if at_stop>d(max_cash_risk,"MAX_CASH_RISK"):
        raise ProtectHalt("CASH_RISK_EXCEEDS_HALF_USDT_MODEL")
    return {
        "state":"STRUCTURALLY_MATCHED_ACTIVE_NATIVE_STOP_AFTER_FILL",
        "symbol":symbol,"position_id":posid,"order_id":oid,"stop_id":stopid,
        "size_contracts":"1","actual_fill":str(fill),
        "exchange_stop":str(current_stop),"modeled_risk_usdt":str(at_stop),
        "stop_readback_after_post_ack":True,
        "one_snapshot_only":True,
        "authenticated_origin_independently_proven":False,
        "liquidation_buffer_absolute_usdt":str(expected_stop-liquidation),
        "real_exchange_execution_performed_by_this_module":False,
        "trading_authority":"NONE",
    }
