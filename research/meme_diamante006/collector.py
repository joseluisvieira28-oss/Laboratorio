#!/usr/bin/env python3
"""MEME006 frozen, read-only prospective observations; no swaps, secrets or orders."""
import collections
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WSOL = "So11111111111111111111111111111111111111112"
RAY = "https://transaction-v1.raydium.io/compute/swap-base-in"
DEX = "https://api.dexscreener.com/latest/dex/pairs/solana/"
GECKO = "https://api.geckoterminal.com/api/v2/networks/solana/pools/"
SEED_SHA256 = "39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4"
STAKE_LAMPORTS = 50_000_000
OVERHEAD_LAMPORTS = 100_000
START_UTC = dt.datetime(2026, 11, 19, tzinfo=dt.timezone.utc)
LAST_UTC = dt.datetime(2026, 12, 24, tzinfo=dt.timezone.utc)
UA = "CryptoLab-MEME006-ReadOnly-Prospective/0.1"

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def parse_utc(s):
    return dt.datetime.fromisoformat(s.replace("Z","+00:00"))

def num(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError,OverflowError):
        return None

def number_int(v):
    try:
        x=int(v)
        return x if x>0 else None
    except (ValueError,TypeError,OverflowError):
        return None

def request(url, timeout=20):
    start=utc(); tick=time.monotonic(); raw=None; data=None; err=None; status=None
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"},method="GET")
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            status=resp.status
            raw=resp.read(1_500_000)
        data=json.loads(raw)
    except urllib.error.HTTPError as exc:
        status=exc.code;err="HTTP_"+str(exc.code)
    except (urllib.error.URLError,OSError,TimeoutError,ValueError,UnicodeDecodeError) as exc:
        err=type(exc).__name__+":"+str(exc)[:130]
    receipt=dict(url=url,requested_at=start,received_at=utc(),http_status=status,
                 elapsed_ms=round((time.monotonic()-tick)*1000),
                 body_sha256=hashlib.sha256(raw).hexdigest() if raw else None,
                 error=err)
    return data,receipt

def ray_quote(from_mint,to_mint,amount):
    qs=urllib.parse.urlencode({"inputMint":from_mint,"outputMint":to_mint,
        "amount":str(amount),"slippageBps":"50","txVersion":"V0"})
    data,receipt=request(RAY+"?"+qs)
    info=data.get("data") if isinstance(data,dict) and data.get("success") is True else None
    if not isinstance(info,dict):return None,receipt
    out=number_int(info.get("outputAmount"))
    minimum=number_int(info.get("otherAmountThreshold"))
    inp=number_int(info.get("inputAmount"))
    if not (out and minimum and inp==amount and minimum<=out):
        return None,receipt
    return dict(input_amount=inp,expected_amount=out,min_amount=minimum,
                impact_pct=num(info.get("priceImpactPct")),
                routes=[x.get("poolId") for x in (info.get("routePlan") or []) if isinstance(x,dict)]),receipt

def fixed_seed(seed_bytes):
    if hashlib.sha256(seed_bytes).hexdigest()!=SEED_SHA256:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: seed hash does not match")
    seed=json.loads(seed_bytes)
    rows=[x for x in seed.get("selection",[]) if (x.get("screen") or {}).get("status")=="SCREEN_PASS_ONLY"]
    if len(rows)!=6:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: frozen cohort is not six")
    cohort=[]
    for x in rows:
        addr=(x.get("mint") or "")
        pool=(x.get("pair") or {}).get("pair_address") or ""
        if not isinstance(addr,str) or not 32<=len(addr)<=44 or not isinstance(pool,str) or len(pool)<30:
            raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: unmapped mint/pair")
        cohort.append(dict(id=x["coingecko_id"],mint=addr,pool=pool))
    if len(set(x["mint"] for x in cohort))!=6:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: duplicate mint")
    return cohort

def verify_pair(payload,row):
    data=payload.get("pairs") if isinstance(payload,dict) else None
    if not isinstance(data,list):return None
    p=next((v for v in data if v.get("pairAddress")==row["pool"] and
            v.get("chainId")=="solana" and
            (v.get("baseToken") or {}).get("address")==row["mint"]),None)
    if p is None:return None
    tx1=(p.get("txns") or {}).get("h1") or {}
    tx24=(p.get("txns") or {}).get("h24") or {}
    age_ms=p.get("pairCreatedAt")
    age_days=(time.time()*1000-float(age_ms))/86400000 if num(age_ms) else None
    return dict(price_usd=num(p.get("priceUsd")),
        liq_usd=num((p.get("liquidity") or {}).get("usd")),
        vol24_usd=num((p.get("volume") or {}).get("h24")),
        age_days=age_days,ch1=num((p.get("priceChange") or {}).get("h1")),
        ch6=num((p.get("priceChange") or {}).get("h6")),
        tx24=(num(tx24.get("buys")) or 0)+(num(tx24.get("sells")) or 0),
        buy1=num(tx1.get("buys")),sell1=num(tx1.get("sells")))

def tags(info):
    if not info:return [],"PAIR_UNKNOWN"
    checks=[info.get("age_days"),info.get("liq_usd"),info.get("vol24_usd"),
            info.get("tx24"),info.get("ch1"),info.get("ch6"),
            info.get("buy1"),info.get("sell1"),info.get("price_usd")]
    if any(x is None for x in checks):return [],"METRICS_MISSING"
    if not (info["age_days"]>=7 and info["liq_usd"]>=150000
            and info["vol24_usd"]>=50000 and info["tx24"]>=200):
        return [],"QUALITY_REJECT"
    t1=info["buy1"]+info["sell1"]
    buying=(info["buy1"]>=info["sell1"] and t1>=20)
    labels=[]
    if buying and info["ch6"]<=-4 and info["ch1"]>=1.5:
        labels.append("H_REVERSAL")
    if buying and info["ch6"]>=5 and info["ch1"]>=2:
        labels.append("H_MOMENTUM")
    return labels,"QUALITY_PASS"

def start_state(previous_path,cohort):
    if not previous_path:
        return dict(protocol="MEME006-v0.1",created_at=utc(),seed_sha256=SEED_SHA256,
            cohort=cohort,cycle_count=0,previous_state_sha256=None,
            snapshots=[],entries=[],continuity="GENESIS")
    raw=pathlib.Path(previous_path).read_bytes()
    h=hashlib.sha256(raw).hexdigest()
    obj=json.loads(raw)
    if obj.get("seed_sha256")!=SEED_SHA256 or obj.get("cohort")!=cohort:
        raise RuntimeError("CONTINUITY_BLOCKED: cohort or seed mismatch")
    if obj.get("protocol")!="MEME006-v0.1":
        raise RuntimeError("CONTINUITY_BLOCKED: protocol mismatch")
    obj["previous_state_sha256"]=h
    obj["continuity"]="VERIFIED_PREVIOUS_ARTIFACT"
    return obj

def settle_pending(state, now, row, receipts, events):
    # Settlement at first available quote after each target. All historical entries remain archived.
    for pos in state["entries"]:
        if pos.get("mint")!=row["mint"]:continue
        entry_when=parse_utc(pos["entry_at"])
        for horizon in (4,24):
            label="h"+str(horizon)
            entry=pos["settlements"][label]
            if entry["status"]!="PENDING":continue
            target=entry_when+dt.timedelta(hours=horizon)
            end=target+dt.timedelta(hours=2 if horizon==4 else 4)
            if now<target:continue
            if now>end:
                entry.update(status="CENSORED_WINDOW_MISSED",reason="No acceptable future observation",at=utc())
                events.append({"mint":row["mint"],"policy":pos["policy"],"horizon":label,"outcome":"CENSORED_WINDOW_MISSED"})
                continue
            # Never replace missing quote by last/next DEX price.
            quote,receipt=ray_quote(row["mint"],WSOL,int(pos["min_token_amount"]))
            receipts.append(dict(source="RAY_SELL_"+label,mint=row["mint"],entry_id=pos["id"],**receipt))
            if quote is None or receipt["elapsed_ms"]>30000:
                entry["attempt_errors"]=entry.get("attempt_errors",0)+1
                continue
            net_lamports=quote["min_amount"]-STAKE_LAMPORTS-OVERHEAD_LAMPORTS
            entry.update(status="COUNTERFACTUAL_QUOTE_ONLY",at=receipt["received_at"],
                         target_at=target.isoformat(),min_out_sol_lamports=quote["min_amount"],
                         net_pct=round(100*net_lamports/STAKE_LAMPORTS,5),
                         receipt_sha256=receipt["body_sha256"],
                         route_pools=quote["routes"])
            events.append({"mint":row["mint"],"policy":pos["policy"],"horizon":label,
                           "outcome":"COUNTERFACTUAL_QUOTE_ONLY","net_pct":entry["net_pct"]})

def observe_one(row, state, now):
    receipts=[]; events=[]
    p,pr=request(DEX+urllib.parse.quote(row["pool"],safe=""))
    receipts.append(dict(source="DEX_PAIR",mint=row["mint"],**pr))
    info=verify_pair(p,row)
    labels,quality=tags(info)
    g,gpr=request(GECKO+urllib.parse.quote(row["pool"],safe=""))
    receipts.append(dict(source="GECKO_POOL",mint=row["mint"],**gpr))
    attr=(((g or {}).get("data") or {}).get("attributes") or {}) if isinstance(g,dict) else {}
    pxg=num(attr.get("base_token_price_usd"))
    pxd=info.get("price_usd") if info else None
    mismatch=abs(pxg-pxd)/pxd if pxd and pxg else None
    verified=(mismatch is not None and mismatch<=.03)
    snap=dict(id=row["id"],mint=row["mint"],pool=row["pool"],
        at=utc(),quality_status=quality,signal_tags=labels,
        pair=info,gecko_price_usd=pxg,
        disagreement_pct=round(100*mismatch,4) if mismatch is not None else None,
        cross_source_ok=verified,decision="NO_ENTRY",
        receipts=receipts)
    # Quotes still tested only for source-qualified, not to hide failed pool observations.
    if quality!="QUALITY_PASS" or not verified:
        snap["decision"]="SOURCE_UNVERIFIED" if quality=="QUALITY_PASS" else quality
        settle_pending(state,now,row,receipts,events)
        return snap,events
    latest=max((parse_utc(e["entry_at"]) for e in state["entries"] if e.get("mint")==row["mint"]),default=None)
    if latest is not None and (now-latest).total_seconds()<4*3600:
        snap["decision"]="COOLDOWN_4H"
        settle_pending(state,now,row,receipts,events)
        return snap,events
    buy,br=ray_quote(WSOL,row["mint"],STAKE_LAMPORTS)
    receipts.append(dict(source="RAY_BUY",mint=row["mint"],**br))
    if buy is None or br["elapsed_ms"]>30000:
        snap["decision"]="BUY_QUOTE_UNAVAILABLE"
        settle_pending(state,now,row,receipts,events)
        return snap,events
    sell,sr=ray_quote(row["mint"],WSOL,buy["min_amount"])
    receipts.append(dict(source="RAY_IMMEDIATE_SELL",mint=row["mint"],**sr))
    if sell is None or sr["elapsed_ms"]>30000:
        snap["decision"]="SELL_QUOTE_UNAVAILABLE"
        settle_pending(state,now,row,receipts,events)
        return snap,events
    stressed=100*(1-sell["min_amount"]/STAKE_LAMPORTS)
    snap["immediate_cost_stress_pct"]=round(stressed,5)
    if stressed>2.50:
        snap["decision"]="COST_GT_2_50PCT"
        settle_pending(state,now,row,receipts,events)
        return snap,events
    received=br["received_at"]
    position=dict(id=hashlib.sha256((row["mint"]+received).encode()).hexdigest()[:20],
        id_name=row["id"],mint=row["mint"],pool=row["pool"],entry_at=received,
        policy=labels or ["CONTROL_UNCONDITIONAL"],
        min_token_amount=buy["min_amount"],stake_lamports=STAKE_LAMPORTS,
        entry_buy_sha256=br["body_sha256"],entry_sell_check_sha256=sr["body_sha256"],
        immediately_reversible_cost_pct=round(stressed,5),
        asof_features=dict(ch1=info["ch1"],ch6=info["ch6"],buy1=info["buy1"],
                           sell1=info["sell1"],liq=info["liq_usd"],vol24=info["vol24_usd"]),
        settlements={"h4":{"status":"PENDING"},"h24":{"status":"PENDING"}})
    state["entries"].append(position)
    snap["decision"]="SHADOW_ENTRY_QUOTE_ONLY"
    snap["entry_id"]=position["id"]
    settle_pending(state,now,row,receipts,events)
    return snap,events

def main():
    seed=pathlib.Path(sys.argv[1]).read_bytes()
    cohort=fixed_seed(seed)
    state=start_state(sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!="NONE" else None,cohort)
    now=dt.datetime.now(dt.timezone.utc)
    if now<START_UTC or now>=LAST_UTC:
        print("MEME006_WINDOW_CLOSED: no API calls");return 0
    prev=parse_utc(state["snapshots"][-1]["completed_at"]) if state.get("snapshots") else None
    if prev and now<=prev:
        raise RuntimeError("CONTINUITY_BLOCKED: event time non-increasing")
    snaps=[];settled=[]
    for row in cohort:
        snap,events=observe_one(row,state,now)
        snaps.append(snap);settled.extend(events)
        time.sleep(.20)
    state["cycle_count"]+=1
    state["snapshots"].append(dict(run=state["cycle_count"],started_at=now.isoformat(),
                                  completed_at=utc(),coins=snaps,settlement_events=settled))
    outdir=pathlib.Path("meme006-ledger")
    outdir.mkdir(exist_ok=True)
    raw=json.dumps(state,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
    (outdir/"state.json").write_bytes(raw)
    (outdir/"state.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  state.json\n",encoding="utf8")
    decisions=collections.Counter(s["decision"] for s in snaps)
    labels=collections.Counter(t for s in snaps for t in s["signal_tags"])
    counters=collections.Counter(x["status"] for e in state["entries"] for x in e["settlements"].values())
    print("MEME006_RECEIPT="+json.dumps(dict(cycle=state["cycle_count"],first_at=now.isoformat(),
         coins=len(snaps),decisions=dict(decisions),labels=dict(labels),
         entries=len(state["entries"]),settlement_statuses=dict(counters),
         state_sha256=hashlib.sha256(raw).hexdigest(),previous_sha256=state["previous_state_sha256"],
         trades=0,orders=0,economic_status="NO-GO"),sort_keys=True))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (ValueError,RuntimeError,OSError,KeyError) as exc:
        print("MEME006_BLOCKED:"+str(exc),file=sys.stderr)
        sys.exit(3)
