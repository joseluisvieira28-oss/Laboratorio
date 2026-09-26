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
const SOURCE="research/dual_lst_rv_001/DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json";

const START=20_000_000;
const STEP=7_200;
const TOTAL=556;
const Q192=1n<<192n;

if(!fs.existsSync(SOURCE)) throw new Error("AUTHORITATIVE_SOURCE_RECEIPT_MISSING");
const source=JSON.parse(fs.readFileSync(SOURCE,"utf8"));
if(source.classification!=="SOURCE_PASS") throw new Error("AUTHORITATIVE_SOURCE_NOT_PASS");
if(source.stage!=="SOURCE_DATA_GATE_V0.1B") throw new Error("WRONG_SOURCE_STAGE");
if((source.sentinels||[]).length!==4) throw new Error("SOURCE_SENTINEL_COUNT_NOT_4");

function minBig(xs){
  return xs.reduce((a,b)=>a<b?a:b);
}
const candidates=(source.pool_assessment||[])
  .filter(p=>p.all_four_sentinels_valid)
  .map(p=>{
    const liqs=(source.sentinels||[]).map(s=>{
      const x=(s.pools||[]).find(o=>String(o.pool).toLowerCase()===String(p.pool).toLowerCase());
      if(!x?.valid||!x?.positive_liquidity) throw new Error("SOURCE_POOL_SENTINEL_INVALID:"+p.pool);
      return BigInt(x.liquidity);
    });
    return {...p,min_liquidity:minBig(liqs)};
  });

if(!candidates.length) throw new Error("NO_AUTHORITATIVE_DIRECT_POOL");
candidates.sort((a,b)=>{
  if(a.min_liquidity!==b.min_liquidity) return a.min_liquidity>b.min_liquidity?-1:1;
  if(Number(a.fee)!==Number(b.fee)) return Number(a.fee)-Number(b.fee);
  return String(a.pool).toLowerCase().localeCompare(String(b.pool).toLowerCase());
});
const selected=candidates[0];
const POOL=getAddress(selected.pool);

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
 {name:"reth",target:RETH,allowFailure:false,data:rethI.encodeFunctionData("getExchangeRate")},
 {name:"wst_primary",target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("stEthPerToken")},
 {name:"wst_fallback",target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("getStETHByWstETH",[10n**18n])},
 {name:"st_supply",target:STETH,allowFailure:false,data:stI.encodeFunctionData("totalSupply")},
 {name:"st_pooled",target:STETH,allowFailure:false,data:stI.encodeFunctionData("getTotalPooledEther")},
 {name:"token0",target:POOL,allowFailure:false,data:poolI.encodeFunctionData("token0")},
 {name:"token1",target:POOL,allowFailure:false,data:poolI.encodeFunctionData("token1")},
 {name:"slot0",target:POOL,allowFailure:false,data:poolI.encodeFunctionData("slot0")},
 {name:"liquidity",target:POOL,allowFailure:false,data:poolI.encodeFunctionData("liquidity")}
];
const calldata=multiI.encodeFunctionData("aggregate3",[
 defs.map(d=>({target:d.target,allowFailure:d.allowFailure,callData:d.data}))
]);

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function point(index){
 const block=START+STEP*index;
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
   if(rr<=0n||w===null) throw new Error("ANCHOR_NONPOSITIVE");

   const supply=BigInt(stI.decodeFunctionResult("totalSupply",res[3].returnData)[0]);
   const pooled=BigInt(stI.decodeFunctionResult("getTotalPooledEther",res[4].returnData)[0]);
   if(supply<=0n||pooled<=0n||supply!==pooled) throw new Error("COMMON_NUMERAIRE_FAIL");

   const t0=getAddress(poolI.decodeFunctionResult("token0",res[5].returnData)[0]);
   const t1=getAddress(poolI.decodeFunctionResult("token1",res[6].returnData)[0]);
   const s0=poolI.decodeFunctionResult("slot0",res[7].returnData);
   const liq=BigInt(poolI.decodeFunctionResult("liquidity",res[8].returnData)[0]);
   if(liq<=0n) throw new Error("NONPOSITIVE_LIQUIDITY");
   const pair=[t0.toLowerCase(),t1.toLowerCase()];
   if(new Set(pair).size!==2||!pair.includes(RETH.toLowerCase())||!pair.includes(WSTETH.toLowerCase())) throw new Error("PAIR_IDENTITY_FAIL");

   const sqrt=BigInt(s0.sqrtPriceX96);
   const sq=sqrt*sqrt;
   let marketNum,marketDen,orientation;
   if(t0.toLowerCase()===RETH.toLowerCase()&&t1.toLowerCase()===WSTETH.toLowerCase()){
     marketNum=sq; marketDen=Q192; orientation="TOKEN1_PER_TOKEN0_DIRECT";
   }else if(t0.toLowerCase()===WSTETH.toLowerCase()&&t1.toLowerCase()===RETH.toLowerCase()){
     marketNum=Q192; marketDen=sq; orientation="TOKEN0_PER_TOKEN1_INVERTED";
   }else throw new Error("PAIR_ORIENTATION_FAIL");

   const navNum=rr*supply;
   const navDen=w*pooled;
   const ratioNum=marketNum*navDen;
   const ratioDen=marketDen*navNum;
   if(ratioDen<=0n) throw new Error("RATIO_DEN_NONPOSITIVE");
   const dNum=ratioNum-ratioDen;
   const ppb=(dNum*1_000_000_000n)/ratioDen;

   return {
    index,block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    reth_exchange_rate_wei:rr.toString(),
    wsteth_steth_per_token_wei:w.toString(),
    wsteth_method:(wp&&wp>0n)?"stEthPerToken":"getStETHByWstETH",
    steth_total_supply_wei:supply.toString(),
    steth_total_pooled_ether_wei:pooled.toString(),
    common_numeraire_exact:true,
    pool:POOL,fee:Number(selected.fee),token0:t0,token1:t1,
    sqrtPriceX96:sqrt.toString(),tick:Number(s0.tick),liquidity:liq.toString(),
    market_wsteth_per_reth_exact:{numerator:marketNum.toString(),denominator:marketDen.toString(),orientation},
    protocol_nav_wsteth_per_reth_exact:{numerator:navNum.toString(),denominator:navDen.toString()},
    dislocation_exact:{numerator:dNum.toString(),denominator:ratioDen.toString()},
    dislocation_ppb_trunc:ppb.toString(),
    transport:"PUBLIC_HEADER_PLUS_MULTICALL3_EIP1898",
    block_pinned_by_hash:true,valid:true,attempt
   };
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<10) await sleep(1500*attempt);
  }
 }
 return {index,block_number:block,valid:false,block_pinned_by_hash:true,error:last};
}

const rows=[];
for(let i=0;i<TOTAL;i++){
 rows.push(await point(i));
 if((i+1)%25===0) console.log("progress",i+1,TOTAL);
 await sleep(250);
}

const errors=[];
if(rows.length!==TOTAL) errors.push("ROW_COUNT");
for(let i=0;i<TOTAL;i++){
 const r=rows[i];
 if(!r||r.index!==i) errors.push("INDEX_"+i);
 if(!r||r.block_number!==START+STEP*i) errors.push("GRID_"+i);
 if(!r||r.valid!==true) errors.push("INVALID_"+i+":"+String(r?.error||"missing"));
 if(r?.block_pinned_by_hash!==true) errors.push("NOT_HASH_PINNED_"+i);
 if(r?.valid&&r.common_numeraire_exact!==true) errors.push("NUMERAIRE_"+i);
}
const valid=rows.filter(r=>r.valid);
const ppb=valid.map(r=>BigInt(r.dislocation_ppb_trunc));
const sum=xs=>xs.reduce((a,b)=>a+b,0n);
const min=xs=>xs.reduce((a,b)=>a<b?a:b);
const max=xs=>xs.reduce((a,b)=>a>b?a:b);
const q=(xs,p)=>{
 const s=[...xs].sort((a,b)=>a<b?-1:a>b?1:0);
 return s[Math.max(1,Math.ceil(p*s.length))-1];
};

const canonical=rows.map(r=>({...r}));
const rowSha=crypto.createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
const receipt={
 lab_id:"DUAL-LST-RV-001",stage:"PREDICTOR_ONLY_CENSUS_V0.1",
 captured_at_utc:new Date().toISOString(),
 classification:errors.length===0?"PREDICTOR_CENSUS_PASS":"PREDICTOR_CENSUS_BLOCKED",
 authoritative_source_stage:source.stage,
 selected_pool:{
  fee:Number(selected.fee),pool:POOL,
  selection_rule:"highest minimum raw liquidity across four source sentinels; lower fee then lexicographic address tie-break",
  source_min_liquidity:selected.min_liquidity.toString()
 },
 source:{header_rpc:HEADER_RPC,archive_rpc:ARCHIVE_RPC,multicall3:MULTI,block_binding:"EIP-1898 blockHash requireCanonical"},
 grid:{start_block:START,end_boundary:24_000_000,step_blocks:STEP,expected_count:TOTAL,last_block:START+STEP*(TOTAL-1)},
 valid_count:valid.length,invalid_count:rows.length-valid.length,row_set_sha256:rowSha,
 predictor_stats:ppb.length?{
  min_ppb:min(ppb).toString(),max_ppb:max(ppb).toString(),
  mean_ppb_trunc:(sum(ppb)/BigInt(ppb.length)).toString(),
  negative_count:ppb.filter(x=>x<0n).length,zero_count:ppb.filter(x=>x===0n).length,positive_count:ppb.filter(x=>x>0n).length,
  p10_ppb:q(ppb,.10).toString(),p50_ppb:q(ppb,.50).toString(),p90_ppb:q(ppb,.90).toString()
 }:null,
 errors:errors.slice(0,200),
 future_returns_opened:false,convergence_outcomes_opened:false,direction_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};

fs.mkdirSync("artifacts/dual_lst_rv_001/census",{recursive:true});
fs.writeFileSync("artifacts/dual_lst_rv_001/census/DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/dual_lst_rv_001/census/DUAL_LST_PREDICTOR_CENSUS_ROWS_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,row_set_sha256:rowSha,rows:canonical},null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(receipt.classification!=="PREDICTOR_CENSUS_PASS") process.exit(2);
