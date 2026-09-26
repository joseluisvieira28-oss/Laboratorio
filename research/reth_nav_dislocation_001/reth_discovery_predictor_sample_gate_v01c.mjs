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
const CAL="research/reth_nav_dislocation_001/RETH_STATE_CALIBRATION_RECEIPT_V0.1.json";
const EQ="research/reth_nav_dislocation_001/RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json";
const START=24_000_000, STEP=7_200, COUNT=139, PREV=23_992_800;

if(!fs.existsSync(CAL)) throw new Error("STATE_CALIBRATION_RECEIPT_MISSING");
if(!fs.existsSync(EQ)) throw new Error("SPLIT_EQUIVALENCE_RECEIPT_MISSING");
const cal=JSON.parse(fs.readFileSync(CAL,"utf8"));
const eq=JSON.parse(fs.readFileSync(EQ,"utf8"));
if(cal.classification!=="PREDICTOR_STATE_CALIBRATION_PASS") throw new Error("STATE_CALIBRATION_NOT_PASS");
if(eq.classification!=="SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS") throw new Error("SPLIT_EQUIVALENCE_NOT_PASS");

const q05=cal.quantile_rule.q05, q95=cal.quantile_rule.q95;

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
 {target:RETH,callData:rethI.encodeFunctionData("getExchangeRate")},
 {target:RETH,callData:rethI.encodeFunctionData("getTotalCollateral")},
 {target:POOL,callData:poolI.encodeFunctionData("slot0")},
 {target:POOL,callData:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[
 calls.map(c=>({target:c.target,allowFailure:false,callData:c.callData}))
]);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function cmpRat(an,ad,bn,bd){
 const l=BigInt(an)*BigInt(bd), r=BigInt(bn)*BigInt(ad);
 return l<r?-1:l>r?1:0;
}
function stateFor(n,d){
 if(cmpRat(n,d,q05.numerator,q05.denominator)<=0) return "DISCOUNT_EXTREME";
 if(cmpRat(n,d,q95.numerator,q95.denominator)>=0) return "PREMIUM_EXTREME";
 return "NEUTRAL";
}

async function point(block,index,role){
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
   const s0=poolI.decodeFunctionResult("slot0",res[2].returnData);
   const liq=BigInt(poolI.decodeFunctionResult("liquidity",res[3].returnData)[0]);
   if(rate<=0n||liq<=0n) throw new Error("NONPOSITIVE_STATE");
   const sqrt=BigInt(s0.sqrtPriceX96), q192=1n<<192n;
   const den=q192*rate;
   const num=sqrt*sqrt*1_000_000_000_000_000_000n-den;
   return {
    role,index,block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    exchange_rate_wei_per_reth:rate.toString(),total_collateral_wei:collateral.toString(),
    sqrtPriceX96:sqrt.toString(),tick:Number(s0.tick),liquidity:liq.toString(),
    dislocation_exact:{numerator:num.toString(),denominator:den.toString()},
    state:stateFor(num,den),transport:"PUBLIC_HEADER_PLUS_MULTICALL3_EIP1898",
    valid:true,block_pinned_by_hash:true,attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<10) await sleep(2000*attempt);
  }
 }
 return {role,index,block_number:block,valid:false,block_pinned_by_hash:true,error:last};
}

const predecessor=await point(PREV,-1,"BOUNDARY_PREDECESSOR");
const rows=[];
for(let k=0;k<COUNT;k++){
 rows.push(await point(START+STEP*k,k,"DISCOVERY_PREDICTOR"));
 if((k+1)%20===0) console.log("progress",k+1,COUNT);
 await sleep(1500);
}

const errors=[];
if(!predecessor.valid) errors.push("INVALID_BOUNDARY_PREDECESSOR");
for(let k=0;k<COUNT;k++){
 const r=rows[k];
 if(!r?.valid) errors.push(`INVALID:${k}:${r?.error||"unknown"}`);
 if(r?.block_number!==START+STEP*k) errors.push(`GRID:${k}`);
 if(r?.block_pinned_by_hash!==true) errors.push(`PIN:${k}`);
}

let prevState=predecessor.state;
const events=[];
for(const r of rows){
 const d=r.state==="DISCOUNT_EXTREME"&&prevState!=="DISCOUNT_EXTREME";
 const p=r.state==="PREMIUM_EXTREME"&&prevState!=="PREMIUM_EXTREME";
 if(d||p) events.push({
   index:r.index,block_number:r.block_number,block_hash:r.block_hash,block_timestamp:r.block_timestamp,
   state:r.state,dislocation_exact:r.dislocation_exact
 });
 prevState=r.state;
}
const dc=events.filter(e=>e.state==="DISCOUNT_EXTREME").length;
const pc=events.filter(e=>e.state==="PREMIUM_EXTREME").length;
let classification;
if(errors.length) classification="DISCOVERY_PREDICTOR_SOURCE_BLOCKED";
else if(events.length<30||dc<10||pc<10) classification="DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE";
else classification="DISCOVERY_PREDICTOR_SAMPLE_PASS";

const canonical={predecessor,rows,events};
const sha=crypto.createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
const receipt={
 lab_id:"RETH-NAV-DISLOCATION-001",stage:"DISCOVERY_PREDICTOR_SAMPLE_GATE_V0.1C",
 captured_at_utc:new Date().toISOString(),classification,
 source:{header_rpc:HEADER_RPC,archive_rpc:ARCHIVE_RPC,reth:RETH,pool:POOL,multicall3:MULTI,block_binding:"EIP-1898 blockHash requireCanonical"},
 grid:{start_block:START,step_blocks:STEP,count:COUNT,last_block:START+STEP*(COUNT-1),boundary_predecessor_block:PREV},
 state_calibration_source_sha256:cal.source_census_row_set_sha256,q05,q95,
 valid_discovery_state_count:rows.filter(x=>x.valid).length,
 invalid_discovery_state_count:rows.filter(x=>!x.valid).length,
 transition_event_count:events.length,discount_extreme_event_count:dc,premium_extreme_event_count:pc,
 predictor_evidence_sha256:sha,errors:errors.slice(0,100),
 future_dislocation_outcomes_opened:false,market_returns_opened:false,direction_pnl_opened:false,
 holding_horizon_outcomes_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};
fs.mkdirSync("artifacts/reth_discovery_predictor",{recursive:true});
fs.writeFileSync("artifacts/reth_discovery_predictor/RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/reth_discovery_predictor/RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json",JSON.stringify(canonical,null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(classification==="DISCOVERY_PREDICTOR_SOURCE_BLOCKED") process.exit(2);
