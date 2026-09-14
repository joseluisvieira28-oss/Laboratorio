#!/usr/bin/env python3
"""Technical wrapper around the frozen 2025 OOS Confirmation runner.

Only Binance timestamp-unit decoding is replaced. Candidate UP_LOW, costs,
metrics, gates, OOS window, and 2026 firewall remain exactly those of V0.1.
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import zipfile
from pathlib import Path

import binance_timestamp_normalizer_v01 as tsnorm
import confirmation_runner_2025_v01 as base


def compatible_load_btc(root: Path, manifest):
    out = {}
    entries = manifest.get('btc_price_raw_archives', [])
    if len(entries) != 13:
        raise RuntimeError('SOURCE_OR_DATA_BLOCKED: expected 13 BTC archives')
    for e in entries:
        p = root / 'raw_binance_btcusdt_1d' / e['file']
        if not p.exists() or base.sha(p) != e['sha256']:
            raise RuntimeError('SOURCE_OR_DATA_BLOCKED: BTC integrity')
        with zipfile.ZipFile(p) as zf:
            members = [x for x in zf.namelist() if not x.endswith('/')]
            if len(members) != 1:
                raise RuntimeError('SOURCE_OR_DATA_BLOCKED: BTC zip members')
            with zf.open(members[0]) as fh:
                for row in csv.reader(io.TextIOWrapper(fh, encoding='utf-8')):
                    if not row:
                        continue
                    d = tsnorm.to_utc_datetime(row[0]).date()
                    if d.year >= 2026:
                        raise RuntimeError('SOURCE_OR_DATA_BLOCKED: 2026 BTC row')
                    if d.year < 2024:
                        raise RuntimeError('SOURCE_OR_DATA_BLOCKED: unexpected BTC history year')
                    op = float(row[1])
                    if not (math.isfinite(op) and op > 0):
                        raise RuntimeError('SOURCE_OR_DATA_BLOCKED: invalid BTC open')
                    out[d] = op
    return out


def main() -> int:
    tsnorm.self_test()
    base.load_btc = compatible_load_btc
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    return int(base.run(Path(args.source_root), Path(args.output)))


if __name__ == '__main__':
    raise SystemExit(main())
