#!/usr/bin/env python3
"""Technical wrapper around the frozen 2025 source acquisition.

Only Binance timestamp-unit decoding is replaced. Deribit acquisition, source
window, candidate, scientific gates, costs, and 2026 firewall remain unchanged.
"""
from __future__ import annotations

import argparse
import urllib.request
import zipfile
from pathlib import Path

import binance_timestamp_normalizer_v01 as tsnorm
import confirmation_source_acquire_2025_v01 as base


def compatible_download_binance(out: Path):
    d = out / 'raw_binance_btcusdt_1d'
    d.mkdir(parents=True, exist_ok=True)
    entries = []
    for y, m in base.BINANCE_MONTHS:
        name = f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'
        url = f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/{name}'
        p = d / name
        with urllib.request.urlopen(url, timeout=90) as r:
            p.write_bytes(r.read())
        with zipfile.ZipFile(p) as zf:
            members = [n for n in zf.namelist() if not n.endswith('/')]
            if len(members) != 1:
                raise RuntimeError(f'unexpected Binance ZIP members: {name}')
            rows = []
            with zf.open(members[0]) as fh:
                for line in fh:
                    s = line.decode('utf-8').strip()
                    if s:
                        rows.append(s)
            if not rows:
                raise RuntimeError(f'empty Binance archive: {name}')
            first_ms = tsnorm.to_milliseconds(rows[0].split(',')[0])
            last_ms = tsnorm.to_milliseconds(rows[-1].split(',')[0])
            first_dt = tsnorm.to_utc_datetime(rows[0].split(',')[0])
            last_dt = tsnorm.to_utc_datetime(rows[-1].split(',')[0])
            if first_dt.year >= 2026 or last_dt.year >= 2026:
                raise RuntimeError('FAIL-CLOSED: 2026 Binance row present')
            if y == 2024 and not (first_dt.year == 2024 and last_dt.year == 2024):
                raise RuntimeError(f'FAIL-CLOSED: unexpected year in {name}')
            if y == 2025 and not (first_dt.year == 2025 and last_dt.year == 2025):
                raise RuntimeError(f'FAIL-CLOSED: unexpected year in {name}')
        entries.append({
            'file': name,
            'url': url,
            'sha256': base.sha256_file(p),
            'bytes': p.stat().st_size,
            'first_open_ms': first_ms,
            'last_open_ms': last_ms,
            'timestamp_unit_normalized_to': 'milliseconds',
        })
    return entries


def main() -> int:
    tsnorm.self_test()
    base.download_binance = compatible_download_binance
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    return int(base.run(Path(args.output)))


if __name__ == '__main__':
    raise SystemExit(main())
