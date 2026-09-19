from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .deployment import RiskLimits

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PROJECT_ROOT / "deployment_registry_v1.json"
DH03_STRATEGY_ID = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
LOCAL_FORWARD_STRATEGY_IDS = {
    "BNB-LAUNCHPOOL-DEMAND-001",
    "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
    "OPTIONS-SPOTPERP-001-V2.1",
    "ETF-CME-INSTFLOW-001",
    "EMA6H-50X200-REGIME-DEPENDENCY-001",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        if not path.exists():
            return default
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else default
    except Exception:
        return default


def _read_jsonl_tail(path: Path, limit: int = 30) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    except Exception:
        return []
    return rows


def _bot_operating_state(
    candidate: dict[str, Any],
    *,
    dh03_status: dict[str, Any] | None = None,
    forward_supervisor_status: dict[str, Any] | None = None,
    forward_state: dict[str, Any] | None = None,
) -> str:
    strategy_id = str(candidate.get("strategy_id") or "")
    deployment_state = str(candidate.get("deployment_state") or "").upper()
    if deployment_state.startswith("BLOCKED") or candidate.get("scientific_tier") == 4:
        return "BLOCKED"
    if candidate.get("micro_live_allowed_now") is True:
        return "ARMED"

    # DH03 is special: registry readiness alone must never inflate the live
    # cockpit. It becomes SHADOW only after the canonical local collector
    # reports COLLECTING. BOOTSTRAPPING/missing remains GATED; FAIL_CLOSED is
    # an operational BLOCKED state.
    if strategy_id == DH03_STRATEGY_ID:
        status = str((dh03_status or {}).get("status") or "MISSING").upper()
        if status == "COLLECTING":
            return "SHADOW"
        if status == "FAIL_CLOSED":
            return "BLOCKED"
        return "GATED"

    # The five public forward engines are real local runtime components.
    # Registry readiness alone must not display SHADOW if their supervisor is
    # missing or their shared runtime has failed closed.
    if strategy_id in LOCAL_FORWARD_STRATEGY_IDS:
        supervisor = str((forward_supervisor_status or {}).get("status") or "MISSING").upper()
        health = str((forward_state or {}).get("health") or "MISSING").upper()
        if supervisor == "FAIL_CLOSED" or health == "DEGRADED_FAIL_CLOSED":
            return "BLOCKED"
        if supervisor == "RUNNING" and health == "OK":
            return "SHADOW"
        return "GATED"

    if candidate.get("shadow_allowed") is True or "SHADOW" in deployment_state or "WATCHER" in deployment_state:
        return "SHADOW"
    return "GATED"


def build_control_room_state(
    *,
    status_path: str,
    notification_path: str,
    registry_path: str | None = None,
) -> dict[str, Any]:
    selected_registry = Path(registry_path) if registry_path else DEFAULT_REGISTRY
    registry = _read_json(selected_registry, {"candidates": []})
    service_status_path = Path(status_path)
    service = _read_json(service_status_path, {"health": "UNKNOWN"})
    events = _read_jsonl_tail(Path(notification_path))
    dh03_status_path = service_status_path.parent / "dh03_local_status.json"
    dh03_status = _read_json(dh03_status_path, {})
    forward_supervisor_status_path = service_status_path.parent / "forward_local_supervisor_status.json"
    forward_supervisor_status = _read_json(forward_supervisor_status_path, {})
    forward_status_path = service_status_path.parent / "forward_local_status.json"
    forward_state = _read_json(forward_status_path, {})
    render_sentinel_path = service_status_path.parent / "render_sentinel_status.json"
    render_sentinel = _read_json(render_sentinel_path, {})
    render_sentinel_supervisor_path = service_status_path.parent / "render_sentinel_supervisor_status.json"
    render_sentinel_supervisor = _read_json(render_sentinel_supervisor_path, {})

    candidates = registry.get("candidates") or []
    focus_ids = registry.get("focus_strategy_ids") or [
        "ETF-CME-INSTFLOW-001",
        "BNB-LAUNCHPOOL-DEMAND-001",
        "OPTIONS-SPOTPERP-001-V2.1",
        "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
        "HTF-DH03-12H-STANDALONE-FORWARD-V1",
    ]
    focus_id_set = {str(x) for x in focus_ids}

    bots: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        blockers = candidate.get("blocking_gates") or []
        if isinstance(blockers, str):
            blockers = [blockers]
        strategy_id = str(candidate.get("strategy_id", "UNKNOWN"))
        operating_state = _bot_operating_state(
            candidate,
            dh03_status=dh03_status,
            forward_supervisor_status=forward_supervisor_status,
            forward_state=forward_state,
        )
        runtime_status = None
        if strategy_id == DH03_STRATEGY_ID:
            runtime_status = str(dh03_status.get("status") or "MISSING")
            if operating_state == "GATED":
                blockers = list(blockers) + [f"local DH03 collector runtime not COLLECTING ({runtime_status})"]
            elif operating_state == "BLOCKED":
                err = dh03_status.get("error")
                blockers = list(blockers) + [f"local DH03 collector FAIL_CLOSED{': ' + str(err) if err else ''}"]
        elif strategy_id in LOCAL_FORWARD_STRATEGY_IDS:
            supervisor = str(forward_supervisor_status.get("status") or "MISSING")
            health = str(forward_state.get("health") or "MISSING")
            runtime_status = f"FORWARD_SUPERVISOR={supervisor};FORWARD_HEALTH={health}"
            if operating_state == "GATED":
                blockers = list(blockers) + [f"local forward runtime not healthy ({runtime_status})"]
            elif operating_state == "BLOCKED":
                err = forward_supervisor_status.get("error") or (forward_state.get("errors") or {})
                blockers = list(blockers) + [f"local forward runtime FAIL_CLOSED ({runtime_status}){': ' + str(err) if err else ''}"]
        bots.append(
            {
                "strategy_id": strategy_id,
                "tier": candidate.get("scientific_tier"),
                "scientific_status": candidate.get("scientific_status", "UNKNOWN"),
                "deployment_state": candidate.get("deployment_state", "UNKNOWN"),
                "operating_state": operating_state,
                "shadow_allowed": bool(candidate.get("shadow_allowed")),
                "runtime_status": runtime_status,
                "micro_live_allowed_now": bool(candidate.get("micro_live_allowed_now")),
                "blockers": blockers,
                "reason": candidate.get("reason"),
            }
        )

    focus = [bot for bot in bots if str(bot["strategy_id"]) in focus_id_set]
    counts = {
        key: sum(1 for bot in focus if bot["operating_state"] == key)
        for key in ("ARMED", "SHADOW", "GATED", "BLOCKED")
    }
    registry_ok = bool(registry.get("registry_version")) and len(focus) == len(focus_id_set)
    service_health = str(service.get("health", "UNKNOWN"))

    # Local V0.14.1 control-plane health is independent of one legacy market
    # provider. Individual motors retain fail-closed runtime truth. The cockpit
    # stays reachable for diagnosis even when a motor blocks itself.
    forward_supervisor = str(forward_supervisor_status.get("status") or "MISSING").upper()
    forward_health = str(forward_state.get("health") or "MISSING").upper()
    dh03_runtime = str(dh03_status.get("status") or "MISSING").upper()
    sentinel_supervisor = str(render_sentinel_supervisor.get("status") or "MISSING").upper()
    sentinel_runtime = str(render_sentinel.get("status") or "MISSING").upper()
    if not registry_ok:
        effective_health = "REGISTRY_DESYNC"
    elif (
        forward_supervisor == "FAIL_CLOSED"
        or forward_health == "DEGRADED_FAIL_CLOSED"
        or dh03_runtime == "FAIL_CLOSED"
        or sentinel_supervisor == "FAIL_CLOSED"
        or sentinel_runtime == "REMOTE_FAIL_CLOSED"
    ):
        effective_health = "DEGRADED_FAIL_CLOSED"
    else:
        effective_health = "OK"
    limits = RiskLimits()

    return {
        "generated_at_utc": _utc_now(),
        "system": {
            "name": "CRYPTO EDGE RADAR",
            "mode": "AGGRESSIVE_FAIL_CLOSED",
            "market_provider": service.get("provider", "UNKNOWN"),
            "health": effective_health,
            "market_health": service_health,
            "cycle": service.get("cycle"),
            "universe": service.get("universe", []),
            "live_order_transport_enabled": False,
            "authenticated_exchange_api_enabled": False,
        },
        "registry": {
            "ok": registry_ok,
            "path": str(selected_registry),
            "exists": selected_registry.exists(),
            "candidate_count": len(candidates),
            "focus_expected": len(focus_id_set),
            "focus_loaded": len(focus),
            "focus_strategy_ids": list(focus_ids),
        },
        "local_runtime": {
            "dh03_status_path": str(dh03_status_path),
            "dh03_status": str(dh03_status.get("status") or "MISSING"),
            "forward_supervisor_status_path": str(forward_supervisor_status_path),
            "forward_supervisor_status": str(forward_supervisor_status.get("status") or "MISSING"),
            "forward_status_path": str(forward_status_path),
            "forward_health": str(forward_state.get("health") or "MISSING"),
            "render_sentinel_status_path": str(render_sentinel_path),
            "render_sentinel_status": str(render_sentinel.get("status") or "MISSING"),
            "render_sentinel_supervisor_status": str(render_sentinel_supervisor.get("status") or "MISSING"),
            "render_sentinel_last_check_utc": render_sentinel.get("checked_at_utc"),
        },
        "risk_policy": {
            "planned_risk_per_trade_pct": limits.per_trade * 100,
            "max_concurrent_risk_pct": limits.max_concurrent * 100,
            "daily_stop_pct": limits.daily_stop * 100,
            "weekly_stop_pct": limits.weekly_stop * 100,
        },
        "focus_counts": counts,
        "bots": focus,
        "recent_events": events,
        "registry_version": registry.get("registry_version"),
        "governance": registry.get("governance"),
    }


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crypto Edge Radar — Control Room</title>
<style>
:root{--bg:#07090d;--panel:#10141b;--line:#252c37;--text:#f4f7fb;--muted:#9099a8;--ok:#59e19a;--warn:#ffd166;--bad:#ff6b6b;--cyan:#55d7ff}
*{box-sizing:border-box}body{margin:0;background:#07090d;color:var(--text);font-family:Inter,system-ui,sans-serif}.wrap{max-width:1400px;margin:auto;padding:28px}.top{display:flex;justify-content:space-between;gap:20px;margin-bottom:22px}.eyebrow{font-size:12px;letter-spacing:.18em;color:var(--cyan);font-weight:800}.title{font-size:34px;font-weight:850;margin-top:5px}.sub{color:var(--muted);margin-top:6px}.health,.metric,.card,.feed,.cell{border:1px solid var(--line);background:var(--panel);border-radius:15px}.health{padding:13px 16px;min-width:260px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;background:var(--warn)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.metric{padding:17px}.metric .n{font-size:28px;font-weight:850}.metric .k{font-size:11px;color:var(--muted);letter-spacing:.1em}.bots{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.card{padding:20px}.row{display:flex;justify-content:space-between;gap:12px}.id{font-size:17px;font-weight:800}.badge{font-size:11px;font-weight:850;padding:6px 9px;border-radius:999px;border:1px solid var(--line)}.ARMED{color:var(--ok)}.SHADOW{color:var(--cyan)}.GATED{color:var(--warn)}.BLOCKED{color:var(--bad)}.meta,.risk{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}.meta{grid-template-columns:1fr 1fr}.cell{padding:11px}.cell b{display:block;font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:5px}.blockers{font-size:12px;color:#c1c8d4;line-height:1.5;margin-top:13px}.section{margin-top:20px}.section h2{font-size:13px;color:var(--muted);letter-spacing:.09em}.feed{padding:14px;max-height:250px;overflow:auto;font:11px ui-monospace,monospace}.event{padding:7px;border-bottom:1px solid #1a202b}.footer{font-size:11px;color:#667080;margin-top:16px;text-align:right}.diag{font-size:11px;color:var(--muted);margin-top:6px}@media(max-width:850px){.grid,.risk,.bots{grid-template-columns:1fr}.top{flex-direction:column}.health{width:100%}}
</style></head><body><div class="wrap">
<div class="top"><div><div class="eyebrow">AGGRESSIVE MODE · SCIENCE FROZEN · V3 AUTHORITY</div><div class="title">Crypto Edge Radar — Control Room</div><div class="sub">Prospective observation · fail-closed deployment gates · no discretionary rescue</div></div><div class="health"><div><span id="dot" class="dot"></span><strong id="health">LOADING</strong></div><div class="sub" id="provider"></div><div class="diag" id="diag"></div></div></div>
<div class="grid"><div class="metric"><div class="n" id="armed">0</div><div class="k">ARMED</div></div><div class="metric"><div class="n" id="shadow">0</div><div class="k">SHADOW</div></div><div class="metric"><div class="n" id="gated">0</div><div class="k">GATED</div></div><div class="metric"><div class="n" id="blocked">0</div><div class="k">BLOCKED</div></div></div>
<div class="bots" id="bots"></div><div class="section"><h2>RISK FIREWALL</h2><div class="risk" id="risk"></div></div><div class="section"><h2>RECENT MACHINE EVENTS</h2><div class="feed" id="events"></div></div><div class="footer" id="stamp"></div></div>
<script>
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function refresh(){try{const r=await fetch('/api/state',{cache:'no-store'}),d=await r.json(),s=d.system||{},rg=d.registry||{};document.getElementById('health').textContent=s.health||'UNKNOWN';document.getElementById('provider').textContent=(s.market_provider||'UNKNOWN')+' · '+(s.universe||[]).join(' / ');document.getElementById('dot').style.background=s.health==='OK'?'var(--ok)':'var(--bad)';document.getElementById('diag').textContent='registry '+(d.registry_version||'NULL')+' · '+(rg.focus_loaded??0)+'/'+(rg.focus_expected??0)+' focus loaded';for(const k of ['armed','shadow','gated','blocked'])document.getElementById(k).textContent=(d.focus_counts||{})[k.toUpperCase()]||0;document.getElementById('bots').innerHTML=(d.bots||[]).map(b=>`<div class="card"><div class="row"><div class="id">${esc(b.strategy_id)}</div><div class="badge ${esc(b.operating_state)}">${esc(b.operating_state)}</div></div><div class="meta"><div class="cell"><b>Tier</b>${esc(b.tier)}</div><div class="cell"><b>Deployment</b>${esc(b.deployment_state)}</div><div class="cell"><b>Shadow allowed</b>${b.shadow_allowed?'YES':'NO'}${b.runtime_status?'<br><span class="diag">runtime '+esc(b.runtime_status)+'</span>':''}</div><div class="cell"><b>Micro-live</b>${b.micro_live_allowed_now?'YES':'NO'}</div></div><div class="blockers">${(b.blockers||[]).length?'<b>Gates:</b> '+b.blockers.map(esc).join(' · '):esc(b.reason||'No active blocker text')}</div></div>`).join('')||'<div class="card BLOCKED">REGISTRY DESYNC — no focus bots loaded.</div>';const rp=d.risk_policy||{};document.getElementById('risk').innerHTML=[['Trade',rp.planned_risk_per_trade_pct],['Concurrent',rp.max_concurrent_risk_pct],['Daily stop',rp.daily_stop_pct],['Weekly stop',rp.weekly_stop_pct]].map(x=>`<div class="cell"><b>${x[0]}</b>${Number(x[1]||0).toFixed(2)}%</div>`).join('');const ev=(d.recent_events||[]).slice().reverse();document.getElementById('events').innerHTML=ev.length?ev.map(e=>`<div class="event">${esc(e.ts_utc||'')} · <b>${esc(e.event_type||'EVENT')}</b> · ${esc(JSON.stringify(e.payload||{}))}</div>`).join(''):'No machine events yet.';document.getElementById('stamp').textContent='Updated '+(d.generated_at_utc||'');}catch(e){document.getElementById('health').textContent='DASHBOARD ERROR';document.getElementById('dot').style.background='var(--bad)';}}
refresh();setInterval(refresh,3000);
</script></body></html>"""


class _DashboardHandler(BaseHTTPRequestHandler):
    status_path = "radar_status.json"
    notification_path = "radar_notifications.jsonl"
    registry_path: str | None = None

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
            return
        if path == "/api/state":
            state = build_control_room_state(status_path=self.status_path, notification_path=self.notification_path, registry_path=self.registry_path)
            self._send(200, "application/json; charset=utf-8", json.dumps(state, sort_keys=True).encode("utf-8"))
            return
        if path == "/healthz":
            state = build_control_room_state(status_path=self.status_path, notification_path=self.notification_path, registry_path=self.registry_path)
            ok = state["system"]["health"] == "OK"
            body = json.dumps({"ok": ok, "role": "read-only-control-room", "health": state["system"]["health"]}, sort_keys=True).encode("utf-8")
            self._send(200 if ok else 503, "application/json", body)
            return
        self._send(404, "application/json", b'{"error":"not_found"}')

    def log_message(self, format: str, *args: Any) -> None:
        if os.getenv("RADAR_DASHBOARD_LOG_HTTP") == "1":
            super().log_message(format, *args)


def serve_dashboard(*, host: str, port: int, status_path: str, notification_path: str, registry_path: str | None = None) -> None:
    if not (1 <= port <= 65535):
        raise ValueError("port must be between 1 and 65535")
    handler = type("ConfiguredDashboardHandler", (_DashboardHandler,), {"status_path": status_path, "notification_path": notification_path, "registry_path": registry_path})
    server = ThreadingHTTPServer((host, port), handler)
    print(json.dumps({"dashboard": f"http://{host}:{port}", "mode": "READ_ONLY_CONTROL_ROOM"}, sort_keys=True))
    server.serve_forever()
