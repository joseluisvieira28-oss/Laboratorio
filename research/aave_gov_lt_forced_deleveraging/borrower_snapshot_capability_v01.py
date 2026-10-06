#!/usr/bin/env python3
"""Historical PRE-SIGNAL borrower snapshot capability. No in-window behavior."""
import json
from source_probe_v01 import OUT, RECEIPTS, rpc, sig, block, digest
URL='https://eth-mainnet.g.alchemy.com/public'
POOL='0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'
ASSET='0x6b175474e89094c44da98b954eedeac495271d0f'
SNAPSHOT=19620892  # Proposal 71's first Core queue block minus one.
def word(s,i):return int(s[2+i*64:2+(i+1)*64],16)
def call(to,name,argument):return rpc(URL,'eth_call',[{'to':to,'data':sig(name)[:10]+argument},hex(SNAPSHOT)])
r={'phase':'PRE_SIGNAL_SOURCE_CAPABILITY_ONLY','snapshot_block':SNAPSHOT,'status':'SOURCE_BLOCKED','full_borrower_census_proved':False,'economic_outcomes_opened':0,'behavior_window_opened':False,'2026_outcomes_opened':False}
try:
 r['snapshot_header']=block(URL,SNAPSHOT)
 # The identity-only source window is January 2023, before every known
 # eligible Ethereum governance shock in the independently audited census.
 query={'address':POOL,'fromBlock':hex(16498100),'toBlock':hex(16498199),'topics':[sig('Borrow(address,address,address,uint256,uint8,uint256,uint16)')]}
 logs=rpc(URL,'eth_getLogs',[query])
 assert logs
 first=min(logs,key=lambda l:(int(l['blockNumber'],16),int(l['logIndex'],16)))
 borrower='0x'+first['topics'][2][-40:]
 r['borrower_identity_source']={'block':int(first['blockNumber'],16),'transaction_hash':first['transactionHash'],'log_index':int(first['logIndex'],16),'borrower':borrower}
 arg=borrower[2:].zfill(64)
 account=call(POOL,'getUserAccountData(address)',arg)
 flags=call(POOL,'getUserConfiguration(address)',arg)
 emode=call(POOL,'getUserEMode(address)',arg)
 reserve=call(POOL,'getReserveData(address)',ASSET[2:].zfill(64))
 assert len(account)==386 and len(flags)==66 and len(emode)==66 and len(reserve)>=962
 # 2024 legacy V3 ReserveData ABI: aToken slot8, stableDebtToken slot9,
 # variableDebtToken slot10; first verify all return words are addresses.
 tokens={name:'0x'+format(word(reserve,i),'040x') for name,i in [('aToken',8),('stableDebtToken',9),('variableDebtToken',10)]}
 balances={}
 for name,target in tokens.items():
  if target=='0x'+'0'*40:balances[name]={'status':'ABSENT_TOKEN'};continue
  data=call(target,'balanceOf(address)',arg);assert len(data)==66
  balances[name]={'abi_sha256':digest(data.encode()),'balance_raw':str(word(data,0))}
 r.update(status='HISTORICAL_PRE_SIGNAL_GETTER_CAPABILITY_PASS_NOT_FULL_RECONSTRUCTION',reserve_asset=ASSET,account_abi_sha256=digest(account.encode()),configuration_abi_sha256=digest(flags.encode()),emode_abi_sha256=digest(emode.encode()),reserve_abi_sha256=digest(reserve.encode()),token_contracts=tokens,balances=balances,projected_hf_computed=False,oracle_prices_opened=False)
except Exception as e:r['failure']=str(e)
r['requests']=RECEIPTS
(OUT/'BORROWER_SNAPSHOT_CAPABILITY_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='requests'}),flush=True)
