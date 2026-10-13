#!/usr/bin/env python3
"""SHORT-REJECTION-SCALP-001: 1h bearish regime, 5m wick rejection, 1m proxy fills.
Historical-only, frozen parameters, fixed 8-alt cohort, no orders/private endpoints.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,tempfile,zipfile
from collections import Counter,defaultdict,deque,OrderedDict
from datetime import datetime,timezone
from pathlib import Path
from research.convex_multialt_4tf_20261013 import multialt_matrix as old
from research.convex_8alt_common_2023_25 import common_3yr as window

ASSETS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
FIVE=300_000;ONE=60_000;HOUR=3_600_000
FEE=.0008;STOP=.004;TARGET=.008;HOLD_MIN=90;EXPOSURE=.20
SLIPPAGES={"BASE":2,"STRESS":5,"DELAY_6H_BASE":2}
START=window.ECON_MS;END=window.END_MS
SOURCE="https://data.binance.vision/data/futures/um/monthly"

def hour_regime(one_hour):
    """At hour end, the hour close and its SMA200 are now observable."""
    from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
    build=src.load_parent()
    sm=build.__globals__["sma"]
    ordered=[one_hour[t] for t in sorted(one_hour)]
    closes=[b["close"] for b in ordered]
    ma=sm(closes,200)
    states={}
    for i,b in enumerate(ordered):
        valid=i>=223 and ma[i] is not None and ma[i-24] is not None
        states[b["t"]+HOUR]=bool(valid and b["close"]<ma[i] and ma[i]<ma[i-24])
    return states

def rejection_decisions(five,one_hour,start=START,end=END):
    """Signals on completed 5m; 1h used only after its entire hour has CLOSED."""
    states=hour_regime(one_hour)
    trail=deque(maxlen=12)
    signals=[]
    audit={"eligible_5m_bars":0,"bearish_hour_context_bars":0,"sweep_rejections":0,
           "signal_decisions":0,"first_10_decisions":[]}
    for t in sorted(five):
        b=five[t]
        if t>=start and t<end and len(trail)==12:
            audit["eligible_5m_bars"]+=1
            done=t+FIVE
            hour_done=(done//HOUR)*HOUR
            bearish=states.get(hour_done,False)
            if bearish:audit["bearish_hour_context_bars"]+=1
            highest=max(trail)
            candle_range=b["high"]-b["low"]
            wick=b["high"]-max(b["open"],b["close"])
            reject=bool(candle_range>0 and b["high"]>highest and b["close"]<highest and
                        b["close"]<b["open"] and wick>=.5*candle_range)
            if reject:audit["sweep_rejections"]+=1
            if bearish and reject:
                signals.append(done)
                audit["signal_decisions"]+=1
                if len(audit["first_10_decisions"])<10:
                    audit["first_10_decisions"].append(done)
        trail.append(b["high"])
    return signals,audit

def month(t):
    return datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m")

def month_bounds(ym):
    y,m=int(ym[:4]),int(ym[5:])
    nxt_y,nxt_m=(y+1,1) if m==12 else (y,m+1)
    a=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
    b=int(datetime(nxt_y,nxt_m,1,tzinfo=timezone.utc).timestamp()*1000)
    return a,b

class OfficialMinuteStore:
    """Official-checksummed monthly 1m archives, sparse access via local ZIP cache.
    No synthetic market reconstruction; monthly 1m/5m revision conflicts audited.
    """
    def __init__(self,symbol,five,tempdir,fetch_fn=None,*,allow_memory_cache=2):
        if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
        from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
        self.src=src
        self.symbol=symbol
        self.five=five
        self.tempdir=Path(tempdir)
        self.tempdir.mkdir(parents=True,exist_ok=True)
        self.fetch=fetch_fn or src.fetch
        self.loaded=OrderedDict()
        self.limit=allow_memory_cache
        self.manifest={}
        self.revision={}
        self.minute_count=0

    def read_month(self,ym):
        if ym<"2023-01" or ym>"2025-12":
            raise ValueError("ONE_MINUTE_OUTSIDE_FROZEN_ECONOMIC_WINDOW:"+ym)
        if ym in self.loaded:
            self.loaded.move_to_end(ym)
            return self.loaded[ym]
        url=f"{SOURCE}/klines/{self.symbol}/1m/{self.symbol}-1m-{ym}.zip"
        fp=self.tempdir/(self.symbol+"-"+ym+"-1m.zip")
        if not fp.exists():
            data=self.fetch(url,25_000_000)
            expected=self.fetch(url+".CHECKSUM",1200).decode("utf-8-sig").strip().split()[0].lower()
            digest=hashlib.sha256(data).hexdigest()
            if len(expected)!=64 or digest!=expected:raise ValueError("ONE_MIN_PUBLISHER_SHA256_FAIL:"+ym)
            fp.write_bytes(data)
        else:
            data=fp.read_bytes()
            digest=hashlib.sha256(data).hexdigest()
            if self.manifest[ym]["sha256"]!=digest:
                raise ValueError("LOCAL_ONE_MIN_CACHE_TAMPER")
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            csvs=[n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(csvs)!=1:raise ValueError("ONE_MIN_ARCHIVE_MEMBER_BAD:"+ym)
            raw=z.read(csvs[0]).decode("utf-8-sig")
        records=list(csv.reader(io.StringIO(raw)))
        bars=self.src.candles(records,ONE)
        a,b=month_bounds(ym)
        if len(bars)!=(b-a)//ONE or min(bars)!=a or max(bars)!=b-ONE or (
             len(bars)!=(max(bars)-min(bars))//ONE+1):
            raise ValueError("ONE_MINUTE_SOURCE_COVERAGE_GAP:"+ym+":"+str(len(bars)))
        self.minute_count+=len(bars) if ym not in self.manifest else 0
        if ym not in self.manifest:
            self.manifest[ym]={"symbol":self.symbol,"month":ym,"sha256":digest,"bytes":len(data),
                               "count":len(bars),"url":url}
            # Check every complete publisher 5m interval within this acquired month.
            count=0;first=[];maxdiff=0.;per_field=Counter()
            for t in range(a,b,FIVE):
                original=self.five.get(t)
                if original is None:raise ValueError("FIVE_MIN_SOURCE_GAP_WHEN_COMPARE_1M")
                mini=[bars[t+i*ONE] for i in range(5)]
                compared={"open":mini[0]["open"],"high":max(x["high"] for x in mini),
                          "low":min(x["low"] for x in mini),"close":mini[-1]["close"],
                          "volume":sum(x["volume"] for x in mini)}
                diff_fields=[]
                for key in ("open","high","low","close","volume"):
                    dv=abs(original[key]-compared[key])
                    if not math.isclose(original[key],compared[key],rel_tol=1e-6,abs_tol=1e-6):
                        per_field[key]+=1;maxdiff=max(maxdiff,dv);diff_fields.append(key)
                if diff_fields:
                    count+=1
                    if len(first)<5:first.append({"t":t,"fields":diff_fields})
            self.revision[ym]={"5m_intervals_checked":(b-a)//FIVE,
                               "bars_with_publisher_1m_5m_conflict":count,
                               "field_mismatch_counts":dict(per_field),
                               "max_absolute_difference_any_field":maxdiff,
                               "first_5":first}
            print("SCALP_1M_SOURCE_OK",self.symbol,ym,len(bars),
                  "revision_conflicts",count,flush=True)
        self.loaded[ym]=bars
        if len(self.loaded)>self.limit:self.loaded.popitem(last=False)
        return bars

    def get(self,t):
        if t<START or t>=END:raise ValueError("ONE_MIN_PRICE_OUTSIDE_VALID_TIME")
        b=self.read_month(month(t)).get(t)
        if b is None:raise ValueError("MISSING_ONE_MINUTE_IN_ARCHIVE")
        return b

def close_trace(decision_ms,minute_store,funding,equity,slip_bps,*,expiry=END):
    """Independent trade, entry at completed B time+ONE; no post-T or undated fill."""
    entry_t=decision_ms+ONE
    if entry_t>=expiry:return None
    slip=slip_bps/10000.
    entry_raw=minute_store.get(entry_t)["open"]
    entry=entry_raw*(1-slip)
    qty=equity*EXPOSURE/entry
    entryfee=entry*qty*FEE
    cash=equity-entryfee
    stop=entry*(1+STOP)
    target=entry*(1-TARGET)
    funding_cash=0.
    peak_mark=equity
    worst_dd=0.
    closed=None
    last_mark=None
    last_close=entry
    for i in range(HOLD_MIN):
        t=entry_t+i*ONE
        if t>=expiry:break
        b=minute_store.get(t)
        if i and t in funding:
            # Actual historical funding rate at settlement, inexact market open proxy.
            delta=qty*b["open"]*funding[t]
            funding_cash+=delta
            cash+=delta
        if b["open"]>=stop:
            raw=b["open"];reason="STOP_GAP"
        elif b["open"]<=target:
            raw=b["open"];reason="TARGET_GAP"
        elif b["high"]>=stop:
            raw=stop;reason="STOP_FIRST"
        elif b["low"]<=target:
            raw=target;reason="TARGET"
        elif i==HOLD_MIN-1:
            raw=b["close"];reason="TIME_90M"
        else:
            raw=None;reason=None
        if raw is not None:
            exit_price=raw*(1+slip)
            fee=qty*exit_price*FEE
            pnl=qty*(entry-exit_price)
            cash+=pnl-fee
            current_mark=cash
            peak_mark=max(peak_mark,current_mark)
            worst_dd=min(worst_dd,current_mark/peak_mark-1)
            closed={"direction":"SHORT","entry_t":entry_t,"exit_t":t+ONE,
                    "entry_price":entry,"exit_price":exit_price,
                    "qty":qty,"price_pnl_usdt":pnl,
                    "entry_fee_usdt":entryfee,"exit_fee_usdt":fee,
                    "funding_usdt":funding_cash,
                    "net_pnl_usdt":pnl-entryfee-fee+funding_cash,
                    "exit_reason":reason,
                    "exit_year":datetime.fromtimestamp((t+ONE-1)/1000,timezone.utc).year,
                    "exit_notional_return_pct":(pnl-entryfee-fee+funding_cash)/(qty*entry)*100}
            break
        # Adverse unrealized valuation at 1m HIGH; estimated exit slip/fee.
        worst_buy=qty*b["high"]*(1+slip)
        high_mark=cash+qty*entry-worst_buy-worst_buy*FEE
        close_buy=qty*b["close"]*(1+slip)
        close_mark=cash+qty*entry-close_buy-close_buy*FEE
        peak_mark=max(peak_mark,close_mark)
        worst_dd=min(worst_dd,high_mark/peak_mark-1)
        last_close=b["close"]
        last_mark=close_mark
    if closed:
        return {"closed":closed,"after_cash":cash,
                "after_mark":cash,"next_free":closed["exit_t"],
                "adverse_1m_dd":worst_dd}
    if last_mark is None:raise ValueError("ENTRY_WITH_NO_AVAILABLE_1M_BAR")
    return {"closed":None,"after_cash":cash,"after_mark":last_mark,
            "next_free":expiry,"adverse_1m_dd":worst_dd}

def replay(candidates,minute_store,funding,slip_bps,*,delay_hours=0,start=START,end=END):
    """All candidates supplied before economic outcomes; placebo merely adds 6h."""
    if slip_bps not in (2,5) or delay_hours not in (0,6):
        raise ValueError("NOT_PREREGISTERED_SCENARIO")
    cash=10000.
    closed=[]
    skip=0;unentered_end=0;entries=0;open_terminal=None
    last_free=start
    max_closed_equity=10000.
    dd_closed=0.
    dd_1m=0.
    pending=None
    seen=0
    for original_decision in candidates:
        signal_at=original_decision+delay_hours*HOUR
        if signal_at<start or signal_at>=end:continue
        seen+=1
        entry_at=signal_at+ONE
        if entry_at>=end:
            unentered_end+=1;continue
        if signal_at<=last_free and entries>0:
            skip+=1;continue
        if open_terminal is not None:
            skip+=1;continue
        tr=close_trace(signal_at,minute_store,funding,cash,slip_bps,expiry=end)
        if tr is None:unentered_end+=1;continue
        entries+=1
        cash=tr["after_cash"]
        dd_1m=min(dd_1m,tr["adverse_1m_dd"])
        if tr["closed"] is None:
            open_terminal=tr
            last_free=end
        else:
            closed.append(tr["closed"])
            last_free=tr["next_free"]
            max_closed_equity=max(max_closed_equity,cash)
            dd_closed=min(dd_closed,cash/max_closed_equity-1)
    marked=open_terminal["after_mark"] if open_terminal is not None else cash
    wins=[x["net_pnl_usdt"] for x in closed if x["net_pnl_usdt"]>0]
    negatives=[-x["net_pnl_usdt"] for x in closed if x["net_pnl_usdt"]<=0]
    positive=sum(wins);negative=sum(negatives)
    total_closed=sum(x["net_pnl_usdt"] for x in closed)
    top3=sum(sorted(wins,reverse=True)[:3])
    annual=defaultdict(float);reasons=Counter()
    streak=max_streak=0
    for x in closed:
        annual[str(x["exit_year"])]+=x["net_pnl_usdt"]
        reasons[x["exit_reason"]]+=1
        streak=0 if x["net_pnl_usdt"]>0 else streak+1
        max_streak=max(max_streak,streak)
    out={"status":"RETROSPECTIVE_1M_SHORT_SCALP_MODEL_ONLY",
         "direction":"SHORT","holding_cap_minutes":HOLD_MIN,
         "delay_control_hours":delay_hours,
         "slippage_bps_side":slip_bps,
         "capital_initial_usdt":10000.,
         "cash_end_usdt":cash,"marked_end_usdt":marked,
         "marked_return_pct":(marked/10000-1)*100,
         "closed_cash_return_pct":(cash/10000-1)*100,
         "closed_trades":len(closed),"wins":len(wins),
         "win_rate_pct":100*len(wins)/len(closed) if closed else None,
         "profit_factor":positive/negative if negative else None,
         "max_closed_dd_pct":dd_closed*100,
         "worst_1m_high_mark_dd_trade_pct":dd_1m*100,
         "fees_closed_usdt":sum(x["entry_fee_usdt"]+x["exit_fee_usdt"] for x in closed),
         "funding_closed_usdt":sum(x["funding_usdt"] for x in closed),
         "price_pnl_closed_usdt":sum(x["price_pnl_usdt"] for x in closed),
         "closed_net_usdt":total_closed,
         "winner_top3_share_pct":(top3/positive*100 if positive else None),
         "closed_net_minus_top3_static_usdt":total_closed-top3,
         "positive_exit_years_count":sum(annual.get(str(y),0)>0 for y in (2023,2024,2025)),
         "annual_closed_pnl_usdt":dict(annual),
         "exit_reasons":dict(reasons),"max_loss_streak":max_streak,
         "entry_count":entries,"signals_in_period":seen,
         "skipped_while_occupied":skip,"too_late_to_enter":unentered_end,
         "has_open_end_position":open_terminal is not None,
         "public_price_proxy_not_real_fills":True,"trades":closed}
    if len(closed)+(1 if open_terminal else 0)!=entries:
        raise AssertionError("ENTRY_CLOSE_COUNT_IDENTITY_FAIL")
    if abs(cash-10000.-total_closed)>0.00001 and not open_terminal:
        raise AssertionError("CLOSED_PNL_CASH_IDENTITY_FAIL")
    return out

def study(symbol,outpath):
    window.apply_locked_3year_window()
    if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
    five,one,funding,manifest=old.fetch_all(symbol)
    hours=old.base.resample(five,HOUR)
    parity=old.base.verify_one_hour_parity(hours,one)
    decisions,audit=rejection_decisions(five,{b["t"]:b for b in hours})
    with tempfile.TemporaryDirectory(prefix="crypto_short_scalp_source_") as directory:
        store=OfficialMinuteStore(symbol,five,directory)
        models={}
        for label,bps,delay in (("BASE",2,0),("STRESS",5,0),("DELAY_6H_BASE",2,6)):
            m=replay(decisions,store,funding,bps,delay_hours=delay)
            trade_rows=m.pop("trades")
            if trade_rows:
                dest=outpath/(label+"_TRADES.csv")
                with dest.open("w",newline="",encoding="utf8") as h:
                    writer=csv.DictWriter(h,fieldnames=trade_rows[0].keys())
                    writer.writeheader();writer.writerows(trade_rows)
            models[label]=m
            print("SCALP_MODEL",symbol,label,
                  "net",round(m["marked_return_pct"],5),
                  "closed",m["closed_trades"],"PF",m["profit_factor"],flush=True)
        return {"status":"HISTORICAL_SCALP_COMPLETED_NO_OOS","symbol":symbol,
                "model":models,"signal_audit":audit,
                "official_5m_market_checksum_manifest":manifest,
                "official_1m_checksum_manifest":list(store.manifest.values()),
                "one_minute_vs_five_minute_revision_audit":store.revision,
                "one_minute_loaded_months":len(store.manifest),
                "official_1h_source_audit":parity,
                "source_counts":{"5m":len(five),"1h":len(one),"funding":len(funding)},
                "source_revision_qualified":any(v["bars_with_publisher_1m_5m_conflict"]>0 for v in store.revision.values()),
                "strategy":"SHORT_REJECTION_SCALP_001",
                "independent_oos":False,"real_trading":False,"trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",choices=ASSETS,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    report={"symbol":a.symbol,"status":"SOURCE_OR_MODEL_BLOCKED",
            "strategy":"SHORT_REJECTION_SCALP_001",
            "freeze":"PRE_OUTCOME_FREEZE_2026-10-13.md",
            "source_scope":"BINANCE_PUBLIC_USDM_2023_2025",
            "independent_oos":False,"trading_authority":"NONE"}
    try:
        report=study(a.symbol,a.output_dir)
    except Exception as ex:
        report["error"]=type(ex).__name__+":"+str(ex)
    (a.output_dir/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("SCALP_FINAL",json.dumps({"symbol":a.symbol,"status":report["status"],
        "error":report.get("error"),
        "signal_audit":report.get("signal_audit"),
        "one_minute_loaded_months":report.get("one_minute_loaded_months"),
        "source_revision_qualified":report.get("source_revision_qualified"),
        "model":{k:{"net":v["marked_return_pct"],"trades":v["closed_trades"],
                    "PF":v["profit_factor"],"DD":v["max_closed_dd_pct"],
                    "yearly":v["annual_closed_pnl_usdt"],"funding":v["funding_closed_usdt"]}
                 for k,v in report.get("model",{}).items()}},sort_keys=True),flush=True)
    if report["status"]!="HISTORICAL_SCALP_COMPLETED_NO_OOS":raise SystemExit(2)
if __name__=="__main__":
    main()
