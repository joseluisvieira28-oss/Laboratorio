#!/usr/bin/env python3
"""Pure offline V0.3 forward paper signal evaluator, no data network or execution."""
import datetime as dt,math,re
SHA=re.compile(r"^[0-9a-f]{64}$")
START=dt.datetime(2026,11,1,tzinfo=dt.timezone.utc).timestamp()*1000
END=dt.datetime(2026,12,1,tzinfo=dt.timezone.utc).timestamp()*1000
SYMS={"BTC_USDT","ETH_USDT"}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def amount(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def has_sha(x):
    return isinstance(x,str) and SHA.fullmatch(x) is not None
def decide(asset,decision_ms,pairs,product,index_tick):
    require(asset in SYMS,"ASSET_BLOCK")
    require(type(decision_ms) is int and START<=decision_ms<END,"FUTURE_PREREG_WINDOW_ONLY")
    second=(decision_ms//1000)%60;minute=(decision_ms//60000)%10
    require(minute==0 and 20<=second<=40,"UTC_10M_SLOT_DECISION_WINDOW_BLOCK")
    require(isinstance(pairs,list) and len(pairs)==3,"NEED_EXACT_THREE_SNAPSHOT_PAIRS")
    signs=[];previous=None
    for i,pair in enumerate(pairs):
        require(pair.get("asset")==asset,"PAIR_ASSET_MISMATCH")
        t=pair.get("received_ms")
        require(type(t) is int and t<decision_ms and 0<=decision_ms-t<=18000,"NONCAUSAL_OR_STALE_PAIR")
        if previous is not None:require(4000<=t-previous<=8000,"SNAPSHOT_CADENCE_BAD")
        previous=t
        okx=pair.get("okx_spot") or {};mexc=pair.get("mexc_futures") or {}
        require(okx.get("venue")=="OKX_SPOT" and mexc.get("venue")=="MEXC_PERPETUAL","VENUE_NOT_INDEPENDENT")
        for packet in (okx,mexc):
            require(has_sha(packet.get("sha256")),"SOURCE_SHA_MISSING")
            recv=packet.get("received_ms")
            require(type(recv) is int and recv<=t and 0<=t-recv<=2000,"SOURCE_AGE_BLOCK")
            v=packet.get("imbalance")
            require(amount(v) and -1<=v<=1,"INVALID_ORDERBOOK_IMBALANCE")
            require(amount(packet.get("spread_bps")) and 0<packet["spread_bps"]<=10,"BAD_SPREAD")
        s_ts=okx.get("server_ms")
        require(type(s_ts) is int and 0<=okx["received_ms"]-s_ts<=2000,"SPOT_ASOF_CLOCK_MISSING")
        a=okx["imbalance"];b=mexc["imbalance"]
        if abs(a)<.25 or abs(b)<.25 or a*b>=0:
            signs.append(0)
        else:signs.append(1 if a>0 else -1)
    if signs==[1,1,1]:side="UP"
    elif signs==[-1,-1,-1]:side="DOWN"
    else:side="ABSTAIN"
    require(product.get("symbol")==asset and product.get("duration_min")==10
       and product.get("state")=="ONLINE","REAL_PRODUCT_NOT_ONLINE")
    require(type(product.get("received_ms")) is int and
       0<=decision_ms-product["received_ms"]<=10000 and
       has_sha(product.get("sha256")),"STALE_OR_UNHASHED_PAYOUT")
    for name in ("up_pay_rate","down_pay_rate"):
        require(amount(product.get(name)) and product[name]>0,"INVALID_SIDE_PAYOUT")
    require(index_tick.get("symbol")==asset and
       type(index_tick.get("received_ms")) is int and
       0<=decision_ms-index_tick["received_ms"]<=2000 and
       type(index_tick.get("server_ms")) is int and
       0<=index_tick["received_ms"]-index_tick["server_ms"]<=2000
       and has_sha(index_tick.get("sha256")) and
       amount(index_tick.get("index_price")) and
       index_tick["index_price"]>0,"STALE_OR_UNAUTHENTICATED_INDEX")
    q=product["up_pay_rate"] if side=="UP" else product["down_pay_rate"] if side=="DOWN" else None
    return {"study":"EVENT10M_OKX_SPOT_VS_MEXC_PERP_DIVERGENCE_V03",
       "decision_ms":decision_ms,"target_ms":decision_ms+600000,
       "asset":asset,"side":side,"qualified":side!="ABSTAIN",
       "side_payout":q,"conditional_breakeven_probability":1/(1+q) if q else None,
       "snapshot_sha256":[[p["okx_spot"]["sha256"],p["mexc_futures"]["sha256"]] for p in pairs],
       "product_sha256":product["sha256"],"index_sha256":index_tick["sha256"],
       "status":"PAPER_DIRECTION_ONLY_NO_EVENT_SERVER_PRICE_PARITY",
       "economic_edge_certified":False,"real_trade":False}
