import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const EQ="research/reth_nav_dislocation_001/RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json";
const START=20_000_000, STEP=7_200, TOTAL=556;

if(!fs.existsSync(EQ)) throw new Error("SPLIT_EQUIVALENCE_RECEIPT_MISSING");
const eq=JSON.parse(fs.readFileSync(EQ,"utf8"));
if(eq.classification!=="SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS") throw new Error("SPLIT_EQUIVALENCE_NOT_PASS");

const rethI=new Interface([
 "function getExchangeRate() view returns (uint256)",
 "function getTotalCollateral() view returns (uint256)"
]);
const poolI=new Interface([
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);
const calls=[
 {name:"getExchangeRate",target:RETH,data:rethI.encodeFunctionData("getExchangeRate")},
 {name:"getTotalCollateral",target:RETH,data:rethI.encodeFunctionData("getTotalCollateral")},
 {name:"slot0",target:POOL,data:poolI.encodeFunctionData("slot0")},
 {name:"liquidity",target:POOL,data:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[
 calls.map(c=>({target:c.target,allowFailure:false,callData:c.data}))
]);

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function getPoint(index){
 const block=START+STEP*index;
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
   if(res.length!==4||res.some(x=>!x.success)) throw new Error("MULTICALL_SUBCALL_FAIL");
   const rate=BigInt(rethI.decodeFunctionResult("getExchangeRate",res[0].returnData)[0]);
   const collateral=BigInt(rethI.decodeFunctionResult("getTotalCollateral",res[1].returnData)[0]);
   const slot=poolI.decodeFunctionResult("slot0",res[2].returnData);
   const liquidity=BigInt(poolI.decodeFunctionResult("liquidity",res[3].returnData)[0]);
   if(rate<=0n) throw new Error("NONPOSITIVE_EXCHANGE_RATE");
   if(liquidity<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");

   const sqrt=BigInt(slot.sqrtPriceX96);
   const q192=1n<<192n;
   const marketNum=sqrt*sqrt;
   const ratioDen=q192*rate;
   const disNum=marketNum*1_000_000_000_000_000_000n-ratioDen;
   const ppb=(disNum*1_000_000_000n)/ratioDen;

   return {
     index,
     block_number:block,
     block_hash:meta.hash,
     block_timestamp:Number(meta.timestamp),
     exchange_rate_wei_per_reth:rate.toString(),
     total_collateral_wei:collateral.toString(),
     sqrtPriceX96:sqrt.toString(),
     tick:Number(slot.tick),
     liquidity:liquidity.toString(),
     market_weth_per_reth_exact:{numerator:marketNum.toString(),denominator:q192.toString()},
     dislocation_exact:{numerator:disNum.toString(),denominator:ratioDen.toString()},
     dislocation_ppb_trunc:ppb.toString(),
     transport:"PUBLIC_HEADER_PLUS_MULTICALL3_EIP1898",
     block_pinned_by_hash:true,
     valid:true,
     attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<10) await sleep(2000*attempt);
  }
 }
 return {index,block_number:block,valid:false,block_pinned_by_hash:true,error:last};
}

const rows=[];
for(let i=0;i<TOTAL;i++){
 rows.push(await getPoint(i));
 if((i+1)%25===0) console.log("progress",i+1,TOTAL);
 await sleep(1500);
}

const errors=[];
if(rows.length!==TOTAL) errors.push("ROW_COUNT");
for(let i=0;i<TOTAL;i++){
 const r=rows[i];
 if(!r||r.index!==i) errors.push(`INDEX:${i}`);
 if(!r||r.block_number!==START+STEP*i) errors.push(`GRID:${i}`);
 if(!r||r.valid!==true) errors.push(`INVALID:${i}:${r?.error||"missing"}`);
 if(r&&r.block_pinned_by_hash!==true) errors.push(`NOT_HASH_PINNED:${i}`);
 if(r&&r.valid&&(!r.block_hash||BigInt(r.exchange_rate_wei_per_reth)<=0n||BigInt(r.liquidity)<=0n)) errors.push(`BAD_VALID_ROW:${i}`);
 if(i>0&&r?.valid&&rows[i-1]?.valid&&Number(r.block_timestamp)<=Number(rows[i-1].block_timestamp)) errors.push(`NONMONOTONIC_TIMESTAMP:${i}`);
}

const valid=rows.filter(x=>x.valid);
const ppb=valid.map(x=>BigInt(x.dislocation_ppb_trunc));
const collateral=valid.map(x=>BigInt(x.total_collateral_wei));
const liquidity=valid.map(x=>BigInt(x.liquidity));
const min=xs=>xs.reduce((a,b)=>a<b?a:b);
const max=xs=>xs.reduce((a,b)=>a>b?a:b);
const sum=xs=>xs.reduce((a,b)=>a+b,0n);
function q(xs,p){
 const s=[...xs].sort((a,b)=>a<b?-1:a>b?1:0);
 const rank=Math.max(1,Math.ceil(p*s.length));
 return s[rank-1];
}

const canonicalRows=rows.map(r=>r.valid?{
 index:r.index,block_number:r.block_number,block_hash:r.block_hash,block_timestamp:r.block_timestamp,
 exchange_rate_wei_per_reth:r.exchange_rate_wei_per_reth,total_collateral_wei:r.total_collateral_wei,
 sqrtPriceX96:r.sqrtPriceX96,tick:r.tick,liquidity:r.liquidity,
 market_weth_per_reth_exact:r.market_weth_per_reth_exact,
 dislocation_exact:r.dislocation_exact,dislocation_ppb_trunc:r.dislocation_ppb_trunc,
 transport:r.transport,block_pinned_by_hash:r.block_pinned_by_hash,valid:r.valid
}:r);
const rowSetSha=crypto.createHash("sha256").update(JSON.stringify(canonicalRows)).digest("hex");

const receipt={
 lab_id:"RETH-NAV-DISLOCATION-001",
 stage:"PREDICTOR_ONLY_CENSUS_V0.1C",
 captured_at_utc:new Date().toISOString(),
 classification:errors.length===0?"PREDICTOR_SOURCE_CENSUS_PASS":"PREDICTOR_SOURCE_CENSUS_BLOCKED",
 source:{
   header_rpc:HEADER_RPC,
   archive_rpc:ARCHIVE_RPC,
   reth:RETH,
   uniswap_v3_reth_weth_fee100_pool:POOL,
   multicall3:MULTI,
   block_binding:"EIP-1898 blockHash requireCanonical"
 },
 grid:{start_block:START,end_boundary:24_000_000,step_blocks:STEP,expected_count:TOTAL,last_block:START+STEP*(TOTAL-1)},
 received_row_count:rows.length,
 valid_count:valid.length,
 invalid_count:rows.length-valid.length,
 min_timestamp:valid.length?Math.min(...valid.map(x=>Number(x.block_timestamp))):null,
 max_timestamp:valid.length?Math.max(...valid.map(x=>Number(x.block_timestamp))):null,
 row_set_sha256:rowSetSha,
 predictor_dislocation_stats:ppb.length?{
   min_ppb:min(ppb).toString(),max_ppb:max(ppb).toString(),mean_ppb_trunc:(sum(ppb)/BigInt(ppb.length)).toString(),
   negative_count:ppb.filter(x=>x<0n).length,zero_count:ppb.filter(x=>x===0n).length,positive_count:ppb.filter(x=>x>0n).length,
   quantiles_ppb:{p01:q(ppb,.01).toString(),p05:q(ppb,.05).toString(),p10:q(ppb,.10).toString(),p25:q(ppb,.25).toString(),p50:q(ppb,.50).toString(),p75:q(ppb,.75).toString(),p90:q(ppb,.90).toString(),p95:q(ppb,.95).toString(),p99:q(ppb,.99).toString()}
 }:null,
 total_collateral_wei_stats:collateral.length?{min:min(collateral).toString(),max:max(collateral).toString(),mean_trunc:(sum(collateral)/BigInt(collateral.length)).toString()}:null,
 pool_liquidity_stats:liquidity.length?{min:min(liquidity).toString(),max:max(liquidity).toString(),mean_trunc:(sum(liquidity)/BigInt(liquidity.length)).toString()}:null,
 errors:errors.slice(0,200),
 market_returns_opened:false,direction_opened:false,holding_horizon_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};

fs.mkdirSync("artifacts/out",{recursive:true});
fs.writeFileSync("artifacts/out/RETH_PREDICTOR_ONLY_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/out/RETH_PREDICTOR_ONLY_CENSUS_ROWS_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,stage:receipt.stage,row_set_sha256:rowSetSha,rows:canonicalRows},null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(receipt.classification!=="PREDICTOR_SOURCE_CENSUS_PASS") process.exit(2);
