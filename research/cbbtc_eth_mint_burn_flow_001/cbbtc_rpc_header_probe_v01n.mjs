const block=20730812;
const endpoints=[
 ["publicnode","https://ethereum-rpc.publicnode.com"],
 ["blockmachine","https://rpc-eth.blockmachine.io"],
 ["1rpc","https://public.1rpc.io/eth"],
 ["flashbots","https://rpc.flashbots.net"]
];
async function probe(name,url){
 const t0=Date.now();
 try{
  const res=await fetch(url,{method:"POST",headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-header-probe/1.0"},
   body:JSON.stringify({jsonrpc:"2.0",id:1,method:"eth_getBlockByNumber",params:["0x"+block.toString(16),false]}),
   signal:AbortSignal.timeout(12000)});
  const txt=await res.text(); let body=null; try{body=JSON.parse(txt)}catch{}
  const ok=res.ok&&body&&!body.error&&body.result&&body.result.number;
  console.log(JSON.stringify({name,ok:!!ok,http_status:res.status,elapsed_ms:Date.now()-t0,
    block_number:ok?Number(BigInt(body.result.number)):null,
    block_hash_present:!!(ok&&body.result.hash),
    timestamp_present:!!(ok&&body.result.timestamp),
    rpc_error:body?.error?{code:body.error.code,message:String(body.error.message||"").slice(0,300)}:null}));
 }catch(e){console.log(JSON.stringify({name,ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)}));}
}
for(const [n,u] of endpoints) await probe(n,u);
