from __future__ import annotations

from math import floor


DEFAULT_VALIDATION_MARGIN_FRACTION = 0.001
DEFAULT_LEVERAGE = 1.0


def isolated_margin_validation_size(
    *,
    account_equity: float,
    price: float,
    contract_size: float,
    min_vol: int,
    vol_unit: int,
    leverage: float = DEFAULT_LEVERAGE,
    max_margin_fraction: float = DEFAULT_VALIDATION_MARGIN_FRACTION,
) -> dict:
    """Compute a fail-closed MEXC isolated-margin validation size.

    This is not stop-based sizing and creates no order. It floors contract
    quantity so the initial isolated margin never exceeds the prospectively
    frozen validation allocation. Fees/funding remain separate costs and must
    pass their own gate before any capital deployment.
    """

    if account_equity <= 0:
        raise ValueError("account_equity must be > 0")
    if price <= 0 or contract_size <= 0:
        raise ValueError("price and contract_size must be > 0")
    if min_vol <= 0 or vol_unit <= 0:
        raise ValueError("min_vol and vol_unit must be > 0")
    if leverage <= 0:
        raise ValueError("leverage must be > 0")
    if not 0 < max_margin_fraction < 1:
        raise ValueError("max_margin_fraction must be between 0 and 1")
    if min_vol % vol_unit != 0:
        raise ValueError("min_vol must align to vol_unit")

    max_initial_margin = account_equity * max_margin_fraction
    notional_per_contract = price * contract_size
    margin_per_contract = notional_per_contract / leverage
    raw_contracts = max_initial_margin / margin_per_contract
    floored_contracts = int(floor(raw_contracts / vol_unit) * vol_unit)

    minimum_notional = min_vol * notional_per_contract
    minimum_initial_margin = minimum_notional / leverage
    eligible = floored_contracts >= min_vol

    if not eligible:
        return {
            "status": "BLOCKED_MINIMUM_CONTRACT_EXCEEDS_VALIDATION_MARGIN",
            "eligible": False,
            "account_equity": account_equity,
            "max_margin_fraction": max_margin_fraction,
            "max_initial_margin": max_initial_margin,
            "leverage": leverage,
            "price": price,
            "contract_size": contract_size,
            "min_vol": min_vol,
            "vol_unit": vol_unit,
            "minimum_notional": minimum_notional,
            "minimum_initial_margin": minimum_initial_margin,
            "contracts": 0,
            "notional": 0.0,
            "initial_margin": 0.0,
            "orders_created": False,
            "capital_enabled": False,
        }

    contracts = floored_contracts
    notional = contracts * notional_per_contract
    initial_margin = notional / leverage
    if initial_margin > max_initial_margin + 1e-12:
        raise RuntimeError("floored sizing exceeded validation margin budget")

    return {
        "status": "ADVISORY_SIZE_AVAILABLE_PENDING_OTHER_GATES",
        "eligible": True,
        "account_equity": account_equity,
        "max_margin_fraction": max_margin_fraction,
        "max_initial_margin": max_initial_margin,
        "leverage": leverage,
        "price": price,
        "contract_size": contract_size,
        "min_vol": min_vol,
        "vol_unit": vol_unit,
        "minimum_notional": minimum_notional,
        "minimum_initial_margin": minimum_initial_margin,
        "contracts": contracts,
        "base_asset_units": contracts * contract_size,
        "notional": notional,
        "initial_margin": initial_margin,
        "unused_margin_budget": max_initial_margin - initial_margin,
        "orders_created": False,
        "capital_enabled": False,
        "warnings": [
            "This is an isolated initial-margin allocation, not stop-based risk.",
            "Fees, funding, slippage, liquidation mechanics and exchange failure modes are not bounded by this calculation.",
            "Authenticated checks must confirm isolated mode, 1x leverage and auto-margin-add disabled before any order transport is enabled.",
        ],
    }
