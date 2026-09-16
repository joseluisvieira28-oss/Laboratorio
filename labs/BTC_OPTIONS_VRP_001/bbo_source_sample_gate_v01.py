#!/usr/bin/env python3
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

AUTH = Path("labs/BTC_OPTIONS_VRP_001/BBO_SOURCE_RECON_AUTHORITY_V0.1.json")
OUT = Path("artifacts/btc_options_vrp_bbo_source_sample_gate_v01")
OUT.mkdir(parents=True, exist_ok=True)
META_URL = "https://api.tardis.dev/v1/exchanges/deribit"
BASE = "https://datasets.tardis.dev/v1/deribit"
UA = "SRC-Crypto-Lab/1.0"


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest(), int(r.status)


def probe_prefix(url, n=2, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes=0-{n-1}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read(n)
            return {
                "url": url,
                "status": int(r.status),
                "prefix_hex": b.hex(),
                "content_type": r.headers.get("Content-Type"),
                "content_range": r.headers.get("Content-Range"),
                "content_length": r.headers.get("Content-Length"),
                "gzip_magic": b[:2] == b"\x1f\x8b",
                "error": None,
            }
    except urllib.error.HTTPError as e:
        body = e.read(256)
        return {
            "url": url,
            "status": int(e.code),
            "prefix_hex": body[:n].hex(),
            "content_type": e.headers.get("Content-Type") if e.headers else None,
            "content_range": e.headers.get("Content-Range") if e.headers else None,
            "content_length": e.headers.get("Content-Length") if e.headers else None,
            "gzip_magic": False,
            "error": f"HTTPError:{e.code}",
        }
    except Exception as e:
        return {
            "url": url,
            "status": None,
            "prefix_hex": "",
            "content_type": None,
            "content_range": None,
            "content_length": None,
            "gzip_magic": False,
            "error": repr(e),
        }


def url_for(data_type, day):
    y, m, d = day.split("-")
    return f"{BASE}/{data_type}/{y}/{m}/{d}/OPTIONS.csv.gz"


def find_options_group(meta):
    datasets = meta.get("datasets", {}) if isinstance(meta, dict) else {}
    symbols = datasets.get("symbols", []) if isinstance(datasets, dict) else []
    for row in symbols:
        if isinstance(row, dict) and str(row.get("id", "")).upper() == "OPTIONS":
            return row
    return None


auth = json.loads(AUTH.read_text(encoding="utf-8"))
assert auth["source_mve_id"] == "OVRP-EXEC-BBO-001-SOURCE"
assert auth["outcomes_authorized"] is False
assert auth["access_2025_authorized"] is False
assert auth["access_2026_authorized"] is False
assert auth["live_trading_authorized"] is False
assert auth["exchange_mutation_authorized"] is False
assert auth["merge_to_main_authorized"] is False

result = {
    "lab_id": auth["lab_id"],
    "source_mve_id": auth["source_mve_id"],
    "classification": None,
    "metadata": None,
    "sample_probes": [],
    "nonfree_probe": None,
    "access_2025": False,
    "access_2026": False,
    "outcomes_opened": False,
    "live_trading": False,
    "exchange_mutation": False,
    "merge_to_main": False,
}

try:
    meta, meta_sha, meta_status = fetch_json(META_URL)
    group = find_options_group(meta)
    data_types = sorted(group.get("dataTypes", [])) if isinstance(group, dict) else []
    required = ["quotes", "options_chain", "incremental_book_L2"]
    result["metadata"] = {
        "status": meta_status,
        "sha256": meta_sha,
        "options_group_found": group is not None,
        "data_types": data_types,
        "required_present": {k: k in data_types for k in required},
        "available_since": group.get("availableSince") if isinstance(group, dict) else None,
        "available_to": group.get("availableTo") if isinstance(group, dict) else None,
    }
except Exception as e:
    result["metadata"] = {"error": repr(e), "options_group_found": False, "required_present": {}}

for day in auth["sample_dates"]:
    assert not day.startswith("2025-") and not day.startswith("2026-")
    day_result = {"date": day, "datasets": {}}
    for data_type in ("quotes", "options_chain", "incremental_book_L2"):
        day_result["datasets"][data_type] = probe_prefix(url_for(data_type, day))
    result["sample_probes"].append(day_result)

nonfree_day = auth["nonfree_probe_date"]
assert not nonfree_day.startswith("2025-") and not nonfree_day.startswith("2026-")
result["nonfree_probe"] = probe_prefix(url_for("quotes", nonfree_day))

meta_ok = bool(result["metadata"].get("options_group_found")) and all(
    result["metadata"].get("required_present", {}).get(k, False)
    for k in ("quotes", "options_chain", "incremental_book_L2")
)
all_samples_ok = all(
    all(v.get("status") in (200, 206) and v.get("gzip_magic") for v in row["datasets"].values())
    for row in result["sample_probes"]
)
nonfree_status = result["nonfree_probe"].get("status")

if meta_ok and all_samples_ok:
    if nonfree_status in (401, 402, 403):
        result["classification"] = "SOURCE_SAMPLE_GATE_PASS_FULL_HISTORY_ACCESS_REQUIRED"
    elif nonfree_status in (200, 206):
        result["classification"] = "SOURCE_SAMPLE_GATE_PASS_ANONYMOUS_NONFIRST_DAY_AVAILABLE"
    else:
        result["classification"] = "SOURCE_SAMPLE_GATE_PASS_NONFIRST_ACCESS_INDETERMINATE"
elif not meta_ok:
    result["classification"] = "SOURCE_SCHEMA_NOT_PROVEN"
else:
    result["classification"] = "SOURCE_SAMPLE_ACCESS_BLOCKED_OR_INCOMPLETE"

result["sample_gate_pass"] = result["classification"].startswith("SOURCE_SAMPLE_GATE_PASS")
result["full_history_anonymous"] = nonfree_status in (200, 206)
result["full_history_purchase_authorized"] = False
result["strategy_outcomes_authorized"] = False

(OUT / "source_sample_gate_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
manifest = {
    "authority_sha256": hashlib.sha256(AUTH.read_bytes()).hexdigest(),
    "result_sha256": hashlib.sha256((OUT / "source_sample_gate_result.json").read_bytes()).hexdigest(),
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
