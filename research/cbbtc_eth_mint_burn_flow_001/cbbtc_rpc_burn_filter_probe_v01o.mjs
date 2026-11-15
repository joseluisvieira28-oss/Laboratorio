const TOKEN="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf";
const TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const ZERO="0x"+"0".repeat(64);
const endpoint="https://rpc-eth.blockmachine.io";
const ranges=[
 ["A",20730812,20740811],
 ["B",22600000,22609999]
];
for(const [label,from,to] of ranges){
 const t0=Date.now();
 try{
  const res=await fetch(endpoint,{method:"POST",headers:{"content-type":"application/json","user-agent":"CryptoLab-CBBTC-burn-probe/1.0"},
   body:JSON.stringify({jsonrpc:"2.0",id:1,method:"eth_getLogs",params:[{
    address:TOKEN,fromBlock:"0x"+from.toString(16),toBlock:"0x"+to.toString(16),topics:[TRANSFER,null,ZERO]
   }]}),signal:AbortSignal.timeout(15000)});
  const txt=await res.text();let body=null;try{body=JSON.parse(txt)}catch{}
  const ok=res.ok&&body&&!body.error&&Array.isArray(body.result);
  console.log(JSON.stringify({label,ok,http_status:res.status,elapsed_ms:Date.now()-t0,result_count:ok?body.result.length:null,
   rpc_error:body?.error?{code:body.error.code,message:String(body.error.message||"").slice(0,300)}:null}));
 }catch(e){console.log(JSON.stringify({label,ok:false,elapsed_ms:Date.now()-t0,error:String(e?.name||"Error")+":"+String(e?.message||e).slice(0,300)}));}
}
