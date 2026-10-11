#!/usr/bin/env python3
"""MEXC public metadata/clock feasibility: research only, no account or orders."""
import argparse
import datetime as dt
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

from public_bbo_probe import SYMBOLS, probe

HOST="https://contract.mexc.com"
ANNOUNCED_API_TAKER_PER_SIDE=0.0008

def public_get(path, params=None):
    url=HOST+path
    if params:
        url+="?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SOURCE-ONLY/1.1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=12) as response:
        if response.status != 200:
            raise ValueError("HTTP_NON_200")
        obj=json.loads(response.read(1_000_000))
    if not isinstance(obj,dict) or obj.get("success") is not True or obj.get("code")!=0:
        raise ValueError("API_STATUS_FAIL")
    return obj.get("data")

def positive(name,value):
    if isinstance(value,bool):
        raise ValueError("BAD_"+name)
    f=float(value)
    if not math.isfinite(f) or f <= 0:
        raise ValueError("BAD_"+name)
    return f

def normalize_contract(data,symbol):
    if isinstance(data,list):
        matches=[x for x in data if isinstance(x,dict) and x.get("symbol")==symbol]
        if len(matches)!=1: raise ValueError("CONTRACT_NOT_UNIQUE")
        obj=matches[0]
    elif isinstance(data,dict):
        if "symbol" in data:
            obj=data
        elif isinstance(data.get("list"),list):
            return normalize_contract(data["list"],symbol)
        else:
            raise ValueError("CONTRACT_SCHEMA_UNEXPECTED")
    else:
        raise ValueError("CONTRACT_SCHEMA_UNEXPECTED")
    if obj.get("symbol")!=symbol or obj.get("quoteCoin")!="USDT" or obj.get("futureType")!=1:
        raise ValueError("CONTRACT_IDENTITY_FAIL")
    contract_size=positive("CONTRACT_SIZE",obj.get("contractSize"))
    min_vol=positive("MIN_VOLUME",obj.get("minVol"))
    vol_unit=positive("VOLUME_STEP",obj.get("volUnit"))
    tick=positive("TICK_SIZE",obj.get("priceUnit"))
    taker=obj.get("takerFeeRate")
    if isinstance(taker,bool) or taker is None or not math.isfinite(float(taker)) or float(taker)<0:
        raise ValueError("BAD_PUBLIC_TAKER_FEE")
    taker=float(taker)
    state=obj.get("state")
    enabled=(state==0 and obj.get("apiAllowed") is True and obj.get("type") in (None,1))
    return {
        "symbol":symbol, "enabled_in_public_contract_metadata":enabled,
        "state":state, "api_allowed_public_flag":obj.get("apiAllowed"),
        "contract_size":contract_size,"min_vol_contracts":min_vol,
        "volume_step_contracts":vol_unit,"tick_size":tick,
        "fee_rate_mode":obj.get("feeRateMode"),
        "public_taker_fee_rate":taker,
        "announced_api_taker_fee_rate":ANNOUNCED_API_TAKER_PER_SIDE,
        "fee_sources_match":abs(taker-ANNOUNCED_API_TAKER_PER_SIDE)<1e-12,
        "fee_decision":"UNRESOLVED_EXACT_FEE_NO_ACCOUNT_CHECK",
        "contract_rules_decision":"PUBLIC_METADATA_PASS" if enabled else "CONTRACT_NOT_TRADABLE_FLAG"
    }

def check_server_time(value,observed_ms):
    if isinstance(value,bool) or not isinstance(value,int) or value<1_500_000_000_000:
        raise ValueError("BAD_SERVER_TIME")
    offset=observed_ms-value
    if abs(offset)>10_000:
        raise ValueError("SERVER_CLOCK_UNRELIABLE")
    return {"server_clock_offset_ms_observed_minus_exchange":offset}

def run():
    status={"schema":"asymmetric_contract_meta_gate.v1",
            "checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "trading_authority":"NONE","live_trading":False,
            "results":[],"gate":"SOURCE_CONTRACT_META_BLOCKED"}
    try:
        now=int(time.time()*1000)
        status["clock"]=check_server_time(public_get("/api/v1/contract/ping"),now)
    except Exception as e:
        status["clock"]={"error_type":type(e).__name__,"detail":str(e)[:180]}
    for symbol in SYMBOLS:
        try:
            data=public_get("/api/v1/contract/detail/country",{"symbol":symbol})
            info=normalize_contract(data,symbol)
            book=probe(symbol)
            # Contract size price is a rough quote notional per *contract*,
            # not evidence the displayed book can fill that size.
            info["indicative_min_contract_notional_usdt"]=round(
                info["contract_size"]*info["min_vol_contracts"]*book["ask"],8)
            info["observed_bbo_spread_bps"]=book["spread_bps"]
            info["observation_timestamp_ms"]=book["observation_timestamp_ms"]
            info["gate"]="SOURCE_META_PASS_FEE_RECONCILIATION_OPEN" if info["enabled_in_public_contract_metadata"] else "SOURCE_META_BLOCKED_NOT_ENABLED"
            status["results"].append(info)
        except Exception as e:
            status["results"].append({"symbol":symbol,"gate":"SOURCE_META_BLOCKED","error_type":type(e).__name__,"detail":str(e)[:180]})
    if ("error_type" not in status.get("clock",{}) and
       all(x.get("gate")=="SOURCE_META_PASS_FEE_RECONCILIATION_OPEN" for x in status["results"])):
        status["gate"]="SOURCE_META_PASS_FEE_RECONCILIATION_OPEN"
    status["limitations"]=[
        "Public API flags do not authorize an operator account, country, or any order.",
        "Contract min notional is only indicative, not depth-weighted fillability.",
        "Public fee field and announced API fee cannot settle exact account-route costs.",
        "No historical BBO archive, shock edge, forward outcomes, execution, or money."
    ]
    return status

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    x=p.parse_args()
    result=run()
    dst=Path(x.out)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))

if __name__=="__main__":
    main()
