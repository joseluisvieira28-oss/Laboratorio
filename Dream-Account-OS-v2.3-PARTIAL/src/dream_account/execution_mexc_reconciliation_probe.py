from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Callable

from .execution_mexc_readonly import MEXCSpotReadOnlyClient, ReadOnlyMEXCError


ACCESS_KEY_ENV = "MEXC_READONLY_ACCESS_KEY"
SECRET_KEY_ENV = "MEXC_READONLY_SECRET_KEY"
SCOPE_ATTESTATION_ENV = "MEXC_READONLY_SCOPE_ATTESTED"
RECONCILIATION_ENABLE_ENV = "MEXC_READONLY_RECONCILE_ENABLE"
MAX_CLOCK_SKEW_MS = 5_000
DAOS_CLIENT_PREFIX = "DAOS-"
TRADE_LIMIT_PER_SYMBOL = 100
CANONICAL_SPOT_SYMBOLS = (
    "ADAUSDT",
    "AVAXUSDT",
    "BNBUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "SOLUSDT",
    "XRPUSDT",
)


class ReadOnlyReconciliationBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class SanitizedReconciliationReport:
    status: str
    account_type: str
    clock_skew_ms: int
    symbols_queried: int
    balance_rows: int
    nonzero_balance_rows: int
    open_order_count: int
    recent_trade_count: int
    daos_open_order_count: int
    daos_recent_trade_count: int
    trade_query_limit_per_symbol: int
    exchange_mutation_routes: int = 0
    note: str = (
        "Counts are sanitized. No symbols, order IDs, prices, quantities, balances, "
        "trade IDs, or credential values are emitted. Recent trades are bounded per symbol."
    )

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def sanitized_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint()
        return payload


def _is_nonzero(value: str) -> bool:
    try:
        return float(value) != 0.0
    except (TypeError, ValueError) as exc:
        raise ReadOnlyReconciliationBlocked("MEXC returned a non-numeric balance field") from exc


def load_guarded_client_from_env(
    *, client_factory: Callable[..., MEXCSpotReadOnlyClient] = MEXCSpotReadOnlyClient
) -> MEXCSpotReadOnlyClient:
    if os.getenv(SCOPE_ATTESTATION_ENV) != "1":
        raise ReadOnlyReconciliationBlocked(
            f"set {SCOPE_ATTESTATION_ENV}=1 only after verifying read-only API scope"
        )
    if os.getenv(RECONCILIATION_ENABLE_ENV) != "1":
        raise ReadOnlyReconciliationBlocked(
            f"set {RECONCILIATION_ENABLE_ENV}=1 only for an explicit one-shot reconciliation"
        )
    access_key = os.getenv(ACCESS_KEY_ENV, "")
    secret_key = os.getenv(SECRET_KEY_ENV, "")
    if not access_key or not secret_key:
        raise ReadOnlyReconciliationBlocked("read-only MEXC credentials are missing")
    return client_factory(access_key, secret_key)


def run_reconciliation(client: MEXCSpotReadOnlyClient) -> SanitizedReconciliationReport:
    clock_skew = client.sync_clock()
    if abs(clock_skew) > MAX_CLOCK_SKEW_MS:
        raise ReadOnlyReconciliationBlocked("MEXC clock skew exceeds Gate K limit")

    account = client.account()
    if account.account_type.upper() != "SPOT":
        raise ReadOnlyReconciliationBlocked("unexpected MEXC account type")

    nonzero_balances = sum(
        1
        for row in account.balances
        if _is_nonzero(row.free) or _is_nonzero(row.locked)
    )

    open_order_count = 0
    recent_trade_count = 0
    daos_open_order_count = 0
    daos_recent_trade_count = 0

    for symbol in CANONICAL_SPOT_SYMBOLS:
        orders = client.open_orders(symbol)
        trades = client.recent_trades(symbol, limit=TRADE_LIMIT_PER_SYMBOL)
        open_order_count += len(orders)
        recent_trade_count += len(trades)
        daos_open_order_count += sum(
            1 for row in orders if row.client_order_id.startswith(DAOS_CLIENT_PREFIX)
        )
        daos_recent_trade_count += sum(
            1
            for row in trades
            if (row.client_order_id or "").startswith(DAOS_CLIENT_PREFIX)
        )

    status = "PASS_CLEAN"
    if daos_open_order_count or daos_recent_trade_count:
        status = "DIVERGENCE_BLOCKED"

    return SanitizedReconciliationReport(
        status=status,
        account_type=account.account_type,
        clock_skew_ms=clock_skew,
        symbols_queried=len(CANONICAL_SPOT_SYMBOLS),
        balance_rows=len(account.balances),
        nonzero_balance_rows=nonzero_balances,
        open_order_count=open_order_count,
        recent_trade_count=recent_trade_count,
        daos_open_order_count=daos_open_order_count,
        daos_recent_trade_count=daos_recent_trade_count,
        trade_query_limit_per_symbol=TRADE_LIMIT_PER_SYMBOL,
    )


def main() -> int:
    try:
        client = load_guarded_client_from_env()
        report = run_reconciliation(client)
    except (ReadOnlyReconciliationBlocked, ReadOnlyMEXCError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report.sanitized_dict(), sort_keys=True))
    return 0 if report.status == "PASS_CLEAN" else 3


if __name__ == "__main__":
    raise SystemExit(main())
