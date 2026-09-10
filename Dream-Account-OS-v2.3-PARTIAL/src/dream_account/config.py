from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    balance_chf: float = 56.0
    normal_risk_pct: float = 1.0
    defensive_risk_pct: float = 0.5
    drawdown_defensive_pct: float = 5.0
    drawdown_halt_pct: float = 10.0
    loss_streak_defensive: int = 5
    min_volume_usd: float = 500_000.0
    strong_volume_usd: float = 5_000_000.0
    preferred_spread_pct: float = 0.20
    hard_spread_pct: float = 0.50
    min_net_rr: float = 2.0
    ideal_a_plus_rr: float = 2.5
    request_timeout_seconds: float = 10.0
    deep_scan_limit: int = 20
    database_path: str = "runtime/dream_account.sqlite3"
    dashboard_path: str = "runtime/dashboard.html"
