import {writeFile,mkdir,appendFile} from 'node:fs/promises'
const RPC='https://eth-mainnet.public.blastapi.io'
const MIN=24720899,CHUNKS=16
async function rpc(method,params){
 const r=await fetch(RPC,{method:'POST',headers:{'content-type':'application/json','user-agent':'CryptoLab-LCOD-ActivePrep/0.8'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})})
 const x=await r.json();if(x.error)throw new Error(JSON.stringify(x.error));return x.result
}
const b=await rpc('eth_getBlockByNumber',['finalized',false])
if(!b)throw new Error('NO_FINALIZED_BLOCK')
const N=parseInt(b.number,16),hash=b.hash.toLowerCase()
const total=N-MIN+1,step=Math.ceil(total/CHUNKS),include=[]
let from=MIN
for(let id=0;id<CHUNKS;id++){const to=Math.min(N,from+step-1);include.push({id,from,to});from=to+1;if(from>N)break}
const out={stage:'BLOCK_PINNED_ACTIVE_POPULATION_PREP_V0.8',classification:include.length===16?'PREP_PASS':'PREP_BLOCKED',
 finalized_block_number:N,finalized_block_hash:hash,min_block:MIN,chunks:include,chunk_count:include.length,
 raw_wallet_addresses_retained:false,curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile('artifacts/lcod_active_population_prepare_v08.json',JSON.stringify(out,null,2)+'\n')
if(process.env.GITHUB_OUTPUT){
 await appendFile(process.env.GITHUB_OUTPUT,'matrix='+JSON.stringify({include})+'\n')
 await appendFile(process.env.GITHUB_OUTPUT,'block='+String(N)+'\n')
 await appendFile(process.env.GITHUB_OUTPUT,'block_hash='+hash+'\n')
}
console.log(JSON.stringify(out,null,2));if(out.classification!=='PREP_PASS')process.exitCode=2
