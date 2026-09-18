#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-RISK-PARAMETER-SHOCK-001"
PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
FROM_BLOCK = 16_490_000
TO_BLOCK = 21_525_890
MAX_TS = 1_735_689_599
WINDOW = 75_000
TRANSIENT = {429, 500, 502, 503, 504, 529}
SIG = "CollateralConfigurationChanged(address,uint256,uint256,uint256)"
TOPIC0 = "0x" + keccak(SIG.encode()).hex()

MIN_CLUSTERS = 12
MIN_ASSETS = 4
MIN_YEARS = 2

def as_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 16) if v.startswith("0x") else int(v)
    raise TypeError(f"cannot convert {type(v).__name__} to int")

def topic_addr(v: str) -> str:
    s = str(v).lower()
    if not s.startswith("0x") or len(s) != 66:
        raise ValueError("invalid indexed address topic")
    return "0x" + s[-40:]

def words(data: str, n: int) -> list[int]:
    s = str(data)
    if not s.startswith("0x"):
        raise ValueError("ABI data missing 0x")
    h = s[2:]
    if len(h) < 64 * n or len(h) % 64:
        raise ValueError("invalid ABI data length")
    return [int(h[i*64:(i+1)*64], 16) for i in range(n)]

def load_source_census() -> dict[str, Any]:
    xs = []
    for p in Path("downloaded_source_census").rglob("*.json"):
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("frontier_id") == LAB_ID:
            xs.append(obj)
    if len(xs) != 1:
        raise RuntimeError(f"expected exactly one source census receipt, found {len(xs)}")
    x = xs[0]
    if x.get("classification") != "SOURCE_CENSUS_PASS":
        raise RuntimeError(f"source census is not PASS: {x.get('classification')}")
    if int(x.get("from_block", -1)) != FROM_BLOCK or int(x.get("to_block", -1)) != TO_BLOCK:
        raise RuntimeError("source census envelope mismatch")
    safety = x.get("safety") or {}
    if safety.get("market_prices_opened") or safety.get("returns_opened") or safety.get("pnl_opened"):
        raise RuntimeError("source census safety violation")
    return x

def post(body: dict[str, Any], stats: Counter[str]) -> requests.Response:
    last = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL,
                json=body,
                timeout=(20, 180),
                stream=True,
                headers={
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip",
                    "User-Agent": f"{LAB_ID}/primary-mechanism-census-v0.1",
                },
            )
            stats["http_attempts"] += 1
            if r.status_code in TRANSIENT:
                last = RuntimeError(f"transient HTTP {r.status_code}")
                r.close()
                if attempt < 7:
                    stats["transient_retries"] += 1
                    time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                    continue
                raise last
            if r.status_code == 204:
                r.close()
                raise RuntimeError("unexpected Portal 204 inside frozen envelope")
            r.raise_for_status()
            stats["successful_http_responses"] += 1
            return r
        except (requests.RequestException, RuntimeError) as exc:
            last = exc
            if attempt < 7:
                stats["network_retries"] += 1
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
            raise
    raise RuntimeError(str(last))

def acquire(stats: Counter[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    cursor = FROM_BLOCK
    while cursor <= TO_BLOCK:
        request_to = min(TO_BLOCK, cursor + WINDOW - 1)
        body = {
            "type": "evm",
            "fromBlock": cursor,
            "toBlock": request_to,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": {
                    "address": True,
                    "topics": True,
                    "data": True,
                    "transactionHash": True,
                    "logIndex": True,
                },
            },
            "logs": [{"address": [CONFIGURATOR], "topic0": [TOPIC0]}],
        }
        r = post(body, stats)
        matched_this_window = 0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                header = obj.get("header") or obj.get("block") or {}
                bn = as_int(header.get("number"))
                ts = as_int(header.get("timestamp"))
                if not (cursor <= bn <= request_to):
                    raise RuntimeError("row outside exact request window")
                if ts > MAX_TS:
                    raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
                for log in obj.get("logs") or []:
                    address = str(log.get("address", "")).lower()
                    topics = [str(x).lower() for x in (log.get("topics") or [])]
                    txh = str(log.get("transactionHash", "")).lower()
                    li = as_int(log.get("logIndex"))
                    if address != CONFIGURATOR:
                        raise RuntimeError("unexpected contract address")
                    if len(topics) < 2 or topics[0] != TOPIC0:
                        raise RuntimeError("unexpected event identity")
                    if not txh:
                        raise RuntimeError("missing transactionHash")
                    key = (txh, li)
                    if key in seen:
                        raise RuntimeError("duplicate canonical log identity")
                    seen.add(key)
                    ltv, threshold, bonus = words(log.get("data", ""), 3)
                    rows.append({
                        "block": bn,
                        "timestamp": ts,
                        "transactionHash": txh,
                        "logIndex": li,
                        "asset": topic_addr(topics[1]),
                        "ltv": str(ltv),
                        "liquidationThreshold": str(threshold),
                        "liquidationBonus": str(bonus),
                    })
                    matched_this_window += 1
        finally:
            r.close()
        stats["windows_completed"] += 1
        stats["matching_logs"] += matched_this_window
        if matched_this_window == 0:
            stats["empty_matching_windows"] += 1
        stats["covered_through_block"] = request_to
        cursor = request_to + 1
    return rows

def main() -> int:
    outdir = Path("out/aave_risk_parameter_shock")
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / "AAVE_RISK_PARAMETER_SHOCK_001_PRIMARY_MECHANISM_CENSUS_V0_1.json"
    stats: Counter[str] = Counter()
    receipt: dict[str, Any] = {
        "frontier_id": LAB_ID,
        "phase": "PRIMARY_MECHANISM_CENSUS_OUTCOME_BLIND",
        "classification": None,
        "failure": None,
        "frozen_from_block": FROM_BLOCK,
        "frozen_to_block": TO_BLOCK,
        "hard_timestamp_ceiling": MAX_TS,
        "primary_mechanism": "liquidationThreshold decrease",
        "sample_gate": {
            "min_distinct_transaction_clusters": MIN_CLUSTERS,
            "min_unique_affected_assets": MIN_ASSETS,
            "min_calendar_years": MIN_YEARS,
        },
        "safety": {
            "borrower_state_opened": False,
            "health_factor_computed": False,
            "liquidation_overhang_computed": False,
            "future_liquidation_outcomes_opened": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    try:
        source = load_source_census()
        rows = acquire(stats)
        expected = int((source.get("event_counts") or {}).get("CollateralConfigurationChanged", -1))
        if expected < 0:
            raise RuntimeError("source census missing CollateralConfigurationChanged count")
        if len(rows) != expected:
            raise RuntimeError(f"decoded/source-census count mismatch: {len(rows)} != {expected}")

        by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_asset[row["asset"]].append(row)
        for xs in by_asset.values():
            xs.sort(key=lambda x: (int(x["block"]), int(x["logIndex"])))

        decreases: list[dict[str, Any]] = []
        history: list[dict[str, Any]] = []
        for asset, xs in sorted(by_asset.items()):
            prev = None
            for row in xs:
                entry = dict(row)
                if prev is None:
                    entry["prior_liquidationThreshold"] = None
                    entry["is_primary_decrease"] = False
                    entry["baseline_only"] = True
                else:
                    prev_thr = int(prev["liquidationThreshold"])
                    cur_thr = int(row["liquidationThreshold"])
                    entry["prior_liquidationThreshold"] = str(prev_thr)
                    entry["threshold_delta"] = str(cur_thr - prev_thr)
                    entry["is_primary_decrease"] = cur_thr < prev_thr
                    entry["baseline_only"] = False
                    if cur_thr < prev_thr:
                        cand = dict(entry)
                        cand["calendar_year"] = datetime.fromtimestamp(
                            int(row["timestamp"]), tz=timezone.utc
                        ).year
                        decreases.append(cand)
                history.append(entry)
                prev = row

        clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in decreases:
            clusters[row["transactionHash"]].append(row)
        cluster_rows = []
        for txh, xs in sorted(clusters.items(), key=lambda kv: min((x["block"], x["logIndex"]) for x in kv[1])):
            cluster_rows.append({
                "transactionHash": txh,
                "block": min(int(x["block"]) for x in xs),
                "timestamp": min(int(x["timestamp"]) for x in xs),
                "calendar_year": min(int(x["calendar_year"]) for x in xs),
                "affected_assets": sorted({x["asset"] for x in xs}),
                "decrease_log_count": len(xs),
            })

        affected_assets = sorted({x["asset"] for x in decreases})
        years = sorted({int(x["calendar_year"]) for x in decreases})
        gate = {
            "distinct_transaction_clusters": len(cluster_rows),
            "unique_affected_assets": len(affected_assets),
            "calendar_years": years,
            "cluster_gate_pass": len(cluster_rows) >= MIN_CLUSTERS,
            "asset_gate_pass": len(affected_assets) >= MIN_ASSETS,
            "year_gate_pass": len(years) >= MIN_YEARS,
        }
        classification = (
            "MECHANISM_CENSUS_PASS"
            if gate["cluster_gate_pass"] and gate["asset_gate_pass"] and gate["year_gate_pass"]
            else "INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE"
        )
        digest = hashlib.sha256(
            "\n".join(
                f"{x['block']}|{x['transactionHash']}|{x['logIndex']}|{x['asset']}|"
                f"{x.get('prior_liquidationThreshold')}|{x['liquidationThreshold']}|{x.get('threshold_delta')}"
                for x in history
            ).encode()
        ).hexdigest()

        receipt.update({
            "classification": classification,
            "source_census_event_count": expected,
            "decoded_event_count": len(rows),
            "asset_history_count": len(history),
            "primary_decrease_log_count": len(decreases),
            "primary_decrease_transaction_cluster_count": len(cluster_rows),
            "unique_affected_asset_count": len(affected_assets),
            "affected_assets": affected_assets,
            "calendar_years": years,
            "gate_results": gate,
            "configuration_history": history,
            "primary_decrease_rows": decreases,
            "primary_decrease_clusters": cluster_rows,
            "mechanism_history_sha256": digest,
        })
    except Exception as exc:
        receipt["classification"] = "MECHANISM_CENSUS_TECHNICAL_OR_PROVENANCE_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1500]}"
    receipt["transport_stats"] = dict(stats)
    outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "decoded_events": receipt.get("decoded_event_count"),
        "decrease_logs": receipt.get("primary_decrease_log_count"),
        "decrease_clusters": receipt.get("primary_decrease_transaction_cluster_count"),
        "affected_assets": receipt.get("unique_affected_asset_count"),
        "calendar_years": receipt.get("calendar_years"),
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] in {"MECHANISM_CENSUS_PASS", "INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE"} else 2

if __name__ == "__main__":
    raise SystemExit(main())
