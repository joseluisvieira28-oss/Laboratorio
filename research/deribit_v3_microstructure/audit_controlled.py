"""Offline revalidation of saved controlled evidence; never HTTP."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import adapter
import collector

def audit(path):
    path=Path(path)
    if path.suffix=='.zip':
        import zipfile
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as archive:
            collector.require(set(archive.namelist())=={'call.json','put.json','index.json','instruments.json','manifest.json','receipt.json'},'ARCHIVE_SET')
            archive.extractall(tmp)
            return audit(tmp)
    receipt=json.loads((path/'receipt.json').read_bytes())
    raw_manifest=(path/'manifest.json').read_bytes()
    collector.require(hashlib.sha256(raw_manifest).hexdigest()==receipt['manifest_sha256'],'MANIFEST_HASH')
    manifest=json.loads(raw_manifest)
    collector.require({m['name'] for m in manifest}=={'call','put','index','instruments'} and len(manifest)==4,'SOURCE_SET')
    data={}; sources={}
    for m in manifest:
        raw=(path/(m['name']+'.json')).read_bytes()
        collector.require(len(raw)==m['bytes'] and hashlib.sha256(raw).hexdigest()==m['sha256'],'RAW_HASH')
        collector.require(dt.datetime.fromisoformat(m['started'])<=dt.datetime.fromisoformat(m['received']),'TIME')
        data[m['name']]=json.loads(raw)['result']; sources[m['name']]=m
    expiry=dt.datetime.combine(dt.date.fromisoformat(receipt['session_utc'])+dt.timedelta(days=1),dt.time(8),collector.UTC)
    chosen=collector.select(data['instruments'],data['index']['index_price'],expiry)
    legs={}
    for side in ('call','put'):
        expected=adapter.request_url(chosen[side]['instrument_name'])
        collector.require(sources[side]['url']==expected,'URL')
        legs[side]=adapter.decode((path/(side+'.json')).read_bytes(),chosen[side]['instrument_name'],
            dt.datetime.fromisoformat(sources[side]['received']).timestamp()*1000,'controlled_observation')
    sync=adapter.synchronize(legs['call'],legs['put'],dt.datetime.fromisoformat(sources['index']['received']).timestamp()*1000)
    collector.require(receipt['mode']=='controlled_observation' and receipt['prospective_v3'] is False and receipt['net_pnl'] is None,'COHORT')
    return dict(status='OFFLINE_REVALIDATION_PASS',raw_hashes=4,synchronization=sync,prospective_sessions=0,live_go=False)

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1]),indent=2))
