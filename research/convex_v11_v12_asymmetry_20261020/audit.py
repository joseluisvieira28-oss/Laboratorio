"""Fixed-ledger diagnostic; no market requests, strategy fitting or OOS claims."""
from pathlib import Path
import csv,json,hashlib,math
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lanes=[('V11','SOL','4h',11831078628),('V11','BNB','30m',11830584859),('V11','ETH','1h',11831023679),('V12','BNB','5m',11832357900),('V12','SOL','30m',11831078628),('V12','BNB','15m',11830584859),('V12','DOGE','4h',11831058673)]
master4=json.loads((SRC/'4tf/COMMON_3YEAR_MASTER.json').read_text())
master5=json.loads((SRC/'5m/NATIVE_5M_16_CASES.json').read_text())
metadata=[]
for f in SRC.glob('artifacts_*.json'):metadata+=json.loads(f.read_text())
checks=[]
for a in metadata:
 p=SRC/(str(a['id'])+'.zip')
 if p.exists():
  assert 'sha256:'+sha(p)==a['digest'],a['id']
  checks.append({'artifact_id':a['id'],'sha256':sha(p),'github_digest_match':True})
rows=[]
for group,sym,tf,aid in lanes:
 p=SRC/str(aid)/'RESULT.json';d=json.loads(p.read_text())
 expected=(master5['source_receipts'][sym+'USDT']['sha256'] if tf=='5m' else master4['verified_source_receipts'][sym+'USDT']['result_sha256'])
 assert sha(p)==expected
 for cost in ['BASE','STRESS']:
  m=d['models'][cost] if tf=='5m' else d['model'][tf+'_'+cost]
  ledger=p.parent/((cost if tf=='5m' else tf+'_'+cost)+'_TRADES.csv')
  trades=list(csv.DictReader(ledger.open())); n=len(trades)
  a=np.array([float(t['net_pnl']) for t in trades]); risks=np.array([.04*float(t['entry_price'])*float(t['qty']) for t in trades]); r=a/risks
  for t in trades:
   assert math.isclose(float(t['net_pnl']),float(t['price_pnl'])-float(t['entry_fees'])-float(t['exit_fee'])+float(t['funding']),abs_tol=1e-8)
  assert n==m['closed_trades'] and sum(a>0)==m['wins']
  pf=sum(a[a>0])/-sum(a[a<0]);assert math.isclose(pf,m['profit_factor'],abs_tol=1e-9)
  years={str(y):sum(float(t['net_pnl']) for t in trades if t['exit_year']==str(y)) for y in [2023,2024,2025]}
  assert all(math.isclose(years[y],m['annual_closed_trade_pnl_usdt'].get(y,0),abs_tol=1e-8) for y in years)
  top=sorted(a,reverse=True); deleted={str(k):float(sum(a)-sum(top[:k])) for k in [1,2,3]}
  assert math.isclose(deleted['3'],m['removed_3_biggest_net_pnl_sum_usdt'],abs_tol=1e-8)
  quarters=np.zeros((12,2));hold=[]
  for t,rr in zip(trades,r):
   dt=datetime.fromtimestamp(int(t['close_t'])/1000,timezone.utc);qi=(dt.year-2023)*4+(dt.month-1)//3
   assert 0<=qi<12
   quarters[qi]+=[rr,1];hold.append((int(t['close_t'])-int(t['open_t']))/86400000)
  rng=np.random.default_rng(20261020);idx=rng.integers(0,12,size=(20000,12));sums=quarters[idx].sum(axis=1);valid=sums[:,1]>0;means=sums[valid,0]/sums[valid,1]
  ci=np.quantile(means,[.025,.975]);winr=float(np.mean(r[r>0]));lossr=float(-np.mean(r[r<0]));streak=worst=0
  for x in a:streak=streak+1 if x<0 else 0;worst=max(worst,streak)
  fees=sum(float(t['entry_fees'])+float(t['exit_fee']) for t in trades);fund=sum(float(t['funding']) for t in trades);price=sum(float(t['price_pnl']) for t in trades)
  row={'group':group,'symbol':sym,'tf':tf,'cost':cost,'n':n,'win_pct':float(np.mean(a>0)*100),'mean_win_R':winr,'mean_loss_R':lossr,'payoff_R':winr/lossr,'mean_R':float(np.mean(r)),'median_R':float(np.median(r)),'mean_USDT':float(np.mean(a)),'closed_net_USDT':float(sum(a)),'PF':pf,'terminal_return_pct':m['marked_return_pct'],'DD_model_pct':m['max_5m_low_stress_dd_pct'],'annual_closed_USDT':years,'static_remove_winners_USDT':deleted,'top3_share_of_positive_pnl_pct':100*sum(top[:3])/sum(a[a>0]),'top3_share_of_total_net_pct':100*sum(top[:3])/sum(a),'quarter_bootstrap_mean_R_95pct':[float(x) for x in ci],'bootstrap_invalid_empty_samples':int(sum(~valid)),'max_loss_streak':worst,'median_hold_days':float(np.median(hold)),'max_hold_days':max(hold),'closed_price_pnl_after_slip':price,'closed_fees_USDT':fees,'closed_funding_USDT':fund,'model_all_fees_USDT':m['fees_usdt'],'model_all_funding_USDT':m['funding_usdt'],'end_open_position':m['end_position_open'],'ledger_sha256':sha(ledger),'result_sha256':sha(p),'run':38435206427 if tf=='5m' else 38432883246,'artifact_id':aid}
  assert math.isclose(price-fees+fund,sum(a),abs_tol=1e-7)
  rows.append(row)
result={'status':'HISTORICAL_ASYMMETRY_PRESENT_INDEPENDENT_NET_EDGE_UNPROVEN','scope':'seven unchanged V11/V12 lanes, 2023-2025','oos':False,'protected_2026_opened':False,'trade_authority':'NONE','risk_unit':'R = 4% of entry_price times qty; net R includes modeled fees/slippage/funding; realized loss can exceed 1R','bootstrap':'quarter of exit, 12 calendar clusters, 20000 resamples seed20261020; descriptive selected-history uncertainty only','source_archive_checks':checks,'rows':rows}
(ROOT/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
for x in rows:
 if x['cost']=='BASE':print(x['group'],x['symbol'],x['tf'],'N',x['n'],'win',round(x['win_pct'],2),'payoff',round(x['payoff_R'],2),'E_R',round(x['mean_R'],3),'CI',[round(v,3) for v in x['quarter_bootstrap_mean_R_95pct']],'top1/2/3',[round(v,2) for v in x['static_remove_winners_USDT'].values()],'years',[round(v,2) for v in x['annual_closed_USDT'].values()])
print('Reconciled',len(rows),'ledgers; archive digest checks',len(checks))
