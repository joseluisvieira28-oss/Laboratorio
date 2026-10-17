import {DataSourceBuilder} from '@subsquid/evm-stream'
import {id} from 'ethers'
import {createHash} from 'node:crypto'
import {writeFile,mkdir} from 'node:fs/promises'

const FROM=Number(process.env.FROM_BLOCK),TO=Number(process.env.TO_BLOCK),CID=Number(process.env.CHUNK_ID)
const N=Number(process.env.FINAL_BLOCK),EXPECTED_HASH=String(process.env.FINAL_HASH||'').toLowerCase()
const RPC='https://eth-mainnet.public.blastapi.io',PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
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
const VALID=new Set(SPOKES),sha=s=>createHash('sha256').update(s).digest('hex')
const hx=v=>{const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}
const sleep=ms=>new Promise(r=>setTimeout(r,ms))
async function rpc(payload,retries=5){
 for(let a=0;a<retries;a++){
  try{
   const r=await fetch(RPC,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-ActiveChunk/0.8'},body:JSON.stringify(payload)})
   const t=await r.text();if(!r.ok)throw new Error('HTTP_'+r.status+':'+t.slice(0,200));return JSON.parse(t)
  }catch(e){if(a===retries-1)throw e;await sleep(400*(a+1))}
 }
}
const check=await rpc({jsonrpc:'2.0',id:1,method:'eth_getBlockByNumber',params:['0x'+N.toString(16),false]})
if(check.error||!check.result||String(check.result.hash).toLowerCase()!==EXPECTED_HASH)throw new Error('FINAL_BLOCK_HASH_MISMATCH')

const src=new DataSourceBuilder().setPortal(PORTAL)
 .setFields({log:{address:true,topics:true,transactionHash:true}})
 .addLog({where:{address:SPOKES,topic0:[TOPIC]},range:{from:FROM,to:TO}}).build()
const pairs=new Set();let events=0,decode=0,batches=0,min=null,max=null;const canonical=[]
for await(const batch of src.getStream({from:FROM,to:TO})){
 batches++
 for(const b of batch.blocks){
  const h=Number(b.header.height);min=min==null?h:Math.min(min,h);max=max==null?h:Math.max(max,h)
  for(const l of b.logs||[]){
   const a=hx(l.address),t=(l.topics||[]).map(hx)
   if(!VALID.has(a)||!t.length||t[0]!==TOPIC)continue
   events++;if(t.length<4){decode++;continue}
   const user='0x'+t[3].replace(/^0x/,'').slice(-40)
   if(!/^0x[0-9a-f]{40}$/.test(user)){decode++;continue}
   pairs.add(a+'::'+user);canonical.push([h,a,user,hx(l.transactionHash)].join('|'))
  }
 }
}
canonical.sort()
const pairList=[...pairs].sort(),active=[],inactive=[],errors=[]

function decodeUad(pair,x){
 if(!x||x.error||typeof x.result!=='string')return {pair,error:x?.error||'MISSING_RESULT'}
 try{
  const h=x.result.replace(/^0x/,'')
  if(h.length<64*7)throw new Error('SHORT')
  const debt=BigInt('0x'+h.slice(64*4,64*5))
  return {pair,debt}
 }catch(e){return {pair,error:e.message}}
}

async function retryOne(pair,attempts=5){
 const [spoke,user]=pair.split('::')
 const data='0x'+UAD_SELECTOR+'0'.repeat(24)+user.slice(2)
 for(let a=0;a<attempts;a++){
  try{
   const x=await rpc({jsonrpc:'2.0',id:1,method:'eth_call',params:[{to:spoke,data},'0x'+N.toString(16)]},5)
   const row=decodeUad(pair,x)
   if(!row.error)return row
  }catch{}
  await sleep(500*(a+1))
 }
 return {pair,error:'INDIVIDUAL_RETRY_EXHAUSTED'}
}

for(let off=0;off<pairList.length;off+=20){
 const part=pairList.slice(off,off+20)
 const req=part.map((p,i)=>{
  const [spoke,user]=p.split('::'),rid=off+i+1
  return {jsonrpc:'2.0',id:rid,method:'eth_call',params:[{to:spoke,data:'0x'+UAD_SELECTOR+'0'.repeat(24)+user.slice(2)},'0x'+N.toString(16)]}
 })
 let arr
 try{arr=await rpc(req,5)}catch{arr=null}
 const m=Array.isArray(arr)?new Map(arr.map(x=>[x.id,x])):new Map()
 for(let i=0;i<part.length;i++){
  const p=part[i],x=m.get(off+i+1)
  let row=decodeUad(p,x)
  if(row.error)row=await retryOne(p,5)
  if(row.error)errors.push(sha(p)+':RPC_RETRY_EXHAUSTED')
  else (row.debt>0n?active:inactive).push(sha(p))
 }
 await sleep(120)
}
active.sort();inactive.sort()
const pass=min===FROM&&max===TO&&decode===0&&errors.length===0&&(active.length+inactive.length===pairList.length)
const out={stage:'BLOCK_PINNED_ACTIVE_POPULATION_CHUNK_V0.8',chunk_id:CID,from_block:FROM,to_block:TO,
 finalized_block_number:N,finalized_block_hash:EXPECTED_HASH,classification:pass?'ACTIVE_CHUNK_PASS':'ACTIVE_CHUNK_BLOCKED',
 batch_count:batches,borrow_event_count:events,decode_error_count:decode,historical_pair_count:pairList.length,
 active_pair_count:active.length,inactive_pair_count:inactive.length,uad_error_count:errors.length,
 pair_hashes:pairList.map(sha).sort(),active_pair_hashes:active,inactive_pair_hashes:inactive,
 canonical_stream_sha256:sha(canonical.join('\n')),raw_wallet_addresses_retained:false,all_uad_calls_block_pinned:true,
 curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile(`artifacts/lcod_active_population_chunk_${String(CID).padStart(2,'0')}_v08.json`,JSON.stringify(out,null,2)+'\n')
console.log(JSON.stringify({...out,pair_hashes:undefined,active_pair_hashes:undefined,inactive_pair_hashes:undefined},null,2))
if(!pass)process.exitCode=2
