from __future__ import annotations

"""Outcome-blind source-byte gate for TFG-VWAP-15M-001.

The gate opens only the inner .csv.zst member BYTES for Discovery 2022-01..2023-12
from the already-normalized H180 packages. It does not decompress the Zstandard
payload, parse a market row, form a VWAP signal, calculate a return/PnL, or open
2024/2025/2026 members. The aggregate fingerprint emitted here must be committed
before the Discovery runner can be activated.
"""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

LAB_ID = "TFG-VWAP-15M-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
EXPECTED_PACKAGES = {s: f"H180-0001_NORMALIZED_{s}.zip" for s in SYMBOLS}
EXPECTED_HISTORICAL_H180_FP = "51952d966395e34a0390e1da3063b999c4de68d00a3e0e965e27f6ee58ed01f3"
EXPECTED_ACTIVE_H180_FP_V2 = "ff8b787d3b27e8daf80574ee35251836c2893e1f7c8eb32b5b6531edabbb1b42"
EXPECTED_RAW_FP = "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a"
EXPECTED_MEMBER_COUNT = 6 * 24


def months_2022_2023() -> list[str]:
    return [f"{year}-{month:02d}" for year in (2022, 2023) for month in range(1, 13)]


def expected_member(symbol: str, ym: str) -> str:
    return f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _aggregate(rows: list[dict]) -> str:
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_authorities(freeze_path: Path, amendment_path: Path, activation_path: Path) -> None:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    if freeze.get("experiment_id") != LAB_ID or freeze.get("status") != "PREFROZEN_NOT_EXECUTED":
        raise RuntimeError("FREEZE_ID_OR_STATUS_MISMATCH")
    if freeze["data_stages"]["discovery"].get("start") != "2022-01-01T00:00:00Z":
        raise RuntimeError("DISCOVERY_START_MISMATCH")
    if freeze["data_stages"]["discovery"].get("end") != "2023-12-31T23:59:59Z":
        raise RuntimeError("DISCOVERY_END_MISMATCH")
    if freeze["governance"].get("2024_access_before_discovery_pass") is not False:
        raise RuntimeError("2024_FIREWALL_MISMATCH")
    if freeze["governance"].get("2025_access") is not False or freeze["governance"].get("2026_access") is not False:
        raise RuntimeError("PROTECTED_DATA_FIREWALL_MISMATCH")
    if amendment.get("status") != "FROZEN_BEFORE_ANY_TFG_VWAP_OUTCOME_EVALUATION":
        raise RuntimeError("PROVENANCE_AMENDMENT_STATUS_MISMATCH")
    if LAB_ID not in amendment.get("applies_to", []):
        raise RuntimeError("PROVENANCE_AMENDMENT_SCOPE_MISMATCH")
    if amendment.get("historical_h180_bundle_fingerprint") != EXPECTED_HISTORICAL_H180_FP:
        raise RuntimeError("HISTORICAL_H180_FP_MISMATCH")
    if amendment.get("active_h180_bundle_fingerprint_v2") != EXPECTED_ACTIVE_H180_FP_V2:
        raise RuntimeError("ACTIVE_H180_FP_MISMATCH")
    if amendment.get("monthly_raw_fingerprint") != EXPECTED_RAW_FP:
        raise RuntimeError("RAW_FP_MISMATCH")
    if activation.get("experiment_id") != LAB_ID:
        raise RuntimeError("ACTIVATION_ID_MISMATCH")
    if activation.get("outcome_evaluation_authorized_now") is not False:
        raise RuntimeError("OUTCOME_AUTHORITY_UNEXPECTEDLY_OPEN")
    if activation["data_lock"].get("discovery_member_fingerprint") is not None:
        raise RuntimeError("SOURCE_FINGERPRINT_ALREADY_FROZEN_USE_BOUND_RUNNER")


def run(normalized_dir: Path, freeze_path: Path, amendment_path: Path, activation_path: Path) -> dict:
    _validate_authorities(freeze_path, amendment_path, activation_path)
    rows: list[dict] = []
    for symbol in SYMBOLS:
        package = normalized_dir / EXPECTED_PACKAGES[symbol]
        if not package.is_file():
            raise RuntimeError(f"MISSING_NORMALIZED_PACKAGE:{package.name}")
        with zipfile.ZipFile(package, "r") as archive:
            names = set(archive.namelist())
            for ym in months_2022_2023():
                member = expected_member(symbol, ym)
                if member not in names:
                    raise RuntimeError(f"MISSING_DISCOVERY_MEMBER:{member}")
                # This reads the inner Zstandard file bytes only. No Zstd decompression,
                # CSV parsing, signal formation, price inspection, or outcome evaluation.
                payload = archive.read(member)
                rows.append({
                    "symbol": symbol,
                    "month": ym,
                    "member": member,
                    "byte_count": len(payload),
                    "sha256": _sha(payload),
                })
    rows.sort(key=lambda r: (r["symbol"], r["month"], r["member"]))
    if len(rows) != EXPECTED_MEMBER_COUNT:
        raise RuntimeError(f"DISCOVERY_MEMBER_COUNT_MISMATCH:{len(rows)}")
    fingerprint = _aggregate(rows)
    return {
        "status": "PASS_SOURCE_BYTE_GATE_AWAITING_FINGERPRINT_FREEZE",
        "lab_id": LAB_ID,
        "source_authority": "H180-0001_NORMALIZED_BINANCE_USDM_1M",
        "historical_h180_bundle_fingerprint": EXPECTED_HISTORICAL_H180_FP,
        "active_h180_bundle_fingerprint_v2": EXPECTED_ACTIVE_H180_FP_V2,
        "monthly_raw_fingerprint": EXPECTED_RAW_FP,
        "discovery_month_range": ["2022-01", "2023-12"],
        "symbol_count": len(SYMBOLS),
        "member_count": len(rows),
        "discovery_member_fingerprint": fingerprint,
        "member_hashes": rows,
        "zstandard_payload_decompressed": False,
        "market_rows_parsed": False,
        "signal_geometry_evaluation_performed": False,
        "outcome_evaluation_performed": False,
        "return_or_pnl_computation_performed": False,
        "internal_oos_2024_member_bytes_opened": False,
        "protected_2025_member_bytes_opened": False,
        "locked_2026_member_bytes_opened": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "next_required_action": "COMMIT_DISCOVERY_MEMBER_FINGERPRINT_BEFORE_OUTCOMES",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Outcome-blind source-byte gate for TFG-VWAP-15M-001")
    parser.add_argument("--normalized-dir", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--amendment", required=True)
    parser.add_argument("--activation", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt_path = Path(args.receipt)
    try:
        payload = run(Path(args.normalized_dir), Path(args.freeze), Path(args.amendment), Path(args.activation))
        rc = 0
    except Exception as exc:
        payload = {
            "status": "BLOCKED_PRE_OUTCOME_SOURCE_GATE",
            "lab_id": LAB_ID,
            "reason": f"{type(exc).__name__}:{exc}",
            "market_rows_parsed": False,
            "outcome_evaluation_performed": False,
            "return_or_pnl_computation_performed": False,
            "internal_oos_2024_member_bytes_opened": False,
            "protected_2025_member_bytes_opened": False,
            "locked_2026_member_bytes_opened": False,
            "network_access_performed": False,
            "exchange_mutation_performed": False,
            "orders_submitted": False,
        }
        rc = 2
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
