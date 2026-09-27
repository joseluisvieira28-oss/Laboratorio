import fs from "fs";

const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO="0x"+"0".repeat(64);
const fromBlock=20730812;
const toBlock=20732811;
const endpoints=[
  ["publicnode","https://ethereum-rpc.publicnode.com"],
  ["1rpc","https://public.1rpc.io/eth"],
  ["drpc","https://eth.drpc.org"],
  ["blockmachine","https://rpc-eth.blockmachine.io"],
  ["flashbots","https://rpc.flashbots.net"]
];

async function rpc(url,method,params){
  const t0=Date.now();
  try{
    const res=await fetch(url,{
      method:"POST",
      headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-source-probe/1.0"},
      body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
      signal:AbortSignal.timeout(12000)
    });
    const text=await res.text();
    let body=null;
    try{ body=JSON.parse(text); }catch{}
    const ok=res.ok && body && !body.error && Array.isArray(body.result);
    return {
      ok,
      http_status:res.status,
      elapsed_ms:Date.now()-t0,
      result_count:ok?body.result.length:null,
      rpc_error:body?.error?{code:body.error.code,message:String(body.error.message||"").slice(0,300)}:null,
      parse_ok:body!==null
    };
  }catch(e){
    return {ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)};
  }
}

const receipt={
  lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",
  stage:"RPC_GETLOGS_CAPABILITY_PROBE_V0.1J",
  source_only:true,
  market_returns_opened:false,
  protected_2026_opened:false,
  pnl_opened:false,
  mutation:false,
  range:{from_block:fromBlock,to_block:toBlock,block_count:toBlock-fromBlock+1},
  endpoints:[]
};

for(const [name,url] of endpoints){
  const result=await rpc(url,"eth_getLogs",[{
    address:TOKEN,
    fromBlock:"0x"+fromBlock.toString(16),
    toBlock:"0x"+toBlock.toString(16),
    topics:[TRANSFER,ZERO]
  }]);
  receipt.endpoints.push({name,url,...result});
  console.log(JSON.stringify({name,...result}));
}

fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/CBBTC_RPC_GETLOGS_CAPABILITY_V0.1J.json",JSON.stringify(receipt,null,2)+"\n");
