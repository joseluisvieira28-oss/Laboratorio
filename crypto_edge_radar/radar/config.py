from __future__ import annotations

from dataclasses import dataclass
import os

CORE5 = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")
ALLOWED_UNIVERSE_MODES = {"core5", "liquid"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = float(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


@dataclass(frozen=True)
class Settings:
    db_path: str = "radar_evidence.sqlite3"
    universe_mode: str = "core5"
    max_symbols: int = 50
    min_quote_volume: float = 50_000_000.0
    http_timeout: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        mode = os.getenv("RADAR_UNIVERSE_MODE", "core5").strip().lower()
        if mode not in ALLOWED_UNIVERSE_MODES:
            raise ValueError(
                f"RADAR_UNIVERSE_MODE must be one of {sorted(ALLOWED_UNIVERSE_MODES)}"
            )
        return cls(
            db_path=os.getenv("RADAR_DB", "radar_evidence.sqlite3"),
            universe_mode=mode,
            max_symbols=_int_env("RADAR_MAX_SYMBOLS", 50),
            min_quote_volume=_float_env("RADAR_MIN_QUOTE_VOLUME", 50_000_000.0),
            http_timeout=_int_env("RADAR_HTTP_TIMEOUT", 10),
        )
