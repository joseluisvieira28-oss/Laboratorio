import {DataSourceBuilder} from '@subsquid/evm-stream'
import {id} from 'ethers'
import {createHash} from 'node:crypto'
import {mkdir,writeFile} from 'node:fs/promises'

const RPC='https://eth-mainnet.public.blastapi.io'
const PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
const OUT='artifacts/lcod_block_pinned_active_population_v06.json'
const MIN=24720899,CHUNKS=16
const TOPIC='0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd'
const UAD_SELECTOR=id('getUserAccountData(address)').slice(2,10)
const SPOKES=[
'0x973a023a77420ba610f06b3858ad991df6d85a08','0x58131e79531cab1d52301228d1f7b842f26b9649',
'0xba1b3d55d249692b669a164024a838309b7508af','0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1',
'0x65407b940966954b23dfa3caa5c0702bb42984dc','0x7ec68b5695e803e98a21a9a05d744f28b0a7753d',
'0x94e7a5dcbe816e498b89ab752661904e2f56c485','0xad75ce6354f87f3135ce10621d385d8d1e2562c2',
'0x956d8e0a89cfa3744428c4641b5a53b56167a7f9','0xbf10bdfe177de0336afd7fccf80a904e15386219',
'0x3131fe68c4722e726fe6b2819ed68e514395b9a4','0xe1900480ac69f0b296841cd01cc37546d92f35cd',
'0x774b9655413c34809c1f1b16b654465a89ebe989']
const VALID=new Set(SPOKES)
const sha=s=>createHash('sha256').update(s).digest('hex')
const hx=v=>{const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}
const sleep=ms=>new Promise(r=>setTimeout(r,ms))

async function rpc(payload,retries=5){
 for(let a=0;a<retries;a++){
  try{
   const r=await fetch(RPC,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-ActivePop/0.6'},body:JSON.stringify(payload)})
   const t=await r.text();if(!r.ok)throw new Error('HTTP_'+r.status+':'+t.slice(0,300))
   const x=JSON.parse(t);return x
  }catch(e){if(a===retries-1)throw e;await sleep(500*(a+1))}
 }
}

const finalResp=await rpc({jsonrpc:'2.0',id:1,method:'eth_getBlockByNumber',params:['finalized',false]})
if(finalResp.error||!finalResp.result)throw new Error('FINALIZED_BLOCK_UNAVAILABLE')
const N=parseInt(finalResp.result.number,16),BLOCK_HASH=finalResp.result.hash.toLowerCase()

const total=N-MIN+1,step=Math.ceil(total/CHUNKS),ranges=[]
let from=MIN
for(let i=0;i<CHUNKS;i++){const to=Math.min(N,from+step-1);ranges.push({id:i,from,to});from=to+1;if(from>N)break}

async function streamRange(r){
 const src=new DataSourceBuilder().setPortal(PORTAL)
  .setFields({log:{address:true,topics:true,transactionHash:true}})
  .addLog({where:{address:SPOKES,topic0:[TOPIC]},range:{from:r.from,to:r.to}}).build()
 const pairs=new Set();let events=0,decode=0,batches=0,min=null,max=null
 const canonical=[]
 for await(const batch of src.getStream({from:r.from,to:r.to})){
  batches++
  for(const b of batch.blocks){
   const h=Number(b.header.height);min=min==null?h:Math.min(min,h);max=max==null?h:Math.max(max,h)
   for(const l of b.logs||[]){
    const a=hx(l.address),t=(l.topics||[]).map(hx)
    if(!VALID.has(a)||!t.length||t[0]!==TOPIC)continue
    events++
    if(t.length<4){decode++;continue}
    const user='0x'+t[3].replace(/^0x/,'').slice(-40)
    if(!/^0x[0-9a-f]{40}$/.test(user)){decode++;continue}
    pairs.add(a+'::'+user)
    canonical.push([h,a,user,hx(l.transactionHash)].join('|'))
   }
  }
 }
 canonical.sort()
 return {id:r.id,from:r.from,to:r.to,min,max,events,decode,batches,pairs,stream_sha:sha(canonical.join('\n'))}
}

const chunks=await Promise.all(ranges.map(streamRange))
const allPairs=new Set();for(const c of chunks)for(const p of c.pairs)allPairs.add(p)
const pairs=[...allPairs].sort()
let contiguous=chunks.length===ranges.length
chunks.sort((a,b)=>a.from-b.from)
for(let i=0;i<chunks.length;i++){
 if(chunks[i].min!==chunks[i].from||chunks[i].max!==chunks[i].to)contiguous=false
 if(i&&chunks[i].from!==chunks[i-1].to+1)contiguous=false
}
const decodeErrors=chunks.reduce((s,c)=>s+c.decode,0)

async function classifyBatch(part,offset){
 const req=part.map((p,i)=>{
  const [spoke,user]=p.split('::')
  const data='0x'+UAD_SELECTOR+'0'.repeat(24)+user.slice(2)
  return {jsonrpc:'2.0',id:offset+i+1,method:'eth_call',params:[{to:spoke,data},'0x'+N.toString(16)]}
 })
 const arr=await rpc(req)
 if(!Array.isArray(arr))throw new Error('BATCH_RPC_NON_ARRAY')
 const map=new Map(arr.map(x=>[x.id,x]))
 const out=[]
 for(let i=0;i<part.length;i++){
  const x=map.get(offset+i+1),pair=part[i]
  if(!x||x.error||typeof x.result!=='string'){
   out.push({pair,error:x?.error||'MISSING_RESULT'});continue
  }
  try{
   const h=x.result.replace(/^0x/,'')
   if(h.length<64*7)throw new Error('SHORT_UAD')
   const words=[];for(let j=0;j<7;j++)words.push(BigInt('0x'+h.slice(j*64,(j+1)*64)))
   out.push({pair,debt:words[4],hf:words[2],borrowCount:words[6]})
  }catch(e){out.push({pair,error:e.message})}
 }
 return out
}

const classified=[];const errors=[]
for(let off=0;off<pairs.length;off+=80){
 const part=pairs.slice(off,off+80)
 const rows=await classifyBatch(part,off)
 for(const x of rows){if(x.error)errors.push({pair_sha256:sha(x.pair),error:String(x.error).slice(0,300)});else classified.push(x)}
 await sleep(60)
}
const active=classified.filter(x=>x.debt>0n),inactive=classified.filter(x=>x.debt===0n)
const activeHashes=active.map(x=>sha(x.pair)).sort()
const perSpoke=Object.fromEntries(SPOKES.map(s=>[s,0]))
for(const x of active)perSpoke[x.pair.split('::')[0]]++
const universeHashes=pairs.map(sha).sort()
const pass=contiguous&&decodeErrors===0&&pairs.length>=3650&&errors.length===0&&classified.length===pairs.length&&active.length>0

const receipt={
 lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',
 stage:'BLOCK_PINNED_ACTIVE_POPULATION_V0.6',
 captured_at_utc:new Date().toISOString(),
 classification:pass?'BLOCK_PINNED_ACTIVE_POPULATION_PASS':'BLOCK_PINNED_ACTIVE_POPULATION_BLOCKED',
 ethereum_block_number:N,ethereum_block_hash:BLOCK_HASH,block_tag_policy:'finalized',
 source_prerequisite:'SQD_SDK_PARALLEL_BORROW_UNIVERSE_PASS',
 range_from_block:MIN,range_to_block:N,chunk_count:chunks.length,
 contiguous_complete_coverage:contiguous,borrow_event_count:chunks.reduce((s,c)=>s+c.events,0),
 borrow_decode_error_count:decodeErrors,historical_candidate_pair_count:pairs.length,
 uad_success_count:classified.length,uad_error_count:errors.length,
 active_debt_pair_count:active.length,inactive_pair_count:inactive.length,
 active_plus_inactive_equals_candidates:(active.length+inactive.length)===pairs.length,
 per_spoke_active_debt_pair_count:perSpoke,
 canonical_historical_pair_set_sha256:sha(universeHashes.join('\n')),
 canonical_active_pair_set_sha256:sha(activeHashes.join('\n')),
 active_pair_hash_sample:activeHashes.slice(0,20),
 stream_chunk_summaries:chunks.map(c=>({id:c.id,from:c.from,to:c.to,events:c.events,batches:c.batches,decode_errors:c.decode,stream_sha256:c.stream_sha})),
 uad_errors:errors.slice(0,50),
 raw_wallet_addresses_retained:false,all_uad_calls_block_pinned:true,
 curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false
}
await mkdir('artifacts',{recursive:true});await writeFile(OUT,JSON.stringify(receipt,null,2)+'\n')
console.log(JSON.stringify(receipt,null,2));if(!pass)process.exitCode=2
