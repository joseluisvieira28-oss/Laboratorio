from __future__ import annotations

"""Outcome-blind source-identity preflight for TFG VWAP timeframe siblings.

This module verifies only the authorized 2022-01..2023-12 normalized member
bytes against the trusted H180 provenance manifest. It never decompresses
market candles, computes VWAP/signals/outcomes, or opens protected 2024/2025
member content.
"""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Iterable

LAB_IDS = ("TFG-VWAP-15M-001", "TFG-VWAP-30M-001")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
DISCOVERY_MONTHS = tuple(f"{year}-{month:02d}" for year in (2022, 2023) for month in range(1, 13))
PROVENANCE_MANIFEST_SHA256 = "14ad215a99d367fdd7dd393cd533aa7c83d78b2dee036ee140dd9c7a1f49c8b3"
MONTHLY_RAW_FINGERPRINT = "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a"
NORMALIZATION_VERSION = "H180-NORM-1.0.0"
EXPECTED_PACKAGES = {symbol: f"H180-0001_NORMALIZED_{symbol}.zip" for symbol in SYMBOLS}
OUTCOME_COMPUTATION_AUTHORIZED = False
WORKFLOW_TRIGGER_AUTHORIZED = False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_member(symbol: str, month: str) -> str:
    return f"{symbol}/1m/{symbol}-1m-{month}.normalized.csv.zst"


def load_trusted_provenance(path: Path, *, expected_sha256: str = PROVENANCE_MANIFEST_SHA256) -> dict:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise RuntimeError(f"PROVENANCE_MANIFEST_SHA256_MISMATCH:{actual}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("experiment") != "H180-0001":
        raise RuntimeError("PROVENANCE_EXPERIMENT_MISMATCH")
    if raw.get("provider") != "Binance" or raw.get("market") != "USD-M Futures":
        raise RuntimeError("PROVENANCE_VENUE_MISMATCH")
    if raw.get("interval") != "1m" or raw.get("clock") != "UTC":
        raise RuntimeError("PROVENANCE_INTERVAL_OR_CLOCK_MISMATCH")
    if raw.get("normalization_version") != NORMALIZATION_VERSION:
        raise RuntimeError("PROVENANCE_NORMALIZATION_VERSION_MISMATCH")
    if raw.get("monthly_raw_fingerprint") != MONTHLY_RAW_FINGERPRINT:
        raise RuntimeError("PROVENANCE_RAW_FINGERPRINT_MISMATCH")
    return raw


def _index_discovery_entries(provenance: dict, symbols: Iterable[str], months: Iterable[str]) -> dict[tuple[str, str], dict]:
    symbol_set = set(symbols)
    month_set = set(months)
    index: dict[tuple[str, str], dict] = {}
    for row in provenance.get("files", []):
        symbol = row.get("symbol")
        month = row.get("month")
        if symbol not in symbol_set or month not in month_set:
            continue
        key = (symbol, month)
        if key in index:
            raise RuntimeError(f"DUPLICATE_PROVENANCE_ENTRY:{symbol}:{month}")
        expected = expected_member(symbol, month)
        if row.get("normalized_member") != expected:
            raise RuntimeError(f"PROVENANCE_MEMBER_PATH_MISMATCH:{symbol}:{month}")
        digest = row.get("normalized_compressed_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RuntimeError(f"PROVENANCE_NORMALIZED_HASH_INVALID:{symbol}:{month}")
        index[key] = row

    expected_count = len(symbol_set) * len(month_set)
    if len(index) != expected_count:
        missing = sorted((s, m) for s in symbol_set for m in month_set if (s, m) not in index)
        raise RuntimeError(f"DISCOVERY_PROVENANCE_PARTITIONS_MISSING:{missing[:5]}:TOTAL={len(missing)}")
    return index


def verify_discovery_source_identity(
    normalized_dir: Path,
    provenance_manifest: Path,
    *,
    symbols: Iterable[str] = SYMBOLS,
    months: Iterable[str] = DISCOVERY_MONTHS,
    expected_manifest_sha256: str = PROVENANCE_MANIFEST_SHA256,
) -> dict:
    if OUTCOME_COMPUTATION_AUTHORIZED or WORKFLOW_TRIGGER_AUTHORIZED:
        raise RuntimeError("PREFREEZE_AUTHORITY_DRIFT")

    symbols = tuple(symbols)
    months = tuple(months)
    provenance = load_trusted_provenance(provenance_manifest, expected_sha256=expected_manifest_sha256)
    expected = _index_discovery_entries(provenance, symbols, months)

    verified: list[dict] = []
    total_bytes = 0
    for symbol in symbols:
        package_name = EXPECTED_PACKAGES.get(symbol, f"H180-0001_NORMALIZED_{symbol}.zip")
        package = normalized_dir / package_name
        if not package.is_file():
            raise RuntimeError(f"NORMALIZED_PACKAGE_MISSING:{package_name}")

        with zipfile.ZipFile(package) as zf:
            infos = {info.filename: info for info in zf.infolist()}
            if any("2026" in name for name in infos):
                raise RuntimeError(f"FORBIDDEN_2026_MEMBER_PRESENT:{package_name}")

            for month in months:
                member = expected_member(symbol, month)
                info = infos.get(member)
                if info is None:
                    raise RuntimeError(f"DISCOVERY_MEMBER_MISSING:{member}")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise RuntimeError(f"OUTER_PACKAGE_COMPRESSION_DRIFT:{member}")

                # The member itself is a .zst byte stream stored without outer ZIP compression.
                # Hash exactly those authorized Discovery bytes; do not decompress or parse them.
                payload = zf.read(member)
                actual = sha256_bytes(payload)
                exp = expected[(symbol, month)]
                wanted = exp["normalized_compressed_sha256"]
                if actual != wanted:
                    raise RuntimeError(f"DISCOVERY_MEMBER_SHA256_MISMATCH:{member}:{actual}")
                total_bytes += len(payload)
                verified.append({
                    "symbol": symbol,
                    "month": month,
                    "member": member,
                    "rows_from_trusted_manifest": exp.get("rows"),
                    "normalized_compressed_sha256": actual,
                    "member_bytes_hashed": len(payload),
                })

    required = len(symbols) * len(months)
    if len(verified) != required:
        raise RuntimeError(f"VERIFIED_PARTITION_COUNT_MISMATCH:{len(verified)}:{required}")

    return {
        "status": "PASS_DISCOVERY_SOURCE_IDENTITY_ONLY",
        "labs": list(LAB_IDS),
        "provider": "Binance",
        "market": "USD-M Futures",
        "source_interval": "1m",
        "clock": "UTC",
        "normalization_version": NORMALIZATION_VERSION,
        "trusted_provenance_manifest_sha256": expected_manifest_sha256,
        "monthly_raw_fingerprint": MONTHLY_RAW_FINGERPRINT,
        "months_verified": [months[0], months[-1]] if months else [],
        "symbols_verified": list(symbols),
        "discovery_members_verified": len(verified),
        "authorized_member_bytes_hashed": total_bytes,
        "verified_members": verified,
        "market_rows_decompressed": False,
        "market_rows_parsed": False,
        "vwap_computed": False,
        "signals_computed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "outcome_evaluation_performed": False,
        "outcome_computation_authorized": False,
        "workflow_trigger_authorized": False,
        "validation_2024_member_content_opened": False,
        "protected_2025_member_content_opened": False,
        "holdout_2026_member_content_opened": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "submitted_to_exchange": False,
        "next_state": "SOURCE_IDENTITY_READY_BUT_EXPERIMENT_REMAINS_PREFROZEN_UNTIL_QUEUE_TURN_AND_SEPARATE_ACTIVATION",
    }


def write_receipt(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Outcome-blind TFG VWAP Discovery provenance preflight")
    parser.add_argument("--normalized-dir", type=Path, required=True)
    parser.add_argument("--provenance-manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = verify_discovery_source_identity(args.normalized_dir, args.provenance_manifest)
    except Exception as exc:
        payload = {
            "status": "BLOCKED_PROVENANCE",
            "reason": str(exc),
            "outcome_evaluation_performed": False,
            "outcome_computation_authorized": False,
            "validation_2024_member_content_opened": False,
            "protected_2025_member_content_opened": False,
            "holdout_2026_member_content_opened": False,
            "network_access_performed": False,
            "exchange_mutation_performed": False,
            "submitted_to_exchange": False,
        }
        write_receipt(args.receipt, payload)
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2
    write_receipt(args.receipt, payload)
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
