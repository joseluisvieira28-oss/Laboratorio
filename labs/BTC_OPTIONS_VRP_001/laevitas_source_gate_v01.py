#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AUTH = Path("labs/BTC_OPTIONS_VRP_001/LAEVITAS_SOURCE_AUTHORITY_V0.1.json")
OUT = Path("artifacts/btc_options_vrp_laevitas_source_gate_v01")
OUT.mkdir(parents=True, exist_ok=True)
UA = "SRC-Crypto-Lab-Laevitas-SourceGate/0.1"


def get_raw(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return int(r.status), dict(r.headers.items()), raw, None
    except urllib.error.HTTPError as e:
        raw = e.read(4096)
        return int(e.code), dict(e.headers.items()) if e.headers else {}, raw, f"HTTPError:{e.code}"
    except Exception as e:
        return None, {}, b"", repr(e)


def public_json(base, path):
    status, headers, raw, error = get_raw(base + path)
    obj = None
    if raw:
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception:
            pass
    return {
        "path": path,
        "status": status,
        "headers": {k.lower(): v for k, v in headers.items() if k.lower().startswith("x-") or k.lower() in ("content-type", "content-length")},
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "json": obj,
        "error": error,
    }


def path_get_spec(openapi, path):
    return ((openapi.get("paths") or {}).get(path) or {}).get("get")


def param_names(op):
    names = []
    for p in (op or {}).get("parameters", []):
        if isinstance(p, dict):
            names.append({"name": p.get("name"), "required": bool(p.get("required")), "in": p.get("in"), "schema": p.get("schema")})
    return names


def deref(root, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return None
    cur = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def collect_properties(root, node, out=None, depth=0, seen_refs=None):
    if out is None:
        out = set()
    if seen_refs is None:
        seen_refs = set()
    if depth > 20:
        return out
    if isinstance(node, list):
        for item in node:
            collect_properties(root, item, out, depth + 1, seen_refs)
        return out
    if not isinstance(node, dict):
        return out
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/") and ref not in seen_refs:
        seen_refs.add(ref)
        target = deref(root, ref)
        if target is not None:
            collect_properties(root, target, out, depth + 1, seen_refs)
    props = node.get("properties")
    if isinstance(props, dict):
        out.update(props.keys())
    for key, value in node.items():
        if key == "$ref":
            continue
        if isinstance(value, (dict, list)):
            collect_properties(root, value, out, depth + 1, seen_refs)
    return out


def collect_documented_keys(root, node, out=None, depth=0, seen_refs=None):
    """Collect literal field names from schema AND inline OpenAPI examples.

    Laevitas documents some 200 responses as inline examples rather than a typed
    row schema. This engineering-only reader is scoped to the endpoint's own
    200-response content; it does not alter source, dates, required fields or any
    scientific/outcome/payment firewall.
    """
    if out is None:
        out = set()
    if seen_refs is None:
        seen_refs = set()
    if depth > 24:
        return out
    if isinstance(node, list):
        for item in node:
            collect_documented_keys(root, item, out, depth + 1, seen_refs)
        return out
    if not isinstance(node, dict):
        return out
    out.update(str(k) for k in node.keys())
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/") and ref not in seen_refs:
        seen_refs.add(ref)
        target = deref(root, ref)
        if target is not None:
            collect_documented_keys(root, target, out, depth + 1, seen_refs)
    for key, value in node.items():
        if key == "$ref":
            continue
        if isinstance(value, (dict, list)):
            collect_documented_keys(root, value, out, depth + 1, seen_refs)
    return out


def response_content(openapi, op):
    if not op:
        return {}
    resp = (op.get("responses") or {}).get("200") or {}
    return (resp.get("content") or {}).get("application/json") or {}


def response_properties(openapi, op):
    content = response_content(openapi, op)
    return collect_properties(openapi, content.get("schema") or {})


def response_documented_fields(openapi, op):
    return collect_documented_keys(openapi, response_content(openapi, op))


def build_query(op, when_iso):
    when = dt.datetime.fromisoformat(when_iso.replace("Z", "+00:00"))
    end = when + dt.timedelta(minutes=1)
    known = {
        "exchange": "deribit",
        "currency": "BTC",
        "base_currency": "BTC",
        "underlying": "BTC",
        "resolution": "1m",
        "date": when_iso,
        "timestamp": when_iso,
        "start": when_iso,
        "end": end.isoformat().replace("+00:00", "Z"),
        "limit": "10",
    }
    q = {}
    unknown_required = []
    for p in param_names(op):
        name = p.get("name")
        if p.get("in") != "query" or not name:
            continue
        if name in known:
            q[name] = known[name]
        elif p.get("required"):
            unknown_required.append(name)
    return q, unknown_required


def probe_endpoint(base, path, op, when_iso):
    q, unknown = build_query(op, when_iso)
    if unknown:
        return {"path": path, "date": when_iso, "skipped": True, "unknown_required_parameters": unknown, "query": q}
    url = base + path + "?" + urllib.parse.urlencode(q)
    status, headers, raw, error = get_raw(url)
    body_prefix = raw[:512].decode("utf-8", errors="replace") if raw else ""
    payload = None
    if raw and status == 200:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            pass
    return {
        "path": path,
        "date": when_iso,
        "query": q,
        "status": status,
        "headers": {k.lower(): v for k, v in headers.items() if k.lower().startswith("x-") or k.lower() in ("content-type", "content-length")},
        "body_prefix": body_prefix,
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "json_payload": payload,
        "error": error,
        "payment_signature_sent": False,
        "api_key_sent": False,
    }


def recursively_has_quote_fields(obj, required):
    if isinstance(obj, dict):
        keys = set(obj.keys())
        if set(required).issubset(keys):
            return True
        return any(recursively_has_quote_fields(v, required) for v in obj.values())
    if isinstance(obj, list):
        return any(recursively_has_quote_fields(v, required) for v in obj[:100])
    return False


auth = json.loads(AUTH.read_text(encoding="utf-8"))
assert auth["source_mve_id"] == "OVRP-EXEC-BBO-LAEVITAS-001-SOURCE"
for flag in ("outcomes_authorized", "strategy_pnl_authorized", "payment_authorized", "wallet_signature_authorized", "api_subscription_authorized", "access_2025_authorized", "access_2026_authorized", "live_trading_authorized", "exchange_mutation_authorized", "merge_to_main_authorized"):
    assert auth[flag] is False
for d in auth["probe_dates"]:
    assert not d.startswith("2025-") and not d.startswith("2026-")

base = auth["base_url"].rstrip("/")
openapi_rec = public_json(base, "/openapi.json")
x402_rec = public_json(base, "/.well-known/x402")
openapi = openapi_rec.get("json") if isinstance(openapi_rec.get("json"), dict) else {}

required_paths = auth["required_paths"]
path_info = {}
for path in required_paths:
    op = path_get_spec(openapi, path)
    path_info[path] = {
        "present": op is not None,
        "parameters": param_names(op),
        "response_properties": sorted(response_properties(openapi, op)),
        "response_documented_fields": sorted(response_documented_fields(openapi, op)),
    }

probes = []
for d in auth["probe_dates"]:
    for path in ("/api/v1/options/snapshot", "/api/v1/options/level1"):
        op = path_get_spec(openapi, path)
        if op:
            probes.append(probe_endpoint(base, path, op, d))

required_fields = set(auth["required_quote_fields"])
level1_fields = set(path_info.get("/api/v1/options/level1", {}).get("response_documented_fields", []))
snapshot_fields = set(path_info.get("/api/v1/options/snapshot", {}).get("response_documented_fields", []))
schema_quote_fields_proven = required_fields.issubset(level1_fields) or required_fields.issubset(snapshot_fields)
historical_selector_proven = False
for path in ("/api/v1/options/snapshot", "/api/v1/options/level1"):
    names = {p.get("name") for p in path_info.get(path, {}).get("parameters", [])}
    if names.intersection({"date", "timestamp", "start"}):
        historical_selector_proven = True

actual_historical_payload_pass = any(
    p.get("status") == 200 and recursively_has_quote_fields(p.get("json_payload"), required_fields)
    for p in probes
)
payment_gate_seen = any(p.get("status") == 402 for p in probes)
auth_gate_seen = any(p.get("status") == 401 for p in probes)
query_schema_issue = any(p.get("skipped") or p.get("status") == 400 for p in probes)
all_paths_present = all(path_info.get(p, {}).get("present") for p in required_paths)
public_discovery_ok = openapi_rec.get("status") == 200 and x402_rec.get("status") == 200

if not all_paths_present or not schema_quote_fields_proven or not historical_selector_proven:
    classification = "SOURCE_SCHEMA_INSUFFICIENT"
elif actual_historical_payload_pass:
    classification = "SOURCE_DATA_PASS"
elif public_discovery_ok and (payment_gate_seen or auth_gate_seen):
    classification = "SOURCE_PAYMENT_ACCESS_REQUIRED_COVERAGE_UNPROVEN"
elif query_schema_issue:
    classification = "SOURCE_QUERY_SCHEMA_REMEDIATION_REQUIRED"
else:
    classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"

result = {
    "lab_id": auth["lab_id"],
    "source_mve_id": auth["source_mve_id"],
    "classification": classification,
    "technical_remediation_of_runs": [35077276351, 35077515821],
    "scientific_rules_changed": False,
    "public_openapi": {k: v for k, v in openapi_rec.items() if k != "json"},
    "public_x402": {k: v for k, v in x402_rec.items() if k != "json"},
    "path_info": path_info,
    "historical_probes": probes,
    "all_required_paths_present": all_paths_present,
    "schema_quote_fields_proven": schema_quote_fields_proven,
    "historical_selector_proven": historical_selector_proven,
    "actual_historical_payload_pass": actual_historical_payload_pass,
    "payment_gate_seen": payment_gate_seen,
    "auth_gate_seen": auth_gate_seen,
    "payment_authorized": False,
    "payment_executed": False,
    "wallet_signature_executed": False,
    "api_subscription_executed": False,
    "outcomes_opened": False,
    "strategy_pnl_opened": False,
    "access_2025": False,
    "access_2026": False,
    "live_trading": False,
    "exchange_mutation": False,
    "merge_to_main": False,
}

result_path = OUT / "laevitas_source_gate_result.json"
result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
manifest = {
    "authority_sha256": hashlib.sha256(AUTH.read_bytes()).hexdigest(),
    "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
