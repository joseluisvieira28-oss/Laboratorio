#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

BASES = [
    ("LAB_PROXY", "https://lab.ethpandaops.io/api/v1/mainnet"),
    ("DIRECT_CBT_API", "https://cbt-api-mainnet.primary.production.platform.ethpandaops.io/api/v1"),
]

CONTROLS = [
    {"date":"2025-02-24","epoch":347738,"unix":1740355415,"pending_queued":0,"active_exiting":5,"net_queue":-5},
    {"date":"2025-03-02","epoch":349088,"unix":1740873815,"pending_queued":0,"active_exiting":0,"net_queue":0},
    {"date":"2025-10-17","epoch":400613,"unix":1760659415,"pending_queued":48,"active_exiting":55209,"net_queue":-55161},
]

def get_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent":"crypto-lab-source-probe/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return r.status, dict(r.headers), raw, json.loads(raw)

def qurl(base, table, params):
    return base + "/" + table + "?" + urllib.parse.urlencode(params)

receipt = {
    "lab_id":"ETH-STAKING-FLOW-001",
    "stage":"V3_STAGEA_CBT_TRANSITION_SOURCE_PROBE_V0_1_5",
    "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
    "transports":[],
    "controls":CONTROLS,
    "signal_evaluated":False,
    "market_prices_opened":False,
    "returns_opened":False,
    "pnl_opened":False,
    "source_after_2026_08_31_opened":False,
    "mutation":False,
}

for name, base in BASES:
    tr = {"name":name,"base":base,"transition_probe":None,"daily_control_diagnostics":[],"errors":[]}
    try:
        url = qurl(base, "dim_validator_status", {
            "validator_index_gte":0,
            "epoch_lte":401063,
            "page_size":3,
            "order_by":"validator_index,epoch",
        })
        status, headers, raw, obj = get_json(url)
        keys = sorted(obj.keys()) if isinstance(obj, dict) else []
        rows = []
        token = None
        if isinstance(obj, dict):
            rows = obj.get("dim_validator_status", obj.get("items", []))
            token = obj.get("next_page_token")
        tr["transition_probe"] = {
            "url":url,
            "http_status":status,
            "body_sha256":hashlib.sha256(raw).hexdigest(),
            "top_level_keys":keys,
            "row_count":len(rows) if isinstance(rows,list) else None,
            "first_rows":rows[:3] if isinstance(rows,list) else None,
            "next_page_token_present":bool(token),
        }
    except Exception as e:
        tr["errors"].append({"scope":"transition_probe","error":repr(e)})

    for c in CONTROLS:
        diag={"date":c["date"],"status_rows":{}}
        for st in ("pending_queued","active_exiting"):
            try:
                url = qurl(base, "fct_validator_count_by_entity_by_status_daily", {
                    "day_start_date_eq":c["date"],
                    "status_eq":st,
                    "page_size":10000,
                })
                status, headers, raw, obj = get_json(url)
                rows = obj.get("fct_validator_count_by_entity_by_status_daily", obj.get("items", [])) if isinstance(obj,dict) else []
                total = sum(int(x.get("validator_count",0)) for x in rows) if isinstance(rows,list) else None
                diag["status_rows"][st]={
                    "http_status":status,
                    "row_count":len(rows) if isinstance(rows,list) else None,
                    "summed_validator_count":total,
                    "body_sha256":hashlib.sha256(raw).hexdigest(),
                }
            except Exception as e:
                diag["status_rows"][st]={"error":repr(e)}
        tr["daily_control_diagnostics"].append(diag)
    receipt["transports"].append(tr)
    time.sleep(1)

usable = []
for tr in receipt["transports"]:
    p=tr.get("transition_probe") or {}
    if p.get("http_status")==200 and p.get("row_count",0)>0 and p.get("top_level_keys"):
        usable.append(tr["name"])

receipt["usable_transition_transports"]=usable
receipt["classification"]="CBT_TRANSITION_API_PROBE_PASS" if usable else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"

Path("artifacts").mkdir(exist_ok=True)
out=Path("artifacts/ETH_STAKING_FLOW_001_CBT_TRANSITION_SOURCE_PROBE_V0_1_5.json")
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
raise SystemExit(0 if usable else 2)
