from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'source_gate_evidence' / 'evm_candidate_scan_v01' / 'UCF_EVM_CANDIDATE_MANIFEST_V01.json'
OUT = HERE / 'source_gate_evidence' / 'evm_candidate_scan_v01' / 'UCF_ALLOCATION_PRIORITY_RECEIPT_V01.json'


def main() -> None:
    rows = json.loads(SRC.read_text())
    token_sections = defaultdict(Counter)
    token_chain = {}
    for r in rows:
        token_chain[r['symbol']] = r['chain']
        sections = r.get('sections') or ['<UNKNOWN>']
        for s in sections:
            token_sections[r['symbol']][s] += 1

    result = {
        'lab_id': 'UNLOCK-CLAIM-FLOW-001',
        'mve_id': 'UCF-VESTING-OUTFLOW-24H-001',
        'mode': 'SOURCE_ONLY_ALLOCATION_PRIORITY_SCAN',
        'tokens': {},
        'guards': {
            'claim_flow_accessed': False,
            'market_prices_accessed': False,
            'returns_computed': False,
            'pnl_computed': False,
            'year_2025_opened': False,
            'year_2026_opened': False,
        },
    }
    by_token = Counter(r['symbol'] for r in rows)
    for symbol, count in sorted(by_token.items(), key=lambda kv: (-kv[1], kv[0])):
        result['tokens'][symbol] = {
            'chain': token_chain[symbol],
            'event_count': count,
            'section_event_memberships': dict(token_sections[symbol].most_common()),
        }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
