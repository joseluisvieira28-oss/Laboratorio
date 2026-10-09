#!/usr/bin/env python3
"""Verify 2026-10-02..09 restored MM-V1 evidence end-to-end; source-only.

Never analyzes future returns, event classifications, trades, PnL or exchange state.
Canonical 2026-10-09 archive NOT created from this as-of snapshot.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault

ROOT=Path(__file__).resolve().parent
FROM="2026-10-02"
THROUGH="2026-10-08"
ASOF="recovery/2026-10-09_ASOF_1100UTC_RAW_TVFP_RECEIPTS.jsonl"
DATES=[f"2026-10-{day:02d}" for day in range(2,9)]
EXPECTED={"2026-10-02":175,**{day:288 for day in DATES[1:]}}
EXPECTED_FIRST_MS=1790933100000 # 2026-10-02 09:25 UTC, validated against label at runtime
EXPECTED_ASOF_LAST_MS=1791543600000 # 2026-10-09 11:00 UTC
REQUIRED_BASELINE=2016

def check_one(day):
    dir=ROOT/"archive"/day
    manifest=json.loads((dir/f"{day}.manifest.json").read_text())
    raw=(dir/f"{day}.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest["corpus_sha256"]:
        raise AssertionError(f"{day}: corpus SHA256 mismatch")
    chain="0"*64
    closes=[]
    records=[]
    for line in raw.decode("utf-8").splitlines():
        rec=json.loads(line)
        if rec["trading_authority"]!="NONE" or rec["payload"]["lab_id"]!=vault.LAB_ID:
            raise AssertionError(f"{day}: sensor/trading mismatch")
        if rec["payload_sha256"]!=vault.payload_sha(rec["payload"]):
            raise AssertionError(f"{day}: payload digest mismatch")
        key=(f"{vault.LAB_ID}|{vault.SENSOR_VERSION}|"
             f"{vault.SYMBOL}|{vault.TIMEFRAME}|{rec['payload']['bar_close_ms']}")
        if rec["evidence_key"]!=key:
            raise AssertionError(f"{day}: evidence key mismatch")
        normalized={key_:val for key_,val in rec.items() if key_!="chain_sha256"}
        chain=hashlib.sha256(bytes.fromhex(chain)+vault.canonical_json(normalized)).hexdigest()
        if chain!=rec["chain_sha256"]:
            raise AssertionError(f"{day}: chain broken")
        closes.append(rec["payload"]["bar_close_ms"])
        records.append(rec)
    if len(records)!=manifest["unique_receipts"] or len(records)!=EXPECTED[day]:
        raise AssertionError(f"{day}: sample mismatch")
    if chain!=manifest["terminal_chain_sha256"]:
        raise AssertionError(f"{day}: terminal chain SHA mismatch")
    if manifest["missing_slots"]!=0 or any(b-a!=vault.BAR_MS for a,b in zip(closes,closes[1:])):
        raise AssertionError(f"{day}: unexplained continuity gap")
    if manifest["first_bar_close_ms"]!=closes[0] or manifest["last_bar_close_ms"]!=closes[-1]:
        raise AssertionError(f"{day}: wrong manifest boundaries")
    return closes

def run():
    closes=[]
    manifest_states=[]
    for day in DATES:
        vals=check_one(day)
        closes.extend(vals)
        manifest_states.append({"day":day,"verified":len(vals),"first":vals[0],"last":vals[-1]})
    asof=vault.load_input([ROOT/ASOF])
    asof,stats=vault.deduplicate(asof)
    ts=[r["payload"]["bar_close_ms"] for r in asof]
    if len(ts)!=133 or ts[-1]!=EXPECTED_ASOF_LAST_MS or len(ts)!=len(set(ts)):
        raise AssertionError("2026-10-09 as-of mismatch")
    if ts[0]!=1791504000000 or any(b-a!=vault.BAR_MS for a,b in zip(ts,ts[1:])):
        raise AssertionError("2026-10-09 partial integrity mismatch")
    closes.extend(ts)
    if closes[0]!=EXPECTED_FIRST_MS:
        raise AssertionError("2026-10-02 incomplete-day boundary incorrect")
    if any(b-a!=vault.BAR_MS for a,b in zip(closes,closes[1:])):
        raise AssertionError("CROSS-DAY GAP — fail closed")
    if len(closes)!=2036 or len(closes)<=REQUIRED_BASELINE:
        raise AssertionError("BASELINE_UPPER_BOUND_WRONG")
    receipt={
        "state":"SOURCE_ONLY_CONTIGUOUS_2016_CANDLE_POTENTIAL",
        "lab_id":"ABSORPTION-FAILED-AUCTION-001",
        "sensor_lab":vault.LAB_ID,
        "source":"authentic Render TVFP_RECEIPT, GitHub immutable daily archives + partial as-of",
        "complete_days":6,
        "partial_oct02_count":175,
        "partial_oct09_count":133,
        "total_verified_contiguous":len(closes),
        "first_bar_close_ms":closes[0],
        "last_bar_close_ms":closes[-1],
        "candidate_bars_with_2016_causal_predecessors":len(closes)-REQUIRED_BASELINE,
        "first_candidate_bar_close_ms":closes[REQUIRED_BASELINE],
        "required_prior_bars":REQUIRED_BASELINE,
        "archive_manifests":manifest_states,
        "oct02_missing_earlier_receipts":"UNRECOVERED — do not manufacture or assume availability",
        "oct01_through_oct02_gap":"PRESERVED; 2016 sequential source baseline resets from Oct02 09:25",
        "oct09_archive":"AS_OF_NON_FINAL — full-day manifest prohibited until UTC day completes",
        "binance_canonical_aggtrade_flow_join_verified":False,
        "primary_events_classified":False,
        "economic_outcomes_unlocked":False,
        "trading_authority":"NONE",
        "automatic_collector_restart_authorized":False,
        "interpretation":"2016 consecutive live footprint payloads exist; canonical aggTrades and unchanged event logic still require independent source gate. NOT a scientific or economic PASS."
    }
    output=ROOT/"recovery"/"TVFP_RESTORED_2026-10-02_TO_09_SOURCE_ONLY_RECEIPT.json"
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("archive_manifests",)},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(run())
