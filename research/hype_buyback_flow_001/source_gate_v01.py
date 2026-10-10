#!/usr/bin/env python3
"""HYPE-BUYBACK-FLOW-001: bounded, PUBLIC Hyperliquid info SOURCE-ONLY gate.
No prices/returns are modelled; no exchange mutation, credentials or S3."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

URL = "https://api.hyperliquid.xyz/info"
AF = "0xfefefefefefefefefefefefefefefefefefefefe"
assert len(AF) == 42 and AF.startswith("0x") and all(c in "0123456789abcdef" for c in AF[2:]), "invalid_OFFICIAL_ASSISTANCE_FUND_ADDRESS"
MS_DAY = 86_400_000
OUT = Path("research/hype_buyback_flow_001/receipts/source_only_one_shot")
MAX_BYTES = 8_000_000


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(b):
    return hashlib.sha256(b).hexdigest()


def info(kind, payload, out):
    """Read official PUBLIC data only; persist the raw response for byte provenance."""
    assert kind in ("spotMeta", "af_recent", "af_historical_retention_probe")
    body = canonical(payload)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.monotonic()
    req = urllib.request.Request(
        URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "CryptoLab-HYPE-SourceGate/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(MAX_BYTES + 1)
            status = resp.status
        if len(raw) > MAX_BYTES:
            raise ValueError("response_exceeds_cap")
        parsed = json.loads(raw)
        out.mkdir(parents=True, exist_ok=True)
        (out / (kind + ".json")).write_bytes(raw)
        return parsed, dict(
            request_type=kind, endpoint=URL, request_body_sha256=digest(body),
            response_sha256=digest(raw), http_status=status,
            requested_at_utc=started, received_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            latency_ms=round((time.monotonic() - t0) * 1000, 2), bytes=len(raw)
        )
    except urllib.error.HTTPError as exc:
        body = exc.read(1200)
        # Public exchange diagnostics only; no credentials or private account payloads.
        out.mkdir(parents=True, exist_ok=True)
        (out / (kind + "_http_error.json")).write_bytes(canonical({
            "http_status": exc.code, "body_sha256": digest(body),
            "public_error_body_excerpt": body.decode("utf-8", errors="replace")[:600],
        }) + b"\n")
        raise RuntimeError(kind + ":HTTP_" + str(exc.code)) from exc
    except (urllib.error.URLError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(kind + ":" + type(exc).__name__) from exc


def hype_pair(meta):
    if not isinstance(meta, dict) or not isinstance(meta.get("tokens"), list) or not isinstance(meta.get("universe"), list):
        raise ValueError("spot_meta_structure_invalid")
    token_by_name = {t.get("name"): t.get("index") for t in meta["tokens"] if isinstance(t, dict)}
    if not isinstance(token_by_name.get("HYPE"), int) or not isinstance(token_by_name.get("USDC"), int):
        raise ValueError("HYPE_or_USDC_not_in_spotMeta")
    bindings = []
    for i, pair in enumerate(meta["universe"]):
        if not isinstance(pair, dict):
            continue
        if pair.get("tokens") == [token_by_name["HYPE"], token_by_name["USDC"]]:
            bindings.append({"coin": pair.get("name"), "universe_index": i, "tokens": pair.get("tokens")})
    if len(bindings) != 1 or not isinstance(bindings[0]["coin"], str):
        raise ValueError("HYPE_USDC_pair_not_unambiguous")
    return bindings[0]


def audit_fills(data, coin):
    if not isinstance(data, list):
        raise ValueError("userFillsByTime_response_not_list")
    ids, duplicates, invalid, buys, sells, nonhype, timemin, timemax = set(), 0, 0, 0, 0, 0, None, None
    for f in data:
        if not isinstance(f, dict):
            invalid += 1
            continue
        if f.get("coin") != coin:
            nonhype += 1
            continue
        side, timestamp, txid = f.get("side"), f.get("time"), f.get("tid")
        if side not in ("A", "B") or not isinstance(timestamp, int) or timestamp <= 0 or txid is None:
            invalid += 1
            continue
        try:
            valid_amount = float(f.get("sz", "0")) > 0 and float(f.get("px", "0")) > 0
        except (ValueError, TypeError, OverflowError):
            valid_amount = False
        if not valid_amount:
            invalid += 1
            continue
        identity = (str(txid), str(f.get("hash", "")))
        if identity in ids:
            duplicates += 1
            continue
        ids.add(identity)
        timemin = timestamp if timemin is None else min(timemin, timestamp)
        timemax = timestamp if timemax is None else max(timemax, timestamp)
        if side == "B":
            buys += 1
        else:
            sells += 1
    return {"rows": len(data), "verified_hype_buys": buys, "hype_sells": sells,
            "other_markets": nonhype, "malformed": invalid, "duplicate_tid_hash": duplicates,
            "min_fill_ms": timemin, "max_fill_ms": timemax,
            "at_api_page_limit_2000": len(data) >= 2000,
            "HISTORICAL_COMPLETENESS": "NOT_ESTABLISHED"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = {
        "candidate_id": "HYPE-BUYBACK-FLOW-001",
        "phase": "SOURCE_ONLY", "trading_authority": "NONE",
        "outcome_lookups": 0, "private_account_reads": 0,
        "aws_spend": 0, "exchange_mutations": 0,
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "LOCAL"),
        "commit_sha": os.environ.get("GITHUB_SHA", "UNSET"),
        "status": "SOURCE_BLOCKED", "raw_receipts": [], "fail_reasons": [],
    }
    now_ms = int(time.time() * 1000)
    try:
        meta, m = info("spotMeta", {"type": "spotMeta"}, OUT)
        receipt["raw_receipts"].append(m)
        pair = hype_pair(meta)
        receipt["official_market_binding"] = pair
        windows = {
            "af_recent": (now_ms - MS_DAY, now_ms),
            "af_historical_retention_probe": (now_ms - 90 * MS_DAY, now_ms - 89 * MS_DAY),
        }
        for name, (start, end) in windows.items():
            data, provenance = info(name, {
                "type": "userFillsByTime", "user": AF, "startTime": start,
                "endTime": end, "aggregateByTime": False,
            }, OUT)
            receipt["raw_receipts"].append(provenance)
            receipt[name] = {
                "requested_start_ms": start, "requested_end_ms": end,
                **audit_fills(data, pair["coin"]),
            }
        if receipt["af_recent"]["verified_hype_buys"] == 0:
            receipt["fail_reasons"].append("NO_VERIFIED_ASSISTANCE_FUND_BUY_FILL_IN_PUBLIC_ACCOUNT_RESPONSE")
        if receipt["af_historical_retention_probe"]["verified_hype_buys"] == 0:
            receipt["fail_reasons"].append("90_DAY_HISTORICAL_BUY_FILL_NOT_VERIFIED")
        if receipt["af_recent"]["at_api_page_limit_2000"]:
            receipt["fail_reasons"].append("RECENT_API_RESPONSE_TRUNCATION_RISK")
        if any(receipt[k]["malformed"] or receipt[k]["duplicate_tid_hash"] for k in windows):
            receipt["fail_reasons"].append("FILL_SCHEMA_OR_IDENTITY_INTEGRITY_FAILURE")
        receipt["fail_reasons"].append("90_DAY_CONTIGUOUS_COMPLETE_TIMESTAMPED_FILL_CORPUS_NOT_VERIFIED")
        receipt["fail_reasons"].append("PIT_PUBLICATION_LATENCY_AND_EXECUTABLE_DEPTH_HISTORY_NOT_VERIFIED")
    except Exception as exc:
        receipt["fail_reasons"].append("PUBLIC_SOURCE_PROBE_ERROR_" + type(exc).__name__)
        receipt["fail_stage"] = str(exc)[:120]
    receipt["checked_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    p = OUT / "SOURCE_GATE_RECEIPT_V0_1.json"
    p.write_bytes(canonical(receipt) + b"\n")
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0  # data-source failure is a scientific gate state, not a technical CI failure


if __name__ == "__main__":
    raise SystemExit(main())
