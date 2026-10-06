#!/usr/bin/env python3
"""Earliest Core queue + parameter-known-at-signal proof on the four recovered V3 payloads."""
import json
from source_probe_v01 import OUT, RECEIPTS, rpc, block, sig, digest, lower_bound
URL='https://eth-mainnet.g.alchemy.com/public'
CORE='0x9aee0b04504cef83a65ac3f0e838d0593bcb2bc7'
PC='0xdabad81af85554e9ae636395611c58f7ec1aaec5'
POOL='0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'
PROBES=[(84,19519241,19526281,['0xf5a40b84e4c73d9a6de5c0950d7430f6d43b3d2c']), (98,19620894,19628049,['0xd56232b949dd7e70e95bb99514eaf9dba160d042']), (112,19761839,19769002,['0xa761fa68173378d0a138a764fb610abe128545d0','0xdc3f8a2969675ab03d82369a074b0cc86b052ebb']), (122,19840920,19848075,['0x7f9cc7079ab0c2afc4613ce30653870c92245e54'])]
def word(s,n):return int(s[2+n*64:2+(n+1)*64],16)
def call(to,name,arg,bn):return rpc(URL,'eth_call',[{'to':to,'data':sig(name)[:10]+arg},hex(bn)])
rows=[]
for pid,qb,eb,targets in PROBES:
 r={'payload_id':pid,'payload_queue_block':qb,'effect_block':eb,'status':'SOURCE_BLOCKED','borrower_reconstruction_proved':False}
 try:
  logs=rpc(URL,'eth_getLogs',[{'address':CORE,'fromBlock':hex(qb),'toBlock':hex(qb),'topics':[sig('PayloadSent(uint256,uint40,address,uint256,uint256,uint256)'),None,'0x'+PC[2:].zfill(64),'0x'+format(1,'064x')]}])
  matches=[l for l in logs if word(l['data'],0)==pid]
  assert len(matches)==1
  proposal=int(matches[0]['topics'][1],16);r['proposal_id']=proposal;r['payload_sent_log']=matches[0]
  data=call(CORE,'getProposal(uint256)',format(proposal,'064x'),qb)
  base=word(data,0)//32;queued=word(data,base+5)
  assert queued>0
  sb=lower_bound(URL,queued,qb,max(16490000,qb-500000));r['signal_header']=block(URL,sb)
  assert r['signal_header']['timestamp']==queued
  qlogs=rpc(URL,'eth_getLogs',[{'address':CORE,'fromBlock':hex(sb),'toBlock':hex(sb),'topics':[sig('ProposalQueued(uint256,uint128,uint128)'),'0x'+format(proposal,'064x')]}]);assert len(qlogs)==1
  r['core_queue_log']=qlogs[0];r['core_proposal_abi_sha256']=digest(data.encode())
  changes=[];target_results=[]
  for target in targets:
   tr={'target':target,'status':'NO_COLLATERAL_UPDATES_ABI'}
   try:
    updates=call(target,'collateralsUpdates()','',sb)
    assert word(updates,0)==32
    n=word(updates,1);total=(len(updates)-2)//64
    assert n<100
    width=(total-2)//n if n else 0
    assert n==0 or (width in (5,6) and total==2+n*width)
    tr.update(status='PARAMETER_ABI_RECOVERED_AT_CORE_QUEUE',count=n,tuple_width=width,abi_sha256=digest(updates.encode()))
    for i in range(n):
     asset='0x'+format(word(updates,2+i*width),'040x');ltv=word(updates,3+i*width);new_lt=word(updates,4+i*width)
     old_cfg=call(POOL,'getConfiguration(address)',asset[2:].zfill(64),sb-1)
     old_lt=(word(old_cfg,0)>>16)&65535
     changes.append({'asset':asset,'old_lt_at_signal_minus_1':old_lt,'proposed_ltv_raw':str(ltv),'proposed_lt_raw':str(new_lt),'is_base_lt_reduction':0<=new_lt<old_lt,'target':target,'pre_signal_configuration_sha256':digest(old_cfg.encode())})
   except Exception as e:tr['failure']=str(e)
   target_results.append(tr)
  r.update(status='CORE_QUEUE_SOURCE_PASS_PARAMETERS_PARTIAL_NOT_FULL_SOURCE_GATE',target_results=target_results,parameter_rows=changes,base_lt_reductions_known_at_core_queue=sum(c['is_base_lt_reduction'] for c in changes),signal_to_effect_seconds=block(URL,eb)['timestamp']-queued)
 except Exception as e:r['failure']=str(e)
 rows.append(r);print(json.dumps(r),flush=True)
receipt={'phase':'APPROVED_PARAMETER_SOURCE_ONLY','probes':rows,'requests':RECEIPTS,'economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False,'accepted_full_source_shocks':0}
(OUT/'APPROVED_PARAMETER_SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
