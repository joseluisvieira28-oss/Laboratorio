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
BRANCH_ATOM_URL = (
    "https://github.com/joseluisvieira28-oss/Laboratorio/commits/"
    "crypto-edge-radar-postgres-v0.5.atom"
)
_COMMIT_LINK_RE = re.compile(r"/commit/([0-9a-f]{40})(?:[\"'<\\s?]|$)")


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
            "Accept": "application/atom+xml,text/xml;q=0.9,*/*;q=0.1",
            "User-Agent": "CRYPTO-EDGE-RADAR-DEPLOY-DRIFT/0.2",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="strict")


def _head_from_atom(text: str) -> str:
    match = _COMMIT_LINK_RE.search(text)
    if not match:
        raise ValueError("canonical branch head SHA unavailable from Atom feed")
    return match.group(1)


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

    primary_error = None
    source = "GITHUB_API"
    try:
        data = _fetch_json(BRANCH_URL, timeout)
        head = str(((data or {}).get("commit") or {}).get("sha") or "").strip()
        if len(head) != 40:
            raise ValueError("canonical branch head SHA unavailable")
    except Exception as exc:
        primary_error = f"{type(exc).__name__}:{exc}"
        source = "GITHUB_ATOM_FALLBACK"
        try:
            head = _head_from_atom(_fetch_text(BRANCH_ATOM_URL, timeout))
        except Exception as fallback_exc:
            return {
                "classification": "UNAVAILABLE_FAIL_CLOSED",
                "deployed_commit": deployed,
                "canonical_head_commit": None,
                "in_sync": None,
                "primary_error": primary_error,
                "fallback_error": f"{type(fallback_exc).__name__}:{fallback_exc}",
                "source": None,
                "automatic_deploy_performed": False,
            }

    same = deployed == head
    return {
        "classification": "IN_SYNC" if same else "STALE_RUNTIME",
        "deployed_commit": deployed,
        "canonical_head_commit": head,
        "in_sync": same,
        "source": source,
        "primary_error": primary_error,
        "automatic_deploy_performed": False,
    }
