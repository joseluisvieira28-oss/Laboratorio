"""Four existing frozen decoder references; exact SQD/RPC pair diagnostics."""
import ast,json,time,urllib.request,urllib.error
import run_alternative_source_equivalence_v0_1 as g


def main():
    tree=ast.parse((g.BASE/'source/validate_field_decoder_implementation_v0_1.py').read_text())
    refs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REFS' for t in n.targets))[:4]
    rpc=g.RPC();results=[]
    for ref in refs:
        rec={'protocol':ref['name'],'signature':ref['sig'],'slot':ref['slot'],'pass':False,'sqd_attempts':[]}
        body={'type':'solana','fromBlock':ref['slot'],'toBlock':ref['slot'],
              'fields':{'block':{'number':True,'timestamp':True},'transaction':{'transactionIndex':True,'signatures':True,'err':True},
              'instruction':{'programId':True,'accounts':True,'data':True,'transactionIndex':True,'instructionAddress':True,'isCommitted':True,'error':True},
              'tokenBalance':{'transactionIndex':True,'account':True,'preMint':True,'postMint':True,'preDecimals':True,'postDecimals':True}},
              'instructions':[{'programId':[ref['program']],'transaction':True,'transactionTokenBalances':True}]}
        try:
            n=g.normalize(rpc.tx(ref['sig']))
            mi=[ix for p,ix in g.matches(n,g.cfg()) if p==ref['name']]
            rec.update(rpc_transaction_observed=True,raw_success=n['err'] is None,
                       raw_shape_pass=bool(mi) and all(g.shape(ref['name'],i) for i in mi),
                       raw_paths=[i['path'] for i in mi],cpi_depth_ambiguities=n['depth_errors'])
            if ref['name']=='save11':
                rec['raw_unit_mapping_pass']=bool(mi) and all(bool(g.unit(n,i)[0]) for i in mi)
            blocks=None
            for attempt in range(3):
                try:
                    request=urllib.request.Request('https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Accept':'application/x-ndjson'})
                    with urllib.request.urlopen(request,timeout=25) as response:
                        raw=response.read();status=response.status
                    rec['sqd_attempts'].append({'http':status,'bytes':len(raw)})
                    if status==200:
                        blocks=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
                        p=g.OUT/'paired'/f'{ref["name"]}.ndjson';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
                        rec['sqd_raw_sha256']=g.digest(raw)
                    break
                except urllib.error.HTTPError as e:
                    rec['sqd_attempts'].append({'http':e.code})
                    if e.code in (401,403):break
                except (urllib.error.URLError,TimeoutError,OSError):
                    rec['sqd_attempts'].append({'transport_error':True})
                time.sleep(2)
            if not blocks:raise ValueError('SQD_PAIRED_SOURCE_UNAVAILABLE')
            sq=[];units={}
            for block in blocks:
                hdr=block['header'];assert hdr['number']==ref['slot'],'sqd_slot_conflict'
                if isinstance(hdr['timestamp'],str):
                    stamp=int(g.dt.datetime.fromisoformat(hdr['timestamp'].replace('Z','+00:00')).timestamp())
                else:stamp=hdr['timestamp']
                assert stamp==n['timestamp'],'sqd_time_conflict'
                txs={tx['transactionIndex']:tx for tx in block.get('transactions',[])}
                for ix in block.get('instructions',[]):
                    tx=txs[ix['transactionIndex']]
                    if tx['signatures'][0]!=ref['sig'] or ix['programId']!=ref['program']:continue
                    if not g.b58(ix['data']).startswith(bytes.fromhex(ref['prefix'])):continue
                    assert 'err' in tx and tx['err']==n['err'],'sqd_status_conflict'
                    assert ix['isCommitted'] is True and ix.get('error') is None,'sqd_instruction_status'
                    sq.append({'path':ix['instructionAddress'],'program':ix['programId'],'accounts':ix['accounts'],'data':g.b58(ix['data'])})
                    for tb in block.get('tokenBalances',[]):
                        if tb['transactionIndex']!=ix['transactionIndex']:continue
                        for side in ('pre','post'):
                            if isinstance(tb.get(side+'Mint'),str) and type(tb.get(side+'Decimals')) is int:
                                units.setdefault(tb['account'],set()).add((tb[side+'Mint'],tb[side+'Decimals']))
            assert sq and len(sq)==len(mi),'relevant_instruction_count_conflict'
            assert len({tuple(x['path']) for x in sq})==len(sq),'duplicate_sqd_path'
            assert not n['depth_errors'],'CPI_DEPTH_AMBIGUOUS'
            actual=[{k:i[k] for k in ('path','program','accounts','data')} for i in mi]
            assert sorted(sq,key=lambda i:i['path'])==sorted(actual,key=lambda i:i['path']),'SQD_RPC_EXACT_INSTRUCTION_CONFLICT'
            if ref['name']=='save11':
                for ix in mi:
                    pair,opt=g.unit(n,ix)
                    primary=units.get(ix['accounts'][8],set());optional=units.get(ix['accounts'][2],set())
                    assert sorted(primary)==pair and (not optional or optional==primary),'SQD_RPC_UNIT_CONFLICT'
                rec['sqd_raw_unit_equal']=True
            rec['pass']=n['slot']==ref['slot'] and n['signature']==ref['sig'] and n['err'] is None and rec['raw_shape_pass']
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as e:
            rec['reason']=str(e) if isinstance(e,(ValueError,AssertionError)) else type(e).__name__
        results.append(rec)
        print(json.dumps({'protocol':ref['name'],'pass':rec['pass'],'reason':rec.get('reason')}),flush=True)
    g.dump(g.OUT/'FOUR_CLASS_PAIRED_SOURCE_RECEIPT_V0.1.json',{'results':results,'pass':len(results)==4 and all(r['pass'] for r in results),
      'provenance':'Existing frozen validate_field_decoder_implementation_v0_1.py REFS; no reselection',
      'run_id':g.os.environ.get('GITHUB_RUN_ID'),'commit':g.os.environ.get('GITHUB_SHA'),'economic_outcomes_opened':False})
    g.dump(g.OUT/'RPC_LEDGER.json',rpc.ledger)

if __name__=='__main__':main()

