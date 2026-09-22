from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

BRANCH_URL = (
    "https://api.github.com/repos/joseluisvieira28-oss/"
    "Laboratorio/branches/crypto-edge-radar-postgres-v0.5"
)
ATOM_URL = (
    "https://github.com/joseluisvieira28-oss/Laboratorio/commits/"
    "crypto-edge-radar-postgres-v0.5.atom"
)
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
ATOM_COMMIT_URL_RE = re.compile(
    r"https://github\.com/joseluisvieira28-oss/Laboratorio/commit/([0-9a-f]{40})"
)


def _fetch_json(url: str, timeout: int) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CRYPTO-EDGE-RADAR-DEPLOY-DRIFT/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def _fetch_text(url: str, timeout: int) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/atom+xml,application/xml,text/xml",
            "User-Agent": "CRYPTO-EDGE-RADAR-DEPLOY-DRIFT/0.2",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="strict")


def _head_from_rest(timeout: int) -> str:
    data = _fetch_json(BRANCH_URL, timeout)
    head = str(((data or {}).get("commit") or {}).get("sha") or "").strip().lower()
    if not SHA40_RE.fullmatch(head):
        raise ValueError("canonical REST branch head SHA unavailable")
    return head


def _head_from_atom(timeout: int) -> str:
    text = _fetch_text(ATOM_URL, timeout)
    entry_start = text.find("<entry")
    if entry_start < 0:
        raise ValueError("Atom feed has no entry")
    next_entry = text.find("<entry", entry_start + 1)
    first_entry = text[entry_start:] if next_entry < 0 else text[entry_start:next_entry]
    matches = ATOM_COMMIT_URL_RE.findall(first_entry)
    unique = list(dict.fromkeys(x.lower() for x in matches))
    if len(unique) != 1 or not SHA40_RE.fullmatch(unique[0]):
        raise ValueError("Atom first entry has no unique exact commit SHA")
    return unique[0]


def deployment_drift_receipt(*, timeout: int = 15) -> dict[str, Any]:
    deployed = (os.getenv("RENDER_GIT_COMMIT") or "").strip()
    if not deployed:
        return {
            "classification": "NOT_RENDER_RUNTIME",
            "deployed_commit": None,
            "canonical_head_commit": None,
            "in_sync": None,
            "automatic_deploy_performed": False,
        }

    errors: list[str] = []
    try:
        head = _head_from_rest(timeout)
        head_source = "GITHUB_REST"
    except Exception as exc:
        errors.append(f"REST:{type(exc).__name__}:{exc}")
        try:
            head = _head_from_atom(timeout)
            head_source = "GITHUB_ATOM"
        except Exception as atom_exc:
            errors.append(f"ATOM:{type(atom_exc).__name__}:{atom_exc}")
            return {
                "classification": "UNAVAILABLE_FAIL_CLOSED",
                "deployed_commit": deployed,
                "canonical_head_commit": None,
                "head_source": None,
                "in_sync": None,
                "errors": errors,
                "automatic_deploy_performed": False,
            }

    same = deployed.lower() == head
    return {
        "classification": "IN_SYNC" if same else "STALE_RUNTIME",
        "deployed_commit": deployed,
        "canonical_head_commit": head,
        "head_source": head_source,
        "in_sync": same,
        "primary_source_errors": errors,
        "automatic_deploy_performed": False,
    }
