#!/usr/bin/env python3
"""Pure synthetic CPI future-source-timestamp diagnostic against PINNED PR188 source.
No exchange calls, economic outcomes, API keys, accounts or orders.
"""
import importlib, json, sys
from pathlib import Path

SHOCK=Path("shock_source/research/asymmetric_shock_breakout")
if not (SHOCK/"public_bbo_probe.py").exists():
 raise SystemExit("PINNED_UPSTREAM_CPI_SOURCE_MISSING_FAIL_CLOSED")
sys.path.insert(0,str(SHOCK.resolve()))
from public_bbo_probe import check, MAX_AGE_MS, SYMBOLS
from cpi_public_source_capture import START_MS,T0_MS,SLOTS,INTERVAL_MS,MAX_DRIFT_MS

assert SYMBOLS==("BTC_USDT","SOL_USDT")
assert START_MS==1791980940000 and T0_MS==1791981000000
assert INTERVAL_MS==5000 and SLOTS==49 and MAX_DRIFT_MS==2000
assert MAX_AGE_MS==10000
obs=T0_MS
def book(ts):
 return {"success":True,"code":0,
  "data":{"timestamp":ts,"version":12345,
    "bids":[[80000.,2.]],"asks":[[80001.,2.]]}}
assert check(book(obs-2000),obs)["exchange_timestamp_ms"]==obs-2000
future_4sec_accepted=False
try:
 out=check(book(obs+4000),obs)
 future_4sec_accepted=(out["exchange_timestamp_ms"]==obs+4000)
except ValueError:
 pass
# This is a FALSIFICATION diagnostic, so success means reproduce the exact
# SOURCE-SAFETY GAP and preserve block until pre-event correction is proven.
if not future_4sec_accepted:
 status="NOT_REPRODUCED__UPSTREAM_CODE_MAY_HAVE_CHANGED"
else:
 status="REPRODUCED_4S_FUTURE_QUOTE_ACCEPTED_BEYOND_FROZEN_2S_CLOCK"
receipt={"status":status,"original_source_commit_pinned":
  "0f7d4d8e0edd38dd082b213f599e24765a7ed95e",
  "source_only":True,"synthetic_no_network":True,
  "future_quote_4s_accepted":future_4sec_accepted,
  "frozen_tolerance_ms":MAX_DRIFT_MS,
  "collector_5s_future_tolerance_ms":5000,
  "no_performance_test":True,"trading_authority":"NONE"}
Path("audits").mkdir(exist_ok=True)
Path("audits/CPI_20261014_SYNTHETIC_TIMESTAMP_RECEIPT.json").write_text(
  json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("CPI_PRE_EVENT_SOURCE_PROVENANCE_QA",json.dumps(receipt,sort_keys=True))
if not future_4sec_accepted:
 # Do not accidentally claim freeze-safe improvement without reading the code.
 raise SystemExit("SOURCE_CHANGED_READ_ONLY_REVIEW_REQUIRED")
