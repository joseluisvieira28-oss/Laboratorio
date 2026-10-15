import crypto from "crypto";

const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TOTAL_SUPPLY_SELECTOR="0x18160ddd";
const START_TS=Math.floor(Date.parse("2024-09-12T00:00:00Z")/1000);
const END_TS=Math.floor(Date.parse("2026-01-01T00:00:00Z")/1000);
const ENDPOINTS=[
  ["blockmachine","https://rpc-eth.blockmachine.io"],
  ["mevblocker","https://rpc.mevblocker.io"]
];

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const tag=n=>"0x"+BigInt(n).toString(16);

async function rpc(url,method,params,timeout=15000){
  const r=await fetch(url,{
    method:"POST",
    headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-supply-anchor-crosscheck/1.0"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(timeout)
  });
  const text=await r.text();
  let x=null; try{x=JSON.parse(text)}catch{}
  if(!r.ok) throw new Error("HTTP_"+r.status);
  if(x?.error) throw new Error("RPC_"+JSON.stringify(x.error));
  if(!Object.prototype.hasOwnProperty.call(x||{},"result")) throw new Error("RESULT_MISSING");
  return x.result;
}

async function block(url,n){
  const x=await rpc(url,"eth_getBlockByNumber",[typeof n==="string"?n:tag(n),false]);
  if(!x) throw new Error("NULL_BLOCK");
  return {number:Number(BigInt(x.number)),hash:String(x.hash),timestamp:Number(BigInt(x.timestamp))};
}

async function firstAtOrAfter(url,ts){
  const latest=await block(url,"latest");
  let lo=0,hi=latest.number;
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    try{
      const b=await block(url,mid);
      if(b.timestamp>=ts) hi=mid; else lo=mid+1;
    }catch(e){
      // These two archive-capable sources are expected to serve the frozen historical range.
      throw new Error("BOUNDARY_"+mid+":"+String(e?.message||e));
    }
    await sleep(10);
  }
  return await block(url,lo);
}

async function one(name,url){
  const t0=Date.now();
  try{
    const start=await firstAtOrAfter(url,START_TS);
    const endBoundary=await firstAtOrAfter(url,END_TS);
    const startAnchor=await block(url,start.number-1);
    const endBlock=await block(url,endBoundary.number-1);
    const startSupply=await rpc(url,"eth_call",[
      {to:TOKEN,data:TOTAL_SUPPLY_SELECTOR},
      {blockHash:startAnchor.hash,requireCanonical:true}
    ]);
    const endSupply=await rpc(url,"eth_call",[
      {to:TOKEN,data:TOTAL_SUPPLY_SELECTOR},
      {blockHash:endBlock.hash,requireCanonical:true}
    ]);
    return {
      name,url,ok:true,elapsed_ms:Date.now()-t0,
      start_boundary:start,start_anchor:startAnchor,
      end_boundary:endBoundary,end_block:endBlock,
      start_supply_raw:BigInt(startSupply).toString(),
      end_supply_raw:BigInt(endSupply).toString(),
      start_supply_hex:String(startSupply).toLowerCase(),
      end_supply_hex:String(endSupply).toLowerCase()
    };
  }catch(e){
    return {name,url,ok:false,elapsed_ms:Date.now()-t0,error:String(e?.message||e).slice(0,1200)};
  }
}

const rows=[];
for(const [name,url] of ENDPOINTS){
  const r=await one(name,url);
  rows.push(r);
  console.log(JSON.stringify(r));
}

const good=rows.filter(x=>x.ok);
const exactMatch=
  good.length===2 &&
  good[0].start_anchor.number===good[1].start_anchor.number &&
  good[0].start_anchor.hash.toLowerCase()===good[1].start_anchor.hash.toLowerCase() &&
  good[0].end_block.number===good[1].end_block.number &&
  good[0].end_block.hash.toLowerCase()===good[1].end_block.hash.toLowerCase() &&
  good[0].start_supply_hex===good[1].start_supply_hex &&
  good[0].end_supply_hex===good[1].end_supply_hex;

const receipt={
  lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",
  probe_id:"CBBTC-SUPPLY-ANCHOR-CROSSCHECK-V0.1W",
  source_only:true,
  market_outcomes_opened:false,
  access_2026_market_outcomes:false,
  exact_match:exactMatch,
  rows,
  digest:crypto.createHash("sha256").update(JSON.stringify(rows)).digest("hex")
};
console.log(JSON.stringify(receipt,null,2));
if(!exactMatch) process.exit(2);
