import fs from "fs";
const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO="0x"+"0".repeat(64);
const start=20730812;
const endpoints=[
  ["blockmachine","https://rpc-eth.blockmachine.io"],
  ["flashbots","https://rpc.flashbots.net"]
];
const spans=[2000,10000,20000,50000];

async function probe(name,url,span){
  const from=start,to=start+span-1,t0=Date.now();
  try{
    const res=await fetch(url,{
      method:"POST",
      headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-range-probe/1.0"},
      body:JSON.stringify({jsonrpc:"2.0",id:1,method:"eth_getLogs",params:[{
        address:TOKEN,fromBlock:"0x"+from.toString(16),toBlock:"0x"+to.toString(16),topics:[TRANSFER,ZERO]
      }]}),
      signal:AbortSignal.timeout(15000)
    });
    const txt=await res.text(); let body=null; try{body=JSON.parse(txt)}catch{}
    const ok=res.ok && body && !body.error && Array.isArray(body.result);
    return {name,url,span,ok,http_status:res.status,elapsed_ms:Date.now()-t0,
      result_count:ok?body.result.length:null,
      rpc_error:body?.error?{code:body.error.code,message:String(body.error.message||"").slice(0,300)}:null};
  }catch(e){return {name,url,span,ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)};}
}
const out={lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",stage:"RPC_LOG_RANGE_PROBE_V0.1L",source_only:true,market_returns_opened:false,results:[]};
for(const [name,url] of endpoints) for(const span of spans){const r=await probe(name,url,span);out.results.push(r);console.log(JSON.stringify(r));}
fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/CBBTC_RPC_LOG_RANGE_PROBE_V0.1L.json",JSON.stringify(out,null,2)+"\n");
