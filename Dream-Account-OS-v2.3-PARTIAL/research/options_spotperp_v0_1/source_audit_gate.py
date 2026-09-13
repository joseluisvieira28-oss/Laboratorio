#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — FINAL SOURCE/DATA GATE WRAPPER.

Outcome-blind wrapper around source_audit.py. It adds the frozen authority checks
that the first implementation omitted: machine-protocol binding, raw-page hash
verification, per-page monotonic/request-bound checks, required trade-field
presence, exact trade-id deduplication, and the exact 2021-04-01..2024-12-31
BTCUSDT Spot 1d price-file cutoff. It computes NO skew, signal, return, or PnL.
"""

from __future__ import annotations
import argparse, csv, datetime as dt, gzip, hashlib, io, json, math, sqlite3
import subprocess, sys, time, urllib.error, urllib.request, zipfile
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
LAB_ID = "OPTIONS-SPOTPERP-001"
VERSION = "V0.1"
AUTHORITY_DRIVE_ID = "1RtBYsET0t8yFAVDCJV1mEmGCAikMp-UQS0Yd802blBc"
AUTHORITY_SHA256 = "138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa"
START = dt.datetime(2021, 4, 1, tzinfo=UTC)
END = dt.datetime(2025, 1, 1, tzinfo=UTC)
START_MS = int(START.timestamp() * 1000)
END_MS = int(END.timestamp() * 1000)
BINANCE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
MAX_RETRIES = 4
UA = f"{LAB_ID}/{VERSION} final-source-gate"


class EnvBlocked(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last: Exception | None = None
    env = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                if getattr(r, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {getattr(r, 'status', '?')}")
                b = r.read()
            if not b:
                raise RuntimeError("empty response")
            return b
        except urllib.error.HTTPError as e:
            last, env = e, False
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last, env = e, True
        except RuntimeError as e:
            last, env = e, False
        if attempt < MAX_RETRIES:
            delay = 1.5 * attempt
            if isinstance(last, urllib.error.HTTPError) and last.code == 429:
                try:
                    delay = max(delay, float(last.headers.get("Retry-After", "0")))
                except Exception:
                    pass
            time.sleep(delay)
    if env:
        raise EnvBlocked(f"network/transport failed after {MAX_RETRIES} attempts: {last}")
    raise RuntimeError(f"source request failed after {MAX_RETRIES} attempts: {last}")


def protocol_binding(protocol_path: Path) -> dict[str, Any]:
    raw = protocol_path.read_bytes()
    p = json.loads(raw.decode("utf-8"))
    expected = {
        "active_frontier_family": "ONCHAIN-CAPFLOW-001",
        "authority_drive_id": AUTHORITY_DRIVE_ID,
        "authority_sha256": AUTHORITY_SHA256,
        "lab_id": LAB_ID,
        "source_audit_only": True,
        "status": "FROZEN_QUEUED_NOT_AUTHORIZED_FOR_DISCOVERY",
        "holdout_2025": "LOCKED",
        "year_2026": "LOCKED",
    }
    bad = [f"{k}={p.get(k)!r}" for k, v in expected.items() if p.get(k) != v]
    source = p.get("primary_source", {})
    expected_source = {
        "provider": "Deribit",
        "host": "history.deribit.com",
        "endpoint": "/api/v2/public/get_last_trades_by_currency_and_time",
        "currency": "BTC",
        "kind": "option",
    }
    bad += [
        f"primary_source.{k}={source.get(k)!r}"
        for k, v in expected_source.items() if source.get(k) != v
    ]
    if p.get("discovery_window") != {"start": "2021-04-01", "end": "2024-12-31"}:
        bad.append(f"discovery_window={p.get('discovery_window')!r}")
    s = p.get("signal", {})
    expected_signal = {
        "dte_days": [30, 120],
        "call_strike_over_index": [1.05, 1.2],
        "put_strike_over_index": [0.8, 0.95],
        "instrument_daily_aggregation": "median_transaction_iv",
        "side_daily_aggregation": "median_instrument_daily_iv",
        "min_distinct_instruments_per_side": 5,
        "formula": "CALL_IV_t - PUT_IV_t",
    }
    bad += [f"signal.{k}={s.get(k)!r}" for k, v in expected_signal.items() if s.get(k) != v]
    if bad:
        raise RuntimeError("FAIL-CLOSED protocol binding mismatch: " + "; ".join(bad))
    return {
        "authority_drive_id": AUTHORITY_DRIVE_ID,
        "authority_sha256": AUTHORITY_SHA256,
        "machine_protocol_sha256": sha256_bytes(raw),
        "pass": True,
    }


def parse_name(name: str) -> tuple[dt.date, float, str]:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").date()
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry, strike, parts[3]


def audit_deribit_raw(root: Path, probe: bool) -> dict[str, Any]:
    manifest_path = root / "source_manifest.json"
    report_path = root / "source_audit_report.json"
    if not manifest_path.exists() or not report_path.exists():
        raise RuntimeError("missing source_audit.py receipts")
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    r = json.loads(report_path.read_text(encoding="utf-8"))
    if m.get("holdout_accessed") is not False or m.get("locked_2026_accessed") is not False:
        raise RuntimeError("FAIL-CLOSED holdout/2026 flag")
    if r.get("outcome_metrics_computed") is not False:
        raise RuntimeError("FAIL-CLOSED source audit claims outcome metrics were computed")
    a = r.get("audit", {})
    if any(a.get(k) is not False for k in ("skew_values_computed", "forward_returns_computed", "pnl_computed")):
        raise RuntimeError("FAIL-CLOSED source audit outcome flag")

    db = root / "gate_trade_ids.sqlite"
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ids(id TEXT PRIMARY KEY) WITHOUT ROWID")
    counts = {
        "pages": 0, "trades": 0, "missing_trade_id": 0, "duplicate_trade_id": 0,
        "page_nonmonotonic": 0, "page_out_of_bounds": 0, "timestamp_invalid": 0,
        "instrument_parse_failure": 0, "iv_invalid": 0, "index_price_invalid": 0,
        "mark_price_invalid": 0, "direction_invalid": 0, "amount_invalid_when_present": 0,
    }
    try:
        for e in m.get("raw_pages", []):
            p = root / "raw" / e["page"]
            if not p.exists():
                raise RuntimeError(f"missing raw Deribit page: {p}")
            if sha256_file(p) != e.get("sha256"):
                raise RuntimeError(f"raw Deribit page hash mismatch: {p.name}")
            body = gzip.decompress(p.read_bytes())
            obj = json.loads(body.decode("utf-8"))
            trades = obj.get("result", {}).get("trades")
            if not isinstance(trades, list):
                raise RuntimeError(f"invalid trades payload: {p.name}")
            counts["pages"] += 1
            ts_page: list[int] = []
            lo, hi = int(e["start_ms"]), int(e["end_ms"])
            for row in trades:
                if not isinstance(row, dict):
                    raise RuntimeError(f"non-object trade row: {p.name}")
                counts["trades"] += 1
                try:
                    ts = int(row["timestamp"])
                except Exception:
                    counts["timestamp_invalid"] += 1
                    continue
                ts_page.append(ts)
                if ts < lo or ts > hi or ts < START_MS or ts >= END_MS:
                    counts["page_out_of_bounds"] += 1

                tid = row.get("trade_id")
                if tid in (None, ""):
                    counts["missing_trade_id"] += 1
                else:
                    before = conn.total_changes
                    conn.execute("INSERT OR IGNORE INTO ids(id) VALUES (?)", (str(tid),))
                    if conn.total_changes == before:
                        counts["duplicate_trade_id"] += 1

                try:
                    parse_name(str(row.get("instrument_name", "")))
                except Exception:
                    counts["instrument_parse_failure"] += 1

                for field, key in (("iv", "iv_invalid"), ("index_price", "index_price_invalid"),
                                   ("mark_price", "mark_price_invalid")):
                    try:
                        v = float(row[field])
                        if not math.isfinite(v) or v <= 0:
                            raise ValueError
                    except Exception:
                        counts[key] += 1
                if str(row.get("direction", "")).lower() not in {"buy", "sell"}:
                    counts["direction_invalid"] += 1
                if row.get("amount") not in (None, ""):
                    try:
                        av = float(row["amount"])
                        if not math.isfinite(av) or av <= 0:
                            raise ValueError
                    except Exception:
                        counts["amount_invalid_when_present"] += 1

            if any(b < a0 for a0, b in zip(ts_page, ts_page[1:])):
                counts["page_nonmonotonic"] += 1
        conn.commit()
    finally:
        conn.close()
        for suffix in ("", "-wal", "-shm"):
            q = Path(str(db) + suffix)
            if q.exists():
                q.unlink()

    hard_zero = [
        "missing_trade_id", "duplicate_trade_id", "page_nonmonotonic",
        "page_out_of_bounds", "timestamp_invalid", "instrument_parse_failure",
        "iv_invalid", "index_price_invalid", "mark_price_invalid",
        "direction_invalid", "amount_invalid_when_present",
    ]
    return {
        **counts,
        "schema_and_provenance_pass": all(counts[k] == 0 for k in hard_zero),
        "underlying_source_status": r.get("status"),
        "underlying_valid_signal_coverage_days": a.get("valid_signal_coverage_days"),
        "underlying_min_required_valid_days": a.get("min_required_valid_days"),
        "underlying_probe_mode": m.get("probe_mode"),
        "outcomes_computed": False,
    }


def months() -> list[tuple[int, int]]:
    out = []
    y, m = 2021, 4
    while (y, m) <= (2024, 12):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def audit_binance(root: Path, probe: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dest = root / "raw_binance_btcusdt_1d"
    dest.mkdir(parents=True, exist_ok=True)
    todo = months()[:1] if probe else months()
    found: set[str] = set()
    manifest: list[dict[str, Any]] = []
    for y, mo in todo:
        if y >= 2025:
            raise RuntimeError("FAIL-CLOSED attempted 2025+ BTC price archive")
        name = f"BTCUSDT-1d-{y:04d}-{mo:02d}.zip"
        url = f"{BINANCE}/{name}"
        b = fetch_bytes(url)
        path = dest / name
        path.write_bytes(b)
        try:
            zf = zipfile.ZipFile(io.BytesIO(b))
        except zipfile.BadZipFile as e:
            raise RuntimeError(f"bad Binance ZIP {name}: {e}") from e
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"unexpected ZIP members {name}: {members}")
        rows = 0
        with zf.open(members[0]) as raw:
            for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                if not row:
                    continue
                rows += 1
                try:
                    ms = int(row[0])
                except Exception as e:
                    raise RuntimeError(f"invalid BTC timestamp {name}") from e
                x = dt.datetime.fromtimestamp(ms / 1000, tz=UTC)
                if x.hour or x.minute or x.second or x.microsecond:
                    raise RuntimeError(f"BTC 1d timestamp not 00:00 UTC: {x.isoformat()}")
                if x < START or x >= END or x.year != y or x.month != mo:
                    raise RuntimeError(f"BTC archive cutoff/month violation: {x.isoformat()}")
                k = x.date().isoformat()
                if k in found:
                    raise RuntimeError(f"duplicate BTC date: {k}")
                found.add(k)
        manifest.append({"file": name, "url": url, "sha256": sha256_bytes(b), "bytes": len(b), "rows": rows})

    if probe:
        return ({
            "probe_mode": True, "archive_count": len(manifest),
            "date_min": min(found) if found else None, "date_max": max(found) if found else None,
            "exact_discovery_cutoff_verified": False,
        }, manifest)

    expected = set()
    d = START.date()
    while d < END.date():
        expected.add(d.isoformat())
        d += dt.timedelta(days=1)
    missing, extra = sorted(expected - found), sorted(found - expected)
    exact = (
        len(manifest) == 45 and not missing and not extra
        and min(found) == "2021-04-01" and max(found) == "2024-12-31"
    )
    return ({
        "probe_mode": False, "archive_count": len(manifest), "expected_archive_count": 45,
        "daily_observations": len(found), "expected_daily_observations": len(expected),
        "date_min": min(found), "date_max": max(found),
        "missing_dates_preview": missing[:20], "extra_dates_preview": extra[:20],
        "exact_discovery_cutoff_verified": exact,
    }, manifest)


def write_receipt(root: Path, status: str, binding: dict[str, Any] | None,
                  deribit: dict[str, Any] | None, btc: dict[str, Any] | None,
                  btc_manifest: list[dict[str, Any]], detail: str | None) -> Path:
    receipt = {
        "lab_id": LAB_ID, "version": VERSION, "stage": "FINAL_SOURCE_DATA_GATE",
        "status": status, "authority": binding, "deribit_audit": deribit,
        "btc_price_audit": btc, "btc_price_raw_archives": btc_manifest,
        "detail": detail, "skew_values_computed": False, "signals_computed": False,
        "forward_returns_computed": False, "pnl_computed": False,
        "holdout_2025_accessed": False, "year_2026_accessed": False,
    }
    p = root / "source_gate_receipt.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="source_audit_data")
    ap.add_argument("--probe-days", type=int, default=0)
    args = ap.parse_args()
    if args.probe_days < 0:
        raise SystemExit("--probe-days must be >= 0")

    here = Path(__file__).resolve().parent
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    probe = args.probe_days > 0
    binding = deribit = btc = None
    btc_manifest: list[dict[str, Any]] = []

    print(f"{LAB_ID} {VERSION} — FINAL SOURCE/DATA GATE")
    print("NO skew | NO signals | NO returns | NO PnL | NO 2025/2026")
    try:
        binding = protocol_binding(here / "PROTOCOL.json")
        cmd = [sys.executable, str(here / "source_audit.py"), "--output", str(root)]
        if probe:
            cmd += ["--probe-days", str(args.probe_days)]
        rc = subprocess.run(cmd, check=False).returncode
        if rc == 12:
            p = write_receipt(root, "EXECUTION_ENVIRONMENT_BLOCKED", binding, None, None, [], "underlying Deribit audit network/transport block")
            print(f"EXECUTION_ENVIRONMENT_BLOCKED: {p}")
            return 12
        if rc not in ({4} if probe else {0}):
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", binding, None, None, [], f"underlying source_audit.py returned {rc}")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        deribit = audit_deribit_raw(root, probe)
        if not deribit["schema_and_provenance_pass"]:
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", binding, deribit, None, [], "Deribit raw-page/schema/provenance gate failed")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        btc, btc_manifest = audit_binance(root, probe)
        if probe:
            p = write_receipt(root, "PROBE_ONLY_NO_DECISION", binding, deribit, btc, btc_manifest, None)
            print(f"PROBE_ONLY_NO_DECISION: {p}")
            return 4

        coverage = deribit.get("underlying_valid_signal_coverage_days")
        min_cov = deribit.get("underlying_min_required_valid_days")
        coverage_pass = isinstance(coverage, int) and isinstance(min_cov, int) and coverage >= min_cov
        if not coverage_pass or btc.get("exact_discovery_cutoff_verified") is not True:
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", binding, deribit, btc, btc_manifest, "coverage or exact BTC price cutoff gate failed")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        p = write_receipt(root, "SOURCE_AUDIT_PASS", binding, deribit, btc, btc_manifest, None)
        print(f"SOURCE_AUDIT_PASS: {p}")
        return 0

    except EnvBlocked as e:
        p = write_receipt(root, "EXECUTION_ENVIRONMENT_BLOCKED", binding, deribit, btc, btc_manifest, str(e))
        print(f"EXECUTION_ENVIRONMENT_BLOCKED: {p}")
        return 12
    except Exception as e:
        p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", binding, deribit, btc, btc_manifest, str(e))
        print(f"SOURCE_AUDIT_BLOCKED: {p}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
