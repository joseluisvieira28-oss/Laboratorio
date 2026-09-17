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


def _bot_operating_state(candidate: dict[str, Any]) -> str:
    deployment_state = str(candidate.get("deployment_state") or "").upper()
    if deployment_state == "BLOCKED" or candidate.get("scientific_tier") == 4:
        return "BLOCKED"
    if candidate.get("micro_live_allowed_now") is True:
        return "ARMED"
    if "SHADOW" in deployment_state or candidate.get("shadow_allowed") is True:
        return "SHADOW"
    return "GATED"


def build_control_room_state(
    *,
    status_path: str,
    notification_path: str,
    registry_path: str | None = None,
) -> dict[str, Any]:
    registry = _read_json(Path(registry_path) if registry_path else DEFAULT_REGISTRY, {"candidates": []})
    service = _read_json(Path(status_path), {"health": "UNKNOWN"})
    events = _read_jsonl_tail(Path(notification_path))

    bots: list[dict[str, Any]] = []
    for candidate in registry.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        state = _bot_operating_state(candidate)
        blockers = candidate.get("blocking_gates") or []
        if isinstance(blockers, str):
            blockers = [blockers]
        bots.append(
            {
                "strategy_id": candidate.get("strategy_id", "UNKNOWN"),
                "tier": candidate.get("scientific_tier"),
                "scientific_status": candidate.get("scientific_status", "UNKNOWN"),
                "deployment_state": candidate.get("deployment_state", "UNKNOWN"),
                "operating_state": state,
                "shadow_allowed": bool(candidate.get("shadow_allowed")),
                "micro_live_allowed_now": bool(candidate.get("micro_live_allowed_now")),
                "blockers": blockers,
                "reason": candidate.get("reason"),
            }
        )

    focus = [
        bot
        for bot in bots
        if bot["strategy_id"]
        in {
            "ETF-CME-INSTFLOW-001",
            "BNB-LAUNCHPOOL-DEMAND-001",
            "BTC-OPTIONS-EXPIRY-REVERSAL-001",
            "HTF-DH03-12H",
        }
    ]
    counts = {
        key: sum(1 for bot in focus if bot["operating_state"] == key)
        for key in ("ARMED", "SHADOW", "GATED", "BLOCKED")
    }
    limits = RiskLimits()
    return {
        "generated_at_utc": _utc_now(),
        "system": {
            "name": "CRYPTO EDGE RADAR",
            "mode": "AGGRESSIVE_FAIL_CLOSED",
            "market_provider": service.get("provider", "UNKNOWN"),
            "health": service.get("health", "UNKNOWN"),
            "cycle": service.get("cycle"),
            "universe": service.get("universe", []),
            "live_order_transport_enabled": False,
            "authenticated_exchange_api_enabled": False,
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
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Crypto Edge Radar — Control Room</title>
<style>
:root{--bg:#07090d;--panel:#10141b;--line:#252c37;--text:#f4f7fb;--muted:#9099a8;--ok:#59e19a;--warn:#ffd166;--bad:#ff6b6b;--cyan:#55d7ff;--violet:#a98bff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#111827 0,#07090d 38%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh}
.wrap{max-width:1380px;margin:0 auto;padding:28px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:24px}.eyebrow{font-size:12px;letter-spacing:.18em;color:var(--cyan);font-weight:800}.title{font-size:34px;font-weight:850;letter-spacing:-.04em;margin-top:5px}.sub{color:var(--muted);margin-top:6px}.health{border:1px solid var(--line);background:rgba(16,20,27,.85);border-radius:14px;padding:12px 16px;min-width:215px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;background:var(--warn)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.metric,.card,.feed{border:1px solid var(--line);background:rgba(16,20,27,.88);border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.18)}.metric{padding:17px}.metric .n{font-size:28px;font-weight:850}.metric .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:3px}.bots{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.card{padding:20px}.row{display:flex;align-items:center;justify-content:space-between;gap:12px}.id{font-size:17px;font-weight:800;letter-spacing:-.02em}.badge{font-size:11px;font-weight:850;letter-spacing:.07em;padding:6px 9px;border-radius:999px;border:1px solid var(--line)}.ARMED{color:var(--ok);border-color:rgba(89,225,154,.4);background:rgba(89,225,154,.08)}.SHADOW{color:var(--cyan);border-color:rgba(85,215,255,.35);background:rgba(85,215,255,.08)}.GATED{color:var(--warn);border-color:rgba(255,209,102,.35);background:rgba(255,209,102,.08)}.BLOCKED{color:var(--bad);border-color:rgba(255,107,107,.35);background:rgba(255,107,107,.08)}.meta{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:17px}.cell{padding:12px;background:#0a0d12;border:1px solid #1d2330;border-radius:11px}.cell b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin-bottom:5px}.cell span{font-size:13px}.blockers{margin-top:14px;color:#c1c8d4;font-size:12px;line-height:1.55}.section{margin-top:20px}.section h2{font-size:14px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}.risk{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.risk .cell span{font-size:18px;font-weight:800}.feed{padding:15px;max-height:240px;overflow:auto;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:#b8c1cf}.event{padding:8px 4px;border-bottom:1px solid #1a202b}.empty{color:#6f7887;padding:12px 0}.footer{color:#606a79;font-size:11px;margin-top:18px;text-align:right}@media(max-width:850px){.grid,.risk,.bots{grid-template-columns:1fr}.top{flex-direction:column}.health{width:100%}.wrap{padding:18px}.title{font-size:28px}}
</style>
</head>
<body><div class="wrap">
<div class="top"><div><div class="eyebrow">AGGRESSIVE MODE · FAIL-CLOSED</div><div class="title">Crypto Edge Radar — Control Room</div><div class="sub">MEXC market observation · frozen gates · no discretionary overrides</div></div><div class="health"><div><span id="dot" class="dot"></span><strong id="health">LOADING</strong></div><div class="sub" id="provider">provider —</div></div></div>
<div class="grid"><div class="metric"><div class="n" id="armed">0</div><div class="k">Armed</div></div><div class="metric"><div class="n" id="shadow">0</div><div class="k">Shadow</div></div><div class="metric"><div class="n" id="gated">0</div><div class="k">Gated</div></div><div class="metric"><div class="n" id="blocked">0</div><div class="k">Blocked</div></div></div>
<div class="bots" id="bots"></div>
<div class="section"><h2>Risk firewall</h2><div class="risk" id="risk"></div></div>
<div class="section"><h2>Recent machine events</h2><div class="feed" id="events"></div></div>
<div class="footer" id="stamp"></div>
</div>
<script>
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function refresh(){try{const r=await fetch('/api/state',{cache:'no-store'});const d=await r.json();
const sys=d.system||{};document.getElementById('health').textContent=sys.health||'UNKNOWN';document.getElementById('provider').textContent=(sys.market_provider||'UNKNOWN')+' · '+(sys.universe||[]).join(' / ');document.getElementById('dot').style.background=sys.health==='OK'?'var(--ok)':'var(--warn)';
for(const k of ['armed','shadow','gated','blocked'])document.getElementById(k).textContent=(d.focus_counts||{})[k.toUpperCase()]||0;
const bots=(d.bots||[]).map(b=>`<div class="card"><div class="row"><div class="id">${esc(b.strategy_id)}</div><div class="badge ${esc(b.operating_state)}">${esc(b.operating_state)}</div></div><div class="meta"><div class="cell"><b>Tier</b><span>${esc(b.tier??'secondary')}</span></div><div class="cell"><b>Deployment</b><span>${esc(b.deployment_state)}</span></div><div class="cell"><b>Shadow</b><span>${b.shadow_allowed?'YES':'NO'}</span></div><div class="cell"><b>Micro-live</b><span>${b.micro_live_allowed_now?'YES':'NO'}</span></div></div><div class="blockers">${(b.blockers||[]).length?'<b>Gates:</b> '+(b.blockers||[]).map(esc).join(' · '):esc(b.reason||'No active blocker text')}</div></div>`).join('');document.getElementById('bots').innerHTML=bots||'<div class="empty">No focus bots loaded.</div>';
const rp=d.risk_policy||{};document.getElementById('risk').innerHTML=[['Trade',rp.planned_risk_per_trade_pct],['Concurrent',rp.max_concurrent_risk_pct],['Daily stop',rp.daily_stop_pct],['Weekly stop',rp.weekly_stop_pct]].map(x=>`<div class="cell"><b>${x[0]}</b><span>${Number(x[1]||0).toFixed(2)}%</span></div>`).join('');
const ev=(d.recent_events||[]).slice().reverse();document.getElementById('events').innerHTML=ev.length?ev.map(e=>`<div class="event">${esc(e.ts_utc||'')} · <b>${esc(e.event_type||'EVENT')}</b> · ${esc(JSON.stringify(e.payload||{}))}</div>`).join(''):'<div class="empty">No machine events yet.</div>';document.getElementById('stamp').textContent='Updated '+(d.generated_at_utc||'');
}catch(e){document.getElementById('health').textContent='DASHBOARD ERROR';document.getElementById('dot').style.background='var(--bad)';}}
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
            state = build_control_room_state(
                status_path=self.status_path,
                notification_path=self.notification_path,
                registry_path=self.registry_path,
            )
            self._send(200, "application/json; charset=utf-8", json.dumps(state, sort_keys=True).encode("utf-8"))
            return
        if path == "/healthz":
            self._send(200, "application/json", b'{"ok":true,"role":"read-only-control-room"}')
            return
        self._send(404, "application/json", b'{"error":"not_found"}')

    def log_message(self, format: str, *args: Any) -> None:
        if os.getenv("RADAR_DASHBOARD_LOG_HTTP") == "1":
            super().log_message(format, *args)


def serve_dashboard(
    *,
    host: str,
    port: int,
    status_path: str,
    notification_path: str,
    registry_path: str | None = None,
) -> None:
    if not (1 <= port <= 65535):
        raise ValueError("port must be between 1 and 65535")
    handler = type(
        "ConfiguredDashboardHandler",
        (_DashboardHandler,),
        {
            "status_path": status_path,
            "notification_path": notification_path,
            "registry_path": registry_path,
        },
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(json.dumps({"dashboard": f"http://{host}:{port}", "mode": "READ_ONLY_CONTROL_ROOM"}, sort_keys=True))
    server.serve_forever()
