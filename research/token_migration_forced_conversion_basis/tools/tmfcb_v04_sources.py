#!/usr/bin/env python3
"""Anonymous metadata-only source capability tests. Never download market files."""
import ast
import concurrent.futures as cf
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/v04'
OUT.mkdir(parents=True, exist_ok=True)
FACTORY = '0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f'
PAIR = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'
RPCS = ['https://ethereum-rpc.publicnode.com', 'https://eth.llamarpc.com',
        'https://1rpc.io/eth', 'https://rpc.flashbots.net', 'https://cloudflare-eth.com']

def load_constant(filename, name):
    tree = ast.parse((Path(__file__).parent / filename).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(name)

TOKENS = load_constant('tmfcb_v03_dex_factory_probe.py', 'TOKENS')
TXS = load_constant('tmfcb_v03_eth_provenance_probe.py', 'PREIDENTIFIED_TXS')

def fetch(url, body=None, method=None):
    started = time.monotonic()
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
          headers={'Content-Type': 'application/json', 'User-Agent': 'CryptoLab-TMFCB-V04-Metadata'}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read() if method != 'HEAD' else b''
            return {'status': res.status, 'sha256': hashlib.sha256(raw).hexdigest(),
                    'body': raw.decode(), 'seconds': round(time.monotonic()-started, 3)}
    except urllib.error.HTTPError as exc:
        return {'status': exc.code, 'error': str(exc), 'seconds': round(time.monotonic()-started,3)}
    except Exception as exc:
        return {'status': None, 'error': str(exc), 'seconds': round(time.monotonic()-started,3)}

def rpc_test(ep):
    rec = {'endpoint': ep, 'requests': []}
    token = '0x'+'0'*24+TOKENS['OGV'][2:].lower()
    tasks = [('eth_getBlockByNumber', ['0xff7376', False]),
             ('eth_getBlockByNumber', [hex(24000000), False]),
             ('eth_getTransactionReceipt', [TXS['TBTC_VENDING_MACHINE_V2_DEPLOY']]),
             ('eth_getLogs', [{'address': FACTORY, 'fromBlock':hex(15100000),
              'toBlock':hex(15100999), 'topics':[PAIR, token]}])]
    for method, params in tasks:
        reply = fetch(ep, {'jsonrpc':'2.0','id':1,'method':method,'params':params})
        raw = reply.pop('body', None)
        if raw:
            try:
                value = json.loads(raw)
                if 'error' in value: reply['rpc_error'] = value['error']
                else:
                    value = value.get('result')
                    if method == 'eth_getBlockByNumber' and value:
                        reply['metadata'] = {k:value.get(k) for k in ['number','hash','timestamp']}
                    elif method == 'eth_getTransactionReceipt' and value:
                        reply['metadata'] = {k:value.get(k) for k in ['transactionHash','blockNumber','blockHash','status','contractAddress']}
                    else: reply['metadata'] = value
            except Exception as exc: reply['parse_error'] = str(exc)
        reply.update(method=method, params=params)
        rec['requests'].append(reply)
    return rec

def auxiliary():
    results = []
    urls = ['https://portal.sqd.dev/datasets/ethereum-mainnet/metadata',
            'https://v2.archive.subsquid.io/network/ethereum-mainnet/16741270/worker',
            'https://aws-public-blockchain.s3.amazonaws.com/?list-type=2&prefix=v1.0/eth/&delimiter=/&max-keys=20']
    for url in urls:
        rec = fetch(url)
        rec['url'] = url
        results.append(rec)
    query = {'type':'evm','fromBlock':16741270,'toBlock':16741270,'includeAllBlocks':True,
             'fields':{'block':{'number':True,'hash':True,'timestamp':True}}}
    rec = fetch('https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream',query)
    rec.update(url='https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream',query=query)
    results.append(rec)
    gql = '{ pairs(first:1,where:{token0:"'+TOKENS['OGV'].lower()+'"}) { id token0 { id } token1 { id } createdAtTimestamp createdAtBlockNumber } }'
    rec = fetch('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',{'query':gql})
    rec.update(url='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',query=gql)
    results.append(rec)
    return results

SYMBOLS = ['OGV','OGN','MPL','SYRUP','CUDOS','FET','LBR','RAINI','RST','PLA','PDA',
           'MATIC','POL','GAL','G','MFT','HIFI','KEEP','NU','T','TBTC','RNDR','RENDER',
           'AGIX','OCEAN','CQT','CXT','BIT','MNT']

def archive_symbols():
    # Object listings only: never GET a .zip/.csv/.CHECKSUM file.
    base = 'https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?'
    results = []
    ns = {'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    for symbol in SYMBOLS:
        prefix = f'data/spot/monthly/klines/{symbol}USDT/1m/'
        continuation = None
        keys = []
        pages = []
        complete = False
        for _ in range(10):
            params = {'list-type':2,'prefix':prefix,'max-keys':1000}
            if continuation: params['continuation-token'] = continuation
            url = base + urllib.parse.urlencode(params)
            rec = fetch(url)
            raw = rec.pop('body',None)
            pages.append(rec)
            if raw is None: break
            try:
                tree = ET.fromstring(raw)
                for item in tree.findall('s:Contents',ns):
                    key = item.findtext('s:Key',namespaces=ns)
                    # Record dates, object IDs and size only; filter out 2026.
                    date = key.rsplit('/',1)[-1].split('-1m-')[-1].split('.')[0]
                    if '2022-01' <= date <= '2025-12' and key.endswith('.zip'):
                        keys.append({'key':key,'month':date,'size':item.findtext('s:Size',namespaces=ns),
                                     'etag':item.findtext('s:ETag',namespaces=ns)})
                if tree.findtext('s:IsTruncated',namespaces=ns) != 'true':
                    complete = True
                    break
                continuation = tree.findtext('s:NextContinuationToken',namespaces=ns)
                if not continuation: break
            except Exception as exc:
                pages[-1]['parse_error'] = str(exc)
                break
        results.append({'symbol':symbol+'USDT','prefix':prefix,'listing_complete':complete,
                        'objects_2022_2025':keys,'pages':pages})
    return results

def main():
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(rpc_test,ep) for ep in RPCS]
        aux = pool.submit(auxiliary)
        arch = pool.submit(archive_symbols)
        rpc = [f.result() for f in futures]
        data = {'rpc':rpc,'auxiliary':aux.result(),'archive':arch.result(),
                'scope':'metadata only; zero market-file downloads; no A-F promotions'}
    (OUT/'source_capabilities.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'rpc_http':[{'ep':r['endpoint'],'status':[x['status'] for x in r['requests']]} for r in rpc],
          'aux_http':[r['status'] for r in data['auxiliary']],
          'archive_nonempty':[r['symbol'] for r in data['archive'] if r['objects_2022_2025']]}))

if __name__ == '__main__': main()
