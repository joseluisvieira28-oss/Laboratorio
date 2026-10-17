"""Canonical LCOD component snapshot arithmetic.

This module does not know Aave MCP response field names. Adapters must map live
payloads into these explicit fields before health reconstruction is permitted.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SupplyLeg:
    reserve_id: str
    amount_main_units: float
    oracle_price_usd: float
    collateral_factor_pct: float
    collateral_enabled: bool


@dataclass(frozen=True)
class BorrowLeg:
    reserve_id: str
    principal_main_units: float
    accrued_interest_main_units: float
    oracle_price_usd: float


@dataclass(frozen=True)
class ComponentPosition:
    position_id_hash: str
    official_health_factor: float
    supplies: tuple[SupplyLeg, ...]
    borrows: tuple[BorrowLeg, ...]


def collateral_capacity_usd(position: ComponentPosition) -> float:
    total=0.0
    for x in position.supplies:
        if not x.collateral_enabled:
            continue
        if x.amount_main_units < 0 or x.oracle_price_usd < 0:
            raise ValueError("NEGATIVE_SUPPLY_OR_PRICE")
        if not 0 <= x.collateral_factor_pct <= 100:
            raise ValueError("INVALID_COLLATERAL_FACTOR")
        total += x.amount_main_units * x.oracle_price_usd * (x.collateral_factor_pct / 100.0)
    return total


def debt_usd(position: ComponentPosition) -> float:
    total=0.0
    for x in position.borrows:
        if x.principal_main_units < 0 or x.accrued_interest_main_units < 0 or x.oracle_price_usd < 0:
            raise ValueError("NEGATIVE_DEBT_COMPONENT_OR_PRICE")
        total += (x.principal_main_units + x.accrued_interest_main_units) * x.oracle_price_usd
    return total


def reconstructed_health_factor(position: ComponentPosition) -> float:
    debt=debt_usd(position)
    if debt <= 0:
        raise ValueError("NO_POSITIVE_DEBT")
    return collateral_capacity_usd(position) / debt


def relative_reconciliation_error(position: ComponentPosition) -> float:
    official=position.official_health_factor
    if official <= 0:
        raise ValueError("INVALID_OFFICIAL_HEALTH_FACTOR")
    reconstructed=reconstructed_health_factor(position)
    return abs(reconstructed-official) / official
