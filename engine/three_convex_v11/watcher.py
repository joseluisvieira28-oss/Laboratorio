"""V11 independent experimental Telegram observer. Never imports MEXC transport."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from datetime import datetime,timezone
from engine.three_convex_v05.signals import Halt
from engine.three_convex_v07.feed import get_public,clock_ms,FeedHalt
from engine.three_convex_v07.telegram import TelegramBot,TelegramHalt
from engine.three_convex_v11.public_feed import fetch_experimental
from engine.three_convex_v11.experimental import experimental_signals,experimental_message

from engine.three_convex_v07.observer_io import drain, add_receipt_column, instance_lock

from engine.three_convex_v07.coverage import Coverage
from engine.three_convex_v11.experimental import LANES

SYMBOLS=("SOL_USDT","BNB_USDT","ETH_USDT")

class Outbox:
    def __init__(self,folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
        self.folder=folder
        self.db=sqlite3.connect(folder/"V11_OUTBOX.sqlite3",timeout=5)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS notices(id TEXT PRIMARY KEY,message TEXT NOT NULL,sent_ms INTEGER)")
        self.db.commit()
        add_receipt_column(self.db,"notices")
    def activation(self,now):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO kv(key,value) VALUES('activation_ms',?)",(str(now),))
        return int(self.db.execute("SELECT value FROM kv WHERE key='activation_ms'").fetchone()[0])
    def queue(self,s):
        message=experimental_message(s)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO notices(id,message) VALUES(?,?)",(s["signal_id"],message))
    def flush(self,send,now):
        return drain(self.db,"notices","sent_ms",send,now,10,"id")
    def pending(self):
        return self.db.execute("SELECT count(*) FROM notices WHERE sent_ms IS NULL").fetchone()[0]

def cycle(box,send,*,now_ms,server_ms,fetch=fetch_experimental,completion_clock=None):
    if type(now_ms) is not int or type(server_ms) is not int or abs(server_ms-now_ms)>5000:
        raise FeedHalt("SOURCE_CLOCK_MISMATCH")
    completion_clock=completion_clock or (lambda:server_ms)
    activation=box.activation(now_ms)
    coverage=Coverage(box.db)
    findings=[];sources={};latencies={}
    # Source failure is isolated; successfully validated observations are persisted
    # before attempting another asset. Telegram failure does not stop detection.
    for symbol in SYMBOLS:
        try:
            bars=fetch(symbol,server_ms,box.folder/"market_cache")
            completed=completion_clock()
            if type(completed) is not int or completed<server_ms:
                raise FeedHalt("NONMONOTONIC_SOURCE_CLOCK")
            signals=experimental_signals(symbol,bars,completed,activation)
            for signal in signals:box.queue(signal)
            findings.extend(signals);sources[symbol]=True
            latencies[symbol]=completed-server_ms
            for lane,(asset,n) in LANES.items():
                if asset==symbol:coverage.record(lane,n,bars,completed,activation,signals)
        except (FeedHalt,Halt,ValueError,TypeError,OSError) as exc:
            sources[symbol]=False
            for lane,(asset,n) in LANES.items():
                if asset==symbol:coverage.record(lane,n,[],server_ms,activation,[],error=exc)
    delivery_error=None
    try:sent=box.flush(send,completion_clock())
    except TelegramHalt as exc:sent=0;delivery_error=type(exc).__name__
    healthy=all(sources.values()) and delivery_error is None
    return {"status":"V11_EXPERIMENTAL_READONLY" if healthy else "V11_DEGRADED_READONLY",
            "checked_at_utc":datetime.fromtimestamp(now_ms/1000,timezone.utc).isoformat(),
            "sources_ok":all(sources.values()),"source_status":sources,"collection_elapsed_ms":latencies,
            "coverage":coverage.summary(),"telegram_error_type":delivery_error,
            "lanes":3,"signal_events":len(findings),"telegram_sent_this_cycle":sent,
            "telegram_pending":box.pending(),"mexc_private_access":False,"orders_enabled":False}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path)
    parser.add_argument("--once",action="store_true")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args(argv)
    if args.self_test:
        from engine.convex_observer_audit.packaged_selftest import run
        return run("V11",Outbox)
    if args.data_dir is None:parser.error("--data-dir is required unless --self-test")
    bot=TelegramBot(os.environ.get("TELEGRAM_BOT_TOKEN",""),os.environ.get("TELEGRAM_CHAT_ID",""))
    with instance_lock(args.data_dir):
        return run_loop(args,bot)

def run_loop(args,bot):
    box=Outbox(args.data_dir)
    while True:
        now=int(time.time()*1000)
        try:
            report=cycle(box,bot.send,now_ms=now,server_ms=clock_ms(),completion_clock=clock_ms)
        except (FeedHalt,Halt,TelegramHalt,sqlite3.Error,ValueError,TypeError,OSError) as e:
            report={"status":"V11_FAIL_CLOSED","error_type":type(e).__name__,
                    "checked_at_utc":datetime.now(timezone.utc).isoformat(),
                    "mexc_private_access":False,"orders_enabled":False}
        target=args.data_dir/"V11_STATUS.json"
        temp=target.with_suffix(".tmp")
        temp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
        os.replace(temp,target)
        print(json.dumps(report,sort_keys=True),flush=True)
        if args.once:return 0 if report["status"]=="V11_EXPERIMENTAL_READONLY" else 2
        time.sleep(60)
if __name__=="__main__":sys.exit(main())
