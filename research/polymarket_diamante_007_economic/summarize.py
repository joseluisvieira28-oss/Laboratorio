"""Build an economic decision from the two untouched validation days."""
import gzip,json
from collections import defaultdict
from pathlib import Path
doc=json.loads(Path('economic.json').read_text())
loc={(x['rule'],x['horizon'],x['capital'],x['stress'],x['date']):x for x in doc['aggregate']}
days=('2026-11-08','2026-11-09')
hypotheses=('maker','hybrid','oracle','inventory','micro')
checks=[]; results=[]
for rule in hypotheses:
    comparator='maker' if rule in ('inventory','micro') else 'control'
    for t in (60,120,180):
        for c in (100,250,500,1000,5000):
            four=[]
            for stress in (False,True):
                for d in days:
                    k=(t,c,stress,d)
                    r=loc[(rule,*k)]; control=loc[(comparator,*k)]
                    four.append({'date':d,'stress':stress,'net':r['net'],'control':control['net'],
                                 'concentration':r['positive_concentration'],
                                 'ambiguous_gaps':r['gap_with_active_order'],
                                 'passes':r['net']>0 and r['net']>control['net']
                                 and (r['positive_concentration'] or 0)<=.5
                                 and r['gap_with_active_order']==0})
            checks.append(dict(rule=rule,horizon=t,capital=c,outcomes=four,survives=all(x['passes'] for x in four)))
            if t==120 and c==500:
                base=[loc[(rule,t,c,False,d)] for d in days]
                row={'rule':rule,'capital':c,'horizon':t,'adversarial':[x['net'] for x in four if x['stress']],
                     'net_by_day':[r['net'] for r in base],'drawdown_max_daily':max(x['drawdown'] for x in base)}
                for k in ('eligible','orders','fills','complete_pair','residual','gross','costs','net','spent','gap_with_active_order','unhedged_first_markets'):
                    row[k]=sum(x[k] for x in base)
                row['worst']=min(x['worst'] for x in base)
                results.append(row)
with gzip.open('ledger.jsonl.gz') as f:
    count=0
    for line in f:
        item=json.loads(line);count+=1
        assert abs(item['gross']-item['costs']-item['net'])<1e-8
        assert item['residual']>=0 and item['spent']>=0
        assert item['spent']<=item['capital']+1e-8
        assert all(a[2]>0 for a in item['fills'])
Path('decision.json').write_text(json.dumps(dict(ledger_rows=count,oracle_calibration_n=doc['oracle_calibration_n'],
    oracle_features=doc['oracle_features'],validation_500_120=results,
    candidates=[x for x in checks if x['survives']],comparisons=checks),indent=2)+'\n')
for x in results: print(x)
print('survivors',len([x for x in checks if x['survives']]),'oracle calibration',doc['oracle_calibration_n'])
