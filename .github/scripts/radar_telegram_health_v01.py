"""Private Telegram notifications for public Radar health, never for order execution.

Bounded single GET; only https://crypto-edge-radar-v05-canary.onrender.com/api/state.
Bot token is read from environment only during send, never logged or persisted.
Github Actions handles best-effort once-per-UTC-day dedup via a cache receipt.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

RADAR_URL = "https://crypto-edge-radar-v05-canary.onrender.com/api/state"
EXPECTED_HOST = "crypto-edge-radar-v05-canary.onrender.com"
MAX_RESPONSE_BYTES = 2_000_000


def classify_snapshot(snapshot: object, *, now: datetime, fetch_error: str | None = None) -> dict:
    reasons: list[str] = []
    if fetch_error is not None:
        reasons.append("PUBLIC_RADAR_UNREACHABLE_" + fetch_error)
    if not isinstance(snapshot, dict):
        snapshot = {}
        reasons.append("NO_VALID_JSON_STATE")
    if snapshot.get("mode") != "PUBLIC_SHADOW_ONLY":
        reasons.append("PUBLIC_SHADOW_MODE_UNVERIFIED")
    if snapshot.get("health") != "OK":
        reasons.append("PUBLIC_SHADOW_HEALTH_NOT_OK")
    identity = snapshot.get("runtime_identity") or {}
    if not isinstance(identity, dict) or identity.get("service_id") != "srv-dalqkpu1egvs73fhiehg":
        reasons.append("CANONICAL_RUNTIME_IDENTITY_UNVERIFIED")
    stamp = snapshot.get("checked_at_utc")
    try:
        latest = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if latest.tzinfo is None or not (-60 <= (now - latest).total_seconds() <= 1200):
            reasons.append("SOURCE_STATE_STALE_OR_FUTURE")
    except (ValueError, TypeError, OverflowError):
        reasons.append("SOURCE_STATE_TIMESTAMP_MISSING")

    ced = snapshot.get("ced1d_render_shadow") or {}
    if not isinstance(ced, dict) or ced.get("status") in {"FAIL_CLOSED", "SOURCE_BLOCKED", "ERROR", None}:
        reasons.append("CED1D_COLLECTOR_FAIL_CLOSED_OR_UNVERIFIED")

    gaps = snapshot.get("runtime_gap_history") or {}
    if isinstance(gaps, dict):
        if gaps.get("continuity_review_status") in {
            "HISTORICAL_GAPS_REVIEW_REQUIRED", "UNVERIFIED"
        }:
            reasons.append("CONTINUITY_REVIEW_OUTSTANDING")
    else:
        reasons.append("CONTINUITY_REVIEW_UNVERIFIED")
    # Legacy live state has no lifetime gap counter. An isolated bucket's
    # CONTINUOUS classification cannot erase earlier persisted gap receipts.
    if "runtime_gap_history" not in snapshot:
        reasons.append("CONTINUITY_REVIEW_UNVERIFIED")

    flags = ("orders_created", "authenticated_exchange_api_used",
             "exchange_mutation_performed", "live_capital_enabled")
    if any(snapshot.get(k) is not False for k in flags):
        reasons.append("SHADOW_SAFETY_FLAGS_UNVERIFIED")

    # Notification categories are deliberately high-level: never forward
    # unknown payloads, credentials, prices, forecasts or execution instructions.
    reasons = sorted(set(reasons))
    status = "DEGRADED" if reasons else "OK"
    day = now.strftime("%Y-%m-%d")
    fingerprint = hashlib.sha256(
        json.dumps([day, status, reasons], separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    return {
        "schema": "RADAR_TELEGRAM_HEALTH_V0.1",
        "status": status,
        "reason_codes": reasons,
        "utc_date": day,
        "incident_key": "radar-telegram-v01-" + fingerprint,
        "notify": status != "OK",
        "orders_created": False,
        "exchange_mutation_performed": False,
        "authenticated_account_reads": False,
    }


def inspect_remote(*, url: str, timeout: int, now: datetime) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != EXPECTED_HOST or parsed.path != "/api/state":
        return classify_snapshot(None, now=now, fetch_error="BAD_CONFIGURED_URL")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "crypto-lab-health-v01"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if urlsplit(response.geturl()).hostname != EXPECTED_HOST:
                raise ValueError("UNEXPECTED_REDIRECT")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("OVERSIZE_BODY")
    except HTTPError as exc:
        # Render returns 503 with useful JSON for fail-closed health.
        if exc.code != 503:
            return classify_snapshot(None, now=now, fetch_error=f"HTTP_{exc.code}")
        body = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            return classify_snapshot(None, now=now, fetch_error="OVERSIZE_BODY")
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return classify_snapshot(None, now=now, fetch_error=type(exc).__name__.upper())
    try:
        return classify_snapshot(json.loads(body), now=now)
    except (ValueError, UnicodeError):
        return classify_snapshot(None, now=now, fetch_error="INVALID_JSON")


def _message(report: dict, *, test: bool = False) -> str:
    if test:
        return "Crypto Lab Fishing Bot — conexão de alertas testada. Modo READ-ONLY; nenhuma ordem nem trading ativados. ✅"
    reasons = "\n".join("- " + code for code in report.get("reason_codes", [])[:10])
    return (
        "🚨 CRYPTO LAB — RADAR HEALTH\n"
        f"Data UTC: {report.get('utc_date')}\n"
        f"Estado: {report.get('status')}\n"
        f"Bloqueios:\n{reasons}\n"
        "PUBLIC SHADOW ONLY • sem ordens • sem autoridade de trading.\n"
        "Não usar este aviso como sinal de entrada."
    )[:3500]


def send_telegram(report: dict, *, test: bool = False, opener=urlopen) -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return "NOT_CONFIGURED"
    if not re.fullmatch(r"[0-9]{5,16}:[A-Za-z0-9_-]{20,}", token):
        return "INVALID_BOT_TOKEN_FORMAT"
    if not re.fullmatch(r"-?[0-9]{4,20}", chat_id):
        return "INVALID_CHAT_ID_FORMAT"
    from urllib.parse import urlencode
    data = urlencode({"chat_id": chat_id, "text": _message(report, test=test),
                      "disable_notification": "false"}).encode("utf-8")
    request = Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=data, headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with opener(request, timeout=12) as response:
            body = response.read(4096)
        parsed = json.loads(body)
        return "SENT" if isinstance(parsed, dict) and parsed.get("ok") is True else "REJECTED"
    except HTTPError as exc:
        # HTTPError may stringify a URL containing the token. Do not log it.
        return "HTTP_" + str(exc.code)
    except Exception:
        return "TRANSPORT_FAIL"


def _write_github_output(report: dict) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        for key in ("status", "incident_key"):
            fh.write(f"{key}={report[key]}\n")
        fh.write(f"notify={'true' if report['notify'] else 'false'}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect", "send", "test"])
    parser.add_argument("--out", default="/tmp/radar-telegram-health.json")
    parser.add_argument("--url", default=RADAR_URL)
    parser.add_argument("--timeout", type=int, default=105)
    args = parser.parse_args()
    if args.action == "inspect":
        result = inspect_remote(url=args.url, timeout=min(max(1, args.timeout), 110),
                                now=datetime.now(timezone.utc))
        Path(args.out).write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
        _write_github_output(result)
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.action == "send":
        report = json.loads(Path(args.out).read_text(encoding="utf-8"))
        if report.get("notify") is not True:
            print("NO_ALERT_REQUIRED")
            return 0
        outcome = send_telegram(report)
    else:
        outcome = send_telegram({"utc_date": datetime.now(timezone.utc).date().isoformat()},
                                test=True)
    print("TELEGRAM_DELIVERY_" + outcome)
    if args.action == "send" and os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write("sent=" + ("true" if outcome == "SENT" else "false") + "\\n")
    return 0 if outcome in ("SENT", "NOT_CONFIGURED") else 2


if __name__ == "__main__":
    sys.exit(main())
