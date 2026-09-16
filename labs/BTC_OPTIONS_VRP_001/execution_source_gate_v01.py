#!/usr/bin/env python3
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LAB = "BTC-OPTIONS-VRP-001"
GATE = "OVRP-EXEC-ATM30-SOURCE-001"
AUTH_PATH = Path("labs/BTC_OPTIONS_VRP_001/EXECUTION_SOURCE_AUTHORITY_V0.1.json")
OUT = Path("artifacts/btc_options_vrp_execution_source_v01")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://history.deribit.com/api/v2/public"
PROTECTED_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def iso_to_ms(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)


def iso_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def get_json(endpoint: str, params: dict, timeout: int = 60):
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "SRC-Crypto-Lab/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    sha = hashlib.sha256(raw).hexdigest()
    obj = json.loads(raw.decode("utf-8"))
    if "error" in obj:
        raise RuntimeError(f"Deribit API error on {endpoint}: {obj['error']}")
    return obj.get("result"), sha


def trade_list(result):
    if isinstance(result, dict):
        trades = result.get("trades")
        if isinstance(trades, list):
            return trades
    if isinstance(result, list):
        return result
    raise RuntimeError("Unexpected Deribit historical trade response shape")


def classify_exception(exc: Exception) -> str:
    text = repr(exc).lower()
    if any(x in text for x in ["401", "403", "unauthorized", "forbidden", "api key", "authentication"]):
        return "SOURCE_ACCESS_BLOCKED"
    return "SOURCE_ACQUISITION_TECHNICAL_FAILURE"


auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
assert auth["source_feasibility_only"] is True
assert auth["strategy_pnl_authorized"] is False
assert auth["trade_returns_authorized"] is False
assert auth["directional_btc_returns_authorized"] is False
assert auth["parameter_tuning_authorized"] is False
assert auth["access_2025_authorized"] is False
assert auth["access_2026_authorized"] is False
assert auth["live_trading_authorized"] is False
assert auth["exchange_mutation_authorized"] is False
assert auth["merge_to_main_authorized"] is False
assert auth["unbounded_instrument_catalog_allowed"] is False
assert auth["delivery_price_source_required"] is False

required_fields = list(auth["required_option_trade_fields"])
min_coverage = float(auth["minimum_sampled_field_coverage"])

result = {
    "lab_id": LAB,
    "source_gate_id": GATE,
    "execution_mve_family_id": auth["execution_mve_family_id"],
    "classification": None,
    "access_2025": False,
    "access_2026": False,
    "strategy_pnl_opened": False,
    "trade_returns_opened": False,
    "directional_btc_returns_opened": False,
    "economic_values_retained": False,
    "unbounded_instrument_catalog_called": False,
    "delivery_price_route_called": False,
    "option_probes": [],
    "perpetual_probes": [],
    "errors": [],
}
manifest = []
technical_failure = False
source_access_blocked = False
insufficient = False
protected_failure = False

for start_iso, end_iso in auth["fixed_probe_windows"]:
    start_ms, end_ms = iso_to_ms(start_iso), iso_to_ms(end_iso)
    if end_ms >= PROTECTED_MS:
        raise RuntimeError("Authority contains a protected-period probe")
    year = start_iso[:4]

    # Bounded historical BTC option tape probe. Economic values are never persisted or printed.
    try:
        params = {
            "currency": "BTC",
            "kind": "option",
            "start_timestamp": start_ms,
            "end_timestamp": end_ms,
            "count": 1000,
            "sorting": "asc",
            "include_old": "true",
        }
        payload, raw_sha = get_json("/get_last_trades_by_currency_and_time", params)
        trades = trade_list(payload)
        in_window = []
        for t in trades:
            ts = int(t.get("timestamp", -1))
            if ts >= PROTECTED_MS:
                result["access_2025"] = True
                protected_failure = True
            if start_ms <= ts <= end_ms:
                in_window.append(t)
        if not in_window:
            insufficient = True
            raise ValueError(f"No bounded BTC option trades returned for {year}")

        present = 0
        total_checks = len(in_window) * len(required_fields)
        for t in in_window:
            for k in required_fields:
                if k in t and t[k] is not None:
                    present += 1
        coverage = present / total_checks if total_checks else 0.0
        if coverage < min_coverage:
            insufficient = True

        instruments = sorted({str(t.get("instrument_name")) for t in in_window if t.get("instrument_name")})
        if not instruments:
            insufficient = True
            raise ValueError(f"No instrument identity found in option tape for {year}")
        selected = instruments[0]  # administrative deterministic choice; no prices/IV used

        md, md_sha = get_json("/get_instrument", {"instrument_name": selected})
        if not isinstance(md, dict):
            insufficient = True
            raise ValueError(f"Instrument metadata unavailable for {selected}")
        exp = int(md.get("expiration_timestamp", -1))
        creation = int(md.get("creation_timestamp", -1))
        if exp >= PROTECTED_MS:
            protected_failure = True
            result["access_2025"] = True
        metadata_pass = (
            md.get("kind") == "option"
            and md.get("option_type") in {"call", "put"}
            and md.get("strike") is not None
            and creation > 0
            and exp > 0
            and exp < PROTECTED_MS
        )
        if not metadata_pass:
            insufficient = True

        rec = {
            "year": int(year),
            "requested_start": start_iso,
            "requested_end": end_iso,
            "raw_payload_sha256": raw_sha,
            "record_count_in_window": len(in_window),
            "first_timestamp": iso_from_ms(min(int(t["timestamp"]) for t in in_window)),
            "last_timestamp": iso_from_ms(max(int(t["timestamp"]) for t in in_window)),
            "required_field_coverage": coverage,
            "selected_instrument": selected,
            "instrument_metadata_sha256": md_sha,
            "instrument_kind": md.get("kind"),
            "instrument_option_type": md.get("option_type"),
            "instrument_strike": md.get("strike"),
            "instrument_creation_timestamp": iso_from_ms(creation) if creation > 0 else None,
            "instrument_expiration_timestamp": iso_from_ms(exp) if exp > 0 else None,
            "metadata_pass": metadata_pass,
            "economic_values_retained": False,
        }
        result["option_probes"].append(rec)
        manifest.append({"source": "deribit_option_tape", **rec})
    except ValueError as e:
        result["errors"].append(f"OPTION_{year}:{e!r}")
    except Exception as e:
        cls = classify_exception(e)
        source_access_blocked |= cls == "SOURCE_ACCESS_BLOCKED"
        technical_failure |= cls == "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        result["errors"].append(f"OPTION_{year}:{e!r}")

    # Bounded historical same-venue BTC perpetual tape probe. Retain timestamps/hash only.
    try:
        params = {
            "instrument_name": "BTC-PERPETUAL",
            "start_timestamp": start_ms,
            "end_timestamp": end_ms,
            "count": 100,
            "sorting": "asc",
            "include_old": "true",
        }
        payload, raw_sha = get_json("/get_last_trades_by_instrument_and_time", params)
        trades = trade_list(payload)
        in_window = []
        for t in trades:
            ts = int(t.get("timestamp", -1))
            if ts >= PROTECTED_MS:
                result["access_2025"] = True
                protected_failure = True
            if start_ms <= ts <= end_ms:
                in_window.append(t)
        if not in_window:
            insufficient = True
            raise ValueError(f"No bounded BTC-PERPETUAL trades returned for {year}")
        rec = {
            "year": int(year),
            "requested_start": start_iso,
            "requested_end": end_iso,
            "raw_payload_sha256": raw_sha,
            "record_count_in_window": len(in_window),
            "first_timestamp": iso_from_ms(min(int(t["timestamp"]) for t in in_window)),
            "last_timestamp": iso_from_ms(max(int(t["timestamp"]) for t in in_window)),
            "economic_values_retained": False,
        }
        result["perpetual_probes"].append(rec)
        manifest.append({"source": "deribit_btc_perpetual_tape", **rec})
    except ValueError as e:
        result["errors"].append(f"PERP_{year}:{e!r}")
    except Exception as e:
        cls = classify_exception(e)
        source_access_blocked |= cls == "SOURCE_ACCESS_BLOCKED"
        technical_failure |= cls == "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        result["errors"].append(f"PERP_{year}:{e!r}")

if result["access_2025"] or result["access_2026"] or protected_failure:
    result["classification"] = "PROVENANCE_FAILURE"
elif source_access_blocked:
    result["classification"] = "SOURCE_ACCESS_BLOCKED"
elif technical_failure:
    result["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
else:
    option_years = {x["year"] for x in result["option_probes"] if x.get("metadata_pass") and x.get("required_field_coverage", 0) >= min_coverage}
    perp_years = {x["year"] for x in result["perpetual_probes"] if x.get("record_count_in_window", 0) > 0}
    required_years = {2021, 2022, 2023, 2024}
    if not insufficient and option_years == required_years and perp_years == required_years:
        result["classification"] = "SOURCE_DATA_PASS"
    else:
        result["classification"] = "SOURCE_DATA_INSUFFICIENT"

mb = ("\n".join(json.dumps(x, sort_keys=True, separators=(",", ":")) for x in manifest) + "\n").encode("utf-8")
(OUT / "source_manifest.jsonl").write_bytes(mb)
result["source_manifest_sha256"] = hashlib.sha256(mb).hexdigest()
result["source_manifest_records"] = len(manifest)
rb = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
(OUT / "source_gate_result.json").write_bytes(rb)
print(rb.decode("utf-8"))

# Source blockers are scientific outputs, not workflow failures. Only code/provenance assertions fail the job.
if result["classification"] == "PROVENANCE_FAILURE":
    sys.exit(2)
