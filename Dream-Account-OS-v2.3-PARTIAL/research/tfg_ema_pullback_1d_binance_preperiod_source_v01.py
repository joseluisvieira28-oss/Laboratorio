from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

LAB_ID = "TFG-EMA-PULLBACK-1D-BINANCE-PREPERIOD-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2021-01"
END_MONTH = "2022-12"
INTERVAL = "15m"
FIFTEEN_MIN_MS = 900_000
START_MS = 1609459200000
END_MS = 1672531200000
BASE = "https://data.binance.vision/data/spot/monthly/klines"
HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")


def months(start: str, end: str) -> list[str]:
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out: list[str] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-Research/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def normalize_ts(v: str) -> int:
    x = int(v)
    if x > 100_000_000_000_000:
        x //= 1000
    return x


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    month_list = months(START_MONTH, END_MONTH)
    archive_receipts: list[dict] = []
    symbol_receipts: dict[str, dict] = {}
    accepted = 0

    for symbol in SYMBOLS:
        rows: dict[int, tuple[int, str, str, str, str, str, int]] = {}
        for month in month_list:
            filename = f"{symbol}-{INTERVAL}-{month}.zip"
            url = f"{BASE}/{symbol}/{INTERVAL}/{filename}"
            checksum_url = url + ".CHECKSUM"
            payload = get(url)
            checksum_text = get(checksum_url).decode("utf-8", errors="strict").strip()
            expected = checksum_text.split()[0].lower()
            observed = sha256_bytes(payload)
            if observed != expected:
                raise RuntimeError(f"CHECKSUM_MISMATCH:{filename}:{expected}:{observed}")

            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                names = [n for n in zf.namelist() if not n.endswith("/")]
                if len(names) != 1:
                    raise RuntimeError(f"ZIP_MEMBER_COUNT:{filename}:{len(names)}")
                raw = zf.read(names[0]).decode("utf-8")

            parsed = 0
            reader = csv.reader(io.StringIO(raw))
            for r in reader:
                if not r:
                    continue
                try:
                    t = normalize_ts(r[0])
                    close_t = normalize_ts(r[6])
                except ValueError:
                    continue
                if not (START_MS <= t < END_MS):
                    continue
                if t % FIFTEEN_MIN_MS != 0:
                    raise RuntimeError(f"OPEN_TIME_ALIGNMENT:{symbol}:{t}")
                if close_t != t + FIFTEEN_MIN_MS - 1:
                    raise RuntimeError(f"CLOSE_TIME_ALIGNMENT:{symbol}:{t}:{close_t}")
                o, h, l, c, v = r[1], r[2], r[3], r[4], r[5]
                vals = [float(o), float(h), float(l), float(c), float(v)]
                if min(vals[:4]) <= 0 or vals[4] < 0:
                    raise RuntimeError(f"INVALID_OHLCV:{symbol}:{t}")
                if vals[1] < max(vals[0], vals[2], vals[3]) or vals[2] > min(vals[0], vals[1], vals[3]):
                    raise RuntimeError(f"OHLC_ORDER:{symbol}:{t}")
                row = (t, o, h, l, c, v, close_t)
                if t in rows and rows[t] != row:
                    raise RuntimeError(f"DUPLICATE_CONFLICT:{symbol}:{t}")
                rows[t] = row
                parsed += 1

            archive_receipts.append({
                "symbol": symbol,
                "month": month,
                "filename": filename,
                "url": url,
                "checksum_url": checksum_url,
                "published_sha256": expected,
                "observed_sha256": observed,
                "parsed_rows_in_window": parsed,
                "accepted": True,
            })
            accepted += 1

        ordered = [rows[k] for k in sorted(rows)]
        path = out / f"{symbol}_15m_2021_2022.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            w.writerows(ordered)

        gaps = 0
        prev = None
        for r in ordered:
            if prev is not None and r[0] - prev != FIFTEEN_MIN_MS:
                gaps += 1
            prev = r[0]
        symbol_receipts[symbol] = {
            "rows": len(ordered),
            "first_open_time_ms": ordered[0][0] if ordered else None,
            "last_open_time_ms": ordered[-1][0] if ordered else None,
            "detected_15m_gap_transitions": gaps,
            "canonical_csv_sha256": canonical_hash(path),
        }

    receipt = {
        "lab": LAB_ID,
        "stage": "BINANCE_PREPERIOD_SOURCE_V01",
        "classification": "SOURCE_READY" if accepted == 144 else "SOURCE_INCOMPLETE",
        "provider": "BINANCE_DATA_VISION",
        "market": "SPOT",
        "symbols": list(SYMBOLS),
        "interval": INTERVAL,
        "source_start_month": START_MONTH,
        "source_end_month": END_MONTH,
        "source_window_start_ms": START_MS,
        "source_window_end_ms_exclusive": END_MS,
        "expected_archive_count": 144,
        "accepted_archive_count": accepted,
        "archive_receipts": archive_receipts,
        "symbol_receipts": symbol_receipts,
        "accessed_2023": False,
        "accessed_2024": False,
        "accessed_2025": False,
        "accessed_2026": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "outcome_evaluation_performed": False,
    }
    receipt_bytes = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8")
    receipt["receipt_sha256_without_self"] = hashlib.sha256(receipt_bytes).hexdigest()
    (out / "SOURCE_RECEIPT.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "accepted_archive_count": accepted,
        "symbol_rows": {k: v["rows"] for k, v in symbol_receipts.items()},
        "accessed_2023": False,
        "accessed_2024": False,
        "accessed_2025": False,
        "accessed_2026": False,
    }, indent=2, sort_keys=True))
    return 0 if accepted == 144 else 2


if __name__ == "__main__":
    raise SystemExit(main())
