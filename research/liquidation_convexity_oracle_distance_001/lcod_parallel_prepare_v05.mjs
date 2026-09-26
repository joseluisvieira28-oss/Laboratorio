import {createHash} from 'node:crypto'
import {mkdir,writeFile,appendFile} from 'node:fs/promises'

const MCP='https://mcp.aave.com/'
const RPC='https://eth-mainnet.public.blastapi.io'
const OUT='artifacts/lcod_parallel_prepare_v05.json'
const MIN_BLOCK=24720899
const CHUNKS=16
const SPOKES=new Set([
'0x973a023a77420ba610f06b3858ad991df6d85a08','0x58131e79531cab1d52301228d1f7b842f26b9649',
'0xba1b3d55d249692b669a164024a838309b7508af','0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1',
'0x65407b940966954b23dfa3caa5c0702bb42984dc','0x7ec68b5695e803e98a21a9a05d744f28b0a7753d',
'0x94e7a5dcbe816e498b89ab752661904e2f56c485','0xad75ce6354f87f3135ce10621d385d8d1e2562c2',
'0x956d8e0a89cfa3744428c4641b5a53b56167a7f9','0xbf10bdfe177de0336afd7fccf80a904e15386219',
'0x3131fe68c4722e726fe6b2819ed68e514395b9a4','0xe1900480ac69f0b296841cd01cc37546d92f35cd',
'0x774b9655413c34809c1f1b16b654465a89ebe989'])
const sha=s=>createHash('sha256').update(s).digest('hex')
function walk(v,out=[]){if(Array.isArray(v)){for(const z of v)walk(z,out)}else if(v&&typeof v==='object'){out.push(v);for(const z of Object.values(v))walk(z,out)}return out}
async function post(url,payload){
 const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-ParallelPrepare/0.5'},body:JSON.stringify(payload)})
 const t=await r.text();if(!r.ok)throw new Error('HTTP_'+r.status+':'+t.slice(0,300))
 const x=JSON.parse(t);if(x.error)throw new Error(JSON.stringify(x.error));return x.result
}
function unwrap(x){
 if(x&&typeof x==='object'&&x.structuredContent!=null){const y=x.structuredContent;return y&&typeof y==='object'&&'data'in y?y.data:y}
 if(x&&typeof x==='object'&&Array.isArray(x.content)){for(const c of x.content){if(c&&c.type==='text'){try{const y=JSON.parse(c.text||'');return y&&typeof y==='object'&&'data'in y?y.data:y}catch{}}}}
 return x&&typeof x==='object'&&'data'in x?x.data:x
}
async function tool(name,args){return unwrap(await post(MCP,{jsonrpc:'2.0',id:1,method:'tools/call',params:{name,arguments:args}}))}
function decode(s){try{const [chain,spoke,rid]=Buffer.from(s,'base64').toString('utf8').split('::');if(chain!=='1'||!/^0x[0-9a-fA-F]{40}$/.test(spoke))return null;return[spoke.toLowerCase(),Number(rid),s]}catch{return null}}
function holders(x){const o=new Set();for(const d of walk(x,[]))for(const k of ['user','address','wallet']){const v=d[k];if(typeof v==='string'&&/^0x[0-9a-fA-F]{40}$/.test(v))o.add(v.toLowerCase())}return o}

const pairs=new Set(),errors=[];let pages=0
const markets=await tool('get_markets',{version:'v4',chainId:1})
const opaque=[...new Set(walk(markets,[]).map(d=>d.reserveId).filter(x=>typeof x==='string'))].sort()
const decoded=opaque.map(decode).filter(Boolean).filter(x=>SPOKES.has(x[0]))
for(const [spoke,rid,oid] of decoded){
 let cursor=null;const seen=new Set()
 for(let i=0;i<200;i++){
  const args={reserveId:oid,side:'borrow',limit:50,version:'v4'};if(cursor)args.cursor=cursor
  let page;try{page=await tool('get_reserve_holders',args)}catch(e){errors.push(spoke+':'+rid+':'+e.name);break}
  pages++;for(const u of holders(page))pairs.add(spoke+'::'+u)
  const curs=[...new Set(walk(page,[]).map(d=>d.nextCursor||d.next_cursor).filter(x=>typeof x==='string'&&x.trim()).map(x=>x.trim()))]
  if(!curs.length)break
  if(curs.length!==1||seen.has(curs[0])){errors.push(spoke+':'+rid+':CURSOR');break}
  seen.add(curs[0]);cursor=curs[0]
 }
}
const latestHex=await post(RPC,{jsonrpc:'2.0',id:1,method:'eth_blockNumber',params:[]})
const L=parseInt(latestHex,16)
const total=L-MIN_BLOCK+1,step=Math.ceil(total/CHUNKS),include=[]
let from=MIN_BLOCK
for(let id=0;id<CHUNKS;id++){
 const to=Math.min(L,from+step-1);include.push({id,from,to});from=to+1;if(from>L)break
}
const pairHashes=[...pairs].map(sha).sort()
const out={stage:'SQD_SDK_PARALLEL_PREPARE_V0.5',classification:errors.length?'PREPARE_BLOCKED':'PREPARE_PASS',
 min_block:MIN_BLOCK,latest_block:L,chunk_count:include.length,chunks:include,
 current_mcp_pair_count:pairs.size,current_mcp_pair_hashes:pairHashes,mcp_pages:pages,mcp_errors:errors,
 raw_wallet_addresses_retained:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile(OUT,JSON.stringify(out,null,2)+'\n')
if(process.env.GITHUB_OUTPUT)await appendFile(process.env.GITHUB_OUTPUT,'matrix='+JSON.stringify({include})+'\n')
console.log(JSON.stringify({...out,current_mcp_pair_hashes:undefined},null,2))
if(errors.length)process.exitCode=2
