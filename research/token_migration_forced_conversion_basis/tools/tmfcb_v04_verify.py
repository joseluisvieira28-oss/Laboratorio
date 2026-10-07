"""Offline integrity checks for metadata collection and failure semantics."""
import json
import hashlib
from unittest.mock import patch
import tmfcb_v04_factory_archive as archive
from tmfcb_v04_sources import OUT
from tmfcb_keccak import keccak

def run():
    manifest=json.loads((OUT/'EVIDENCE_MANIFEST.json').read_text())
    for item in manifest['files']:
        data=(OUT.parent.parent/item['path']).read_bytes()
        data=data.replace(b'\r\n',b'\n')
        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    assert keccak(b'')=='0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    assert keccak(b'Transfer(address,address,uint256)')=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    observed=[]
    def partial(url,q):
        observed.append(q['fromBlock'])
        n=12 if q['fromBlock']==10 else 15
        return {'status':200,'body':json.dumps({'header':{'number':n,'hash':'test','timestamp':1600000000}})}
    with patch.object(archive,'fetch',partial):
        pages,records,complete=archive.scan_range(10,15,archive.FACTORY,archive.PAIR)
        assert observed==[10,13] and complete and not records
    with patch.object(archive,'fetch',lambda *args:{'status':200,'body':''}):
        assert not archive.scan_range(10,15,archive.FACTORY,archive.PAIR)[2]
    with patch.object(archive,'fetch',lambda *args:{'status':529,'error':'test'}), patch.object(archive.time,'sleep'):
        assert not archive.scan_range(10,15,archive.FACTORY,archive.PAIR)[2]
    with patch.object(archive,'fetch',lambda *args:{'status':200,'body':json.dumps({'header':{'number':15,'hash':'test','timestamp':1767225600}})}):
        try: archive.scan_range(10,15,archive.FACTORY,archive.PAIR)
        except ValueError: pass
        else: raise AssertionError('2026 must fail')
    receipts=json.loads((OUT/'verified_deployment_receipts.json').read_text())
    assert len(receipts)==6 and all(r['receipt_matches_headers'] for r in receipts)
    for r in receipts:
        for item in r['receipts']:
            if item.get('metadata'):
                assert item['metadata']['transactionHash']==r['preidentified_tx']
                assert item['metadata']['status']=='0x1'
                assert 'logs' not in item['metadata']
        for h in r['headers']:
            if h.get('metadata'): assert int(h['metadata']['timestamp'],16)<1767225600
    for name in ['factory_archive_paginated.json','targeted_factory_windows.json']:
        d=json.loads((OUT/name).read_text())
        rows=d.get('creations',[]) if isinstance(d,dict) else [c for r in d for c in r.get('creations',[])]
        for c in rows:
            assert c['timestamp']<1767225600 and len(c['pool'])==42
            assert c['factory'] in [archive.FACTORY,'0x1f98431c8ad98523631ae4a59f267346ea31f984']
            assert set(c)<={'block','blockHash','timestamp','factory','token0','token1','pool','fee','transactionHash','logIndex'}
    print('PASS: pagination, empty/error fail-closed, 2026 guard, receipt/header consistency, creation field allowlists')

if __name__=='__main__': run()
