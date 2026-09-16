#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse, urllib.error, pathlib, hashlib, math
from datetime import datetime, timezone

BASE='https://api.glassnode.com'
OUT=pathlib.Path('artifacts/whale_cex_netflow_source_v01')
OUT.mkdir(parents=True, exist_ok=True)
AUTH=json.load(open(pathlib.Path(__file__).with_name('SOURCE_AUTHORITY_V0.1.json')))
METRICS=AUTH['metrics']
START=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2024,12,31,23,59,59,tzinfo=timezone.utc).timestamp())
KEY=os.getenv('GLASSNODE_API_KEY','').strip()

result={'lab_id':AUTH['lab_id'],'source_gate_id':AUTH['source_gate_id'],'access_2025':False,'access_2026':False,'outcomes_opened':False,'btc_prices_opened':False,'requests':[]}

def save():
    b=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    (OUT/'source_gate_result_v01.json').write_bytes(b)
    print(json.dumps(result,indent=2,sort_keys=True))

if not KEY:
    result['classification']='SOURCE_AUTH_BLOCKED'
    result['blocker']='GLASSNODE_API_KEY_NOT_AVAILABLE_FOR_PIT_ENDPOINTS'
    save(); raise SystemExit(0)

series={}
for path in METRICS:
    q={'a':'BTC','i':'24h','s':str(START),'u':str(END),'api_key':KEY}
    if 'volume' in path: q['c']='NATIVE'
    url=BASE+path+'?'+urllib.parse.urlencode(q)
    safe_url=BASE+path+'?a=BTC&i=24h&s='+str(START)+'&u='+str(END)+('&c=NATIVE' if 'volume' in path else '')
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'WHALE-CEX-NETFLOW-001-source-only'})
        with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
    except urllib.error.HTTPError as e:
        result['classification']='SOURCE_AUTH_BLOCKED' if e.code in (401,403) else 'SOURCE_PROVENANCE_FAILURE'
        result['blocker']=f'HTTP_{e.code}_{path}'
        result['requests'].append({'url':safe_url,'status':e.code})
        save(); raise SystemExit(0)
    h=hashlib.sha256(raw).hexdigest()
    (OUT/(path.rsplit('/',1)[-1]+'.json')).write_bytes(raw)
    rows=json.loads(raw)
    if not isinstance(rows,list):
        result['classification']='SOURCE_PROVENANCE_FAILURE'; result['blocker']='NON_LIST_RESPONSE'; save(); raise SystemExit(0)
    vals={}
    for row in rows:
        t=int(row['t']); v=float(row['v'])
        if t>END or t<START: raise RuntimeError('PROTECTED_OR_OUT_OF_RANGE_ROW')
        if t in vals or not math.isfinite(v) or v<0: raise RuntimeError('BAD_ROW')
        vals[t]=v
    series[path]=vals
    result['requests'].append({'url':safe_url,'status':200,'rows':len(rows),'sha256':h})

common=set.intersection(*(set(v) for v in series.values()))
years={str(y):0 for y in range(2021,2025)}
for t in common: years[str(datetime.fromtimestamp(t,tz=timezone.utc).year)]+=1
result['common_days']=len(common); result['common_days_by_year']=years
pass_gate=(len(common)>=AUTH['min_common_days'] and all(years[str(y)]>=AUTH['min_common_days_per_year'] for y in range(2021,2025)))
result['classification']='SOURCE_DATA_PASS' if pass_gate else 'SOURCE_DATA_INSUFFICIENT'
if pass_gate:
    dep=series['/v1/metrics/transactions/transfers_volume_whales_to_exchanges_sum_pit']
    wd=series['/v1/metrics/transactions/transfers_volume_exchanges_to_whales_sum_pit']
    derived=[{'t':t,'whale_cex_netflow_btc':dep[t]-wd[t]} for t in sorted(common)]
    db=('\n'.join(json.dumps(x,sort_keys=True) for x in derived)+'\n').encode()
    (OUT/'whale_cex_netflow_source_only_v01.jsonl').write_bytes(db)
    result['derived_sha256']=hashlib.sha256(db).hexdigest()
save()
