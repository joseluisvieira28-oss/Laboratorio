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

def cycle(box,send,*,now_ms,server_ms,fetch=fetch_experimental):
    if type(now_ms) is not int or type(server_ms) is not int or abs(server_ms-now_ms)>5000:
        raise FeedHalt("SOURCE_CLOCK_MISMATCH")
    # Previously queued observations are independent of current source availability.
    sent=box.flush(send,now_ms)
    activation=box.activation(now_ms)
    findings=[]
    # Complete all three asset histories before queueing any signals.
    for symbol in SYMBOLS:
        bars=fetch(symbol,server_ms,box.folder/"market_cache")
        findings.extend(experimental_signals(symbol,bars,server_ms,activation))
    # Multiple SOL timeframes share the same physical symbol: observation only.
    for signal in findings:box.queue(signal)
    sent+=box.flush(send,now_ms)
    return {"status":"V11_EXPERIMENTAL_READONLY","checked_at_utc":datetime.fromtimestamp(now_ms/1000,timezone.utc).isoformat(),
            "sources_ok":True,"lanes":3,"signal_events":len(findings),"telegram_sent_this_cycle":sent,
            "telegram_pending":box.pending(),"mexc_private_access":False,"orders_enabled":False}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,required=True)
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args(argv)
    bot=TelegramBot(os.environ.get("TELEGRAM_BOT_TOKEN",""),os.environ.get("TELEGRAM_CHAT_ID",""))
    with instance_lock(args.data_dir):
        return run_loop(args,bot)

def run_loop(args,bot):
    box=Outbox(args.data_dir)
    while True:
        now=int(time.time()*1000)
        try:
            report=cycle(box,bot.send,now_ms=now,server_ms=clock_ms())
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
