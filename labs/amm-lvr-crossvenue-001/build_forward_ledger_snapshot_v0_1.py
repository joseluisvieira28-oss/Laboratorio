from __future__ import annotations

import hashlib
import json
import os
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
EVID = ROOT / "evidence"
LEDGER = ROOT / "forward_ledger"
LEDGER.mkdir(parents=True, exist_ok=True)

RAW = EVID / "forward_protocol_capture_v0_1.json"
RAW_RECEIPT = EVID / "forward_protocol_capture_v0_1_receipt.json"
HEADROOM = EVID / "headroom_evaluation_v0_1.json"
HEADROOM_SUMMARY = EVID / "headroom_evaluation_v0_1_summary.json"
TRIGGER = ROOT / "DAILY_CAPTURE_TRIGGER.txt"

def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def trigger_fields():
    out={}
    for line in TRIGGER.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            out[k.strip()]=v.strip()
    return out

raw=load(RAW)
receipt=load(RAW_RECEIPT)
rows=load(HEADROOM)
summary=load(HEADROOM_SUMMARY)
trig=trigger_fields()

tx_keys=sorted({str(x.get("tx_hash","")).lower() for x in raw if x.get("tx_hash")})
swap_keys=set()
dates=set()
for ev in raw:
    ts=ev.get("block_timestamp")
    if ts is not None:
        try:
            dates.add(datetime.fromtimestamp(int(ts),tz=timezone.utc).date().isoformat())
        except Exception:
            pass
    tx=str(ev.get("tx_hash","")).lower()
    for sw in ev.get("swaps",[]) or []:
        swap_keys.add("|".join([
            tx,
            str(sw.get("pool","")).lower(),
            str(sw.get("log_index","")),
        ]))

state_keys=set()
for r in rows:
    if r.get("status")!="EXECUTABLE":
        continue
    state_keys.add("|".join([
        str(r.get("block_number","")),
        str(r.get("pool","")).lower(),
        str(r.get("notional_usdt","")),
    ]))

snapshot={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "protocol":"FORWARD_ECONOMIC_PROTOCOL_V0.1",
    "snapshot_version":"V0.1",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "github_run_id":os.getenv("GITHUB_RUN_ID"),
    "github_sha":os.getenv("GITHUB_SHA"),
    "trigger":trig,
    "source_digests":{
        "raw_capture_sha256":sha256(RAW),
        "raw_receipt_sha256":sha256(RAW_RECEIPT),
        "headroom_rows_sha256":sha256(HEADROOM),
        "headroom_summary_sha256":sha256(HEADROOM_SUMMARY),
    },
    "raw_candidate_population":{
        "transaction_count":len(tx_keys),
        "swap_key_count":len(swap_keys),
        "utc_dates":sorted(dates),
        "transaction_keys":tx_keys,
        "swap_keys":sorted(swap_keys),
    },
    "headroom_population":{
        "executable_state_notional_key_count":len(state_keys),
        "state_notional_keys":sorted(state_keys),
        "by_notional_latency":summary.get("by_notional_latency",{}),
    },
    "source_receipt":{
        "captured_transaction_events":receipt.get("captured_transaction_events"),
        "captured_swap_logs":receipt.get("captured_swap_logs"),
        "trace_pass_events":receipt.get("trace_pass_events"),
        "latency_depth_coverage":receipt.get("latency_depth_coverage"),
        "runtime_errors":receipt.get("websocket_or_chain_errors"),
    },
    "scientific_accounting":{
        "eligible_event_count_claimed":0,
        "discovery_event_credit_claimed":0,
        "minimum_eligible_events":500,
        "minimum_utc_days":14,
        "full_cost_pnl_computed":False,
        "accessibility":"UNPROVEN",
        "scientific_verdict":"NOT_OPEN",
        "note":"Raw candidates and headroom states are persisted for deduplication only. They are not converted into eligible Discovery events until every frozen inclusion/cost requirement is satisfied."
    }
}

run_id=os.getenv("GITHUB_RUN_ID") or "local"
date=(trig.get("utc_date") or (sorted(dates)[0] if dates else "unknown"))
seq=trig.get("run_seq","na")
path=LEDGER / f"{date}__seq-{seq}__run-{run_id}.json"
path.write_text(json.dumps(snapshot,indent=2,sort_keys=True),encoding="utf-8")
(EVID/"forward_ledger_snapshot_v0_1.json").write_text(json.dumps(snapshot,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps({
    "ledger_path":str(path),
    "raw_transactions":len(tx_keys),
    "swap_keys":len(swap_keys),
    "state_notional_keys":len(state_keys),
    "utc_dates":sorted(dates),
    "eligible_event_count_claimed":0,
    "scientific_verdict":"NOT_OPEN"
},indent=2,sort_keys=True))
