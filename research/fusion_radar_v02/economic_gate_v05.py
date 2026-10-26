#!/usr/bin/env python3
"""Fusion AVAX20+BTC20 V0.5: frozen historical friction sensitivity.

Research-only. Reads the single *already exposed* operator CSV, exactly 730
2022-23 observations. No network access; no 2024-26, orders or account calls.
No new signal/fee parameter is chosen or optimized on the data. Illustrative
cost grids are not claims about a particular exchange or execution venue.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
from hashlib import sha256
import json
import math
from pathlib import Path

EXPECTED_CSV_SHA256 = '38b042c4d439f8ddf2f6bc5665b24608345a765dddbc00b2f0d4f767729ad8d3'
START = date(2022, 1, 1)
N_DAYS = 730
# Fixed hypothetical TOTAL roundtrip friction incl. both fees, spread,
# slippage, latency, and other applicable costs (no double fee counting).
TOTAL_COST_GRID_BPS = (0, 4, 8, 10, 12, 14, 16, 20, 24)

class GateError(ValueError):
    pass


def load_rows(path: Path):
    original = path.read_bytes()
    if sha256(original).hexdigest() != EXPECTED_CSV_SHA256:
        raise GateError('EXPOSED_SOURCE_CSV_HASH_MISMATCH')
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'date', 'avax20', 'btc20', 'gross_bps',
                    'baseline_trade', 'fusion_trade', 'opposite_context_trade'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise GateError('MISSING_FROZEN_COLUMNS')
        rows = list(reader)
    if len(rows) != N_DAYS:
        raise GateError('UNEXPECTED_DAYS')
    out = []
    for index, item in enumerate(rows):
        day = START + timedelta(days=index)
        if item['date'] != day.isoformat():
            raise GateError('CALENDAR_GAP_OR_HOLDOUT')
        if item['avax20'] not in ('-1', '0', '1') or item['btc20'] not in ('-1', '0', '1'):
            raise GateError('BAD_DIRECTION')
        a, b = int(item['avax20']), int(item['btc20'])
        try:
            gross = float(item['gross_bps'])
        except ValueError as e:
            raise GateError('BAD_GROSS_RETURN') from e
        if not math.isfinite(gross):
            raise GateError('NONFINITE_GROSS_RETURN')
        masks = {
            'baseline_trade': bool(a),
            'fusion_trade': bool(a and a == b),
            'opposite_context_trade': bool(a and a == -b),
        }
        for name, predicted in masks.items():
            if item[name] != str(predicted):
                raise GateError('MASK_NOT_REPRODUCIBLE:' + name)
        if sum((masks['fusion_trade'], masks['opposite_context_trade'])) != masks['baseline_trade']:
            raise GateError('NON_PARTITIONING_BTC_SIGN')
        out.append({'day': day, 'a': a, 'b': b, 'gross': gross, 'masks': masks})
    if sum(x['masks']['fusion_trade'] for x in out) != 568:
        raise GateError('EXPECTED_FROZEN_FUSION_N_MISMATCH')
    return out


def scenario(rows, cost_bps):
    """Single daily unit of notional; no compounding, no leverage."""
    if not 0 <= cost_bps <= 100 or not math.isfinite(cost_bps):
        raise GateError('INVALID_ROUNDTRIP_FRICTION')
    out = {}
    for year in ('2022', '2023', 'all'):
        sub = rows if year == 'all' else [r for r in rows if str(r['day'].year) == year]
        sample = [r['gross'] for r in sub if r['masks']['fusion_trade']]
        benchmark = [r['gross'] for r in sub if r['masks']['baseline_trade']]
        if not sample:
            raise GateError('ZERO_FUSION_ENTRIES')
        out[year] = {
            'calendar_days': len(sub),
            'fusion_trades': len(sample),
            'break_even_total_friction_bps': round(sum(sample)/len(sample), 6),
            'fusion_net_mean_bps_per_trade': round(sum(sample)/len(sample)-cost_bps, 6),
            'fusion_net_mean_bps_per_calendar_day': round((sum(sample)-cost_bps*len(sample))/len(sub), 6),
            'fusion_net_sum_bps_daily_unit_notional': round(sum(sample)-cost_bps*len(sample), 6),
            'baseline_net_sum_bps_daily_unit_notional': round(sum(benchmark)-cost_bps*len(benchmark), 6),
        }
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('results/FUSION_ECONOMIC_GATE_V05.json'))
    args = p.parse_args()
    rows = load_rows(args.csv)
    output = {
        'identity': 'FUSION_AVAX20_BTC20_FROZEN_ECONOMIC_GATE_V05',
        'source_sha256': EXPECTED_CSV_SHA256,
        'source_period': '2022-01-01 through 2023-12-31 UTC',
        'status': 'EXPLORATORY_COST_SENSITIVITY_ONLY',
        'cost_model': 'hypothetical total roundtrip friction inclusive of fees, bid-ask and impact',
        'cost_scenarios_total_roundtrip_bps': {
            str(c): scenario(rows, float(c)) for c in TOTAL_COST_GRID_BPS
        },
        'known_unknowns': [
            'ACTUAL_MEXC_SWITZERLAND_FEE_TIER_UNVERIFIED',
            'HISTORICAL_MEXC_BID_ASK_ORDER_BOOK_NOT_AVAILABLE',
            'HISTORICAL_VENUE_BASIS_BINANCE_TO_MEXC_NOT_ESTIMATED',
            'OPEN_PRICE_NOT_EXECUTABLE_FILL',
            'SLIPPAGE_LATENCY_NOT_MEASURED',
            'FUNDING_APPLICABILITY_NOT_VERIFIED',
            'INDEPENDENT_OUT_OF_SAMPLE_EDGE_NOT_TESTED',
        ],
        'execution_gate': 'NO_GO_UNVERIFIED_REAL_EXECUTION_COST',
        'scientific_promotion': 'NO_GO',
        'critical_guard': '2024_2025_2026_HOLDOUT_CLOSED',
    }
    args.output.parent.mkdir(exist_ok=True, parents=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'report': str(args.output),
                      'all_break_even': output['cost_scenarios_total_roundtrip_bps']['14']['all']['break_even_total_friction_bps'],
                      '2023_break_even': output['cost_scenarios_total_roundtrip_bps']['14']['2023']['break_even_total_friction_bps'],
                      'execution_gate': output['execution_gate']},indent=2))


if __name__ == '__main__':
    try:
        main()
    except (GateError, OSError) as ex:
        raise SystemExit('FAIL_CLOSED: ' + str(ex)) from ex
