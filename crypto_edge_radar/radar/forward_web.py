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
from .evidence import build_evidence_store
from .strategies.bnb_launchpool_demand import BinanceSpotBNBBTCKlineFeed
from .strategies.tfg_donchian_regime_forward import MEXCSpotKlineFeed
from .spot_mapping import spot_perp_mapping_receipt
from .friction import mexc_friction_shadow_receipt
from .tfg_forward_watcher import (
    TFGForwardShadowWatcher,
    latest_certifiable_signal_close_ms,
)
from .tfg_forward_metrics import evaluate_tfg_forward_evidence
from .options_v21_live import BinanceBTCUSDTDailyFeed, DeribitBTCOptionTradeFeed
from .options_v21_watcher import OptionsV21ForwardShadowWatcher
from .options_v21_metrics import evaluate_options_v21_forward
from .dh03_archive_watcher import run_once as run_dh03_archive_shadow


class CachingBinanceOfficialLaunchpoolSource(BinanceOfficialLaunchpoolSource):
    """Rate-limit-aware official CMS cache. Never used as execution authority."""

    def __init__(self, timeout: int = 15) -> None:
        super().__init__(timeout=timeout)
        self._detail_cache: dict[str, tuple[Any, bytes]] = {}
        self._catalog_cache: tuple[Any, bytes] | None = None
        self._catalog_cached_at: float | None = None
        self._catalog_ttl_seconds = 600.0
        self._catalog_backoff_until = 0.0
        self._catalog_failures = 0
        self.catalog_status = "STARTING"

    def catalog(self) -> tuple[Any, bytes]:
        now = time.monotonic()
        if (
            self._catalog_cache is not None
            and self._catalog_cached_at is not None
            and now - self._catalog_cached_at < self._catalog_ttl_seconds
        ):
            self.catalog_status = "CACHE_FRESH"
            return self._catalog_cache
        if self._catalog_cache is not None and now < self._catalog_backoff_until:
            self.catalog_status = "CACHE_BACKOFF_STALE"
            return self._catalog_cache
        try:
            result = super().catalog()
        except Exception as exc:
            if "429" in str(exc) and self._catalog_cache is not None:
                self._catalog_failures += 1
                backoff = min(3600.0, 300.0 * (2 ** (self._catalog_failures - 1)))
                self._catalog_backoff_until = now + backoff
                self.catalog_status = "CACHE_BACKOFF_STALE"
                return self._catalog_cache
            raise
        self._catalog_cache = result
        self._catalog_cached_at = now
        self._catalog_backoff_until = 0.0
        self._catalog_failures = 0
        self.catalog_status = "LIVE"
        return result

    def detail(self, article_code: str) -> tuple[Any, bytes]:
        cached = self._detail_cache.get(article_code)
        if cached is not None:
            return cached
        result = super().detail(article_code)
        self._detail_cache[article_code] = result
        return result


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
        self.bnb = BNBLaunchpoolForwardShadowWatcher(
            store=self.store,
            source=CachingBinanceOfficialLaunchpoolSource(timeout=settings.http_timeout),
            market=BinanceSpotBNBBTCKlineFeed(timeout=settings.http_timeout),
        )
        self.options_v21 = OptionsV21ForwardShadowWatcher(
            store=self.store,
            options_feed=DeribitBTCOptionTradeFeed(timeout=settings.http_timeout),
            btc_feed=BinanceBTCUSDTDailyFeed(timeout=settings.http_timeout),
        )
        self.status_path = os.getenv("RADAR_FORWARD_STATUS", settings.status_path)
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "health": "STARTING",
            "mode": "PUBLIC_SHADOW_ONLY",
            "evidence_backend": self.store.backend,
            "orders_created": False,
        }
        self._last_tfg_due: int | None = None
        self._last_etf_public_check_ms: int | None = None
        self._last_options_runtime_day: str | None = None
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
        self._dh03_thread: threading.Thread | None = None
        self._dh03_last_attempt_day: str | None = None
        self._dh03_state: dict[str, Any] = {
            "status": "STARTING",
            "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
            "mode": "PUBLIC_ARCHIVE_SHADOW_ONLY",
            "live_capital_enabled": False,
            "orders_created": False,
        }

    def state(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def _set_state(self, value: dict[str, Any]) -> None:
        with self._lock:
            self._state = value
        _atomic_json_write(self.status_path, value)

    def _dh03_worker(self) -> None:
        try:
            receipt = run_dh03_archive_shadow(persist=True)
            totals = ((receipt.get("evaluation") or {}).get("totals") or {})
            summary = {
                "status": receipt.get("status", "UNKNOWN"),
                "strategy_id": receipt.get("strategy_id", "HTF-DH03-12H-STANDALONE-FORWARD-V1"),
                "mode": receipt.get("mode", "PUBLIC_ARCHIVE_SHADOW_ONLY"),
                "latest_archive_day": receipt.get("latest_archive_day"),
                "signals": totals.get("signals", 0),
                "price_exits": totals.get("price_exits", 0),
                "final_resolutions": totals.get("final_resolutions", 0),
                "funding_pending": totals.get("funding_pending", 0),
                "unresolved_price_paths": totals.get("unresolved_price_paths", 0),
                "evidence_backend": receipt.get("evidence_backend", self.store.backend),
                "evidence_chain_ok": receipt.get("evidence_chain_ok"),
                "evidence_chain_detail": receipt.get("evidence_chain_detail"),
                "live_capital_enabled": False,
                "orders_created": False,
                "authenticated_exchange_api_used": False,
                "exchange_mutation_performed": False,
            }
            if receipt.get("error"):
                summary["error"] = receipt["error"]
        except Exception as exc:
            summary = {
                "status": "FAIL_CLOSED",
                "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "mode": "PUBLIC_ARCHIVE_SHADOW_ONLY",
                "error": f"{type(exc).__name__}:{exc}",
                "live_capital_enabled": False,
                "orders_created": False,
                "authenticated_exchange_api_used": False,
                "exchange_mutation_performed": False,
            }
        with self._lock:
            self._dh03_state = summary

    def _maybe_start_dh03(self, *, runtime_day: str) -> dict[str, Any]:
        with self._lock:
            running = self._dh03_thread is not None and self._dh03_thread.is_alive()
            if self._dh03_last_attempt_day != runtime_day and not running:
                self._dh03_last_attempt_day = runtime_day
                self._dh03_state = {
                    "status": "RUNNING",
                    "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                    "mode": "PUBLIC_ARCHIVE_SHADOW_ONLY",
                    "live_capital_enabled": False,
                    "orders_created": False,
                }
                worker = threading.Thread(
                    target=self._dh03_worker,
                    name="dh03-12h-archive-shadow",
                    daemon=True,
                )
                self._dh03_thread = worker
                worker.start()
            return json.loads(json.dumps(self._dh03_state))

    def run_cycle(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        checked = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        errors: dict[str, str] = {}

        try:
            bnb_state = self.bnb.run_once(now_ms=now_ms)
            bnb_state["source_transport_status"] = getattr(
                self.bnb.source, "catalog_status", "UNKNOWN"
            )
            bnb_state["source_transport_execution_authority"] = False
        except Exception as exc:
            bnb_state = {"status": "FAIL_CLOSED", "error": f"{type(exc).__name__}:{exc}"}
            errors["bnb_launchpool"] = bnb_state["error"]

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

        dh03_runtime_day = datetime.fromtimestamp(
            now_ms / 1000.0, tz=timezone.utc
        ).date().isoformat()
        dh03_12h = self._maybe_start_dh03(runtime_day=dh03_runtime_day)
        if dh03_12h.get("status") == "FAIL_CLOSED":
            errors["dh03_12h"] = str(dh03_12h.get("error") or "FAIL_CLOSED")

        state = {
            "health": "OK" if not errors else "DEGRADED_FAIL_CLOSED",
            "mode": "PUBLIC_SHADOW_ONLY",
            "checked_at_utc": checked,
            "version": "1.0",
            "evidence_backend": self.store.backend,
            "evidence_chain_ok": chain_ok,
            "evidence_chain_detail": chain_detail,
            "tfg": tfg_state,
            "tfg_forward_metrics": tfg_forward_metrics,
            "bnb_launchpool": bnb_state,
            "etf_exec_v2_public": etf_exec_v2,
            "options_v21": options_v21,
            "options_v21_metrics": options_v21_metrics,
            "dh03_12h": dh03_12h,
            "errors": errors,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        self._set_state(state)
        print(json.dumps(state, sort_keys=True), flush=True)
        return state

    def run_loop(self, *, interval_seconds: float) -> None:
        # The old V0.5 canary start command passes 30s. Do not hammer official CMS;
        # clamp the public-shadow poll interval to a conservative two minutes.
        interval_seconds = max(float(interval_seconds), 120.0)
        while True:
            started = time.monotonic()
            try:
                self.run_cycle()
            except Exception as exc:
                fatal = {
                    "health": "DEGRADED_FAIL_CLOSED",
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
<title>Crypto Edge Radar V1.0</title>
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
<h1>Crypto Edge Radar V1.0</h1>
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

<section class="card"><div class="k">OPTIONS-SPOTPERP V2.1</div><div id="optStatus" class="v">—</div>
<div class="row"><span>First signal day</span><span id="optFirst">—</span></div>
<div class="row"><span>Signal days</span><span id="optDays">—</span></div>
<div class="row"><span>Resolved trades</span><span id="optResolved">—</span></div>
<div class="row"><span>BASE mean bps</span><span id="optBase">—</span></div>
<div class="row"><span>BASE PF</span><span id="optPf">—</span></div>
<div class="row"><span>STRESS mean bps</span><span id="optStress">—</span></div></section>

<section class="card"><div class="k">DH03 12H Standalone</div><div id="dh03Status" class="v">—</div>
<div class="row"><span>Archive day</span><span id="dh03Day">—</span></div>
<div class="row"><span>Signals</span><span id="dh03Signals">—</span></div>
<div class="row"><span>Price exits</span><span id="dh03Exits">—</span></div>
<div class="row"><span>Final resolutions</span><span id="dh03Final">—</span></div>
<div class="row"><span>Funding pending</span><span id="dh03Funding">—</span></div>
<div class="row"><span>Path unresolved</span><span id="dh03Unresolved">—</span></div></section>

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
    const o=s.options_v21||{}, om=s.options_v21_metrics||{};
    paint("optStatus",o.status,o.status==="OK"||String(o.status||"").startsWith("WAITING_"));
    $("optFirst").textContent=val(o.first_signal_day);
    $("optDays").textContent=val(om.signal_days_observed,0);
    $("optResolved").textContent=val(om.resolved_forward_trades,0);
    $("optBase").textContent=val(om.base_net_mean_bps);
    $("optPf").textContent=om.base_profit_factor===Infinity?"INF":val(om.base_profit_factor);
    $("optStress").textContent=val(om.stress_net_mean_bps);
    const d=s.dh03_12h||{};
    paint("dh03Status",d.status,d.status==="OK"||d.status==="RUNNING"||String(d.status||"").startsWith("WAITING_"));
    $("dh03Day").textContent=val(d.latest_archive_day);
    $("dh03Signals").textContent=val(d.signals,0);
    $("dh03Exits").textContent=val(d.price_exits,0);
    $("dh03Final").textContent=val(d.final_resolutions,0);
    $("dh03Funding").textContent=val(d.funding_pending,0);
    $("dh03Unresolved").textContent=val(d.unresolved_price_paths,0);
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
        self._send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve_forward_shadow(*, port: int, interval: float) -> int:
    settings = Settings.from_env()
    runtime = ForwardShadowRuntime(settings=settings)
    runtime.run_cycle()
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
