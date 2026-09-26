import { JsonRpcProvider, Contract, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const RPC=process.env.ETH_RPC_URL || "https://rpc-eth.blockmachine.io";
const provider=new JsonRpcProvider(RPC);
const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const CAL="research/reth_nav_dislocation_001/RETH_STATE_CALIBRATION_RECEIPT_V0.1.json";
const START=24_000_000;
const STEP=7_200;
const COUNT=139;
const PREV=23_992_800;

if(!fs.existsSync(CAL)) throw new Error("STATE_CALIBRATION_RECEIPT_MISSING");
const cal=JSON.parse(fs.readFileSync(CAL,"utf8"));
if(cal.classification!=="PREDICTOR_STATE_CALIBRATION_PASS") throw new Error("STATE_CALIBRATION_NOT_PASS");
const q05=cal.quantile_rule.q05;
const q95=cal.quantile_rule.q95;

const reth=new Contract(RETH,[
 "function getExchangeRate() view returns (uint256)",
 "function getTotalCollateral() view returns (uint256)"
],provider);
const pool=new Contract(POOL,[
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
],provider);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function cmpRat(an,ad,bn,bd){
 const left=BigInt(an)*BigInt(bd);
 const right=BigInt(bn)*BigInt(ad);
 return left<right?-1:left>right?1:0;
}
function stateFor(n,d){
 if(cmpRat(n,d,q05.numerator,q05.denominator)<=0) return "DISCOUNT_EXTREME";
 if(cmpRat(n,d,q95.numerator,q95.denominator)>=0) return "PREMIUM_EXTREME";
 return "NEUTRAL";
}
async function point(block,index,role){
 let lastErr=null;
 for(let attempt=1;attempt<=8;attempt++){
  try{
   const meta=await provider.getBlock(block);
   if(!meta) throw new Error("BLOCK_NOT_FOUND");
   const rate=await reth.getExchangeRate({blockTag:block});
   const collateral=await reth.getTotalCollateral({blockTag:block});
   const s0=await pool.slot0({blockTag:block});
   const liq=await pool.liquidity({blockTag:block});
   const L=BigInt(liq);
   if(L<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");
   const sqrt=BigInt(s0.sqrtPriceX96);
   const q192=1n<<192n;
   const r=BigInt(rate);
   const marketNum=sqrt*sqrt;
   const ratioDen=q192*r;
   const disNum=marketNum*1_000_000_000_000_000_000n-ratioDen;
   return {
    role,index,block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    exchange_rate_wei_per_reth:r.toString(),total_collateral_wei:BigInt(collateral).toString(),
    sqrtPriceX96:sqrt.toString(),tick:Number(s0.tick),liquidity:L.toString(),
    dislocation_exact:{numerator:disNum.toString(),denominator:ratioDen.toString()},
    state:stateFor(disNum,ratioDen),valid:true,block_pinned:true,attempt
   };
  }catch(e){
   lastErr=String(e?.shortMessage||e?.message||e);
   if(attempt<8) await sleep(1000*attempt);
  }
 }
 return {role,index,block_number:block,valid:false,block_pinned:true,error:lastErr};
}

const predecessor=await point(PREV,-1,"BOUNDARY_PREDECESSOR");
const rows=[];
for(let k=0;k<COUNT;k++){
 rows.push(await point(START+STEP*k,k,"DISCOVERY_PREDICTOR"));
 if((k+1)%10===0) console.log("progress",k+1,COUNT);
 await sleep(150);
}

const errors=[];
if(!predecessor.valid) errors.push("INVALID_BOUNDARY_PREDECESSOR");
if(rows.length!==COUNT) errors.push("ROW_COUNT");
for(let k=0;k<COUNT;k++){
 const r=rows[k];
 if(!r.valid) errors.push(`INVALID:${k}:${r.error||"unknown"}`);
 if(r.block_number!==START+STEP*k) errors.push(`GRID:${k}`);
 if(r.block_pinned!==true) errors.push(`PIN:${k}`);
}
let prevState=predecessor.state;
const events=[];
for(const r of rows){
 const isD=r.state==="DISCOUNT_EXTREME" && prevState!=="DISCOUNT_EXTREME";
 const isP=r.state==="PREMIUM_EXTREME" && prevState!=="PREMIUM_EXTREME";
 if(isD||isP){
  events.push({index:r.index,block_number:r.block_number,block_hash:r.block_hash,block_timestamp:r.block_timestamp,state:r.state,dislocation_exact:r.dislocation_exact});
 }
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
 lab_id:"RETH-NAV-DISLOCATION-001",
 stage:"DISCOVERY_PREDICTOR_SAMPLE_GATE_V0.1",
 captured_at_utc:new Date().toISOString(),
 classification,
 source:{rpc:RPC,reth:RETH,pool:POOL},
 grid:{start_block:START,step_blocks:STEP,count:COUNT,last_block:START+STEP*(COUNT-1),boundary_predecessor_block:PREV},
 state_calibration_source_sha256:cal.source_census_row_set_sha256,
 q05,q95,
 valid_discovery_state_count:rows.filter(x=>x.valid).length,
 invalid_discovery_state_count:rows.filter(x=>!x.valid).length,
 transition_event_count:events.length,
 discount_extreme_event_count:dc,
 premium_extreme_event_count:pc,
 predictor_evidence_sha256:sha,
 errors:errors.slice(0,100),
 future_dislocation_outcomes_opened:false,
 market_returns_opened:false,
 direction_pnl_opened:false,
 holding_horizon_outcomes_opened:false,
 pnl_opened:false,
 mutation:false,
 promotion_credit:0
};
fs.mkdirSync("artifacts/reth_discovery_predictor",{recursive:true});
fs.writeFileSync("artifacts/reth_discovery_predictor/RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/reth_discovery_predictor/RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json",JSON.stringify(canonical,null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(classification==="DISCOVERY_PREDICTOR_SOURCE_BLOCKED") process.exit(2);
