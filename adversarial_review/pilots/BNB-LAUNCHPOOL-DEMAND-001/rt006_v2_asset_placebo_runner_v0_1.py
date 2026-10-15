#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import math
import random
import statistics
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = "joseluisvieira28-oss/Laboratorio"
SOURCE_BRANCH = "bnb-launchpool-demand-v3-readjudication-2026-09-17"
BASE = (
    "Dream-Account-OS-v2.3-PARTIAL/research/"
    "bnb_launchpool_demand_001/"
)
SOURCE_FILES = {
    "discovery_2022_2024": BASE + "market_source_v01/BNB_LAUNCHPOOL_DEMAND_001_MARKET_SOURCE_AUDIT_V0.1.json",
    "oos_2025": BASE + "oos_2025/market_source_v01/BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_MARKET_SOURCE_V0.1.json",
    "presample_1_30": BASE + "final_presample/market_source_v01/BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_MARKET_SOURCE_V0.1.json",
}
TARGET = "BNBBTC"
CONTROLS = ("ETHBTC", "SOLBTC", "XRPBTC", "DOGEBTC")
INTERVAL = "15m"
COST_BPS = 20.0
MIN_CONTROL_COUNT = 3
MIN_BASKET_COVERAGE = 0.80
SEED = 20260927
REPS = 10_000
OUT = Path("adversarial_review/pilots/BNB-LAUNCHPOOL-DEMAND-001/rt006_v2_asset_placebo_result_v0_1.json")
CACHE = Path(".rt006_cache")

def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-Adversarial-RT006-V2"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))

def raw_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{SOURCE_BRANCH}/{path}"

def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def epoch_ms(value: str) -> int:
    return int(parse_iso(value).timestamp() * 1000)

def normalize_epoch(value: str) -> int:
    x = int(value)
    if x > 100_000_000_000_000:
        x //= 1000
    return x

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def pf(values: list[float]) -> float | None:
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return math.inf if pos > 0 else None
    return pos / neg

def summarize(values: list[float]) -> dict:
    return {
        "n": len(values),
        "mean_bps": statistics.mean(values) if values else None,
        "median_bps": statistics.median(values) if values else None,
        "pf": pf(values) if values else None,
        "positive_fraction": (sum(x > 0 for x in values) / len(values)) if values else None,
        "total_bps": sum(values) if values else None,
    }

def provider_month_url(pair: str, month: str) -> str:
    return f"https://data.binance.vision/data/spot/monthly/klines/{pair}/{INTERVAL}/{pair}-{INTERVAL}-{month}.zip"

def download_verified_month(pair: str, month: str, canonical_target_hash: str | None) -> tuple[dict[int, float] | None, dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"{pair}-{INTERVAL}-{month}"
    zip_path = CACHE / f"{key}.zip"
    checksum_path = CACHE / f"{key}.zip.CHECKSUM"
    url = provider_month_url(pair, month)
    receipt = {"pair": pair, "month": month, "url": url}

    try:
        if not zip_path.exists():
            zip_path.write_bytes(fetch_bytes(url))
        if not checksum_path.exists():
            checksum_path.write_bytes(fetch_bytes(url + ".CHECKSUM"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            receipt.update({"status": "NOT_AVAILABLE_404"})
            return None, receipt
        raise

    data = zip_path.read_bytes()
    got = sha256(data)
    parts = checksum_path.read_text(encoding="utf-8").strip().split()
    if not parts:
        raise RuntimeError(f"empty provider checksum: {pair} {month}")
    provider_hash = parts[0]
    if got != provider_hash:
        raise RuntimeError(f"provider checksum mismatch: {pair} {month}")
    if pair == TARGET and canonical_target_hash is not None and got != canonical_target_hash:
        raise RuntimeError(f"canonical BNBBTC hash mismatch: {month}")

    opens: dict[int, float] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip contents: {pair} {month}")
        with archive.open(names[0]) as handle:
            for raw in handle:
                row = raw.decode("utf-8").strip().split(",")
                if len(row) < 2:
                    continue
                timestamp = normalize_epoch(row[0])
                opens[timestamp] = float(row[1])

    receipt.update({
        "status": "PASS",
        "sha256": got,
        "provider_checksum": provider_hash,
        "canonical_target_hash_checked": canonical_target_hash is not None,
        "rows": len(opens),
    })
    return opens, receipt

def main() -> int:
    sources = {block: fetch_json(raw_url(path)) for block, path in SOURCE_FILES.items()}

    events = []
    canonical_hashes: dict[tuple[str, str], str] = {}
    for block, source in sources.items():
        for row in source.get("archive_manifest", []):
            month = row["month"]
            canonical_hashes[(block, month)] = row["sha256"]
        for index, event in enumerate(source["selected"]):
            entry = parse_iso(event["entry_time_utc"])
            exit_ = parse_iso(event["exit_time_utc"])
            if entry.year >= 2026 or exit_.year >= 2026:
                raise RuntimeError("PROTECTED_2026_EVENT_ENCOUNTERED")
            events.append({
                "block": block,
                "index": index,
                "signal_time_utc": event["signal_time_utc"],
                "entry_time_utc": event["entry_time_utc"],
                "exit_time_utc": event["exit_time_utc"],
                "entry_ms": epoch_ms(event["entry_time_utc"]),
                "exit_ms": epoch_ms(event["exit_time_utc"]),
                "entry_month": event["entry_time_utc"][:7],
                "exit_month": event["exit_time_utc"][:7],
            })

    if len(events) != 66:
        raise RuntimeError(f"expected 66 frozen selected events, got {len(events)}")

    needed = {}
    for event in events:
        block = event["block"]
        for pair in (TARGET,) + CONTROLS:
            for month in {event["entry_month"], event["exit_month"]}:
                needed[(block, pair, month)] = True

    market: dict[tuple[str, str, str], dict[int, float] | None] = {}
    source_receipts = []
    for block, pair, month in sorted(needed):
        canonical = canonical_hashes.get((block, month)) if pair == TARGET else None
        bars, receipt = download_verified_month(pair, month, canonical)
        market[(block, pair, month)] = bars
        receipt["block"] = block
        source_receipts.append(receipt)

    pair_values = {pair: [] for pair in (TARGET,) + CONTROLS}
    event_rows = []
    basket_diffs = []
    basket_count = 0

    for event in events:
        block = event["block"]
        pair_returns = {}
        for pair in (TARGET,) + CONTROLS:
            entry_map = market.get((block, pair, event["entry_month"]))
            exit_map = market.get((block, pair, event["exit_month"]))
            if entry_map is None or exit_map is None:
                pair_returns[pair] = None
                continue
            entry_open = entry_map.get(event["entry_ms"])
            exit_open = exit_map.get(event["exit_ms"])
            if entry_open is None or exit_open is None:
                pair_returns[pair] = None
                continue
            gross = (exit_open / entry_open - 1.0) * 10_000.0
            pair_returns[pair] = gross
            pair_values[pair].append(gross - COST_BPS)

        bnb = pair_returns[TARGET]
        controls = [pair_returns[pair] for pair in CONTROLS if pair_returns[pair] is not None]
        row = {
            "block": block,
            "signal_time_utc": event["signal_time_utc"],
            "entry_time_utc": event["entry_time_utc"],
            "target_gross_bps": bnb,
            "available_control_count": len(controls),
        }
        if bnb is not None and len(controls) >= MIN_CONTROL_COUNT:
            median_control = statistics.median(controls)
            diff = bnb - median_control
            row["median_control_gross_bps"] = median_control
            row["bnb_minus_median_control_bps"] = diff
            basket_diffs.append(diff)
            basket_count += 1
        event_rows.append(row)

    coverage = basket_count / len(events)
    result = {
        "protocol_id": "BNB-RT006-V2-CANONICAL-ALT-BTC-CONTROLS-V0.1",
        "status": "EXECUTED" if coverage >= MIN_BASKET_COVERAGE else "BLOCKED_COVERAGE_LT_0_80",
        "target": TARGET,
        "controls": list(CONTROLS),
        "event_count": len(events),
        "basket_event_count": basket_count,
        "basket_coverage": coverage,
        "per_pair_net20": {pair: summarize(values) for pair, values in pair_values.items()},
        "source_receipts": source_receipts,
        "guards": {
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
            "candidate_rule_changed": False,
            "promotion_credit": False,
        },
    }

    if coverage >= MIN_BASKET_COVERAGE:
        observed = statistics.mean(basket_diffs)
        rng = random.Random(SEED)
        perm_means = []
        for _ in range(REPS):
            perm = [value if rng.random() < 0.5 else -value for value in basket_diffs]
            perm_means.append(statistics.mean(perm))
        two_sided = sum(abs(x) >= abs(observed) for x in perm_means) / REPS
        result["bnb_minus_median_control"] = {
            **summarize(basket_diffs),
            "signflip_replications": REPS,
            "seed": SEED,
            "two_sided_fraction_abs_perm_mean_gte_observed": two_sided,
        }
        result["event_rows"] = event_rows

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "basket_coverage": result["basket_coverage"],
        "per_pair_net20": result["per_pair_net20"],
        "bnb_minus_median_control": result.get("bnb_minus_median_control"),
    }, indent=2))
    return 0 if coverage >= MIN_BASKET_COVERAGE else 2

if __name__ == "__main__":
    raise SystemExit(main())
