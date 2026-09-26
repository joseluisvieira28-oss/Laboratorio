import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const GATE="research/reth_nav_dislocation_001/RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json";
const ROWS="research/reth_nav_dislocation_001/RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json";
const EQ="research/reth_nav_dislocation_001/RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json";

for(const p of [GATE,ROWS,EQ]) if(!fs.existsSync(p)) throw new Error("REQUIRED_EVIDENCE_MISSING:"+p);
const gate=JSON.parse(fs.readFileSync(GATE,"utf8"));
const evidence=JSON.parse(fs.readFileSync(ROWS,"utf8"));
const eq=JSON.parse(fs.readFileSync(EQ,"utf8"));
if(gate.classification!=="DISCOVERY_PREDICTOR_SAMPLE_PASS") throw new Error("DISCOVERY_PREDICTOR_SAMPLE_NOT_PASS");
if(eq.classification!=="SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS") throw new Error("SPLIT_EQUIVALENCE_NOT_PASS");
const events=evidence.events||[];
if(events.length!==gate.transition_event_count) throw new Error("EVENT_COUNT_MISMATCH");

const rethI=new Interface(["function getExchangeRate() view returns (uint256)"]);
const poolI=new Interface([
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);
const calls=[
 {target:RETH,callData:rethI.encodeFunctionData("getExchangeRate")},
 {target:POOL,callData:poolI.encodeFunctionData("slot0")},
 {target:POOL,callData:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[
 calls.map(c=>({target:c.target,allowFailure:false,callData:c.callData}))
]);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function dAt(block){
 let last=null;
 for(let attempt=1;attempt<=10;attempt++){
  try{
   const meta=await header.getBlock(block);
   if(!meta) throw new Error("HEADER_BLOCK_NOT_FOUND");
   const raw=await archive.send("eth_call",[
     {to:MULTI,data:calldata},
     {blockHash:meta.hash,requireCanonical:true}
   ]);
   const res=multiI.decodeFunctionResult("aggregate3",raw)[0];
   if(res.length!==3||res.some(x=>!x.success)) throw new Error("MULTICALL_SUBCALL_FAIL");
   const rate=BigInt(rethI.decodeFunctionResult("getExchangeRate",res[0].returnData)[0]);
   const s0=poolI.decodeFunctionResult("slot0",res[1].returnData);
   const liq=BigInt(poolI.decodeFunctionResult("liquidity",res[2].returnData)[0]);
   if(rate<=0n||liq<=0n) throw new Error("NONPOSITIVE_STATE");
   const sqrt=BigInt(s0.sqrtPriceX96), q192=1n<<192n;
   const den=q192*rate;
   const num=sqrt*sqrt*1_000_000_000_000_000_000n-den;
   return {
    block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    exchange_rate_wei_per_reth:rate.toString(),sqrtPriceX96:sqrt.toString(),liquidity:liq.toString(),
    dislocation_exact:{numerator:num.toString(),denominator:den.toString()},
    transport:"PUBLIC_HEADER_PLUS_MULTICALL3_EIP1898",block_pinned_by_hash:true,valid:true,attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<10) await sleep(1500*attempt);
  }
 }
 return {block_number:block,valid:false,block_pinned_by_hash:true,error:last};
}

const rows=[];
for(let i=0;i<events.length;i++){
 const e=events[i];
 const primary=await dAt(Number(e.block_number)+7200);
 await sleep(250);
 const secondary=await dAt(Number(e.block_number)+21600);
 rows.push({
  event_index:i,entry_block_number:e.block_number,entry_block_hash:e.block_hash,entry_block_timestamp:e.block_timestamp,
  state:e.state,entry_dislocation_exact:e.dislocation_exact,
  primary_horizon_blocks:7200,primary,secondary_horizon_blocks:21600,secondary,
  market_returns_opened:false,pnl_opened:false
 });
 console.log("progress",i+1,events.length);
 await sleep(250);
}

const invalidPrimary=rows.filter(x=>!x.primary.valid).length;
const invalidSecondary=rows.filter(x=>!x.secondary.valid).length;
const out={
 lab_id:"RETH-NAV-DISLOCATION-001",stage:"MECHANISM_DISCOVERY_SOURCE_V0.1C",
 captured_at_utc:new Date().toISOString(),
 classification:invalidPrimary===0?"MECHANISM_DISCOVERY_SOURCE_PASS":"MECHANISM_DISCOVERY_SOURCE_BLOCKED",
 source:{header_rpc:HEADER_RPC,archive_rpc:ARCHIVE_RPC,multicall3:MULTI,block_binding:"EIP-1898 blockHash requireCanonical"},
 event_count:rows.length,invalid_primary_count:invalidPrimary,invalid_secondary_diagnostic_count:invalidSecondary,
 rows,market_returns_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};
fs.mkdirSync("artifacts/reth_mechanism_discovery",{recursive:true});
fs.writeFileSync("artifacts/reth_mechanism_discovery/RETH_MECHANISM_DISCOVERY_SOURCE_V0.1.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({...out,rows:undefined},null,2));
if(invalidPrimary!==0) process.exit(2);
