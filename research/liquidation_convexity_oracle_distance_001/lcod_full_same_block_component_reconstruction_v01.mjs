import {DataSourceBuilder} from '@subsquid/evm-stream'
import {Interface} from 'ethers'
import {createHash} from 'node:crypto'
import {readFile,writeFile,mkdir} from 'node:fs/promises'

const RPC='https://eth-mainnet.public.blastapi.io'
const PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
const CANON_PATH='research/liquidation_convexity_oracle_distance_001/LCOD_BLOCK_PINNED_ACTIVE_POPULATION_RECEIPT.json'
const OUT='artifacts/lcod_full_same_block_component_reconstruction_v01.json'
const MIN=24720899,K=16,TOL_NUM=5n,TOL_DEN=100000n // 5e-5
const RAY=10n**27n,BPS_TO_WAD=10n**14n
const TOPIC='0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd'
const SPOKES=[
'0x973a023a77420ba610f06b3858ad991df6d85a08','0x58131e79531cab1d52301228d1f7b842f26b9649',
'0xba1b3d55d249692b669a164024a838309b7508af','0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1',
'0x65407b940966954b23dfa3caa5c0702bb42984dc','0x7ec68b5695e803e98a21a9a05d744f28b0a7753d',
'0x94e7a5dcbe816e498b89ab752661904e2f56c485','0xad75ce6354f87f3135ce10621d385d8d1e2562c2',
'0x956d8e0a89cfa3744428c4641b5a53b56167a7f9','0xbf10bdfe177de0336afd7fccf80a904e15386219',
'0x3131fe68c4722e726fe6b2819ed68e514395b9a4','0xe1900480ac69f0b296841cd01cc37546d92f35cd',
'0x774b9655413c34809c1f1b16b654465a89ebe989']
const VALID=new Set(SPOKES),sha=s=>createHash('sha256').update(s).digest('hex')
const hx=v=>{const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}
const sleep=ms=>new Promise(r=>setTimeout(r,ms))

const spokeI=new Interface([
 'function getReserveCount() view returns (uint256)',
 'function ORACLE() view returns (address)',
 'function getUserAccountData(address) view returns ((uint256 riskPremium,uint256 avgCollateralFactor,uint256 healthFactor,uint256 totalCollateralValue,uint256 totalDebtValueRay,uint256 activeCollateralCount,uint256 borrowCount))',
 'function getUserReserveStatus(uint256,address) view returns (bool,bool)',
 'function getReserve(uint256) view returns ((address underlying,address hub,uint16 assetId,uint8 decimals,uint24 collateralRisk,uint8 flags,uint32 dynamicConfigKey))',
 'function getUserPosition(uint256,address) view returns ((uint120 drawnShares,uint120 premiumShares,int200 premiumOffsetRay,uint120 suppliedShares,uint32 dynamicConfigKey))',
 'function getUserSuppliedAssets(uint256,address) view returns (uint256)',
 'function getDynamicReserveConfig(uint256,uint32) view returns ((uint16 collateralFactor,uint32 maxLiquidationBonus,uint16 liquidationFee))',
 'function getUserPremiumDebtRay(uint256,address) view returns (uint256)'
])
const oracleI=new Interface(['function getReservePrice(uint256) view returns (uint256)'])
const hubI=new Interface(['function getAssetDrawnIndex(uint256) view returns (uint256)'])

const canon=JSON.parse(await readFile(CANON_PATH,'utf8'))
if(canon.classification!=='BLOCK_PINNED_ACTIVE_POPULATION_PASS')throw new Error('ACTIVE_POPULATION_PREREQUISITE_NOT_PASS')
const N=Number(canon.ethereum_block_number),BLOCK_HASH=String(canon.ethereum_block_hash).toLowerCase()
const EXPECTED_ACTIVE=Number(canon.active_debt_pair_count),EXPECTED_SHA=String(canon.canonical_active_pair_set_sha256)
const blockTag='0x'+N.toString(16)

async function rpc(payload,retries=7){
 let last
 for(let a=0;a<retries;a++){
  try{
   const r=await fetch(RPC,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-Components/0.1'},body:JSON.stringify(payload)})
   const t=await r.text();if(!r.ok)throw new Error('HTTP_'+r.status+':'+t.slice(0,250))
   return JSON.parse(t)
  }catch(e){last=e;await sleep(Math.min(500*2**a,8000))}
 }
 throw last
}
async function ethCall(to,data){
 const x=await rpc({jsonrpc:'2.0',id:1,method:'eth_call',params:[{to,data},blockTag]})
 if(x.error||typeof x.result!=='string')throw new Error('ETH_CALL:'+JSON.stringify(x.error||'MISSING'))
 return x.result
}
async function callIface(iface,to,fn,args=[]){
 const raw=await ethCall(to,iface.encodeFunctionData(fn,args))
 return iface.decodeFunctionResult(fn,raw)
}

const check=await rpc({jsonrpc:'2.0',id:1,method:'eth_getBlockByNumber',params:[blockTag,false]})
if(check.error||!check.result||String(check.result.hash).toLowerCase()!==BLOCK_HASH)throw new Error('CANONICAL_BLOCK_HASH_MISMATCH')

// 1) Re-stream canonical Borrow history sequentially, wallets memory-only.
const total=N-MIN+1,step=Math.ceil(total/K),ranges=[];let f=MIN
for(let id=0;id<K;id++){const to=Math.min(N,f+step-1);ranges.push({id,from:f,to});f=to+1;if(f>N)break}
const pairSet=new Set(),chunkEvidence=[];let decodeErrors=0,totalEvents=0
for(const rr of ranges){
 const src=new DataSourceBuilder().setPortal(PORTAL)
  .setFields({log:{address:true,topics:true,transactionHash:true}})
  .addLog({where:{address:SPOKES,topic0:[TOPIC]},range:{from:rr.from,to:rr.to}}).build()
 let min=null,max=null,events=0,batches=0;const canonical=[]
 for await(const batch of src.getStream({from:rr.from,to:rr.to})){
  batches++
  for(const b of batch.blocks){
   const h=Number(b.header.height);min=min==null?h:Math.min(min,h);max=max==null?h:Math.max(max,h)
   for(const l of b.logs||[]){
    const a=hx(l.address),t=(l.topics||[]).map(hx)
    if(!VALID.has(a)||!t.length||t[0]!==TOPIC)continue
    events++;totalEvents++
    if(t.length<4){decodeErrors++;continue}
    const user='0x'+t[3].replace(/^0x/,'').slice(-40)
    if(!/^0x[0-9a-f]{40}$/.test(user)){decodeErrors++;continue}
    pairSet.add(a+'::'+user);canonical.push([h,a,user,hx(l.transactionHash)].join('|'))
   }
  }
 }
 if(min!==rr.from||max!==rr.to)throw new Error('SQD_RANGE_INCOMPLETE:'+rr.id+':'+min+':'+max)
 canonical.sort();chunkEvidence.push({id:rr.id,from:rr.from,to:rr.to,events,batches,stream_sha256:sha(canonical.join('\n'))})
 await sleep(800)
}
if(decodeErrors)throw new Error('BORROW_DECODE_ERRORS:'+decodeErrors)
const pairs=[...pairSet].sort()

// Small batch helper with individual fallback.
async function batchRaw(calls){
 const req=calls.map((c,i)=>({jsonrpc:'2.0',id:i+1,method:'eth_call',params:[{to:c.to,data:c.data},blockTag]}))
 let arr
 try{arr=await rpc(req,7)}catch{arr=null}
 const map=Array.isArray(arr)?new Map(arr.map(x=>[x.id,x])):new Map()
 const out=[]
 for(let i=0;i<calls.length;i++){
  let x=map.get(i+1)
  if(!x||x.error||typeof x.result!=='string'){
   try{x=await rpc({jsonrpc:'2.0',id:1,method:'eth_call',params:[{to:calls[i].to,data:calls[i].data},blockTag]},7)}
   catch(e){out.push({error:'RPC_RETRY_EXHAUSTED'});continue}
  }
  if(!x||x.error||typeof x.result!=='string')out.push({error:'RPC_ERROR'})
  else out.push({raw:x.result})
 }
 return out
}

// 2) Reproduce exact canonical active set and cache official UAD.
const uadByPair=new Map(),activePairs=[]
for(let off=0;off<pairs.length;off+=20){
 const part=pairs.slice(off,off+20)
 const calls=part.map(p=>{const [spoke,user]=p.split('::');return{to:spoke,data:spokeI.encodeFunctionData('getUserAccountData',[user])}})
 const raws=await batchRaw(calls)
 for(let i=0;i<part.length;i++){
  if(raws[i].error)throw new Error('UAD_REPRODUCTION_ERROR:'+sha(part[i]))
  const d=spokeI.decodeFunctionResult('getUserAccountData',raws[i].raw)[0]
  const row={riskPremium:BigInt(d.riskPremium),avgCollateralFactor:BigInt(d.avgCollateralFactor),healthFactor:BigInt(d.healthFactor),
             totalCollateralValue:BigInt(d.totalCollateralValue),totalDebtValueRay:BigInt(d.totalDebtValueRay),
             activeCollateralCount:BigInt(d.activeCollateralCount),borrowCount:BigInt(d.borrowCount)}
  uadByPair.set(part[i],row);if(row.totalDebtValueRay>0n)activePairs.push(part[i])
 }
 await sleep(100)
}
activePairs.sort()
const activeHashes=activePairs.map(sha).sort()
const reproducedSha=sha(activeHashes.join('\n'))
if(activePairs.length!==EXPECTED_ACTIVE||reproducedSha!==EXPECTED_SHA)throw new Error('ACTIVE_SET_MISMATCH:'+activePairs.length+':'+reproducedSha)

// 3) Block-N static reserve/oracle/index caches.
const staticBySpoke=new Map()
for(const spoke of SPOKES){
 const [cntR,orR]=await Promise.all([
  callIface(spokeI,spoke,'getReserveCount'),
  callIface(spokeI,spoke,'ORACLE')
 ])
 const count=Number(cntR[0]),oracle=String(orR[0]).toLowerCase(),reserves=[]
 for(let rid=0;rid<count;rid++){
  const reserve=(await callIface(spokeI,spoke,'getReserve',[rid]))[0]
  const price=BigInt((await callIface(oracleI,oracle,'getReservePrice',[rid]))[0])
  const hub=String(reserve.hub).toLowerCase(),assetId=BigInt(reserve.assetId),decimals=Number(reserve.decimals)
  const drawnIndex=BigInt((await callIface(hubI,hub,'getAssetDrawnIndex',[assetId]))[0])
  reserves.push({rid,hub,assetId,decimals,price,drawnIndex})
 }
 staticBySpoke.set(spoke,{count,oracle,reserves})
}

// 4) Exact same-block component reconstruction.
const rows=[],reasonCount={};let totalDebt=0n,includedDebt=0n
function exclude(pair,uad,reason){
 reasonCount[reason]=(reasonCount[reason]||0)+1
 rows.push({pair_sha256:sha(pair),status:'EXCLUDED',reason,official_total_debt_value_ray:uad.totalDebtValueRay.toString(),
            official_health_factor_wad:uad.healthFactor.toString()})
}
for(let idx=0;idx<activePairs.length;idx++){
 const pair=activePairs[idx],[spoke,user]=pair.split('::'),uad=uadByPair.get(pair),st=staticBySpoke.get(spoke)
 totalDebt+=uad.totalDebtValueRay
 try{
  const statusCalls=st.reserves.map(r=>({to:spoke,data:spokeI.encodeFunctionData('getUserReserveStatus',[r.rid,user])}))
  const statusRaw=await batchRaw(statusCalls)
  if(statusRaw.some(x=>x.error)){exclude(pair,uad,'STATUS_READ_ERROR');continue}
  const activeLegs=[]
  for(let j=0;j<st.reserves.length;j++){
   const [collateral,borrowing]=spokeI.decodeFunctionResult('getUserReserveStatus',statusRaw[j].raw)
   if(collateral||borrowing)activeLegs.push({...st.reserves[j],collateral:Boolean(collateral),borrowing:Boolean(borrowing)})
  }
  let weighted=0n,reconDebt=0n,collCount=0,borrowCount=0
  for(const leg of activeLegs){
   const pos=(await callIface(spokeI,spoke,'getUserPosition',[leg.rid,user]))[0]
   const userKey=BigInt(pos.dynamicConfigKey),drawnShares=BigInt(pos.drawnShares)
   const scale=10n**BigInt(18-leg.decimals)
   if(leg.collateral){
    const supplied=BigInt((await callIface(spokeI,spoke,'getUserSuppliedAssets',[leg.rid,user]))[0])
    const cfg=(await callIface(spokeI,spoke,'getDynamicReserveConfig',[leg.rid,userKey]))[0]
    const cf=BigInt(cfg.collateralFactor)
    if(cf>0n&&supplied>0n){
      const value=supplied*leg.price*scale
      weighted+=cf*value;collCount++
    }
   }
   if(leg.borrowing){
    const premium=BigInt((await callIface(spokeI,spoke,'getUserPremiumDebtRay',[leg.rid,user]))[0])
    const debtRay=drawnShares*leg.drawnIndex+premium
    reconDebt+=debtRay*leg.price*scale;borrowCount++
   }
  }
  if(reconDebt!==uad.totalDebtValueRay){exclude(pair,uad,'DEBT_MISMATCH');continue}
  if(reconDebt<=0n){exclude(pair,uad,'ZERO_RECON_DEBT');continue}
  const reconHf=(weighted*BPS_TO_WAD*RAY)/reconDebt
  const diff=reconHf>=uad.healthFactor?reconHf-uad.healthFactor:uad.healthFactor-reconHf
  const hfPass=(uad.healthFactor>0n && diff*TOL_DEN<=uad.healthFactor*TOL_NUM)
  if(!hfPass){exclude(pair,uad,'HF_TOLERANCE_FAIL');continue}
  includedDebt+=uad.totalDebtValueRay
  rows.push({pair_sha256:sha(pair),status:'INCLUDED',reason:null,
    official_total_debt_value_ray:uad.totalDebtValueRay.toString(),reconstructed_total_debt_value_ray:reconDebt.toString(),
    official_health_factor_wad:uad.healthFactor.toString(),reconstructed_health_factor_wad:reconHf.toString(),
    weighted_collateral_bps_value:weighted.toString(),active_collateral_count:collCount,borrow_count:borrowCount})
 }catch(e){exclude(pair,uad,'COMPONENT_READ_OR_DECODE_ERROR')}
 if((idx+1)%50===0){console.log(JSON.stringify({progress:idx+1,total:activePairs.length,included:rows.filter(x=>x.status==='INCLUDED').length}));await sleep(150)}
}
rows.sort((a,b)=>a.pair_sha256.localeCompare(b.pair_sha256))
const included=rows.filter(x=>x.status==='INCLUDED').length
const countNum=BigInt(included),countDen=BigInt(activePairs.length)
const countPass=countNum*100n>=countDen*90n
const debtPass=includedDebt*100n>=totalDebt*90n
const pass=countPass&&debtPass&&rows.length===activePairs.length
const receipt={
 lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',stage:'FULL_SAME_BLOCK_COMPONENT_RECONSTRUCTION_V0.1',
 captured_at_utc:new Date().toISOString(),classification:pass?'FULL_SAME_BLOCK_COMPONENT_PASS':'FULL_SAME_BLOCK_COMPONENT_BLOCKED',
 ethereum_block_number:N,ethereum_block_hash:BLOCK_HASH,active_population_count:activePairs.length,
 canonical_active_pair_set_sha256:EXPECTED_SHA,reproduced_active_pair_set_sha256:reproducedSha,active_set_match:reproducedSha===EXPECTED_SHA,
 historical_candidate_pair_count:pairs.length,borrow_event_count:totalEvents,borrow_decode_error_count:decodeErrors,
 included_pair_count:included,excluded_pair_count:activePairs.length-included,
 count_coverage:Number(countNum*1000000n/countDen)/1000000,
 total_active_debt_value_ray:totalDebt.toString(),included_debt_value_ray:includedDebt.toString(),
 debt_coverage:Number(includedDebt*1000000n/totalDebt)/1000000,
 exclusion_reason_counts:reasonCount,frozen_hf_relative_tolerance:0.00005,
 exact_debt_equality_required:true,all_scientific_calls_block_pinned:true,
 value_units:'1e26 Value = 1 USD; debt values are ValueRay',rows,stream_chunk_evidence:chunkEvidence,
 raw_wallet_addresses_retained:false,curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false
}
await mkdir('artifacts',{recursive:true});await writeFile(OUT,JSON.stringify(receipt,null,2)+'\n')
console.log(JSON.stringify({...receipt,rows:undefined,stream_chunk_evidence:undefined},null,2))
if(!pass)process.exitCode=2
