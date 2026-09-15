from __future__ import annotations

"""Official Binance source recovery + deterministic H180 Discovery normalization.

Research/source-only helper for TFG-VWAP-15M-001. It downloads only 2022-01..2023-12
USD-M Futures monthly 1m archives and their CHECKSUM sidecars from data.binance.vision,
verifies SHA-256, audits exact historical H180 Discovery structure, and recreates only
Discovery normalized members using the frozen H180-NORM-1.0.0 contract.

It does NOT access 2024/2025/2026 market data, calculate VWAP/signals/returns/PnL,
or perform any exchange mutation or order action.
"""

import argparse
import calendar
import hashlib
import io
import json
import os
import re
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import zstandard as zstd

LAB_ID = "TFG-VWAP-15M-001"
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
MONTHS = tuple(f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13))
START_MS = 1640995200000
END_EXCLUSIVE_MS = 1704067200000
MINUTE_MS = 60000
EXPECTED_ROWS = {
    "BTCUSDT": 1051200,
    "ETHUSDT": 1051200,
    "SOLUSDT": 1044000,
    "BNBUSDT": 1051200,
    "XRPUSDT": 1044000,
    "DOGEUSDT": 1051200,
}
EXPECTED_GAPS = {
    "BTCUSDT": (),
    "ETHUSDT": (),
    "SOLUSDT": ((1645833600000, 1646092800000, 4320), (1648771200000, 1648944000000, 2880)),
    "BNBUSDT": (),
    "XRPUSDT": ((1645833600000, 1646092800000, 4320), (1648771200000, 1648944000000, 2880)),
    "DOGEUSDT": (),
}
EXPECTED_TOTAL_ROWS = 6292800
EXPECTED_MISSING_TOTAL = 14400
FIELDS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_volume",
    "taker_buy_quote_volume", "ignore_provider_field", "symbol", "interval",
    "source_archive", "source_csv", "provider_sha256", "source_local_sha256",
]
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Sink:
    def __init__(self, x):
        self.x = x
        self.h = hashlib.sha256()
        self.n = 0

    def write(self, b: bytes):
        self.h.update(b)
        self.n += len(b)
        return self.x.write(b)

    def flush(self):
        return self.x.flush()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def month_bounds_ms(ym: str) -> tuple[int, int]:
    year, month = map(int, ym.split("-"))
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def download(url: str, target: Path, retries: int = 3) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Crypto-Lab-TFG-VWAP-Source-Recovery/1.0"})
            with urllib.request.urlopen(req, timeout=60) as response, tmp.open("wb") as out:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"HTTP_{response.status}")
                while True:
                    block = response.read(1 << 20)
                    if not block:
                        break
                    out.write(block)
            os.replace(tmp, target)
            return
        except Exception:
            if tmp.exists():
                tmp.unlink()
            if attempt >= retries:
                raise
            time.sleep(1.5 * attempt)


def ensure_archive(raw_root: Path, symbol: str, ym: str) -> tuple[Path, str, str]:
    fname = f"{symbol}-1m-{ym}.zip"
    archive = raw_root / symbol / "1m" / fname
    checksum = archive.with_name(fname + ".CHECKSUM")
    base = f"{BASE}/{symbol}/1m/{fname}"

    if not checksum.exists():
        download(base + ".CHECKSUM", checksum)
    text = checksum.read_text(encoding="utf-8-sig").strip()
    parts = text.split()
    if not parts or not HEX64.fullmatch(parts[0].lower()):
        raise RuntimeError(f"INVALID_PROVIDER_CHECKSUM:{symbol}:{ym}")
    provider = parts[0].lower()

    if archive.exists() and sha256_file(archive) != provider:
        archive.unlink()
    if not archive.exists():
        download(base, archive)
    local = sha256_file(archive)
    if local != provider:
        raise RuntimeError(f"CHECKSUM_MISMATCH:{symbol}:{ym}:{local}:{provider}")
    return archive, provider, local


def normalize_month(
    package: zipfile.ZipFile,
    archive_path: Path,
    symbol: str,
    ym: str,
    provider_sha: str,
    local_sha: str,
    last_seen: int | None,
) -> tuple[dict, int | None, list[tuple[int, int, int]]]:
    source_archive_name = f"{symbol}/1m/{symbol}-1m-{ym}.zip"
    with zipfile.ZipFile(archive_path, "r") as source_zip:
        csvs = [n for n in source_zip.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise RuntimeError(f"CSV_MEMBER_COUNT:{symbol}:{ym}:{len(csvs)}")
        source_csv = csvs[0]
        member = f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst"
        zi = zipfile.ZipInfo(member, (1980, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_STORED
        zi.external_attr = 0o100444 << 16

        uh = hashlib.sha256()
        rows = 0
        first = None
        last = None
        gaps: list[tuple[int, int, int]] = []
        month_start, month_end = month_bounds_ms(ym)
        zc = zstd.ZstdCompressor(level=6, threads=0, write_checksum=True, write_content_size=False)

        with package.open(zi, "w", force_zip64=True) as rawout:
            sink = Sink(rawout)
            with zc.stream_writer(sink, closefd=False) as zw:
                header = (",".join(FIELDS) + "\n").encode()
                zw.write(header)
                uh.update(header)
                with source_zip.open(source_csv, "r") as src:
                    for rb in src:
                        line = rb.decode("utf-8-sig").rstrip("\r\n")
                        if not line or line.startswith("open_time,"):
                            continue
                        x = line.split(",")
                        if len(x) != 12:
                            raise RuntimeError(f"SCHEMA_ROW:{symbol}:{ym}:{len(x)}")
                        try:
                            t = int(x[0])
                        except Exception as exc:
                            raise RuntimeError(f"BAD_OPEN_TIME:{symbol}:{ym}") from exc
                        if not (month_start <= t < month_end):
                            raise RuntimeError(f"MONTH_RANGE_VIOLATION:{symbol}:{ym}:{t}")
                        if not (START_MS <= t < END_EXCLUSIVE_MS):
                            raise RuntimeError(f"FROZEN_RANGE_VIOLATION:{symbol}:{ym}:{t}")
                        if last_seen is not None:
                            if t <= last_seen:
                                raise RuntimeError(f"ORDER_OR_DUPLICATE:{symbol}:{ym}:{t}")
                            if t - last_seen > MINUTE_MS:
                                missing = (t - last_seen) // MINUTE_MS - 1
                                gaps.append((last_seen + MINUTE_MS, t, int(missing)))
                        last_seen = t
                        first = t if first is None else first
                        last = t
                        out = (",".join(x + [symbol, "1m", source_archive_name, source_csv, provider_sha, local_sha]) + "\n").encode()
                        zw.write(out)
                        uh.update(out)
                        rows += 1

        return ({
            "symbol": symbol,
            "month": ym,
            "rows": rows,
            "first_open_time": first,
            "last_open_time": last,
            "source_archive": source_archive_name,
            "source_csv": source_csv,
            "provider_sha256": provider_sha,
            "source_local_sha256": local_sha,
            "normalized_member": member,
            "normalized_uncompressed_sha256": uh.hexdigest(),
            "normalized_compressed_sha256": sink.h.hexdigest(),
        }, last_seen, gaps)


def canonical_fingerprint(records: list[dict]) -> str:
    keys = [
        "symbol", "month", "rows", "first_open_time", "last_open_time", "source_archive",
        "provider_sha256", "source_local_sha256", "normalized_member",
        "normalized_uncompressed_sha256", "normalized_compressed_sha256",
    ]
    rows = [{k: r[k] for k in keys} for r in sorted(records, key=lambda r: (r["symbol"], r["month"]))]
    encoded = (json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    return hashlib.sha256(encoded).hexdigest()


def run(raw_root: Path, normalized_dir: Path, receipt: Path) -> int:
    records: list[dict] = []
    audit_by_symbol: dict[str, dict] = {}
    network_used = False
    try:
        normalized_dir.mkdir(parents=True, exist_ok=True)
        for symbol in SYMBOLS:
            package_path = normalized_dir / f"H180-0001_NORMALIZED_{symbol}.zip"
            tmp_package = package_path.with_suffix(".zip.part")
            if tmp_package.exists():
                tmp_package.unlink()
            total = 0
            last_seen = None
            gaps: list[tuple[int, int, int]] = []
            month_rows: dict[str, int] = {}
            with zipfile.ZipFile(tmp_package, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as package:
                for ym in MONTHS:
                    archive_before = raw_root / symbol / "1m" / f"{symbol}-1m-{ym}.zip"
                    checksum_before = archive_before.with_name(archive_before.name + ".CHECKSUM")
                    if not (archive_before.exists() and checksum_before.exists()):
                        network_used = True
                    archive, provider, local = ensure_archive(raw_root, symbol, ym)
                    rec, last_seen, found_gaps = normalize_month(package, archive, symbol, ym, provider, local, last_seen)
                    records.append(rec)
                    month_rows[ym] = rec["rows"]
                    total += rec["rows"]
                    gaps.extend(found_gaps)
                    print(f"{symbol} {ym}: rows={rec['rows']:,} checksum=PASS", flush=True)
            os.replace(tmp_package, package_path)
            normalized_gaps = tuple((int(a), int(b), int(n)) for a, b, n in gaps)
            expected_gaps = EXPECTED_GAPS[symbol]
            audit_by_symbol[symbol] = {
                "rows": total,
                "expected_rows": EXPECTED_ROWS[symbol],
                "row_count_pass": total == EXPECTED_ROWS[symbol],
                "gaps": [list(g) for g in normalized_gaps],
                "expected_gaps": [list(g) for g in expected_gaps],
                "gap_structure_pass": normalized_gaps == expected_gaps,
                "first_open_time": next(r["first_open_time"] for r in records if r["symbol"] == symbol and r["month"] == "2022-01"),
                "last_open_time": next(r["last_open_time"] for r in records if r["symbol"] == symbol and r["month"] == "2023-12"),
                "monthly_rows": month_rows,
                "normalized_package": package_path.name,
                "normalized_package_sha256_discovery_only": sha256_file(package_path),
            }

        total_rows = sum(a["rows"] for a in audit_by_symbol.values())
        total_missing = sum(g[2] for a in audit_by_symbol.values() for g in a["gaps"])
        structure_pass = (
            len(records) == 144
            and total_rows == EXPECTED_TOTAL_ROWS
            and total_missing == EXPECTED_MISSING_TOTAL
            and all(a["row_count_pass"] and a["gap_structure_pass"] for a in audit_by_symbol.values())
            and all(a["first_open_time"] == START_MS for a in audit_by_symbol.values())
            and all(a["last_open_time"] == END_EXCLUSIVE_MS - MINUTE_MS for a in audit_by_symbol.values())
        )
        fingerprint = canonical_fingerprint(records) if structure_pass else None
        status = "PASS_REACQUISITION_NORMALIZATION_AWAITING_FINGERPRINT_FREEZE" if structure_pass else "SOURCE_VERSION_DRIFT_BLOCKED"
        payload = {
            "status": status,
            "lab_id": LAB_ID,
            "source": "BINANCE_PUBLIC_DATA_USDM_MONTHLY_KLINES_1M",
            "source_host": "data.binance.vision",
            "months": [MONTHS[0], MONTHS[-1]],
            "symbols": list(SYMBOLS),
            "monthly_archive_count": len(records),
            "provider_checksum_verified_count": len(records),
            "total_rows": total_rows,
            "expected_total_rows": EXPECTED_TOTAL_ROWS,
            "total_missing_minutes": total_missing,
            "expected_missing_minutes": EXPECTED_MISSING_TOTAL,
            "per_symbol": audit_by_symbol,
            "discovery_source_member_fingerprint": fingerprint,
            "normalization_version": "H180-NORM-1.0.0",
            "historical_h180_canonical_fingerprint_reference": "51952d966395e34a0390e1da3063b999c4de68d00a3e0e965e27f6ee58ed01f3",
            "historical_h180_full_raw_fingerprint_reference": "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a",
            "records": records,
            "network_access_performed": network_used,
            "market_rows_parsed_for_source_integrity_only": True,
            "vwap_signal_calculation_performed": False,
            "outcome_evaluation_performed": False,
            "return_or_pnl_computation_performed": False,
            "internal_oos_2024_access_performed": False,
            "protected_2025_access_performed": False,
            "locked_2026_access_performed": False,
            "exchange_mutation_performed": False,
            "orders_submitted": False,
            "next_required_action": "COMMIT_DISCOVERY_SOURCE_MEMBER_FINGERPRINT_BEFORE_OUTCOMES" if structure_pass else "STOP_SOURCE_VERSION_DRIFT",
        }
        write_json(receipt, payload)
        print(json.dumps({
            "status": status,
            "monthly_archive_count": len(records),
            "total_rows": total_rows,
            "total_missing_minutes": total_missing,
            "discovery_source_member_fingerprint": fingerprint,
            "outcome_evaluation_performed": False,
            "internal_oos_2024_access_performed": False,
            "protected_2025_access_performed": False,
            "locked_2026_access_performed": False,
        }, indent=2, sort_keys=True))
        return 0 if structure_pass else 3
    except Exception as exc:
        payload = {
            "status": "BLOCKED_PRE_OUTCOME_SOURCE_REACQUISITION",
            "lab_id": LAB_ID,
            "reason": f"{type(exc).__name__}:{exc}",
            "network_access_performed": network_used,
            "vwap_signal_calculation_performed": False,
            "outcome_evaluation_performed": False,
            "return_or_pnl_computation_performed": False,
            "internal_oos_2024_access_performed": False,
            "protected_2025_access_performed": False,
            "locked_2026_access_performed": False,
            "exchange_mutation_performed": False,
            "orders_submitted": False,
        }
        write_json(receipt, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Reacquire official Binance 2022-2023 Discovery source and reproduce H180 normalization")
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--normalized-dir", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    return run(Path(args.raw_root), Path(args.normalized_dir), Path(args.receipt))


if __name__ == "__main__":
    raise SystemExit(main())
