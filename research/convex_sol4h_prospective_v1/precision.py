"""Planning from already-seen original closed ledgers, not new OOS evidence."""
import argparse,csv,json,math
from pathlib import Path
from statistics import NormalDist,mean,stdev

def calculate(path,symbol,tf):
    trades=list(csv.DictReader(Path(path).open()))
    r=[float(t['net_pnl'])/(.04*float(t['entry_price'])*float(t['qty'])) for t in trades]
    sd=stdev(r);mu=mean(r);freq=len(r)/3;z=NormalDist().inv_cdf(.975);power=NormalDist().inv_cdf(.8)
    result=dict(symbol=symbol,tf=tf,n=len(r),historical_mean_R=mu,historical_sd_R=sd,frequency_per_year=freq,precision=[],power=[])
    for h in [.25,.5,1]:
        n=math.ceil((z*sd/h)**2)
        result['precision'].append(dict(halfwidth_R=h,n_iid=n,years_historical_rate=n/freq,n_design_effect_2=2*n,years_design_effect_2=2*n/freq))
    for true_mu,h0 in [(mu,0),(mu/2,0),(mu,.25),(.25,0)]:
        n=math.ceil(((z+power)*sd/(true_mu-h0))**2)
        result['power'].append(dict(true_mu_R=true_mu,null_mu_R=h0,power=.8,alpha_two_sided=.05,n_iid=n,years_historical_rate=n/freq))
    result['expected_n_365d']=freq
    result['halfwidth_95_R_at_historical_one_year_n']=z*sd/math.sqrt(freq)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--sol-ledger',required=True);p.add_argument('--bnb-ledger',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    rows=[calculate(a.sol_ledger,'SOL','4h'),calculate(a.bnb_ledger,'BNB','30m')]
    d=dict(status='FEASIBILITY_FAIL_FOR_ONE_YEAR_CONFIRMATION',warning='IID Gaussian planning approximation using selected history; NOT prospective proof or rigorous sample guarantee; dependence/tails may increase required sample',precision_target_R=.25,economic_materiality_equity_pct_per_year_SOL_approx=.25*.008*(44/3)*100,rows=rows)
    Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(d['status'])
if __name__=='__main__':main()
