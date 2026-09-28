from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import (
    MEXCCredentials,
    MEXCFuturesAuthenticatedReadOnlyClient,
)
from radar.mexc_symbol_readiness_v01 import run_symbol_readiness


ALLOWED_SYMBOLS = ("BNB_USDT", "AVAX_USDT")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read-only MEXC Futures readiness for operator BNB/CED1D lanes."
    )
    ap.add_argument(
        "--symbol",
        action="append",
        choices=ALLOWED_SYMBOLS,
        dest="symbols",
        help="Repeat to probe a subset. Default probes both frozen operator symbols.",
    )
    ap.add_argument("--output", default=None)
    ap.add_argument("--timeout", type=int, default=10)
    args = ap.parse_args()

    symbols = args.symbols or list(ALLOWED_SYMBOLS)
    creds = MEXCCredentials.from_env()
    private = MEXCFuturesAuthenticatedReadOnlyClient(
        creds,
        timeout=args.timeout,
    )
    public = MEXCFuturesPublicFeed(timeout=args.timeout)

    results = {
        symbol: run_symbol_readiness(
            symbol=symbol,
            private_client=private,
            public_feed=public,
            require_no_global_open_positions=True,
        )
        for symbol in symbols
    }
    all_pass = all(row.get("pass") is True for row in results.values())
    out = {
        "probe_id": "OPERATOR_FUTURES_BNB_CED1D_READONLY_READINESS_V0.1",
        "status": "PASS_TECHNICAL_READINESS_ONLY" if all_pass else "FAIL_CLOSED",
        "pass": all_pass,
        "symbols": results,
        "security": {
            "http_methods": ["GET"],
            "orders": False,
            "exchange_mutation": False,
            "transfers": False,
            "withdrawals": False,
            "credentials_persisted_by_probe": False,
        },
        "authority": {
            "live_activation_authorized": False,
            "note": "A PASS only clears technical symbol/account readiness. Candidate signal, execution authority, risk, fee, source, duplicate and reconciliation gates remain mandatory.",
        },
    }

    payload = json.dumps(out, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
