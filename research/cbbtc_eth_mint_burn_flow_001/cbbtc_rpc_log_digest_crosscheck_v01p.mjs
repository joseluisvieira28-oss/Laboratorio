import crypto from "crypto";
const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO="0x"+"0".repeat(64);
const from=20730812,to=20740811;
const endpoints=[
 ["blockmachine","https://rpc-eth.blockmachine.io"],
 ["cloudflare","https://cloudflare-eth.com/v1/mainnet"],
 ["llamarpc","https://eth.llamarpc.com"],
 ["mevblocker","https://rpc.mevblocker.io"]
];
function digest(logs){
 const rows=logs.map(x=>[
  x.blockNumber,x.blockHash,x.transactionHash,x.logIndex,x.data,...(x.topics||[])
 ].map(v=>String(v).toLowerCase()).join("|")).sort();
 return crypto.createHash("sha256").update(rows.join("\n")).digest("hex");
}
async function get(url,topics){
 const t0=Date.now();
 try{
  const r=await fetch(url,{method:"POST",headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-crosscheck/1.0"},
   body:JSON.stringify({jsonrpc:"2.0",id:1,method:"eth_getLogs",params:[{
    address:TOKEN,fromBlock:"0x"+from.toString(16),toBlock:"0x"+to.toString(16),topics
   }]}),signal:AbortSignal.timeout(15000)});
  const txt=await r.text();let x=null;try{x=JSON.parse(txt)}catch{}
  const ok=r.ok&&x&&!x.error&&Array.isArray(x.result);
  return {ok,http_status:r.status,elapsed_ms:Date.now()-t0,count:ok?x.result.length:null,
    digest:ok?digest(x.result):null,rpc_error:x?.error?{code:x.error.code,message:String(x.error.message||"").slice(0,300)}:null};
 }catch(e){return {ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)};}
}
for(const [name,url] of endpoints){
 for(const [kind,topics] of [["MINT",[TRANSFER,ZERO]],["BURN",[TRANSFER,null,ZERO]]]){
  const r=await get(url,topics); console.log(JSON.stringify({name,kind,...r}));
 }
}
