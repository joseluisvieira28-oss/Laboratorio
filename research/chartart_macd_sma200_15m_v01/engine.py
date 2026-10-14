#!/usr/bin/env python3
"""Research-only fixed MACD-SMA200 V1.0 signal interpretation. NOT exact TradingView Pine v2 emulator.
Requires previously committed PRE_OUTCOME_FREEZE_2026-10-14.md; never accesses private accounts.
"""
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import pathlib
import sys
import urllib.request
import zipfile

STEP = 900000
DAY = 86400000
UTC = dt.timezone.utc
WARM = int(dt.datetime(2021, 1, 1, tzinfo=UTC).timestamp()*1000)
START = int(dt.datetime(2022, 1, 1, tzinfo=UTC).timestamp()*1000)
END = int(dt.datetime(2026, 1, 1, tzinfo=UTC).timestamp()*1000)
HIST_BASE = "https://data.binance.vision/data/futures/um/monthly"
FEE = 0.0008
COSTS = {"BASE":0.0002,"STRESS":0.0005}
ARMS = ("E0_ORIGINAL_SIGNALS","E1_PROTECTED_4PCT_7DAY")


class SourceBlocked(Exception):
    pass


def ms_timestamp(s):
    x = int(s)
    if x >= 10**15:
        if x % 1000 != 0:
            raise SourceBlocked("microsecond timestamp not on exact ms")
        x //= 1000
    if not (1_400_000_000_000 < x < 1_900_000_000_000):
        raise SourceBlocked("timestamp outside sane epoch: "+str(s))
    return x


def months(start,stop):
    for year in range(start, stop+1):
        for month in range(1,13):
            yield year,month


def fetch_publisher_zip(folder, filename, receipts):
    root=f"{HIST_BASE}/{folder}/{filename}"
    try:
        with urllib.request.urlopen(urllib.request.Request(root+".CHECKSUM",headers={"User-Agent":"CryptoLab-chartart-source-v01"}),timeout=45) as h:
            expected=h.read(400).decode("ascii").split()[0].lower()
        if len(expected)!=64 or not all(x in "0123456789abcdef" for x in expected):
            raise SourceBlocked("bad checksum metadata "+filename)
        with urllib.request.urlopen(urllib.request.Request(root,headers={"User-Agent":"CryptoLab-chartart-source-v01"}),timeout=50) as h:
            raw=h.read(30_000_001)
        if len(raw)>30_000_000 or hashlib.sha256(raw).hexdigest()!=expected:
            raise SourceBlocked("missing/wrong publisher sha256 "+filename)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members=[n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(members)!=1 or not members[0].endswith(filename.replace(".zip",".csv")):
                raise SourceBlocked("unexpected archive contents "+filename)
            decoded=z.read(members[0]).decode("utf-8-sig")
        rows=list(csv.reader(io.StringIO(decoded)))
        receipts.append({"archive":filename, "sha256":expected, "rows":len(rows)})
        return rows
    except (OSError, UnicodeError, zipfile.BadZipFile, ValueError, IndexError) as exc:
        raise SourceBlocked("PUBLIC_ARCHIVE_FAIL "+filename+": "+str(exc)[:260]) from exc


def read_source():
    receipt=[]
    candles=[]
    for y,m in months(2021,2025):
        name=f"BTCUSDT-15m-{y}-{m:02d}.zip"
        rows=fetch_publisher_zip("klines/BTCUSDT/15m",name,receipt)
        if not rows:raise SourceBlocked("empty market archive "+name)
        for r in rows:
            if not r or not r[0].strip().isdigit():
                continue
            if len(r)<5:raise SourceBlocked("short candle record "+name)
            stamp=ms_timestamp(r[0])
            o,hi,lo,c=(float(r[j]) for j in [1,2,3,4])
            if not all(math.isfinite(v) for v in [o,hi,lo,c]) or not (0<lo<=min(o,c)<=max(o,c)<=hi):
                raise SourceBlocked("malformed candle "+name)
            candles.append((stamp,o,hi,lo,c))
    if not candles or candles[0][0]!=WARM or candles[-1][0]!=END-STEP:
        raise SourceBlocked("not exact complete 2021-25 UTC 15m archive")
    if len(candles)!=(END-WARM)//STEP:
        raise SourceBlocked("wrong 15m archive number of bars "+str(len(candles)))
    for i,r in enumerate(candles):
        if r[0]!=WARM+i*STEP:
            raise SourceBlocked("hole/duplicate/not ordered in 15m market at "+str(i))
    funding={}
    jitter_events=0;max_jitter=0;mark_count=0
    for y,m in months(2022,2025):
        name=f"BTCUSDT-fundingRate-{y}-{m:02d}.zip"
        rows=fetch_publisher_zip("fundingRate/BTCUSDT",name,receipt)
        if not rows:raise SourceBlocked("empty official funding archive "+name)
        head=[c.strip().lower() for c in rows[0]]
        is_header=not rows[0][0].strip().isdigit()
        if is_header:
            ti=next((i for i,h in enumerate(head) if h in ("calc_time","fundingtime","funding_time")),None)
            ri=next((i for i,h in enumerate(head) if h in ("last_funding_rate","fundingrate","funding_rate")),None)
            mi=next((i for i,h in enumerate(head) if h in ("markprice","mark_price")),None)
            if ti is None or ri is None:raise SourceBlocked("unknown funding header "+name)
        else:
            ti,ri,mi=0,2,None
        for r in rows[1:] if is_header else rows:
            if not r or not r[ti].strip().isdigit():continue
            raw_t=ms_timestamp(r[ti])
            jitter=raw_t%STEP
            if jitter>=1000:raise SourceBlocked("funding timestamp not on 15m bound +/- <1000ms "+name)
            when=raw_t-jitter
            if when<START or when>=END or when in funding:
                raise SourceBlocked("funding outside frozen window or duplicate "+name)
            rate=float(r[ri])
            if not math.isfinite(rate) or abs(rate)>0.1:raise SourceBlocked("invalid funding rate "+name)
            mark=float(r[mi]) if mi is not None and r[mi] else None
            if mark is not None and (not math.isfinite(mark) or mark<=0):
                raise SourceBlocked("invalid mark "+name)
            funding[when]=(rate,mark)
            jitter_events += int(jitter>0)
            max_jitter=max(max_jitter,jitter)
            mark_count+=int(mark is not None)
    if not 4000<=len(funding)<=5000:
        raise SourceBlocked("incomplete funding event count "+str(len(funding)))
    if not all(START<=t<END for t in funding):raise SourceBlocked("unexpected funding date")
    provenance={"sample":"BTCUSDT USD-M futures 15m UTC 2022-25, warmup 2021","market_bars":len(candles),
                "market_files":60,"funding_files":48,"funding_events":len(funding),
                "funding_time_subsecond_normalized":jitter_events,"max_positive_jitter_ms":max_jitter,
                "exact_mark_events":mark_count,"source_receipts":receipt}
    return candles,funding,provenance


def rolling_sma(source, n):
    result=[None]*len(source);s=0.0
    for i,price in enumerate(source):
        if price is None:continue
        s+=price
        if i>=n:s-=source[i-n]
        if i>=n-1:result[i]=s/n
    return result


def compute_signals(candles):
    closes=[bar[4] for bar in candles]
    f=rolling_sma(closes,12)
    s=rolling_sma(closes,26)
    baseline=rolling_sma(closes,200)
    macd=[f[i]-s[i] if f[i] is not None and s[i] is not None else None for i in range(len(closes))]
    signal=[None]*len(closes)
    # SMA9 of MACD initialized only after 26 complete closes, no zero-padding.
    for i in range(33,len(closes)):
        signal[i]=sum(macd[i-8:i+1])/9.0
    hist=[macd[i]-signal[i] if signal[i] is not None else None for i in range(len(closes))]
    pending={}
    for i in range(200,len(closes)-1):
        if candles[i][0]+STEP >= END:break
        # A historical bar (index i) is confirmed at i+1 bar OPEN.
        prior,current=hist[i-1],hist[i]
        if prior is None or current is None:continue
        long=(prior<=0 and current>0 and macd[i]>0 and f[i]>s[i] and closes[i-26]>baseline[i])
        short=(prior>=0 and current<0 and macd[i]<0 and f[i]<s[i] and closes[i-26]<baseline[i])
        if long and short:raise AssertionError("mutually exclusive MACD cross")
        if long or short:pending[candles[i+1][0]]=1 if long else -1
    return pending


def simulate(candles, funding, orders, arm, slip):
    paper=10000.0
    pos=None;trades=[]
    hist_marks=[];fund_tot=0.0;paid_fees=0.0;signals=0;gap_stops=0
    def fillprice(price,side):
        return price*(1+slip if side==1 else 1-slip)
    def close_pos(ts,raw,reason,exit_side):
        nonlocal pos,paper,paid_fees
        px=fillprice(raw,exit_side)
        fee=abs(px*pos["qty"])*FEE
        gross=pos["qty"]*pos["side"]*(px-pos["entry"])
        paper+=gross-fee;paid_fees+=fee
        net=gross-pos["entry_fee"]-fee+pos["funding"]
        tr={"opened":pos["start"],"exit":ts,"side":pos["side"],"qty":pos["qty"],"entry":pos["entry"],"exit_px":px,
            "gross_trade":gross,"entry_fee":pos["entry_fee"],"exit_fee":fee,"funding":pos["funding"],
            "net":net,"reason":reason,"bars_held":round((ts-pos["start"])/STEP),"notional_at_entry":pos["entry"]*pos["qty"]}
        trades.append(tr);pos=None
    for ts,o,high,low,c in candles:
        if ts<START:continue
        if pos is not None and ts in funding:
            rate,mark=funding[ts]
            price=o if mark is None else mark
            flow=-pos["side"]*pos["qty"]*price*rate
            paper+=flow;fund_tot+=flow;pos["funding"]+=flow
        signal=orders.get(ts,0)
        if signal:signals+=1
        did_exit=False
        if pos is not None and signal and signal!=pos["side"]:
            close_pos(ts,o,"OPPOSITE_SIGNAL",exit_side=-1 if pos["side"]==1 else 1)
            did_exit=True
        if pos is not None and arm=="E1_PROTECTED_4PCT_7DAY" and ts-pos["start"]>=7*DAY:
            close_pos(ts,o,"TIME_7D",exit_side=-1 if pos["side"]==1 else 1)
            did_exit=True
        if signal and pos is None:
            # Same timestamp close/reverse is allowed if opposite confirmed signal.
            opening=fillprice(o,signal)
            if paper>0:
                notional=paper*.10
                qty=notional/opening
                fee=qty*opening*FEE
                paper-=fee;paid_fees+=fee
                pos={"start":ts,"entry":opening,"side":signal,"qty":qty,"entry_fee":fee,"funding":0.0,
                     "stop":opening*(0.96 if signal==1 else 1.04)}
        if pos is not None and arm=="E1_PROTECTED_4PCT_7DAY":
            touched=low<=pos["stop"] if pos["side"]==1 else high>=pos["stop"]
            if touched:
                if pos["side"]==1:
                    raw=min(o,pos["stop"])
                    if o<pos["stop"]:gap_stops+=1
                    close_pos(ts,raw,"STOP_4PCT",exit_side=-1)
                else:
                    raw=max(o,pos["stop"])
                    if o>pos["stop"]:gap_stops+=1
                    close_pos(ts,raw,"STOP_4PCT",exit_side=1)
        floating=pos["qty"]*pos["side"]*(c-pos["entry"]) if pos else 0.0
        hist_marks.append((ts,paper+floating))
    if not hist_marks:raise SourceBlocked("no history measured")
    peak=10000.0;maxdd=0.0
    for t,v in hist_marks:
        peak=max(peak,v)
        maxdd=min(maxdd,v/peak-1)
    winning=[t["net"] for t in trades if t["net"]>0]
    losers=[t["net"] for t in trades if t["net"]<0]
    plus=sum(winning);minus=-sum(losers)
    years={str(y):{"net":0.0,"trades":0} for y in range(2022,2026)}
    sides={"LONG":{"trades":0,"net":0.0},"SHORT":{"trades":0,"net":0.0}}
    for tr in trades:
        y=str(dt.datetime.fromtimestamp(tr["exit"]/1000,UTC).year)
        years[y]["net"]+=tr["net"]
        years[y]["trades"]+=1
        key="LONG" if tr["side"]==1 else "SHORT"
        sides[key]["net"]+=tr["net"];sides[key]["trades"]+=1
    terminal=hist_marks[-1][1]
    # Ledger invariant for realized net + open already accrued fees/funding (not double count).
    closed=sum(t["net"] for t in trades)
    open_net=(pos["qty"]*pos["side"]*(candles[-1][4]-pos["entry"])-pos["entry_fee"]+pos["funding"]) if pos else 0.0
    if abs(10000.0+closed+open_net-terminal)>0.00001:
        raise AssertionError("cash/PnL ledger mismatch")
    top3=sum(sorted(winning,reverse=True)[:3])
    return {"arm":arm,"scenario":next(k for k,v in COSTS.items() if v==slip),
            "signal_count":signals,"closed":len(trades),"wins":len(winning),"losses":len(losers),
            "pf":plus/minus if minus>0 else None,"closed_realized_net":closed,
            "terminal_equity":terminal,"terminal_return_pct":100*(terminal/10000-1),
            "max_15m_mtm_dd_pct":100*maxdd,"funding_total":fund_tot,"fees_paid":paid_fees,
            "open_position":pos is not None,"open_mark_net":open_net,"years":years,"sides":sides,
            "top3_net_winners":top3,"net_excluding_top3_static":closed-top3,
            "stop_gap_worse_fills":gap_stops},trades


def evaluate(out):
    b=out["BASE"]["E1_PROTECTED_4PCT_7DAY"];s=out["STRESS"]["E1_PROTECTED_4PCT_7DAY"]
    control=out["BASE"]["E0_ORIGINAL_SIGNALS"]
    def ept(z):return z["closed_realized_net"]/z["closed"] if z["closed"] else -float("inf")
    conditions={
        "100_trades":b["closed"]>=100,
        "15_each_year":all(b["years"][str(y)]["trades"]>=15 for y in range(2022,2026)),
        "both_terminal_positive":b["terminal_return_pct"]>0 and s["terminal_return_pct"]>0,
        "pf_minima":b["pf"] is not None and s["pf"] is not None and b["pf"]>1.15 and s["pf"]>1.05,
        "3_of_4_net_years_base_and_stress":sum(b["years"][str(y)]["net"]>0 and s["years"][str(y)]["net"]>0 for y in range(2022,2026))>=3,
        "max_dd_lt_20pct":b["max_15m_mtm_dd_pct"]>=-20,
        "tail_resilience":b["net_excluding_top3_static"]>0,
        "incremental_over_E0":ept(b)>ept(control) and (
             b["terminal_return_pct"]>control["terminal_return_pct"] or (
             b["terminal_return_pct"]>0 and abs(b["max_15m_mtm_dd_pct"])<=.7*abs(control["max_15m_mtm_dd_pct"])))
    }
    return {"criteria":conditions,"verdict":"DESCRIPTIVE_HISTORICAL_CANDIDACY_NOT_OOS" if all(conditions.values()) else "NO_HISTORICAL_CANDIDACY","live_authority":"NONE"}


def main():
    dest=pathlib.Path(os.environ.get("CHARTART_OUT","chartart_rnd_outputs"))
    dest.mkdir(parents=True,exist_ok=True)
    try:
        candles,funding,source=read_source()
        (dest/"source_sha256_receipt.json").write_text(json.dumps(source,indent=2))
        instructions=compute_signals(candles)
        all_results={}; all_trades=[]
        for scenario,slip in COSTS.items():
            all_results[scenario]={}
            for arm in ARMS:
                result,ledger=simulate(candles,funding,instructions,arm,slip)
                all_results[scenario][arm]=result
                for trade in ledger:
                    trade["scenario"]=scenario
                    trade["arm"]=arm
                all_trades.extend(ledger)
        result={"state":"HISTORICAL_RESEARCH_COMPLETE","scopes":"2022-2025 descriptive, 2026 never fetched",
                "economic_verdict":evaluate(all_results),"models":all_results,"live_authority":"NONE",
                "limitations":"Python marketable-next-open Pine-v2 interpretation, not TradingView exact replay; funding 15m OPEN proxy; no executable BBO/real stops"}
        (dest/"chartart_protected_child_results.json").write_text(json.dumps(result,indent=2,allow_nan=False))
        with (dest/"chartart_protected_child_trades.csv").open("w",newline="") as fh:
            if all_trades:
                w=csv.DictWriter(fh,fieldnames=list(all_trades[0]))
                w.writeheader();w.writerows(all_trades)
        print("SCIENTIFIC_RESULT="+json.dumps({"state":result["state"],
              "verdict":result["economic_verdict"],
              "models":{q:{k:{f:r[f] for f in ("closed","pf","terminal_return_pct","max_15m_mtm_dd_pct","net_excluding_top3_static")} for k,r in arms.items()} for q,arms in all_results.items()}},allow_nan=False))
        return 0
    except (SourceBlocked,ValueError,OSError,AssertionError,ZeroDivisionError) as e:
        receipt={"state":"SOURCE_OR_ENGINE_BLOCKED","error":str(e),"live_authority":"NONE"}
        (dest/"fail_closed.json").write_text(json.dumps(receipt,indent=2))
        print("SOURCE_FAILED="+json.dumps(receipt))
        return 2


if __name__=="__main__":
    sys.exit(main())
