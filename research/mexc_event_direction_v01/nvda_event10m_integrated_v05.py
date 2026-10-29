#!/usr/bin/env python3
"""As-of source capture. --source-smoke never computes a signal.
--decision uses ONLY frozen November 10m paper evaluator. No orders/outcomes.
"""
import argparse,asyncio,datetime as dt,hashlib,json,math,pathlib,time,urllib.parse,urllib.request
from nvda_event10m_exact_source_v04 import product as exact_product, index as event_index
from nvda_event10m_forecast_v01 import forecast
OUT=pathlib.Path("artifacts/nvda_event10m_integrated_v05")
UTC=dt.timezone.utc
def ms():return int(time.time()*1000)
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PaperSourceOnly/0.5",
       "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as res:
        if res.status!=200:raise RuntimeError("HTTP_NOT_200")
        raw=res.read(2_000_001)
    if len(raw)>2_000_000:raise RuntimeError("SOURCE_TOO_LARGE")
    arrival=ms()
    return json.loads(raw),hashlib.sha256(raw).hexdigest(),arrival
def extract_prices(times,prices,received_ms,symbol,digest):
    if not isinstance(times,list) or not isinstance(prices,list) or len(times)!=len(prices):
        raise RuntimeError("BAR_SOURCE_SCHEMA")
    # Only two bars are feature inputs. Do not fail because unrelated old daily
    # Yahoo rows contain null/zero (no model information from these).
    boundary=received_ms//60000*60000
    needed={boundary-4*60000,boundary-60000}
    found={}
    for t,p in zip(times,prices):
        if t is None:continue
        try: t=int(t)*1000
        except (TypeError,ValueError):continue
        if t not in needed:continue
        if t in found:raise RuntimeError("DUPLICATE_CAUSAL_FEATURE_BAR")
        if p is None:raise RuntimeError("NULL_CAUSAL_FEATURE_BAR")
        try:p=float(p)
        except (TypeError,ValueError):raise RuntimeError("BAD_CAUSAL_FEATURE_BAR")
        if t%60000 or not(math.isfinite(p) and p>0):
            raise RuntimeError("BAD_CAUSAL_FEATURE_BAR")
        if t+60000>received_ms-1000:
            raise RuntimeError("UNFINISHED_CAUSAL_FEATURE_BAR")
        found[t]={"start_ms":t,"close":p,"received_ms":received_ms}
    if set(found)!=needed:raise RuntimeError("MISSING_CAUSAL_FEATURE_BAR")
    return {"symbol":symbol,"sha256":digest,"received_ms":received_ms,
            "bars":[found[t] for t in sorted(found)]}

def cash():
    url="https://query1.finance.yahoo.com/v8/finance/chart/NVDA?"+urllib.parse.urlencode(
       {"range":"1d","interval":"1m","includePrePost":"false"})
    obj,sha,received=fetch(url)
    chart=obj.get("chart") or {}
    results=chart.get("result") or []
    if chart.get("error") or len(results)!=1:
        raise RuntimeError("YAHOO_MARKET_REFERENCE_UNAVAILABLE")
    raw=results[0]
    if (raw.get("meta") or {}).get("symbol")!="NVDA":
        raise RuntimeError("YAHOO_WRONG_CASH_ID")
    quote=(raw.get("indicators") or {}).get("quote") or []
    if not quote:raise RuntimeError("YAHOO_NO_QUOTE")
    packet=extract_prices(raw.get("timestamp"),quote[0].get("close"),received,"NVDA",sha)
    return packet,{"provider":"YAHOO_UNOFFICIAL_CASH","retrieved_ms":received,
      "raw_sha256":sha,"last_completed_bar_start_ms":packet["bars"][-1]["start_ms"],"url":url}
def mexc():
    t=int(time.time())
    start=(t-1800)//60*60
    end=(t-60)//60*60
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+urllib.parse.urlencode(
       {"interval":"Min1","start":start,"end":end})
    obj,sha,received=fetch(url)
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise RuntimeError("MEXC_INDEX_SOURCE_UNAVAILABLE")
    data=obj["data"]
    packet=extract_prices(data.get("time"),data.get("close"),received,"NVIDIA_USDT",sha)
    return packet,{"provider":"MEXC_STANDARD_INDEX","retrieved_ms":received,
      "raw_sha256":sha,"last_completed_bar_start_ms":packet["bars"][-1]["start_ms"],"url":url}
async def collect(mode):
    started=ms()
    report={"study":"NVIDIA_EVENT10M_INTEGRATED_V05","mode":mode,
      "started_ms":started,"status":"SOURCE_STARTING",
      "signal_issued":False,"economic_outcomes_opened":0,
      "old_v06_oct05_oct30_read":False,"orders_account_private_calls":0,
      "event_order_openprice_parity_proven":False,
      "source_receipts":[]}
    try:
        # The product detail is captured LAST among HTTP legs; after it completes,
        # subscribe for a NEW public index tick so it cannot be stale from page startup.
        first=await asyncio.gather(asyncio.to_thread(cash),asyncio.to_thread(mexc),
                                   exact_product(),return_exceptions=True)
        fresh_tick=await event_index() if not any(isinstance(v,BaseException) for v in first) else RuntimeError("PRIOR_SOURCE_EXCEPTION")
        results=[*first,fresh_tick]
        for source_name,v in zip(("yahoo_cash_1m","mexc_index_1m","event_detail","event_ws_tick"),results):
            if isinstance(v,BaseException):
                report.setdefault("source_failures",[]).append({
                    "source":source_name,
                    "type":type(v).__name__,
                    "reason":str(v)[:180]})
        if report.get("source_failures"):
            raise RuntimeError("PUBLIC_SOURCE_EXCEPTION_DIAGNOSTIC")
        cash_pack,cash_info=results[0]
        index_pack,index_info=results[1]
        prod,idx=results[2],results[3]
        report["source_receipts"]=[cash_info,index_info,
           {k:v for k,v in prod.items() if k not in ("raw_body",)},
           {k:v for k,v in idx.items() if k not in ("raw_body",)}]
        if prod.get("status")!="PUBLIC_PRODUCT_10M_PASS" or idx.get("status")!="PUBLIC_INDEX_TICK_PASS":
            raise RuntimeError("EVENT_PRODUCT_OR_TICK_SOURCE_BLOCKED")
        # --source-smoke is permanently nonpredictive, and cannot open outcomes.
        if mode=="source-smoke":
            # A proof of same-instant readiness, separate from product/source existence.
            t=ms()
            source_gates={}
            for name,pkt in (("cash",cash_pack),("index",index_pack)):
                expected={t//60000*60000-4*60000,t//60000*60000-60000}
                seen={x["start_ms"] for x in pkt["bars"]}
                source_gates[name]=(
                    pkt["received_ms"]<=t and t-pkt["received_ms"]<=90000 and
                    expected==seen and all(x["received_ms"]<=t and
                        x["start_ms"]+60000<=x["received_ms"] for x in pkt["bars"]))
            source_gates["product"]=(
                prod["response_received_ms"]<=t and
                t-prod["response_received_ms"]<=10000)
            source_gates["event_tick"]=(
                idx["received_ms"]<=t and t-idx["received_ms"]<=2000 and
                isinstance(idx.get("server_ts"),int) and
                0<=idx["received_ms"]-idx["server_ts"]<=5000)
            report["asof_source_gates"]=source_gates
            report["asof_source_ready_at_ms"]=t
            report["asof_all_gates_pass"]=all(source_gates.values())
            report["status"]="FOUR_PUBLIC_SOURCES_PRESENT__NO_MODEL_NO_OUTCOME"
            return report
        decision_ms=ms()
        model_product={"symbol":"NVIDIA_USDT","state":prod["product_state"],
          "horizon_min":10,"up_pay_rate":prod["up_pay_rate"],"down_pay_rate":prod["down_pay_rate"],
          "received_ms":prod["response_received_ms"],"sha256":prod["raw_sha256"]}
        tick={"symbol":"NVIDIA_USDT","index_price":idx["index_price"],
          "received_ms":idx["received_ms"],"sha256":idx["index_raw_sha256"]}
        f=forecast(decision_ms,cash_pack,index_pack,model_product,tick)
        report["forecast"]=f
        report["decision_public_index"]=idx["index_price"]
        report["decision_index_source_sha256"]=idx["index_raw_sha256"]
        report["status"]="PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION"
        report["signal_issued"]=f["candidate"]!="ABSTAIN"
        report["requires_external_pre_expiry_anchor"]=True
        report["caveat"]="No price/payout or order/expiry parity; outcome evaluator must be separate."
        return report
    except Exception as e:
        report["status"]="BLOCKED"
        report["block_code"]=type(e).__name__+":"+str(e)[:150]
        return report
async def run(mode):
    OUT.mkdir(parents=True,exist_ok=True)
    report=await collect(mode)
    report["finished_ms"]=ms()
    data=json.dumps(report,sort_keys=True,indent=2)+"\n"
    output=OUT/("source_smoke.json" if mode=="source-smoke" else "decision.json")
    output.write_text(data)
    print(json.dumps({"status":report["status"],"mode":mode,
      "source_receipts":report["source_receipts"],
      "signal_issued":report["signal_issued"],
      "block_code":report.get("block_code"),"source_failures":report.get("source_failures")},indent=2),flush=True)
    if report["status"]=="BLOCKED":raise SystemExit(2)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-smoke",action="store_true")
    p.add_argument("--decision",action="store_true")
    args=p.parse_args()
    if args.source_smoke==args.decision:
        raise SystemExit("choose EXACTLY one mode: --source-smoke or --decision")
    asyncio.run(run("source-smoke" if args.source_smoke else "decision"))
