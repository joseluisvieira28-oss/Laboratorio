import { Interface, getAddress } from "ethers";
import fs from "fs";

const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const CBETH=getAddress("0xBe9895146f7AF43049ca1c1AE358B0541Ea49704");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const SOURCE="research/cbeth_redemption_basis_001/SOURCE_GATE_RECEIPT_V0.1.json";
const BLOCKS=[16_000_000,20_000_000,24_000_000];

if(!fs.existsSync(SOURCE)) throw new Error("SOURCE_GATE_RECEIPT_MISSING");
const source=JSON.parse(fs.readFileSync(SOURCE,"utf8"));
if(source.classification!=="SOURCE_PASS") throw new Error("SOURCE_GATE_NOT_PASS");

const cbI=new Interface(["function exchangeRate() view returns (uint256)"]);
const poolI=new Interface([
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function rpc(method,params){
  const res=await fetch(ARCHIVE_RPC,{
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(30_000)
  });
  if(!res.ok) throw new Error("HTTP_"+res.status);
  const x=await res.json();
  if(x?.error) throw new Error("RPC_"+JSON.stringify(x.error));
  return x?.result;
}

async function retry(fn,scope,max=8){
  let last=null;
  for(let a=1;a<=max;a++){
    try{return await fn();}
    catch(e){
      last=String(e?.message||e);
      if(a<max) await sleep(800*a);
    }
  }
  throw new Error(scope+":"+last);
}

function selectPool(){
  const finalizedNumber=Number(source.finalized_block.number);
  const sentinels=new Set(source.fixed_historical_sentinels.map(Number));
  const candidates=[];
  for(const p of source.pools||[]){
    if(!p.discovered||p.token_order_verified!==true) continue;
    const hist=(p.historical_reads||[]).filter(x=>sentinels.has(Number(x.number))&&x.positive_liquidity===true);
    const fin=(p.historical_reads||[]).find(x=>Number(x.number)===finalizedNumber&&x.positive_liquidity===true);
    if(hist.length<4||!fin) continue;
    candidates.push({
      fee:Number(p.fee),pool:getAddress(p.pool),
      historical_positive_count:hist.length,
      finalized_liquidity:BigInt(fin.liquidity)
    });
  }
  candidates.sort((a,b)=>{
    if(a.historical_positive_count!==b.historical_positive_count) return b.historical_positive_count-a.historical_positive_count;
    if(a.finalized_liquidity!==b.finalized_liquidity) return a.finalized_liquidity>b.finalized_liquidity?-1:1;
    return a.fee-b.fee;
  });
  if(!candidates.length) throw new Error("NO_SOURCE_QUALIFIED_POOL");
  return candidates[0];
}

const selected=selectPool();
const calls=[
 {name:"exchangeRate",target:CBETH,data:cbI.encodeFunctionData("exchangeRate")},
 {name:"slot0",target:selected.pool,data:poolI.encodeFunctionData("slot0")},
 {name:"liquidity",target:selected.pool,data:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[
 calls.map(c=>({target:c.target,allowFailure:false,callData:c.data}))
]);

const out={
 lab_id:"CBETH-REDEMPTION-BASIS-001",
 stage:"MULTICALL_TRANSPORT_EQUIVALENCE_V0.1C",
 captured_at_utc:new Date().toISOString(),
 classification:"MULTICALL_TRANSPORT_EQUIVALENCE_FAIL",
 selected_pool:{fee:selected.fee,pool:selected.pool},
 multicall3:MULTI,
 blocks:[],
 errors:[],
 scientific_credit:0,
 future_mechanism_outcomes_opened:false,
 market_returns_opened:false,
 oos_2025_opened:false,
 protected_2026_opened:false,
 pnl_opened:false
};

for(const n of BLOCKS){
 try{
  const anchor=(source.protocol_anchor||[]).find(x=>Number(x.number)===n);
  if(!anchor?.hash) throw new Error("SOURCE_BLOCK_HASH_MISSING_"+n);
  const tag={blockHash:anchor.hash,requireCanonical:true};
  const direct={};
  for(const c of calls){
    direct[c.name]=await retry(
      ()=>rpc("eth_call",[{to:c.target,data:c.data},tag]),
      "DIRECT_"+c.name+"_"+n
    );
  }
  const raw=await retry(
    ()=>rpc("eth_call",[{to:MULTI,data:calldata},tag]),
    "MULTICALL_"+n
  );
  const decoded=multiI.decodeFunctionResult("aggregate3",raw)[0];
  const comparisons=calls.map((c,i)=>({
    name:c.name,
    direct_return_data:String(direct[c.name]),
    multicall_success:Boolean(decoded[i].success),
    multicall_return_data:String(decoded[i].returnData),
    exact_bytes_equal:
      Boolean(decoded[i].success) &&
      String(direct[c.name]).toLowerCase()===String(decoded[i].returnData).toLowerCase()
  }));
  out.blocks.push({
    block_number:n,
    block_hash:anchor.hash,
    comparisons,
    all_exact:comparisons.every(x=>x.exact_bytes_equal)
  });
 }catch(e){
  out.errors.push({block_number:n,error:String(e?.message||e)});
 }
}

out.classification=
 out.errors.length===0 &&
 out.blocks.length===3 &&
 out.blocks.every(x=>x.all_exact)
 ? "MULTICALL_TRANSPORT_EQUIVALENCE_PASS"
 : "MULTICALL_TRANSPORT_EQUIVALENCE_FAIL";

fs.mkdirSync("artifacts/cbeth_transport",{recursive:true});
fs.writeFileSync(
 "artifacts/cbeth_transport/CBETH_MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json",
 JSON.stringify(out,null,2)+"\n"
);
console.log(JSON.stringify(out,null,2));
if(out.classification!=="MULTICALL_TRANSPORT_EQUIVALENCE_PASS") process.exit(2);
