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
from .tfg_forward_watcher import (
    TFGForwardShadowWatcher,
    latest_certifiable_signal_close_ms,
)


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
        self.status_path = os.getenv("RADAR_FORWARD_STATUS", settings.status_path)
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "health": "STARTING",
            "mode": "PUBLIC_SHADOW_ONLY",
            "evidence_backend": self.store.backend,
            "orders_created": False,
        }
        self._last_tfg_due: int | None = None

    def state(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

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

        state = {
            "health": "OK" if not errors else "DEGRADED_FAIL_CLOSED",
            "mode": "PUBLIC_SHADOW_ONLY",
            "checked_at_utc": checked,
            "version": "0.9",
            "evidence_backend": self.store.backend,
            "evidence_chain_ok": chain_ok,
            "evidence_chain_detail": chain_detail,
            "tfg": tfg_state,
            "bnb_launchpool": bnb_state,
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

<section class="card"><div class="k">BNB Launchpool</div><div id="bnbStatus" class="v">—</div>
<div class="row"><span>Official source</span><span id="bnbOfficial">—</span></div>
<div class="row"><span>Market source</span><span id="bnbMarket">—</span></div>
<div class="row"><span>Eligible events</span><span id="bnbEvents">—</span></div>
<div class="row"><span>Clusters visible</span><span id="bnbClusters">—</span></div></section>

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
    const b=s.bnb_launchpool||{}; paint("bnbStatus",b.status,b.status==="OK");
    $("bnbOfficial").textContent=val(b.official_source_provider); $("bnbMarket").textContent=val(b.market_provider);
    $("bnbEvents").textContent=val(b.eligible_events_visible); $("bnbClusters").textContent=val(b.clusters_visible);
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
