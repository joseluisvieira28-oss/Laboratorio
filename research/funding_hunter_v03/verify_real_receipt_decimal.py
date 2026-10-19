"""Independent exact-decimal quote cross-check; local archives never exported.

This deliberately does not import the primary replay. It checks the six fixed
as-of aggregates against a full-archive receipt, not contract sizing or fills.
"""
import argparse
from decimal import Decimal
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import tarfile


def verify(path, case):
    targets=[int(datetime(2025,6,2,h,m,tzinfo=timezone.utc).timestamp()*1000)
             for h,m in ((0,5),(12,5),(23,55))]
    sides={'bids':{},'asks':{}}
    last=None
    checked=[]
    def check():
        i=len(checked); r=case['sample_quotes'][i]
        bid=max(sides['bids']);ask=min(sides['asks'])
        values={'best_bid_raw_price':bid,'best_ask_raw_price':ask,
                'best_bid_raw_contracts':sides['bids'][bid],
                'best_ask_raw_contracts':sides['asks'][ask],
                'sum_visible_bid_raw_contracts':sum(sides['bids'].values()),
                'sum_visible_ask_raw_contracts':sum(sides['asks'].values())}
        assert r['last_book_event_ms']==last
        assert last<=targets[i] and targets[i]-last<=2000
        assert len(sides['bids'])==len(sides['asks'])==400
        for k,v in values.items():
            assert abs(v-Decimal(str(r[k])))<=max(Decimal('0.00000001'),abs(v)*Decimal('1e-12')),(k,v,r[k])
        checked.append({'probe_utc':r['probe_utc'],'last_book_event_ms':last,
                        'exact_decimal_aggregates':{k:str(v) for k,v in values.items()}})
    with gzip.open(path,'rb') as g,tarfile.open(fileobj=g,mode='r|') as t:
        f=t.extractfile(t.next())
        for line in f:
            e=json.loads(line);ts=int(e['ts'])
            while len(checked)<3 and ts>targets[len(checked)]:check()
            if len(checked)==3:break
            assert e['instId']==case['instrument']
            assert last is None or ts>=last
            if e['action']=='snapshot':sides={'bids':{},'asks':{}}
            else:assert last is not None and e['action']=='update'
            for side in sides:
                for p,q,_ in e[side]:
                    p=Decimal(p);q=Decimal(q)
                    if q:sides[side][p]=q
                    else:sides[side].pop(p,None)
            last=ts
    while len(checked)<3:check()
    return checked


def main():
    a=argparse.ArgumentParser();a.add_argument('--receipt',type=Path,required=True)
    a.add_argument('--archive-dir',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    args=a.parse_args();r=json.loads(args.receipt.read_text())
    out={}
    for key,case in r['source_only_cases'].items():
        p=args.archive_dir/(case['instrument']+'-L2orderbook-400lv-2025-06-02.tar.gz')
        out[key]=verify(p,case)
    args.out.write_text(json.dumps({'status':'SIX_REAL_QUOTES_DECIMAL_CROSSCHECK_PASS','checks':out},indent=2)+'\n')
    print('SIX_REAL_QUOTES_DECIMAL_CROSSCHECK_PASS')


if __name__=='__main__':main()
