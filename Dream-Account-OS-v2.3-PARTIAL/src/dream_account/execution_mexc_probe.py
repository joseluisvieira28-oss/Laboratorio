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
PROBE_ENABLE_ENV = "MEXC_READONLY_PROBE_ENABLE"
MAX_PROBE_CLOCK_SKEW_MS = 5_000


class ReadOnlyProbeBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class MinimalReadOnlyProbeReport:
    status: str
    account_type: str
    clock_skew_ms: int
    balance_rows: int
    nonzero_balance_rows: int
    account_can_trade_flag: bool
    account_can_withdraw_flag: bool
    account_can_deposit_flag: bool
    note: str = "Account capability flags are not proof of API-key write scope."

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
    except (TypeError, ValueError):
        raise ReadOnlyProbeBlocked("MEXC returned a non-numeric balance field")


def minimal_account_probe(client: MEXCSpotReadOnlyClient) -> MinimalReadOnlyProbeReport:
    """Perform only server-time sync plus one authenticated account GET.

    No order/trade endpoints are queried by this minimal probe. The returned report
    intentionally omits asset names and amounts so it is safe to persist as gate
    evidence after operator review.
    """
    clock_skew = client.sync_clock()
    if abs(clock_skew) > MAX_PROBE_CLOCK_SKEW_MS:
        raise ReadOnlyProbeBlocked("MEXC clock skew exceeds Gate K limit")

    account = client.account()
    if account.account_type.upper() != "SPOT":
        raise ReadOnlyProbeBlocked("unexpected MEXC account type for Spot read-only probe")

    nonzero = sum(
        1
        for row in account.balances
        if _is_nonzero(row.free) or _is_nonzero(row.locked)
    )
    return MinimalReadOnlyProbeReport(
        status="PASS",
        account_type=account.account_type,
        clock_skew_ms=clock_skew,
        balance_rows=len(account.balances),
        nonzero_balance_rows=nonzero,
        account_can_trade_flag=account.can_trade,
        account_can_withdraw_flag=account.can_withdraw,
        account_can_deposit_flag=account.can_deposit,
    )


def load_guarded_client_from_env(
    *,
    client_factory: Callable[..., MEXCSpotReadOnlyClient] = MEXCSpotReadOnlyClient,
) -> MEXCSpotReadOnlyClient:
    """Load credentials only after two explicit operator-side safety gates.

    The operator must attest that the MEXC key has read permissions only and must
    separately enable this one-shot probe. Secrets are never printed or persisted.
    """
    if os.getenv(SCOPE_ATTESTATION_ENV) != "1":
        raise ReadOnlyProbeBlocked(
            f"set {SCOPE_ATTESTATION_ENV}=1 only after verifying the key is read-only"
        )
    if os.getenv(PROBE_ENABLE_ENV) != "1":
        raise ReadOnlyProbeBlocked(f"set {PROBE_ENABLE_ENV}=1 for the one-shot read-only probe")

    access_key = os.getenv(ACCESS_KEY_ENV, "")
    secret_key = os.getenv(SECRET_KEY_ENV, "")
    if not access_key or not secret_key:
        raise ReadOnlyProbeBlocked("read-only MEXC credentials are missing from the environment")
    return client_factory(access_key, secret_key)


def main() -> int:
    try:
        client = load_guarded_client_from_env()
        report = minimal_account_probe(client)
    except (ReadOnlyProbeBlocked, ReadOnlyMEXCError, ValueError) as exc:
        # Never include credential values in the error path.
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report.sanitized_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
