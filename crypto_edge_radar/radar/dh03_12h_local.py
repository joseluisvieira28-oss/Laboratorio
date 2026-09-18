from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any

from .binance_usdm_archive import SYMBOLS, load_verified_daily_interval_rows
from .binance_usdm_public import BinanceUSDMPublicFeed, BinanceUSDMPublicError
from .dh03_12h_core import (
    FIFTEEN_MIN_MS,
    MINUTE_MS,
    TWELVE_H_MS,
    Bar,
    aggregate_12h,
    bind_exact_entry,
    latest_signal_candidate,
    resolve_minute_path,
)
from .evidence import EvidenceStore

WS_BASE="wss://fstream.binance.com/market"
ARCHIVE_WARMUP_DAYS=24
CELL_ID="HTF-DH03-12H-STANDALONE-FORWARD-V1"


class DH03CollectorError(RuntimeError):
    pass


class DH03MarketStore:
    def __init__(self,path:str)->None:
        self.path=path
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as conn:
            conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS bars15m(
                symbol TEXT NOT NULL,
                open_time INTEGER NOT NULL,
                o REAL NOT NULL,h REAL NOT NULL,l REAL NOT NULL,c REAL NOT NULL,v REAL NOT NULL,
                source TEXT NOT NULL,
                PRIMARY KEY(symbol,open_time)
            );
            CREATE TABLE IF NOT EXISTS minutes(
                symbol TEXT NOT NULL,
                open_time INTEGER NOT NULL,
                o REAL NOT NULL,h REAL NOT NULL,l REAL NOT NULL,c REAL NOT NULL,
                source TEXT NOT NULL,
                PRIMARY KEY(symbol,open_time)
            );
            CREATE TABLE IF NOT EXISTS funding(
                symbol TEXT NOT NULL,
                funding_time INTEGER NOT NULL,
                rate REAL NOT NULL,
                source TEXT NOT NULL,
                PRIMARY KEY(symbol,funding_time)
            );
            CREATE TABLE IF NOT EXISTS meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """)

    def _connect(self):
        return sqlite3.connect(self.path)

    def set_meta(self,key:str,value:Any)->None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key,json.dumps(value,sort_keys=True))
            )

    def get_meta(self,key:str,default:Any=None)->Any:
        with self._connect() as conn:
            row=conn.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
        return default if row is None else json.loads(row[0])

    def put_15m(self,symbol:str,row:tuple[int,float,float,float,float,float],source:str)->None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO bars15m(symbol,open_time,o,h,l,c,v,source) VALUES(?,?,?,?,?,?,?,?)",
                (symbol,*row,source)
            )

    def put_minute(self,symbol:str,row:tuple[int,float,float,float,float],source:str)->None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO minutes(symbol,open_time,o,h,l,c,source) VALUES(?,?,?,?,?,?,?)",
                (symbol,*row,source)
            )

    def put_funding(self,symbol:str,settlement:int,rate:float,source:str)->None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO funding(symbol,funding_time,rate,source) VALUES(?,?,?,?)",
                (symbol,settlement,rate,source)
            )

    def bars15m(self,symbol:str)->list[Bar]:
        with self._connect() as conn:
            rows=conn.execute(
                "SELECT open_time,o,h,l,c,v FROM bars15m WHERE symbol=? ORDER BY open_time",
                (symbol,)
            ).fetchall()
        return [Bar(int(t),float(o),float(h),float(l),float(c),float(v)) for t,o,h,l,c,v in rows]

    def minutes_since(self,symbol:str,start_ms:int)->list[tuple[int,float,float,float,float]]:
        with self._connect() as conn:
            rows=conn.execute(
                "SELECT open_time,o,h,l,c FROM minutes WHERE symbol=? AND open_time>=? ORDER BY open_time",
                (symbol,start_ms)
            ).fetchall()
        return [(int(t),float(o),float(h),float(l),float(c)) for t,o,h,l,c in rows]

    def funding_between(self,symbol:str,start_ms:int,end_ms:int)->list[tuple[int,float]]:
        with self._connect() as conn:
            rows=conn.execute(
                "SELECT funding_time,rate FROM funding WHERE symbol=? AND funding_time>? AND funding_time<? ORDER BY funding_time",
                (symbol,start_ms,end_ms)
            ).fetchall()
        return [(int(t),float(r)) for t,r in rows]


def _utc_ms(dt:datetime)->int:
    return int(dt.timestamp()*1000)


def _latest_archive_day(now:datetime)->date:
    # Mature-day default; caller probes backwards if provider publication lags.
    return now.date()-timedelta(days=1)


def bootstrap_archives(
    market:DH03MarketStore,
    *,
    now:datetime,
    days:int=ARCHIVE_WARMUP_DAYS,
    timeout:int=20,
)->dict[str,Any]:
    end=_latest_archive_day(now)
    summary={}
    for symbol in SYMBOLS:
        loaded=0
        checksum_days=0
        d=end-timedelta(days=days-1)
        while d<=end:
            try:
                receipt=load_verified_daily_interval_rows(symbol,d,"15m",timeout)
            except Exception:
                d+=timedelta(days=1)
                continue
            for row in receipt["rows"]:
                market.put_15m(symbol,row,"BINANCE_OFFICIAL_ARCHIVE_15M")
            loaded+=len(receipt["rows"])
            checksum_days+=1
            d+=timedelta(days=1)
        summary[symbol]={"rows":loaded,"checksum_days":checksum_days}
    return summary


def bootstrap_recent_rest(
    market:DH03MarketStore,
    *,
    feed:BinanceUSDMPublicFeed|None=None,
    now_ms:int,
)->dict[str,Any]:
    feed=feed or BinanceUSDMPublicFeed(timeout=15)
    out={}
    for symbol in SYMBOLS:
        existing=market.bars15m(symbol)
        start=(existing[-1].open_time+FIFTEEN_MIN_MS) if existing else now_ms-3*24*60*60*1000
        inserted=0
        cursor=start
        blocked=None
        while cursor<now_ms:
            try:
                rows=feed.klines(
                    symbol,"15m",limit=1500,start_ms=cursor,end_ms=now_ms-1
                )
            except Exception as exc:
                blocked=f"{type(exc).__name__}:{exc}"
                break
            if not rows:
                break
            parsed=[]
            for row in rows:
                if not isinstance(row,list) or len(row)<7:
                    raise DH03CollectorError("invalid REST kline row")
                t=int(row[0]); o=float(row[1]); h=float(row[2]); l=float(row[3]); c=float(row[4]); v=float(row[5])
                # Never bootstrap an unclosed 15m candle.
                close_t=int(row[6])
                if close_t>=now_ms:
                    continue
                parsed.append((t,o,h,l,c,v))
            if not parsed:
                break
            for row in parsed:
                market.put_15m(symbol,row,"BINANCE_USDM_PUBLIC_REST_BOOTSTRAP")
            inserted+=len(parsed)
            nxt=max(x[0] for x in parsed)+FIFTEEN_MIN_MS
            if nxt<=cursor:
                raise DH03CollectorError("REST bootstrap pagination did not advance")
            cursor=nxt
            if len(rows)<1500:
                break
        out[symbol]={"inserted":inserted,"blocked":blocked}
    return out


class DH03ShadowEngine:
    def __init__(
        self,
        *,
        market:DH03MarketStore,
        evidence:EvidenceStore,
        activation_ms:int,
    )->None:
        self.market=market
        self.evidence=evidence
        self.activation_ms=activation_ms

    def _event_key(self,symbol:str,signal_open:int)->str:
        return f"{CELL_ID}:{symbol}:{signal_open}"

    def _payloads(self,event_type:str)->dict[str,dict[str,Any]]:
        out={}
        for x in self.evidence.read_payloads(event_type):
            k=x.get("event_key")
            if isinstance(k,str):
                out[k]=x
        return out

    def on_closed_15m(self,symbol:str,row:tuple[int,float,float,float,float,float],source:str="BINANCE_USDM_PUBLIC_WEBSOCKET")->dict[str,Any]|None:
        self.market.put_15m(symbol,row,source)
        open_time=row[0]
        # Signal evaluation only when this candle closes a UTC 12H bucket.
        if (open_time+FIFTEEN_MIN_MS)%TWELVE_H_MS!=0:
            return None
        bars12,incomplete=aggregate_12h(self.market.bars15m(symbol))
        if incomplete:
            # Incomplete old buckets are allowed only if the latest contiguous segment remains sufficient.
            pass
        candidate=latest_signal_candidate(symbol,bars12)
        if candidate is None or candidate.signal_close_time<=self.activation_ms:
            return None
        key=self._event_key(symbol,candidate.signal_open_time)
        active_entries=self._payloads("DH03_LOCAL_ENTRY")
        resolutions=self._payloads("DH03_LOCAL_RESOLUTION")
        # One active trade per symbol.
        for ek,p in active_entries.items():
            if p.get("symbol")==symbol and ek not in resolutions:
                return {"status":"OVERLAP_SKIPPED","event_key":key}
        payload={
            "event_key":key,
            "evidence_role":"OPERATIONAL_TIMING_DIAGNOSTIC_ONLY",
            "counts_as_scientific_forward_outcome":False,
            "cell_id":CELL_ID,
            "symbol":symbol,
            "candidate":asdict(candidate),
            "activation_ms":self.activation_ms,
            "source":source,
            "authenticated_exchange_api_used":False,
            "orders_created":False,
            "exchange_mutation_performed":False,
        }
        rec=self.evidence.append_once("DH03_LOCAL_SIGNAL",key,payload)
        return {"status":"SIGNAL_RECORDED" if rec["inserted"] else "SIGNAL_DUPLICATE","event_key":key}

    def on_open_1m(
        self,
        symbol:str,
        open_time:int,
        open_price:float,
        source:str="BINANCE_USDM_PUBLIC_WEBSOCKET",
    )->list[dict[str,Any]]:
        signals=self._payloads("DH03_LOCAL_SIGNAL")
        entries=self._payloads("DH03_LOCAL_ENTRY")
        resolutions=self._payloads("DH03_LOCAL_RESOLUTION")
        deviations=self._payloads("DH03_LOCAL_DEVIATION")
        changes=[]
        for key,payload in signals.items():
            if payload.get("symbol")!=symbol or key in entries or key in resolutions or key in deviations:
                continue
            cand_payload=payload.get("candidate") or {}
            entry_time=int(cand_payload["signal_close_time"])
            if open_time<entry_time:
                continue
            if open_time>entry_time:
                d={
                    "event_key":key,"symbol":symbol,
                    "reason":"MISSED_EXACT_ENTRY_MINUTE_NO_RECONSTRUCTION",
                    "expected_entry_open_time":entry_time,"first_seen_minute":open_time,
                }
                self.evidence.append_once("DH03_LOCAL_DEVIATION",key,d)
                changes.append(d)
                continue
            from .dh03_12h_core import SignalCandidate
            candidate=SignalCandidate(**cand_payload)
            try:
                signal=bind_exact_entry(candidate,open_time,open_price)
            except ValueError as exc:
                d={"event_key":key,"symbol":symbol,"reason":f"PRE_ENTRY_CANCELLED:{exc}"}
                self.evidence.append_once("DH03_LOCAL_DEVIATION",key,d)
                changes.append(d)
                continue
            entry={
                "event_key":key,"symbol":symbol,"signal":asdict(signal),
                "source":source,"orders_created":False,"live_capital_enabled":False,
            }
            self.evidence.append_once("DH03_LOCAL_ENTRY",key,entry)
            changes.append({"status":"ENTRY_BOUND","event_key":key})
        return changes

    def on_closed_1m(self,symbol:str,row:tuple[int,float,float,float,float],source:str="BINANCE_USDM_PUBLIC_WEBSOCKET")->list[dict[str,Any]]:
        self.market.put_minute(symbol,row,source)
        t,o,hi,lo,c=row
        signals=self._payloads("DH03_LOCAL_SIGNAL")
        entries=self._payloads("DH03_LOCAL_ENTRY")
        resolutions=self._payloads("DH03_LOCAL_RESOLUTION")
        deviations=self._payloads("DH03_LOCAL_DEVIATION")
        changes=[]

        for key,payload in signals.items():
            if payload.get("symbol")!=symbol or key in resolutions or key in deviations or key not in entries:
                continue
            signal_payload=(entries[key].get("signal") or {})
            from .dh03_12h_core import Signal
            signal=Signal(**signal_payload)
            minutes=self.market.minutes_since(symbol,signal.entry_open_time)
            funding=self.market.funding_between(
                symbol,signal.entry_open_time,signal.entry_open_time+80*TWELVE_H_MS+MINUTE_MS
            )
            outcome=resolve_minute_path(signal,minutes,funding)
            if outcome.exit_reason=="EXECUTION_PATH_UNRESOLVED_GAP":
                d={
                    "event_key":key,"symbol":symbol,
                    "reason":"EXECUTION_PATH_UNRESOLVED_GAP",
                    "last_seen_minute":t,
                }
                self.evidence.append_once("DH03_LOCAL_DEVIATION",key,d)
                changes.append(d)
            elif outcome.resolved:
                resolution={
                    "event_key":key,"evidence_role":"OPERATIONAL_TIMING_DIAGNOSTIC_ONLY",
                    "counts_as_scientific_forward_outcome":False,
                    "symbol":symbol,
                    "signal":signal_payload,
                    "outcome":asdict(outcome),
                    "orders_created":False,"live_capital_enabled":False,
                }
                self.evidence.append_once("DH03_LOCAL_RESOLUTION",key,resolution)
                changes.append({"status":"RESOLVED","event_key":key,"reason":outcome.exit_reason})
        return changes

    def on_mark_price(self,symbol:str,event_time:int,next_funding_ms:int,rate:float)->dict[str,Any]|None:
        meta_key=f"funding_pending:{symbol}"
        prev=self.market.get_meta(meta_key)
        current={"next_funding_ms":int(next_funding_ms),"rate":float(rate),"event_time":int(event_time)}
        self.market.set_meta(meta_key,current)
        if not prev:
            return None
        prev_t=int(prev["next_funding_ms"])
        if int(next_funding_ms)==prev_t:
            return None
        # The next funding timestamp rolled forward: the last observed rate belongs to the prior settlement.
        if int(event_time)<prev_t:
            return None
        self.market.put_funding(symbol,prev_t,float(prev["rate"]),"BINANCE_MARK_PRICE_STREAM_FINAL_OBS")
        key=f"{symbol}:{prev_t}"
        payload={
            "event_key":key,"symbol":symbol,"funding_time":prev_t,
            "funding_rate":float(prev["rate"]),"source":"BINANCE_MARK_PRICE_STREAM_FINAL_OBS",
        }
        self.evidence.append_once("DH03_LOCAL_FUNDING_SETTLEMENT",key,payload)
        return payload


class DH03LocalCollector:
    def __init__(
        self,
        *,
        data_db:str,
        evidence_db:str,
        activation_ms:int|None=None,
    )->None:
        self.market=DH03MarketStore(data_db)
        self.evidence=EvidenceStore(evidence_db)
        existing=self.market.get_meta("collector_activation_ms")
        if existing is None:
            activation_ms=activation_ms or int(datetime.now(timezone.utc).timestamp()*1000)
            self.market.set_meta("collector_activation_ms",activation_ms)
        else:
            activation_ms=int(existing)
        self.engine=DH03ShadowEngine(
            market=self.market,evidence=self.evidence,activation_ms=int(activation_ms)
        )

    def bootstrap(self)->dict[str,Any]:
        now=datetime.now(timezone.utc)
        archives=bootstrap_archives(self.market,now=now)
        rest=bootstrap_recent_rest(
            self.market,now_ms=int(now.timestamp()*1000)
        )
        return {
            "archives":archives,"rest":rest,
            "activation_ms":self.engine.activation_ms,
            "mode":"PUBLIC_SHADOW_ONLY",
            "orders_created":False,"live_capital_enabled":False,
        }

    def run_forever(self)->None:
        try:
            from websockets.sync.client import connect
        except Exception as exc:
            raise DH03CollectorError("websockets dependency unavailable") from exc

        streams=[]
        for symbol in SYMBOLS:
            s=symbol.lower()
            streams.extend([f"{s}@kline_15m",f"{s}@kline_1m",f"{s}@markPrice@1s"])
        url=f"{WS_BASE}/stream?streams={'/'.join(streams)}"
        while True:
            try:
                with connect(url,open_timeout=10,close_timeout=3,ping_interval=120,ping_timeout=30) as ws:
                    self.evidence.append("DH03_LOCAL_COLLECTOR_CONNECTION",{
                        "status":"CONNECTED","url_host":"fstream.binance.com",
                        "authenticated_exchange_api_used":False,
                    })
                    while True:
                        raw=ws.recv(timeout=180)
                        obj=json.loads(raw)
                        data=obj.get("data") if isinstance(obj,dict) else None
                        if not isinstance(data,dict):
                            continue
                        symbol=str(data.get("s","")).upper()
                        if symbol not in SYMBOLS:
                            continue
                        event=str(data.get("e",""))
                        if event=="kline":
                            k=data.get("k")
                            if not isinstance(k,dict):
                                continue
                            interval=str(k.get("i"))
                            if interval=="1m":
                                self.engine.on_open_1m(symbol,int(k["t"]),float(k["o"]))
                                if bool(k.get("x")):
                                    row=(int(k["t"]),float(k["o"]),float(k["h"]),float(k["l"]),float(k["c"]))
                                    self.engine.on_closed_1m(symbol,row)
                            elif interval=="15m" and bool(k.get("x")):
                                row=(int(k["t"]),float(k["o"]),float(k["h"]),float(k["l"]),float(k["c"]),float(k["v"]))
                                self.engine.on_closed_15m(symbol,row)
                        elif event=="markPriceUpdate":
                            self.engine.on_mark_price(
                                symbol,int(data["E"]),int(data["T"]),float(data["r"])
                            )
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                self.evidence.append("DH03_LOCAL_COLLECTOR_CONNECTION",{
                    "status":"RECONNECTING",
                    "error":f"{type(exc).__name__}:{exc}",
                    "authenticated_exchange_api_used":False,
                })
                time.sleep(3)


def default_paths()->tuple[str,str]:
    root=Path(os.getenv("LOCALAPPDATA") or Path.home())/"CryptoEdgeRadar"
    root.mkdir(parents=True,exist_ok=True)
    return str(root/"dh03_market.sqlite3"),str(root/"dh03_evidence.sqlite3")
