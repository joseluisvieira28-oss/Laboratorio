"""Read-only source diagnostics from immutable receipts. Never signals or PnL."""
import argparse
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path
import collector as c
import quality


def summarize(values):
    if not values:
        return {'n': 0}
    values=sorted(values)
    return {'n':len(values),'median_ms':statistics.median(values),
            'p95_ms':values[max(0, (95*len(values)+99)//100-1)],'max_ms':max(values)}


def audit(path):
    path=Path(path).resolve(strict=True)
    store=c.Store.__new__(c.Store)
    store.db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    try:
        result={**store.verify(),'outcomes_opened':0,'pnl_computed':False}
        counts=Counter(); failures=Counter(); intervals={v:[] for v in ['mexc','binance']}
        ages={v:[] for v in intervals};previous={}
        for payload, in store.db.execute('SELECT payload FROM receipts ORDER BY seq'):
            row=json.loads(payload);source=row['source'];validation=row.get('validation',{})
            if source.endswith('_connection_failure'):
                counts[source]+=1
            for venue in intervals:
                if source==venue+'_ws' and validation.get('applied'):
                    if venue in previous:
                        intervals[venue].append(row['received_ms']-previous[venue])
                    previous[venue]=row['received_ms']
                    ages[venue].append(validation['source_age_ms'])
            if source!='paired_grid':continue
            g=json.loads(store.db.execute('SELECT body FROM raw WHERE hash=?',(row['raw_sha256'],)).fetchone()[0])
            counts['grids']+=1;counts['claimed_valid']+=bool(g['source_valid'])
            future=any(o.get('received_ms',0)>g['grid_ms'] for o in g['observations'].values())
            counts['post_grid_quote']+=future
            counts['claimed_valid_post_grid_quote']+=future and g['source_valid']
            if g.get('quality_version')==2:
                rejected=quality.reasons(g);failures.update(rejected)
                counts['independently_valid']+=not rejected
            else:counts['legacy_quality_unproven']+=1
        result.update(counts=dict(counts),invalid_reasons_overlapping=dict(failures),
                      venues={v:{'applied_receipt_interval':summarize(intervals[v]),
                                 'applied_source_age':summarize(ages[v]),
                                 'intervals_over_1000ms':sum(x>1000 for x in intervals[v])} for v in intervals},
                      interpretation='Depth message silence does not establish fresh exchange observation; retain frozen 1000ms age limit. Short smoke cannot estimate full-day qualification.')
        return result
    finally:store.db.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);a=p.parse_args()
    print(json.dumps(audit(a.state),indent=2,allow_nan=False))
