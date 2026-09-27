import fs from "fs";

const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER_TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO_TOPIC="0x"+"0".repeat(64);

// Diagnostic blocks are transport probes only, not scientific sample boundaries.
const ANCHORS=[20800000,22600000];
const SPANS=[20000,10000,5000,2000,1000];
const ENDPOINTS=[
  {slug:"publicnode",url:"https://ethereum-rpc.publicnode.com"},
  {slug:"blockmachine",url:"https://rpc-eth.blockmachine.io"}
];

const hex=n=>"0x"+BigInt(n).toString(16);
async function rpc(endpoint,method,params){
  const t0=Date.now();
  try{
    const res=await fetch(endpoint,{
      method:"POST",
      headers:{"content-type":"application/json"},
      body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
      signal:AbortSignal.timeout(30000)
    });
    const text=await res.text();
    let body=null;
    try{body=JSON.parse(text)}catch{}
    return {
      ok:res.ok && body && !body.error,
      http_status:res.status,
      ms:Date.now()-t0,
      error:body?.error||(!res.ok?text.slice(0,500):null),
      result_count:Array.isArray(body?.result)?body.result.length:null
    };
  }catch(e){
    return {ok:false,http_status:null,ms:Date.now()-t0,error:String(e?.message||e),result_count:null};
  }
}

const rows=[];
for(const ep of ENDPOINTS){
  for(const anchor of ANCHORS){
    for(const span of SPANS){
      const from=anchor;
      const to=anchor+span-1;
      const mint=await rpc(ep.url,"eth_getLogs",[{
        address:TOKEN,fromBlock:hex(from),toBlock:hex(to),topics:[TRANSFER_TOPIC,ZERO_TOPIC]
      }]);
      rows.push({endpoint:ep.slug,kind:"MINT",from,to,span,...mint});
      const burn=await rpc(ep.url,"eth_getLogs",[{
        address:TOKEN,fromBlock:hex(from),toBlock:hex(to),topics:[TRANSFER_TOPIC,null,ZERO_TOPIC]
      }]);
      rows.push({endpoint:ep.slug,kind:"BURN",from,to,span,...burn});
      console.log(ep.slug,anchor,span,"mint",mint.ok,mint.ms,"burn",burn.ok,burn.ms);
    }
  }
}

const out={
  lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",
  stage:"GETLOGS_TRANSPORT_DIAGNOSTIC_V0.1",
  scientific_credit:0,
  official_source_gate_modified:false,
  market_outcomes_opened:false,
  rows
};
fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/cbbtc_getlogs_transport_diag_v01.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
