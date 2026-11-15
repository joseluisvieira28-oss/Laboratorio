import crypto from "crypto";

const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TARGET_TS=Math.floor(Date.parse("2025-07-01T00:00:00Z")/1000);
const headerEndpoints=[
  ["blockmachine","https://rpc-eth.blockmachine.io"],
  ["1rpc","https://public.1rpc.io/eth"],
  ["flashbots","https://rpc.flashbots.net"]
];
const codeEndpoints=[
  ["publicnode","https://ethereum-rpc.publicnode.com"],
  ["blockmachine","https://rpc-eth.blockmachine.io"],
  ["1rpc","https://public.1rpc.io/eth"],
  ["flashbots","https://rpc.flashbots.net"],
  ["mevblocker","https://rpc.mevblocker.io"]
];

async function rpc(url,method,params,timeout=12000){
  const r=await fetch(url,{
    method:"POST",
    headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-code-probe/1.0"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(timeout)
  });
  const txt=await r.text(); let x=null; try{x=JSON.parse(txt)}catch{}
  if(!r.ok||!x||x.error||!Object.prototype.hasOwnProperty.call(x,"result")){
    const e=x?.error?JSON.stringify(x.error):("HTTP_"+r.status);
    throw new Error(e);
  }
  return x.result;
}
async function header(tag){
  const failures=[];
  for(const [name,url] of headerEndpoints){
    try{
      const x=await rpc(url,"eth_getBlockByNumber",[typeof tag==="number"?"0x"+tag.toString(16):tag,false]);
      if(!x) throw new Error("NULL_BLOCK");
      return {name,url,number:Number(BigInt(x.number)),hash:x.hash,timestamp:Number(BigInt(x.timestamp))};
    }catch(e){failures.push({name,error:String(e?.message||e).slice(0,250)});}
  }
  throw new Error("HEADER_FAIL:"+JSON.stringify(failures));
}
async function firstBlockAtOrAfter(ts){
  const latest=await header("latest");
  let lo=0,hi=latest.number;
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const b=await header(mid);
    if(b.timestamp>=ts) hi=mid; else lo=mid+1;
  }
  return await header(lo);
}
function digest(code){
  return crypto.createHash("sha256").update(Buffer.from(code.slice(2),"hex")).digest("hex");
}

const boundary=await firstBlockAtOrAfter(TARGET_TS);
const endBlock=boundary.number-1;
const endHeader=await header(endBlock);
console.log(JSON.stringify({target_ts:TARGET_TS,boundary,end_block:endHeader}));

for(const [name,url] of codeEndpoints){
  const t0=Date.now();
  try{
    const code=await rpc(url,"eth_getCode",[TOKEN,"0x"+endBlock.toString(16)]);
    const present=typeof code==="string"&&code!=="0x";
    console.log(JSON.stringify({
      name,ok:true,http_status:200,elapsed_ms:Date.now()-t0,
      end_block:endBlock,code_present:present,
      code_bytes:present?(code.length-2)/2:0,
      code_sha256:present?digest(code):null
    }));
  }catch(e){
    console.log(JSON.stringify({name,ok:false,elapsed_ms:Date.now()-t0,end_block:endBlock,error:String(e?.message||e).slice(0,400)}));
  }
}
