#!/usr/bin/env python3
"""Frozen BINANCE-004 hypothesis applied prospectively via raw receipt-time journal.
No orders; best bid/ask static-book hypothetical forward quotes are NOT fills.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import statistics
import sys
from decimal import Decimal as D, getcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent/"binance_diamante003"
sys.path.insert(0,str(ROOT))
from book_core import SYMBOLS,LocalBook,replay,event_validation

getcontext().prec=34
OUT=Path("binance004-evidence")
WINDOW_NS=30_000_000_000
CAPTURE_NS=480_000_000_000
LATEST_DECISION_NS=360_000_000_000
HORIZON_NS=60_000_000_000
COOLDOWN_NS=120_000_000_000
MAX_ENTRY_WAIT_NS=3_000_000_000
MAX_EXIT_WAIT_NS=3_000_000_000
MAX_BOOK_AGE_NS=2_000_000_000
MAX_EVENT_AGE_MS=3000
MAX_EVENT_FUTURE_MS=1000
MIN_QUOTE=D("5000")
SELL_THRESHOLD=D("0.65")
DEPTH_PERSIST_MIN=D("0.80")
MID_FLOOR_BPS=D("-3")
NOTIONALS=(D("100"),D("1000"))
FEE_BPS=D("10")
SCENARIOS={"BASE_2BPS":D("2"),"STRESS_5BPS":D("5")}
MIN_EVENTS_FOR_GO=200
MIN_DAYS_FOR_GO=20

def visible_mid_bid10(book):
    if book.status!="SYNCED" or not book.bids or not book.asks:
        return None
    bid=max(book.bids);ask=min(book.asks)
    if bid>=ask:raise ValueError("INVALID_BOOK_CROSS")
    mid=(bid+ask)/2
    bottom=mid*(D(1)-D("0.001"))
    depth=sum((p*q for p,q in book.bids.items() if p>=bottom and p<=mid),D(0))
    return {"mid":mid,"bid_depth_10bps_quote":depth}

def buy_quote(book,notional):
    left=notional;units=D(0)
    for price,qty in sorted(book.asks.items()):
        take=min(left,price*qty)
        units+=take/price
        left-=take
        if left<=D("0.00000000000000000001"):
            return units
    return None

def sell_base(book,units):
    left=units;proceeds=D(0)
    for price,qty in sorted(book.bids.items(),reverse=True):
        take=min(left,qty)
        proceeds+=take*price
        left-=take
        if left<=D("0.00000000000000000001"):
            return proceeds
    return None

def bps_move(before,after):
    return (after/before-D(1))*D(10000)

def utc_date(utc_ns):
    return dt.datetime.fromtimestamp(utc_ns/1e9,tz=dt.timezone.utc).strftime("%Y-%m-%d")

def raw_age_ok(raw_event,receipt_utc_ns):
    receipt_ms=receipt_utc_ns//1_000_000
    times=[raw_event.get("E")]
    if raw_event.get("e")=="aggTrade":times.append(raw_event.get("T"))
    if any(type(t) is not int or not -MAX_EVENT_FUTURE_MS<=receipt_ms-t<=MAX_EVENT_AGE_MS for t in times):
        return False
    return True

class ProspectiveStudy:
    def __init__(self):
        self.books={s:LocalBook(s) for s in SYMBOLS}
        self.last_depth_ns={s:None for s in SYMBOLS}
        self.t0_ns=None
        self.idx=0
        self.last_seen_ns=None
        self.buckets={}
        self.windows=[]
        self.events=[]
        self.last_decision={}
        self.clock_errors=0
        self.capture_frames=0

    def _book_snapshot(self,s):
        return visible_mid_bid10(self.books[s])

    def _new_bucket(self,s,at_ns):
        snap=self._book_snapshot(s)
        depth_ns=self.last_depth_ns[s]
        return {
            "start_ns":at_ns,
            "mid_start":snap["mid"] if snap else None,
            "depth_start":snap["bid_depth_10bps_quote"] if snap else None,
            "source_start_fresh":depth_ns is not None and 0<=at_ns-depth_ns<=MAX_BOOK_AGE_NS,
            "sell_quote":D(0),"buy_quote":D(0),
            "depth_updates":0,"invalid_clock":0
        }

    def _start(self,at_ns):
        self.t0_ns=at_ns
        self.buckets={s:self._new_bucket(s,at_ns) for s in SYMBOLS}

    def _window_close(self,boundary_ns):
        idx=self.idx
        allowed=(idx+1)*WINDOW_NS<=LATEST_DECISION_NS
        for s in SYMBOLS:
            item=self.buckets[s]
            end=self._book_snapshot(s)
            last=self.last_depth_ns[s]
            fresh_end=(last is not None and 0<=boundary_ns-last<=MAX_BOOK_AGE_NS)
            fresh=item["source_start_fresh"] and fresh_end and item["depth_updates"]>=1
            total=item["sell_quote"]+item["buy_quote"]
            share=item["sell_quote"]/total if total>0 else None
            d0=item["depth_start"];d1=end["bid_depth_10bps_quote"] if end else None
            m0=item["mid_start"];m1=end["mid"] if end else None
            ratio=d1/d0 if d0 is not None and d1 is not None and d0>0 else None
            move=bps_move(m0,m1) if m0 is not None and m1 is not None else None
            valid=(fresh and item["invalid_clock"]==0 and self.books[s].status=="SYNCED"
                   and m0 is not None and m1 is not None and d0 is not None
                   and d0>0 and d1 is not None and d1>0)
            pressure=valid and total>=MIN_QUOTE and share is not None and share>=SELL_THRESHOLD
            resilient=pressure and ratio is not None and ratio>=DEPTH_PERSIST_MIN and move is not None and move>=MID_FLOOR_BPS
            window={
                "symbol":s,"index":idx,"end_t0_seconds":(idx+1)*30,
                "sell_quote":str(item["sell_quote"]),
                "buy_quote":str(item["buy_quote"]),
                "sell_share":str(share) if share is not None else None,
                "bid_depth_start":str(d0) if d0 is not None else None,
                "bid_depth_end":str(d1) if d1 is not None else None,
                "bid_depth_ratio":str(ratio) if ratio is not None else None,
                "mid_change_bps":str(move) if move is not None else None,
                "depth_frames":item["depth_updates"],
                "clock_invalid_events":item["invalid_clock"],
                "valid":bool(valid),"pressure":bool(pressure),
                "resilience_proxy":bool(resilient),
                "allowed_before_cutoff":allowed,
                "window_decision_mono_ns":boundary_ns
            }
            self.windows.append(window)
            kinds=[]
            if allowed and pressure:kinds.append("PRIMARY" if resilient else "FLOW_ONLY_CONTROL")
            if allowed and valid and idx%4==3:kinds.append("UNCONDITIONAL_BASELINE")
            for kind in kinds:
                prior=self.last_decision.get((s,kind))
                if prior is not None and boundary_ns-prior<COOLDOWN_NS:
                    window.setdefault("cooldown_skipped",[]).append(kind)
                    continue
                self.last_decision[(s,kind)]=boundary_ns
                self.events.append({
                    "symbol":s,"kind":kind,"window_index":idx,
                    "decision_mono_ns":boundary_ns,
                    "decision_t0_sec":(idx+1)*30,
                    "sell_share":str(share) if share is not None else None,
                    "depth_ratio":str(ratio) if ratio is not None else None,
                    "mid_change_bps":str(move) if move is not None else None,
                    "status":"WAIT_ENTRY","entry":None,"exit":None,
                    "returns":{}
                })
        self.idx+=1
        self.buckets={s:self._new_bucket(s,boundary_ns) for s in SYMBOLS}

    def _advance(self,mono_ns):
        if self.t0_ns is None:return
        while mono_ns >= self.t0_ns+(self.idx+1)*WINDOW_NS and self.idx<16:
            self._window_close(self.t0_ns+(self.idx+1)*WINDOW_NS)

    def _settle_quotes(self,event,book,mono_ns,utc_ns):
        if event["status"]=="WAIT_ENTRY":
            if mono_ns<=event["decision_mono_ns"]:return
            if mono_ns-event["decision_mono_ns"]>MAX_ENTRY_WAIT_NS:
                event["status"]="CENSORED_LATE_ENTRY";return
            entries={str(n):buy_quote(book,n) for n in NOTIONALS}
            if any(v is None for v in entries.values()):
                event["status"]="CENSORED_ENTRY_DEPTH";return
            event["entry"]={
                "mono_ns":mono_ns,"utc_ns":utc_ns,
                "best_ask":str(min(book.asks)),"entry_quote_base":{n:str(v) for n,v in entries.items()}
            }
            event["_base"]=entries
            event["status"]="WAIT_EXIT"
        elif event["status"]=="WAIT_EXIT":
            target=event["entry"]["mono_ns"]+HORIZON_NS
            if mono_ns<target:return
            if mono_ns-target>MAX_EXIT_WAIT_NS:
                event["status"]="CENSORED_LATE_EXIT";return
            event["exit"]={
                "mono_ns":mono_ns,"utc_ns":utc_ns,"best_bid":str(max(book.bids))
            }
            for n in NOTIONALS:
                qty=event["_base"][str(n)]
                proceeds=sell_base(book,qty)
                if proceeds is None:
                    event["status"]="CENSORED_EXIT_DEPTH"
                    event["returns"]={}
                    return
                r={"gross_bps":str((proceeds/n-D(1))*D(10000))}
                for scenario,slippage in SCENARIOS.items():
                    entry_cost=n*(D(1)+(FEE_BPS+slippage)/D(10000))
                    exit_quote=proceeds*(D(1)-(FEE_BPS+slippage)/D(10000))
                    r[scenario+"_net_bps"]=str((exit_quote/entry_cost-D(1))*D(10000))
                event["returns"][str(n)]=r
            event["status"]="MATURED_HYPOTHETICAL_NOT_FILLED"
            event.pop("_base",None)

    def consume(self,rec):
        now=rec["mono_ns"]
        if self.last_seen_ns is not None and now<self.last_seen_ns:
            raise ValueError("COLLECTOR_MONOTONIC_REVERSAL")
        self.last_seen_ns=now
        if self.t0_ns is not None:self._advance(now) # closes windows BEFORE reading later frame
        symbol=rec.get("symbol")
        if symbol not in SYMBOLS:raise ValueError("UNKNOWN_JOURNAL_SYMBOL")
        b=self.books[symbol]
        raw=json.loads(rec["raw"])
        if rec["kind"]=="snapshot":
            b.snapshot(raw)
            if b.status!="SYNCED":
                raise ValueError("SNAPSHOT_BRIDGE_FAILED_"+symbol+"_"+str(b.failure))
            self.last_depth_ns[symbol]=now
            if self.t0_ns is None and all(z.status=="SYNCED" for z in self.books.values()):
                self._start(now)
            return
        if rec["kind"]!="ws":raise ValueError("UNEXPECTED_JOURNAL_KIND")
        if not isinstance(raw,dict):raise ValueError("BAD_WS_JSON")
        stream=raw.get("stream")
        if not isinstance(stream,str) or stream not in (
            symbol.lower()+"@depth@100ms",symbol.lower()+"@aggTrade"
        ):raise ValueError("UNAPPROVED_STREAM")
        evt=raw.get("data")
        if not isinstance(evt,dict):raise ValueError("INVALID_EVENT")
        parsed=event_validation(evt,symbol)
        age_valid=raw_age_ok(evt,rec["utc_ns"])
        prev_depth_count=b.depth_applied
        b.ingest(evt)
        if b.status=="SOURCE_BLOCKED":
            raise ValueError("ORDER_BOOK_SOURCE_GAP_"+symbol+"_"+str(b.failure))
        self.capture_frames+=1
        if self.t0_ns is None:return
        if not age_valid:
            self.clock_errors+=1
            self.buckets[symbol]["invalid_clock"]+=1
        if parsed[0]=="depth" and b.depth_applied>prev_depth_count:
            self.last_depth_ns[symbol]=now
            self.buckets[symbol]["depth_updates"]+=1
            if age_valid:
                for event in self.events:
                    if event["symbol"]==symbol and event["status"] in ("WAIT_ENTRY","WAIT_EXIT"):
                        self._settle_quotes(event,b,now,rec["utc_ns"])
        elif parsed[0]=="trade" and age_valid:
            # validated user-observable aggregate trade with m=true => aggressive sell
            quote=parsed[2]*parsed[3]
            if parsed[4]:self.buckets[symbol]["sell_quote"]+=quote
            else:self.buckets[symbol]["buy_quote"]+=quote

    def close(self):
        if self.t0_ns is not None:
            self._advance(self.t0_ns+CAPTURE_NS)
        for event in self.events:
            if event["status"] in ("WAIT_ENTRY","WAIT_EXIT"):
                event["status"]="CENSORED_NO_MATURED_QUOTE"
            event.pop("_base",None)
        return self.summary()

    def summary(self):
        kinds=("PRIMARY","FLOW_ONLY_CONTROL","UNCONDITIONAL_BASELINE")
        out={}
        for kind in kinds:
            entries=[e for e in self.events if e["kind"]==kind]
            matured=[e for e in entries if e["status"]=="MATURED_HYPOTHETICAL_NOT_FILLED"]
            stats={}
            for notional in ("100","1000"):
                for scenario in ("BASE_2BPS","STRESS_5BPS"):
                    key=scenario+"_net_bps"
                    numbers=[float(e["returns"][notional][key]) for e in matured]
                    stats[notional+"_"+scenario]={
                        "n":len(numbers),
                        "mean_net_bps":statistics.mean(numbers) if numbers else None,
                        "positive_count":sum(n>0 for n in numbers),
                        "min_net_bps":min(numbers) if numbers else None,
                        "max_net_bps":max(numbers) if numbers else None
                    }
            out[kind]={
                "decisions":len(entries),"matured":len(matured),
                "censored":len(entries)-len(matured),
                "distinct_utc_days":len(set(utc_date(e["entry"]["utc_ns"]) for e in matured)),
                "hypothetical":stats
            }
        return {
            "research_lab_id":"BINANCE-004-SELL-AGGRESSION-BID-RESILIENCE-V01",
            "freeze":"2026-11-23; no outcomes viewed before freeze",
            "t0_monotonic_ns":self.t0_ns,
            "source_clock_invalid_frames":self.clock_errors,
            "processed_ws_frames":self.capture_frames,
            "windows_evaluated":len(self.windows),
            "window_valid":sum(w["valid"] for w in self.windows),
            "sell_pressure_windows":sum(w["pressure"] for w in self.windows),
            "bid_resilience_pressure_windows":sum(w["resilience_proxy"] for w in self.windows),
            "groups":out,
            "minimum_independent_primary_events_for_economic_go":MIN_EVENTS_FOR_GO,
            "minimum_utc_days_for_economic_go":MIN_DAYS_FOR_GO,
            "economic_go":False,
            "trading_authorized":False,
            "real_fills":0,
            "sampling_note":"One short prospectively captured interval is not an independent long-run economic result",
            "status":"SOURCE_PASS_SMALL_PROSPECTIVE_SAMPLE_NO_LIVE_GO"
        }

def run_study(path):
    journal=Path(path)
    original=replay(journal) # verifies SHA chain and independent local-book state
    model=ProspectiveStudy()
    with journal.open(encoding="utf-8") as stream:
        for line in stream:
            model.consume(json.loads(line))
    report=model.close()
    for s in SYMBOLS:
        if model.books[s].summary()!=original["books"][s]:
            raise ValueError("BOOK_STATE_REPLAY_MISMATCH_"+s)
    if model.t0_ns is None or report["source_clock_invalid_frames"] or original["events"]<100:
        report["status"]="SOURCE_BLOCKED_OR_CLOCK_INVALID"
        report["economic_go"]=False
    return report,{"windows":model.windows,"events":model.events}

def main():
    OUT.mkdir(exist_ok=True)
    source=json.loads((OUT/"source_manifest.json").read_text())
    if hashlib.sha256((OUT/"journal.jsonl").read_bytes()).hexdigest()!=source["journal_file_sha256"]:
        raise ValueError("RAW_JOURNAL_SHA256_MISMATCH")
    if source["status"]!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE":
        raise ValueError("SOURCE_NOT_APPROVED_FOR_STUDY")
    report,ledger=run_study(OUT/"journal.jsonl")
    if report["t0_monotonic_ns"]!=source["ready_monotonic_ns"]:
        raise ValueError("T0_NOT_ANCHORED_TO_THIRD_SNAPSHOT")
    raw=json.dumps(ledger,sort_keys=True,indent=2)+"\n"
    (OUT/"forward_ledger.json").write_text(raw)
    report["ledger_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    report["source_journal_sha256"]=source["journal_file_sha256"]
    f=OUT/"forward_verdict.json"
    f.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    (OUT/"forward_verdict.sha256").write_text(hashlib.sha256(f.read_bytes()).hexdigest()+"  forward_verdict.json\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    return 0 if report["status"]=="SOURCE_PASS_SMALL_PROSPECTIVE_SAMPLE_NO_LIVE_GO" else 2

if __name__=="__main__":
    raise SystemExit(main())
