"""Descriptive audit of already-open published ledgers; never a strategy backtest."""
import base64, csv, gzip, hashlib, io, json, pathlib, statistics
from datetime import datetime
ROOT=pathlib.Path(__file__).resolve().parent
def dt(x): return datetime.fromisoformat(x.removesuffix('Z'))
def summarize(rows):
 rows=sorted(rows,key=lambda r:r['entry'])
 closed=[r for r in rows if not r['open']]
 returns=[r['ret'] for r in closed]
 durations=[(r['exit']-r['entry']).total_seconds()/3600 for r in closed]
 wins=[r for r in closed if r['ret']>0]
 losses=[r for r in closed if r['ret']<0]
 streak=longest=0
 for r in closed:
  streak=streak+1 if r['ret']<0 else 0; longest=max(longest,streak)
 peak=equity=1.; dd=0.
 for r in closed:
  equity*=1+.95*r['ret']/100; peak=max(peak,equity); dd=min(dd,equity/peak-1)
 span=(max(r['exit'] for r in closed)-min(r['entry'] for r in closed)).total_seconds()/86400/365.25
 def count(threshold):
  n=sum(r['ret']>=threshold for r in closed)
  return dict(count=n,total=len(closed),fraction=n/len(closed),fraction_of_wins=n/len(wins),per_observed_year=n/span)
 return dict(closed=len(closed),open_excluded=len(rows)-len(closed),wins=len(wins),losses=len(losses),flat=len(closed)-len(wins)-len(losses),
  win_fraction=len(wins)/len(closed),observed_years=span,closed_per_year=len(closed)/span,
  fee_only_target_40_at_1x=count(40),fee_only_target_40_at_2x=count(20),
  fee_only_target_40_at_loss_budget_ceiling=count(16.76),
  average_win_pct=statistics.mean(r['ret'] for r in wins),average_loss_pct=statistics.mean(r['ret'] for r in losses),
  median_loss_pct=statistics.median(r['ret'] for r in losses),worst_loss_pct=min(returns),
  longest_loss_streak=longest,median_hold_hours=statistics.median(durations),max_hold_hours=max(durations),
  median_win_hold_hours=statistics.median((r['exit']-r['entry']).total_seconds()/3600 for r in wins),
  median_loss_hold_hours=statistics.median((r['exit']-r['entry']).total_seconds()/3600 for r in losses),
  same_timestamp_reentries=sum(a['exit']==b['entry'] for a,b in zip(closed,closed[1:])),
  overlapping_pairs_within_tf=sum(a['entry']<b['exit'] and b['entry']<a['exit'] for i,a in enumerate(closed) for b in closed[i+1:]),
  illustrative_95pct_allocation_closed_dd=dd,
  yearly={str(y):dict(closed=sum(r['exit'].year==y for r in closed),wins=sum(r['exit'].year==y and r['ret']>0 for r in closed),
   target_40_1x=sum(r['exit'].year==y and r['ret']>=40 for r in closed),target_40_2x=sum(r['exit'].year==y and r['ret']>=20 for r in closed)) for y in sorted({r['exit'].year for r in closed})})
def compute():
 manifest=json.loads((ROOT/'source_manifest.json').read_text())
 for source in manifest:
  raw=(ROOT/source['local_path']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=source['sha256']: raise ValueError('Source hash mismatch: '+source['local_path'])
 groups={}; hashes={}
 for source in manifest:
  if not source['path'].endswith('.b64'): continue
  raw=gzip.decompress(base64.b64decode((ROOT/source['local_path']).read_bytes()))
  hashes[source['path']]=hashlib.sha256(raw).hexdigest()
  for r in csv.DictReader(io.StringIO(raw.decode())):
   tf=r.get('timeframe','1h')
   is_open=r.get('open',r.get('is_open')).lower()=='true'
   groups.setdefault(tf,[]).append(dict(entry=dt(r['entry_dt']),exit=None if is_open else dt(r['exit_dt']),ret=float(r.get('ret',r.get('trade_return_pct'))),open=is_open))
 overlaps={}
 for a in sorted(groups):
  for b in sorted(groups):
   if a>=b: continue
   aa=[r for r in groups[a] if not r['open']]; bb=[r for r in groups[b] if not r['open']]
   overlaps[a+'_'+b]=dict(overlapping_interval_pairs=sum(x['entry']<y['exit'] and y['entry']<x['exit'] for x in aa for y in bb),identical_exit_timestamps=sum(x['exit']==y['exit'] for x in aa for y in bb),timezone_caveat='Normalized 1h has Z; other exports omit timezone. Cross-TF comparisons conditional on same clock basis.')
 return dict(classification='TARGET_NOT_ESTABLISHED_COST_EXECUTION_AND_INDEPENDENT_SAMPLE_GAPS',
  scope='Published retrospective seed only. No new market outcomes; no parameter selection; leveraged counts are arithmetic counterfactuals.',
  costs='Seed returns include reported commission only. 1h reported denominator reconciles to entry value including 0.1% entry fee, not exact notional. Leveraged counts use reported return basis and are illustrative. Funding, executable slippage, margin tiers, min-notional and liquidation are not verified; target counts are not verified all-cost wins.',
  leverage=dict(fee_only_typical_loss_pct=4.19,algebraic_typical_loss_ceiling=10/4.19,required_return_pct_at_ceiling=40/(10/4.19),warning='Not a recommended leverage; ceiling assumes typical loss, ignores gaps and missing costs. No guarantee of -10% maximum loss.'),
  decoded_ledger_sha256=hashes,seed={k:summarize(v) for k,v in sorted(groups.items())},cross_timeframe_overlap=overlaps,
  qualified_all_cost_margin_target_count=None,qualified_independent_target_frequency=None)
if __name__=='__main__':
 result=compute()
 (ROOT/'descriptive_metrics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result['seed'],indent=2))
