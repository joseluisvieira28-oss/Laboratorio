import {DataSourceBuilder} from '@subsquid/evm-stream'
import {createHash} from 'node:crypto'
import {mkdir,writeFile} from 'node:fs/promises'

const PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
const ADDR='0x973a023a77420ba610f06b3858ad991df6d85a08'
const TOPIC='0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd'
const FIX='0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f'
const FROM=25393769,TO=25403769
const OUT='artifacts/lcod_sqd_sdk_continuation_fixture_v01.json'
const hx=v=>{const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}
const sha=s=>createHash('sha256').update(s).digest('hex')

const src=new DataSourceBuilder()
 .setPortal(PORTAL)
 .setFields({log:{address:true,topics:true,transactionHash:true}})
 .addLog({where:{address:[ADDR],topic0:[TOPIC]},range:{from:FROM,to:TO}})
 .build()

let batches=0,blocks=0,logs=0,fixture=false,min=null,max=null,decodeErrors=0
const rows=[]
for await(const batch of src.getStream({from:FROM,to:TO})){
 batches++
 for(const b of batch.blocks){
  blocks++
  const h=Number(b.header.height)
  min=min==null?h:Math.min(min,h);max=max==null?h:Math.max(max,h)
  for(const l of b.logs||[]){
   const a=hx(l.address);const topics=(l.topics||[]).map(hx)
   if(a!==ADDR||!topics.length||topics[0]!==TOPIC)continue
   logs++
   if(topics.length<4){decodeErrors++;continue}
   const tx=hx(l.transactionHash)
   if(tx===FIX)fixture=true
   rows.push([h,a,topics[3],tx].join('|'))
  }
 }
}
rows.sort()
const pass=batches>=2&&logs>=1&&fixture&&decodeErrors===0
const out={lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',
 stage:'SQD_SDK_CONTINUATION_FIXTURE_V0.1',
 classification:pass?'SQD_SDK_CONTINUATION_PASS':'SQD_SDK_CONTINUATION_BLOCKED',
 sdk:'@subsquid/evm-stream@0.1.5',from_block:FROM,to_block:TO,
 batch_count:batches,stream_block_count:blocks,borrow_log_count:logs,
 min_stream_block:min,max_stream_block:max,fixture_tx_present:fixture,
 decode_error_count:decodeErrors,canonical_sha256:sha(rows.join('\n')),
 market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile(OUT,JSON.stringify(out,null,2)+'\n')
console.log(JSON.stringify(out,null,2))
if(!pass)process.exitCode=2
