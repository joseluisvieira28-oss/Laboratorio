"""Pack the executed fixed sample; contains no network or trading code."""
import gzip
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path('research/cbeth_redemption_basis_001')
REC = Path('receipts/diamond_cbeth_20261020')
rowfile = HERE / 'PREDICTOR_CENSUS_ROWS_V0.1.json'
rowfile.with_suffix('.json.gz').write_bytes(gzip.compress(rowfile.read_bytes(), mtime=0))
probe = json.loads((REC / 'result.json').read_text())
raw_paths = []
for route in probe['routes']:
    for request in route['requests']:
        if 'raw_file' in request:
            path = REC / request['raw_file']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == request['response_sha256']
            raw_paths.append(path)
with zipfile.ZipFile(REC / 'necessary_raw_packets.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path in raw_paths:
        info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 20, 0, 0, 0))
        z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
names = ['SOURCE_GATE_RECEIPT_V0.1.json', 'MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json',
         'PREDICTOR_CENSUS_RECEIPT_V0.1.json', 'PREDICTOR_CENSUS_ROWS_V0.1.json.gz',
         'STATE_CALIBRATION_RECEIPT_V0.1.json', 'DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json',
         'DISCOVERY_PREDICTOR_SAMPLE_ROWS_V0.1.json']
paths = [HERE / n for n in names] + [REC / n for n in
         ['result.json', 'result.sha256', 'pr_audit_snapshot.json', 'hyperliquid_branch_union_audit.json', 'necessary_raw_packets.zip']]
files = {p.as_posix(): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}
manifest = {'verdict': 'PREDICTOR_INSUFFICIENT_SAMPLE', 'parent_sha': '41909a1ac0f86166e7fac4a3deb9f9c9a120b35d',
            'row_set_sha256': '07ff2d7173232d11b68812def0909338f3baabf97f529417c7496d5283e92892',
            'source_days': 731, 'discovery_events': 3, 'discount_events': 2, 'premium_events': 1,
            'required_total_discount_premium': [20, 6, 6], 'convergence_executed': False,
            'market_returns_opened': False, 'pnl_opened': False, 'protected_2026_outcomes_opened': False,
            'files': files}
data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
(HERE / 'EVIDENCE_MANIFEST.json').write_bytes(data)
(HERE / 'EVIDENCE_MANIFEST.sha256').write_text(hashlib.sha256(data).hexdigest() + '\n')
print(json.dumps({'packed_files': len(files), 'manifest_sha256': hashlib.sha256(data).hexdigest(),
                  'compressed_rows_bytes': rowfile.with_suffix('.json.gz').stat().st_size}))
