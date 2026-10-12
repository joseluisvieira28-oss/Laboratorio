"""Bounded public-only transport diagnostic; never sends Telegram or accesses accounts."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

url = "https://crypto-edge-radar-v05-canary.onrender.com/api/state"
report = {"observed_utc": datetime.now(timezone.utc).isoformat(),
          "url": url, "orders": False, "account_reads": False, "notifications_sent": False}
try:
    req = Request(url, headers={"User-Agent": "CryptoLab-ReadOnly-Recovery/1.0"})
    try:
        response = urlopen(req, timeout=105)
    except HTTPError as error:
        response = error
    with response:
        body = response.read(2000001)
        report["http_status"] = response.code
        report["content_type"] = response.headers.get("Content-Type")
        report["body_bytes"] = len(body)
        report["body_sha256"] = hashlib.sha256(body).hexdigest()
    if len(body) > 2000000:
        report["state"] = "RESPONSE_SIZE_BLOCKED"
    else:
        try:
            state = json.loads(body)
            report["valid_json"] = isinstance(state, dict)
            if isinstance(state, dict):
                report["runtime_health"] = state.get("health")
                report["runtime_mode"] = state.get("mode")
                report["runtime_checked_at_utc"] = state.get("checked_at_utc")
            report["state"] = "PUBLIC_TRANSPORT_JSON_RECEIVED" if isinstance(state, dict) else "NON_OBJECT_JSON"
        except (ValueError, UnicodeDecodeError):
            report["valid_json"] = False
            report["state"] = "PUBLIC_TRANSPORT_NON_JSON"
except Exception as exc:
    report["state"] = "PUBLIC_TRANSPORT_BLOCKED"
    report["error_type"] = type(exc).__name__
Path("evidence").mkdir(exist_ok=True)
Path("evidence/radar_public_transport.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, sort_keys=True))
