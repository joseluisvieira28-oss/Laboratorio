"""Isolated V12 four-lane Telegram observer. PUBLIC Binance + Telegram send only.

No MEXC import, no buy/sell actions, no private exchange API, no Telegram
getUpdates, no webhook mutation, no interference with V07/V11 databases.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from engine.three_convex_v05.signals import Halt
from engine.three_convex_v07.feed import FeedHalt,clock_ms
from engine.three_convex_v07.telegram import TelegramBot,TelegramHalt
from engine.three_convex_v12.public_feed import fetch,atomic_save
from engine.three_convex_v12.lanes import ASSETS,LANES,decide,message_for_signal

SYMBOLS=("BNB_USDT","SOL_USDT","DOGE_USDT")
MAX_SIGNAL_AGE_MS=180000
assert frozenset(SYMBOLS)==ASSETS and len(LANES)==4

class AlreadyRunning(Exception):
    pass

class SingleInstance:
    """Portable OS-managed lifetime lock: automatically released after crash."""
    def __init__(self,path):
        self.path=Path(path)
        self.fp=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.fp=open(self.path,"a+b")
        try:
            self.fp.seek(0)
            self.fp.write(b"0")
            self.fp.flush()
            self.fp.seek(0)
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(self.fp.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.fp.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (OSError,IOError):
            self.fp.close()
            self.fp=None
            raise AlreadyRunning("V12_SINGLE_INSTANCE_LOCKED") from None
        return self
    def __exit__(self,exc_type,exc,tb):
        if self.fp:
            try:
                if os.name=="nt":
                    import msvcrt
                    self.fp.seek(0)
                    msvcrt.locking(self.fp.fileno(),msvcrt.LK_UNLCK,1)
                else:
                    import fcntl
                    fcntl.flock(self.fp.fileno(),fcntl.LOCK_UN)
            finally:
                self.fp.close()
        return False

class Outbox:
    def __init__(self,dir):
        self.folder=Path(dir)
        self.folder.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.folder/"V12_ONLY.sqlite3",timeout=5)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS notices (
            id TEXT PRIMARY KEY, message TEXT NOT NULL, close_ms INTEGER NOT NULL,
            sent_ms INTEGER, expired_ms INTEGER)""")
        self.db.commit()
    def activation(self,now):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO kv(key,value) VALUES('activation_ms',?)",(str(now),))
        return int(self.db.execute("SELECT value FROM kv WHERE key='activation_ms'").fetchone()[0])
    def enqueue(self,event):
        if event.get("lane") not in LANES or event.get("category")!="V12_HISTORICAL_ONLY_EXPERIMENTAL":
            raise Halt("V12_ALERT_CATEGORY_NOT_AUTHORIZED")
        msg=message_for_signal(event)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO notices(id,message,close_ms,sent_ms,expired_ms) VALUES(?,?,?,NULL,NULL)",
                (event["signal_id"],msg,event["signal_close_ms"]))
    def drain(self,send,now):
        expired=0
        # Prevent stale/delayed alerts appearing as fresh entries after outages.
        with self.db:
            cur=self.db.execute("UPDATE notices SET expired_ms=? WHERE sent_ms IS NULL AND expired_ms IS NULL AND (? - close_ms > ? OR close_ms > ?)",
                (now,now,MAX_SIGNAL_AGE_MS,now))
            expired=cur.rowcount
        rows=self.db.execute("SELECT id,message,close_ms FROM notices WHERE sent_ms IS NULL AND expired_ms IS NULL ORDER BY close_ms,id LIMIT 10").fetchall()
        delivered=0
        for id,msg,close_ms in rows:
            if now-close_ms>MAX_SIGNAL_AGE_MS:
                with self.db:self.db.execute("UPDATE notices SET expired_ms=? WHERE id=? AND sent_ms IS NULL",(now,id))
                expired+=1
                continue
            # A crash between Telegram ACK and SQLite commit MAY duplicate a notice;
            # exactly-once Telegram delivery cannot be proven.
            send(msg)
            with self.db:self.db.execute("UPDATE notices SET sent_ms=? WHERE id=? AND sent_ms IS NULL",(now,id))
            delivered+=1
        return delivered,expired
    def pending(self):
        return self.db.execute("SELECT count(*) FROM notices WHERE sent_ms IS NULL AND expired_ms IS NULL").fetchone()[0]
    def close(self):
        self.db.close()

def cycle(box,send,*,now_ms,server_ms,market_fetch=fetch,fresh_clock=None):
    if type(now_ms) is not int or type(server_ms) is not int or abs(now_ms-server_ms)>5000:
        raise FeedHalt("V12_CLOCK_MISMATCH")
    activation=box.activation(now_ms)
    sources={}
    histories=[]
    # Each source is independent: an invalid DOGE feed must NOT erase a
    # previously verified SOL/BNB observation or block queued Telegram.
    for symbol in SYMBOLS:
        try:
            bars=market_fetch(symbol,server_ms,box.folder/"market_cache")
            histories.append((symbol,bars))
            sources[symbol]="OK"
        except (FeedHalt,Halt,ValueError,TypeError,OSError) as exc:
            sources[symbol]="BLOCKED:"+type(exc).__name__
    # In production, refresh the trusted Binance clock after ALL downloads.
    # Never use a clock from before slow HTTP pagination to claim a fresh alert.
    evaluated_ms=fresh_clock() if fresh_clock is not None else now_ms
    if type(evaluated_ms) is not int or evaluated_ms<server_ms:
        raise FeedHalt("V12_EVALUATION_CLOCK_INVALID")
    found=[]
    for symbol,bars in histories:
        try:
            found.extend(decide(symbol,bars,evaluated_ms,activation))
        except (FeedHalt,Halt,ValueError,TypeError,OSError) as exc:
            sources[symbol]="BLOCKED:"+type(exc).__name__
    if len(found)>4 or any(s["lane"] not in LANES for s in found):
        raise Halt("V12_INVALID_SIGNAL_SET")
    for s in found:box.enqueue(s)
    # Previously durable outbox drains even while any live source is blocked.
    sent,expired=box.drain(send,evaluated_ms)
    healthy=all(v=="OK" for v in sources.values()) and len(sources)==len(SYMBOLS)
    return {
        "status":"V12_EXPERIMENTAL_READONLY" if healthy else "V12_DEGRADED_READONLY",
        "checked_at_utc":datetime.fromtimestamp(evaluated_ms/1000,timezone.utc).isoformat(),
        "source_status":sources,
        "sources_ok":healthy,"new_lanes":len(LANES),"total_inventory":10,
        "signal_events":len(found),"telegram_sent_this_cycle":sent,
        "telegram_pending":box.pending(),"stale_signals_suppressed_this_cycle":expired,
        "exchange_private_access":False,"orders_enabled":False,"telegram_outbound_only":True
    }

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",type=Path,required=True)
    p.add_argument("--once",action="store_true")
    args=p.parse_args(argv)
    box=None
    try:
        with SingleInstance(args.data_dir/"V12_INSTANCE_LOCK"):
            bot=TelegramBot(os.environ.get("TELEGRAM_BOT_TOKEN",""),os.environ.get("TELEGRAM_CHAT_ID",""))
            box=Outbox(args.data_dir)
            while True:
                now=int(time.time()*1000)
                try:
                    report=cycle(box,bot.send,now_ms=now,server_ms=clock_ms(),fresh_clock=clock_ms)
                except (FeedHalt,Halt,TelegramHalt,sqlite3.Error,ValueError,TypeError,OSError) as exc:
                    report={
                        "status":"V12_FAIL_CLOSED","error_type":type(exc).__name__,
                        "checked_at_utc":datetime.now(timezone.utc).isoformat(),
                        "new_lanes":4,"total_inventory":10,"sources_ok":False,
                        "orders_enabled":False,"exchange_private_access":False
                    }
                atomic_save(args.data_dir/"V12_STATUS.json",report)
                print(json.dumps(report,sort_keys=True),flush=True)
                if args.once:
                    return 0 if report["status"]=="V12_EXPERIMENTAL_READONLY" else 2
                time.sleep(60)
    except (AlreadyRunning,TelegramHalt,sqlite3.Error,OSError) as exc:
        print(json.dumps({"status":"V12_INITIALIZATION_BLOCKED",
            "error_type":type(exc).__name__,"orders_enabled":False}),flush=True)
        return 2
    finally:
        if box:box.close()

if __name__=="__main__":
    sys.exit(main())
