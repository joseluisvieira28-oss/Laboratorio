#!/usr/bin/env python3
"""PRE-FROZEN source-only AF fill retention and HYPE market-liquidity feasibility census."""
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
import urllib.error
import urllib.request

URL = "https://api.hyperliquid.xyz/info"
AF = "0x" + "fe" * 20
assert len(AF) == 42
OUT = Path("research/hype_buyback_flow_001/receipts/retention_liquidity_v013")
OUT.mkdir(parents=True, exist_ok=True)
DAY_MS = 86400000
MAX_BYTES = 8_000_000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pull(label, body, receipts):
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    tic = time.monotonic()
    record = {"label": label, "request_sha256": sha(encoded), "requested_utc": start}
    try:
        request = urllib.request.Request(
            URL, method="POST", data=encoded,
            headers={"Content-Type": "application/json", "User-Agent": "CryptoLab-HYPE-Research-SourceOnly/0.1.3"})
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_BYTES+1)
            record["status"] = response.status
        if len(raw)>MAX_BYTES:
            raise ValueError("response_exceeded_8MB_limit")
        record["raw_sha256"] = sha(raw)
        record["raw_bytes"] = len(raw)
        (OUT / (label + ".json")).write_bytes(raw)
        obj = json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read(256)
        record.update({"status":exc.code, "error_hash":sha(raw),
                       "error_excerpt":raw.decode(errors="replace")[:160]})
        obj = None
    except (urllib.error.URLError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        record["error"] = type(exc).__name__
        obj = None
    record.update({"received_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
                   "latency_ms":round((time.monotonic()-tic)*1000,3)})
    receipts.append(record)
    return obj


def market_binding(payload):
    if not isinstance(payload,list) or len(payload)!=2:
        raise ValueError("spotMetaAndAssetCtxs_not_pair")
    meta, ctxs = payload
    if not isinstance(meta,dict) or not isinstance(ctxs,list) or not isinstance(meta.get("universe"),list):
        raise ValueError("bad_spot_metadata")
    tokens = {t.get("name"):t.get("index") for t in meta.get("tokens",[]) if isinstance(t,dict)}
    matches = [(i,pair) for i,pair in enumerate(meta["universe"])
               if pair.get("tokens")==[tokens.get("HYPE"),tokens.get("USDC")] and pair.get("name")=="@107"]
    if len(matches) != 1:
        raise ValueError("HYPE_USDC_not_exactly_bound")
    i, pair = matches[0]
    market_index = pair.get("index")
    if not isinstance(market_index,int) or market_index < 0 or market_index >= len(ctxs):
        raise ValueError("spot_market_index_not_valid")
    ctx = ctxs[market_index]
    exact_coin_matches = [j for j,x in enumerate(ctxs) if isinstance(x,dict) and x.get("coin")==pair["name"]]
    if exact_coin_matches != [market_index] or not isinstance(ctx,dict) or ctx.get("coin")!=pair["name"]:
        raise ValueError("spot_ctx_coin_market_index_identity_mismatch")
    return {"coin":pair["name"],"universe_index":i,"spot_market_index":market_index,
            "tokens":pair["tokens"],"dayNtlVlm":ctx.get("dayNtlVlm"),
            "prevDayPx":ctx.get("prevDayPx")}


def slice_audit(fills, coin, start, stop):
    if not isinstance(fills,list):
        return {"verified":False,"error":"non_list"}
    seen=set()
    cnt=0
    bad=0
    wrong_market=0
    wrong_side=0
    dupe=0
    out_window=0
    hype=Decimal("0")
    notional=Decimal("0")
    crossed={"true":0,"false":0,"unknown":0}
    times=[]
    for f in fills:
        if not isinstance(f,dict):
            bad+=1
            continue
        if f.get("coin")!=coin:
            wrong_market+=1
            continue
        if f.get("side")!="B":
            wrong_side+=1
            continue
        try:
            ms=f.get("time")
            if not isinstance(ms,int) or not start<=ms<=stop: 
                out_window+=1
                continue
            px=Decimal(str(f.get("px")))
            sz=Decimal(str(f.get("sz")))
            if not(px.is_finite() and sz.is_finite()) or px<=0 or sz<=0 or f.get("tid") is None or not isinstance(f.get("hash"),str):
                bad+=1
                continue
        except (ValueError,TypeError,InvalidOperation):
            bad+=1
            continue
        identifier=(str(f["tid"]),f["hash"])
        if identifier in seen:
            dupe+=1
            continue
        seen.add(identifier)
        cnt+=1
        hype+=sz
        notional+=px*sz
        times.append(ms)
        key=str(f.get("crossed")).lower()
        crossed[key if key in crossed else "unknown"]+=1
    times.sort()
    intervals=[(v-u)/1000 for u,v in zip(times,times[1:])]
    return {
        "verified":True,"raw_rows":len(fills),"valid_exact_af_hype_buy_fills":cnt,
        "total_hype_buy_quantity":str(hype),"total_execution_notional_usdc":str(notional),
        "duplicate_tid_hash":dupe,"wrong_side":wrong_side,"wrong_market":wrong_market,
        "bad_rows":bad,"out_of_window":out_window,"page_censored_ge_2000":len(fills)>=2000,
        "first_ms":times[0] if times else None,"last_ms":times[-1] if times else None,
        "median_inter_fill_seconds":statistics.median(intervals) if intervals else None,
        "crossed_count":crossed,
        "hist_coverage_complete":False
    }


def book_audit(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("levels"),list) or len(payload["levels"])!=2:
        return {"valid":False}
    bids,asks=payload["levels"]
    if not bids or not asks:
        return {"valid":False}
    best_bid=Decimal(str(bids[0]["px"]))
    best_ask=Decimal(str(asks[0]["px"]))
    if best_bid<=0 or best_ask<=best_bid:
        return {"valid":False,"reason":"crossed_or_invalid_book"}
    mid=(best_bid+best_ask)/2
    out={
        "valid":True,"best_bid":str(best_bid),"best_ask":str(best_ask),
        "instantaneous_spread_bps":str((best_ask-best_bid)/mid*10000),
        "top5_bid_notional_usdc":str(sum((Decimal(str(x["px"]))*Decimal(str(x["sz"])) for x in bids[:5]),Decimal(0))),
        "top5_ask_notional_usdc":str(sum((Decimal(str(x["px"]))*Decimal(str(x["sz"])) for x in asks[:5]),Decimal(0))),
        "historical_execution_liquidity_proven":False
    }
    return out


def main():
    rec={
        "candidate_id":"HYPE-BUYBACK-FLOW-001","phase":"SOURCE_ONLY","trading_authority":"NONE",
        "market_price_outcomes":0,"exchange_mutations":0,"private_account_access":0,
        "paid_data":0,"status":"SOURCE_INTEGRITY_NOT_YET_SUFFICIENT",
        "run_id":os.environ.get("GITHUB_RUN_ID","LOCAL"),
        "commit_sha":os.environ.get("GITHUB_SHA","UNSET"),
        "raw_source_records":[],"windows":{}
    }
    now=int(time.time()*1000)
    meta=pull("spot_meta_ctxs",{"type":"spotMetaAndAssetCtxs"},rec["raw_source_records"])
    try:
        bind=market_binding(meta)
    except (ValueError,TypeError,AttributeError) as exc:
        rec["error"]="MARKET_BINDING_"+type(exc).__name__
        bind=None
    if bind:
        rec["market_binding"]={"coin":bind["coin"],"universe_index":bind["universe_index"],
                               "tokens":bind["tokens"]}
        book=pull("spot_l2book",{"type":"l2Book","coin":bind["coin"]},rec["raw_source_records"])
        rec["snapshot_liquidity"]=book_audit(book)
        rec["spot_ctx_reported_dayNtlVlm_usdc"]=bind["dayNtlVlm"]
        for offset in list(range(1,8))+[14,21,28,35,60,90]:
            start=now-offset*DAY_MS
            end=start+DAY_MS-1
            label=f"af_day_minus_{offset:02d}"
            response=pull(label,{"type":"userFillsByTime","user":AF,
                                 "startTime":start,"endTime":end,"aggregateByTime":False},
                          rec["raw_source_records"])
            rec["windows"][label]=slice_audit(response,bind["coin"],start,end)
        latest=rec["windows"].get("af_day_minus_01",{})
        if latest.get("verified") and not latest.get("page_censored_ge_2000"):
            rec["latest_24h_count"]=latest["valid_exact_af_hype_buy_fills"]
            rec["latest_24h_notional_usdc"]=latest["total_execution_notional_usdc"]
            rec["latest_24h_hype_quantity"]=latest["total_hype_buy_quantity"]
            if bind["dayNtlVlm"] and Decimal(str(bind["dayNtlVlm"]))>0:
                rec["indicative_AF_buy_notional_to_spot_pair_day_volume_pct"] = str(
                    Decimal(latest["total_execution_notional_usdc"])/Decimal(str(bind["dayNtlVlm"]))*100)
                rec["volume_ratio_note"]="Different rolling-window endpoints; only an indicative market-scale diagnostic, not a causal comparison."
        bounded=[rec["windows"][f"af_day_minus_{x:02d}"] for x in range(1,8)]
        if all(r.get("verified") and not r.get("page_censored_ge_2000") and
               not r.get("bad_rows") and not r.get("out_of_window") for r in bounded):
            rec["seven_24h_windows_transport_pass"]=True
            rec["seven_day_observed_hype_buy_fills"]=sum(x["valid_exact_af_hype_buy_fills"] for x in bounded)
            rec["seven_day_observed_notional_usdc"]=str(sum((Decimal(x["total_execution_notional_usdc"]) for x in bounded), Decimal("0")))
        else:
            rec["seven_24h_windows_transport_pass"]=False
    rec["checked_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    (OUT/"SOURCE_RETENTION_LIQUIDITY_RECEIPT_V013.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
