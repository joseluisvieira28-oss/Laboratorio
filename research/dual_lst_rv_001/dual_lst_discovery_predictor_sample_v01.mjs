import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const WSTETH=getAddress("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0");
const STETH=getAddress("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const CAL="research/dual_lst_rv_001/DUAL_LST_STATE_CALIBRATION_RECEIPT_V0.1.json";
const REC="research/dual_lst_rv_001/DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json";

const START=24_000_000, STEP=7_200, COUNT=139, PREV=23_992_800;
const Q192=1n<<192n;

for(const p of [CAL,REC]) if(!fs.existsSync(p)) throw new Error("REQUIRED_EVIDENCE_MISSING:"+p);
const cal=JSON.parse(fs.readFileSync(CAL,"utf8"));
const rec=JSON.parse(fs.readFileSync(REC,"utf8"));
if(cal.classification!=="PREDICTOR_STATE_CALIBRATION_PASS") throw new Error("CALIBRATION_NOT_PASS");
if(rec.classification!=="PREDICTOR_CENSUS_PASS") throw new Error("CENSUS_NOT_PASS");
if(cal.source_census_row_set_sha256!==rec.row_set_sha256) throw new Error("CALIBRATION_CENSUS_SHA_MISMATCH");

const POOL=getAddress(rec.selected_pool.pool);
const FEE=Number(rec.selected_pool.fee);
const q10=cal.quantile_rule.q10, q90=cal.quantile_rule.q90;

const rethI=new Interface(["function getExchangeRate() view returns (uint256)"]);
const wstI=new Interface([
 "function stEthPerToken() view returns (uint256)",
 "function getStETHByWstETH(uint256) view returns (uint256)"
]);
const stI=new Interface([
 "function totalSupply() view returns (uint256)",
 "function getTotalPooledEther() view returns (uint256)"
]);
const poolI=new Interface([
 "function token0() view returns (address)",
 "function token1() view returns (address)",
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);
const defs=[
 {target:RETH,allowFailure:false,data:rethI.encodeFunctionData("getExchangeRate")},
 {target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("stEthPerToken")},
 {target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("getStETHByWstETH",[10n**18n])},
 {target:STETH,allowFailure:false,data:stI.encodeFunctionData("totalSupply")},
 {target:STETH,allowFailure:false,data:stI.encodeFunctionData("getTotalPooledEther")},
 {target:POOL,allowFailure:false,data:poolI.encodeFunctionData("token0")},
 {target:POOL,allowFailure:false,data:poolI.encodeFunctionData("token1")},
 {target:POOL,allowFailure:false,data:poolI.encodeFunctionData("slot0")},
 {target:POOL,allowFailure:false,data:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[defs.map(d=>({target:d.target,allowFailure:d.allowFailure,callData:d.data}))]);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function cmpRat(an,ad,bn,bd){
 const l=BigInt(an)*BigInt(bd), r=BigInt(bn)*BigInt(ad);
 return l<r?-1:l>r?1:0;
}
function stateFor(n,d){
 if(cmpRat(n,d,q10.numerator,q10.denominator)<=0) return "RETH_CHEAP_EXTREME";
 if(cmpRat(n,d,q90.numerator,q90.denominator)>=0) return "RETH_RICH_EXTREME";
 return "NEUTRAL";
}

async function point(block,index,role){
 let last=null;
 for(let attempt=1;attempt<=10;attempt++){
  try{
   const meta=await header.getBlock(block);
   if(!meta) throw new Error("HEADER_MISSING");
   const raw=await archive.send("eth_call",[
    {to:MULTI,data:calldata},
    {blockHash:meta.hash,requireCanonical:true}
   ]);
   const res=multiI.decodeFunctionResult("aggregate3",raw)[0];
   if(res.length!==defs.length) throw new Error("MULTICALL_RESULT_COUNT");
   if(res.some((x,i)=>!x.success&&!defs[i].allowFailure)) throw new Error("REQUIRED_SUBCALL_FAIL");

   const rr=BigInt(rethI.decodeFunctionResult("getExchangeRate",res[0].returnData)[0]);
   let wp=null,wf=null;
   if(res[1].success) wp=BigInt(wstI.decodeFunctionResult("stEthPerToken",res[1].returnData)[0]);
   if(res[2].success) wf=BigInt(wstI.decodeFunctionResult("getStETHByWstETH",res[2].returnData)[0]);
   const w=(wp&&wp>0n)?wp:((wf&&wf>0n)?wf:null);
   if(rr<=0n||w===null) throw new Error("ANCHOR_FAIL");

   const supply=BigInt(stI.decodeFunctionResult("totalSupply",res[3].returnData)[0]);
   const pooled=BigInt(stI.decodeFunctionResult("getTotalPooledEther",res[4].returnData)[0]);
   if(supply<=0n||pooled<=0n||supply!==pooled) throw new Error("COMMON_NUMERAIRE_FAIL");

   const t0=getAddress(poolI.decodeFunctionResult("token0",res[5].returnData)[0]);
   const t1=getAddress(poolI.decodeFunctionResult("token1",res[6].returnData)[0]);
   const s0=poolI.decodeFunctionResult("slot0",res[7].returnData);
   const liq=BigInt(poolI.decodeFunctionResult("liquidity",res[8].returnData)[0]);
   if(liq<=0n) throw new Error("LIQUIDITY_FAIL");
   const pair=[t0.toLowerCase(),t1.toLowerCase()];
   if(new Set(pair).size!==2||!pair.includes(RETH.toLowerCase())||!pair.includes(WSTETH.toLowerCase())) throw new Error("PAIR_FAIL");

   const sqrt=BigInt(s0.sqrtPriceX96), sq=sqrt*sqrt;
   let marketNum,marketDen;
   if(t0.toLowerCase()===RETH.toLowerCase()&&t1.toLowerCase()===WSTETH.toLowerCase()){
    marketNum=sq;marketDen=Q192;
   }else{
    marketNum=Q192;marketDen=sq;
   }
   const navNum=rr*supply, navDen=w*pooled;
   const ratioNum=marketNum*navDen, ratioDen=marketDen*navNum;
   const dNum=ratioNum-ratioDen;
   return {
    role,index,block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    pool:POOL,fee:FEE,liquidity:liq.toString(),
    dislocation_exact:{numerator:dNum.toString(),denominator:ratioDen.toString()},
    dislocation_ppb_trunc:((dNum*1_000_000_000n)/ratioDen).toString(),
    state:stateFor(dNum,ratioDen),
    valid:true,block_pinned_by_hash:true,attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<10) await sleep(1500*attempt);
  }
 }
 return {role,index,block_number:block,valid:false,block_pinned_by_hash:true,error:last};
}

const predecessor=await point(PREV,-1,"BOUNDARY_PREDECESSOR");
const rows=[];
for(let k=0;k<COUNT;k++){
 rows.push(await point(START+STEP*k,k,"DISCOVERY_PREDICTOR"));
 if((k+1)%20===0) console.log("progress",k+1,COUNT);
 await sleep(250);
}

const errors=[];
if(!predecessor.valid) errors.push("INVALID_PREDECESSOR");
for(let k=0;k<COUNT;k++){
 const r=rows[k];
 if(!r?.valid) errors.push("INVALID_"+k+":"+String(r?.error||"unknown"));
 if(r?.block_number!==START+STEP*k) errors.push("GRID_"+k);
}
let prev=predecessor.state;
const events=[];
for(const r of rows){
 const cheap=r.state==="RETH_CHEAP_EXTREME"&&prev!=="RETH_CHEAP_EXTREME";
 const rich=r.state==="RETH_RICH_EXTREME"&&prev!=="RETH_RICH_EXTREME";
 if(cheap||rich){
  events.push({
   index:r.index,block_number:r.block_number,block_hash:r.block_hash,block_timestamp:r.block_timestamp,
   state:r.state,dislocation_exact:r.dislocation_exact,dislocation_ppb_trunc:r.dislocation_ppb_trunc
  });
 }
 prev=r.state;
}
const cheapN=events.filter(e=>e.state==="RETH_CHEAP_EXTREME").length;
const richN=events.filter(e=>e.state==="RETH_RICH_EXTREME").length;
let classification;
if(errors.length) classification="DUAL_LST_PREDICTOR_SOURCE_BLOCKED";
else if(events.length<20||cheapN<6||richN<6) classification="DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE";
else classification="DUAL_LST_PREDICTOR_SAMPLE_PASS";

const evidence={predecessor,rows,events};
const sha=crypto.createHash("sha256").update(JSON.stringify(evidence)).digest("hex");
const out={
 lab_id:"DUAL-LST-RV-001",stage:"DISCOVERY_PREDICTOR_SAMPLE_GATE_V0.1",
 captured_at_utc:new Date().toISOString(),classification,
 selected_pool:rec.selected_pool,
 source_census_row_set_sha256:rec.row_set_sha256,
 q10,q90,
 grid:{start_block:START,step_blocks:STEP,count:COUNT,last_block:START+STEP*(COUNT-1),boundary_predecessor_block:PREV},
 valid_count:rows.filter(r=>r.valid).length,invalid_count:rows.filter(r=>!r.valid).length,
 transition_event_count:events.length,cheap_event_count:cheapN,rich_event_count:richN,
 predictor_evidence_sha256:sha,errors:errors.slice(0,100),
 future_returns_opened:false,convergence_outcomes_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};
fs.mkdirSync("artifacts/dual_lst_rv_001/discovery_predictor",{recursive:true});
fs.writeFileSync("artifacts/dual_lst_rv_001/discovery_predictor/DUAL_LST_DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json",JSON.stringify(out,null,2)+"\n");
fs.writeFileSync("artifacts/dual_lst_rv_001/discovery_predictor/DUAL_LST_DISCOVERY_PREDICTOR_ROWS_V0.1.json",JSON.stringify(evidence,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
if(classification==="DUAL_LST_PREDICTOR_SOURCE_BLOCKED") process.exit(2);
