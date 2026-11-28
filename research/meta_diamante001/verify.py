"""Compare regenerated futures CSV byte digests and independently reconcile accounting."""
import json,hashlib
import pandas as pd,numpy as np
from experiment import OUT
source=json.loads((OUT/'prior_asymmetry.json').read_text())
res=[]
for row in source['rows']:
    sym,tf,cost=(row[k] for k in ['symbol','tf','cost'])
    path=OUT/'legacy'/(sym+'5m' if tf=='5m' else sym)/((cost if tf=='5m' else tf+'_'+cost)+'_TRADES.csv')
    t=pd.read_csv(path)
    np.testing.assert_allclose(t.net_pnl,t.price_pnl-t.entry_fees-t.exit_fee+t.funding)
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    risk=.04*t.entry_price*t.qty; r=t.net_pnl/risk
    res.append([sym,tf,cost,len(t),100*(r>0).mean(),r[r>0].mean()/-r[r<0].mean(),t.net_pnl.sum()-t.net_pnl.nlargest(3).sum(),h,row['ledger_sha256'],h==row['ledger_sha256']])
d=pd.DataFrame(res,columns='asset tf cost n win_pct payoff_R net_ex_top3 regenerated_hash original_hash exact_match'.split())
d.to_csv(OUT/'legacy_match.csv',index=False)
m=pd.read_csv(OUT/'metrics.csv');np.testing.assert_allclose(m.net,m.gross-m.fees-m.friction,atol=1e-8)
print(d.to_string(index=False,columns=['asset','tf','cost','n','win_pct','payoff_R','net_ex_top3','exact_match']))
