#!/usr/bin/env python3
import base64
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AUTH = Path("labs/BTC_OPTIONS_VRP_001/LAEVITAS_PAID_MICRO_PROBE_AUTHORITY_V0.1.json")
OUT = Path("artifacts/btc_options_vrp_laevitas_x402_challenge_v01")
OUT.mkdir(parents=True, exist_ok=True)


def decode_payment_required(value):
    if not value:
        return None
    candidates = [value]
    # v2 commonly uses base64/base64url JSON in PAYMENT-REQUIRED.
    for raw in list(candidates):
        try:
            padded = raw + "=" * (-len(raw) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            candidates.append(decoded)
        except Exception:
            pass
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {"unparsed": True, "sha256": hashlib.sha256(value.encode()).hexdigest()}


def sanitize_payment(obj):
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        lk = k.lower()
        if lk in {"signature", "payment-signature", "privatekey", "private_key", "seed", "mnemonic"}:
            continue
        if isinstance(v, dict):
            out[k] = sanitize_payment(v)
        elif isinstance(v, list):
            out[k] = [sanitize_payment(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


a = json.loads(AUTH.read_text(encoding="utf-8"))
assert a["payment_authorized"] is True
assert a["wallet_signature_authorized"] is True
assert a["outcomes_authorized"] is False
assert a["strategy_pnl_authorized"] is False
assert a["access_2025_authorized"] is False
assert a["access_2026_authorized"] is False
assert a["max_bundle_purchases"] == 1
assert a["provider_payment_cap_usdc"] == 0.10

params = urllib.parse.urlencode({
    "exchange": a["exchange"],
    "currency": a["currency"],
    "date": a["probe_timestamp"],
    "resolution": a["resolution"],
})
url = a["base_url"].rstrip("/") + a["endpoint"] + "?" + params
req = urllib.request.Request(url, headers={"User-Agent": "SRC-Crypto-Lab-x402-Challenge/0.1", "Accept": "application/json"})

status = None
headers = {}
body = b""
error = None
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        status = int(r.status)
        headers = {k.lower(): v for k, v in r.headers.items()}
        body = r.read(4096)
except urllib.error.HTTPError as e:
    status = int(e.code)
    headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
    body = e.read(4096)
    error = f"HTTPError:{e.code}"
except Exception as e:
    error = repr(e)

payment_header = headers.get("payment-required") or headers.get("x-payment-required")
decoded = sanitize_payment(decode_payment_required(payment_header))

result = {
    "lab_id": a["lab_id"],
    "source_mve_id": a["source_mve_id"],
    "request_url": url,
    "status": status,
    "error": error,
    "payment_required_header_present": bool(payment_header),
    "payment_required_header_sha256": hashlib.sha256(payment_header.encode()).hexdigest() if payment_header else None,
    "payment_required_decoded": decoded,
    "x402_related_headers": {k: v for k, v in headers.items() if k.startswith("x-402-") or k in {"content-type", "content-length"}},
    "body_prefix": body[:512].decode("utf-8", errors="replace"),
    "body_sha256": hashlib.sha256(body).hexdigest() if body else None,
    "payment_executed": False,
    "wallet_signature_executed": False,
    "outcomes_opened": False,
    "strategy_pnl_opened": False,
    "access_2025": False,
    "access_2026": False,
}

if status == 402 and payment_header:
    result["classification"] = "X402_CHALLENGE_CAPTURED_PAYMENT_NOT_EXECUTED"
elif status == 200:
    result["classification"] = "UNEXPECTED_FREE_ACCESS_REVIEW_REQUIRED"
else:
    result["classification"] = "X402_CHALLENGE_CAPTURE_TECHNICAL_FAILURE"

p = OUT / "x402_challenge_result.json"
p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps({
    "authority_sha256": hashlib.sha256(AUTH.read_bytes()).hexdigest(),
    "result_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
