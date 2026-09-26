from __future__ import annotations

from dataclasses import dataclass
import os
import re
from urllib.parse import quote

CORE5 = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")
ALLOWED_UNIVERSE_MODES = {"core5", "liquid"}
ALLOWED_PROVIDERS = {"binance_usdm", "binance_spot_public", "mexc_futures_public"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = float(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


SUPABASE_PROJECT_REF = "jqzdvgjeuveiktftyrlz"
SUPABASE_POOLER_HOST_RE = re.compile(
    r"^aws-[0-9]+-eu-central-1[.]pooler[.]supabase[.]com$"
)


def _supabase_target_url_from_env() -> str | None:
    if not _bool_env("RADAR_USE_SUPABASE_TARGET", False):
        return None

    host = os.getenv("RADAR_SUPABASE_POOLER_HOST", "").strip().lower()
    if not SUPABASE_POOLER_HOST_RE.fullmatch(host):
        raise ValueError(
            "RADAR_SUPABASE_POOLER_HOST must be an audited eu-central-1 "
            "Supavisor host"
        )

    password = os.getenv("RADAR_SUPABASE_POOLER_PASSWORD", "")
    if not password:
        raise ValueError(
            "RADAR_SUPABASE_POOLER_PASSWORD is required when "
            "RADAR_USE_SUPABASE_TARGET=true"
        )

    user = f"radar_runtime.{SUPABASE_PROJECT_REF}"
    return (
        "postgresql://"
        + quote(user, safe=".")
        + ":"
        + quote(password, safe="")
        + "@"
        + host
        + ":5432/postgres?sslmode=require"
    )


@dataclass(frozen=True)
class Settings:
    db_path: str = "radar_evidence.sqlite3"
    database_url: str | None = None
    database_schema_preprovisioned: bool = False
    database_target_mode: str = "SOURCE"
    status_path: str = "radar_status.json"
    notification_path: str = "radar_notifications.jsonl"
    provider: str = "binance_usdm"
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
        provider = os.getenv("RADAR_PROVIDER", "binance_usdm").strip().lower()
        if provider not in ALLOWED_PROVIDERS:
            raise ValueError(f"RADAR_PROVIDER must be one of {sorted(ALLOWED_PROVIDERS)}")
        source_database_url = os.getenv("RADAR_DATABASE_URL")
        if source_database_url is not None:
            source_database_url = source_database_url.strip() or None

        target_database_url = _supabase_target_url_from_env()
        if target_database_url is not None:
            database_url = target_database_url
            database_schema_preprovisioned = True
            database_target_mode = "SUPABASE_POOLER"
        else:
            database_url = source_database_url
            database_schema_preprovisioned = _bool_env(
                "RADAR_POSTGRES_SCHEMA_PREPROVISIONED",
                False,
            )
            database_target_mode = "SOURCE"

        return cls(
            db_path=os.getenv("RADAR_DB", "radar_evidence.sqlite3"),
            database_url=database_url,
            database_schema_preprovisioned=database_schema_preprovisioned,
            database_target_mode=database_target_mode,
            status_path=os.getenv("RADAR_STATUS", "radar_status.json"),
            notification_path=os.getenv(
                "RADAR_NOTIFICATIONS", "radar_notifications.jsonl"
            ),
            provider=provider,
            universe_mode=mode,
            max_symbols=_int_env("RADAR_MAX_SYMBOLS", 50),
            min_quote_volume=_float_env("RADAR_MIN_QUOTE_VOLUME", 50_000_000.0),
            http_timeout=_int_env("RADAR_HTTP_TIMEOUT", 10),
        )
