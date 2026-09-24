from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

from .bnb_launchpool_watcher import (
    BNBLaunchpoolForwardShadowWatcher,
    BinanceOfficialLaunchpoolSource,
)
from .config import Settings
from .ced1d_source_probe import ced1d_render_source_probe
from .ced1d_render_shadow_runtime import CED1DRenderShadowRunner
from .evidence import build_evidence_store
from .strategies.bnb_launchpool_demand import BinanceSpotBNBBTCKlineFeed
from .bnb_launchpool_diamond_v02 import (
    BinancePublicMinuteFeed,
    evaluate_bnb_diamond_v02,
)
from .strategies.tfg_donchian_regime_forward import MEXCSpotKlineFeed
from .spot_mapping import spot_perp_mapping_receipt
from .friction import mexc_friction_shadow_receipt
from .tfg_forward_watcher import (
    TFGForwardShadowWatcher,
    latest_certifiable_signal_close_ms,
)
from .tfg_forward_metrics import evaluate_tfg_forward_evidence
from .ema6h_regime_watcher import EMA6HRegimeForwardWatcher
from .ema6h_regime_metrics import evaluate_ema6h_regime_forward
from .strategies.ema6h_50x200_regime_forward import (
    BinanceSpotKlineFeed as EMA6HBinanceSpotKlineFeed,
    latest_certifiable_signal_close_ms as latest_ema6h_certifiable_signal_close_ms,
)
from .options_v21_live import BinanceBTCUSDTDailyFeed, DeribitBTCOptionTradeFeed
from .options_v21_watcher import OptionsV21ForwardShadowWatcher
from .options_v21_metrics import evaluate_options_v21_forward
from .etf_cme_watcher import ETFCMEPublicSignalWatcher
from .etf_cme_exact_scheduler import ETFCMEExactRuntimeScheduler
from .external_freshness import all_external_freshness
from .private_evidence_backup import emit_snapshot_json_chunks, emit_snapshot_log_chunks
from .persistence_expiry import persistence_expiry_state
from .deploy_drift import deployment_drift_receipt
from .diamond_board import build_diamond_board


RUNTIME_LIVENESS_EVENT = "RADAR_RUNTIME_LIVENESS"
RUNTIME_GAP_EVENT = "RADAR_RUNTIME_GAP_DETECTED"
RUNTIME_LIVENESS_BUCKET_MS = 15 * 60 * 1000
RUNTIME_GAP_ALERT_SECONDS = 30 * 60


def _runtime_identity() -> dict[str, Any]:
    return {
        "render": os.getenv("RENDER", "").lower() == "true",
        "git_commit": os.getenv("RENDER_GIT_COMMIT"),
        "git_branch": os.getenv("RENDER_GIT_BRANCH"),
        "service_id": os.getenv("RENDER_SERVICE_ID"),
        "service_name": os.getenv("RENDER_SERVICE_NAME"),
        "instance_id": os.getenv("RENDER_INSTANCE_ID"),
    }


def _parse_utc_ms(value: Any) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return int(
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .timestamp()
            * 1000
        )
    except Exception:
        return None


class CachingBinanceOfficialLaunchpoolSource(BinanceOfficialLaunchpoolSource):
    """Caches immutable detail responses in-process; the catalog itself is always refreshed."""

    def __init__(self, timeout: int = 15) -> None:
        super().__init__(timeout=timeout)
        self._detail_cache: dict[str, tuple[Any, bytes]] = {}

    def detail(self, article_code: str) -> tuple[Any, bytes]:
        cached = self._detail_cache.get(article_code)
        if cached is not None:
            return cached
        result = super().detail(article_code)
        self._detail_cache[article_code] = result
        return result


def normalized_poll_interval_seconds(value: float) -> float:
    value = float(value)
    if value <= 0:
        raise ValueError("poll interval must be positive")
    return max(value, 30.0)


def _atomic_json_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)


class ForwardShadowRuntime:
    """Runs TFG and BNB as independent public-data shadow watchers over one evidence store."""

    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.store = build_evidence_store(settings.db_path, settings.database_url)
        self.tfg = TFGForwardShadowWatcher(
            store=self.store,
            feed=MEXCSpotKlineFeed(timeout=settings.http_timeout),
        )
        self.ema6h_regime = EMA6HRegimeForwardWatcher(
            store=self.store,
            feed=EMA6HBinanceSpotKlineFeed(timeout=settings.http_timeout),
        )
        self.bnb_diamond_v02_enabled = (
            os.getenv("BNB_DIAMOND_V02_ENABLED", "").lower() == "true"
        )
        self.bnb = BNBLaunchpoolForwardShadowWatcher(
            store=self.store,
            source=CachingBinanceOfficialLaunchpoolSource(timeout=settings.http_timeout),
            market=BinanceSpotBNBBTCKlineFeed(timeout=settings.http_timeout),
            diamond_feed=(
                BinancePublicMinuteFeed(timeout=settings.http_timeout)
                if self.bnb_diamond_v02_enabled
                else None
            ),
        )
        self.options_v21 = OptionsV21ForwardShadowWatcher(
            store=self.store,
            options_feed=DeribitBTCOptionTradeFeed(timeout=settings.http_timeout),
            btc_feed=BinanceBTCUSDTDailyFeed(timeout=settings.http_timeout),
        )
        self.etf_cme_signal = ETFCMEPublicSignalWatcher(
            store=self.store,
            timeout=settings.http_timeout,
        )
        self.etf_cme_exact_scheduler = ETFCMEExactRuntimeScheduler(
            watcher=self.etf_cme_signal,
        )
        self.ced1d_render_shadow = CED1DRenderShadowRunner(store=self.store)
        self.status_path = os.getenv("RADAR_FORWARD_STATUS", settings.status_path)
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "health": "STARTING",
            "mode": "PUBLIC_SHADOW_ONLY",
            "evidence_backend": self.store.backend,
            "orders_created": False,
        }
        self._last_tfg_due: int | None = None
        self._last_ema6h_due: int | None = None
        self._ema6h_state: dict[str, Any] = {
            "status": "STARTING",
            "watcher_id": "EMA6H-50X200-REGIME-DEPENDENCY-001-FORWARD-SHADOW",
        }
        self._last_etf_public_check_ms: int | None = None
        self._last_etf_signal_check_ms: int | None = None
        self._last_options_runtime_day: str | None = None
        self._last_external_freshness_check_ms: int | None = None
        self._last_deploy_drift_check_ms: int | None = None
        self._deploy_drift_state: dict[str, Any] = {"classification": "STARTING"}
        self._last_ced1d_render_shadow_check_date: str | None = None
        self._ced1d_render_shadow_state: dict[str, Any] = {
            "status": "DISABLED_NOT_ARMED",
            "strategy_id": "CED1D-0031",
        }
        self._last_liveness_bucket_ms: int | None = None
        self._runtime_liveness_state: dict[str, Any] = {"status": "STARTING"}
        self._options_state: dict[str, Any] = {
            "status": "STARTING",
            "watcher_id": "OPTIONS-SPOTPERP-001-V2.1-FORWARD-SHADOW",
        }
        self._etf_public_state: dict[str, Any] = {
            "status": "STARTING",
            "classification": "PUBLIC_PREFLIGHT_ONLY",
            "capital_enabled": False,
            "orders_created": False,
        }
        self._etf_signal_state: dict[str, Any] = {
            "status": "STARTING",
            "source_status": "UNKNOWN",
            "watcher_id": "ETF-CME-INSTFLOW-001-CFTC-PUBLIC-FORWARD-WATCHER",
        }
        self._external_freshness_state: dict[str, Any] = {}

    def state(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def _runtime_liveness(self, *, now_ms: int) -> dict[str, Any]:
        bucket_ms = now_ms - (now_ms % RUNTIME_LIVENESS_BUCKET_MS)
        if self._last_liveness_bucket_ms == bucket_ms:
            return self._runtime_liveness_state

        previous_rows = self.store.read_payloads(RUNTIME_LIVENESS_EVENT)
        previous_ms = max(
            (
                parsed
                for parsed in (
                    _parse_utc_ms(row.get("checked_at_utc")) for row in previous_rows
                )
                if parsed is not None and parsed < bucket_ms
            ),
            default=None,
        )
        gap_seconds = None if previous_ms is None else max(0.0, (now_ms - previous_ms) / 1000.0)
        if previous_ms is None:
            classification = "FIRST_OBSERVATION"
        elif gap_seconds is not None and gap_seconds > RUNTIME_GAP_ALERT_SECONDS:
            classification = "RECOVERED_GAP_REVIEW_REQUIRED"
        else:
            classification = "CONTINUOUS"

        checked = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        bucket_utc = datetime.fromtimestamp(bucket_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "status": classification,
            "checked_at_utc": checked,
            "bucket_start_utc": bucket_utc,
            "previous_liveness_utc": (
                datetime.fromtimestamp(previous_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
                if previous_ms is not None
                else None
            ),
            "gap_seconds": gap_seconds,
            "gap_alert_threshold_seconds": RUNTIME_GAP_ALERT_SECONDS,
            "requires_missed_window_review": classification == "RECOVERED_GAP_REVIEW_REQUIRED",
            "evidence_backend": self.store.backend,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        key = f"RADAR_RUNTIME_LIVENESS:{bucket_utc}"
        receipt = self.store.append_once(RUNTIME_LIVENESS_EVENT, key, payload)
        payload["evidence_inserted"] = bool(receipt["inserted"])

        if classification == "RECOVERED_GAP_REVIEW_REQUIRED":
            gap_receipt = self.store.append_once(
                RUNTIME_GAP_EVENT,
                f"RADAR_RUNTIME_GAP_DETECTED:{bucket_utc}",
                {
                    **payload,
                    "reason": "PERSISTED_LIVENESS_GAP_EXCEEDED_FAIL_CLOSED_THRESHOLD",
                    "scientific_rules_changed": False,
                },
            )
            payload["gap_receipt_inserted"] = bool(gap_receipt["inserted"])
        else:
            payload["gap_receipt_inserted"] = False

        self._last_liveness_bucket_ms = bucket_ms
        self._runtime_liveness_state = payload
        return payload

    def _set_state(self, value: dict[str, Any]) -> None:
        with self._lock:
            self._state = value
        _atomic_json_write(self.status_path, value)

    def run_cycle(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        checked = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        errors: dict[str, str] = {}

        try:
            bnb_state = self.bnb.run_once(now_ms=now_ms)
        except Exception as exc:
            bnb_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
            errors["bnb_launchpool"] = bnb_state["error"]

        try:
            bnb_diamond_metrics = evaluate_bnb_diamond_v02(self.store)
        except Exception as exc:
            bnb_diamond_metrics = {
                "strategy_id": "BNB-LAUNCHPOOL-DEMAND-001",
                "classification": "DIAMOND_METRICS_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "automatic_promotion": False,
                "live_trading_authorized": False,
            }

        due = latest_certifiable_signal_close_ms(now_ms)
        if due is not None and due != self._last_tfg_due:
            try:
                tfg_state = self.tfg.run_once(now_ms=now_ms)
                self._last_tfg_due = due
            except Exception as exc:
                tfg_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
                errors["tfg"] = tfg_state["error"]
        else:
            tfg_state = {
                "status": "IDLE_NO_NEW_CERTIFIABLE_12H_BOUNDARY",
                "latest_seen_boundary_ms": self._last_tfg_due,
            }

        ema6h_due = latest_ema6h_certifiable_signal_close_ms(now_ms)
        if ema6h_due != self._last_ema6h_due or self._ema6h_state.get("status") == "STARTING":
            try:
                ema6h_state = self.ema6h_regime.run_once(now_ms=now_ms)
                self._ema6h_state = ema6h_state
                self._last_ema6h_due = ema6h_due
            except Exception as exc:
                ema6h_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
                self._ema6h_state = ema6h_state
                errors["ema6h_regime"] = ema6h_state["error"]
        else:
            ema6h_state = self._ema6h_state

        try:
            ema6h_metrics = evaluate_ema6h_regime_forward(self.store)
        except Exception as exc:
            ema6h_metrics = {
                "classification": "METRICS_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "automatic_promotion": False,
                "live_trading_authorized": False,
            }
            errors["ema6h_regime_metrics"] = ema6h_metrics["error"]

        runtime_liveness = self._runtime_liveness(now_ms=now_ms)

        chain_ok, chain_detail = self.store.verify_chain()
        if not chain_ok:
            errors["evidence_chain"] = chain_detail

        try:
            tfg_forward_metrics = evaluate_tfg_forward_evidence(self.store)
        except Exception as exc:
            tfg_forward_metrics = {
                "classification": "METRICS_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "readiness_gate_pass": False,
                "live_trading_automatically_authorized": False,
            }
            errors["tfg_forward_metrics"] = tfg_forward_metrics["error"]

        etf_due = (
            self._last_etf_public_check_ms is None
            or now_ms - self._last_etf_public_check_ms >= 60 * 60 * 1000
        )
        if etf_due:
            try:
                spot_receipt = spot_perp_mapping_receipt()
                short_receipt = mexc_friction_shadow_receipt(symbol="BTC_USDT")
                etf_exec_v2 = {
                    "status": "OK",
                    "classification": "PUBLIC_PREFLIGHT_ONLY",
                    "checked_at_utc": checked,
                    "spot_mapping": {
                        "symbol": "BTCUSDT",
                        "spread_bps": spot_receipt["long_mapping_candidate"]["spread_bps"],
                        "perp_minus_spot_mid_bps": spot_receipt["cross_market"]["perp_minus_spot_mid_bps"],
                        "spot_api_supported": spot_receipt["long_mapping_candidate"]["api_default_symbol_supported"],
                        "funding_cost_long_spot": "NONE",
                    },
                    "short_perp_friction": {
                        "same_book_taker_round_trip_proxy_bps": short_receipt["edge_budget"]["same_book_taker_round_trip_proxy_bps"],
                        "trailing_short_fee_spread_funding_bps": short_receipt["edge_budget"]["trailing_7d_directional_proxy"]["short_fee_spread_funding_bps"],
                        "historical_break_even_bps": short_receipt["edge_budget"]["historical_estimated_break_even_round_trip_bps"],
                        "future_funding_is_forecast": False,
                    },
                    "account_fee_verified_read_only": False,
                    "authenticated_transport_ready": False,
                    "execution_authority_present": False,
                    "capital_enabled": False,
                    "orders_created": False,
                    "authenticated_exchange_api_used": False,
                    "exchange_mutation_performed": False,
                }
                hour_key = datetime.fromtimestamp(
                    now_ms / 1000.0, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H")
                self.store.append_once(
                    "ETF_EXEC_V2_PUBLIC_PREFLIGHT",
                    f"ETF-CME-INSTFLOW-001:EXEC-V2:{hour_key}",
                    etf_exec_v2,
                )
                self._etf_public_state = etf_exec_v2
                self._last_etf_public_check_ms = now_ms
            except Exception as exc:
                etf_exec_v2 = {
                    "status": "FAIL_CLOSED",
                    "classification": "PUBLIC_PREFLIGHT_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}:{exc}",
                    "capital_enabled": False,
                    "orders_created": False,
                    "authenticated_exchange_api_used": False,
                    "exchange_mutation_performed": False,
                }
                self._etf_public_state = etf_exec_v2
                errors["etf_exec_v2"] = etf_exec_v2["error"]
        else:
            etf_exec_v2 = self._etf_public_state

        etf_signal_due = self._last_etf_signal_check_ms is None
        next_window = self._etf_signal_state.get("next_expected_source_window")
        if isinstance(next_window, str):
            try:
                target_ms = int(datetime.fromisoformat(next_window.replace("Z", "+00:00")).timestamp() * 1000)
                if abs(target_ms - now_ms) <= 5 * 60 * 1000:
                    etf_signal_due = True
            except ValueError:
                etf_signal_due = True
        if self._last_etf_signal_check_ms is not None and now_ms - self._last_etf_signal_check_ms >= 60 * 60 * 1000:
            etf_signal_due = True
        if etf_signal_due:
            etf_signal = self.etf_cme_signal.run_once(now_ms=now_ms)
            self._etf_signal_state = etf_signal
            self._last_etf_signal_check_ms = now_ms
            if etf_signal.get("status") == "FAIL_CLOSED":
                errors["etf_cme_signal"] = str(etf_signal.get("error") or "source failure")
        else:
            etf_signal = self._etf_signal_state

        options_runtime_day = datetime.fromtimestamp(
            now_ms / 1000.0, tz=timezone.utc
        ).date().isoformat()
        if options_runtime_day != self._last_options_runtime_day:
            try:
                options_v21 = self.options_v21.run_once(now_ms=now_ms)
                self._options_state = options_v21
                self._last_options_runtime_day = options_runtime_day
            except Exception as exc:
                options_v21 = {
                    "status": "FAIL_CLOSED",
                    "error": f"{type(exc).__name__}:{exc}",
                }
                self._options_state = options_v21
                errors["options_v21"] = options_v21["error"]
        else:
            options_v21 = self._options_state

        try:
            options_v21_metrics = evaluate_options_v21_forward(self.store)
        except Exception as exc:
            options_v21_metrics = {
                "classification": "METRICS_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "micro_live_authorized": False,
                "live_capital_enabled": False,
            }
            errors["options_v21_metrics"] = options_v21_metrics["error"]

        ced1d_enabled = os.getenv("CED1D_RENDER_SHADOW_V03_ENABLED", "").lower() == "true"
        ced1d_runtime_day = datetime.fromtimestamp(
            now_ms / 1000.0, tz=timezone.utc
        ).date().isoformat()
        if not ced1d_enabled:
            ced1d_render_shadow = {
                "status": "DISABLED_NOT_ARMED",
                "strategy_id": "CED1D-0031",
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }
            self._ced1d_render_shadow_state = ced1d_render_shadow
        elif (
            self._last_ced1d_render_shadow_check_date != ced1d_runtime_day
            or self._ced1d_render_shadow_state.get("status") == "STARTING"
        ):
            try:
                ced1d_render_shadow = self.ced1d_render_shadow.run_once(now_ms=now_ms)
                self._ced1d_render_shadow_state = ced1d_render_shadow
                self._last_ced1d_render_shadow_check_date = ced1d_runtime_day
            except Exception as exc:
                ced1d_render_shadow = {
                    "status": "FAIL_CLOSED",
                    "strategy_id": "CED1D-0031",
                    "error": f"{type(exc).__name__}:{exc}",
                    "authenticated_exchange_api_used": False,
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                self._ced1d_render_shadow_state = ced1d_render_shadow
                self._last_ced1d_render_shadow_check_date = ced1d_runtime_day
                errors["ced1d_render_shadow"] = ced1d_render_shadow["error"]
        else:
            ced1d_render_shadow = self._ced1d_render_shadow_state

        freshness_due = (
            self._last_external_freshness_check_ms is None
            or now_ms - self._last_external_freshness_check_ms >= 60 * 60 * 1000
        )
        if freshness_due:
            external_freshness = all_external_freshness(
                now=datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc),
                timeout=self.settings.http_timeout,
            )
            self._external_freshness_state = external_freshness
            self._last_external_freshness_check_ms = now_ms
        else:
            external_freshness = self._external_freshness_state

        deploy_drift_due = (
            self._last_deploy_drift_check_ms is None
            or now_ms - self._last_deploy_drift_check_ms >= 60 * 60 * 1000
        )
        if deploy_drift_due:
            deploy_drift = deployment_drift_receipt(
                timeout=self.settings.http_timeout
            )
            self._deploy_drift_state = deploy_drift
            self._last_deploy_drift_check_ms = now_ms
        else:
            deploy_drift = self._deploy_drift_state

        persistence_expiry = persistence_expiry_state(
            os.getenv("RADAR_PERSISTENCE_EXPIRY_UTC"),
            now=datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc),
        )

        state = {
            "health": "OK" if not errors else "DEGRADED_FAIL_CLOSED",
            "mode": "PUBLIC_SHADOW_ONLY",
            "checked_at_utc": checked,
            "version": "0.9",
            "runtime_identity": _runtime_identity(),
            "evidence_backend": self.store.backend,
            "evidence_chain_ok": chain_ok,
            "evidence_chain_detail": chain_detail,
            "runtime_liveness": runtime_liveness,
            "persistence_expiry": persistence_expiry,
            "tfg": tfg_state,
            "tfg_forward_metrics": tfg_forward_metrics,
            "ema6h_regime": ema6h_state,
            "ema6h_regime_metrics": ema6h_metrics,
            "bnb_launchpool": bnb_state,
            "bnb_diamond_v02_enabled": self.bnb_diamond_v02_enabled,
            "bnb_diamond_v02_metrics": bnb_diamond_metrics,
            "etf_exec_v2_public": etf_exec_v2,
            "etf_cme_signal": etf_signal,
            "etf_cme_exact_scheduler": self.etf_cme_exact_scheduler.state(),
            "options_v21": options_v21,
            "options_v21_metrics": options_v21_metrics,
            "ced1d_render_shadow": ced1d_render_shadow,
            "external_collectors": external_freshness,
            "deployment_drift": deploy_drift,
            "operational_attention_required": (
                deploy_drift.get("classification")
                in {"STALE_RUNTIME", "UNAVAILABLE_FAIL_CLOSED"}
            ),
            "errors": errors,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        state["diamond_board"] = build_diamond_board(state)
        self._set_state(state)
        print(json.dumps(state, sort_keys=True), flush=True)
        return state

    def run_loop(self, *, interval_seconds: float) -> None:
        # The old V0.5 canary start command passes 30s. Do not hammer official CMS;
        # Operational latency policy: 30s floor. Scientific signal/timing rules are unchanged.
        interval_seconds = normalized_poll_interval_seconds(interval_seconds)
        while True:
            started = time.monotonic()
            try:
                self.run_cycle()
            except Exception as exc:
                fatal = {
                    "health": "DEGRADED_FAIL_CLOSED",
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "runtime_identity": _runtime_identity(),
                    "evidence_backend": self.store.backend,
                    "errors": {"runtime": f"{type(exc).__name__}:{exc}"},
                    "authenticated_exchange_api_used": False,
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                self._set_state(fatal)
                print(json.dumps(fatal, sort_keys=True), flush=True)
            elapsed = time.monotonic() - started
            time.sleep(max(1.0, interval_seconds - elapsed))


def dashboard_html() -> str:
    """Read-only V0.9 cockpit. No order, account, credential or mutation controls."""
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crypto Edge Radar V0.9</title>
<style>
:root{color-scheme:dark;background:#0b0d10;color:#f5f7fa;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;padding:24px}.wrap{max-width:1100px;margin:auto}
h1{margin:0 0 6px;font-size:28px}.sub{color:#9aa4b2;margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:#12161c;border:1px solid #242b35;border-radius:14px;padding:16px}
.k{color:#9aa4b2;font-size:12px;text-transform:uppercase;letter-spacing:.08em}.v{font-size:20px;font-weight:700;margin:5px 0 10px}
.row{display:flex;justify-content:space-between;gap:14px;border-top:1px solid #202630;padding:9px 0;font-size:14px}
.row span:first-child{color:#9aa4b2}.ok{color:#59d185}.bad{color:#ff6b6b}.warn{color:#f2c94c}
.footer{margin-top:16px;color:#7f8996;font-size:12px}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all}
</style>
</head>
<body><main class="wrap">
<h1>Crypto Edge Radar V0.9</h1>
<div class="sub">Persistent public shadow · read-only · no exchange mutation</div>
<div class="grid">
<section class="card"><div class="k">Runtime</div><div id="health" class="v">Loading…</div>
<div class="row"><span>Mode</span><span id="mode">—</span></div>
<div class="row"><span>Evidence</span><span id="evidence">—</span></div>
<div class="row"><span>Chain</span><span id="chain">—</span></div>
<div class="row"><span>Checked</span><span id="checked">—</span></div></section>

<section class="card"><div class="k">TFG Donchian Regime</div><div id="tfgStatus" class="v">—</div>
<div class="row"><span>Provider</span><span id="tfgProvider">—</span></div>
<div class="row"><span>Latest boundary</span><span id="tfgBoundary">—</span></div>
<div class="row"><span>Regime ON boundaries</span><span id="tfgRegime">—</span></div>
<div class="row"><span>Eligible signals</span><span id="tfgSignals">—</span></div></section>

<section class="card"><div class="k">TFG Forward Gate</div><div id="tfgGate" class="v">—</div>
<div class="row"><span>Progress</span><span id="tfgProgress">—</span></div>
<div class="row"><span>BASE expectancy</span><span id="tfgBaseExp">—</span></div>
<div class="row"><span>BASE PF</span><span id="tfgBasePf">—</span></div>
<div class="row"><span>STRESS expectancy</span><span id="tfgStressExp">—</span></div>
<div class="row"><span>STRESS PF</span><span id="tfgStressPf">—</span></div>
<div class="row"><span>BASE max DD</span><span id="tfgDD">—</span></div></section>

<section class="card"><div class="k">BNB Launchpool</div><div id="bnbStatus" class="v">—</div>
<div class="row"><span>Official source</span><span id="bnbOfficial">—</span></div>
<div class="row"><span>Market source</span><span id="bnbMarket">—</span></div>
<div class="row"><span>Eligible events</span><span id="bnbEvents">—</span></div>
<div class="row"><span>Clusters visible</span><span id="bnbClusters">—</span></div></section>

<section class="card"><div class="k">ETF-CME EXEC-V2</div><div id="etfStatus" class="v">—</div>
<div class="row"><span>Spot spread bps</span><span id="etfSpread">—</span></div>
<div class="row"><span>Perp-spot basis bps</span><span id="etfBasis">—</span></div>
<div class="row"><span>SHORT fee+spread proxy</span><span id="etfShortProxy">—</span></div>
<div class="row"><span>SHORT trailing 7d proxy</span><span id="etfShortTrailing">—</span></div>
<div class="row"><span>Historical break-even</span><span id="etfBE">—</span></div>
<div class="row"><span>Account fee</span><span id="etfFee">UNVERIFIED</span></div></section>

<section class="card"><div class="k">ETF-CME Signal Watcher</div><div id="etfSignalStatus" class="v">—</div>
<div class="row"><span>Source</span><span id="etfSignalSource">—</span></div>
<div class="row"><span>Last success</span><span id="etfSignalSuccess">—</span></div>
<div class="row"><span>Next window</span><span id="etfSignalNext">—</span></div>
<div class="row"><span>Direction</span><span id="etfSignalDirection">—</span></div>
<div class="row"><span>Missed</span><span id="etfSignalMissed">—</span></div></section>

<section class="card"><div class="k">OPTIONS-SPOTPERP V2.1</div><div id="optStatus" class="v">—</div>
<div class="row"><span>First signal day</span><span id="optFirst">—</span></div>
<div class="row"><span>Signal days</span><span id="optDays">—</span></div>
<div class="row"><span>Resolved trades</span><span id="optResolved">—</span></div>
<div class="row"><span>BASE mean bps</span><span id="optBase">—</span></div>
<div class="row"><span>BASE PF</span><span id="optPf">—</span></div>
<div class="row"><span>STRESS mean bps</span><span id="optStress">—</span></div></section>

<section class="card"><div class="k">External Collectors</div><div class="v">Freshness</div>
<div class="row"><span>DH03</span><span id="dh03Freshness">—</span></div>
<div class="row"><span>DH03 last run</span><span id="dh03Run">—</span></div>
<div class="row"><span>CED1D-0031</span><span id="cedFreshness">—</span></div>
<div class="row"><span>CED last run</span><span id="cedRun">—</span></div></section>

<section class="card"><div class="k">Safety</div><div class="v ok">FAIL-CLOSED</div>
<div class="row"><span>Authenticated API</span><span id="auth">—</span></div>
<div class="row"><span>Orders created</span><span id="orders">—</span></div>
<div class="row"><span>Exchange mutation</span><span id="mutation">—</span></div>
<div class="row"><span>Live capital</span><span id="capital">—</span></div></section>
</div>
<div class="footer">Auto-refresh every 15s · raw state: <span class="mono">/api/state</span></div>
</main>
<script>
const $=id=>document.getElementById(id);
const val=(x,f="—")=>x===undefined||x===null?f:String(x);
function paint(id,text,ok){const e=$(id);e.textContent=val(text);e.className="v "+(ok===true?"ok":ok===false?"bad":"");}
function tf(v){return v===false?"NO":v===true?"YES":val(v)}
async function refresh(){
  try{
    const r=await fetch("/api/state",{cache:"no-store"}); const s=await r.json();
    paint("health",s.health,s.health==="OK");
    $("mode").textContent=val(s.mode); $("evidence").textContent=val(s.evidence_backend);
    $("chain").textContent=(s.evidence_chain_ok?"OK · ":"FAIL · ")+val(s.evidence_chain_detail);
    $("checked").textContent=val(s.checked_at_utc);
    const t=s.tfg||{}; paint("tfgStatus",t.status,t.status==="OK"||String(t.status||"").startsWith("IDLE_"));
    $("tfgProvider").textContent=val(t.provider); $("tfgBoundary").textContent=val(t.latest_due_signal_close_utc,val(t.latest_seen_boundary_ms));
    $("tfgRegime").textContent=val(t.regime_on_boundaries); $("tfgSignals").textContent=val(t.eligible_signal_count);
    const m=s.tfg_forward_metrics||{}; paint("tfgGate",m.classification,m.readiness_gate_pass===true);
    $("tfgProgress").textContent=val(m.progress);
    $("tfgBaseExp").textContent=val(m.base_expectancy_r);
    $("tfgBasePf").textContent=m.base_profit_factor_infinite?"INF":val(m.base_profit_factor);
    $("tfgStressExp").textContent=val(m.stress_expectancy_r);
    $("tfgStressPf").textContent=m.stress_profit_factor_infinite?"INF":val(m.stress_profit_factor);
    $("tfgDD").textContent=val(m.base_max_additive_drawdown_r);
    const b=s.bnb_launchpool||{}; paint("bnbStatus",b.status,b.status==="OK");
    $("bnbOfficial").textContent=val(b.official_source_provider); $("bnbMarket").textContent=val(b.market_provider);
    $("bnbEvents").textContent=val(b.eligible_events_visible); $("bnbClusters").textContent=val(b.clusters_visible);
    const e=s.etf_exec_v2_public||{}; paint("etfStatus",e.status,e.status==="OK");
    const sm=e.spot_mapping||{}, sf=e.short_perp_friction||{};
    $("etfSpread").textContent=val(sm.spread_bps); $("etfBasis").textContent=val(sm.perp_minus_spot_mid_bps);
    $("etfShortProxy").textContent=val(sf.same_book_taker_round_trip_proxy_bps);
    $("etfShortTrailing").textContent=val(sf.trailing_short_fee_spread_funding_bps);
    $("etfBE").textContent=val(sf.historical_break_even_bps);
    $("etfFee").textContent=e.account_fee_verified_read_only?"VERIFIED":"UNVERIFIED";
    const es=s.etf_cme_signal||{}; paint("etfSignalStatus",es.status,es.source_status==="OK"&&es.status!=="MISSED_EXPECTED_OBSERVATION_NO_CHASE");
    $("etfSignalSource").textContent=val(es.source_status); $("etfSignalSuccess").textContent=val(es.last_source_success_utc);
    $("etfSignalNext").textContent=val(es.next_expected_source_window); $("etfSignalDirection").textContent=val(es.signal_direction);
    $("etfSignalMissed").textContent=val(es.missed_expected_observation_count,0);
    const o=s.options_v21||{}, om=s.options_v21_metrics||{};
    paint("optStatus",o.status,o.status==="OK"||String(o.status||"").startsWith("WAITING_"));
    $("optFirst").textContent=val(o.first_signal_day);
    $("optDays").textContent=val(om.signal_days_observed,0);
    $("optResolved").textContent=val(om.resolved_forward_trades,0);
    $("optBase").textContent=val(om.base_net_mean_bps);
    $("optPf").textContent=om.base_profit_factor===Infinity?"INF":val(om.base_profit_factor);
    $("optStress").textContent=val(om.stress_net_mean_bps);
    const xc=s.external_collectors||{};
    const dh=xc["HTF-DH03-12H-STANDALONE-FORWARD-V1"]||{}, ce=xc["CED1D-0031"]||{};
    $("dh03Freshness").textContent=val(dh.freshness_classification); $("dh03Run").textContent=val(dh.last_workflow_run_id);
    $("cedFreshness").textContent=val(ce.freshness_classification); $("cedRun").textContent=val(ce.last_workflow_run_id);
    $("auth").textContent=tf(s.authenticated_exchange_api_used); $("orders").textContent=tf(s.orders_created);
    $("mutation").textContent=tf(s.exchange_mutation_performed); $("capital").textContent=tf(s.live_capital_enabled);
  }catch(e){paint("health","UNREACHABLE",false)}
}
refresh(); setInterval(refresh,15000);
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    runtime: ForwardShadowRuntime

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, body: str) -> None:
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send_html(200, dashboard_html())
            return
        if self.path in ("/health", "/api/state"):
            state = self.runtime.state()
            status = 200 if state.get("health") in ("OK", "STARTING") else 503
            self._send_json(status, state)
            return
        if self.path == "/api/diamond":
            state = self.runtime.state()
            self._send_json(200, state.get("diamond_board") or {})
            return
        if self.path == "/api/ced1d-source-probe":
            result = ced1d_render_source_probe(timeout=self.runtime.settings.http_timeout)
            self._send_json(200, result)
            return
        self._send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve_forward_shadow(*, port: int, interval: float) -> int:
    settings = Settings.from_env()
    runtime = ForwardShadowRuntime(settings=settings)
    quiesced = os.getenv("RADAR_EVIDENCE_WRITES_QUIESCED", "").lower() == "true"

    if quiesced:
        chain_ok, chain_detail = runtime.store.verify_chain()
        state = {
            "health": "OK" if chain_ok else "DEGRADED_FAIL_CLOSED",
            "mode": "EVIDENCE_WRITES_QUIESCED",
            "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "version": "0.9",
            "runtime_identity": _runtime_identity(),
            "evidence_backend": runtime.store.backend,
            "evidence_chain_ok": chain_ok,
            "evidence_chain_detail": chain_detail,
            "maintenance_quiesce": True,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        runtime._set_state(state)
        print(json.dumps(state, sort_keys=True), flush=True)
    else:
        runtime.run_cycle()

    if os.getenv("RADAR_BACKUP_LOG_EMIT_ON_START", "").lower() == "true":
        emit_snapshot_log_chunks(runtime.store)
    if os.getenv("RADAR_BACKUP_JSON_LOG_EMIT_ON_START", "").lower() == "true":
        emit_snapshot_json_chunks(runtime.store)

    if not quiesced:
        exact_etf_worker = threading.Thread(
            target=runtime.etf_cme_exact_scheduler.run_loop,
            name="etf-cme-exact-timing-scheduler",
            daemon=True,
        )
        exact_etf_worker.start()

        worker = threading.Thread(
            target=runtime.run_loop,
            kwargs={"interval_seconds": interval},
            name="forward-shadow-watchers",
            daemon=True,
        )
        worker.start()

    handler = type("ForwardShadowHandler", (_Handler,), {"runtime": runtime})
    server = ThreadingHTTPServer(("0.0.0.0", int(port)), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0
