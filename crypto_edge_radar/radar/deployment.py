from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeploymentMode(str, Enum):
    BLOCKED = "BLOCKED"
    SHADOW_ONLY = "SHADOW_ONLY"
    MICRO_LIVE_ADVISORY = "MICRO_LIVE_ADVISORY"


@dataclass(frozen=True)
class RiskLimits:
    """Account-level launch limits expressed as fractions of account equity."""

    per_trade: float = 0.0010
    max_concurrent: float = 0.0030
    daily_stop: float = 0.0030
    weekly_stop: float = 0.0075

    def __post_init__(self) -> None:
        fields = {
            "per_trade": self.per_trade,
            "max_concurrent": self.max_concurrent,
            "daily_stop": self.daily_stop,
            "weekly_stop": self.weekly_stop,
        }
        for name, value in fields.items():
            if not 0 < value < 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.per_trade > self.max_concurrent:
            raise ValueError("per_trade cannot exceed max_concurrent")
        if self.daily_stop > self.weekly_stop:
            raise ValueError("daily_stop cannot exceed weekly_stop")

    def money_budgets(self, account_equity: float) -> dict[str, float]:
        if account_equity <= 0:
            raise ValueError("account_equity must be > 0")
        return {
            "account_equity": account_equity,
            "planned_risk_per_trade": account_equity * self.per_trade,
            "max_simultaneous_planned_risk": account_equity * self.max_concurrent,
            "daily_stop_amount": account_equity * self.daily_stop,
            "weekly_stop_amount": account_equity * self.weekly_stop,
        }


@dataclass(frozen=True)
class DeploymentProfile:
    strategy_id: str
    scientific_tier: int | None
    shadow_authorized: bool
    adapter_frozen: bool
    execution_instrument_frozen: bool
    cost_model_frozen: bool
    risk_model_frozen: bool
    rejected: bool = False
    unresolved_scientific_blocker: bool = False
    post_outcome_secondary: bool = False


@dataclass(frozen=True)
class DeploymentDecision:
    strategy_id: str
    mode: DeploymentMode
    reason: str


class DeploymentGate:
    """Pure advisory gate. It has no exchange credentials and no order path."""

    @staticmethod
    def adjudicate(profile: DeploymentProfile) -> DeploymentDecision:
        if profile.rejected or profile.scientific_tier == 4:
            return DeploymentDecision(
                profile.strategy_id,
                DeploymentMode.BLOCKED,
                "BLOCKED_REJECTED_OR_TIER4",
            )

        if profile.unresolved_scientific_blocker:
            return DeploymentDecision(
                profile.strategy_id,
                DeploymentMode.BLOCKED,
                "BLOCKED_UNRESOLVED_SCIENTIFIC_OR_PROVENANCE_GATE",
            )

        if profile.post_outcome_secondary:
            return DeploymentDecision(
                profile.strategy_id,
                DeploymentMode.SHADOW_ONLY if profile.shadow_authorized else DeploymentMode.BLOCKED,
                "SECONDARY_POST_OUTCOME_SURVIVOR_NOT_CAPITAL_ELIGIBLE",
            )

        if profile.scientific_tier == 3:
            return DeploymentDecision(
                profile.strategy_id,
                DeploymentMode.SHADOW_ONLY if profile.shadow_authorized else DeploymentMode.BLOCKED,
                "TIER3_SHADOW_ONLY",
            )

        if profile.scientific_tier not in {1, 2}:
            return DeploymentDecision(
                profile.strategy_id,
                DeploymentMode.BLOCKED,
                "BLOCKED_NOT_TIER1_OR_TIER2",
            )

        missing: list[str] = []
        if not profile.adapter_frozen:
            missing.append("adapter")
        if not profile.execution_instrument_frozen:
            missing.append("execution_instrument")
        if not profile.cost_model_frozen:
            missing.append("cost_model")
        if not profile.risk_model_frozen:
            missing.append("risk_model")

        if missing:
            shadow_mode = DeploymentMode.SHADOW_ONLY if profile.shadow_authorized else DeploymentMode.BLOCKED
            return DeploymentDecision(
                profile.strategy_id,
                shadow_mode,
                "BLOCKED_FROM_MICRO_LIVE_MISSING_" + "_".join(item.upper() for item in missing),
            )

        return DeploymentDecision(
            profile.strategy_id,
            DeploymentMode.MICRO_LIVE_ADVISORY,
            "ALL_MICRO_LIVE_ELIGIBILITY_GATES_PASS",
        )


def stop_based_position_size(
    account_equity: float,
    entry_price: float,
    stop_price: float,
    limits: RiskLimits | None = None,
) -> dict[str, float]:
    """Calculate advisory size only when a deterministic stop bounds the planned loss.

    Fees/slippage must be included upstream in the frozen risk model before this output
    is treated as executable sizing. No order is created by this function.
    """

    limits = limits or RiskLimits()
    if account_equity <= 0:
        raise ValueError("account_equity must be > 0")
    if entry_price <= 0 or stop_price <= 0:
        raise ValueError("prices must be > 0")

    stop_distance = abs(entry_price - stop_price)
    if stop_distance == 0:
        raise ValueError("entry_price and stop_price must differ")

    risk_budget = account_equity * limits.per_trade
    units = risk_budget / stop_distance
    notional = units * entry_price
    return {
        "planned_risk": risk_budget,
        "stop_distance": stop_distance,
        "units": units,
        "notional": notional,
    }
