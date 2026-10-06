#!/usr/bin/env python3
"""Source-lineage validation on all five known 2023–2024 clusters, no outcomes."""
import json
from source_probe_v01 import OUT, RECEIPTS, rpc, block, sig, digest, lower_bound

URL='https://eth.drpc.org'
PC='0xdabad81af85554e9ae636395611c58f7ec1aaec5'
GV2='0xec568fffba86c094cf06b22134b23074dfe2252c'
EXECUTIONS=[
 (17878097,'0x1fc35b0c3c317912ae40386e27bd20c4548bdb81b2857e04539c9739d30255cc'),
 (19526281,'0xa1d1abeeff779dc93a698dec3530026b6d55dd68cbcda9865a782f7317359868'),
 (19628049,'0xdc24579df95e2a816f240607d0dbf065cdb12ac131bcd9910a71afb3829ace9a'),
 (19769002,'0xa1d2e846c8171ae52755836364ba7252913119794c7eeb5fc879e296c6de7a76'),
 (19848075,'0x57ad6fd3effd544c0d6cf74810f424ba0edf1a724bcc041760ee4512ef55bf16'),
]
rows=[]
def word(data,index):return int(data[2+index*64:2+(index+1)*64],16)
for bn,tx in EXECUTIONS:
 row={'effect_block':bn,'effect_tx':tx,'status':'SOURCE_BLOCKED'}
 try:
  row['effect_header']=block(URL,bn)
  logs=rpc(URL,'eth_getLogs',[{'address':[PC,GV2],'fromBlock':hex(bn),'toBlock':hex(bn),'topics':[[sig('PayloadExecuted(uint40)'),sig('ProposalExecuted(uint256,address)')]]}])
  logs=[l for l in logs if l['transactionHash'].lower()==tx]
  row['governance_execution_logs']=logs
  payloads=[l for l in logs if l['address'].lower()==PC and l['topics'][0].lower()==sig('PayloadExecuted(uint40)')]
  if len(payloads)!=1:raise RuntimeError('No unique V3 payload execution linkage; V2 lineage needs separate semantics')
  pid=word(payloads[0]['data'],0);row['payload_id']=pid
  data=rpc(URL,'eth_call',[{'to':PC,'data':sig('getPayloadById(uint40)')[:10]+format(pid,'064x')},hex(bn-1)])
  offset=word(data,0)//32
  state=word(data,offset+2);queued=word(data,offset+4)
  assert state==2 and 0<queued<row['effect_header']['timestamp']
  qb=lower_bound(URL,queued,bn,max(16490000,bn-500000))
  row['payload_queue_header']=block(URL,qb)
  assert row['payload_queue_header']['timestamp']==queued
  qlogs=rpc(URL,'eth_getLogs',[{'address':PC,'fromBlock':hex(qb),'toBlock':hex(qb),'topics':[sig('PayloadQueued(uint40)')]}])
  qlogs=[l for l in qlogs if word(l['data'],0)==pid]
  assert len(qlogs)==1
  row['payload_queue_log']=qlogs[0]
  row['pre_effect_payload_abi_sha256']=digest(data.encode())
  # Read immutable payload target bytecode at queue. Protocol source, never users.
  array_word=offset+word(data,offset+10)//32
  count=word(data,array_word);targets=[]
  assert 0<count<100
  for i in range(count):
   action_word=array_word+1+word(data,array_word+1+i)//32
   target='0x'+format(word(data,action_word),'040x')
   code=rpc(URL,'eth_getCode',[target,hex(qb)])
   assert code!='0x'
   targets.append({'target':target,'queued_code_sha256':digest(code.encode())})
  row.update(status='PAYLOAD_QUEUE_EXECUTION_SOURCE_LINK_PASS_NOT_FULL_SOURCE_GATE',targets=targets,signal_to_effect_seconds=row['effect_header']['timestamp']-queued,earliest_core_approval_status='NOT_YET_PROVED',parameters_known_at_signal_status='BYTECODE_RECOVERED_NOT_YET_REPRODUCED',borrower_reconstruction_status='NOT_YET_PROVED')
 except Exception as e:row['failure']=str(e)
 rows.append(row);print(json.dumps(row),flush=True)
r={'lab_id':'AAVE-GOV-LT-FORCED-DELEVERAGING-001','phase':'SOURCE_LINEAGE_ONLY','prior_source_artifact':10564642712,'probe_clusters':rows,'requests':RECEIPTS,'accepted_fully_defensible_shocks':0,'economic_outcomes_opened':0,'2026_outcomes_opened':False}
(OUT/'GOVERNANCE_LINEAGE_PROBE_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
