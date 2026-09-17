#!/usr/bin/env python3
"""Corrected outcome-blind Tardis source-feasibility probe V0.2.

Only the free-sample calendar differs from V0.1, per the recorded erratum.
No returns, PnL, expectancy, PF, drawdown, 2025 or 2026 access.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import tardis_source_probe_v01 as base

ROOT = Path(__file__).resolve().parent
AUTH_PATH = ROOT / 'TARDIS_SOURCE_PROBE_AUTHORITY_V0.2.json'
OUT = Path('artifacts/btc_options_vrp_tardis_source_probe_v02')
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    auth = json.loads(AUTH_PATH.read_text())
    receipt = {
        'lab_id': auth['lab_id'],
        'probe_id': auth['probe_id'],
        'authority_sha256': hashlib.sha256(AUTH_PATH.read_bytes()).hexdigest(),
        'classification': None,
        'dates': [],
        'failure': None,
        'safety': dict(base.SAFETY),
        'parent_v01_run': auth['parent_v01_run'],
        'schema_diagnostic_run': auth['schema_diagnostic_run'],
    }
    try:
        assert auth['status'] == 'FROZEN_SOURCE_ONLY_OUTCOME_BLIND'
        assert auth['sample_dates'] == ['2021-01-01','2022-01-01','2023-01-01','2024-01-01']
        assert all(int(x[:4]) < 2025 for x in auth['sample_dates'])
        assert all(v is False for k, v in auth['safety'].items() if k.endswith('_authorized'))
        for sample in auth['sample_dates']:
            chain = base.probe_chain(auth, sample)
            quotes = base.probe_quotes(auth, sample, chain['selected_pair'])
            receipt['dates'].append({'date': sample, 'options_chain': chain, 'quotes': quotes})
        receipt['classification'] = 'PAID_SOURCE_ROUTE_FEASIBLE'
    except base.RouteInsufficient as exc:
        receipt['classification'] = 'SOURCE_ROUTE_SCHEMA_INSUFFICIENT'
        receipt['failure'] = f'{type(exc).__name__}: {exc}'
    except base.AcquisitionFailure as exc:
        receipt['classification'] = 'SOURCE_ACQUISITION_TECHNICAL_FAILURE'
        receipt['failure'] = f'{type(exc).__name__}: {exc}'
    except Exception as exc:
        receipt['classification'] = 'PROVENANCE_FAILURE'
        receipt['failure'] = f'{type(exc).__name__}: {exc}'

    receipt['receipt_sha256'] = base.stable_sha({k: v for k, v in receipt.items() if k != 'receipt_sha256'})
    path = OUT / 'BTC_OPTIONS_VRP_001_TARDIS_SOURCE_PROBE_RECEIPT_V0_2.json'
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'classification': receipt['classification'],
        'dates_completed': len(receipt['dates']),
        'date_summaries': [
            {
                'date': x['date'],
                'pair': x['options_chain']['selected_pair'],
                'chain_rows_scanned': x['options_chain']['rows_scanned'],
                'quote_rows_scanned': x['quotes']['rows_scanned'],
                'quote_bbo_legs': len(x['quotes']['targets_with_nonempty_bbo']),
            }
            for x in receipt['dates']
        ],
        'failure': receipt['failure'],
        'receipt_sha256': receipt['receipt_sha256'],
        'safety': receipt['safety'],
    }, sort_keys=True))
    return 0 if receipt['classification'] in {'PAID_SOURCE_ROUTE_FEASIBLE','SOURCE_ROUTE_SCHEMA_INSUFFICIENT'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
