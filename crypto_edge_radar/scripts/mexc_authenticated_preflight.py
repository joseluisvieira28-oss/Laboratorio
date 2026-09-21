from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from radar.mexc_auth_readonly import (
    MEXCAuthenticatedReadError,
    MEXCCredentials,
    MEXCFuturesAuthenticatedReadOnlyClient,
)
from radar.mexc_authenticated_preflight import run_authenticated_preflight


def main() -> int:
    try:
        credentials = MEXCCredentials.from_env()
        client = MEXCFuturesAuthenticatedReadOnlyClient(credentials)
        expected_raw = os.getenv("MEXC_EXPECTED_FUTURES_EQUITY_USDT", "").strip()
        expected_equity = float(expected_raw) if expected_raw else None
        result = run_authenticated_preflight(
            private_client=client,
            expected_equity_usdt=expected_equity,
        )
    except Exception as exc:
        result = {
            "preflight_id": "MEXC_FUTURES_AUTHENTICATED_READ_ONLY_PREFLIGHT_V0.1",
            "status": "FAIL_CLOSED",
            "pass": False,
            "blockers": ["PREFLIGHT_RUNTIME_EXCEPTION"],
            "error": f"{type(exc).__name__}: {exc}",
            "security": {
                "order_endpoint_implemented": False,
                "exchange_mutation_performed": False,
                "credentials_printed": False,
            },
        }

    output = Path("mexc_authenticated_preflight_receipt.json")
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "receipt_path": str(output.resolve()),
        "status": result.get("status"),
        "pass": result.get("pass"),
        "blockers": result.get("blockers", []),
    }, indent=2, ensure_ascii=False))
    return 0 if result.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
