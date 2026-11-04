"""Audit original bytes, preserve original report, replay without network access."""
import gzip, json
from collections import Counter
from pathlib import Path
from shadow import Replay, sha
p=Path(__file__).parent/'pilot-20261104'
if not (p/'raw.jsonl').exists(): (p/'raw.jsonl').write_bytes(gzip.decompress((p/'raw.jsonl.gz').read_bytes()))
original=json.loads((p/'report.json').read_text())
assert sha(p/'raw.jsonl')==original['raw_sha256'], 'RAW_HASH_MISMATCH'
rows=[json.loads(x) for x in (p/'raw.jsonl').read_text().splitlines()]
contract=json.loads(next(x['raw'] for x in rows if x['kind']=='contract'))['data']['contractSize']
r=Replay(contract)
for row in rows: r.feed(row)
report=r.finish(); report['errors_summary']=dict(Counter(report.pop('errors')))
report.update(raw_sha256=sha(p/'raw.jsonl'),protocol_sha256=sha(Path(__file__).parent/'PROTOCOL.md'),
              rows=len(rows),start_utc_ms=rows[0]['utc_ms'],end_utc_ms=rows[-1]['utc_ms'],
              observed_span_seconds=(rows[-1]['mono_ns']-rows[0]['mono_ns'])/1e9,
              provenance='Corrected envelope ts parser; same original receive order; no new collection; original report retained')
(p/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
with (p/'raw.jsonl.gz').open('wb') as f:
    f.write(gzip.compress((p/'raw.jsonl').read_bytes(),mtime=0))
print(json.dumps(report,indent=2))
