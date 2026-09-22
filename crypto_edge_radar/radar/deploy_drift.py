from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

BRANCH_URL = (
    "https://api.github.com/repos/joseluisvieira28-oss/"
    "Laboratorio/branches/crypto-edge-radar-postgres-v0.5"
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

    try:
        data = _fetch_json(BRANCH_URL, timeout)
        head = str(((data or {}).get("commit") or {}).get("sha") or "").strip()
        if len(head) != 40:
            raise ValueError("canonical branch head SHA unavailable")
    except Exception as exc:
        return {
            "classification": "UNAVAILABLE_FAIL_CLOSED",
            "deployed_commit": deployed,
            "canonical_head_commit": None,
            "in_sync": None,
            "error": f"{type(exc).__name__}:{exc}",
            "automatic_deploy_performed": False,
        }

    same = deployed == head
    return {
        "classification": "IN_SYNC" if same else "STALE_RUNTIME",
        "deployed_commit": deployed,
        "canonical_head_commit": head,
        "in_sync": same,
        "automatic_deploy_performed": False,
    }
