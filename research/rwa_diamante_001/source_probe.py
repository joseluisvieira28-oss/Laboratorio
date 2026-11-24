import datetime as dt
import hashlib, json, pathlib, urllib.request, urllib.parse, urllib.error, math
from decimal import Decimal
OUT = pathlib.Path("rwa_source_receipts")
OUT.mkdir(exist_ok=True)
SYMBOLS = ("NVDA","TSLA","AAPL","SPY","QQQ")
records = []
def get(name, url, params=None):
    if params: url += "?" + urllib.parse.urlencode(params)
    start = dt.datetime.now(dt.timezone.utc)
    status = None
    raw = b""
    error = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"RWA001-public-research/1.0","Accept":"application/json"})
        with urllib.request.urlopen(req, timeout=12) as response:
            status = response.status
            raw = response.read(4_000_001)
        if len(raw)>4_000_000: raise ValueError("response cap")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read(8192)
        error = str(exc)
    except Exception as exc: error = str(exc)
    end = dt.datetime.now(dt.timezone.utc)
    (OUT / (name+".raw")).write_bytes(raw)
    rec = dict(name=name,url=url,http=status,error=error,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),start=start.isoformat(),end=end.isoformat())
    records.append(rec)
    try:
        data=json.loads(raw)
        if not isinstance(data,dict): raise ValueError("not object")
        if data.get("error"): rec["api_error"]=data["error"]
        return data if status==200 and not error and not data.get("error") else {}
    except Exception: return {}
def book_summary(payload):
    vals=list(payload.get("result",{}).values())
    if len(vals)!=1: return None
    v=vals[0]
    try:
        asks=[(Decimal(a[0]),Decimal(a[1])) for a in v["asks"]]
        bids=[(Decimal(a[0]),Decimal(a[1])) for a in v["bids"]]
        if not asks or not bids or any(not p.is_finite() or not q.is_finite() or p<=0 or q<=0 for p,q in asks+bids): return None
        if asks!=sorted(asks,key=lambda x:x[0]) or bids!=sorted(bids,key=lambda x:x[0],reverse=True) or asks[0][0]<bids[0][0]: return None
        def vwap(levels,qty):
            rem=qty; value=Decimal(0)
            for p,q in levels:
                take=min(rem,q); value+=take*p;rem-=take
                if rem==0:return value/qty
            return None
        qty=Decimal(100)/asks[0][0]
        a,b=vwap(asks,qty),vwap(bids,qty)
        mid=(asks[0][0]+bids[0][0])/2
        return dict(bid=str(bids[0][0]),ask=str(asks[0][0]),spread_bps=float((asks[0][0]-bids[0][0])/mid*10000),roundtrip_100usd_bps=float((1-b*Decimal("0.999")/(a*Decimal("1.001")))*10000) if a and b else None,depth_sufficient=a is not None and b is not None)
    except (KeyError,ValueError,ArithmeticError,TypeError,IndexError): return None
def main():
    root="https://api.kraken.com/0/public/"
    pairs=get("pairs",root+"AssetPairs",{"aclass_base":"tokenized_asset"})
    markets=pairs.get("result",{})
    summary={}
    for s in SYMBOLS:
        candidates=[(k,v) for k,v in markets.items() if str(v.get("wsname","")).upper()==s+"X/USD" or str(v.get("altname","")).upper()==s+"XUSD"]
        item={"matches":[k for k,v in candidates]}
        if len(candidates)==1:
            k,v=candidates[0]
            item["metadata"]={key:v.get(key) for key in ("altname","wsname","base","quote","status")}
            p={"pair":k,"asset_class":"tokenized_asset"}
            item["book"]=book_summary(get(s+"_depth",root+"Depth",dict(p,count=20)))
            o=get(s+"_ohlc",root+"OHLC",dict(p,interval=60))
            rows=[x for key,x in o.get("result",{}).items() if key!="last" and isinstance(x,list)]
            if len(rows)==1 and rows[0]:
                rr=rows[0]
                item["ohlc"]={"rows":len(rr),"first":rr[0][0],"last_uncommitted":rr[-1][0],"weekend_positive_volume_rows":sum(1 for row in rr[:-1] if dt.datetime.fromtimestamp(row[0],dt.timezone.utc).weekday()>=5 and float(row[6])>0)}
        # Yahoo is an unauthenticated candidate trade-bar source, not executable BBO.
        y=get(s+"_yahoo","https://query1.finance.yahoo.com/v8/finance/chart/"+s,{"range":"5d","interval":"5m"})
        try:
            z=y["chart"]["result"][0]
            item["cash_proxy"]={"symbol":z["meta"]["symbol"],"rows":len(z["timestamp"]),"first":z["timestamp"][0],"last":z["timestamp"][-1]}
        except (KeyError,TypeError,IndexError): item["cash_proxy"]=None
        summary[s]=item
    result={"classification":"SOURCE_PROBE_ONLY_NO_ECONOMIC_TEST","markets":summary,"requests":records,"alpaca":"Not attempted: authentication required; no credentials authorized.","limitations":["One-time depth snapshot is not historical executable price","Yahoo trade candles not stock BBO","No entry or outcome examined","No automatic collection or orders"]}
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
