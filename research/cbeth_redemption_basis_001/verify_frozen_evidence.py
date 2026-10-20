"""Offline integrity and unchanged-parent replay; never performs a network call."""
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path('research/cbeth_redemption_basis_001')


def load(name):
    return json.loads((HERE / name).read_text())


def verify():
    manifest = load('EVIDENCE_MANIFEST.json')
    for name, meta in manifest['files'].items():
        data = Path(name).read_bytes()
        assert len(data) == meta['bytes'] and hashlib.sha256(data).hexdigest() == meta['sha256'], 'evidence file changed: ' + name
    parent_blobs = {
        'SOURCE_GATE_FREEZE_V0.1.md': 'e1aa08cff5dce6c21c80617a22167fb66bf2703e',
        'PRE_OUTCOME_PREDICTOR_DESIGN_FREEZE_V0.1.md': '00864da8c28785bfdf64780226576017da160929',
        'MECHANISM_SAMPLE_BOUNDARY_ADDENDUM_V0.1A.md': 'c70f4c173af46d688288e1effa67ed2e3fd22778',
        'MECHANISM_DISCOVERY_STATISTICAL_GATE_FREEZE_V0.1B.md': '8c9325176595bbada078de7fa266242fb399cd5f',
        'MULTICALL_TRANSPORT_EQUIVALENCE_FREEZE_V0.1C.md': '31f261830fec04e723ace4722629a9c880c5e859',
        'cbeth_source_probe_v01.mjs': '0030fe3a9f64017d3d5d29c9054d18156f5ef194',
        'cbeth_predictor_census_v01.mjs': '35d4d2b810705265affb8c6a4b8081895928b415',
        'cbeth_state_calibration_v01.py': '17be229d59f3eb041fdab3f7e0022f852e83791a',
        'cbeth_discovery_predictor_sample_v01.py': '727d2aa70dc4c75604b3e197dda59167a326dfa4',
        'cbeth_mechanism_discovery_v01.py': '41e23567fcdb3da94f5a9af88f752c9766b1b4ed',
        'cbeth_multicall_equivalence_v01c.mjs': 'e517948de4939d6fd512dab281a5ce2154a19235',
    }
    for name, expected in parent_blobs.items():
        data = (HERE / name).read_bytes().replace(b'\r\n', b'\n')
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert actual == expected, 'parent protocol/code changed: ' + name
    source = load('SOURCE_GATE_RECEIPT_V0.1.json')
    assert source['classification'] == 'SOURCE_PASS'
    fixed = [16000000, 18000000, 20000000, 22000000, 24000000]
    assert source['fixed_historical_sentinels'] == fixed
    anchors = {r['number']: r for r in source['protocol_anchor']}
    assert set(anchors) == set(fixed + [source['finalized_block']['number']])
    assert all(int(r['exchange_rate_wei_per_cbeth']) > 0 and r['block_pinned_by_hash'] for r in anchors.values())
    eq = load('MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json')
    assert eq['classification'] == 'MULTICALL_TRANSPORT_EQUIVALENCE_PASS'
    assert [b['block_number'] for b in eq['blocks']] == [16000000, 20000000, 24000000]
    assert all(b['block_hash'] == anchors[b['block_number']]['hash'] for b in eq['blocks'])
    assert all(c['multicall_success'] and c['direct_return_data'].lower() == c['multicall_return_data'].lower() for b in eq['blocks'] for c in b['comparisons'])
    rec = load('PREDICTOR_CENSUS_RECEIPT_V0.1.json')
    rowfile = HERE / 'PREDICTOR_CENSUS_ROWS_V0.1.json'
    if not rowfile.exists():
        rowfile.write_bytes(gzip.decompress(rowfile.with_suffix('.json.gz').read_bytes()))
    obj = json.loads(rowfile.read_text())
    rows = obj['rows']
    digest = hashlib.sha256(json.dumps(rows, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert digest == rec['row_set_sha256'] == obj['row_set_sha256'], 'actual row digest mismatch'
    days = [(date(2023, 1, 1) + timedelta(days=i)).isoformat() for i in range(731)]
    assert [r['utc_day'] for r in rows] == days
    assert rec['classification'] == 'PREDICTOR_CENSUS_PASS'
    assert rec['valid_day_count'] == 731 and rec['invalid_day_count'] == 0
    assert rec['selected_pool']['pool'].lower() == eq['selected_pool']['pool'].lower()
    assert all(r['valid'] and r['block_pinned_by_hash'] and int(r['liquidity']) > 0 for r in rows)
    for flag in ['future_mechanism_outcomes_opened', 'market_returns_opened', 'oos_2025_opened', 'protected_2026_opened', 'pnl_opened', 'mutation']:
        assert rec[flag] is False
    temp_root = (Path.cwd() / 'artifacts/replay_tests').resolve()
    assert Path.cwd().resolve() in temp_root.parents
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
        dest = Path(tmp) / HERE
        dest.mkdir(parents=True)
        for name in ['PREDICTOR_CENSUS_RECEIPT_V0.1.json', 'PREDICTOR_CENSUS_ROWS_V0.1.json']:
            (dest / name).write_bytes((HERE / name).read_bytes())
        scripts = [('cbeth_state_calibration_v01.py', 'STATE_CALIBRATION_RECEIPT_V0.1.json'),
                   ('cbeth_discovery_predictor_sample_v01.py', 'DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json')]
        for script, result in scripts:
            subprocess.run([sys.executable, str((HERE / script).resolve())], cwd=tmp, check=True, capture_output=True)
            assert json.loads((dest / result).read_text()) == load(result), 'parent replay mismatch: ' + result
        sample = load('DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json')
        verdict = sample['classification']
        if verdict == 'PREDICTOR_SAMPLE_PASS':
            subprocess.run([sys.executable, str((HERE / 'cbeth_mechanism_discovery_v01.py').resolve())], cwd=tmp, check=True, capture_output=True)
            result = 'MECHANISM_DISCOVERY_RESULT_V0.1.json'
            assert json.loads((dest / result).read_text()) == load(result)
            verdict = load(result)['classification']
        else:
            assert verdict == 'PREDICTOR_INSUFFICIENT_SAMPLE'
            assert not (HERE / 'MECHANISM_DISCOVERY_RESULT_V0.1.json').exists(), 'outcomes must remain closed'
    print(json.dumps({'integrity': 'PASS', 'unchanged_parent_replay': 'PASS', 'verdict': verdict, 'row_sha256': digest, 'trading_authority': False}))


if __name__ == '__main__':
    verify()
