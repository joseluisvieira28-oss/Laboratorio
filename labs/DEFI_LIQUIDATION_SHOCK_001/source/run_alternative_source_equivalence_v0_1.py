"""Outcome-blind empirical source gate; credentials never enter output/errors."""
import ast
import datetime as dt
import hashlib
import gzip
import json
import os
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FIX = BASE / 'fixtures/route_a2'
OUT = Path('route_a2_evidence')
ZIP_SHA = '5e14c1712a97d60983b7321735615681671b76dcb1bce5f973dfdb28f3cfab7f'
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
SYSVAR = 'Sysvar1nstructions1111111111111111111111111'
ALPH = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
START = 1721417452  # 2024-07-19T19:30:52Z
END = 1721433600    # 2024-07-20T00:00:00Z


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def digest(b):
    return hashlib.sha256(b).hexdigest()


def b58(s):
    n = 0
    for c in s:
        if c not in ALPH:
            raise ValueError('invalid_base58')
        n = n * 58 + ALPH.index(c)
    return b'\0' * (len(s) - len(s.lstrip('1'))) + (n.to_bytes((n.bit_length()+7)//8, 'big') if n else b'')


def cfg():
    # Read the literal frozen configuration without importing/executing collector.
    tree = ast.parse((BASE/'source/collect_protected_2025_source_v0_1.py').read_text())
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'CFG' for t in n.targets))


class RPC:
    def __init__(self):
        self.url = ('https://mainnet.helius-rpc.com/?api-key=' + os.environ['HELIUS_API_KEY']) if os.environ.get('HELIUS_API_KEY') else os.environ.get('DLS_RPC_URL')
        self.ledger = []
        self.cache = {}
        self.disabled = False

    def call(self, method, params):
        if method not in ('getTransaction', 'getSignaturesForAddress'):
            raise ValueError('rpc_method_not_authorized')
        if not self.url or self.disabled:
            raise ValueError('credential_absent_or_rejected')
        payload = json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
        for attempt in range(3):
            time.sleep(.26)
            rec = {'method':method, 'attempt':attempt+1, 'sequence':len(self.ledger)+1}
            try:
                req = urllib.request.Request(self.url, data=payload, headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    raw = response.read()
                obj = json.loads(raw)
                if obj.get('error'):
                    code = obj['error'].get('code')
                    rec['rpc_error_code'] = code if isinstance(code, int) else None
                    self.ledger.append(rec)
                    # Never persist a provider error message/body: it may reflect URL.
                    raise ValueError('rpc_error_response')
                if 'result' not in obj:
                    raise ValueError('rpc_result_missing')
                if method == 'getTransaction' and obj['result'] is not None:
                    bt = obj['result'].get('blockTime')
                    if not isinstance(bt, int) or bt >= 1735689600:
                        raise ValueError('source_time_firewall')
                # Success bodies only. No headers, endpoint, request URL or secret.
                path = OUT/'raw'/f'{rec["sequence"]:06d}_{method}.json'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                rec.update(file=str(path.relative_to(OUT)), sha256=digest(raw), bytes=len(raw))
                self.ledger.append(rec)
                return obj['result']
            except urllib.error.HTTPError as e:
                rec['http_status'] = e.code
                self.ledger.append(rec)
                if e.code in (401,403,402):
                    self.disabled = True
                    raise ValueError('credential_or_credit_rejected') from None
            except (urllib.error.URLError, TimeoutError, OSError):
                rec['transport_error'] = True
                self.ledger.append(rec)
            if attempt < 2:
                time.sleep(2 ** attempt)
        raise ValueError('rpc_transport_exhausted')

    def tx(self, sig):
        if sig not in self.cache:
            self.cache[sig] = self.call('getTransaction',[sig,{'encoding':'json','commitment':'finalized','maxSupportedTransactionVersion':0}])
        if not isinstance(self.cache[sig],dict):
            raise ValueError('archival_transaction_null')
        return self.cache[sig]


def normalize(r):
    if not isinstance(r,dict) or not isinstance(r.get('meta'),dict) or 'err' not in r['meta']:
        raise ValueError('explicit_meta_err_missing')
    msg = r['transaction']['message']
    static = msg['accountKeys']
    if not all(isinstance(x,str) for x in static):
        raise ValueError('parsed_compiled_ambiguity')
    meta = r['meta']
    la = meta.get('loadedAddresses')
    if msg.get('addressTableLookups') and (not isinstance(la,dict) or 'writable' not in la or 'readonly' not in la):
        raise ValueError('loaded_addresses_missing')
    la = la or {'writable':[], 'readonly':[]}
    keys = static + la['writable'] + la['readonly']
    if not all(isinstance(x,str) for x in keys):
        raise ValueError('account_vector_malformed')
    def key(i):
        if type(i) is not int or not 0 <= i < len(keys):
            raise ValueError('account_index_invalid')
        return keys[i]
    def resolve(ix, path):
        if 'parsed' in ix or 'programIdIndex' not in ix:
            raise ValueError('compiled_instruction_required')
        return {'path':path,'program':key(ix['programIdIndex']),
                'accounts':[key(i) for i in ix['accounts']], 'data':b58(ix['data']),
                'depth':ix.get('stackHeight')}
    top = [resolve(ix,[i]) for i,ix in enumerate(msg['instructions'])]
    inner = []
    paths = []
    depth_errors = []
    seen_groups = set()
    for group in meta.get('innerInstructions') or []:
        outer = group['index']
        if type(outer) is not int or not 0 <= outer < len(top) or outer in seen_groups:
            raise ValueError('invalid_inner_group')
        seen_groups.add(outer)
        parents = {1:[outer]}
        counts = {}
        previous = 1
        ambiguous = False
        for ordinal,ix in enumerate(group['instructions']):
            depth = ix.get('stackHeight')
            if type(depth) is not int or depth < 2 or depth > previous+1 or depth-1 not in parents:
                ambiguous = True
            if ambiguous:
                path = None
                depth_errors.append({'outer':outer,'ordinal':ordinal,'reason':'ambiguous_stack_height'})
            else:
                parent = parents[depth-1]
                k = tuple(parent)
                path = parent + [counts.get(k,0)]
                counts[k] = counts.get(k,0)+1
                parents = {d:p for d,p in parents.items() if d < depth}
                parents[depth] = path
                previous = depth
            entry = resolve(ix,path)
            inner.append(entry)
            paths.append(path)
    balances = {}
    for side in ('preTokenBalances','postTokenBalances'):
        if side not in meta or not isinstance(meta[side],list):
            raise ValueError('token_metadata_missing')
        items = []
        seen = set()
        for tb in meta[side]:
            account = key(tb['accountIndex'])
            if account in seen:
                raise ValueError('duplicate_token_balance_index')
            seen.add(account)
            mint,dec = tb.get('mint'),tb.get('uiTokenAmount',{}).get('decimals')
            if not isinstance(mint,str) or type(dec) is not int:
                raise ValueError('token_unit_metadata_malformed')
            items.append((account,mint,dec))
        balances[side] = sorted(items)
    return {'signature':r['transaction']['signatures'][0], 'slot':r['slot'],'timestamp':r['blockTime'],
            'err':meta['err'],'keys':keys,'loaded':la,'top':top,'inner':inner,
            'balances':balances,'depth_errors':depth_errors,'version':r.get('version')}


def fidelity(n):
    # Compare payload bytes in memory only; hash ledger retains original source.
    return {k:n[k] for k in ('signature','slot','timestamp','err','keys','loaded','top','inner','balances','version')}


def matches(n, config):
    return [(name,ix) for ix in n['top']+n['inner'] for name,c in config.items()
            if ix['program']==c['program'] and ix['data'].startswith(bytes.fromhex(c['prefix']))]


def shape(name, ix):
    a,d = ix['accounts'],ix['data']
    if name == 'marginfi':
        return len(a)>=10
    if name == 'save0c':
        return len(a)==12 and len(d)==9
    if name == 'save11':
        return len(a)==15 and len(d) in (9,10)
    return len(d)==32 and ((len(a)==16 and a[14]==TOKEN and a[15]==SYSVAR) or
           (len(a)>=20 and a[16]==TOKEN and bool(a[17]) and bool(a[18]) and a[19]==SYSVAR))


def unit(n, ix):
    if not shape('save11',ix):
        raise ValueError('save11_shape')
    pairs = {}
    for entries in n['balances'].values():
        for account,mint,dec in entries:
            pairs.setdefault(account,set()).add((mint,dec))
    primary = pairs.get(ix['accounts'][8],set())
    optional = pairs.get(ix['accounts'][2],set())
    if len(primary)!=1 or len(optional)>1 or (optional and optional!=primary):
        raise ValueError('save11_primary_optional_conflict')
    return sorted(primary), bool(optional)


def main():
    OUT.mkdir(exist_ok=True)
    present = {'helius_api_key_present':bool(os.environ.get('HELIUS_API_KEY')),
               'dls_rpc_url_present':bool(os.environ.get('DLS_RPC_URL'))}
    dump(OUT/'credential_presence.json',present)
    assert any(present.values()), 'credential_absent'
    zpath = FIX/'DLS_RAW_SAMPLE_VERIFY_20260916_221907.zip'
    assert digest(zpath.read_bytes())==ZIP_SHA, 'original_zip_hash_mismatch'
    originals = {}
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None, 'zip_crc'
        for name in z.namelist():
            if '/candidate_transactions/' in name.replace('\\', '/') and name.endswith('.json'):
                r = json.loads(z.read(name))['result']
                originals[r['transaction']['signatures'][0]] = r
    assert len(originals)==23, 'original_23_required'
    manifest = json.loads((FIX/'SQD_MANIFEST.json').read_text())
    def fixture_bytes(name):
        return gzip.decompress((FIX/(name+'.gz')).read_bytes()) if name=='2024-07-20.json' else (FIX/name).read_bytes()
    for name in ('2024-07-19.json','2024-07-20.json'):
        expected = next(x['sha256'] for x in manifest['chunks'] if x['file']==name)
        assert digest(fixture_bytes(name))==expected, 'sqd_member_hash_mismatch'
    baseline = json.loads((FIX/'2024-07-19.json').read_text())
    assert baseline['stream_complete'] and baseline['classification']=='SOURCE_CHUNK_PASS'
    assert baseline['rows_sha256']==digest(json.dumps(baseline['rows'],sort_keys=True,separators=(',',':')).encode())
    nextday = json.loads(fixture_bytes('2024-07-20.json'))
    anchor = min(nextday['rows'], key=lambda x:(x['slot'],x['transactionIndex']))
    queue = json.loads((BASE/'KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.3.json').read_text())
    selected = [(protocol,e) for protocol,v in queue.items() for e in v['entries']]
    assert len(selected)==64
    config = cfg()
    rpc = RPC()
    normalized = {}
    errors = []
    raw_tests, alt_tests, cpi_tests, semantic_tests, unit_tests = [],[],[],[],[]
    def get(sig):
        if sig not in normalized:
            normalized[sig] = normalize(rpc.tx(sig))
            if normalized[sig]['signature']!=sig:
                raise ValueError('signature_mismatch')
        return normalized[sig]
    for sig in dict.fromkeys(list(originals)+[e['signature'] for _,e in selected]):
        try:
            n = get(sig)
            alt_tests.append({'signature':sig,'pass':True,'version':n['version'],
                              'loaded_writable':len(n['loaded']['writable']),'loaded_readonly':len(n['loaded']['readonly'])})
            if sig in originals:
                raw_tests.append({'signature':sig,'pass':fidelity(n)==fidelity(normalize(originals[sig]))})
            for protocol,ix in matches(n,config):
                if n['err'] is not None:
                    continue
                semantic_tests.append({'signature':sig,'protocol':protocol,'path':ix['path'],'pass':shape(protocol,ix)})
                if protocol=='save11':
                    try:
                        pair,opt = unit(n,ix)
                        original_match = None
                        if sig in originals:
                            old = normalize(originals[sig])
                            oldix = [i for p,i in matches(old,config) if p=='save11' and i['path']==ix['path']]
                            original_match = len(oldix)==1 and unit(old,oldix[0])==(pair,opt)
                        unit_tests.append({'signature':sig,'path':ix['path'],'pass':original_match is not False,
                                           'original_raw_unit_equal':original_match,'optional_available':opt})
                    except ValueError as e:
                        unit_tests.append({'signature':sig,'pass':False,'reason':str(e)})
        except (ValueError, KeyError, TypeError, IndexError) as e:
            errors.append({'signature':sig,'reason':str(e) if isinstance(e,ValueError) else type(e).__name__})
        if len(alt_tests)%20==0:
            print(json.dumps({'phase':'historical_fixture_checks','transactions_validated':len(alt_tests)}),flush=True)
    for protocol,e in selected:
        sig = e['signature']
        try:
            n = get(sig)
            got = [i['path'] for p,i in matches(n,config) if p==protocol]
            expected = e['instruction_addresses']
            passed = not n['depth_errors'] and n['err'] is None and n['slot']==e['slot'] and dt.datetime.fromtimestamp(n['timestamp'],dt.timezone.utc).isoformat().replace('+00:00','Z')==e['timestamp'] and sorted(got)==sorted(expected)
            cpi_tests.append({'signature':sig,'protocol':protocol,'pass':passed,'expected_paths':expected,
                              'observed_paths':got,'depth_errors':n['depth_errors']})
        except (ValueError,KeyError,TypeError) as e:
            cpi_tests.append({'signature':sig,'protocol':protocol,'pass':False,'reason':type(e).__name__})

    # A complete program-address scan, independently filtered by raw discriminator.
    census = {'protocol':'save11','start':'2024-07-19T19:30:52Z','end':'2024-07-20T00:00:00Z',
              'pages':[],'complete':False,'upper_anchor':anchor['signature'],'errors':[],
              'expected':len({r['signature'] for r in baseline['rows']}),
              'observed':None,'intersection':None,'missing':None,'extra':None,'duplicates':0}
    observed = set()
    actual_paths = set()
    expected = {r['signature'] for r in baseline['rows']}
    expected_paths = {(r['signature'],tuple(r['instructionAddress'])) for r in baseline['rows']}
    try:
        a = get(anchor['signature'])
        assert a['timestamp']>=END and a['timestamp']<1735689600 and a['slot']==anchor['slot'], 'historical_upper_anchor'
        cursor = anchor['signature']
        seen = set()
        candidates = []
        for page in range(40):
            rows = rpc.call('getSignaturesForAddress',[config['save11']['program'],{'before':cursor,'limit':1000,'commitment':'finalized'}])
            if not isinstance(rows,list):
                raise ValueError('signature_page_schema')
            if not rows:
                raise ValueError('empty_page_before_lower_boundary')
            if any(type(r.get('blockTime')) is not int for r in rows):
                raise ValueError('signature_blocktime_missing')
            if any(r['blockTime']>=1735689600 for r in rows):
                raise ValueError('signature_time_firewall')
            if any(rows[i]['slot']<rows[i+1]['slot'] for i in range(len(rows)-1)):
                raise ValueError('non_descending_slot_page')
            for r in rows:
                if r['signature'] in seen:
                    census['duplicates']+=1
                seen.add(r['signature'])
                if START<=r['blockTime']<END:
                    candidates.append(r)
            census['pages'].append({'count':len(rows),'first_slot':rows[0]['slot'],'last_slot':rows[-1]['slot'],
                                    'before':cursor,'next_before':rows[-1]['signature']})
            if rows[-1]['blockTime']<START:
                census['pagination_lower_boundary_reached']=True
                break
            if rows[-1]['signature']==cursor:
                raise ValueError('nonadvancing_cursor')
            cursor = rows[-1]['signature']
        else:
            raise ValueError('signature_page_safety_cap')
        census['in_window_program_signatures']=len(candidates)
        # Explicit failed status cannot enter realized-event census. Fetch every successful record.
        if any('err' not in r for r in candidates):
            raise ValueError('signature_err_missing')
        candidates = [r for r in candidates if r['err'] is None]
        census['successful_program_signatures']=len(candidates)
        for r in candidates[:500]:
            n = get(r['signature'])
            if n['timestamp']!=r['blockTime'] or n['slot']!=r['slot'] or n['err'] is not None:
                raise ValueError('signature_transaction_metadata_conflict')
            for p,ix in matches(n,config):
                if p=='save11':
                    observed.add(r['signature'])
                    if ix['path'] is None:
                        raise ValueError('census_cpi_ambiguous')
                    actual_paths.add((r['signature'],tuple(ix['path'])))
        if len(candidates)>500:
            raise ValueError('census_transaction_safety_cap')
        census['complete']=True
    except (ValueError,AssertionError,KeyError,TypeError) as e:
        census['errors'].append(str(e) if isinstance(e,(ValueError,AssertionError)) else type(e).__name__)
    census.update(observed=len(observed), intersection=len(expected&observed), missing=len(expected-observed), extra=len(observed-expected),
                  missing_signatures=sorted(expected-observed), extra_signatures=sorted(observed-expected),
                  instruction_missing=len(expected_paths-actual_paths),instruction_extra=len(actual_paths-expected_paths))
    census['pass']=census['complete'] and not census['errors'] and not census['duplicates'] and expected==observed and expected_paths==actual_paths
    coverage = sorted({x['protocol'] for x in semantic_tests})
    tests = {
      '1_transaction_census':{'status':'PASS' if census['pass'] else 'BLOCKED','executed':True,'evidence':census},
      '2_raw_fidelity':{'status':'PASS' if len(raw_tests)==23 and all(x['pass'] for x in raw_tests) else 'BLOCKED','executed':True,'results':raw_tests,'scope':'original 23 RAW versus new archival RAW; not full four-class SQD fidelity'},
      '3_versioned_alt':{'status':'PASS' if len(alt_tests)==len(set(list(originals)+[e['signature'] for _,e in selected])) and any(x['loaded_writable']+x['loaded_readonly'] for x in alt_tests) else 'BLOCKED','executed':True,'results':alt_tests},
      '4_cpi_instruction_address':{'status':'PASS' if len(cpi_tests)==64 and all(x['pass'] for x in cpi_tests) else 'BLOCKED','executed':True,'results':cpi_tests},
      '5_frozen_semantics':{'status':'PASS' if coverage==sorted(config) and semantic_tests and all(x['pass'] for x in semantic_tests) else 'BLOCKED','executed':True,'coverage':coverage,'missing_classes':sorted(set(config)-set(coverage)),'results':semantic_tests},
      '6_save11_balance_mapping':{'status':'PASS' if unit_tests and all(x['pass'] for x in unit_tests) else 'BLOCKED','executed':True,'results':unit_tests,'scope':'RAW pre/post primary and optional identity; full SQD paired units not supplied by queue'}
    }
    # Additional paired evidence is mandatory; scoped checks cannot authorize global PASS.
    blockers = [name for name,v in tests.items() if v['status']!='PASS']
    blockers += ['FOUR_CLASS_PAIRED_SQD_RAW_ACCOUNT_DATA_AND_UNIT_EVIDENCE_INCOMPLETE']
    receipt = {'schema_version':'0.2','lab_id':'DEFI-LIQUIDATION-SHOCK-001',
       'classification':'ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED' if blockers or errors else 'ALTERNATIVE_SOURCE_EQUIVALENCE_PASS',
       'blockers':blockers,'tests':tests,'errors':errors,'credential_presence':present,
       'original_zip_sha256':ZIP_SHA,'commit':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),
       'rpc_request_count':len(rpc.ledger),'firewall':{'economic_outcomes_opened':False,'protected_2025_acquisition':False,
       'data_2026':False,'science_changed':False,'secret_values_exposed':False,'purchases':False,'live_trading':False,'merge_main':False}}
    dump(OUT/'RPC_LEDGER.json',rpc.ledger)
    dump(OUT/'DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_RECEIPT_V0.2.json',receipt)
    print(json.dumps({'classification':receipt['classification'],'tests':{k:v['status'] for k,v in tests.items()},'rpc_request_count':len(rpc.ledger),'blockers':blockers}),flush=True)


if __name__=='__main__':
    main()

