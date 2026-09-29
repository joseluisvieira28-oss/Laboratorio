from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "cross_venue_diamond_replication_002_okx_shape_probe"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://www.okx.com/api/v5/public/market-data-history"
UA = "CROSS-VENUE-DIAMOND-REPLICATION-002 okx-history-shape/1.0"
MODULES = ("2", "3")
FILTERS = (
    ("INST_ID_LIST", {"instIdList": "AVAX-USDT-SWAP"}),
    ("INST_FAMILY_LIST", {"instFamilyList": "AVAX-USDT"}),
)

def ms(x: str) -> int:
    return int(datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp() * 1000)

def sha(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def clean(body):
    if not isinstance(body, dict):
        return {"body_type": type(body).__name__}
    out = {"code": body.get("code"), "msg": body.get("msg")}
    data = body.get("data")
    if isinstance(data, list):
        out["data_count"] = len(data)
        meta = []
        for row in data:
            if not isinstance(row, dict):
                meta.append({"row_type": type(row).__name__})
                continue
            keep = {}
            for k, v in row.items():
                lk = k.lower()
                if any(tok in lk for tok in (
                    "state", "status", "result", "inst", "family",
                    "date", "begin", "end", "module", "type", "name", "ts"
                )):
                    # File URLs/hrefs are intentionally excluded at this stage.
                    if "url" not in lk and "href" not in lk and "file" not in lk:
                        keep[k] = v
            meta.append(keep)
        out["metadata"] = meta
    return out

def call(module: str, extra: dict) -> dict:
    params = {
        "module": module,
        "instType": "SWAP",
        "dateAggrType": "monthly",
        "begin": ms("2025-01-01T00:00:00Z"),
        "end": ms("2025-02-01T00:00:00Z"),
        **extra,
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    rec = {"module": module, "request_filter": extra}
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            rec["http_status"] = r.status
            rec["body"] = clean(json.loads(r.read().decode("utf-8", "replace")))
    except urllib.error.HTTPError as e:
        rec["http_status"] = e.code
        raw = e.read().decode("utf-8", "replace")
        try:
            rec["body"] = clean(json.loads(raw))
        except Exception:
            rec["body_text"] = raw[:1000]
    except Exception as e:
        rec["transport_error"] = repr(e)
    return rec

def accepted(rec: dict) -> bool:
    body = rec.get("body") or {}
    return rec.get("http_status") == 200 and body.get("code") == "0" and int(body.get("data_count") or 0) > 0

def main() -> int:
    probes = []
    for label, filt in FILTERS:
        for module in MODULES:
            rec = {"filter_label": label, **call(module, filt)}
            rec["provider_accepted"] = accepted(rec)
            probes.append(rec)
            time.sleep(0.5)

    accepted_by_module = {}
    for module in MODULES:
        accepted_by_module[module] = [
            r["filter_label"] for r in probes
            if r["module"] == module and r["provider_accepted"]
        ]

    module3_ok = bool(accepted_by_module["3"])
    classification = (
        "OKX_HISTORICAL_EXPORT_REQUEST_ACCEPTED"
        if module3_ok
        else "OKX_FUNDING_SOURCE_BINDING_BLOCKED"
    )

    receipt = {
        "lab_id": "CROSS-VENUE-DIAMOND-REPLICATION-002",
        "candidate": "CED1D-0031-AVAX20-CONTINUATION-H1",
        "stage": "OKX_HISTORICAL_EXPORT_SHAPE_PROBE",
        "classification": classification,
        "outcome_blind": True,
        "archive_payload_opened": False,
        "signal_calculation_performed": False,
        "return_calculation_performed": False,
        "pnl_calculation_performed": False,
        "2026_plus_accessed": False,
        "frozen_window": ["2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z"],
        "accepted_filter_shapes_by_module": accepted_by_module,
        "probes": probes,
    }
    receipt["fingerprint"] = sha(receipt)
    p = OUT / "CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_HISTORICAL_EXPORT_SHAPE_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "classification": classification,
        "accepted_filter_shapes_by_module": accepted_by_module,
        "fingerprint": receipt["fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
