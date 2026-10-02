#!/usr/bin/env python3
"""
MEXC Event Futures V0.6 — public exact-product source discovery.

SOURCE-ONLY. GET requests only. No auth, cookies, account endpoints, orders, or trading.
"""
import hashlib
import json
import os
import re
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import requests

ENTRY_URLS = [
    "https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT",
    "https://www.mexc.com/en-US/futures/prediction-futures/BTC_USDT",
]
MAX_ASSETS = 80
MAX_BYTES = 8 * 1024 * 1024
MAX_PROBES = 60
ALLOWED_ASSET_HOST_SUFFIXES = (
    "mexc.com",
    "mocortech.com",
)
KEYWORDS = [
    "event-futures",
    "prediction-futures",
    "eventfuture",
    "event_future",
    "predictionfuture",
    "prediction_future",
    "payout",
    "uppayout",
    "downpayout",
    "timeunit",
    "settlement",
    "8938",
    "predict",
]
FORBIDDEN_PROBE_TOKENS = [
    "order", "position", "account", "balance", "asset", "wallet",
    "user", "trade", "deal", "openapi", "private", "auth", "login",
    "withdraw", "deposit", "bonus",
]
SAFE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CryptoLab-SourceResearch/0.6; +public-source-only)",
    "Accept": "text/html,application/javascript,application/json,text/plain,*/*",
    "Accept-Language": "en-GB,en;q=0.9",
}

session = requests.Session()
session.headers.update(SAFE_HEADERS)
# Intentionally no authentication headers and no imported browser cookies.
session.cookies.clear()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def fetch(url, timeout=25):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
        body = bytearray()
        for chunk in r.iter_content(65536):
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > MAX_BYTES:
                return {
                    "ok": False, "url": url, "final_url": r.url,
                    "status_code": r.status_code, "too_large": True,
                    "content_type": r.headers.get("content-type"),
                    "bytes": len(body),
                }
        data = bytes(body)
        return {
            "ok": 200 <= r.status_code < 400,
            "url": url,
            "final_url": r.url,
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type"),
            "etag": r.headers.get("etag"),
            "last_modified": r.headers.get("last-modified"),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "body": data,
        }
    except Exception as e:
        return {"ok": False, "url": url, "error": repr(e)}

def decode_body(rec):
    body = rec.get("body")
    if not isinstance(body, (bytes, bytearray)):
        return ""
    return bytes(body).decode("utf-8", errors="replace")

def allowed_asset_url(url):
    try:
        host = (urlparse(url).hostname or "").lower()
        return any(host == s or host.endswith("." + s) for s in ALLOWED_ASSET_HOST_SUFFIXES)
    except Exception:
        return False

def extract_asset_urls(base_url, html):
    urls = set()
    patterns = [
        r'<script[^>]+src=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\']',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html, re.I):
            raw = unescape(m.group(1)).strip()
            if not raw or raw.startswith("data:"):
                continue
            u = urljoin(base_url, raw)
            if allowed_asset_url(u):
                path = urlparse(u).path.lower()
                if path.endswith((".js", ".mjs", ".css")) or "/_next/" in path or "/assets/" in path:
                    urls.add(u)
    return sorted(urls)

def keyword_snippets(text, source_url, source_sha, max_per_keyword=12):
    low = text.lower()
    out = []
    for kw in KEYWORDS:
        start = 0
        count = 0
        while count < max_per_keyword:
            i = low.find(kw, start)
            if i < 0:
                break
            a = max(0, i - 220)
            b = min(len(text), i + len(kw) + 320)
            snippet = text[a:b].replace("\n", " ").replace("\r", " ")
            out.append({
                "keyword": kw,
                "source_url": source_url,
                "source_sha256": source_sha,
                "offset": i,
                "snippet": snippet,
            })
            count += 1
            start = i + len(kw)
    return out

def extract_candidates(text):
    cands = set()

    # Absolute URLs.
    for m in re.finditer(r'https://[A-Za-z0-9._~:/?#\[\]@!$&()*+,;=%-]{8,300}', text):
        s = m.group(0).rstrip("\"')]}>,;")
        if any(k in s.lower() for k in ("event", "predict", "payout")):
            cands.add(s)

    # Quoted route-like strings containing product keywords.
    quoted = re.compile(r'["\']([^"\']{1,260})["\']')
    for m in quoted.finditer(text):
        s = m.group(1)
        sl = s.lower()
        if not any(k in sl for k in ("event", "predict", "payout", "timeunit")):
            continue
        if s.startswith("/") or "/api/" in sl or "wss://" in sl or "https://" in sl:
            cands.add(s)

    # Nearby /api route fragments around keywords.
    low = text.lower()
    for kw in KEYWORDS:
        pos = 0
        while True:
            i = low.find(kw, pos)
            if i < 0:
                break
            window = text[max(0, i-500):min(len(text), i+700)]
            for m in re.finditer(r'/[A-Za-z0-9._~{}$:/?&=+%-]{3,220}', window):
                s = m.group(0).rstrip("\"')]}>,;")
                if ("/api/" in s.lower() or "event" in s.lower() or "predict" in s.lower()):
                    cands.add(s)
            pos = i + len(kw)
    return sorted(cands)

def is_safe_probe_candidate(candidate):
    s = candidate.strip()
    sl = s.lower()
    if not any(k in sl for k in ("event", "predict", "payout")):
        return False
    if any(tok in sl for tok in FORBIDDEN_PROBE_TOKENS):
        return False
    if any(x in s for x in ("{", "}", "<", ">", "*", "$")):
        return False
    if s.startswith("wss://") or s.startswith("ws://"):
        return False
    if len(s) > 260:
        return False
    return True

def expand_probe_urls(candidate):
    c = candidate.strip()
    out = []
    if c.startswith("https://"):
        if allowed_asset_url(c):
            out.append(c)
    elif c.startswith("/"):
        for base in ("https://www.mexc.com", "https://api.mexc.com", "https://contract.mexc.com"):
            out.append(base + c)
    return out

def probe_url(url):
    # GET only, no query invention, no auth, no cookies.
    try:
        session.cookies.clear()
        r = session.get(url, timeout=15, allow_redirects=True)
        body = r.content[:4000]
        preview = body.decode("utf-8", errors="replace")
        return {
            "url": url,
            "final_url": r.url,
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type"),
            "bytes_sampled": len(body),
            "sha256_sample": sha256_bytes(body),
            "preview": preview[:1200],
            "mentions_payout": "payout" in preview.lower(),
            "mentions_timeunit": "timeunit" in preview.lower(),
            "mentions_event_or_prediction": any(x in preview.lower() for x in ("event", "prediction")),
        }
    except Exception as e:
        return {"url": url, "error": repr(e)}

def strip_body(rec):
    return {k:v for k,v in rec.items() if k != "body"}

def main():
    os.makedirs("artifacts/mexc_event_futures", exist_ok=True)
    evidence = {
        "lab": "MEXC_EVENT_FUTURES_EXACT_SOURCE_V0.6",
        "mode": "SOURCE_ONLY_PUBLIC_GET",
        "authenticated_requests": 0,
        "orders": 0,
        "account_mutations": 0,
        "pages": [],
        "assets": [],
        "matches": [],
        "candidate_strings": [],
        "public_get_probes": [],
    }

    asset_urls = []
    candidate_strings = set()

    for page_url in ENTRY_URLS:
        rec = fetch(page_url)
        text = decode_body(rec)
        evidence["pages"].append(strip_body(rec))
        if text:
            page_assets = extract_asset_urls(rec.get("final_url") or page_url, text)
            asset_urls.extend(page_assets)
            evidence["matches"].extend(keyword_snippets(text, page_url, rec.get("sha256")))
            candidate_strings.update(extract_candidates(text))
        time.sleep(0.25)

    # Deduplicate while preserving order.
    seen = set()
    ordered_assets = []
    for u in asset_urls:
        if u not in seen:
            seen.add(u)
            ordered_assets.append(u)

    for url in ordered_assets[:MAX_ASSETS]:
        rec = fetch(url)
        evidence["assets"].append(strip_body(rec))
        text = decode_body(rec)
        if text:
            hits = keyword_snippets(text, url, rec.get("sha256"))
            if hits:
                evidence["matches"].extend(hits)
                candidate_strings.update(extract_candidates(text))
        time.sleep(0.12)

    evidence["candidate_strings"] = sorted(candidate_strings)

    probe_urls = []
    seen = set()
    for c in evidence["candidate_strings"]:
        if not is_safe_probe_candidate(c):
            continue
        for u in expand_probe_urls(c):
            if u not in seen and allowed_asset_url(u):
                seen.add(u)
                probe_urls.append(u)

    for u in probe_urls[:MAX_PROBES]:
        evidence["public_get_probes"].append(probe_url(u))
        time.sleep(0.18)

    exact_hits = []
    candidate_hits = []
    for p in evidence["public_get_probes"]:
        if p.get("status_code") != 200:
            continue
        if p.get("mentions_payout") or p.get("mentions_timeunit"):
            exact_hits.append(p["url"])
        elif p.get("mentions_event_or_prediction"):
            candidate_hits.append(p["url"])

    if exact_hits:
        verdict = "EXACT_PUBLIC_ROUTE_FOUND"
    elif candidate_strings or candidate_hits:
        verdict = "CANDIDATE_ROUTE_FOUND_UNPROVEN"
    elif any(not p.get("ok") for p in evidence["pages"]):
        verdict = "BLOCKED_BY_BOT_OR_ASSET_ACCESS"
    else:
        verdict = "PUBLIC_WEB_ROUTE_NOT_IDENTIFIED"

    evidence["verdict"] = verdict
    evidence["exact_public_route_hits"] = sorted(set(exact_hits))
    evidence["candidate_public_route_hits"] = sorted(set(candidate_hits))
    evidence["limits"] = {
        "max_assets": MAX_ASSETS,
        "max_bytes_per_asset": MAX_BYTES,
        "max_public_get_probes": MAX_PROBES,
    }

    path = "artifacts/mexc_event_futures/exact_source_discovery_v06.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)

    compact = {
        "verdict": verdict,
        "page_count": len(evidence["pages"]),
        "asset_count": len(evidence["assets"]),
        "match_count": len(evidence["matches"]),
        "candidate_string_count": len(evidence["candidate_strings"]),
        "probe_count": len(evidence["public_get_probes"]),
        "exact_public_route_hits": evidence["exact_public_route_hits"],
        "candidate_public_route_hits": evidence["candidate_public_route_hits"],
        "authenticated_requests": 0,
        "orders": 0,
        "account_mutations": 0,
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    print("WROTE", path)

if __name__ == "__main__":
    main()
