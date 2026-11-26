#!/usr/bin/env python3
"""One-day true-position coverage experiment. Never an economic GO.
No user wallet IDs processed/published; only aggregated liquidation values.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import statistics
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"sample_results"
URL="https://huggingface.co/datasets/liquidvision/crypto-derivatives-sample/resolve/main/hl_positions_sample.csv"
BIN=.005
MIN_DISTANCE=.005
MAX_DISTANCE=.05
TAU=.03
UTC=dt.timezone.utc
COINS=("BTC","ETH","SOL")

def download():
    req=urllib.request.Request(URL,headers={"User-Agent":"CryptoLab-LIQMAP001B-ReadOnly/1.0"})
    start=dt.datetime.now(UTC).isoformat()
    with urllib.request.urlopen(req,timeout=50) as f:raw=f.read(40_000_001)
    end=dt.datetime.now(UTC).isoformat()
    if len(raw)>40_000_000:raise ValueError("SOURCE_BLOCKED exceeds 40MB limit")
    return raw,{"url":URL,"sha256":hashlib.sha256(raw).hexdigest(),
                "bytes":len(raw),"start_utc":start,"end_utc":end}

def read_snapshots(raw):
    groups={}
    n=0
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required={"ts","coin","side","value_usd","liq_px","mark_px"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("SOURCE_BLOCKED missing columns")
    for row in reader:
        n+=1
        coin=row["coin"].upper()
        if coin not in COINS:continue
        t=dt.datetime.fromisoformat(row["ts"]).replace(tzinfo=UTC)
        try:
            price=float(row["mark_px"]);liq=float(row["liq_px"]);value=float(row["value_usd"])
        except ValueError:continue
        if not all(math.isfinite(x) and x>0 for x in (price,liq,value)):continue
        if value<100000:continue
        side=row["side"].lower()
        if side not in ("long","short"):continue
        if side=="long" and liq>=price:continue
        if side=="short" and liq<=price:continue
        g=groups.setdefault((coin,t),{"marks":[],"positions":[]})
        g["marks"].append(price)
        g["positions"].append((liq,value,side))
    series={}
    for (coin,t),entry in groups.items():
        series.setdefault(coin,[]).append({"t":t,"mark":statistics.median(entry["marks"]),
             "positions":entry["positions"],"n_positions":len(entry["positions"])})
    for coin in series:
        series[coin].sort(key=lambda x:x["t"])
    return n,series

def strongest(snapshot):
    """Only positions from EXACT observed timestamp t, not future snapshots."""
    mark=snapshot["mark"];mass={}
    for liq,value,side in snapshot["positions"]:
        dist=abs(math.log(liq/mark))
        if not MIN_DISTANCE<=dist<=MAX_DISTANCE:continue
        key=math.floor(math.log(liq)/BIN)
        centre=math.exp((key+.5)*BIN)
        cd=math.log(centre/mark)
        if not MIN_DISTANCE<=abs(cd)<=MAX_DISTANCE:continue
        mass[key]=mass.get(key,0.)+value*math.exp(-abs(cd)/TAU)
    if not mass:return None
    key=max(sorted(mass),key=lambda k:mass[k])
    chosen=math.exp((key+.5)*BIN)
    return {"direction":"UP" if chosen>mark else "DOWN",
            "est_price":chosen,"distance_pct":100*abs(math.exp(abs(math.log(chosen/mark)))-1),
            "estimated_visible_sample_value":mass[key]}

def nearest_before(items,t):
    choices=[r for r in items if dt.timedelta(hours=1)<=t-r["t"]<=dt.timedelta(hours=2)]
    return max(choices,key=lambda x:x["t"]) if choices else None

def nearest_after(items,t):
    choices=[r for r in items if dt.timedelta(hours=1)<=r["t"]-t<=dt.timedelta(hours=2)]
    return min(choices,key=lambda x:x["t"]) if choices else None

def wilson(wins,n):
    if n==0:return [None,None]
    z=1.959963984540054;p=wins/n
    d=1+z*z/n;c=(p+z*z/(2*n))/d
    e=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [round(c-e,5),round(c+e,5)]

def evaluate(items,coin):
    if not items:return {"status":"SOURCE_BLOCKED","reason":"no filtered position snapshots"}
    valid=[];last_selected=None
    for current in items:
        if last_selected is not None and current["t"]-last_selected<dt.timedelta(hours=2):
            continue
        earlier=nearest_before(items,current["t"])
        later=nearest_after(items,current["t"])
        if earlier is None or later is None:continue
        pool=strongest(current)
        if pool is None:continue
        direction= "UP" if later["mark"]>current["mark"] else "DOWN" if later["mark"]<current["mark"] else "FLAT"
        moment="UP" if current["mark"]>earlier["mark"] else "DOWN" if current["mark"]<earlier["mark"] else "FLAT"
        valid.append({"decision_utc":current["t"].isoformat(),
           "future_utc":later["t"].isoformat(),
           "mark_current":current["mark"],"n_covered_positions":current["n_positions"],
           "est_zone_pct":round(pool["distance_pct"],4),"zone_direction":pool["direction"],
           "future_direction":direction,"momentum_direction":moment,
           "zone_correct":pool["direction"]==direction if direction!="FLAT" else None,
           "momentum_correct":moment==direction if direction!="FLAT" and moment!="FLAT" else None})
        last_selected=current["t"]
    decided=[r for r in valid if r["zone_correct"] is not None and r["momentum_correct"] is not None]
    n=len(decided);w=sum(r["zone_correct"] for r in decided)
    mw=sum(r["momentum_correct"] for r in decided)
    return {"status":"INCONCLUSIVE_SINGLE_DAY",
      "coin":coin,"raw_snapshots":len(items),"time_start":items[0]["t"].isoformat(),
      "time_end":items[-1]["t"].isoformat(),
      "eligible_decisions":len(valid),"paired_scored":n,
      "zone_hits":w,"momentum_hits":mw,
      "zone_directional_accuracy":round(w/n,6) if n else None,
      "momentum_accuracy":round(mw/n,6) if n else None,
      "zone_wilson95":wilson(w,n),
      "meets_min_20_independent_times":n>=20,
      "economic_live_verdict":"NO_GO_NO_EXECUTION",
      "decisions":valid}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"study":"LIQMAP-001B","source":"free actual Hyperliquid position price sample",
      "not_Neuron":True,"only_one_day":True,"no_trades":True,
      "future_mark_is_discrete_checkpoint_not_intrahour_high_low":True,
      "status":"SOURCE_BLOCKED","samples":{}}
    try:
        raw,receipt=download()
        n,series=read_snapshots(raw)
        result["source_receipt"]=receipt
        result["source_rows"]=n
        for coin in COINS:result["samples"][coin]=evaluate(series.get(coin,[]),coin)
        result["status"]="TECH_SAMPLE_PASS_SINGLE_DAY_INCONCLUSIVE"
        print("REAL_POSITIONS_001B_OK",n,"rows",
              [(coin,result["samples"][coin].get("raw_snapshots"),result["samples"][coin].get("paired_scored"),
                 result["samples"][coin].get("zone_directional_accuracy")) for coin in COINS])
    except Exception as e:
        result["error"]=type(e).__name__+": "+str(e)
    (OUT/"REAL_POSITION_REPLAY.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# LIQMAP-001B — ONE-DAY genuine-position snapshots, NO LIVE GO","",
      "Public Hyperliquid exchange-reported liq_px of sampled large positions; not a complete market map.",
      "One historical day, discrete price checkpoints, no executable trading or intrabar first touch.",
      "Not Neuron and NOT proof its map predicts price.",
      "","| Coin | Snapshots | Independent time decisions | Zone correct | MOM1h correct | Wilson 95% |",
      "|---|---:|---:|---:|---:|---|"]
    for coin,x in result["samples"].items():
        if x["status"].startswith("SOURCE_BLOCKED"):
            lines.append(f"| {coin} | SOURCE_BLOCKED | — | — | — | — |")
        else:
            lines.append(f"| {coin} | {x['raw_snapshots']} | {x['paired_scored']} | "
                 +f"{x['zone_hits']}/{x['paired_scored']} | {x['momentum_hits']}/{x['paired_scored']} | {x['zone_wilson95']} |")
    lines+=["","**Economic verdict: INCONCLUSIVE single day. No live GO.**",
       "Output includes time decisions but never user wallet IDs, unlicensed positions or trades."]
    (OUT/"REAL_POSITION_REPORT.md").write_text("\n".join(lines)+"\n")
    if result["status"]!="TECH_SAMPLE_PASS_SINGLE_DAY_INCONCLUSIVE":raise RuntimeError(result["error"])
if __name__=="__main__":main()
