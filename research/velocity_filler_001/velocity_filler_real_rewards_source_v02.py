#!/usr/bin/env python3
"""One-shot public actual fillerReward source: read-only, no accounts or orders."""
from __future__ import annotations
import datetime as dt
import decimal
import hashlib
import json
import pathlib
import re
import statistics
import urllib.request

OUT=pathlib.Path("artifacts/velocity_filler_actual_rewards_v02")
HOST="https://data.velocity.exchange"
PATHS=[("/stats/markets","00_stats_markets.json")]+[
    ("/market/"+symbol+"/trades?limit=100",f"{i:02d}_{symbol.lower()}_trades.json")
    for i,symbol in enumerate(("SOL-PERP","BTC-PERP","ETH-PERP"),1)]
PRECISION=decimal.Decimal(1000000)
MAX_BYTES=2_000_000
TIMEOUT_SECONDS=12
Q=decimal.Decimal
B58=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,100}$")
class Stop(Exception):pass
def utc():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def digest(b):return hashlib.sha256(b).hexdigest()
def number(x):
    if x is None or isinstance(x,bool):raise Stop("MISSING_NUMERIC")
    try:
        n=Q(str(x))
    except (decimal.InvalidOperation,ValueError,TypeError):
        raise Stop("BAD_NUMERIC")
    if not n.is_finite() or n<0:raise Stop("NEGATIVE_OR_NONFINITE")
    if n!=n.to_integral_value():raise Stop("NONINTEGER_QUOTE_MICRO_UNITS")
    return n
def records(obj):
    if isinstance(obj,list):return obj
    if isinstance(obj,dict) and isinstance(obj.get("data"),list):return obj["data"]
    raise Stop("UNDOCUMENTED_TRADE_LIST_SCHEMA")
def normalize_trade(x):
    if not isinstance(x,dict):raise Stop("TRADE_NOT_OBJECT")
    if "fillerReward" not in x:raise Stop("FILLER_REWARD_FIELD_MISSING")
    t=x.get("ts")
    if isinstance(t,bool) or not isinstance(t,(int,str)) or not str(t).isdigit():
        raise Stop("TRADE_UNIX_TIME_BAD")
    timestamp=int(t)
    if not 1580000000<=timestamp<=2200000000:raise Stop("TRADE_TIMESTAMP_OUT_OF_RANGE")
    tx=x.get("txSig")
    if not isinstance(tx,str) or not B58.fullmatch(tx):
        raise Stop("TRADE_SOLANA_TX_SIGNATURE_BAD")
    rew=number(x["fillerReward"])
    fee=number(x["takerFee"]) if "takerFee" in x and x["takerFee"] is not None else None
    if fee is not None and rew>fee:
        raise Stop("REWARD_GT_TAKER_FEE")
    return {"ts":timestamp,"tx_signature":tx,
        "filler_reward_micro_quote":int(rew),"taker_fee_micro_quote":int(fee) if fee is not None else None}
def tests():
    ts=1793440000
    x={"ts":ts,"txSig":"5"*65,"fillerReward":"10000","takerFee":"80000"}
    r=normalize_trade(x)
    assert r["filler_reward_micro_quote"]==10000
    assert len(records({"data":[x]}))==1
    try:normalize_trade({**x,"fillerReward":"-1"});raise AssertionError("accepted negative reward")
    except Stop:pass
    try:normalize_trade({**x,"fillerReward":"1.2"});raise AssertionError("accepted noninteger reward")
    except Stop:pass
    try:normalize_trade({**x,"fillerReward":"80001"});raise AssertionError("accepted reward > fee")
    except Stop:pass
def request(path,fname):
    req=urllib.request.Request(HOST+path,method="GET",
         headers={"Accept":"application/json","User-Agent":"CryptoLab-VelocityActualFiller-SourceOnly/1.0"})
    begin=utc()
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT_SECONDS) as response:
            code=response.status
            body=response.read(MAX_BYTES+1)
    except Exception as exc:
        raise Stop("PUBLIC_GET_"+type(exc).__name__+"_"+path[:110]) from exc
    end=utc()
    if code!=200 or len(body)>MAX_BYTES:raise Stop("HTTP_OR_SIZE_SOURCE_BLOCKED")
    (OUT/fname).write_bytes(body)
    try:obj=json.loads(body)
    except Exception as exc:raise Stop("PUBLIC_RESPONSE_NOT_JSON") from exc
    meta={"path":path,"http":code,"bytes":len(body),
          "received_utc":end,"requested_utc":begin,
          "raw_sha256":digest(body),"raw_file":fname}
    return obj,meta
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    tests()
    v={"study":"VELOCITY_FILLER_REAL_REWARDS_V02_FINAL","started_at_utc":utc(),
       "status":"SOURCE_BLOCKED_FAIL_CLOSED","market_symbols":["SOL-PERP","BTC-PERP","ETH-PERP"],
       "source_receipts":[],"per_market":{},"operator_account_rewards":None,
       "actual_orders":0,"wallet_access":0,"authenticated_calls":0,
       "profitability_verified":False,"private_transactions_submitted":0}
    try:
        baseline=dt.datetime.now(dt.timezone.utc).timestamp()
        v["source_anchor_unix_seconds"]=int(baseline)
        for path,fname in PATHS:
            obj,receipt=request(path,fname)
            v["source_receipts"].append(receipt)
            if path=="/stats/markets":
                if isinstance(obj,dict) and obj.get("success") is True and isinstance(obj.get("markets"),list):rows=obj["markets"]
                elif isinstance(obj,dict) and isinstance(obj.get("data"),list):rows=obj["data"]
                elif isinstance(obj,list):rows=obj
                else:raise Stop("STATS_MARKETS_SCHEMA_BAD")
                if not all(isinstance(item,dict) for item in rows):raise Stop("MARKET_STATS_ITEM_SCHEMA")
                v["stats_market_count"]=len(rows)
                v["stats_selected_markets"]=[{"symbol":str(row.get("symbol")),
                    "volume24h_as_reported":row.get("volume24h"),
                    "status":row.get("status"),
                    "marketIndex":row.get("marketIndex")} for row in rows if row.get("symbol") in ("SOL-PERP","BTC-PERP","ETH-PERP")]
                continue
            symbol=path.split("/")[2]
            txs=records(obj)
            if len(txs)>100:raise Stop("TRADES_MORE_THAN_REQUESTED_100")
            parsed=[normalize_trade(x) for x in txs]
            old=[x for x in parsed if 0<=baseline-x["ts"]<=7*86400]
            positives=[x for x in old if x["filler_reward_micro_quote"]>0]
            distinct=set(x["tx_signature"] for x in positives)
            gross=Q(sum(x["filler_reward_micro_quote"] for x in positives))/PRECISION
            allgross=Q(sum(x["filler_reward_micro_quote"] for x in parsed))/PRECISION
            m={"symbol":symbol,
               "feed_trade_records":len(parsed),
               "data_has_nextPage": bool((obj.get("meta") or {}).get("nextPage")) if isinstance(obj,dict) else None,
               "newest_ts":max((x["ts"] for x in parsed),default=None),
               "oldest_ts":min((x["ts"] for x in parsed),default=None),
               "positive_reward_records_in_recent_7d":len(positives),
               "positive_reward_distinct_tx_in_recent_7d":len(distinct),
               "observed_recent_7d_rewards_quote_units":str(gross),
               "all_sample_rewards_quote_units":str(allgross),
               "max_individual_reward_usd_in_sample":str(Q(max((x["filler_reward_micro_quote"] for x in parsed),default=0))/PRECISION),
               "zero_reward_records":sum(x["filler_reward_micro_quote"]==0 for x in parsed),
               "positive_sample_tx_signatures":sorted(distinct)[:20],
               "not_wallet_transfer_or_net_pnl":True}
            v["per_market"][symbol]=m
        positiveN=sum(x["positive_reward_records_in_recent_7d"] for x in v["per_market"].values())
        distinctT=set()
        for x in v["per_market"].values():distinctT.update(x["positive_sample_tx_signatures"])
        total=sum(Q(x["observed_recent_7d_rewards_quote_units"]) for x in v["per_market"].values())
        v["recent_7d_positive_reward_records"]=positiveN
        v["recent_7d_distinct_tx_at_least_from_saved_sample"]=len(distinctT)
        v["observed_recent_7d_total_quote_usd_approx"]=str(total)
        if positiveN==0:
            v["status"]="SOURCE_VALID_ZERO_REWARDS_IN_FIRST_100_EACH"
        else:v["status"]="SOURCE_VALID_EXPLICIT_HISTORICAL_FILLER_REWARDS"
        hurdle=positiveN>=10 and len(distinctT)>=3 and total>=Q(10)
        v["economic_research_hurdle_passed"]=hurdle
        v["economic_next_step"]="FURTHER_REAL_FEE_COMPETITION_GATES_REQUIRED" if hurdle else "STOP_FAMILY_INSUFFICIENT_PUBLIC_REWARD_EVIDENCE"
    except Stop as exc:
        v["status"]="SOURCE_BLOCKED_FAIL_CLOSED";v["reason"]=str(exc)
    except Exception as exc:
        v["status"]="SOURCE_BLOCKED_FAIL_CLOSED";v["reason"]=type(exc).__name__+":"+str(exc)[:180]
    finally:
        v["finished_at_utc"]=utc()
        v["net_edge_verdict"]="NO_INDEPENDENT_OPERATOR_NET_PROFIT_CERTIFIED"
        (OUT/"receipt.json").write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf8")
        print(json.dumps({key:v.get(key) for key in ("study","status","reason","stats_market_count",
            "stats_selected_markets","per_market","recent_7d_positive_reward_records",
            "recent_7d_distinct_tx_at_least_from_saved_sample","observed_recent_7d_total_quote_usd_approx",
            "economic_research_hurdle_passed","economic_next_step","net_edge_verdict")},indent=2,sort_keys=True),flush=True)
    if v["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":run()
