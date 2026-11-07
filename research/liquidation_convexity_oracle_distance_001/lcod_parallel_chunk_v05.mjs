import {DataSourceBuilder} from '@subsquid/evm-stream'
import {createHash} from 'node:crypto'
import {mkdir,writeFile} from 'node:fs/promises'

const FROM=Number(process.env.FROM_BLOCK),TO=Number(process.env.TO_BLOCK),ID=Number(process.env.CHUNK_ID)
const PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
const TOPIC='0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd'
const FIX_BLOCK=25398769,FIX_TX='0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f'
const SPOKES={
 BLUECHIP:'0x973a023a77420ba610f06b3858ad991df6d85a08',ETHENA_CORRELATED:'0x58131e79531cab1d52301228d1f7b842f26b9649',
 ETHENA_ECOSYSTEM:'0xba1b3d55d249692b669a164024a838309b7508af',FOREX:'0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1',
 GOLD:'0x65407b940966954b23dfa3caa5c0702bb42984dc',LOMBARD_BTC:'0x7ec68b5695e803e98a21a9a05d744f28b0a7753d',
 MAIN:'0x94e7a5dcbe816e498b89ab752661904e2f56c485',PAXG_GOLD:'0xad75ce6354f87f3135ce10621d385d8d1e2562c2',
 USDG_PENDLE:'0x956d8e0a89cfa3744428c4641b5a53b56167a7f9',ETHERFI_ESPOKE:'0xbf10bdfe177de0336afd7fccf80a904e15386219',
 KELP_ESPOKE:'0x3131fe68c4722e726fe6b2819ed68e514395b9a4',LIDO_ESPOKE:'0xe1900480ac69f0b296841cd01cc37546d92f35cd',
 USDG_MAPLE_ESPOKE:'0x774b9655413c34809c1f1b16b654465a89ebe989'}
const ADDRS=Object.values(SPOKES),VALID=new Set(ADDRS),NAMES=Object.fromEntries(Object.entries(SPOKES).map(([k,v])=>[v,k]))
const sha=s=>createHash('sha256').update(s).digest('hex')
const hx=v=>{const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}

const src=new DataSourceBuilder().setPortal(PORTAL)
 .setFields({log:{address:true,topics:true,transactionHash:true}})
 .addLog({where:{address:ADDRS,topic0:[TOPIC]},range:{from:FROM,to:TO}}).build()

let batches=0,blocks=0,events=0,decodeErrors=0,min=null,max=null,fixture=false
const pairs=new Set(),spokeCounts=Object.fromEntries(Object.keys(SPOKES).map(k=>[k,0])),canonical=[]
for await(const batch of src.getStream({from:FROM,to:TO})){
 batches++
 for(const b of batch.blocks){
  blocks++;const h=Number(b.header.height);min=min==null?h:Math.min(min,h);max=max==null?h:Math.max(max,h)
  for(const l of b.logs||[]){
   const a=hx(l.address),t=(l.topics||[]).map(hx)
   if(!VALID.has(a)||!t.length||t[0]!==TOPIC)continue
   events++;if(NAMES[a])spokeCounts[NAMES[a]]++
   if(t.length<4){decodeErrors++;continue}
   const user='0x'+t[3].replace(/^0x/,'').slice(-40);if(!/^0x[0-9a-f]{40}$/.test(user)){decodeErrors++;continue}
   const tx=hx(l.transactionHash);if(tx===FIX_TX)fixture=true
   pairs.add(sha(a+'::'+user));canonical.push([h,a,user,tx].join('|'))
  }
 }
}
canonical.sort()
const pass=decodeErrors===0&&min===FROM&&max===TO
const out={stage:'SQD_SDK_PARALLEL_CHUNK_V0.5',chunk_id:ID,from_block:FROM,to_block:TO,
 classification:pass?'CHUNK_PASS':'CHUNK_BLOCKED',sdk:'@subsquid/evm-stream@0.1.5',
 batch_count:batches,stream_block_count:blocks,min_stream_block:min,max_stream_block:max,
 borrow_event_count:events,borrow_event_count_by_spoke:spokeCounts,decode_error_count:decodeErrors,
 unique_pair_count:pairs.size,pair_hashes:[...pairs].sort(),fixture_expected_in_chunk:FROM<=FIX_BLOCK&&FIX_BLOCK<=TO,
 fixture_tx_present:fixture,canonical_stream_sha256:sha(canonical.join('\n')),
 raw_wallet_addresses_retained:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile(`artifacts/lcod_parallel_chunk_${String(ID).padStart(2,'0')}_v05.json`,JSON.stringify(out,null,2)+'\n')
console.log(JSON.stringify({...out,pair_hashes:undefined},null,2));if(!pass)process.exitCode=2
