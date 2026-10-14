from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
from collections import defaultdict, deque
from datetime import datetime, timezone

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","BNBUSDT"]
NOTIONALS=[100.0,500.0,1000.0,5000.0]
BASE_BPS=5.5
STRESS_BPS=10.0
HOLD_MS=30_000
COOLDOWN_MS=60_000
BOOTSTRAPS=10_000
SEED=260923

def iso_ms(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def iter_messages(paths,boundary_ms):
    for p in paths:
        with pathlib.Path(p).open("r",encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                env=json.loads(line)
                recv=env.get("received_at_utc")
                if not recv or iso_ms(recv)<boundary_ms:
                    continue
                yield env.get("message") or {}

def apply_side(side,rows):
    for r in rows or []:
        if not isinstance(r,list) or len(r)<2:
            continue
        p=float(r[0]); q=float(r[1])
        if q==0:
            side.pop(p,None)
        else:
            side[p]=q

def book_valid(book):
    if not book or not book["b"] or not book["a"]:
        return False
    return max(book["b"])<min(book["a"])

def asks(book):
    return sorted(book["a"].items())

def bids(book):
    return sorted(book["b"].items(),reverse=True)

def buy_for_quote(levels,quote):
    left=quote; base=0.0; spent=0.0
    for p,q in levels:
        level=p*q
        take_quote=min(left,level)
        take_base=take_quote/p
        base+=take_base; spent+=take_quote; left-=take_quote
        if left<=1e-9:
            break
    if left>1e-7:
        return None
    return {"base_qty":base,"quote_value":spent}

def sell_for_quote(levels,quote):
    left=quote; base=0.0; proceeds=0.0
    for p,q in levels:
        level=p*q
        take_quote=min(left,level)
        take_base=take_quote/p
        base+=take_base; proceeds+=take_quote; left-=take_quote
        if left<=1e-9:
            break
    if left>1e-7:
        return None
    return {"base_qty":base,"quote_value":proceeds}

def buy_qty(levels,qty):
    left=qty; cost=0.0
    for p,q in levels:
        take=min(left,q); cost+=take*p; left-=take
        if left<=1e-12:
            break
    if left>1e-10:
        return None
    return cost

def sell_qty(levels,qty):
    left=qty; proceeds=0.0
    for p,q in levels:
        take=min(left,q); proceeds+=take*p; left-=take
        if left<=1e-12:
            break
    if left>1e-10:
        return None
    return proceeds

def bootstrap_lower95(rows,key):
    by_day=defaultdict(list)
    for r in rows:
        by_day[r["utc_day"]].append(r[key])
    days=sorted(by_day)
    if len(days)<2:
        return None
    rng=random.Random(SEED)
    means=[]
    for _ in range(BOOTSTRAPS):
        vals=[]
        for _j in range(len(days)):
            d=days[rng.randrange(len(days))]
            vals.extend(by_day[d])
        means.append(statistics.fmean(vals))
    means.sort()
    return means[max(0,math.floor(0.025*len(means))-1)]

def concentration(rows,group_key,pnl_key):
    pos=[r for r in rows if r[pnl_key]>0]
    total=sum(r[pnl_key] for r in pos)
    if total<=0:
        return {"top_group_share":None,"top1pct_event_share":None}
    g=defaultdict(float)
    for r in pos:
        g[r[group_key]]+=r[pnl_key]
    top_group=max(g.values())/total if g else None
    k=max(1,math.ceil(0.01*len(pos)))
    top1=sum(sorted((r[pnl_key] for r in pos),reverse=True)[:k])/total
    return {"top_group_share":top_group,"top1pct_event_share":top1}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--thresholds",required=True)
    ap.add_argument("--input",required=True,nargs="+")
    ap.add_argument("--output-dir",default=None)
    args=ap.parse_args()

    thr=json.loads(pathlib.Path(args.thresholds).read_text(encoding="utf-8"))
    if thr.get("canonical_thresholds_emitted") is not True or thr.get("verdict")!="SOURCE_CALIBRATION_PASS_READY_TO_FREEZE":
        raise SystemExit("canonical threshold gate not open")
    boundary=iso_ms(thr["generated_at_utc"])
    thresholds={}
    for sym,row in (thr.get("thresholds") or {}).items():
        q=row.get("q95_nearest_rank_usdt")
        if row.get("eligible") and q is not None:
            thresholds[sym]=float(q)
    if not thresholds:
        raise SystemExit("no canonical eligible symbol thresholds")

    # Pass 1: source-only candidate bursts, strictly post-threshold-freeze.
    bins=defaultdict(lambda:{"long":0.0,"short":0.0})
    for msg in iter_messages(args.input,boundary):
        topic=msg.get("topic","")
        if not topic.startswith("allLiquidation."):
            continue
        data=msg.get("data") or []
        if not isinstance(data,list):
            data=[data]
        for x in data:
            try:
                sym=str(x["s"])
                if sym not in thresholds:
                    continue
                t=int(x["T"]); side=str(x["S"]); n=float(x["v"])*float(x["p"])
            except Exception:
                continue
            k=(sym,(t//5000)*5000)
            if side=="Buy":
                bins[k]["long"]+=n
            elif side=="Sell":
                bins[k]["short"]+=n

    cands=defaultdict(list)
    for (sym,start),x in bins.items():
        total=x["long"]+x["short"]
        if total < thresholds[sym]:
            continue
        net=x["short"]-x["long"]
        if net==0:
            continue
        cands[sym].append({
            "symbol":sym,
            "burst_start_ms":start,
            "burst_close_ms":start+5000,
            "long_liq_notional":x["long"],
            "short_liq_notional":x["short"],
            "total_liq_notional":total,
            "net_forced_buy_notional":net,
            "direction":"SHORT" if net>0 else "LONG",
        })
    queues={s:deque(sorted(cands[s],key=lambda x:x["burst_close_ms"])) for s in SYMBOLS}

    # Pass 2: causal book/ticker state machine.
    books={s:{"b":{},"a":{}} for s in SYMBOLS}
    latest_funding={s:None for s in SYMBOLS}
    active={s:None for s in SYMBOLS}
    cooldown={s:0 for s in SYMBOLS}
    event_counter=0
    rows=[]
    excluded=defaultdict(int)
    completed_events=set()
    completed_by_symbol=defaultdict(set)
    event_days=set()

    def start_event(sym,c,book_ts):
        nonlocal event_counter
        f=latest_funding.get(sym)
        if not f:
            excluded["missing_funding_metadata"]+=1
            cooldown[sym]=book_ts+HOLD_MS+COOLDOWN_MS
            return
        exit_target=book_ts+HOLD_MS
        if f["next_funding_time_ms"]>book_ts and f["next_funding_time_ms"]<=exit_target:
            excluded["funding_overlap"]+=1
            cooldown[sym]=exit_target+COOLDOWN_MS
            return

        entries={}
        for n in NOTIONALS:
            if c["direction"]=="LONG":
                e=buy_for_quote(asks(books[sym]),n)
            else:
                e=sell_for_quote(bids(books[sym]),n)
            entries[str(int(n))]=e
        if not any(v is not None for v in entries.values()):
            excluded["entry_depth_insufficient"]+=1
            cooldown[sym]=exit_target+COOLDOWN_MS
            return
        event_counter+=1
        active[sym]={
            "event_id":f"{sym}-{event_counter}",
            "candidate":c,
            "entry_ts_ms":book_ts,
            "exit_target_ms":exit_target,
            "entries":entries,
        }

    def finish_event(sym,book_ts):
        a=active[sym]
        if not a:
            return
        c=a["candidate"]
        day=datetime.fromtimestamp(a["entry_ts_ms"]/1000,tz=timezone.utc).date().isoformat()
        any_complete=False
        for n in NOTIONALS:
            e=a["entries"].get(str(int(n)))
            if not e:
                continue
            if c["direction"]=="LONG":
                exit_value=sell_qty(bids(books[sym]),e["base_qty"])
                entry_value=e["quote_value"]
                if exit_value is None:
                    continue
                gross=exit_value-entry_value
                leg1=entry_value; leg2=exit_value
            else:
                exit_value=buy_qty(asks(books[sym]),e["base_qty"])
                entry_value=e["quote_value"]
                if exit_value is None:
                    continue
                gross=entry_value-exit_value
                leg1=entry_value; leg2=exit_value
            base_fee=(leg1+leg2)*(BASE_BPS/10000.0)
            stress_fee=(leg1+leg2)*(STRESS_BPS/10000.0)
            base_net=gross-base_fee
            stress_net=gross-stress_fee
            rows.append({
                "event_id":a["event_id"],
                "symbol":sym,
                "utc_day":day,
                "direction":c["direction"],
                "burst_close_ms":c["burst_close_ms"],
                "entry_ts_ms":a["entry_ts_ms"],
                "exit_ts_ms":book_ts,
                "notional_usdt":n,
                "base_net_usdt":base_net,
                "stress_net_usdt":stress_net,
                "base_net_bps":base_net/n*10000.0,
                "stress_net_bps":stress_net/n*10000.0,
                "gross_usdt":gross,
                "total_liq_notional":c["total_liq_notional"],
                "net_forced_buy_notional":c["net_forced_buy_notional"],
            })
            any_complete=True
        if any_complete:
            completed_events.add(a["event_id"])
            completed_by_symbol[sym].add(a["event_id"])
            event_days.add(day)
        else:
            excluded["exit_depth_insufficient"]+=1
        cooldown[sym]=book_ts+COOLDOWN_MS
        active[sym]=None

    for msg in iter_messages(args.input,boundary):
        topic=msg.get("topic","")
        if topic.startswith("tickers."):
            d=msg.get("data") or {}
            sym=d.get("symbol") or topic.split(".",1)[1]
            try:
                nxt=int(d["nextFundingTime"])
                interval=int(d["fundingIntervalHour"])
            except Exception:
                continue
            if sym in latest_funding:
                latest_funding[sym]={"next_funding_time_ms":nxt,"funding_interval_hours":interval}
            continue

        if not topic.startswith("orderbook.50."):
            continue
        d=msg.get("data") or {}
        sym=d.get("s") or topic.rsplit(".",1)[-1]
        if sym not in books:
            continue
        typ=msg.get("type")
        if typ=="snapshot" or d.get("u")==1:
            books[sym]={"b":{},"a":{}}
            apply_side(books[sym]["b"],d.get("b"))
            apply_side(books[sym]["a"],d.get("a"))
        elif typ=="delta":
            apply_side(books[sym]["b"],d.get("b"))
            apply_side(books[sym]["a"],d.get("a"))
        else:
            continue
        try:
            book_ts=int(d.get("cts") or msg.get("ts"))
        except Exception:
            excluded["book_timestamp_missing"]+=1
            continue
        if not book_valid(books[sym]):
            excluded["invalid_or_crossed_book"]+=1
            continue

        if active[sym] and book_ts>=active[sym]["exit_target_ms"]:
            finish_event(sym,book_ts)

        q=queues[sym]
        while q and q[0]["burst_close_ms"]<=book_ts:
            c=q.popleft()
            if active[sym]:
                excluded["overlap_active"]+=1
                continue
            if c["burst_close_ms"]<cooldown[sym]:
                excluded["cooldown_overlap"]+=1
                continue
            start_event(sym,c,book_ts)
            if active[sym]:
                break

    # Aggregate and adjudicate.
    metrics={}
    qualifying=[]
    for n in NOTIONALS:
        rr=[r for r in rows if r["notional_usdt"]==n]
        if not rr:
            metrics[str(int(n))]={"count":0}
            continue
        base=[r["base_net_bps"] for r in rr]
        stress=[r["stress_net_bps"] for r in rr]
        bysym=defaultdict(list)
        for x in rr:
            bysym[x["symbol"]].append(x["base_net_bps"])
        positive_symbols=sum(1 for v in bysym.values() if statistics.fmean(v)>0)
        sym_conc=concentration(rr,"symbol","base_net_usdt")
        day_conc=concentration(rr,"utc_day","base_net_usdt")
        lower=bootstrap_lower95(rr,"base_net_bps")
        m={
            "count":len(rr),
            "base_total_usdt":sum(x["base_net_usdt"] for x in rr),
            "stress_total_usdt":sum(x["stress_net_usdt"] for x in rr),
            "base_mean_bps":statistics.fmean(base),
            "stress_mean_bps":statistics.fmean(stress),
            "base_median_bps":statistics.median(base),
            "stress_median_bps":statistics.median(stress),
            "base_positive_rate":sum(x>0 for x in base)/len(base),
            "base_cluster_bootstrap_lower95_bps":lower,
            "positive_base_mean_symbols":positive_symbols,
            "top_symbol_positive_pnl_share":sym_conc["top_group_share"],
            "top_day_positive_pnl_share":day_conc["top_group_share"],
            "top1pct_event_positive_pnl_share":sym_conc["top1pct_event_share"],
        }
        m["bucket_pass"]=(
            m["base_mean_bps"]>0
            and m["stress_mean_bps"]>0
            and lower is not None and lower>0
            and m["base_positive_rate"]>0.50
            and positive_symbols>=3
            and m["top_symbol_positive_pnl_share"] is not None and m["top_symbol_positive_pnl_share"]<=0.50
            and m["top_day_positive_pnl_share"] is not None and m["top_day_positive_pnl_share"]<=0.25
            and m["top1pct_event_positive_pnl_share"] is not None and m["top1pct_event_positive_pnl_share"]<=0.50
        )
        if m["bucket_pass"]:
            qualifying.append(n)
        metrics[str(int(n))]=m

    per_symbol_events={s:len(completed_by_symbol[s]) for s in SYMBOLS}
    sample_pass=(
        len(completed_events)>=500
        and sum(v>=75 for v in per_symbol_events.values())>=3
        and len(event_days)>=14
    )
    if not sample_pass:
        verdict="INSUFFICIENT_FORWARD_SAMPLE"
    elif len(qualifying)>=2:
        verdict="SURVIVES_DISCOVERY"
    else:
        verdict="NO_EDGE"

    outdir=pathlib.Path(args.output_dir) if args.output_dir else pathlib.Path(args.thresholds).resolve().parent
    outdir.mkdir(parents=True,exist_ok=True)
    receipt={
        "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
        "mve_id":"LP2-BYBIT-REV5S-Q95-H30-V1",
        "phase":"FORWARD_ECONOMIC_ENGINE_V0.1",
        "forward_boundary_utc":thr["generated_at_utc"],
        "canonical_threshold_symbols":sorted(thresholds),
        "candidate_bursts":sum(len(v) for v in cands.values()),
        "completed_independent_events":len(completed_events),
        "completed_events_by_symbol":per_symbol_events,
        "distinct_utc_days":len(event_days),
        "excluded_counts":dict(excluded),
        "metrics":metrics,
        "qualifying_notional_buckets":qualifying,
        "sample_gate_pass":sample_pass,
        "verdict":verdict,
        "orders_submitted":0,
        "authenticated_endpoints_used":False,
        "wallet_mutations":0,
    }
    (outdir/"forward_economic_engine_v0_1_receipt.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8"
    )
    (outdir/"forward_economic_engine_v0_1_events.json").write_text(
        json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8"
    )
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
