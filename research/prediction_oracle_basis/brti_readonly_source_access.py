#!/usr/bin/env python3
"""POB-BRTI-READONLY-SOURCE-ACCESS-001.

Default/CI mode is SELF-TEST ONLY. No authenticated Kalshi request is made unless
--execute-authenticated is supplied AND an explicit activation sentinel is set.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request
from typing import Any

OUT = pathlib.Path("artifacts/prediction_oracle_basis/brti_readonly_source")
BASE = "https://external-api.kalshi.com"
PATH = "/trade-api/v2/cfbenchmarks/values"
QUERY = "?id=BRTI"
URL = BASE + PATH + QUERY
ACTIVATION = "POB_BRTI_READONLY_SOURCE_PROBE_V0.1"

IDENTITY_KEYS = {"id", "index", "index_id", "indexid", "symbol", "ticker", "name"}
TIMESTAMP_KEYS = {
    "time", "timestamp", "ts", "source_ts_ms", "received_at",
    "time_ms", "timestamp_ms",
}
VALUE_KEYS = {"value", "value_usd", "price", "index_value", "indexvalue"}
EMBEDDED_JSON_KEYS = {"data", "payload", "raw"}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def private_key_file(pem: str):
    tf = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    try:
        tf.write(pem)
        if not pem.endswith("\n"):
            tf.write("\n")
        tf.flush()
        tf.close()
        os.chmod(tf.name, stat.S_IRUSR | stat.S_IWUSR)
        return tf.name
    except Exception:
        try:
            os.unlink(tf.name)
        except Exception:
            pass
        raise


def rsa_pss_sha256_sign(private_pem: str, message: bytes) -> bytes:
    key_path = private_key_file(private_pem)
    try:
        proc = subprocess.run(
            [
                "openssl", "dgst", "-sha256",
                "-sign", key_path,
                "-sigopt", "rsa_padding_mode:pss",
                "-sigopt", "rsa_pss_saltlen:digest",
                "-sigopt", "rsa_mgf1_md:sha256",
            ],
            input=message,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError("openssl_sign_failed")
        return proc.stdout
    finally:
        try:
            os.unlink(key_path)
        except FileNotFoundError:
            pass


def finite_number_like(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return math.isfinite(float(v))
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return False
        try:
            return math.isfinite(float(s))
        except ValueError:
            return False
    return False


def observation_presence(x: Any, inherited_brti: bool = False) -> tuple[bool, bool, bool]:
    """Require BRTI identity, timestamp and finite value in the same observation branch.

    This deliberately rejects loose-document matches where an unrelated numeric field
    elsewhere in the response could accidentally satisfy the PASS contract.
    """
    if isinstance(x, list):
        for item in x:
            b, t, v = observation_presence(item, inherited_brti)
            if b and t and v:
                return True, True, True
        return False, False, False

    if not isinstance(x, dict):
        return False, False, False

    local_brti = inherited_brti

    # Some APIs encode the stream identity as a map key, e.g. {"BRTI": {...}}.
    for key, value in x.items():
        kl = str(key).lower()
        if kl == "brti":
            b, t, v = observation_presence(value, True)
            if b and t and v:
                return True, True, True
        if (
            kl in IDENTITY_KEYS
            and isinstance(value, str)
            and value.strip().upper() == "BRTI"
        ):
            local_brti = True

    timestamp_here = any(
        str(k).lower() in TIMESTAMP_KEYS and v not in (None, "")
        for k, v in x.items()
    )
    value_here = any(
        str(k).lower() in VALUE_KEYS and finite_number_like(v)
        for k, v in x.items()
    )

    if local_brti and timestamp_here and value_here:
        return True, True, True

    # Kalshi's documented CF Benchmarks websocket shape may carry the raw
    # benchmark observation as JSON text inside a data field. Support that
    # structural form without treating arbitrary strings as evidence.
    for key, value in x.items():
        if isinstance(value, str) and str(key).lower() in EMBEDDED_JSON_KEYS:
            s = value.strip()
            if s.startswith(("{", "[")):
                try:
                    nested = json.loads(s)
                except Exception:
                    nested = None
                if nested is not None:
                    b, t, v = observation_presence(nested, local_brti)
                    if b and t and v:
                        return True, True, True

    for value in x.values():
        if isinstance(value, (dict, list)):
            b, t, v = observation_presence(value, local_brti)
            if b and t and v:
                return True, True, True

    return False, False, False


def parser_self_test() -> dict[str, Any]:
    cases = [
        (
            "direct_numeric_string",
            {"id": "BRTI", "time": 1710000000323, "value": "68000.12"},
            True,
        ),
        (
            "wrapped_value_usd",
            {"payload": [{"index_id": "BRTI", "source_ts_ms": 1710000000323, "value_usd": "68000.12000000"}]},
            True,
        ),
        (
            "map_key_identity",
            {"latest_values": {"BRTI": {"time": 1710000000323, "value": "68000.12"}}},
            True,
        ),
        (
            "embedded_raw_observation",
            {
                "index_id": "BRTI",
                "received_at": 1710000000341,
                "data": '{"type":"value","id":"BRTI","time":1710000000323,"value":"68000.12"}',
            },
            True,
        ),
        (
            "reject_unrelated_numeric",
            {"id": "BRTI", "time": 1710000000323, "status_code": 200},
            False,
        ),
        (
            "reject_cross_record_value",
            {
                "payload": [
                    {"id": "ETHUSD_RTI", "time": 1710000000323, "value": "2000.0"},
                    {"id": "BRTI", "time": 1710000000323, "status": 200},
                ]
            },
            False,
        ),
        (
            "reject_nan",
            {"id": "BRTI", "time": 1710000000323, "value": "NaN"},
            False,
        ),
    ]

    results = []
    all_pass = True
    for name, fixture, expected in cases:
        b, t, v = observation_presence(fixture)
        observed = bool(b and t and v)
        ok = observed == expected
        all_pass = all_pass and ok
        results.append(
            {
                "name": name,
                "expected_pass": expected,
                "observed_pass": observed,
                "test_pass": ok,
            }
        )

    return {
        "classification": "PARSER_SELF_TEST_PASS" if all_pass else "PARSER_SELF_TEST_FAIL",
        "case_count": len(results),
        "cases": results,
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        priv = pathlib.Path(td) / "synthetic.key"
        pub = pathlib.Path(td) / "synthetic.pub"
        sig = pathlib.Path(td) / "sig.bin"

        g = subprocess.run(
            ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if g.returncode != 0:
            return {"classification": "SELF_TEST_FAIL", "stage": "keygen"}

        p = subprocess.run(
            ["openssl", "pkey", "-in", str(priv), "-pubout", "-out", str(pub)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if p.returncode != 0:
            return {"classification": "SELF_TEST_FAIL", "stage": "pubkey"}

        pem = priv.read_text(encoding="utf-8")
        timestamp = "1703123456789"
        message = f"{timestamp}GET{PATH}".encode("utf-8")
        signature = rsa_pss_sha256_sign(pem, message)
        sig.write_bytes(signature)

        v = subprocess.run(
            [
                "openssl", "dgst", "-sha256",
                "-verify", str(pub),
                "-signature", str(sig),
                "-sigopt", "rsa_padding_mode:pss",
                "-sigopt", "rsa_pss_saltlen:digest",
                "-sigopt", "rsa_mgf1_md:sha256",
            ],
            input=message,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        b64 = base64.b64encode(signature).decode("ascii")
        parser = parser_self_test()
        crypto_ok = v.returncode == 0 and base64.b64decode(b64) == signature
        all_ok = crypto_ok and parser["classification"] == "PARSER_SELF_TEST_PASS"
        return {
            "classification": "SELF_TEST_PASS" if all_ok else "SELF_TEST_FAIL",
            "signing_path": PATH,
            "query_excluded_from_signature": True,
            "algorithm": "RSA-PSS-SHA256",
            "signature_base64_roundtrip": base64.b64decode(b64) == signature,
            "parser": parser,
            "private_key_persisted": False,
            "real_credentials_used": False,
            "network_request_made": False,
        }


def key_paths(x: Any, prefix: str = "$", out: list[str] | None = None) -> list[str]:
    if out is None:
        out = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{prefix}.{k}"
            out.append(p)
            key_paths(v, p, out)
    elif isinstance(x, list):
        out.append(prefix + "[]")
        for item in x[:1]:
            key_paths(item, prefix + "[]", out)
    return out


def execute_authenticated() -> dict[str, Any]:
    if os.environ.get("POB_BRTI_EXPLICIT_ACTIVATION") != ACTIVATION:
        return {
            "classification": "BRTI_REAL_ACCESS_NOT_ACTIVATED",
            "network_request_made": False,
            "real_credentials_used": False,
        }

    key_id = os.environ.get("KALSHI_API_KEY_ID")
    private_pem = os.environ.get("KALSHI_PRIVATE_KEY_PEM")
    if not key_id or not private_pem:
        return {
            "classification": "BRTI_CREDENTIAL_ABSENT",
            "network_request_made": False,
            "real_credentials_used": False,
            "api_key_id_present": bool(key_id),
            "private_key_present": bool(private_pem),
        }

    ts = str(int(utc_now().timestamp() * 1000))
    msg = f"{ts}GET{PATH}".encode("utf-8")
    signature = base64.b64encode(rsa_pss_sha256_sign(private_pem, msg)).decode("ascii")

    headers = {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Accept": "application/json",
        "User-Agent": "CryptoLab-POB-BRTI-Source/0.1 research-only",
    }

    started = utc_now()
    req = urllib.request.Request(URL, headers=headers, method="GET")
    raw = b""
    status = None
    content_type = ""
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            status = int(resp.status)
            content_type = resp.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read() if exc.fp else b""
        content_type = exc.headers.get("content-type", "") if exc.headers else ""
    except Exception as exc:
        finished = utc_now()
        return {
            "classification": "BRTI_SOURCE_TECHNICAL_FAILURE",
            "network_request_made": True,
            "real_credentials_used": True,
            "request_started_utc": iso(started),
            "request_finished_utc": iso(finished),
            "error_type": type(exc).__name__,
        }

    finished = utc_now()
    obj = None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        pass

    brti, timestamp_present, numeric_present = observation_presence(obj)
    schema_paths = sorted(set(key_paths(obj)))[:200] if obj is not None else []

    if status in (401, 403):
        classification = "BRTI_AUTH_OR_ENTITLEMENT_BLOCKED"
    elif status is not None and 200 <= status < 300 and obj is not None and brti and timestamp_present and numeric_present:
        classification = "BRTI_SOURCE_ACCESS_PASS"
    elif status is not None and 200 <= status < 300:
        classification = "BRTI_SOURCE_SCHEMA_UNPROVEN"
    else:
        classification = "BRTI_SOURCE_TECHNICAL_FAILURE"

    return {
        "classification": classification,
        "network_request_made": True,
        "real_credentials_used": True,
        "request_started_utc": iso(started),
        "request_finished_utc": iso(finished),
        "request_method": "GET",
        "request_host": BASE,
        "request_path": PATH,
        "request_query": "id=BRTI",
        "signed_path": PATH,
        "http_status": status,
        "content_type": content_type,
        "response_bytes": len(raw),
        "response_sha256": sha256_bytes(raw),
        "schema_key_paths": schema_paths,
        "brti_identity_present": brti,
        "point_in_time_timestamp_present": timestamp_present,
        "finite_numeric_index_value_present": numeric_present,
        "observation_fields_bound_to_same_branch": bool(brti and timestamp_present and numeric_present),
        "numeric_index_value_persisted": False,
        "api_key_value_persisted": False,
        "private_key_value_persisted": False,
        "orders": False,
        "account_endpoint_accessed": False,
        "economic_outputs_computed": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--execute-authenticated", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "POB_BRTI_READONLY_SOURCE_ACCESS_RECEIPT_V0.1",
        "generated_at_utc": iso(utc_now()),
        "authority": "POB_BRTI_READONLY_SOURCE_ACCESS_AUTHORITY_V0.1.md",
        "source_url": URL,
        "source_only": True,
        "self_test": self_test(),
    }

    if args.execute_authenticated:
        receipt["source_access"] = execute_authenticated()
    else:
        receipt["source_access"] = {
            "classification": "BRTI_REAL_ACCESS_NOT_ACTIVATED",
            "network_request_made": False,
            "real_credentials_used": False,
        }

    receipt["firewall"] = {
        "economic_outputs_computed": False,
        "market_quotes_compared": False,
        "matured_outcomes_read": False,
        "orders": False,
        "exchange_mutation": False,
        "main_merge": False,
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    p = OUT / "brti_source_access_receipt.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "self_test": receipt["self_test"]["classification"],
        "parser_self_test": receipt["self_test"].get("parser", {}).get("classification"),
        "source_access": receipt["source_access"]["classification"],
        "firewall": receipt["firewall"],
    }, indent=2, sort_keys=True))

    return 0 if receipt["self_test"]["classification"] == "SELF_TEST_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
