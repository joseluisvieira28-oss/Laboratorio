import crypto from "crypto";
const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO="0x"+"0".repeat(64);
const BM="https://rpc-eth.blockmachine.io";
const MEV="https://rpc.mevblocker.io";
const start=20730812;
function digest(logs){
 const rows=logs.map(x=>[x.blockNumber,x.blockHash,x.transactionHash,x.logIndex,x.data,...(x.topics||[])]
  .map(v=>String(v).toLowerCase()).join("|")).sort();
 return crypto.createHash("sha256").update(rows.join("\n")).digest("hex");
}
async function query(url,from,to,topics){
 const t0=Date.now();
 try{
  const r=await fetch(url,{method:"POST",headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-span-crosscheck/1.0"},
   body:JSON.stringify({jsonrpc:"2.0",id:1,method:"eth_getLogs",params:[{address:TOKEN,
    fromBlock:"0x"+from.toString(16),toBlock:"0x"+to.toString(16),topics}]}),signal:AbortSignal.timeout(20000)});
  const txt=await r.text();let x=null;try{x=JSON.parse(txt)}catch{}
  if(!(r.ok&&x&&!x.error&&Array.isArray(x.result))) return {ok:false,http_status:r.status,elapsed_ms:Date.now()-t0,
    error:x?.error?{code:x.error.code,message:String(x.error.message||"").slice(0,300)}:txt.slice(0,200)};
  return {ok:true,elapsed_ms:Date.now()-t0,logs:x.result};
 }catch(e){return {ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)};}
}
async function baseline(from,to,topics){
 const logs=[];let elapsed=0;
 for(let a=from;a<=to;a+=10000){
  const b=Math.min(to,a+9999),r=await query(BM,a,b,topics);elapsed+=r.elapsed_ms||0;
  if(!r.ok) return {ok:false,elapsed_ms:elapsed,error:r.error};
  logs.push(...r.logs);
 }
 return {ok:true,elapsed_ms:elapsed,logs};
}
for(const span of [50000,100000,200000]){
 const to=start+span-1;
 for(const [kind,topics] of [["MINT",[TRANSFER,ZERO]],["BURN",[TRANSFER,null,ZERO]]]){
  const bm=await baseline(start,to,topics);
  const mv=await query(MEV,start,to,topics);
  const bd=bm.ok?digest(bm.logs):null, md=mv.ok?digest(mv.logs):null;
  console.log(JSON.stringify({span,kind,
    blockmachine_ok:bm.ok,blockmachine_count:bm.ok?bm.logs.length:null,blockmachine_digest:bd,blockmachine_elapsed_ms:bm.elapsed_ms,
    mev_ok:mv.ok,mev_count:mv.ok?mv.logs.length:null,mev_digest:md,mev_elapsed_ms:mv.elapsed_ms,
    exact_match:bm.ok&&mv.ok&&bm.logs.length===mv.logs.length&&bd===md,
    mev_error:mv.ok?null:mv.error}));
 }
}
