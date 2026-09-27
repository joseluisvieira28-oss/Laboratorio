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
        return {
            "classification": "SELF_TEST_PASS" if v.returncode == 0 else "SELF_TEST_FAIL",
            "signing_path": PATH,
            "query_excluded_from_signature": True,
            "algorithm": "RSA-PSS-SHA256",
            "signature_base64_roundtrip": base64.b64decode(b64) == signature,
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


def scan_identity_and_value_presence(x: Any) -> tuple[bool, bool, bool]:
    brti = False
    timestamp = False
    finite_numeric = False

    def walk(v: Any, key: str = ""):
        nonlocal brti, timestamp, finite_numeric
        if isinstance(v, dict):
            for k, z in v.items():
                kl = str(k).lower()
                if any(t in kl for t in ("time", "timestamp", "date")) and z not in (None, ""):
                    timestamp = True
                walk(z, kl)
        elif isinstance(v, list):
            for z in v:
                walk(z, key)
        elif isinstance(v, str):
            if "brti" in v.lower():
                brti = True
            if key in ("id", "index", "indexid", "symbol", "ticker", "name") and "brti" in v.lower():
                brti = True
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            if math.isfinite(float(v)):
                finite_numeric = True

    walk(x)
    return brti, timestamp, finite_numeric


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

    brti, timestamp_present, numeric_present = scan_identity_and_value_presence(obj)
    schema_paths = sorted(set(key_paths(obj)))[:200] if obj is not None else []

    if status in (401, 403, 503):
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
        "source_access": receipt["source_access"]["classification"],
        "firewall": receipt["firewall"],
    }, indent=2, sort_keys=True))

    return 0 if receipt["self_test"]["classification"] == "SELF_TEST_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
