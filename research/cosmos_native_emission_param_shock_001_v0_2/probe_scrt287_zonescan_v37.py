#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
import urllib.error
import urllib.request

TARGET = "2023-12-07T02:54:58.930543213Z"
TARGET_TS = datetime.datetime.fromisoformat(TARGET.replace("Z", "+00:00")).timestamp()
BASE = "https://zonescan.io/api/v1"
CHAIN = "secret"
OUT = "research/cosmos_native_emission_param_shock_001_v0_2/SCRT287_ZONESCAN_EXACT_BLOCK_API_V37.json"
UA = {"User-Agent": "CryptoLab-source-only-zonescan-v37/1.0", "Accept": "application/json,text/plain,*/*"}

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return {
                "ok": True, "status": getattr(r, "status", 200), "url": url,
                "content_type": r.headers.get("content-type", ""),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "body": raw.decode("utf-8", "replace"),
            }
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
        except Exception:
            raw = b""
        return {
            "ok": False, "status": e.code, "url": url, "error": str(e),
            "content_type": e.headers.get("content-type", "") if e.headers else "",
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "body": raw.decode("utf-8", "replace"),
        }
    except Exception as e:
        return {"ok": False, "url": url, "error": repr(e), "body": ""}

def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

def parse_ts(value):
    if value is None:
        return None
    s = str(value).strip()
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        pass
    try:
        v = float(s)
        if v > 1e14:
            v /= 1e6
        elif v > 1e11:
            v /= 1e3
        return v
    except Exception:
        return None

def parse_block(resp, requested_height):
    try:
        payload = json.loads(resp.get("body", ""))
    except Exception:
        return None
    for obj in walk(payload):
        if not isinstance(obj, dict):
            continue
        h = next((obj.get(k) for k in ("height", "block_height", "blockHeight") if obj.get(k) is not None), None)
        t = next((obj.get(k) for k in ("time", "timestamp", "block_time", "blockTime", "created_at", "createdAt") if obj.get(k) is not None), None)
        if h is None or t is None:
            continue
        try:
            hi = int(str(h).replace(",", ""))
        except Exception:
            continue
        if hi != requested_height or parse_ts(t) is None:
            continue
        hs = next((obj.get(k) for k in ("hash", "block_hash", "blockHash") if obj.get(k) is not None), None)
        return {"height": hi, "time": str(t), "hash": hs}
    return None

def block(height):
    url = f"{BASE}/blocks/{CHAIN}/{height}"
    r = get(url)
    return r, parse_block(r, height)

broad = [11752974,11800000,11840000,11860000,11870000,11875000,11880000,11885000,11890000,11900000,11920000]
grid = []
for h in broad:
    r, z = block(h)
    grid.append({
        "requested_height": h, "url": r.get("url"), "ok": r.get("ok"),
        "status": r.get("status"), "content_type": r.get("content_type"),
        "parsed": z, "sha256": r.get("sha256"), "error": r.get("error"),
        "body_excerpt": r.get("body", "")[:3000],
    })

points = sorted((row["parsed"]["height"], parse_ts(row["parsed"]["time"]), row["parsed"]["time"]) for row in grid if row.get("parsed"))
bracket = None
for a, b in zip(points, points[1:]):
    if a[1] < TARGET_TS <= b[1]:
        bracket = (a, b)
        break

exact = {"bracket": bracket}
if bracket:
    L, R = bracket[0][0], bracket[1][0]
    binary_receipts = []
    err = None
    while L < R:
        M = (L + R) // 2
        rr, zz = block(M)
        binary_receipts.append({
            "height": M, "url": rr.get("url"), "status": rr.get("status"),
            "sha256": rr.get("sha256"), "parsed": zz, "error": rr.get("error"),
            "body_excerpt": rr.get("body", "")[:1200],
        })
        if not zz:
            err = {"height": M, "reason": "NO_MATCHING_BLOCK_METADATA", "status": rr.get("status"), "error": rr.get("error")}
            break
        if parse_ts(zz["time"]) < TARGET_TS:
            L = M + 1
        else:
            R = M
    exact["binary_receipts"] = binary_receipts
    exact["error"] = err
    if err is None:
        H = L
        neighbors = []
        for hh in (H - 1, H, H + 1):
            rr, zz = block(hh)
            neighbors.append({
                "height": hh, "url": rr.get("url"), "ok": rr.get("ok"),
                "status": rr.get("status"), "sha256": rr.get("sha256"),
                "content_type": rr.get("content_type"), "parsed": zz,
                "error": rr.get("error"), "body": rr.get("body", "")[:12000],
            })
        exact["H_vote_end_block"] = H
        exact["neighbors"] = neighbors

certified = None
H = exact.get("H_vote_end_block")
ns = exact.get("neighbors") or []
if H is not None and len(ns) == 3 and all(x.get("parsed") for x in ns):
    tprev = parse_ts(ns[0]["parsed"]["time"])
    th = parse_ts(ns[1]["parsed"]["time"])
    tnext = parse_ts(ns[2]["parsed"]["time"])
    if tprev < TARGET_TS <= th < tnext:
        certified = {
            "source": "Zonescan public API",
            "api_template": f"{BASE}/blocks/{CHAIN}/{{height}}",
            "H_minus_1": ns[0]["parsed"], "H": ns[1]["parsed"], "H_plus_1": ns[2]["parsed"],
            "canonical_governance_execution_height": H,
            "canonical_first_reduced_mint_height": H + 1,
            "canonical_T0_time": ns[2]["parsed"]["time"],
            "boundary_check": "time(H-1) < voting_end <= time(H) < time(H+1)",
        }

event_receipts = []
if certified:
    for hh in (H, H + 1):
        u = f"{BASE}/block-events/{CHAIN}/{hh}"
        rr = get(u)
        event_receipts.append({
            "height": hh, "url": u, "ok": rr.get("ok"), "status": rr.get("status"),
            "sha256": rr.get("sha256"), "error": rr.get("error"),
            "body_excerpt": rr.get("body", "")[:20000],
        })

verdict = "H_BOUNDARY_RECOVERED" if certified else "H_BOUNDARY_NOT_RECOVERED"
result = {
    "scope": "SOURCE_ONLY_NO_MARKET_DATA",
    "scientific_rules_changed": False,
    "target_voting_end": TARGET,
    "api_template": f"{BASE}/blocks/{CHAIN}/{{height}}",
    "grid": grid, "points": points, "exact": exact,
    "certified_candidate": certified, "event_receipts": event_receipts,
    "verdict": verdict,
    "tested_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps({"verdict": verdict, "points": points, "bracket": bracket, "certified_candidate": certified}, indent=2))
