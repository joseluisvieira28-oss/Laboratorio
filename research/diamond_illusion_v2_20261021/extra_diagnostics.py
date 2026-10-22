from pathlib import Path
import json,csv,statistics,numpy as np
P=Path(__file__).parent;R=P/'results';T=list(csv.DictReader((R/'all_412_trades.csv').open()));allrows=[]
for fam in ['ETF','OPTIONS']:
 tt=[r for r in T if r['family']==fam];w=np.array([float(r['weight']) for r in tt]);gross=np.array([float(r['gross_simple_bps']) for r in tt]);ratio=np.array([float(r['exit_px'])/float(r['entry_px']) for r in tt]);v=gross-w*(8+8*ratio);n=len(v)
 for b in [1,4,8]:
  rng=np.random.default_rng(20261021);starts=rng.integers(0,n,size=(20000,(n+b-1)//b));ix=((starts[:,:,None]+np.arange(b))%n).reshape(20000,-1)[:,:n];means=v[ix].mean(axis=1);allrows.append({'family':fam,'convention':'cash_simple_bps','fee_bps_per_side':8,'financing_and_extra_friction':'unknown; set zero for this diagnostic','block':b,'mean':float(v.mean()),'ci95':np.quantile(means,[.025,.975]).tolist(),'not_true_edge_probability':True})
(R/'cash_bootstrap.json').write_text(json.dumps(allrows,indent=2))
# Rate history only. This secondary read uses a cached parsed export already byte-verified in prepare_inputs.
ROOT=P.parents[1]
if not (ROOT/'work/final_mexc_private/official_workbooks.json').exists():
 print('Private fee-history replay unavailable; retain published aggregate evidence.');raise SystemExit(0)
wb=json.loads((ROOT/'work/final_mexc_private/official_workbooks.json').read_text(encoding='utf-8-sig'));a={}
for r in wb['Trade History']['sheets']['Sheet1'][1:]:
 if r[2]!='BTCUSDT':continue
 rate=round(float(r[9])/float(r[7])*10000,6);key=(r[1][:7],r[11],rate);a[key]=a.get(key,0)+1
with (R/'observed_fee_history.csv').open('w',newline='') as f:
 q=csv.writer(f);q.writerow(['local_month_UTCplus2','role','charged_bps_per_side','fills','not_all_strategy_attributed'])
 for (month,role,rate),count in sorted(a.items()):q.writerow([month,role,rate,count,True])
print('CASH_CI',allrows)
print('BREAK_EVEN',[(x['family'],x['break_even_all_cost_full_notional_bps'],x['break_even_equal_fee_cash_roundtrip_bps']) for x in json.loads((R/'metrics.json').read_text()) if x['scenario']=='FROZEN_BASE10'])
print('MAKER_SCENARIOS',[(x['family'],x['scenario'],x['mean']) for x in json.loads((R/'metrics.json').read_text()) if x['scenario'].endswith('EXTRA0')])
