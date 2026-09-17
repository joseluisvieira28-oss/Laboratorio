#!/usr/bin/env python3
"""Frozen Discovery V0.1 for BINANCE-MARGIN-BORROW-ACCESS-001.

The source-manifest command is outcome-blind and requests Binance Vision
.CHECKSUM metadata only. Outcome ZIP values are opened only by the shard command
after the immutable manifest is frozen. No authenticated Binance API is used.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import glob
import hashlib
import io
import json
import math
import re
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

LAB_ID = "BINANCE-MARGIN-BORROW-ACCESS-001"
SHARD_COUNT = 8
START = datetime(2023, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)
START_MS = int(START.timestamp() * 1000)
END_MS = int(END.timestamp() * 1000)
DAY_MS = 86_400_000
H1_MS = 3_600_000
H4_MS = 14_400_000
H24_MS = DAY_MS
BASE = "https://data.binance.vision/data/spot/daily/klines"
CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Crypto-Lab-Discovery-source/1.0"})

SOURCE_SAFETY = {
    "market_data_zip_downloaded": False,
    "market_data_values_opened": False,
    "price_data_opened": False,
    "returns_opened": False,
    "authenticated_exchange_api_used": False,
    "borrow_rate_opened": False,
    "borrow_inventory_opened": False,
    "pnl_opened": False,
    "protected_2025_2026_path_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
}
OUTCOME_SAFETY = {
    **SOURCE_SAFETY,
    "market_data_zip_downloaded": True,
    "market_data_values_opened": True,
    "price_data_opened": True,
    "returns_opened": True,
}


class ProvenanceError(RuntimeError):
    pass


def stable_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def request(url: str, attempts: int = 5) -> requests.Response:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            r = SESSION.get(url, timeout=45, allow_redirects=True)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise RuntimeError(f"retryable HTTP {r.status_code}")
            return r
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(min(16.0, 1.25 * (2 ** attempt)))
    raise RuntimeError(str(last))


def checksum_probe(pair: str, date_str: str) -> dict[str, Any]:
    filename = f"{pair}-1m-{date_str}.zip"
    url = f"{BASE}/{pair}/1m/{filename}.CHECKSUM"
    r = request(url)
    raw = r.content
    if r.status_code == 404:
        return {
            "pair": pair, "date": date_str, "url": url, "http_status": 404,
            "valid": False, "archive_sha256": None,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
    r.raise_for_status()
    text = raw.decode("utf-8", "replace").strip()
    m = CHECKSUM_RE.match(text)
    valid = bool(m and m.group(2).strip() == filename)
    return {
        "pair": pair, "date": date_str, "url": url, "http_status": r.status_code,
        "valid": valid, "archive_sha256": m.group(1).lower() if m else None,
        "checksum_filename": m.group(2).strip() if m else None,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
    }


def dates_covering(start_ms: int, end_ms: int) -> list[str]:
    d0 = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).date()
    d1 = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).date()
    out = []
    d = d0
    while d <= d1:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def find_json(root: Path, suffix: str) -> Path:
    files = list(root.rglob(suffix))
    if len(files) != 1:
        raise ProvenanceError(f"expected one {suffix}, found {len(files)}")
    return files[0]


def cmd_manifest(prior_dir: Path, parser_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        prior_path = find_json(prior_dir, "BINANCE_MARGIN_BORROW_ACCESS_001_PRIOR_SPOT_RECEIPT_V0_1.json")
        parser_path = find_json(parser_dir, "BINANCE_MARGIN_BORROW_ACCESS_001_EVENT_PARSE_RECEIPT_V0_1_1.json")
        prior = json.loads(prior_path.read_text())
        parser = json.loads(parser_path.read_text())
        if prior.get("classification") != "PRIOR_SPOT_PRIMARY_PASS":
            raise ProvenanceError("upstream prior-Spot receipt is not PASS")
        if parser.get("classification") != "EVENT_PARSE_PASS":
            raise ProvenanceError("upstream parser receipt is not PASS")
        prior_rows = prior.get("results", [])
        if len(prior_rows) != 100:
            raise ProvenanceError(f"expected 100 prior-Spot rows, found {len(prior_rows)}")
        clean = [r for r in prior_rows if r.get("status") == "PRIOR_SPOT_ARCHIVE_PASS"]
        conf = [r for r in prior_rows if r.get("status") == "ACCESS_CONFOUND"]
        if len(clean) != 96 or len(conf) != 4:
            raise ProvenanceError(f"upstream clean/confound invariant failed {len(clean)}/{len(conf)}")

        add_records = [r for r in parser.get("records", []) if r.get("direction") == "ADD"]
        parser_map: dict[tuple[str, str], dict[str, Any]] = {}
        for r in add_records:
            for asset in r.get("cross_margin_borrowable_assets", []):
                parser_map[(r["code"], asset)] = r
        if len(parser_map) != 100:
            raise ProvenanceError(f"parser asset-event join map expected 100, found {len(parser_map)}")

        checksum_cache: dict[tuple[str, str], dict[str, Any]] = {}
        rows: list[dict[str, Any]] = []
        for src in sorted(clean, key=lambda x: x["candidate_id"]):
            code = src["article_code"]
            asset = src["asset"]
            p = parser_map.get((code, asset))
            if p is None:
                raise ProvenanceError(f"parser join missing {code}:{asset}")
            t0 = int(src["event_information_ms"])
            start_ms = t0 - H24_MS
            end_ms = t0 + H24_MS
            pair = f"{asset}USDT"
            row = {
                "candidate_id": src["candidate_id"],
                "article_code": code,
                "asset": asset,
                "asset_pair": pair,
                "benchmark_pair": "BTCUSDT",
                "event_information_ms": t0,
                "official_title": src.get("official_title"),
                "effective_ms": src.get("effective_ms"),
                "confounds": p.get("confounds", {}),
                "body_sha256": src.get("body_sha256"),
            }
            if start_ms < START_MS or end_ms > END_MS:
                row.update({"source_status": "BOUNDARY_EXCLUDED", "required_dates": [], "checksums": []})
                rows.append(row)
                continue
            required_dates = dates_covering(start_ms, end_ms)
            proofs = []
            ok = True
            for qpair in (pair, "BTCUSDT"):
                for date_str in required_dates:
                    key = (qpair, date_str)
                    if key not in checksum_cache:
                        if date_str.startswith("2025") or date_str.startswith("2026"):
                            raise ProvenanceError("protected-period checksum construction blocked")
                        checksum_cache[key] = checksum_probe(qpair, date_str)
                        time.sleep(0.04)
                    ck = checksum_cache[key]
                    proofs.append({
                        "pair": ck["pair"], "date": ck["date"], "http_status": ck["http_status"],
                        "valid": ck["valid"], "archive_sha256": ck.get("archive_sha256"),
                        "response_sha256": ck["response_sha256"],
                    })
                    if not ck["valid"]:
                        ok = False
            row.update({
                "source_status": "ANALYZABLE" if ok else "NO_USDT_OUTCOME_SOURCE",
                "required_dates": required_dates,
                "checksums": proofs,
            })
            rows.append(row)

        analyzable = [r for r in rows if r["source_status"] == "ANALYZABLE"]
        articles = {r["article_code"] for r in analyzable}
        counts = {
            "upstream_clean": 96,
            "analyzable": len(analyzable),
            "boundary_excluded": sum(r["source_status"] == "BOUNDARY_EXCLUDED" for r in rows),
            "no_usdt_outcome_source": sum(r["source_status"] == "NO_USDT_OUTCOME_SOURCE" for r in rows),
            "analyzable_articles": len(articles),
        }
        classification = "DISCOVERY_SOURCE_MANIFEST_PASS"
        if len(analyzable) < 50 or len(articles) < 25:
            classification = "DISCOVERY_DATA_INSUFFICIENT"
        core = {
            "lab_id": LAB_ID,
            "phase": "DISCOVERY_V0_1_SOURCE_MANIFEST",
            "protocol": "BINANCE_MARGIN_BORROW_ACCESS_001_DISCOVERY_PROTOCOL_V0_1",
            "rows": rows,
            "counts": counts,
            "source_window_start_ms": START_MS,
            "source_window_end_ms": END_MS,
            "bar_interval": "1m",
            "primary_horizon": "24h",
            "secondary_horizons": ["1h", "4h"],
            "benchmark": "BTCUSDT",
            "primary_pair_rule": "ASSETUSDT_ONLY_NO_FALLBACK",
        }
        digest = stable_sha(core)
        out = {**core, "classification": classification, "manifest_sha256": digest, "safety": SOURCE_SAFETY}
        (out_dir / "discovery_source_manifest.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"classification": classification, "counts": counts, "manifest_sha256": digest}))
        return 0 if classification == "DISCOVERY_SOURCE_MANIFEST_PASS" else 3
    except ProvenanceError as exc:
        classification = "DISCOVERY_DATA_PROVENANCE_FAILURE"
        failure = str(exc)
    except Exception as exc:
        classification = "DISCOVERY_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
    out = {"lab_id": LAB_ID, "phase": "DISCOVERY_V0_1_SOURCE_MANIFEST", "classification": classification, "failure": failure, "safety": SOURCE_SAFETY}
    (out_dir / "discovery_source_manifest_failure.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out))
    return 2


def archive_url(pair: str, date_str: str) -> str:
    return f"{BASE}/{pair}/1m/{pair}-1m-{date_str}.zip"


def download_verified_bars(pair: str, date_str: str, expected_sha: str) -> dict[int, float]:
    url = archive_url(pair, date_str)
    r = request(url)
    if r.status_code == 404:
        raise ProvenanceError(f"manifest-proven archive became 404: {pair} {date_str}")
    r.raise_for_status()
    raw = r.content
    got = hashlib.sha256(raw).hexdigest()
    if got.lower() != expected_sha.lower():
        raise ProvenanceError(f"archive checksum mismatch {pair} {date_str}")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if len(names) != 1:
                raise ProvenanceError(f"archive file-count invariant failed {pair} {date_str}")
            text = io.TextIOWrapper(zf.open(names[0]), encoding="utf-8", newline="")
            out: dict[int, float] = {}
            for row in csv.reader(text):
                if not row:
                    continue
                try:
                    ts = int(row[0])
                    op = float(row[1])
                except (ValueError, IndexError):
                    continue
                if ts < 10_000_000_000:
                    ts *= 1000
                if op <= 0 or not math.isfinite(op):
                    raise ProvenanceError(f"invalid open price {pair} {date_str} {ts}")
                out[ts] = op
            if not out:
                raise ProvenanceError(f"no kline rows parsed {pair} {date_str}")
            return out
    except zipfile.BadZipFile as exc:
        raise ProvenanceError(f"bad zip {pair} {date_str}: {exc}")


def checksum_map(row: dict[str, Any]) -> dict[tuple[str, str], str]:
    out = {}
    for c in row["checksums"]:
        if c.get("valid") and c.get("archive_sha256"):
            out[(c["pair"], c["date"])] = c["archive_sha256"]
    return out


def load_window(pair: str, dates: list[str], checksums: dict[tuple[str, str], str], cache: dict[tuple[str, str], dict[int, float]]) -> tuple[list[int], dict[int, float]]:
    merged: dict[int, float] = {}
    for d in dates:
        key = (pair, d)
        if key not in checksums:
            raise ProvenanceError(f"checksum absent from frozen manifest {pair} {d}")
        if key not in cache:
            cache[key] = download_verified_bars(pair, d, checksums[key])
        merged.update(cache[key])
    times = sorted(merged)
    return times, merged


def first_at_or_after(times: list[int], values: dict[int, float], target_ms: int) -> tuple[int, float]:
    i = bisect.bisect_left(times, target_ms)
    if i >= len(times):
        raise ProvenanceError(f"no bar at/after target {target_ms}")
    ts = times[i]
    return ts, values[ts]


def cmd_shard(manifest_path: Path, shard: int, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("classification") != "DISCOVERY_SOURCE_MANIFEST_PASS":
        raise SystemExit("source manifest is not PASS")
    digest = manifest["manifest_sha256"]
    analyzable = [r for r in manifest["rows"] if r["source_status"] == "ANALYZABLE"]
    assigned = [r for i, r in enumerate(analyzable) if i % SHARD_COUNT == shard]
    results = []
    cache: dict[tuple[str, str], dict[int, float]] = {}
    classification = "DISCOVERY_OUTCOME_SHARD_PASS"
    failure = None
    try:
        for row in assigned:
            if any(d.startswith("2025") or d.startswith("2026") for d in row["required_dates"]):
                raise ProvenanceError("protected-period market path blocked")
            cks = checksum_map(row)
            atimes, avals = load_window(row["asset_pair"], row["required_dates"], cks, cache)
            btimes, bvals = load_window("BTCUSDT", row["required_dates"], cks, cache)
            t0_raw = int(row["event_information_ms"])
            targets = {
                "pre24": t0_raw - H24_MS,
                "t0": t0_raw,
                "h1": t0_raw + H1_MS,
                "h4": t0_raw + H4_MS,
                "h24": t0_raw + H24_MS,
            }
            apoints = {k: first_at_or_after(atimes, avals, v) for k, v in targets.items()}
            bpoints = {}
            for k, (ats, _) in apoints.items():
                bts, bp = first_at_or_after(btimes, bvals, ats)
                if bts != ats:
                    raise ProvenanceError(f"BTC timestamp mismatch candidate={row['candidate_id']} point={k} asset={ats} btc={bts}")
                bpoints[k] = (bts, bp)
            p0a = apoints["t0"][1]
            p0b = bpoints["t0"][1]
            def mar(point: str) -> tuple[float, float, float]:
                ar = math.log(apoints[point][1] / p0a)
                br = math.log(bpoints[point][1] / p0b)
                return ar - br, ar, br
            mar1, ar1, br1 = mar("h1")
            mar4, ar4, br4 = mar("h4")
            mar24, ar24, br24 = mar("h24")
            pre_ar = math.log(p0a / apoints["pre24"][1])
            pre_br = math.log(p0b / bpoints["pre24"][1])
            result = {
                "candidate_id": row["candidate_id"], "article_code": row["article_code"],
                "asset": row["asset"], "asset_pair": row["asset_pair"],
                "event_information_ms": t0_raw, "confounds": row.get("confounds", {}),
                "bar_times": {k: apoints[k][0] for k in apoints},
                "mar_1h": mar1, "mar_4h": mar4, "mar_24h": mar24,
                "pre24_mar": pre_ar - pre_br,
                "asset_log_return_1h": ar1, "asset_log_return_4h": ar4, "asset_log_return_24h": ar24,
                "btc_log_return_1h": br1, "btc_log_return_4h": br4, "btc_log_return_24h": br24,
            }
            results.append(result)
    except ProvenanceError as exc:
        classification = "DISCOVERY_DATA_PROVENANCE_FAILURE"
        failure = str(exc)[:1200]
    except Exception as exc:
        classification = "DISCOVERY_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1200]}"
    out = {
        "lab_id": LAB_ID, "phase": "DISCOVERY_V0_1_OUTCOME_SHARD", "classification": classification,
        "manifest_sha256": digest, "shard": shard, "shard_count": SHARD_COUNT,
        "assigned_rows": len(assigned), "resolved_rows": len(results), "results": results,
        "failure": failure, "safety": OUTCOME_SAFETY,
    }
    (out_dir / f"discovery_outcome_shard_{shard}.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classification": classification, "shard": shard, "assigned": len(assigned), "resolved": len(results), "failure": failure}))
    return 0 if classification == "DISCOVERY_OUTCOME_SHARD_PASS" else 2


def article_means(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        groups[r["article_code"]].append(r)
    out = []
    for code, rows in sorted(groups.items()):
        out.append({
            "article_code": code,
            "asset_events": len(rows),
            "mar_1h": sum(r["mar_1h"] for r in rows) / len(rows),
            "mar_4h": sum(r["mar_4h"] for r in rows) / len(rows),
            "mar_24h": sum(r["mar_24h"] for r in rows) / len(rows),
            "pre24_mar": sum(r["pre24_mar"] for r in rows) / len(rows),
        })
    return out


def cmd_aggregate(manifest_path: Path, shards_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    digest = manifest["manifest_sha256"]
    expected = {r["candidate_id"] for r in manifest["rows"] if r["source_status"] == "ANALYZABLE"}
    results = []
    receipts = []
    try:
        files = sorted(glob.glob(str(shards_dir / "**/discovery_outcome_shard_*.json"), recursive=True))
        if len(files) != SHARD_COUNT:
            raise ProvenanceError(f"expected {SHARD_COUNT} outcome shards, got {len(files)}")
        for p in files:
            d = json.loads(Path(p).read_text())
            receipts.append({k: d.get(k) for k in ("shard", "classification", "assigned_rows", "resolved_rows", "failure")})
            if d.get("classification") != "DISCOVERY_OUTCOME_SHARD_PASS" or d.get("manifest_sha256") != digest:
                raise ProvenanceError("non-pass outcome shard or manifest mismatch")
            results.extend(d.get("results", []))
        ids = [r["candidate_id"] for r in results]
        if len(ids) != len(expected) or set(ids) != expected or len(ids) != len(set(ids)):
            raise ProvenanceError(f"outcome coverage mismatch expected={len(expected)} got={len(ids)} unique={len(set(ids))}")

        articles = article_means(results)
        if len(results) < 50 or len(articles) < 25:
            classification = "DISCOVERY_DATA_INSUFFICIENT"
            stats_out = {}
        else:
            import numpy as np
            from scipy import stats
            mar24 = np.array([x["mar_24h"] for x in articles], dtype=float)
            mar4 = np.array([x["mar_4h"] for x in articles], dtype=float)
            mar1 = np.array([x["mar_1h"] for x in articles], dtype=float)
            pre = np.array([x["pre24_mar"] for x in articles], dtype=float)
            primary = stats.ttest_1samp(mar24, 0.0, alternative="less")
            pretest = stats.ttest_1samp(pre, 0.0, alternative="less")
            neg = int(np.sum(mar24 < 0))
            sign = stats.binomtest(neg, len(mar24), p=0.5, alternative="greater")
            rng = np.random.default_rng(20260917)
            idx = rng.integers(0, len(mar24), size=(50_000, len(mar24)))
            boots = mar24[idx].mean(axis=1)
            ci_low, ci_high = np.quantile(boots, [0.025, 0.975])
            mean24 = float(np.mean(mar24))
            mean4 = float(np.mean(mar4))
            mean1 = float(np.mean(mar1))
            premean = float(np.mean(pre))
            p_primary = float(primary.pvalue)
            p_pre = float(pretest.pvalue)
            if mean24 < 0 and p_primary < 0.05 and mean4 <= 0:
                classification = "DISCOVERY_PRETREND_CONFOUNDED" if p_pre < 0.05 else "DISCOVERY_SIGNAL_PASS"
            else:
                classification = "DISCOVERY_NO_SIGNAL"
            stats_out = {
                "asset_events": len(results), "article_observations": len(articles),
                "mean_article_mar_24h": mean24, "primary_t_stat": float(primary.statistic),
                "primary_one_sided_p": p_primary,
                "bootstrap_95pct_ci_mean_mar_24h": [float(ci_low), float(ci_high)],
                "negative_article_count_24h": neg, "negative_article_fraction_24h": neg / len(mar24),
                "sign_test_one_sided_p": float(sign.pvalue),
                "mean_article_mar_4h": mean4, "mean_article_mar_1h": mean1,
                "mean_article_pre24_mar": premean, "pretrend_t_stat": float(pretest.statistic),
                "pretrend_one_sided_p": p_pre,
                "median_article_mar_24h": float(np.median(mar24)),
            }
        failure = None
    except ProvenanceError as exc:
        classification = "DISCOVERY_DATA_PROVENANCE_FAILURE"
        failure = str(exc)[:1200]
        stats_out = {}
        articles = []
    except Exception as exc:
        classification = "DISCOVERY_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1200]}"
        stats_out = {}
        articles = []
    out = {
        "lab_id": LAB_ID, "phase": "DISCOVERY_V0_1_CANONICAL", "classification": classification,
        "manifest_sha256": digest, "manifest_counts": manifest.get("counts", {}),
        "statistics": stats_out, "article_level_results": articles,
        "asset_event_results": sorted(results, key=lambda x: x.get("candidate_id", "")),
        "shards": sorted(receipts, key=lambda x: x.get("shard", -1)), "failure": failure,
        "execution_cost_provenance": "CREDENTIAL_BOUND",
        "executable_strategy_claim": False,
        "safety": OUTCOME_SAFETY,
    }
    (out_dir / "BINANCE_MARGIN_BORROW_ACCESS_001_DISCOVERY_RECEIPT_V0_1.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classification": classification, "statistics": stats_out, "failure": failure}))
    return 0 if classification in {"DISCOVERY_SIGNAL_PASS", "DISCOVERY_NO_SIGNAL", "DISCOVERY_PRETREND_CONFOUNDED", "DISCOVERY_DATA_INSUFFICIENT"} else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest")
    m.add_argument("--prior-spot-dir", type=Path, required=True)
    m.add_argument("--parser-dir", type=Path, required=True)
    m.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("shard")
    s.add_argument("--manifest", type=Path, required=True)
    s.add_argument("--shard", type=int, required=True)
    s.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("aggregate")
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--shards", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    x = ap.parse_args()
    if x.cmd == "manifest":
        return cmd_manifest(x.prior_spot_dir, x.parser_dir, x.out)
    if x.cmd == "shard":
        if not 0 <= x.shard < SHARD_COUNT:
            raise SystemExit("invalid shard")
        return cmd_shard(x.manifest, x.shard, x.out)
    return cmd_aggregate(x.manifest, x.shards, x.out)


if __name__ == "__main__":
    sys.exit(main())
