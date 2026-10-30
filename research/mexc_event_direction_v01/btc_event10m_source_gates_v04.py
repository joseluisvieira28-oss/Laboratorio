"""Pure offline as-of coherence validation for BTC-only source preflight V0.4."""
def asof(snapshots,product,index,decision_ms):
    if not isinstance(snapshots,list) or len(snapshots)!=3 or type(decision_ms)!=int:
        raise ValueError("THREE_PAIRS_REQUIRED")
    times=[]
    checks={}
    for k,pair in enumerate(snapshots):
        t=pair.get("received_ms")
        if type(t)!=int or t>=decision_ms or decision_ms-t>18000:
            raise ValueError("PAIR_NONCAUSAL_OR_OLD")
        times.append(t)
        if pair.get("asset")!="BTC_USDT":raise ValueError("NOT_BTC")
        for venue in ("okx_spot","mexc_futures"):
            pkt=pair.get(venue) or {}
            if type(pkt.get("received_ms"))!=int or not 0<=t-pkt["received_ms"]<=2000:
                raise ValueError("BOOK_AGE_BAD")
            if type(pkt.get("sha256"))!=str or len(pkt["sha256"])!=64:
                raise ValueError("RAW_SHA_MISSING")
            if venue=="okx_spot":
                s=pkt.get("server_ms")
                if type(s)!=int or not 0<=pkt["received_ms"]-s<=2000:
                    raise ValueError("OKX_SERVER_TIMESTAMP_BAD")
        if k>0 and not 4000<=times[k]-times[k-1]<=8000:
            raise ValueError("BOOK_CADENCE_BAD")
    checks["three_orderbooks"]=True
    checks["last_book_fresh"]=all(0<=decision_ms-snapshots[-1][v]["received_ms"]<=2000
        for v in ("okx_spot","mexc_futures"))
    checks["product_fresh"]=(product.get("symbol")=="BTC_USDT" and product.get("state")=="ONLINE" and
        product.get("duration_min")==10 and type(product.get("received_ms"))==int and
        0<=decision_ms-product["received_ms"]<=10000 and
        type(product.get("sha256"))==str and len(product["sha256"])==64 and
        all(isinstance(product.get(x),(int,float)) and product[x]>0 for x in ("up_pay_rate","down_pay_rate")))
    checks["index_fresh"]=(index.get("symbol")=="BTC_USDT" and type(index.get("received_ms"))==int and
        0<=decision_ms-index["received_ms"]<=2000 and
        type(index.get("server_ms"))==int and 0<=index["received_ms"]-index["server_ms"]<=2000 and
        type(index.get("sha256"))==str and len(index["sha256"])==64 and
        isinstance(index.get("index_price"),(float,int)) and index["index_price"]>0)
    return checks
