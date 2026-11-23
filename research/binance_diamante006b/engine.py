#!/usr/bin/env python3
"""BINANCE-006B — fixed 1s Kline SELL-flow proxy, no L2 and NO FILLS.
All input is Binance Spot public 1s archive, prices from CLOSE OF COMPLETED BAR.
Never claim this is a real quote available for a marketable order.
"""
from __future__ import annotations
import datetime as dt
import math
import random
import statistics
from collections import Counter,defaultdict

UTC=dt.timezone.utc
US=1_000_000
S=(("BTCUSDT","ETHUSDT","SOLUSDT"))
T0=int(dt.datetime(2026,8,1,tzinfo=UTC).timestamp()*US)
TV=int(dt.datetime(2026,8,31,tzinfo=UTC).timestamp()*US)
TT=int(dt.datetime(2026,9,30,tzinfo=UTC).timestamp()*US)
TE=int(dt.datetime(2026,10,30,tzinfo=UTC).timestamp()*US)
DAY=86400*US
WINDOW=30*US
HOLD=60*US
WAIT=3*US
COOLDOWN=120*US
MIN_QUOTE=5000.0
MIN_SELL=0.65
SEED=20261123

def cohort(ts_us):
    # Use the last MICROSECOND before decision for previous closed 30s candle.
    if T0<=ts_us<TV:return "TRAIN"
    if TV<=ts_us<TT:return "VALIDATION"
    if TT<=ts_us<TE:return "TEST"
    return "OUTSIDE"

def day_of(ts):
    return dt.datetime.fromtimestamp(ts/US,tz=UTC).strftime("%Y-%m-%d")

def net_bps(entry,exit,slip_bps):
    x=(10.0+slip_bps)/10000
    return 10000*(exit/entry*(1-x)/(1+x)-1)

def parse_1s(row):
    if len(row)!=12:raise ValueError("WRONG_SPOT_KLINE_CSV_COLUMN_COUNT")
    try:
        start=int(row[0]);end=int(row[6])
        o,h,l,c=map(float,(row[1],row[2],row[3],row[4]))
        vol=float(row[7]);n=int(row[8]);buyer=float(row[10])
    except Exception as exc:raise ValueError("INVALID_KLINE_FIELD") from exc
    if not (1_700_000_000_000_000<=start<1_900_000_000_000_000):
        raise ValueError("NOT_2026_SPOT_MICROSECONDS")
    if start%US or end!=start+US-1:raise ValueError("UNALIGNED_OR_BAD_CLOSE_MICROSECONDS")
    if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)):
        raise ValueError("INVALID_KLINE_OHLC")
    if h<max(o,c,l) or l>min(o,c,h):raise ValueError("OHLC_INCONSISTENT")
    if not (math.isfinite(vol) and math.isfinite(buyer) and vol>=0 and buyer>=0):
        raise ValueError("INVALID_KLINE_QUOTE_VOLUME")
    if buyer>vol+max(0.00000001,vol*1e-11):
        raise ValueError("TAKER_BUY_QUOTE_EXCEEDS_TOTAL")
    if n<0:raise ValueError("INVALID_KLINE_AGG_TRADE_COUNT")
    if n==0 and vol>0.00000001:raise ValueError("QUOTE_WITH_ZERO_TRADE_COUNT")
    return start,c,vol,max(0.0,vol-buyer)

class KlineFlow:
    def __init__(self,symbol):
        if symbol not in S:raise ValueError("UNAPPROVED_SYMBOL")
        self.symbol=symbol
        self.last_start=None
        self.bins=0
        self.quote=0.0;self.sells=0.0
        self.bucket_seen=0
        self.active={}
        self.last_decision={}
        self.events=[]
        self.decisions=Counter()
        self.days=Counter()
        self.source_1s_rows=0

    def _done(self,event,status):
        event["status"]=status
        self.events.append(event)
        self.active.pop(event["kind"],None)

    def _decision(self,kind,ts):
        prior=self.last_decision.get(kind)
        if prior is not None and ts-prior<COOLDOWN:return
        if kind in self.active:
            self._done(self.active[kind],"CENSORED_PREVIOUS_PENDING")
        self.last_decision[kind]=ts
        window_cohort=cohort(ts-1)
        if window_cohort=="OUTSIDE":return
        event={"symbol":self.symbol,"kind":kind,"cohort":window_cohort,
               "decision_us":ts,"date":day_of(ts-1),
               "entry_us":None,"entry_close":None,"exit_us":None,"exit_close":None,
               "status":"WAIT_ENTRY","gross_bps":None,"base_net_bps":None,"stress_net_bps":None}
        self.active[kind]=event
        self.decisions[(kind,window_cohort)]+=1

    def _process_matured_bar(self,close_us,price):
        for kind,event in list(self.active.items()):
            if event["status"]=="WAIT_ENTRY":
                gap=close_us-event["decision_us"]
                if gap<=0:continue
                if gap>WAIT:
                    self._done(event,"CENSORED_LATE_ENTRY");continue
                if cohort(close_us-1)!=event["cohort"]:
                    self._done(event,"CENSORED_CROSS_SPLIT");continue
                event["entry_us"]=close_us
                event["entry_close"]=price
                event["status"]="WAIT_EXIT"
            elif event["status"]=="WAIT_EXIT":
                gap=close_us-event["entry_us"]
                if gap<HOLD:continue
                if gap>HOLD+WAIT:
                    self._done(event,"CENSORED_LATE_EXIT");continue
                if cohort(close_us-1)!=event["cohort"]:
                    self._done(event,"CENSORED_CROSS_SPLIT");continue
                event["exit_us"]=close_us
                event["exit_close"]=price
                event["gross_bps"]=10000*(price/event["entry_close"]-1)
                event["base_net_bps"]=net_bps(event["entry_close"],price,2.0)
                event["stress_net_bps"]=net_bps(event["entry_close"],price,5.0)
                self._done(event,"MATURED_NOT_EXECUTED")

    def ingest(self,bar):
        start,close,quote,sells=bar
        if start<T0 or start>=TE:raise ValueError("BAR_OUTSIDE_90D_SCOPE")
        if self.last_start is None:
            if start!=T0:raise ValueError("FIRST_SECOND_MISSING")
        elif start!=self.last_start+US:
            raise ValueError("MISSING_DUPLICATE_OR_NONMONOTONE_1SEC_BAR")
        self.last_start=start
        close_us=start+US # candle becomes observable only after its 1s interval
        self._process_matured_bar(close_us,close)
        self.quote+=quote;self.sells+=sells;self.bucket_seen+=1
        self.source_1s_rows+=1
        self.days[day_of(start)]+=1
        if (close_us-T0)%WINDOW==0:
            if self.bucket_seen!=30:
                raise ValueError("INCOMPLETE_30_SECOND_SOURCE_WINDOW")
            if self.quote>0:
                if self.bins%4==3:self._decision("UNCONDITIONAL_BASELINE",close_us)
                if self.quote>=MIN_QUOTE and self.sells/self.quote>=MIN_SELL:
                    self._decision("SELL_FLOW",close_us)
            self.bins+=1
            self.quote=0.0;self.sells=0.0;self.bucket_seen=0

    def finish(self):
        if self.last_start!=TE-US:
            raise ValueError("MISSING_FINAL_1SEC_BAR")
        for event in list(self.active.values()):
            self._done(event,"CENSORED_ARCHIVE_END")
        return self.events

def bootstrap_lower(rows):
    daily=defaultdict(list)
    for event in rows:
        daily[event["date"]].append(event["stress_net_bps"])
    days=sorted(daily)
    if len(days)<20:return None
    sums=[sum(daily[d]) for d in days]
    counts=[len(daily[d]) for d in days]
    rng=random.Random(SEED)
    results=[]
    for _ in range(10000):
        ids=[rng.randrange(len(days)) for d in days]
        results.append(sum(sums[k] for k in ids)/sum(counts[k] for k in ids))
    results.sort()
    return results[500]

def summarize(events):
    groups={}
    for segment in ("TRAIN","VALIDATION","TEST"):
        groups[segment]={}
        for kind in ("SELL_FLOW","UNCONDITIONAL_BASELINE"):
            subset=[e for e in events if e["kind"]==kind and e["cohort"]==segment]
            matured=[e for e in subset if e["status"]=="MATURED_NOT_EXECUTED"]
            vals=[e["stress_net_bps"] for e in matured]
            bysymbol={}
            for symbol in S:
                x=[e["stress_net_bps"] for e in matured if e["symbol"]==symbol]
                bysymbol[symbol]={
                    "matured":len(x),"mean_stress_net_bps":statistics.mean(x) if x else None,
                    "positive_net":sum(v>0 for v in x)}
            groups[segment][kind]={
                "decisions":len(subset),"matured":len(matured),
                "censored":len(subset)-len(matured),
                "censor_reasons":dict(Counter(e["status"] for e in subset if e["status"]!="MATURED_NOT_EXECUTED")),
                "days":len(set(e["date"] for e in matured)),
                "mean_gross_bps":statistics.mean(e["gross_bps"] for e in matured) if matured else None,
                "mean_base_net_bps":statistics.mean(e["base_net_bps"] for e in matured) if matured else None,
                "mean_stress_net_bps":statistics.mean(vals) if vals else None,
                "median_stress_net_bps":statistics.median(vals) if vals else None,
                "positive_net":sum(v>0 for v in vals),
                "positive_net_rate":sum(v>0 for v in vals)/len(vals) if vals else None,
                "per_symbol":bysymbol
            }
    test=[e for e in events if e["cohort"]=="TEST" and e["kind"]=="SELL_FLOW" and e["status"]=="MATURED_NOT_EXECUTED"]
    days=len(set(e["date"] for e in test))
    adequate=len(test)>=200 and days>=20
    lower=bootstrap_lower(test) if adequate else None
    mean=groups["TEST"]["SELL_FLOW"]["mean_stress_net_bps"]
    baseline=groups["TEST"]["UNCONDITIONAL_BASELINE"]["mean_stress_net_bps"]
    relative=mean is not None and baseline is not None and mean>baseline
    gain=defaultdict(float)
    for e in test:gain[e["date"]]+=max(0,e["stress_net_bps"])
    pos_total=sum(gain.values())
    max_day=max(gain.values())/pos_total if pos_total>0 else None
    go=bool(adequate and mean>0 and lower is not None and lower>0 and max_day is not None and max_day<=0.2 and relative)
    if not adequate:status="INCONCLUSIVE_INSUFFICIENT_TEST_SAMPLE"
    elif go:status="GO_SCIENTIFIC_ONLY_NEW_FORWARD_REPLICATION_REQUIRED"
    else:status="NO_GO_ECONOMIC_1S_PRINT_PROXY"
    return {"study":"BINANCE006B_SPOT_1S_SELLFLOW_60S_OOS_V01",
            "status":status,"hypothetical_only":True,
            "actual_orders":0,"execution_fills":0,"live_trading_authorized":False,
            "L2_absorption_tested":False,
            "1s_close_not_executable_quote":True,
            "test_stress_lower_95_cluster_day_bps":lower,
            "test_primary_matured":len(test),"test_primary_days":days,
            "test_max_day_positive_gain_share":max_day,
            "test_beats_unconditional_baseline":relative,
            "scientific_limited_go":go,"groups":groups}
