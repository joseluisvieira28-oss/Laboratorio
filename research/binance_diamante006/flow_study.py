#!/usr/bin/env python3
"""BINANCE006 -- frozen 90-day historical Spot aggTrade prints-only long counterfactual.

This does NOT reconstruct L2 depth, verify absorption, or simulate real fills.
Chronological as-of decision logic; future trade prints only used AFTER a decision.
"""
from __future__ import annotations
import calendar
import csv
import datetime as dt
import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
START=dt.datetime(2026,8,1,tzinfo=dt.timezone.utc)
VALID_START=dt.datetime(2026,8,31,tzinfo=dt.timezone.utc)
TEST_START=dt.datetime(2026,9,30,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)
US=1_000_000
T0=int(START.timestamp()*US)
T_VALID=int(VALID_START.timestamp()*US)
T_TEST=int(TEST_START.timestamp()*US)
T_END=int(END.timestamp()*US)
WINDOW=30*US
HORIZON=60*US
WAIT=3*US
COOLDOWN=120*US
FEES_BPS=10.0
BASE_SLIP_BPS=2.0
STRESS_SLIP_BPS=5.0
MIN_NOTIONAL=5000.0
MIN_SELL_SHARE=0.65
SEED=20261123
MIN_OOS_EVENTS=200
MIN_OOS_DAYS=20

def group_of(ts:int)->str:
    if T0<=ts<T_VALID:return "TRAIN"
    if T_VALID<=ts<T_TEST:return "VALIDATION"
    if T_TEST<=ts<T_END:return "TEST"
    return "OUTSIDE"

def utc_date(ts:int)->str:
    return dt.datetime.fromtimestamp(ts/US,tz=dt.timezone.utc).strftime("%Y-%m-%d")

@dataclass(frozen=True)
class Trade:
    ts_us:int
    agg_id:int
    price:float
    qty:float
    buyer_maker:bool

def parse_agg_row(raw, previous_id=None, previous_ts=None):
    """Binance official SPOT aggTrades 2025+ CSV (microseconds)."""
    if len(raw)!=8:
        raise ValueError("AGG_WRONG_8_FIELDS")
    ident=int(raw[0]);price=float(raw[1]);qty=float(raw[2])
    first_id=int(raw[3]);last_id=int(raw[4]);ts=int(raw[5])
    if raw[6].lower() not in ("true","false") or raw[7].lower() not in ("true","false"):
        raise ValueError("AGG_INVALID_BOOL")
    if not (1_700_000_000_000_000<=ts<1_900_000_000_000_000):
        raise ValueError("SPOT_2026_TIMESTAMP_NOT_MICROSECONDS")
    if ident<0 or first_id<0 or last_id<first_id:
        raise ValueError("TRADE_IDS_INVALID")
    if previous_id is not None and ident<=previous_id:
        raise ValueError("NON_INCREASING_AGG_ID")
    if previous_ts is not None and ts<previous_ts:
        raise ValueError("NON_MONOTONIC_AGG_TIMESTAMP")
    if not(math.isfinite(price) and math.isfinite(qty) and price>0 and qty>0):
        raise ValueError("INVALID_PRICE_OR_QUANTITY")
    return Trade(ts,ident,price,qty,raw[6].lower()=="true")

def quote_net_bps(entry_price,exit_price,slip_bps):
    cost=(FEES_BPS+slip_bps)/10000.0
    return (((exit_price/entry_price)*(1-cost)/(1+cost))-1)*10000

class FlowStudy:
    def __init__(self,symbol):
        if symbol not in SYMBOLS:raise ValueError("BAD_SYMBOL")
        self.symbol=symbol
        self.bucket_end=T0+WINDOW
        self.bucket_index=0
        self.bucket_n=0
        self.notional=0.0
        self.sell_notional=0.0
        self.events=[]
        self.active={}
        self.last_decision={}
        self.trades=0
        self.notional_by_day=defaultdict(float)
        self.trade_count_by_day=Counter()
        self.source_first_by_day={}
        self.source_last_by_day={}
        self.decisions=Counter()
        self.censored=Counter()
        self.previous_ts=None
        self.previous_id=None

    def _censor(self,event,reason):
        event["status"]=reason
        self.censored[reason]+=1
        self.events.append(event)
        self.active.pop(event["kind"],None)

    def _close_bucket(self):
        ts=self.bucket_end
        cohort=group_of(ts)
        if cohort!="OUTSIDE" and self.bucket_n:
            if self.bucket_index%4==3:self._new_decision("BASELINE",ts)
            if self.notional>=MIN_NOTIONAL and self.sell_notional/self.notional>=MIN_SELL_SHARE:
                self._new_decision("SELL_FLOW",ts)
        self.bucket_end+=WINDOW
        self.bucket_index+=1
        self.bucket_n=0;self.notional=0.0;self.sell_notional=0.0

    def _new_decision(self,kind,ts):
        previous=self.last_decision.get(kind)
        if previous is not None and ts-previous<COOLDOWN:return
        if kind in self.active:
            self._censor(self.active[kind],"CENSORED_OVERLAP_PENDING")
        self.last_decision[kind]=ts
        record={"symbol":self.symbol,"kind":kind,"cohort":group_of(ts),
                "decision_us":ts,"decision_date_utc":utc_date(ts),
                "status":"WAIT_ENTRY","entry_us":None,"exit_us":None,
                "entry_price":None,"exit_price":None,
                "gross_bps":None,"base_net_bps":None,"stress_net_bps":None}
        self.active[kind]=record
        self.decisions[(cohort_name(kind),record["cohort"])]+=1

    def _process_active(self,ts,price):
        for kind,event in list(self.active.items()):
            if event["status"]=="WAIT_ENTRY":
                elapsed=ts-event["decision_us"]
                if elapsed<=0:continue
                if elapsed>WAIT:
                    self._censor(event,"CENSORED_ENTRY_DELAY")
                    continue
                if group_of(ts)!=event["cohort"]:
                    self._censor(event,"CENSORED_CROSS_COHORT")
                    continue
                event["entry_us"]=ts
                event["entry_price"]=price
                event["status"]="WAIT_EXIT"
            elif event["status"]=="WAIT_EXIT":
                delta=ts-event["entry_us"]
                if delta<HORIZON:continue
                if delta>HORIZON+WAIT:
                    self._censor(event,"CENSORED_EXIT_DELAY")
                    continue
                if group_of(ts)!=event["cohort"]:
                    self._censor(event,"CENSORED_CROSS_COHORT")
                    continue
                event["exit_us"]=ts
                event["exit_price"]=price
                event["gross_bps"]=(price/event["entry_price"]-1)*10000
                event["base_net_bps"]=quote_net_bps(event["entry_price"],price,BASE_SLIP_BPS)
                event["stress_net_bps"]=quote_net_bps(event["entry_price"],price,STRESS_SLIP_BPS)
                event["status"]="MATURED_NOT_FILLED"
                self.events.append(event)
                del self.active[kind]

    def ingest(self,trade):
        ts=trade.ts_us
        if self.previous_ts is not None and ts<self.previous_ts:raise ValueError("TRADE_TS_REGRESSED")
        if self.previous_id is not None and trade.agg_id<=self.previous_id:raise ValueError("TRADE_ID_REGRESSED")
        self.previous_ts=ts;self.previous_id=trade.agg_id
        if not T0<=ts<T_END:
            raise ValueError("OUTSIDE_FROZEN_90_DAY_SCOPE")
        # CLOSE PREVIOUS BUCKETS BEFORE USING THE CURRENT NEW TRADE
        while ts>=self.bucket_end and self.bucket_end<=T_END:
            self._close_bucket()
        # Only after original decision windows are sealed may this print form an entry/exit
        self._process_active(ts,trade.price)
        quote=trade.price*trade.qty
        self.notional+=quote
        if trade.buyer_maker:self.sell_notional+=quote
        self.bucket_n+=1
        day=utc_date(ts)
        self.trades+=1
        self.trade_count_by_day[day]+=1
        self.notional_by_day[day]+=quote
        if day not in self.source_first_by_day:self.source_first_by_day[day]=ts
        self.source_last_by_day[day]=ts

    def finish(self):
        while self.bucket_end<=T_END:
            self._close_bucket()
        for event in list(self.active.values()):
            self._censor(event,"CENSORED_ARCHIVE_END")
        return self.events

def cohort_name(kind):return kind

def bootstrap_cluster_lower(rows, reps=10000, seed=SEED):
    by_day=defaultdict(list)
    for event in rows:
        by_day[event["decision_date_utc"]].append(event["stress_net_bps"])
    days=sorted(by_day)
    if len(days)<MIN_OOS_DAYS:return None
    by_day_sum=[sum(by_day[x]) for x in days]
    by_day_count=[len(by_day[x]) for x in days]
    rng=random.Random(seed)
    vals=[]
    for _ in range(reps):
        chosen=[rng.randrange(len(days)) for _ in days]
        vals.append(sum(by_day_sum[x] for x in chosen)/sum(by_day_count[x] for x in chosen))
    vals.sort()
    return vals[int(0.05*reps)]

def summarize(events):
    """Read every original signal, baseline and CENSORED separately, no selection."""
    results={}
    for cohort in ("TRAIN","VALIDATION","TEST"):
        results[cohort]={}
        for kind in ("SELL_FLOW","BASELINE"):
            records=[e for e in events if e["cohort"]==cohort and e["kind"]==kind]
            matured=[e for e in records if e["status"]=="MATURED_NOT_FILLED"]
            vals=[e["stress_net_bps"] for e in matured]
            bysym={}
            for s in SYMBOLS:
                z=[e["stress_net_bps"] for e in matured if e["symbol"]==s]
                bysym[s]={"matured":len(z),"mean_stress_net_bps":statistics.mean(z) if z else None,
                          "positive_after_costs":sum(v>0 for v in z)}
            results[cohort][kind]={
                "decisions":len(records),"matured":len(matured),
                "censored":len(records)-len(matured),
                "censored_reasons":dict(Counter(e["status"] for e in records if e["status"]!="MATURED_NOT_FILLED")),
                "utc_days_with_matured":len(set(e["decision_date_utc"] for e in matured)),
                "mean_gross_bps":statistics.mean(e["gross_bps"] for e in matured) if matured else None,
                "mean_base_net_bps":statistics.mean(e["base_net_bps"] for e in matured) if matured else None,
                "mean_stress_net_bps":statistics.mean(vals) if vals else None,
                "positive_after_costs":sum(v>0 for v in vals),
                "positive_after_cost_rate":sum(v>0 for v in vals)/len(vals) if vals else None,
                "median_stress_net_bps":statistics.median(vals) if vals else None,
                "min_stress_net_bps":min(vals) if vals else None,
                "max_stress_net_bps":max(vals) if vals else None,
                "per_symbol":bysym
            }
    primary=[e for e in events if e["cohort"]=="TEST" and e["kind"]=="SELL_FLOW" and e["status"]=="MATURED_NOT_FILLED"]
    controls=[e for e in events if e["cohort"]=="TEST" and e["kind"]=="BASELINE" and e["status"]=="MATURED_NOT_FILLED"]
    distinct=len(set(e["decision_date_utc"] for e in primary))
    lower=bootstrap_cluster_lower(primary) if len(primary)>=MIN_OOS_EVENTS else None
    positive_by_day=defaultdict(float)
    for e in primary:positive_by_day[e["decision_date_utc"]]+=max(0.0,e["stress_net_bps"])
    total=sum(positive_by_day.values())
    max_share=max(positive_by_day.values())/total if total>0 else None
    enough=(len(primary)>=MIN_OOS_EVENTS and distinct>=MIN_OOS_DAYS)
    mean_p=results["TEST"]["SELL_FLOW"]["mean_stress_net_bps"]
    mean_b=results["TEST"]["BASELINE"]["mean_stress_net_bps"]
    relative=(mean_p is not None and mean_b is not None and mean_p>mean_b)
    all_go=bool(enough and mean_p>0 and lower is not None and lower>0
                and max_share is not None and max_share<=0.20 and relative)
    if not enough:verdict="INCONCLUSIVE_INSUFFICIENT_OOS_SAMPLE"
    elif all_go:verdict="GO_SCIENTIFIC_LIMITED_REPLICATION_NEEDED"
    else:verdict="NO_GO_ECONOMIC_FOR_FLOW_ONLY_PRINT_PROXY"
    return {"study":"BINANCE006_SPOT_AGGTRADE_FLOWONLY_90D_V01",
            "status":verdict,
            "source_verified_externally":False,
            "hypothetical_only":True,"actual_trades":0,
            "cost_assumption":"taker10bps+slippage5bps per side stress; printed prices NOT executable quotes",
            "independent_test_min_events":MIN_OOS_EVENTS,
            "independent_test_min_days":MIN_OOS_DAYS,
            "test_events":len(primary),"test_days_with_events":distinct,
            "test_lower_95_day_bootstrap_stress_bps":lower,
            "test_max_single_day_positive_gain_share":max_share,
            "test_above_unconditional_baseline":relative,
            "economic_go_scientific_limited":all_go,
            "live_trading_go":False,"groups":results}

def write_events_csv(events,path):
    fields=["symbol","kind","cohort","decision_us","decision_date_utc",
            "status","entry_us","exit_us","entry_price","exit_price","gross_bps","base_net_bps","stress_net_bps"]
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for e in events:w.writerow({key:e.get(key) for key in fields})
