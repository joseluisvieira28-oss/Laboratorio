#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BUCKET = "hl-mainnet-node-data"
PREFIXES = ("explorer_blocks", "replica_cmds")
DOC_URL = "https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data"


def write_json(path: str, obj: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def text_sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def xml_error_code(body: bytes) -> tuple[str | None, str | None]:
    try:
        root = ET.fromstring(body)
    except Exception:
        return None, None
    code = root.findtext("Code")
    msg = root.findtext("Message")
    return code, msg


def list_unsigned(prefix: str) -> dict:
    q = urllib.parse.urlencode({"list-type": "2", "prefix": prefix + "/", "max-keys": "3"})
    url = f"https://{BUCKET}.s3.amazonaws.com/?{q}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/xml", "User-Agent": "CryptoLab-CVFB-S3-P0C/0.2"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            status = int(r.status)
            keys: list[str] = []
            if status == 200:
                try:
                    root = ET.fromstring(body)
                    ns = ""
                    if root.tag.startswith("{"):
                        ns = root.tag.split("}", 1)[0] + "}"
                    for c in root.findall(f"{ns}Contents"):
                        k = c.findtext(f"{ns}Key")
                        if k:
                            keys.append(k)
                except Exception:
                    pass
            return {
                "prefix": prefix,
                "url_without_credentials": url,
                "http_status": status,
                "response_sha256": text_sha256(body),
                "response_byte_count": len(body),
                "listed_key_count": len(keys),
                "listed_keys": keys,
                "aws_error_code": None,
                "aws_error_message": None,
            }
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        code, msg = xml_error_code(body)
        return {
            "prefix": prefix,
            "url_without_credentials": url,
            "http_status": int(e.code),
            "response_sha256": text_sha256(body),
            "response_byte_count": len(body),
            "listed_key_count": 0,
            "listed_keys": [],
            "aws_error_code": code,
            "aws_error_message": msg,
        }
    except Exception as e:
        return {
            "prefix": prefix,
            "url_without_credentials": url,
            "http_status": None,
            "response_sha256": None,
            "response_byte_count": 0,
            "listed_key_count": 0,
            "listed_keys": [],
            "aws_error_code": type(e).__name__,
            "aws_error_message": str(e),
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    probes = [list_unsigned(p) for p in PREFIXES]
    any_200 = any(p["http_status"] == 200 for p in probes)
    all_denied = all(p["http_status"] in {400, 401, 403} for p in probes)
    technical = any(p["http_status"] is None or (p["http_status"] not in {200, 400, 401, 403}) for p in probes)

    # Hyperliquid's official historical-data documentation states the requester
    # must pay transfer costs. This frozen gate does not authorize credentials,
    # requester-pays billing, or object downloads. Even if an unsigned prefix
    # listing is visible, schema bytes remain intentionally unopened.
    if technical:
        decision = "TECHNICAL_BLOCKED"
    elif all_denied or any_200:
        decision = "BLOCKED_REQUESTER_PAYS_NO_AUTHORIZED_CREDENTIALS"
    else:
        decision = "TECHNICAL_BLOCKED"

    receipt = {
        "schema_version": "0.2",
        "recovery_id": "CVFB_NATIVE_ORACLE_PROVENANCE_RECOVERY_V0.5",
        "stage": "P0C_OFFICIAL_S3_ACCESS_AND_SCHEMA_GATE",
        "status": "COMPLETE",
        "decision": decision,
        "official_documentation": DOC_URL,
        "documented_requester_pays_transfer": True,
        "bucket": BUCKET,
        "unsigned_prefix_probes": probes,
        "credentials_used": False,
        "requester_pays_header_used": False,
        "paid_transfer_authorized": False,
        "object_bytes_downloaded": False,
        "schema_values_opened": False,
        "market_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "primary_replication_reopened": False,
        "2026_opened": False,
        "live_trading_authorized": False,
        "interpretation": (
            "Official S3 node-history remains a provenance candidate, but byte-level schema adjudication is not authorized without authenticated requester-pays access. This is an access blocker, not evidence for or against the economic mechanism."
            if decision == "BLOCKED_REQUESTER_PAYS_NO_AUTHORIZED_CREDENTIALS"
            else "The anonymous official-S3 access probe did not complete cleanly; no scientific/economic inference is permitted."
        ),
        "next_action": (
            "REQUIRE_SEPARATE_EXPLICIT_AUTHORIZATION_FOR_AUTHENTICATED_REQUESTER_PAYS_SOURCE_PROBE_BEFORE_ANY_OBJECT_BYTES"
            if decision == "BLOCKED_REQUESTER_PAYS_NO_AUTHORIZED_CREDENTIALS"
            else "DIAGNOSE_OFFICIAL_S3_ACCESS_TECHNICALLY_WITHOUT_OPENING_MARKET_VALUES"
        ),
    }
    write_json(a.out, receipt)
    print(json.dumps({
        "status": receipt["status"],
        "decision": decision,
        "prefix_statuses": {p["prefix"]: p["http_status"] for p in probes},
        "credentials_used": False,
        "object_bytes_downloaded": False,
        "economic_outcomes_computed": False,
        "2026_opened": False,
    }, indent=2))


if __name__ == "__main__":
    main()
