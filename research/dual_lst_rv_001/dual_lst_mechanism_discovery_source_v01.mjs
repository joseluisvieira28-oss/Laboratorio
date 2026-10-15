import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const WSTETH=getAddress("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0");
const STETH=getAddress("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const SAMPLE="research/dual_lst_rv_001/DUAL_LST_DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json";
const ROWS="research/dual_lst_rv_001/DUAL_LST_DISCOVERY_PREDICTOR_ROWS_V0.1.json";
const REC="research/dual_lst_rv_001/DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json";
const Q192=1n<<192n;

for(const p of [SAMPLE,ROWS,REC]) if(!fs.existsSync(p)) throw new Error("REQUIRED_EVIDENCE_MISSING:"+p);
const sample=JSON.parse(fs.readFileSync(SAMPLE,"utf8"));
const evObj=JSON.parse(fs.readFileSync(ROWS,"utf8"));
const rec=JSON.parse(fs.readFileSync(REC,"utf8"));
if(sample.classification!=="DUAL_LST_PREDICTOR_SAMPLE_PASS") throw new Error("PREDICTOR_SAMPLE_NOT_PASS");
if(sample.future_returns_opened!==false||sample.convergence_outcomes_opened!==false) throw new Error("SAMPLE_BOUNDARY_ALREADY_OPEN");
const events=evObj.events||[];
if(events.length!==sample.transition_event_count) throw new Error("EVENT_COUNT_MISMATCH");

const POOL=getAddress(rec.selected_pool.pool);
const FEE=Number(rec.selected_pool.fee);

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

async function dAt(block){
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

   const sqrt=BigInt(s0.sqrtPriceX96),sq=sqrt*sqrt;
   let marketNum,marketDen;
   if(t0.toLowerCase()===RETH.toLowerCase()&&t1.toLowerCase()===WSTETH.toLowerCase()){
    marketNum=sq;marketDen=Q192;
   }else if(t0.toLowerCase()===WSTETH.toLowerCase()&&t1.toLowerCase()===RETH.toLowerCase()){
    marketNum=Q192;marketDen=sq;
   }else throw new Error("PAIR_FAIL");

   const navNum=rr*supply,navDen=w*pooled;
   const ratioNum=marketNum*navDen,ratioDen=marketDen*navNum;
   const dNum=ratioNum-ratioDen;
   return {
    block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    dislocation_exact:{numerator:dNum.toString(),denominator:ratioDen.toString()},
    dislocation_ppb_trunc:((dNum*1_000_000_000n)/ratioDen).toString(),
    pool:POOL,fee:FEE,liquidity:liq.toString(),
    valid:true,block_pinned_by_hash:true,attempt
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
  primary_horizon_blocks:7200,primary,
  secondary_horizon_blocks:21600,secondary,
  future_returns_opened:true,pnl_opened:false
 });
 console.log("progress",i+1,events.length);
 await sleep(250);
}

const invalidPrimary=rows.filter(r=>!r.primary.valid).length;
const invalidSecondary=rows.filter(r=>!r.secondary.valid).length;
const out={
 lab_id:"DUAL-LST-RV-001",stage:"MECHANISM_DISCOVERY_SOURCE_V0.1",
 captured_at_utc:new Date().toISOString(),
 classification:invalidPrimary===0?"MECHANISM_DISCOVERY_SOURCE_PASS":"MECHANISM_DISCOVERY_SOURCE_BLOCKED",
 selected_pool:rec.selected_pool,event_count:rows.length,
 invalid_primary_count:invalidPrimary,invalid_secondary_diagnostic_count:invalidSecondary,
 rows,future_returns_opened:true,market_returns_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};
fs.mkdirSync("artifacts/dual_lst_rv_001/mechanism",{recursive:true});
fs.writeFileSync("artifacts/dual_lst_rv_001/mechanism/DUAL_LST_MECHANISM_DISCOVERY_SOURCE_V0.1.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({...out,rows:undefined},null,2));
if(invalidPrimary!==0) process.exit(2);
