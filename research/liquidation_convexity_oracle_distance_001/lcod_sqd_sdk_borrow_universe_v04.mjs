import {DataSourceBuilder} from '@subsquid/evm-stream'
import {createHash} from 'node:crypto'
import {writeFile, mkdir} from 'node:fs/promises'

const MCP='https://mcp.aave.com/'
const RPC='https://eth-mainnet.public.blastapi.io'
const PORTAL='https://portal.sqd.dev/datasets/ethereum-mainnet'
const OUT='artifacts/lcod_sqd_sdk_borrow_universe_v04.json'
const TOPIC='0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd'
const FIXTURE_TX='0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f'

const SPOKES={
 BLUECHIP:['0x973a023a77420ba610f06b3858ad991df6d85a08',24720920],
 ETHENA_CORRELATED:['0x58131e79531cab1d52301228d1f7b842f26b9649',24720926],
 ETHENA_ECOSYSTEM:['0xba1b3d55d249692b669a164024a838309b7508af',24720923],
 FOREX:['0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1',24720917],
 GOLD:['0x65407b940966954b23dfa3caa5c0702bb42984dc',24720914],
 LOMBARD_BTC:['0x7ec68b5695e803e98a21a9a05d744f28b0a7753d',24720911],
 MAIN:['0x94e7a5dcbe816e498b89ab752661904e2f56c485',24720899],
 PAXG_GOLD:['0xad75ce6354f87f3135ce10621d385d8d1e2562c2',25883381],
 USDG_PENDLE:['0x956d8e0a89cfa3744428c4641b5a53b56167a7f9',25094394],
 ETHERFI_ESPOKE:['0xbf10bdfe177de0336afd7fccf80a904e15386219',24720905],
 KELP_ESPOKE:['0x3131fe68c4722e726fe6b2819ed68e514395b9a4',24720908],
 LIDO_ESPOKE:['0xe1900480ac69f0b296841cd01cc37546d92f35cd',24720902],
 USDG_MAPLE_ESPOKE:['0x774b9655413c34809c1f1b16b654465a89ebe989',25594472],
}
const ADDRS=Object.values(SPOKES).map(x=>x[0])
const VALID=new Set(ADDRS)
const MIN_BLOCK=Math.min(...Object.values(SPOKES).map(x=>x[1]))

function sha(s){return createHash('sha256').update(s).digest('hex')}\nfunction hx(v){const s=String(v||'').toLowerCase();return s.startsWith('0x')?s:'0x'+s}
function walk(v,out=[]){
 if(Array.isArray(v)){for(const z of v) walk(z,out)}
 else if(v && typeof v==='object'){out.push(v); for(const z of Object.values(v)) walk(z,out)}
 return out
}
async function jsonPost(url,payload){
 const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-SQDSDK/0.4'},body:JSON.stringify(payload)})
 const text=await r.text()
 if(!r.ok) throw new Error('HTTP_'+r.status+':'+text.slice(0,500))
 const x=JSON.parse(text); if(x.error) throw new Error(JSON.stringify(x.error))
 return x.result
}
function unwrap(x){
 if(x && typeof x==='object' && x.structuredContent!=null){
  const y=x.structuredContent; return y && typeof y==='object' && 'data' in y ? y.data : y
 }
 if(x && typeof x==='object' && Array.isArray(x.content)){
  for(const c of x.content){
   if(c && c.type==='text'){
    try{const y=JSON.parse(c.text||''); return y && typeof y==='object' && 'data' in y ? y.data : y}catch{}
   }
  }
 }
 return x && typeof x==='object' && 'data' in x ? x.data : x
}
async function tool(name,args){
 return unwrap(await jsonPost(MCP,{jsonrpc:'2.0',id:1,method:'tools/call',params:{name,arguments:args}}))
}
function decodeReserveId(s){
 try{
  const raw=Buffer.from(s,'base64').toString('utf8')
  const [chain,spoke,rid]=raw.split('::')
  if(chain!=='1'||!/^(0x)?[0-9a-fA-F]{40}$/.test(spoke)) return null
  return [spoke.toLowerCase(),Number(rid),s]
 }catch{return null}
}
function holderAddresses(x){
 const out=new Set()
 for(const d of walk(x,[])){
  for(const k of ['user','address','wallet']){
   const v=d[k]
   if(typeof v==='string' && /^0x[0-9a-fA-F]{40}$/.test(v)) out.add(v.toLowerCase())
  }
 }
 return out
}

// 1. Current MCP contradiction set first.
const currentPairs=new Set()
const mcpErrors=[]
let mcpPages=0
const markets=await tool('get_markets',{version:'v4',chainId:1})
const opaque=[...new Set(walk(markets,[]).map(d=>d.reserveId).filter(x=>typeof x==='string'))].sort()
const decoded=opaque.map(decodeReserveId).filter(Boolean).filter(x=>VALID.has(x[0]))
for(const [spoke,rid,opaqueId] of decoded){
 let cursor=null; const seen=new Set()
 for(let i=0;i<200;i++){
  const args={reserveId:opaqueId,side:'borrow',limit:50,version:'v4'}
  if(cursor) args.cursor=cursor
  let page
  try{page=await tool('get_reserve_holders',args)}catch(e){mcpErrors.push(spoke+':'+rid+':'+e.name);break}
  mcpPages++
  for(const u of holderAddresses(page)) currentPairs.add(spoke+'::'+u)
  const curs=[...new Set(walk(page,[]).map(d=>d.nextCursor||d.next_cursor).filter(x=>typeof x==='string'&&x.trim()).map(x=>x.trim()))]
  if(curs.length===0) break
  if(curs.length!==1 || seen.has(curs[0])){mcpErrors.push(spoke+':'+rid+':CURSOR');break}
  seen.add(curs[0]);cursor=curs[0]
 }
}

// 2. Latest block strictly after MCP enumeration.
const latestHex=await jsonPost(RPC,{jsonrpc:'2.0',id:1,method:'eth_blockNumber',params:[]})
const L=parseInt(latestHex,16)

// 3. Consume full SQD stream using official SDK.
const source=new DataSourceBuilder()
 .setPortal(PORTAL)
 .setFields({log:{address:true,topics:true,transactionHash:true}})
 .addLog({where:{address:ADDRS,topic0:[TOPIC]},range:{from:MIN_BLOCK,to:L}})
 .build()

const eventPairs=new Set()
const spokeCounts=Object.fromEntries(Object.keys(SPOKES).map(k=>[k,0]))
const addrName=Object.fromEntries(Object.entries(SPOKES).map(([k,v])=>[v[0],k]))
let eventCount=0,decodeErrors=0,batchCount=0,blockCount=0,fixturePresent=false
let minSeen=null,maxSeen=null
const canonical=[]
for await (const batch of source.getStream()){
 batchCount++
 for(const block of batch.blocks){
  blockCount++
  const height=Number(block.header.height)
  if(minSeen==null||height<minSeen) minSeen=height
  if(maxSeen==null||height>maxSeen) maxSeen=height
  for(const log of block.logs||[]){
   const addr=hx(log.address)
   const topics=(log.topics||[]).map(hx)
   if(!VALID.has(addr)||topics.length===0||topics[0]!==TOPIC) continue
   eventCount++
   if(addrName[addr]) spokeCounts[addrName[addr]]++
   if(topics.length<4){decodeErrors++;continue}
   const raw=topics[3].replace(/^0x/,'')
   const user='0x'+raw.slice(-40)
   if(!/^0x[0-9a-f]{40}$/.test(user)){decodeErrors++;continue}
   eventPairs.add(addr+'::'+user)
   const tx=hx(log.transactionHash)
   if(tx===FIXTURE_TX) fixturePresent=true
   canonical.push([height,addr,user,tx].join('|'))
  }
 }
}
canonical.sort()
const missing=[...currentPairs].filter(x=>!eventPairs.has(x)).sort()
const coverage=currentPairs.size ? (currentPairs.size-missing.length)/currentPairs.size : 0
const passed=eventCount>0 && fixturePresent && decodeErrors===0 && mcpErrors.length===0 && coverage===1.0

const receipt={
 lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',
 stage:'SQD_SDK_BORROW_UNIVERSE_V0.4',
 captured_at_utc:new Date().toISOString(),
 classification:passed?'SQD_SDK_BORROW_UNIVERSE_PASS':'SQD_SDK_BORROW_UNIVERSE_BLOCKED',
 sqd_sdk:'@subsquid/evm-stream@0.1.5',
 portal:PORTAL,range_from_block:MIN_BLOCK,range_to_latest_block:L,
 query_spoke_count:ADDRS.length,batch_count:batchCount,stream_block_count:blockCount,
 min_stream_block:minSeen,max_stream_block:maxSeen,
 borrow_event_count:eventCount,borrow_event_count_by_spoke:spokeCounts,
 unique_event_pair_count:eventPairs.size,event_decode_error_count:decodeErrors,
 truth_fixture_tx_present:fixturePresent,
 current_mcp_pair_count:currentPairs.size,mcp_pages:mcpPages,mcp_errors:mcpErrors,
 current_mcp_covered_count:currentPairs.size-missing.length,current_mcp_coverage:coverage,
 missing_current_mcp_pair_count:missing.length,
 missing_current_mcp_pair_sha256:missing.slice(0,100).map(sha),
 canonical_event_stream_sha256:sha(canonical.join('\n')),
 raw_wallet_addresses_retained:false,
 curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false
}
await mkdir('artifacts',{recursive:true})
await writeFile(OUT,JSON.stringify(receipt,null,2)+'\n')
console.log(JSON.stringify({...receipt,missing_current_mcp_pair_sha256:undefined},null,2))
if(!passed) process.exitCode=2
