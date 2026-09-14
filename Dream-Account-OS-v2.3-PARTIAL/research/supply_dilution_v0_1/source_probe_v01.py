import json, urllib.request, urllib.error
from pathlib import Path

OUT=Path('source_probe_output'); OUT.mkdir(exist_ok=True)
probes=[]

def probe(name,url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 CryptoResearchSourceProbe/1.0'})
    rec={'name':name,'url':url,'http_status':None,'json_type':None,'top_keys':None,'series_lengths':None,'economic_values_evaluated':False}
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(); rec['http_status']=r.status
        obj=json.loads(raw)
        rec['json_type']=type(obj).__name__
        if isinstance(obj,dict):
            rec['top_keys']=sorted(obj.keys())
            rec['series_lengths']={k:len(v) for k,v in obj.items() if isinstance(v,list)}
        elif isinstance(obj,list): rec['series_lengths']={'root':len(obj)}
    except urllib.error.HTTPError as e:
        rec['http_status']=e.code
    except Exception as e:
        rec['error_type']=type(e).__name__
    probes.append(rec)

# Fixed pre-2025 windows. Structure/count only; do not inspect values.
probe('coingecko_market_chart_bitcoin_2021','https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from=1609459200&to=1640995199&interval=daily')
probe('coingecko_market_chart_ethereum_2021','https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range?vs_currency=usd&from=1609459200&to=1640995199&interval=daily')
probe('coingecko_explicit_circulating_supply_bitcoin_2021','https://api.coingecko.com/api/v3/coins/bitcoin/circulating_supply_chart/range?from=2021-01-01&to=2021-12-31')

report={
 'lab':'SUPPLY-DILUTION-001','mode':'SOURCE_PROBE_ONLY',
 'signal_computed':False,'returns_computed':False,'pnl_computed':False,
 'holdout_2025_accessed':False,'year_2026_accessed':False,
 'probes':probes,
 'notes':[
  'CoinGecko market_chart/range contains price and market-cap arrays; this probe records only structure/counts, not values.',
  'Historical circulating supply may be directly entitlement-gated; market_cap/price reconstruction is not authorized until semantics and point-in-time integrity are independently validated.',
  'DefiLlama official api-sdk documents Emissions as API-key locked; no credential bypass attempted.'
 ]
}
statuses=[p.get('http_status') for p in probes]
if statuses[0]==200 and statuses[1]==200:
    report['classification']='SOURCE_PARTIAL_FEASIBLE_UNIVERSE_PROVENANCE_PENDING'
else:
    report['classification']='SOURCE_AUTH_OR_ACCESS_BLOCKED'
(OUT/'SUPPLY_DILUTION_001_SOURCE_PROBE_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True))
print('NO SIGNAL / NO RETURN / NO PNL / 2025 LOCKED / 2026 LOCKED')
