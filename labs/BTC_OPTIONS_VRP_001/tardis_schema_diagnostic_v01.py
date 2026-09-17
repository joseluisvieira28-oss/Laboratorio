#!/usr/bin/env python3
"""Source-schema diagnostic only for the Tardis Deribit route.
No returns, PnL, expectancy, PF, drawdown, 2025 or 2026 access.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import tardis_source_probe_v01 as base

ROOT = Path(__file__).resolve().parent
AUTH = json.loads((ROOT / 'TARDIS_SCHEMA_DIAGNOSTIC_AUTHORITY_V0.1.json').read_text())
OUT = Path('artifacts/btc_options_vrp_tardis_schema_diag_v01')
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    sample = AUTH['sample_date']
    d = date.fromisoformat(sample)
    if d.year >= 2025:
        raise SystemExit('protected-period access blocked')

    result = {
        'lab_id': AUTH['lab_id'],
        'diagnostic_id': AUTH['diagnostic_id'],
        'classification': 'SCHEMA_ROLE_DIAGNOSTIC_COMPLETE',
        'sample_date': sample,
        'options_chain': {},
        'quotes': {},
        'failure': None,
        'safety': {
            'returns_computed': False,
            'strategy_pnl_computed': False,
            'performance_computed': False,
            'paid_subscription_used': False,
            'api_key_used': False,
            'access_2025': False,
            'access_2026': False,
            'live_trading': False,
            'exchange_mutation': False,
        },
    }

    try:
        cto, rto = 20, 90
        chain_url = f"https://datasets.tardis.dev/v1/deribit/options_chain/{d.year:04d}/{d.month:02d}/{d.day:02d}/OPTIONS.csv.gz"
        max_chain = int(AUTH['max_chain_rows'])
        pairs = {}
        chain_rows = btc_rows = relevant_rows = relevant_bbo_rows = 0
        selected = None
        chain_header = []

        for response, counter, reader in base.stream_csv(chain_url, cto, rto):
            chain_header = list(reader.fieldnames or [])
            for row in reader:
                chain_rows += 1
                sym = base.row_symbol(row)
                if sym and sym.upper().startswith('BTC-'):
                    parsed = base.parse_option_symbol(sym, d)
                    if parsed:
                        btc_rows += 1
                        expiry, strike, right, dte = parsed
                        if 25 <= dte <= 35:
                            relevant_rows += 1
                            if base.row_bbo_ok(row):
                                relevant_bbo_rows += 1
                            key = (expiry.isoformat(), strike)
                            p = pairs.setdefault(key, {'expiry': expiry.isoformat(), 'strike': strike, 'dte': dte, 'C': None, 'P': None, 'C_chain_bbo': False, 'P_chain_bbo': False})
                            if p[right] is None:
                                p[right] = sym
                            if base.row_bbo_ok(row):
                                p[f'{right}_chain_bbo'] = True
                            if p['C'] and p['P'] and selected is None:
                                selected = dict(p)
                if chain_rows >= max_chain:
                    break
            result['options_chain'] = {
                'url': chain_url,
                'header': chain_header,
                'rows_scanned': chain_rows,
                'compressed_bytes_consumed': counter.n,
                'btc_option_rows': btc_rows,
                'rows_25_35dte': relevant_rows,
                'rows_25_35dte_with_chain_bbo': relevant_bbo_rows,
                'identity_pairs_25_35dte': sum(1 for p in pairs.values() if p['C'] and p['P']),
                'pairs_with_chain_bbo_both_legs': sum(1 for p in pairs.values() if p['C'] and p['P'] and p['C_chain_bbo'] and p['P_chain_bbo']),
                'first_identity_pair': selected,
            }

        if not selected:
            result['classification'] = 'SCHEMA_ROLE_DIAGNOSTIC_INCONCLUSIVE'
            result['failure'] = 'No 25-35DTE same-strike BTC call/put identity pair within bounded chain scan.'
        else:
            quote_url = f"https://datasets.tardis.dev/v1/deribit/quotes/{d.year:04d}/{d.month:02d}/{d.day:02d}/OPTIONS.csv.gz"
            max_quotes = int(AUTH['max_quote_rows'])
            targets = {selected['C'], selected['P']}
            found = {}
            quote_rows = 0
            quote_header = []
            for response, counter, reader in base.stream_csv(quote_url, cto, rto):
                quote_header = list(reader.fieldnames or [])
                for row in reader:
                    quote_rows += 1
                    sym = base.row_symbol(row)
                    if sym in targets and base.row_bbo_ok(row) and sym not in found:
                        found[sym] = {'timestamp': base.row_timestamp(row), 'bbo_present': True}
                        if set(found) == targets:
                            break
                    if quote_rows >= max_quotes:
                        break
                result['quotes'] = {
                    'url': quote_url,
                    'header': quote_header,
                    'rows_scanned': quote_rows,
                    'compressed_bytes_consumed': counter.n,
                    'target_symbols': sorted(targets),
                    'targets_with_quote_bbo': found,
                    'all_target_legs_have_quote_bbo': set(found) == targets,
                }
            if set(found) == targets:
                result['schema_role_conclusion'] = 'CHAIN_IDENTITY_PLUS_QUOTES_BBO_SUPPORTED'
            else:
                result['schema_role_conclusion'] = 'QUOTES_BBO_NOT_PROVEN_WITHIN_BOUND'

    except Exception as exc:
        result['classification'] = 'SOURCE_ACQUISITION_TECHNICAL_FAILURE'
        result['failure'] = f'{type(exc).__name__}: {exc}'

    result['receipt_sha256'] = base.stable_sha({k: v for k, v in result.items() if k != 'receipt_sha256'})
    path = OUT / 'BTC_OPTIONS_VRP_001_TARDIS_SCHEMA_DIAGNOSTIC_RECEIPT_V0_1.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'classification': result['classification'],
        'schema_role_conclusion': result.get('schema_role_conclusion'),
        'options_chain': result['options_chain'],
        'quotes': result['quotes'],
        'failure': result['failure'],
        'receipt_sha256': result['receipt_sha256'],
    }, sort_keys=True))
    return 0 if result['classification'] in {'SCHEMA_ROLE_DIAGNOSTIC_COMPLETE', 'SCHEMA_ROLE_DIAGNOSTIC_INCONCLUSIVE'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
