#!/usr/bin/env python3
"""Post-hoc diagnostics: reused test data, NOT a new independent validation."""
import json
import pandas as pd
import study
from sklearn.metrics import average_precision_score

DIRECT=['holder_count','top10_holder_pct','dev_remaining_pct','rat_position_pct']

def main():
    df,source=study.load()
    (tr,va,te),cuts=study.split(df)
    base=study.choose(tr,study.BASE)
    direct=study.choose(tr,DIRECT)
    structural=study.choose(tr,study.STRUCT)
    result={'sha256':source['sha256'],'WARNING':'POST-HOC, REUSED TEST; NOT NEW INDEPENDENT EVIDENCE',
            'direct_fields':direct}
    preds={name:study.scores(tr,te,cols) for name,cols in {
        'baseline':base,'baseline_direct':base+direct,
        'baseline_full_structure':base+structural}.items()}
    result['models']={name:study.measures(te.target,p) for name,p in preds.items()}
    result['days']={}
    for day,part in te.groupby(te.captured_at.dt.strftime('%Y-%m-%d')):
        indices=te.index.get_indexer(part.index)
        y=part.target.to_numpy()
        result['days'][day]={'n':len(part),'prevalence':float(y.mean()),
           'AP':{name:float(average_precision_score(y,p[indices])) if y.sum() else None
                 for name,p in preds.items()}}
    result['fields']={}
    for c in structural:
        row=[]
        for name,part in [('train',tr),('val',va),('test',te)]:
            v=pd.to_numeric(part[c],errors='coerce')
            pos=part.target.eq(1)
            row.append({'fold':name,'missing_pct':round(100*v.isna().mean(),2),
                'missing_in_winners_pct':round(100*v[pos].isna().mean(),2),
                'missing_in_losers_pct':round(100*v[~pos].isna().mean(),2),
                'median_winners':float(v[pos].median()) if v[pos].notna().any() else None,
                'median_losers':float(v[~pos].median()) if v[~pos].notna().any() else None})
        result['fields'][c]=row
    open('digui006-diagnostics.json','w').write(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
