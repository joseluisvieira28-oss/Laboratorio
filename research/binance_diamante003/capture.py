#!/usr/bin/env python3
"""One-shot public Binance Spot combined WS + REST snapshot 45s source probe.
No account, trading, fills, PnL, future returns or predictions.
"""
from __future__ import annotations
import asyncio
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from book_core import SYMBOLS, Journal, LocalBook, replay

WSS = ("wss://data-stream.binance.vision/stream?streams="
       "btcusdt@depth@100ms/btcusdt@aggTrade/"
       "ethusdt@depth@100ms/ethusdt@aggTrade/"
       "solusdt@depth@100ms/solusdt@aggTrade")
REST_HOST = "https://data-api.binance.vision"
OUT = Path("binance003-evidence")
SECONDS = 45
MAX_FRAMES = 12000
MAX_JOURNAL_BYTES = 20_000_000
MAX_REST_BYTES = 2_000_000

def rest_url(symbol):
    if symbol not in SYMBOLS:
        raise ValueError("UNAUTHORIZED_SYMBOL")
    return f"{REST_HOST}/api/v3/depth?symbol={symbol}&limit=1000"

def fetch_snapshot(symbol):
    """Exactly one whitelisted public GET; never authenticates or retries."""
    url = rest_url(symbol)
    start_ns, start_mono = time.time_ns(), time.monotonic_ns()
    req = urllib.request.Request(url,headers={
        "User-Agent": "CryptoLab-BinanceDiamante003-SOURCE_ONLY/0.1"
    })
    with urllib.request.urlopen(req,timeout=15) as response:
        if response.status != 200:
            raise ValueError("HTTP_" + str(response.status))
        raw = response.read(MAX_REST_BYTES+1)
    recv_ns, recv_mono = time.time_ns(), time.monotonic_ns()
    if len(raw) == 0 or len(raw)>MAX_REST_BYTES:
        raise ValueError("BAD_OR_OVERSIZED_SNAPSHOT_RESPONSE")
    return raw.decode("utf-8"), {
        "source_url":url, "request_utc_ns": start_ns,
        "receipt_utc_ns":recv_ns, "elapsed_ms":round((recv_mono-start_mono)/1_000_000,3),
        "sha256_raw":hashlib.sha256(raw).hexdigest(), "raw_bytes":len(raw)
    }

def iso_utc(ns):
    return dt.datetime.fromtimestamp(ns/1e9, tz=dt.timezone.utc).isoformat()

async def collect():
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"journal.jsonl"
    books={s:LocalBook(s) for s in SYMBOLS}
    report={
        "study":"BINANCE-DIAMANTE-003",
        "status":"SOURCE_BLOCKED_OR_INSUFFICIENT",
        "scope":"ONE_OFF_45S_BINANCE_SPOT_PUBLIC_WS",
        "ws_url":WSS,"seconds_pre_registered":SECONDS,"snapshots":{},
        "symbols":{},"raw_journal":"journal.jsonl",
        "no_account":True,"no_private_endpoints":True,"no_api_keys":True,
        "no_orders":True,"no_trades":True,"no_pnl":True,
        "no_prediction":True,"snapshot_complete_book":False,
        "price_level_removal_is_order_cancellation":False,
        "fee_execution_unverified":True,"swiss_account_access_unverified":True,
        "reconnection_attempts":0,"rest_snapshots_max":len(SYMBOLS)
    }
    journal=Journal(path)
    capture_start=time.monotonic()
    session_started=False
    complete_window=False
    captured_error=None
    snap_tasks={}
    snap_attempted=set()
    frames=0

    async def seed_once(symbol):
        try:
            raw,rec=await asyncio.to_thread(fetch_snapshot,symbol)
            journal.append(kind="snapshot",symbol=symbol,raw=raw,
                           utc_ns=time.time_ns(),mono_ns=time.monotonic_ns())
            books[symbol].snapshot(json.loads(raw))
            rec["bridge_status"]=books[symbol].status
            rec["bridge_failure"]=books[symbol].failure
            report["snapshots"][symbol]=rec
        except Exception as exc:
            report["snapshots"][symbol]={
                "status":"SOURCE_BLOCKED", "error_type":type(exc).__name__,
                "error":str(exc)[:240],"url":rest_url(symbol)
            }
            books[symbol].stop("SNAPSHOT_SOURCE_BLOCKED")

    try:
        # No SUBSCRIBE message: the six public streams are whitelisted in the URL.
        from websockets.asyncio.client import connect
        async with connect(WSS,open_timeout=15,close_timeout=5,
                           ping_interval=20,ping_timeout=20,
                           compression=None,max_size=1_000_000,max_queue=128) as ws:
            session_started=True
            capture_start=time.monotonic()
            deadline=capture_start+SECONDS
            while True:
                left=deadline-time.monotonic()
                if left<=0:
                    complete_window=True
                    break
                if frames>=MAX_FRAMES or journal.bytes_written>=MAX_JOURNAL_BYTES:
                    captured_error="CAPTURE_LIMIT_REACHED_BEFORE_END"
                    break
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=min(2.0,left))
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw,str):
                    captured_error="NON_UTF8_WS_FRAME"
                    break
                now_ns=time.time_ns()
                mono_ns=time.monotonic_ns()
                try:
                    envelope=json.loads(raw)
                    stream=envelope["stream"]
                    if stream=="!serverShutdown":
                        captured_error="SERVER_SHUTDOWN_NO_RECONNECT"
                        break
                    symbol=stream.split("@",1)[0].upper()
                    if symbol not in books or stream not in (
                        symbol.lower()+"@depth@100ms",
                        symbol.lower()+"@aggTrade"
                    ):
                        captured_error="UNAPPROVED_STREAM"
                        break
                    if not isinstance(envelope.get("data"),dict):
                        captured_error="BAD_COMBINED_STREAM"
                        break
                    expected="depthUpdate" if stream.endswith("@100ms") else "aggTrade"
                    if envelope["data"].get("e")!=expected:
                        captured_error="EVENT_TYPE_STREAM_MISMATCH"
                        break
                    journal.append(kind="ws",symbol=symbol,raw=raw,
                                   utc_ns=now_ns,mono_ns=mono_ns)
                    frames+=1
                    books[symbol].ingest(envelope["data"])
                    if books[symbol].status=="BUFFERING" and books[symbol].depth_messages>0 and symbol not in snap_attempted:
                        snap_attempted.add(symbol)
                        snap_tasks[symbol]=asyncio.create_task(seed_once(symbol))
                except (ValueError,KeyError,TypeError) as exc:
                    captured_error="INVALID_WS_MESSAGE_"+type(exc).__name__+"_"+str(exc)[:90]
                    break
            # Any in-flight one-off snapshots must finish for a faithful journal.
            if snap_tasks:
                try:
                    await asyncio.wait_for(asyncio.gather(*snap_tasks.values()),timeout=18)
                except asyncio.TimeoutError:
                    captured_error="SNAPSHOT_TASK_TIMEOUT"
                    for task in snap_tasks.values(): task.cancel()
    except Exception as exc:
        captured_error="WS_SOURCE_BLOCKED_"+type(exc).__name__+"_"+str(exc)[:200]
    finally:
        report["wall_window_seconds"]=round(time.monotonic()-capture_start,3)
        report["ws_connection_started"]=session_started
        report["completed_capture_window"]=complete_window
        report["bounded_capture_error"]=captured_error
        report["ws_frames_captured"]=frames
        journal.close()
        report["journal_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        report["journal_chain_head"]=journal.prev
        report["journal_events"]=journal.n
        report["journal_bytes"]=path.stat().st_size
        # Exact same original raw journal bytes must independently replay.
        try:
            check=replay(path)
            report["replay_matches_original_state"]=(
                check["last_chain_hash"]==journal.prev and
                check["events"]==journal.n and
                all(check["books"][s]==books[s].summary() for s in SYMBOLS)
            )
            report["replay"]={
                "status":"REPLAY_MATCH" if report["replay_matches_original_state"] else "REPLAY_DIVERGENCE",
                "last_chain_hash":check["last_chain_hash"],"events":check["events"]
            }
        except Exception as exc:
            report["replay_matches_original_state"]=False
            report["replay"]={"status":"REPLAY_BLOCKED","error":str(exc)[:200]}
        report["symbols"]={s:b.summary() for s,b in books.items()}
        valid=(complete_window and captured_error is None and frames>0 and
               report["journal_bytes"]<=MAX_JOURNAL_BYTES and
               report["replay_matches_original_state"] and
               len(report["snapshots"])==3 and
               all(b.status=="SYNCED" and b.depth_applied>=10 and b.aggtrades>=1
                   for b in books.values()))
        if valid:report["status"]="SOURCE_REPLAY_PASS_ONLY"
        raw=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
        manifest=OUT/"manifest.json"
        manifest.write_text(raw,encoding="utf-8")
        (OUT/"manifest.sha256").write_text(
            hashlib.sha256(manifest.read_bytes()).hexdigest()+"  manifest.json\n")
        print(json.dumps({
            "study":report["study"],"status":report["status"],
            "completed_window":complete_window,
            "elapsed_seconds":report["wall_window_seconds"],
            "error":captured_error,"frames":frames,
            "journal_sha256":report["journal_sha256"],
            "chain_head":report["journal_chain_head"],
            "replay":report["replay"],
            "snapshot_statuses":{s:report["snapshots"].get(s,{}).get("bridge_status","SOURCE_BLOCKED")
                                 for s in SYMBOLS},
            "books":report["symbols"],"no_trades":True
        },indent=2,sort_keys=True))
    return 0 if report["status"]=="SOURCE_REPLAY_PASS_ONLY" else 2

if __name__=="__main__":
    raise SystemExit(asyncio.run(collect()))
