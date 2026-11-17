#!/usr/bin/env python3
"""LP-NET-004: frozen single-pool hypothetical capital/share fee math + past OHLCV.

NO TRADING, NO ESTIMATED PERSONAL LP APR CLAIM. Under frozen static assumptions
all daily volume is at today's current tick; full time in range is NOT assumed
to be true. Past candles diagnose plausible range exposure, not a forward test.
"""
import argparse,json,hashlib,math
from pathlib import Path
from decimal import Decimal,getcontext
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlencode
getcontext().prec=58

POOL="0xbe3ad6a5669dc0b8b12febc03608860c31e2eef6"
GECKO="https://api.geckoterminal.com/api/v2/networks/arbitrum/pools/"+POOL+"/ohlcv/hour"
def D(x):
    v=Decimal(str(x))
    if not v.is_finite():raise ValueError("nonfinite")
    return v
def fee_scenarios(f):
    if f["pool"]!=POOL or f["slot0_fee_protocol"]!=68:
        raise ValueError("frozen pool identity and protocolFee mismatched")
    raw_sqrt=int(f["sqrtPriceX96"])
    sqrtP=D(raw_sqrt)/D(2**96)
    ratio=sqrtP*sqrtP*D(10)**(int(f["decimals0"])-int(f["decimals1"]))
    frozen_ratio=D(f["token1_per_token0"])
    if abs(ratio-frozen_ratio)/frozen_ratio>D(".000000001"):
        raise ValueError("raw sqrt and declared price disagree")
    L_other=D(f["active_raw_L"])
    fee=D(f["lp_effective_fee_fraction"])
    vol=D(f["pool_vol_usd_h24"])
    price0=D(f["price0_usd"]);price1=D(f["price1_usd"])
    gas=D(f["gas_price_wei"])*D(f["gas_scenario_untested_units"])/D(10**18)*D(f["native_eth_usd"])
    if min(L_other,fee,vol,price0,price1,gas)<=0:raise ValueError("invalid scenario numbers")
    out=[]
    for halfwidth in f["ranges_fractional_half_width"]:
        w=D(halfwidth)
        lower=ratio*(1-w);upper=ratio*(1+w)
        root_lower=lower.sqrt();root_upper=upper.sqrt()
        # Raw token units per L (Q96 normalized sqrt uses raw-unit token1/token0).
        amount0_raw_per_L=(root_upper-sqrtP)/(sqrtP*root_upper)
        amount1_raw_per_L=sqrtP-root_lower
        per_L_USD=(amount0_raw_per_L/(D(10)**int(f["decimals0"])))*price0+(
            amount1_raw_per_L/(D(10)**int(f["decimals1"])))*price1
        if per_L_USD<=0:raise ValueError("position liquidity impossible")
        for notional in f["notional_usd"]:
            amount=D(notional)
            L_user=amount/per_L_USD
            share=L_user/(L_other+L_user)
            fees_day=vol*fee*share
            record={"notional_usd":str(amount),"half_width_frac":str(w),
                    "lower_token1_per_token0":str(lower),"upper_token1_per_token0":str(upper),
                    "hypothetical_added_raw_liquidity_L":str(L_user),
                    "hypothetical_share_at_t0":str(share),
                    "static_total_pool_fees_per_day_usd":str(vol*fee),
                    "static_position_fees_per_day_usd":str(fees_day),
                    "actual_position_fees_received":None,
                    "l1_data_fee":"UNKNOWN",
                    "inventory_loss_vs_hodl":"UNKNOWN",
                    "fee_growth_inside":"UNKNOWN",
                    "gas_450k_scenario_USD_excluding_L1_posting":str(gas),
                    "current_tick_volume_duration_assumption":"ALL_VOLUME_SAME_TICK_DAILY_FOR_FUTURE_DAYS_NOT_FORECAST"}
            for days in f["horizons_days"]:
                gross=fees_day*D(days)
                record[str(days)+"d_static_gross_fee_USD"]=str(gross)
                record[str(days)+"d_static_gross_fee_pct_of_capital"]=str(gross/amount*100)
                record[str(days)+"d_after_only_450k_gas_scenario_usd"]=str(gross-gas)
            record["simple_annual_pct_if_stationary_all_year"]=str(fees_day*365/amount*100)
            record["hurdle_4pct_simple_per_30days_usd"]=str(amount*D(".04")*D(30)/D(365))
            record["simple_annual_fee_below_4pct_hurdle"]=bool(fees_day*365/amount<D(".04"))
            out.append(record)
    return out

def historic_ohlc(f):
    t0=int(datetime.fromisoformat(f["t0_start_utc"]).timestamp())
    query={"aggregate":1,"before_timestamp":t0,"limit":720,"currency":"token","token":"base"}
    url=GECKO+"?"+urlencode(query)
    req=Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-LP-NET-004-HISTORICAL/1.0"})
    with urlopen(req,timeout=20) as resp:raw=resp.read(1200000)
    data=json.loads(raw)
    lst=(data.get("data") or {}).get("attributes",{}).get("ohlcv_list") or []
    if not isinstance(lst,list):raise ValueError("no candle list")
    valid={}
    min_ts=t0-30*86400
    for candle in lst:
        if len(candle)<6:continue
        ts=int(candle[0])
        if not (min_ts<=ts and ts+3600<=t0):continue # strict closed candles before T0
        op,hi,lo,cl=[D(x) for x in candle[1:5]]
        if not (0<lo<=min(op,cl)<=max(op,cl)<=hi):continue
        valid[ts]=(lo,hi,cl)
    candles=sorted(valid.items())
    if not candles:raise ValueError("no timestamped closed candles")
    latest=candles[-1][1][2]
    anchor=D(f["token1_per_token0"])
    orientation_ok=abs(latest-anchor)/anchor<D(".01")
    groups=[]
    for half in f["ranges_fractional_half_width"]:
        w=D(half);low=anchor*(1-w);high=anchor*(1+w)
        guaranteed=sum(1 for _,(l,h,_) in candles if l>=low and h<=high)
        possible=sum(1 for _,(l,h,_) in candles if h>=low and l<=high)
        # Missing hours are unknown, never counted as time in range.
        groups.append({"half_width_frac":str(w),"lower":str(low),"upper":str(high),
           "fully_inside_candle_hours":guaranteed,"possible_intersection_candle_hours":possible,
           "observed_candle_count":len(candles),
           "fully_inside_fraction_of_observed":guaranteed/len(candles),
           "intersection_fraction_of_observed":possible/len(candles),
           "CANNOT_INFER_FUTURE_POSITION_UPTIME":True})
    return {"state":"HISTORICAL_CLOSED_CANDLES_OBSERVED" if orientation_ok else "PRICE_ORIENTATION_BLOCKED",
       "provider":"GeckoTerminal token=base currency=token",
       "query_sha256":hashlib.sha256(raw).hexdigest(),"t0_snapshot_unix":t0,
       "candles_valid":len(candles),"max_hours_30d":720,
       "coverage_fraction":len(candles)/720,
       "oldest_utc":datetime.fromtimestamp(candles[0][0],timezone.utc).isoformat(),
       "newest_utc":datetime.fromtimestamp(candles[-1][0],timezone.utc).isoformat(),
       "last_close_token1_per_token0":str(latest),"onchain_anchor":str(anchor),
       "range_diagnostics":groups,
       "not_a_forward_outcome":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    raw=a.fixture.read_bytes();f=json.loads(raw)
    if f["raw_artifact_json_sha256"]!="8c28d45226600e65a63a8bdd42b6155c77f83e5392b9ea49cd68fe13bd606f7b":
        raise ValueError("source T0 provenance changed")
    result={"study":"LP-NET-004-ARBITRUM-STATIC-HYPOTHESIS",
       "source_snapshot_sha256":hashlib.sha256(raw).hexdigest(),
       "source_original_GitHub_artifact_id":f["artifact_id"],
       "status":"MODEL_ONLY_NOT_AN_ACTUAL_POSITION", "capital_chf":0,"trades":0,
       "economic_verdict":"NO_LIVE_GO","static_scenarios":fee_scenarios(f)}
    try:result["past_30d_ohlcv"]=historic_ohlc(f)
    except (OSError,ValueError,TypeError,KeyError) as e:
        result["past_30d_ohlcv"]={"state":"SOURCE_BLOCKED","error":type(e).__name__+":"+str(e)[:190]}
    result["required_future_evidence"]="point-in-time feeGrowthInside and range-specific swaps/tick crossings, gas L1 data component, token inventory PnL, 7/30d prospective comparison to HODL"
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"scenario_count":len(result["static_scenarios"]),
        "30d_candle_state":result["past_30d_ohlcv"]["state"],
        "candle_count":result["past_30d_ohlcv"].get("candles_valid"),
        "all_frozen_static_scenarios_below_4pct_hurdle":all(x["simple_annual_fee_below_4pct_hurdle"] for x in result["static_scenarios"]),
        "economic_verdict":result["economic_verdict"]},ensure_ascii=False))

if __name__=="__main__":main()
