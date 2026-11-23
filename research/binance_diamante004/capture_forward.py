#!/usr/bin/env python3
"""One new bounded 480-second public Spot WS collection after 3 source bridges.
ZERO account/private data, ZERO orders, ZERO active signals.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent/"binance_diamante003"
sys.path.insert(0,str(ROOT))
from book_core import SYMBOLS,Journal,LocalBook,replay
from capture import WSS,fetch_snapshot

OUT=Path("binance004-evidence")
SECONDS_POST_SYNC=480
MAX_FRAMES=40000
MAX_JOURNAL_BYTES=50_000_000
BOOTSTRAP_TIMEOUT=30

async def collect():
    OUT.mkdir(parents=True,exist_ok=True)
    books={s:LocalBook(s) for s in SYMBOLS}
    journal=Journal(OUT/"journal.jsonl")
    report={
        "study":"BINANCE-DIAMANTE-004",
        "phase":"PRE_FROZEN_PROSPECTIVE_SOURCE_CAPTURE",
        "status":"SOURCE_BLOCKED",
        "ws_host":"data-stream.binance.vision",
        "seconds_post_bridge_target":SECONDS_POST_SYNC,
        "raw_journal":"journal.jsonl",
        "no_keys":True,"no_account":True,"no_orders":True,
        "no_trades":True,"no_paid_data":True,
        "no_auto_reconnect":True,
        "snapshot_receipts":{},
        "source_gap_count":0
    }
    ready_mono_ns=None
    snapshots_requested=set()
    tasks=[]
    nframes=0
    source_error=None
    complete=False
    start_mono=time.monotonic()

    async def snapshot_once(symbol):
        nonlocal ready_mono_ns
        try:
            raw,receipt=await asyncio.to_thread(fetch_snapshot,symbol)
            now_ns=time.time_ns();now_mono=time.monotonic_ns()
            journal.append(kind="snapshot",symbol=symbol,raw=raw,
                           utc_ns=now_ns,mono_ns=now_mono)
            books[symbol].snapshot(json.loads(raw))
            receipt["status"]=books[symbol].status
            receipt["error"]=books[symbol].failure
            report["snapshot_receipts"][symbol]=receipt
            if ready_mono_ns is None and all(b.status=="SYNCED" for b in books.values()):
                ready_mono_ns=now_mono
        except Exception as exc:
            report["snapshot_receipts"][symbol]={
                "status":"SOURCE_BLOCKED","error":type(exc).__name__+": "+str(exc)[:210]
            }
            books[symbol].stop("SNAPSHOT_SOURCE_BLOCKED")

    try:
        from websockets.asyncio.client import connect
        async with connect(WSS,open_timeout=15,close_timeout=5,
                           ping_interval=20,ping_timeout=20,
                           compression=None,max_size=1_000_000,max_queue=128) as ws:
            start_mono=time.monotonic()
            while True:
                if ready_mono_ns is not None:
                    remaining=(ready_mono_ns+SECONDS_POST_SYNC*1_000_000_000-time.monotonic_ns())/1e9
                    if remaining<=0:
                        complete=True
                        break
                else:
                    remaining=BOOTSTRAP_TIMEOUT-(time.monotonic()-start_mono)
                    if remaining<=0:
                        source_error="SNAPSHOT_BOOTSTRAP_TIMEOUT"
                        break
                if nframes>=MAX_FRAMES or journal.bytes_written>=MAX_JOURNAL_BYTES:
                    source_error="RAW_JOURNAL_CAP_REACHED"
                    break
                if any(b.status=="SOURCE_BLOCKED" for b in books.values()):
                    source_error="UNRECONSTRUCTABLE_ORDER_BOOK"
                    break
                try:
                    payload=await asyncio.wait_for(ws.recv(),timeout=min(1.0,remaining))
                except asyncio.TimeoutError:
                    continue
                if not isinstance(payload,str):
                    source_error="BINARY_WS_FRAME_NOT_ALLOWED"
                    break
                now_ns=time.time_ns();mono_ns=time.monotonic_ns()
                try:
                    outer=json.loads(payload)
                    stream=outer["stream"]
                    symbol=stream.split("@")[0].upper()
                    if symbol not in SYMBOLS or stream not in (
                            symbol.lower()+"@depth@100ms",
                            symbol.lower()+"@aggTrade"):
                        raise ValueError("UNAPPROVED_STREAM")
                    evt=outer["data"]
                    if not isinstance(evt,dict) or evt.get("s")!=symbol:
                        raise ValueError("UNEXPECTED_EVENT_SYMBOL")
                    expected="depthUpdate" if stream.endswith("@100ms") else "aggTrade"
                    if evt.get("e")!=expected:
                        raise ValueError("UNEXPECTED_EVENT_KIND")
                    journal.append(kind="ws",symbol=symbol,raw=payload,
                                   utc_ns=now_ns,mono_ns=mono_ns)
                    nframes+=1
                    books[symbol].ingest(evt)
                    if (books[symbol].status=="BUFFERING" and
                        books[symbol].depth_messages>0 and symbol not in snapshots_requested):
                        snapshots_requested.add(symbol)
                        tasks.append(asyncio.create_task(snapshot_once(symbol)))
                except (ValueError,KeyError,TypeError) as exc:
                    source_error="INVALID_PUBLIC_FRAME_"+str(exc)[:150]
                    break
            if tasks:
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks),timeout=17)
                except asyncio.TimeoutError:
                    source_error="SOURCE_SNAPSHOT_TASK_TIMEOUT"
                    for task in tasks:task.cancel()
    except Exception as exc:
        source_error="PUBLIC_WS_SOURCE_BLOCKED_"+type(exc).__name__+"_"+str(exc)[:180]
    finally:
        journal.close()
        report.update({
            "completed_source_window":complete,
            "ws_frames":nframes,"snapshot_count":len(report["snapshot_receipts"]),
            "collection_error":source_error,
            "ready_monotonic_ns":ready_mono_ns,
            "captured_journal_events":journal.n,
            "journal_chain_sha256":journal.prev,
            "journal_file_sha256":hashlib.sha256((OUT/"journal.jsonl").read_bytes()).hexdigest(),
            "journal_bytes":(OUT/"journal.jsonl").stat().st_size,
            "source_books":{s:b.summary() for s,b in books.items()}
        })
        try:
            r=replay(OUT/"journal.jsonl")
            report["source_replay_exact"]=(
                r["events"]==journal.n and r["last_chain_hash"]==journal.prev
                and all(r["books"][s]==books[s].summary() for s in SYMBOLS))
        except Exception as exc:
            report["source_replay_exact"]=False
            report["source_replay_error"]=str(exc)[:220]
        if (complete and source_error is None and
            ready_mono_ns is not None and nframes>100 and
            report["source_replay_exact"] and
            len(report["snapshot_receipts"])==3 and
            all(b.status=="SYNCED" and b.depth_applied>=100 and b.aggtrades>0
                for b in books.values()) and
            report["journal_bytes"]<=MAX_JOURNAL_BYTES):
            report["status"]="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE"
        f=OUT/"source_manifest.json"
        f.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        (OUT/"source_manifest.sha256").write_text(
            hashlib.sha256(f.read_bytes()).hexdigest()+"  source_manifest.json\n")
        print(json.dumps({
            "study":report["study"],"status":report["status"],
            "completed_source_window":complete,"ws_frames":nframes,
            "journal_events":journal.n,"error":source_error,
            "journal_sha256":report["journal_file_sha256"],
            "replay_exact":report["source_replay_exact"],
            "books":{s:{"status":b.status,"depth_applied":b.depth_applied,
                        "aggtrades":b.aggtrades,"failure":b.failure} for s,b in books.items()}
        },indent=2))
    return 0 if report["status"]=="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE" else 2

if __name__=="__main__":
    raise SystemExit(asyncio.run(collect()))
