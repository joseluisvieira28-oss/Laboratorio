import { JsonRpcProvider, Contract, getAddress } from "ethers";
import fs from "fs";

const RPC=process.env.ETH_RPC_URL || "https://rpc-eth.blockmachine.io";
const provider=new JsonRpcProvider(RPC);
const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const GATE_PATH="research/reth_nav_dislocation_001/RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json";
const ROWS_PATH="research/reth_nav_dislocation_001/RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json";

if(!fs.existsSync(GATE_PATH)||!fs.existsSync(ROWS_PATH)) throw new Error("DISCOVERY_SAMPLE_EVIDENCE_MISSING");
const gate=JSON.parse(fs.readFileSync(GATE_PATH,"utf8"));
const evidence=JSON.parse(fs.readFileSync(ROWS_PATH,"utf8"));
if(gate.classification!=="DISCOVERY_PREDICTOR_SAMPLE_PASS") throw new Error("DISCOVERY_PREDICTOR_SAMPLE_NOT_PASS");
const events=evidence.events||[];
if(events.length!==gate.transition_event_count) throw new Error("EVENT_COUNT_MISMATCH");

const reth=new Contract(RETH,["function getExchangeRate() view returns (uint256)"],provider);
const pool=new Contract(POOL,[
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
],provider);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function dAt(block){
 let last=null;
 for(let attempt=1;attempt<=8;attempt++){
  try{
   const meta=await provider.getBlock(block);
   if(!meta) throw new Error("BLOCK_NOT_FOUND");
   const rate=await reth.getExchangeRate({blockTag:block});
   const s0=await pool.slot0({blockTag:block});
   const liq=await pool.liquidity({blockTag:block});
   if(BigInt(liq)<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");
   const sqrt=BigInt(s0.sqrtPriceX96);
   const q192=1n<<192n;
   const r=BigInt(rate);
   const den=q192*r;
   const num=sqrt*sqrt*1_000_000_000_000_000_000n-den;
   return {
    block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    exchange_rate_wei_per_reth:r.toString(),sqrtPriceX96:sqrt.toString(),
    liquidity:BigInt(liq).toString(),dislocation_exact:{numerator:num.toString(),denominator:den.toString()},
    block_pinned:true,valid:true,attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<8) await sleep(1000*attempt);
  }
 }
 return {block_number:block,valid:false,block_pinned:true,error:last};
}

const rows=[];
for(let i=0;i<events.length;i++){
 const e=events[i];
 const primary=await dAt(Number(e.block_number)+7200);
 await sleep(150);
 const secondary=await dAt(Number(e.block_number)+21600);
 rows.push({
  event_index:i,
  entry_block_number:e.block_number,
  entry_block_hash:e.block_hash,
  entry_block_timestamp:e.block_timestamp,
  state:e.state,
  entry_dislocation_exact:e.dislocation_exact,
  primary_horizon_blocks:7200,
  primary,
  secondary_horizon_blocks:21600,
  secondary,
  market_returns_opened:false,
  pnl_opened:false
 });
 console.log("progress",i+1,events.length);
 await sleep(150);
}

const invalidPrimary=rows.filter(x=>!x.primary.valid).length;
const invalidSecondary=rows.filter(x=>!x.secondary.valid).length;
const out={
 lab_id:"RETH-NAV-DISLOCATION-001",
 stage:"MECHANISM_DISCOVERY_SOURCE_V0.1",
 captured_at_utc:new Date().toISOString(),
 classification:invalidPrimary===0?"MECHANISM_DISCOVERY_SOURCE_PASS":"MECHANISM_DISCOVERY_SOURCE_BLOCKED",
 event_count:rows.length,
 invalid_primary_count:invalidPrimary,
 invalid_secondary_diagnostic_count:invalidSecondary,
 rows,
 market_returns_opened:false,
 pnl_opened:false,
 mutation:false,
 promotion_credit:0
};
fs.mkdirSync("artifacts/reth_mechanism_discovery",{recursive:true});
fs.writeFileSync("artifacts/reth_mechanism_discovery/RETH_MECHANISM_DISCOVERY_SOURCE_V0.1.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({...out,rows:undefined},null,2));
if(invalidPrimary!==0) process.exit(2);
