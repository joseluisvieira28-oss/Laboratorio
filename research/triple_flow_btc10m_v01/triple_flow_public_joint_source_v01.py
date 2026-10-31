#!/usr/bin/env python3
"""BTC Triple Flow V0.1: preregistered 150s PUBLIC SOURCE ONLY.
NO predictions, outcomes, payout PnL, trading, account or private API calls.
"""
import argparse,asyncio,datetime as dt,hashlib,json,math,pathlib,time,urllib.request
import websockets

ROOT=pathlib.Path("artifacts/triple_flow_btc10m_public_joint_v01")
WSS="wss://stream.bybit.com/v5/public/linear"
URLS={
 "okx_spot_trades":"https://www.okx.com/api/v5/market/trades?instId=BTC-USDT&limit=100",
 "mexc_perp_deals":"https://contract.mexc.com/api/v1/contract/deals/BTC_USDT?limit=100",
 "mexc_perp_index":"https://contract.mexc.com/api/v1/contract/index_price/BTC_USDT",
 "mexc_perp_depth":"https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20",
}
EXPECTED_DURATION=150
PERIOD=5
def ms():return time.time_ns()//1000000
def pos(x):
    v=float(x)
    if not math.isfinite(v) or v<=0:raise ValueError("NONPOSITIVE_OR_NONFINITE")
    return v
def age(now,stamp,limit=2000):
    if type(stamp) is not int or not 0<=now-stamp<=limit:
        raise ValueError("SOURCE_TIMESTAMP_STALE_OR_FUTURE")
    return now-stamp
class Writer:
 def __init__(self,filename):
    ROOT.mkdir(parents=True,exist_ok=True);self.path=ROOT/filename
    self.f=self.path.open("wb");self.lines=0;self.hasher=hashlib.sha256()
 def write(self,venue,raw,recv,**kws):
    b=raw if isinstance(raw,bytes) else raw.encode("utf-8")
    row={"venue":venue,"received_ms":recv,"source_sha256":hashlib.sha256(b).hexdigest(),
         "raw_utf8":b.decode("utf-8"),**kws}
    line=(json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
    self.f.write(line);self.hasher.update(line);self.lines+=1
 def finish(self):
    self.f.flush();self.f.close()
    return {"file":self.path.name,"sha256":self.hasher.hexdigest(),"rows":self.lines,
      "size_bytes":self.path.stat().st_size}
def validate_bybit_trade(x,recv):
    if not isinstance(x,dict) or x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):
        raise ValueError("BYBIT_TRADE_SCHEMA_SIDE")
    t=x.get("T");age(recv,t)
    pos(x.get("p"));pos(x.get("v"))
    if x.get("i") is None:raise ValueError("BYBIT_TRADE_NO_ID")
    return {"side":x["S"],"source_ms":t,"notional_proxy":pos(x["p"])*pos(x["v"])}
def validate_liquidation(x,recv):
    if not isinstance(x,dict) or x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):
        raise ValueError("BYBIT_LIQUIDATION_SCHEMA_SIDE")
    t=x.get("T");age(recv,t,5000)
    p=pos(x.get("p"));size=pos(x.get("v"))
    # Bybit docs: Buy liquidation event means LONG liquidated; Sell means SHORT.
    return {"liquidated_position":"LONG" if x["S"]=="Buy" else "SHORT",
       "source_ms":t,"bankruptcy_notional_proxy":p*size}
def validate_rest(kind,obj,recv):
    if kind=="okx_spot_trades":
        if str(obj.get("code"))!="0" or not isinstance(obj.get("data"),list) or not obj["data"]:
            raise ValueError("OKX_TRADE_HTTP_SCHEMA")
        x=obj["data"][0]
        if x.get("instId")!="BTC-USDT" or x.get("side") not in ("buy","sell") or not x.get("tradeId"):
            raise ValueError("OKX_TRADE_SIDE_OR_ID")
        pos(x.get("px"));pos(x.get("sz"))
        stamp=int(x["ts"]);lag=age(recv,stamp,5000)
        return {"last_trade_age_ms":lag,"side":x["side"],"rows":len(obj["data"]),
                "max_100_snapshot_may_skip_trades":True}
    if obj.get("success") is not True:return _fail("MEXC_RESPONSE_NOT_SUCCESS")
    v=obj.get("data")
    if kind=="mexc_perp_deals":
        if not isinstance(v,list) or not v:raise ValueError("MEXC_DEALS_MISSING")
        x=v[0]
        if x.get("T") not in (1,2):raise ValueError("MEXC_EXECUTED_DEAL_SIDE")
        lag=age(recv,x.get("t"),5000)
        pos(x.get("p"));pos(x.get("v"))
        return {"last_deal_age_ms":lag,"side":x["T"],"rows":len(v),
                "volume_unit":"CONTRACTS_UNVERIFIED_MULTIPLIER",
                "max_100_snapshot_may_skip_trades":True}
    if not isinstance(v,dict) or v.get("symbol")!="BTC_USDT":
        raise ValueError("MEXC_PRICE_OR_BOOK_SYMBOL")
    stamp=v.get("timestamp");lag=age(recv,stamp)
    if kind=="mexc_perp_index":
        pos(v.get("indexPrice"))
        return {"index_server_age_ms":lag,"index_positive":True}
    if kind=="mexc_perp_depth":
        bids=v.get("bids");asks=v.get("asks")
        if not isinstance(bids,list) or not isinstance(asks,list) or len(bids)<5 or len(asks)<5:
            raise ValueError("MEXC_DEPTH_TOO_SHALLOW")
        if pos(bids[0][0])>=pos(asks[0][0]):
            raise ValueError("MEXC_BOOK_CROSSED")
        return {"depth_server_age_ms":lag,"bid_levels":len(bids),"ask_levels":len(asks)}
    raise ValueError("UNKNOWN_PUBLIC_SOURCE_KIND")
def _fail(reason):raise ValueError(reason)
def http(kind):
    req=urllib.request.Request(URLS[kind],headers={
      "Accept":"application/json","User-Agent":"CryptoLab-TripleFlow-BTC10m-V01-SourceOnly"})
    with urllib.request.urlopen(req,timeout=10) as resp:
        if resp.status!=200:raise ValueError("PUBLIC_HTTP_NOT_200")
        raw=resp.read(350001)
    if len(raw)>350000:raise ValueError("PUBLIC_BODY_TOO_LARGE")
    recv=ms()
    return raw,recv
async def bybit(duration,writer):
    state={"connected":False,"ack":False,"trade_frames":0,"liquidation_frames":0,
      "trade_children":0,"liquidation_children":0,"long_liquidated":0,
      "short_liquidated":0,"pings":0,"pongs":0,"schema_errors":[],
      "transport_errors":[],"trade_age_peak_ms":0,"liquidation_age_peak_ms":0,
      "observed_trade_buy":0,"observed_trade_sell":0}
    end=asyncio.get_running_loop().time()+duration
    try:
        async with websockets.connect(WSS,open_timeout=18,ping_interval=15,
             ping_timeout=12,max_size=3000000) as ws:
            state["connected"]=True
            await ws.send(json.dumps({"op":"subscribe","args":[
                "publicTrade.BTCUSDT","allLiquidation.BTCUSDT"]}))
            next_ping=asyncio.get_running_loop().time()+15
            while asyncio.get_running_loop().time()<end:
                now=asyncio.get_running_loop().time()
                if now>=next_ping:
                    await ws.send('{"op":"ping"}');state["pings"]+=1;next_ping=now+15
                timeout=min(2,max(.05,end-now))
                try:raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                except asyncio.TimeoutError:continue
                if not isinstance(raw,str):
                    state["schema_errors"].append("BINARY_WS_MESSAGE");continue
                rec=ms();writer.write("BYBIT_PUBLIC_LINEAR_WS",raw,rec)
                try:
                    msg=json.loads(raw)
                    if msg.get("op")=="subscribe":
                        if msg.get("success") is True:state["ack"]=True
                        else:raise ValueError("BYBIT_SUBSCRIPTION_REJECTED")
                    elif msg.get("op")=="pong":state["pongs"]+=1
                    elif msg.get("topic")=="publicTrade.BTCUSDT":
                        state["trade_frames"]+=1
                        data=msg.get("data") or []
                        if not isinstance(data,list):raise ValueError("BYBIT_TRADE_NOT_LIST")
                        for x in data:
                            t=validate_bybit_trade(x,rec)
                            state["trade_children"]+=1
                            state["trade_age_peak_ms"]=max(state["trade_age_peak_ms"],rec-t["source_ms"])
                            state["observed_trade_buy" if t["side"]=="Buy" else "observed_trade_sell"]+=1
                    elif msg.get("topic")=="allLiquidation.BTCUSDT":
                        state["liquidation_frames"]+=1
                        data=msg.get("data") or []
                        if not isinstance(data,list):raise ValueError("LIQ_MSG_NOT_LIST")
                        for x in data:
                            q=validate_liquidation(x,rec)
                            state["liquidation_children"]+=1
                            state["liquidation_age_peak_ms"]=max(state["liquidation_age_peak_ms"],rec-q["source_ms"])
                            state["long_liquidated" if q["liquidated_position"]=="LONG" else "short_liquidated"]+=1
                except Exception as e:
                    if len(state["schema_errors"])<12:
                        state["schema_errors"].append(type(e).__name__+":"+str(e)[:110])
    except Exception as e:
        state["transport_errors"].append(type(e).__name__+":"+str(e)[:180])
    state["window_seconds"]=duration
    return state
async def public_rest(duration,writer):
    names=list(URLS)
    state={n:{"success":0,"fail":0,"rows_observed":0,"errors":[],"most_recent_age_ms":None,
          "max_100_trade_census_complete":False if "trades" in n or "deals" in n else None}
           for n in names}
    end=asyncio.get_running_loop().time()+duration;attempt=0
    while asyncio.get_running_loop().time()<end:
        t=asyncio.get_running_loop().time()
        async def getone(kind):
            try:
                raw,rec=await asyncio.to_thread(http,kind)
                parsed=json.loads(raw)
                features=validate_rest(kind,parsed,rec)
                writer.write(kind,raw,rec,snapshot=attempt)
                state[kind]["success"]+=1
                state[kind]["rows_observed"]+=features.get("rows",1)
                for name in ("last_trade_age_ms","last_deal_age_ms",
                             "index_server_age_ms","depth_server_age_ms"):
                    if name in features:state[kind]["most_recent_age_ms"]=features[name]
            except Exception as e:
                state[kind]["fail"]+=1
                if len(state[kind]["errors"])<7:
                    state[kind]["errors"].append(type(e).__name__+":"+str(e)[:130])
        await asyncio.gather(*(getone(n) for n in names))
        attempt+=1;remaining=PERIOD-(asyncio.get_running_loop().time()-t)
        if remaining>0:await asyncio.sleep(min(remaining,max(0,end-asyncio.get_running_loop().time())))
    return state,attempt
def classify(b,rest,polls):
    required=["okx_spot_trades","mexc_perp_deals","mexc_perp_index","mexc_perp_depth"]
    ok=bool(b["connected"] and b["ack"] and b["trade_children"]>0 and
            b["pings"]>0 and b["pongs"]>0 and not b["schema_errors"] and
            not b["transport_errors"] and polls>=10 and
            all(rest[n]["success"]>=1 and rest[n]["fail"]==0 for n in required))
    if not ok:
        return "SOURCE_BLOCKED","LIQUIDATION_SOURCE_UNVERIFIED"
    return ("JOINT_SCHEMA_SOURCE_PASS",
            "LIQUIDATION_SEMANTICS_OBSERVED" if b["liquidation_children"]>0
             else "NO_LIQUIDATION_EVENT_OBSERVED")
async def main(duration):
    if duration!=EXPECTED_DURATION:raise ValueError("SOURCE_DURATION_FROZEN_150_SECONDS")
    ROOT.mkdir(parents=True,exist_ok=True)
    ws_writer=Writer("bybit_public_ws.ndjson")
    rest_writer=Writer("okx_mexc_public_rest.ndjson")
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    t0=ms()
    try:
        (b,(rest,polls))=await asyncio.gather(
            bybit(duration,ws_writer),public_rest(duration,rest_writer))
        status,liq_status=classify(b,rest,polls)
    except Exception as e:
        b={};rest={};polls=0;status="SOURCE_BLOCKED";liq_status="LIQUIDATION_SOURCE_UNVERIFIED"
        error=type(e).__name__+":"+str(e)[:190]
    else:error=None
    manifests=[ws_writer.finish(),rest_writer.finish()]
    report={"study":"TRIPLE_FLOW_BTC10M_V01_JOINT_PUBLIC_SOURCE_ONLY",
        "freeze_ref":"research/triple_flow_btc10m_v01/TRIPLE_FLOW_PUBLIC_JOINT_SOURCE_FREEZE_V01.md",
        "status":status,"liquidation_status":liq_status,
        "started_utc":started,"started_ms":t0,"completed_ms":ms(),
        "duration_spec_seconds":duration,"rest_poll_attempts":polls,
        "bybit":b,"rest":rest,"raw_archive_manifest":manifests,"error":error,
        "read_only":True,"order_calls":0,"account_reads":0,"wallet_calls":0,
        "market_10m_return_labels_read":0,"directional_forecasts_issued":0,
        "event_futures_exact_settlement_parity_proven":False,
        "trade_rest_feed_census_complete":False,
        "liquidation_feed_absence_is_zero_market_events":False,
        "economic_edge_proven":False}
    receipt=ROOT/"source_gate_receipt.json"
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items()
          if k not in ("rest","raw_archive_manifest")},indent=2,sort_keys=True))
    if status!="JOINT_SCHEMA_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--seconds",type=int,default=EXPECTED_DURATION)
    args=p.parse_args();asyncio.run(main(args.seconds))
