"""Unattended 3-CONVEX Telegram + authenticated MEXC READ-ONLY watcher.

No live order methods are imported or reachable from this supervisor.
It never interprets a V5 signal as a filled trade. Native stop status for any
non-flat account is UNVERIFIED until independently reconciled.
"""
from __future__ import annotations
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from engine.three_convex_v06.mexc_futures_live_transport import (
    FuturesV06Transport,PrivateKey,
)
from engine.three_convex_v06.status_app import inspect as account_inspect
from engine.three_convex_v07.feed import (
    clock_ms,fetch_complete,fresh_signals,FeedHalt,
)
from engine.three_convex_v07.telegram import TelegramBot,message_for,TelegramHalt

STATUS="V07_TELEGRAM_PUBLIC_SIGNALS_AND_AUTH_MEXC_READONLY"
ALLOWED_EVENT_TYPES={
    "SYSTEM_ONLINE","MEXC_ACCOUNT_FLAT_READ","MEXC_PROTECTION_UNVERIFIED",
    "MEXC_SOURCE_BLOCKED","V5_SIGNAL_NOT_ORDER",
}


def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class WatchHalt(ValueError):pass


class DurableQueue:
    def __init__(self,dir):
        self.dir=Path(dir)
        self.dir.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.dir/"v07_events.sqlite3",timeout=3)
        self.db.execute("PRAGMA busy_timeout=3000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, message TEXT NOT NULL, sent_at_ms INTEGER, added_ms INTEGER NOT NULL)")
        self.db.commit()

    def state(self,key):
        row=self.db.execute("SELECT value FROM kv WHERE key=?",(key,)).fetchone()
        return row[0] if row else None

    def set(self,key,value):
        with self.db:
            self.db.execute("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (key,str(value)))

    def enqueue(self,event_id,event,now_ms):
        if not isinstance(event_id,str) or not event_id or len(event_id)>200:
            raise WatchHalt("BAD_EVENT_ID")
        if event.get("kind") not in ALLOWED_EVENT_TYPES:
            raise WatchHalt("UNRECOGNIZED_NOTIFICATION_TYPE")
        msg=message_for(event)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO outbox(id,message,sent_at_ms,added_ms) VALUES(?,?,NULL,?)",
                            (event_id,msg,now_ms))

    def drain(self,telegram,now_ms,*,max_count=6):
        rows=self.db.execute("SELECT id,message FROM outbox WHERE sent_at_ms IS NULL ORDER BY added_ms,id LIMIT ?",
                             (max_count,)).fetchall()
        n=0
        for key,message in rows:
            # Crash after Telegram HTTP ACK, before durable DB commit can
            # produce one duplicated notification; NEVER a duplicated ORDER.
            telegram.send(message)
            with self.db:
                self.db.execute("UPDATE outbox SET sent_at_ms=? WHERE id=? AND sent_at_ms IS NULL",
                                (now_ms,key))
            n+=1
        return n

    def pending_count(self):
        return self.db.execute("SELECT COUNT(*) FROM outbox WHERE sent_at_ms IS NULL").fetchone()[0]

    def close(self):
        self.db.close()


def cycle(queue,telegram,*,account_client,public_clock=clock_ms,
          feed=fetch_complete,now_ms=None):
    now_ms=int(time.time()*1000) if now_ms is None else now_ms
    if type(now_ms) is not int:raise WatchHalt("NON_INTEGER_SYSTEM_CLOCK")
    activation=queue.state("activation_ms")
    if activation is None:
        activation=str(now_ms)
        queue.set("activation_ms",activation)
        queue.enqueue("START:"+activation,{"kind":"SYSTEM_ONLINE"},now_ms)
    try:
        activation_ms=int(activation)
    except (TypeError,ValueError):
        raise WatchHalt("CORRUPT_ACTIVATION_TIME")
    # Authenticated private reads; never infer zero positions from errors.
    report=account_inspect(account_client)
    checked=utc(now_ms)
    if report.get("status")!="AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO":
        queue.enqueue("ACCOUNT_BLOCKED:"+str(now_ms//900_000),
                      {"kind":"MEXC_SOURCE_BLOCKED","checked_at_utc":checked,
                       "reason":"ACCOUNT_OR_MARKET_READ_FAILED"},
                      now_ms)
    elif not report.get("broker_account_flat_observed_once"):
        queue.enqueue("UNPROTECTED_OR_UNVERIFIED:"+str(now_ms//300_000),
                      {"kind":"MEXC_PROTECTION_UNVERIFIED","checked_at_utc":checked,
                       "positions":report["open_positions_count"],
                       "orders":report["open_orders_count_all_pages"],
                       "stops":report["open_stops_count"]},now_ms)
    else:
        queue.enqueue("MEXC_FLAT:"+str(now_ms//(6*3600_000)),
                      {"kind":"MEXC_ACCOUNT_FLAT_READ",
                       "checked_at_utc":checked},now_ms)

    # Current public Binance 5m feed (not original archive parity-proven).
    try:
        server=public_clock()
        if abs(server-now_ms)>5_000:
            raise FeedHalt("CLOCK_MISMATCH")
        observations=[]
        for symbol in ("SOL_USDT","BNB_USDT"):
            bars=feed(symbol,server,queue.dir/"market_cache")
            observations+=fresh_signals(symbol,bars,server,activation_ms)
        # Both market histories must validate BEFORE notifying either signal.
        simultaneous={}
        for s in observations:
            simultaneous.setdefault((s["symbol"],s["signal_close_ms"]),[]).append(s)
        for (symbol,close),group in simultaneous.items():
            if symbol=="SOL_USDT" and len(group)>1:
                # Do not portray two same-side SOL lanes as simultaneously
                # executable independent physical positions.
                queue.enqueue("BLOCKED_SOL_COLLISION:"+str(close),
                              {"kind":"MEXC_SOURCE_BLOCKED","checked_at_utc":utc(server),
                               "reason":"TWO_SOL_LONG_LANES_COLLIDE_NO_TRADING"},
                              now_ms)
                continue
            for s in group:
                queue.enqueue("SIGNAL:"+s["signal_id"],{
                    "kind":"V5_SIGNAL_NOT_ORDER",
                    "lane":s["lane"],"symbol":s["symbol"],
                    "close_utc":utc(s["signal_close_ms"]),
                    "signal_id":s["signal_id"],
                },now_ms)
        source_ok=True
    except (FeedHalt,ValueError,TypeError,OSError) as exc:
        # No history replay/fake market data. Never show raw untrusted URLs.
        source_ok=False
        queue.enqueue("BINANCE_SOURCE_BLOCKED:"+str(now_ms//900_000),
                      {"kind":"MEXC_SOURCE_BLOCKED","checked_at_utc":checked,
                       "reason":"PUBLIC_BINANCE_5M_SOURCE_BLOCKED:"+type(exc).__name__},now_ms)
    delivered=queue.drain(telegram,now_ms)
    return {
        "status":STATUS,"checked_at_utc":checked,
        "account_snapshot_status":report.get("status"),
        "account_flat_in_authenticated_snapshot":report.get("broker_account_flat_observed_once",False),
        "v5_public_source_ok":source_ok,
        "telegram_sent_this_cycle":delivered,
        "telegram_outbox_pending":queue.pending_count(),
        "real_order_submission_enabled":False,
        "exchange_mutation":False,
        "live_go":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",type=Path,required=True)
    p.add_argument("--once",action="store_true")
    args=p.parse_args(argv)
    try:
        t=TelegramBot(os.environ.get("TELEGRAM_BOT_TOKEN",""),
                      os.environ.get("TELEGRAM_CHAT_ID",""))
        client=FuturesV06Transport(PrivateKey(
            os.environ.get("MEXC_API_KEY",""),os.environ.get("MEXC_API_SECRET","")))
        q=DurableQueue(args.data_dir)
        while True:
            try:
                info=cycle(q,t,account_client=client)
                print(json.dumps(info,sort_keys=True),flush=True)
                path=args.data_dir/"V07_WATCHER_STATUS.json"
                tmp=path.with_suffix(".tmp")
                with tmp.open("w",encoding="utf8") as f:
                    json.dump(info,f,sort_keys=True,indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp,path)
            except (TelegramHalt,sqlite3.Error,WatchHalt) as exc:
                print(json.dumps({"status":"NO_TRADE_MONITOR_BLOCKED",
                                  "reason_type":type(exc).__name__,
                                  "real_order_submission_enabled":False}),flush=True)
                if args.once:return 2
            if args.once:return 0
            time.sleep(60)
    except Exception as exc:
        print(json.dumps({"status":"V07_INITIALIZATION_BLOCKED",
                          "error_type":type(exc).__name__,
                          "trading_authority":"NONE"}),flush=True)
        return 2


if __name__=="__main__":
    sys.exit(main())
