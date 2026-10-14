"""Offline signed-receipt CONVEX V05 driver, JSONL inputs only.

No HTTP/network, authentication, orders, account reads, task scheduling, or
private credentials. The engine may be run on externally supplied shadow
candles; the file itself does NOT prove origin or true publication time.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from engine.three_convex_v05.signals import Halt, MS5
from engine.three_convex_v05.shadow import raw_market_bars, ShadowMotor


def load_jsonl(path):
    path=Path(path)
    raw=path.read_bytes()
    if len(raw)>100_000_000:
        raise Halt("INPUT_FILE_EXCEEDS_OFFLINE_LIMIT")
    result=[]
    for ln,line in enumerate(raw.decode("utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        try:
            row=json.loads(line)
        except json.JSONDecodeError as exc:
            raise Halt("INPUT_NOT_JSONL_AT_LINE_"+str(ln)) from exc
        if not isinstance(row,dict):
            raise Halt("BAD_ROW_AT_LINE_"+str(ln))
        result.append(row)
    return result,hashlib.sha256(raw).hexdigest()


def synthetic_fixture(count=250):
    """Only to test packaging and deterministic offline operation, NOT alpha."""
    if count<4:
        raise Halt("SYNTHETIC_COUNT_TOO_SMALL")
    base=datetime(2025,1,1,tzinfo=timezone.utc)
    start=int(base.timestamp()*1000)
    out=[]
    for s,price in (("SOL_USDT",100.0),("BNB_USDT",700.0)):
        for i in range(count):
            # Each candle is artificial; constant price means no V5 signal.
            out.append(dict(symbol=s,source="BINANCE_USDM_CANONICAL_5M",
                            t=start+i*MS5,open=price,high=price*1.0001,
                            low=price*.9999,close=price,volume=1000.0))
    return out


def save_immutable(output_dir, report, receipts):
    """Use exclusive file creation to avoid silently overwriting any evidence."""
    output=Path(output_dir)
    if output.exists():
        raise Halt("OUTPUT_DIRECTORY_ALREADY_EXISTS_DO_NOT_OVERWRITE_RECEIPTS")
    output.mkdir(parents=True)
    paths=[output/"SHADOW_REPORT.json",output/"SHADOW_RECEIPTS.jsonl"]
    (paths[0]).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    with paths[1].open("x",encoding="utf-8") as stream:
        for line in receipts:
            stream.write(json.dumps(line,sort_keys=True,default=str)+"\n")
    return paths


def main(argv=None):
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-jsonl",type=Path)
    group.add_argument("--synthetic-qa",action="store_true")
    p.add_argument("--output-dir",type=Path)
    opts=p.parse_args(argv)
    try:
        if opts.synthetic_qa:
            rows=synthetic_fixture()
            sha=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
            origin="SYNTHETIC_QA_NO_ALPHA"
        else:
            rows,sha=load_jsonl(opts.input_jsonl)
            origin="USER_FILE_ASSERTED_SOURCE_NOT_CUSTODY_VERIFIED"
        data=raw_market_bars(rows)
        engine=ShadowMotor(data)
        report=engine.run()
        report["input_origin"]=origin
        report["input_sha256"]=sha
        report["source_origin_automatically_verified"]=False
        report["external_signal_parity_verified"]=False
        report["independent_forward_edge_proven"]=False
        report["realized_live_trade_count"]=0
        report["broker_transport_present"]=False
        report["receipt_chain_consistent"]=True
        if opts.output_dir:
            save_immutable(opts.output_dir,report,engine.ledger)
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0
    except (Halt,ValueError,OSError,UnicodeError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED_NO_LIVE_GO",
                          "error_type":type(exc).__name__,
                          "reason":str(exc),"execution_authority":"NONE"}))
        return 2


if __name__=="__main__":
    sys.exit(main())
