"""Independent raw synchronization replay. Never imports the collector or economics."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def audit(root):
    root=Path(root)
    manifest=json.loads((root/'manifest.json').read_bytes())
    assert len(manifest)==6 and len({x['name'] for x in manifest})==6
    rows={x['name']:x for x in manifest}
    assert set(rows)=={'instruments','summaries','deliveries','index','atm_call','atm_put'}
    payload={}
    for name,row in rows.items():
        raw=(root/(name+'.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256'], 'RAW_HASH'
        assert len(raw)==row['bytes']
        j=json.loads(raw)
        assert j['testnet'] is False and 'error' not in j
        payload[name]=j['result']
    books=[payload[k] for k in ['atm_call','atm_put']]
    ages={k:dt.datetime.fromisoformat(rows[k]['received']).timestamp()-payload[k]['timestamp']/1000 for k in ['atm_call','atm_put']}
    skew=abs(books[0]['timestamp']-books[1]['timestamp'])
    distance=abs(max(b['timestamp'] for b in books)/1000-dt.datetime.fromisoformat(rows['index']['received']).timestamp())
    out=dict(raw_hashes_verified=6,book_skew_ms=skew,book_skew_limit_ms=1000,
             book_ages_seconds=ages,index_distance_seconds=distance,
             synchronization_pass=skew<=1000 and distance<=10 and all(-3<=a<=10 for a in ages.values()),
             economic_observation=False)
    r=json.loads((root/'receipt.json').read_bytes())
    if r.get('mode')=='sync-check':
        assert r.get('diagnostic_only') is True
        assert not any(k in r for k in ['forecast','structures','control_selected'])
        assert r['synchronization']['book_skew_ms']==skew
        assert (r['status']=='SYNC_DIAGNOSTIC_PASS')==out['synchronization_pass']
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--expect',choices=['pass','fail'],required=True)
    a=p.parse_args();result=audit(a.root)
    print(json.dumps(result,indent=2,sort_keys=True))
    assert result['synchronization_pass']==(a.expect=='pass'), 'SYNC_AUDIT_EXPECTATION'
