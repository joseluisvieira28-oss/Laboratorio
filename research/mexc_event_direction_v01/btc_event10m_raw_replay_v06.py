#!/usr/bin/env python3
"""Independently reconstruct V0.5 frozen source features from archived raw HTTP bytes.
Does not accept packet-declared imbalance/price/payout as ground truth.
Does NOT attest source HTTPS transport or Event Futures actual execution parity.
"""
import json,math,hashlib
from pathlib import PurePosixPath
def fail(c,msg):
    if not c:raise ValueError(msg)
def n(v):
    try:
        x=float(v);fail(math.isfinite(x) and x>0,"NONPOSITIVE_OR_NONFINITE")
        return x
    except (TypeError,ValueError):raise ValueError("BAD_NUMERIC")
def approx(a,b):
    return isinstance(b,(float,int)) and not isinstance(b,bool) and math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11)
def load_bytes(archive,name):
    fail(isinstance(name,str) and name in archive.namelist(),"RAW_SOURCE_MISSING")
    b=archive.read(name)
    return json.loads(b)
def bstats(bids,asks):
    fail(isinstance(bids,list) and isinstance(asks,list),"NO_BOOK_ROWS")
    fail(len(bids)>=5 and len(asks)>=5,"BOOK_DEPTH_INSUFFICIENT")
    b=[(n(x[0]),n(x[1])) for x in bids[:20]]
    a=[(n(x[0]),n(x[1])) for x in asks[:20]]
    fail(all(b[i][0]>=b[i+1][0] for i in range(len(b)-1)),"BID_ORDER_WRONG")
    fail(all(a[i][0]<=a[i+1][0] for i in range(len(a)-1)),"ASK_ORDER_WRONG")
    fail(b[0][0]<a[0][0],"CROSSED_BOOK")
    bn=sum(p*q for p,q in b[:5]);an=sum(p*q for p,q in a[:5])
    spread=20000*(a[0][0]-b[0][0])/(a[0][0]+b[0][0])
    fail(0<spread<=10,"SPREAD_GATE_FAIL")
    return {"imbalance":(bn-an)/(bn+an),"spread_bps":spread,
         "bid_notional":bn,"ask_notional":an}
def book_packet_equals_raw(archive,packet,venue):
    filename=packet["raw_file"]
    fail(isinstance(filename,str) and PurePosixPath(filename).name==filename,"UNSAFE_FILENAME")
    data=load_bytes(archive,"raw/"+filename)
    if venue=="OKX_SPOT":
        fail(packet.get("venue")=="OKX_SPOT","VENUE_SPOOFING")
        records=data.get("data") or []
        fail(str(data.get("code"))=="0" and len(records)==1,"OKX_RAW_SCHEMA")
        v=records[0]
        fail(type(packet.get("server_ms")) is int and packet["server_ms"]==int(v["ts"]),
             "OKX_SERVER_TIME_NOT_IN_RAW")
        metrics=bstats(v.get("bids"),v.get("asks"))
    else:
        fail(packet.get("venue")=="MEXC_PERPETUAL","VENUE_SPOOFING")
        fail(data.get("success") is True and isinstance(data.get("data"),dict),"MEXC_RAW_SCHEMA")
        v=data["data"]
        fail(packet.get("book_server_ms_unverified")==v.get("timestamp"),"MEXC_BOOK_TIME_NOT_RAW")
        metrics=bstats(v.get("bids"),v.get("asks"))
    for key,val in metrics.items():
        fail(approx(val,packet.get(key)),"BOOK_FEATURE_NOT_REPRODUCED_"+venue+"_"+key)
def validate_eight(archive,decision):
    source=decision.get("source_receipt") or {}
    pairs=source.get("samples") or []
    fail(len(pairs)==3,"RAW_THREE_PAIRS_REQUIRED")
    for i,pair in enumerate(pairs):
        fail(pair.get("asset")=="BTC_USDT","NOT_BTC_PAIR")
        for label,venue,prefix in (("okx_spot","OKX_SPOT","okx_book_"),
                                   ("mexc_futures","MEXC_PERPETUAL","mexc_book_")):
            packet=pair.get(label) or {}
            fail(packet.get("raw_file")==f"{prefix}{i}.json","WRONG_BOOK_SEQUENCE")
            book_packet_equals_raw(archive,packet,venue)
    product=source.get("product") or {}
    fail(product.get("raw_file")=="mexc_event_contract_detail.json","WRONG_PRODUCT_FILE")
    obj=load_bytes(archive,"raw/mexc_event_contract_detail.json")
    fail(obj.get("success") is True and isinstance(obj.get("data"),list),"PRODUCT_RAW_SCHEMA")
    matches=[v for v in obj["data"] if v.get("symbol")=="BTC_USDT"]
    fail(len(matches)==1,"EXACT_BTC_EVENT_MISSING")
    p=matches[0]
    cycles=(p.get("cycleConfigMap") or {}).get("MINUTE") or []
    ten=[v for v in cycles if v.get("val")==10]
    fail(len(ten)==1,"NO_EXACT_10_MINUTE_CYCLE")
    fail(product.get("symbol")=="BTC_USDT" and product.get("duration_min")==10
         and product.get("state")==p.get("state") and product.get("contract_id")==p.get("contractId"),
         "PRODUCT_STATE_OR_CONTRACT_NOT_IN_RAW")
    for key,rawkey in (("up_pay_rate","upPayRate"),("down_pay_rate","downPayRate")):
        fail(approx(n(ten[0].get(rawkey)),product.get(key)),"DYNAMIC_PAYOUT_NOT_IN_RAW_"+key)
    quote=source.get("index") or {}
    fail(quote.get("raw_file")=="mexc_index.json","WRONG_INDEX_FILE")
    obj=load_bytes(archive,"raw/mexc_index.json")
    idx=obj.get("data") or {}
    fail(obj.get("success") is True and idx.get("symbol")=="BTC_USDT"
       and quote.get("symbol")=="BTC_USDT" and type(quote.get("server_ms")) is int
       and quote["server_ms"]==idx.get("timestamp"),"INDEX_SYMBOL_OR_SERVER_TS_NOT_IN_RAW")
    fail(approx(n(idx.get("indexPrice")),quote.get("index_price")),"INDEX_PRICE_NOT_IN_RAW")
    return True
