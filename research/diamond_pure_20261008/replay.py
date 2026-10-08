"""Offline integrity and numerical replay; never opens new market data."""
import datetime as dt, gzip, hashlib, json, pathlib, urllib.parse, zipfile
import probe
ROOT=pathlib.Path(__file__).resolve().parent
p=ROOT/'evidence/run_001'
if not p.exists():
 with zipfile.ZipFile(ROOT/'PUBLIC_SOURCE_EVIDENCE.zip') as z:
  assert all(n.startswith('evidence/run_001/') and '..' not in pathlib.PurePosixPath(n).parts for n in z.namelist())
  z.extractall(ROOT)
manifest=[json.loads(s) for s in (p/'manifest.jsonl').read_text().splitlines()]
freeze=dt.datetime.fromisoformat('2026-10-08T15:24:00+00:00')
by_name={}
for r in manifest:
 assert 'error' not in r,r
 assert dt.datetime.fromisoformat(r['request_utc'])>freeze
 raw=gzip.decompress((p/r['raw_file']).read_bytes())
 assert hashlib.sha256(raw).hexdigest()==r['raw_sha256']
 obj=json.loads(raw); assert 'error' not in obj
 u=urllib.parse.urlsplit(r['url']); assert u.netloc=='www.deribit.com'
 assert u.path.startswith('/api/v2/public/') and u.path.rsplit('/',1)[1] in probe.ALLOWED
 if 'get_order_book?' in r['url']:
  name=urllib.parse.parse_qs(u.query)['instrument_name'][0]
  by_name.setdefault(name,[]).append({'data':obj['result'],'received_ms':int(dt.datetime.fromisoformat(r['receive_utc']).timestamp()*1000)})
groups=json.loads((p/'selected_geometry.json').read_text()); rows=json.loads((p/'quote_diagnostics.json').read_text())
for row in rows:
 g=next(g for g in groups if g['instruments']==row['instruments'])
 books=[by_name[n][row['snapshot']-1] for n in row['instruments']]
 fresh=probe.assess(g,books)
 for key in ('source_status','debit_usdc','entry_fees_usdc','entry_fee_adjusted_upper_bound_usdc','initial_capital_indication_usdc'):
  assert fresh.get(key)==row.get(key),(key,fresh.get(key),row.get(key))
 assert not row['atomic_execution_proven'] and row['all_cost_net_usdc'] is None
 assert row['gross_cashflow_upper_bound_usdc']<0
summary=json.loads((p/'summary.json').read_text())
assert summary['valid_leg_snapshots']==8 and summary['positive_entry_fee_upper_bounds']==0
assert summary['active_btc_eth_box_count']==0 and summary['trades_executed']==0
result={'status':'PASS','raw_receipts_verified':len(manifest),'quote_rows_reproduced':len(rows),'all_receipts_after_freeze':True,'future_outcomes_opened':False,'network_used':False}
probe.dump(ROOT/'OFFLINE_REPLAY_RECEIPT.json',result); print(json.dumps(result,indent=2))
