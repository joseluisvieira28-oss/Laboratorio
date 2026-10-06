#!/usr/bin/env python3
"""Independent public archival protocol-state capability, no borrower outcomes."""
import json
from source_probe_v01 import OUT, RECEIPTS, END_TS, rpc, block, sig, digest

PROBES = [
 ('ethereum', 'https://eth.drpc.org', 21525890, '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'),
 ('ethereum', 'https://eth.llamarpc.com', 21525890, '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'),
 ('ethereum', 'https://eth-mainnet.g.alchemy.com/public', 21525890, '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'),
 ('polygon', 'https://polygon.drpc.org', 64000000, '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('avalanche', 'https://avalanche.drpc.org', 30000000, '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('arbitrum', 'https://arbitrum.drpc.org', 280000000, '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('optimism', 'https://optimism.drpc.org', 130000000, '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('base', 'https://base.drpc.org', 25000000, '0xa238dd80c259a72e81d7e4664a9801593f98d1c5'),
]
rows=[]
for name,url,bn,pool in PROBES:
 row={'network':name,'url':url,'block':bn,'status':'SOURCE_BLOCKED'}
 try:
  row['header']=block(url,bn)
  assert row['header']['timestamp']<=END_TS
  data=rpc(url,'eth_call',[{'to':pool,'data':sig('getReservesList()')[:10]},hex(bn)])
  assert len(data)>=130 and int(data[2:66],16)==32
  count=int(data[66:130],16)
  assert 0<count<1000 and len(data)==130+count*64
  row.update(status='HISTORICAL_RESERVES_ENUMERATION_PASS',reserve_count=count,abi_sha256=digest(data.encode()))
 except Exception as e:row['failure']=str(e)
 rows.append(row);print(json.dumps(row),flush=True)
r={'phase':'SOURCE_CAPABILITY_ONLY','probes':rows,'requests':RECEIPTS,'economic_outcomes_opened':0,'borrower_behavior_opened':False,'2026_outcomes_opened':False,'warning':'A single protocol-state read does not prove full historical borrower reconstruction or SOURCE_GATE_PASS.'}
(OUT/'ARCHIVE_FALLBACK_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
