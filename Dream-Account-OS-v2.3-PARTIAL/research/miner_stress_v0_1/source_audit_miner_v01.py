import json, urllib.request, hashlib
from datetime import datetime, timezone
from pathlib import Path

OUT=Path('source_audit_output'); OUT.mkdir(exist_ok=True)
START='2018-01-01'; END_TS=int(datetime(2024,12,31,23,59,59,tzinfo=timezone.utc).timestamp())
URLS={
 'hash_rate':'https://api.blockchain.info/charts/hash-rate?start=2018-01-01&timespan=2556days&format=json&sampled=false',
 'difficulty':'https://api.blockchain.info/charts/difficulty?start=2018-01-01&timespan=2556days&format=json&sampled=false',
}
manifest=[]; series={}
for name,url in URLS.items():
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 CryptoResearchSourceAudit/1.0'})
    with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
    sha=hashlib.sha256(raw).hexdigest(); obj=json.loads(raw)
    vals=obj.get('values',[])
    rows=[]
    for p in vals:
        x=int(p['x'])
        if x<=END_TS: rows.append((x,p.get('y')))
    timestamps=[x for x,_ in rows]
    dup=len(timestamps)-len(set(timestamps))
    manifest.append({'series':name,'url':url,'sha256':sha,'rows_in_protected_window':len(rows),'min_ts':min(timestamps) if timestamps else None,'max_ts':max(timestamps) if timestamps else None,'duplicates':dup,'economic_outcome':False})
    series[name]=timestamps
    (OUT/f'{name}_raw.json').write_bytes(raw)
common=sorted(set(series['hash_rate']) & set(series['difficulty']))
from_ts=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp())
to_ts=int(datetime(2024,12,31,23,59,59,tzinfo=timezone.utc).timestamp())
common=[x for x in common if from_ts<=x<=to_ts]
report={
 'lab':'MINER-STRESS-001','mode':'SOURCE_DATA_AUDIT_ONLY','source_manifest':manifest,
 'common_timestamp_count':len(common),
 'common_min_utc':datetime.fromtimestamp(min(common),timezone.utc).isoformat() if common else None,
 'common_max_utc':datetime.fromtimestamp(max(common),timezone.utc).isoformat() if common else None,
 'min_required_common':500,
 'structural_pass':len(common)>=500 and all(m['duplicates']==0 for m in manifest),
 'miner_signal_computed':False,'btc_price_values_evaluated':False,'btc_returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,
}
report['classification']='MINER_SOURCE_PASS' if report['structural_pass'] else 'SOURCE_DATA_INADEQUATE'
(OUT/'MINER_STRESS_001_SOURCE_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True))
print('MINER SOURCE ONLY / NO SIGNAL / NO BTC PRICES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['structural_pass'] else 2)
