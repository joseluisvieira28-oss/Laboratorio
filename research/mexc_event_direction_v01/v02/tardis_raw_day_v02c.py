#!/usr/bin/env python3
"""Source only: 1440 public Tardis raw minute receipts, no outcomes."""
import concurrent.futures,datetime as dt,gzip,hashlib,json,math,pathlib,time
import urllib.error,urllib.parse,urllib.request
DAY=dt.datetime(2026,4,1,tzinfo=dt.timezone.utc)
SYMS=("BTCUSDT","ETHUSDT")
PREV={"BTCUSDT":1318,"ETHUSDT":1013}
PATH=pathlib.Path("artifacts/triple_flow_v02c")
API="https://api.tardis.dev/v1/data-feeds/bybit"
def decode(offset,raw):
    data=gzip.decompress(raw) if raw[:2]==b"\x1f\x8b" else raw
    if len(data)>20_000_000:raise ValueError("DECODED_OVERSIZE")
    res={"offset":offset,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
         "empty_response":len(data)==0,"disconnect_markers":0,"messages":0,
         "events":{s:0 for s in SYMS}}
    since=DAY+dt.timedelta(minutes=offset)
    until=since+dt.timedelta(minutes=1)
    for line in data.decode("utf-8").splitlines():
        if line.strip()=="":
            res["disconnect_markers"]+=1
            continue
        stamp,sep,body=line.partition(" ")
        if not sep:raise ValueError("LOCAL_TIMESTAMP_ABSENT")
        t=dt.datetime.fromisoformat(stamp.replace("Z","+00:00"))
        if t.tzinfo is None or not(since<=t<until):
            raise ValueError("LOCAL_TIMESTAMP_WRONG_MINUTE")
        obj=json.loads(body)
        topic=obj.get("topic")
        if topic not in ("allLiquidation.BTCUSDT","allLiquidation.ETHUSDT"):
            raise ValueError("WRONG_TOPIC")
        sym=topic.split(".")[-1]
        records=obj.get("data")
        if not isinstance(records,list):raise ValueError("NO_DATA_LIST")
        for x in records:
            if not isinstance(x,dict) or x.get("s")!=sym or x.get("S") not in ("Buy","Sell"):
                raise ValueError("BAD_LIQUIDATION_IDENTITY")
            try:v=float(x["v"]);p=float(x["p"]);tms=int(x["T"])
            except (ValueError,TypeError,KeyError):raise ValueError("INVALID_LIQUIDATION_VALUE")
            if not(math.isfinite(v) and math.isfinite(p) and v>0 and p>0 and tms>0):
                raise ValueError("BAD_LIQUIDATION_VALUE")
            res["events"][sym]+=1
        res["messages"]+=1
    return res
def one(offset):
    query=urllib.parse.urlencode({"from":"2026-04-01","offset":offset,
        "filters":json.dumps([{"channel":"allLiquidation","symbols":list(SYMS)}],separators=(",",":"))})
    url=API+"?"+query
    for trial in range(3):
        try:
            req=urllib.request.Request(url,headers={"Accept-Encoding":"gzip",
                "User-Agent":"CryptoLab-Public-SourceOnly/0.2c"})
            with urllib.request.urlopen(req,timeout=25) as z:
                if z.status!=200:raise ValueError("HTTP_NON200")
                raw=z.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError("RAW_TOO_LARGE")
            d=decode(offset,raw);d["status"]="READABLE"
            return d
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and trial<2:
                time.sleep(0.4*(trial+1));continue
            return {"offset":offset,"status":"BLOCKED","error":"HTTP_"+str(e.code)}
        except Exception as e:
            return {"offset":offset,"status":"BLOCKED","error":type(e).__name__+":"+str(e)[:120]}
    return {"offset":offset,"status":"BLOCKED","error":"NO_RESULT"}
def main():
    assert decode(0,gzip.compress(b""))["disconnect_markers"]==0
    assert decode(0,gzip.compress(b"\n"))["disconnect_markers"]==1
    print("RAW_EMPTY_VS_DISCONNECT_TEST_PASS",flush=True)
    PATH.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        receipts=list(pool.map(one,range(1440)))
    good=[x for x in receipts if x.get("status")=="READABLE"]
    sums={s:sum(x["events"][s] for x in good) for s in SYMS}
    complete=len(good)==1440
    parity=complete and sums==PREV
    out={"study":"TRIPLE_FLOW_V02C_RAW_FULLDAY",
         "gate":"RAW_DAY_READABLE" if complete else "RAW_DAY_PARTIAL",
         "minutes_readable":len(good),"minutes_total":1440,
         "messages":sum(x["messages"] for x in good),
         "raw_liquidations":sums,"frozen_normalized_counts":PREV,
         "raw_csv_count_parity":parity,
         "disconnect_markers":sum(x["disconnect_markers"] for x in good),
         "empty_raw_minutes":sum(x["empty_response"] for x in good),
         "source_errors":1440-len(good),
         "source_census_complete_proven":False,
         "empty_minutes_zero_liquidations_proven":False,
         "can_open_outcomes":False,"economic_verdict":"NOT_TESTED",
         "orders":0,"private_requests":0,"protected_holdout_accessed":False,
         "receipts":receipts}
    (PATH/"whole_day_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="receipts"},indent=2),flush=True)
    if not complete:raise SystemExit(2)
if __name__=="__main__":main()
