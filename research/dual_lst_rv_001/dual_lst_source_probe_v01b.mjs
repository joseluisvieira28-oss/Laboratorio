import { JsonRpcProvider, Contract, Interface, getAddress, ZeroAddress } from "ethers";
import fs from "fs";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const WSTETH=getAddress("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0");
const STETH=getAddress("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84");
const FACTORY=getAddress("0x1F98431c8aD98523631AE4a59f267346ea31F984");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const FEES=[100,500,3000,10000];
const FIXED=[20_000_000,22_000_000,24_000_000];

const factory=new Contract(FACTORY,["function getPool(address,address,uint24) view returns (address)"],header);
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

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function archiveCallByHash(to,data,hash,scope){
 let last=null;
 for(let attempt=1;attempt<=8;attempt++){
  try{
   return await archive.send("eth_call",[
    {to,data},
    {blockHash:hash,requireCanonical:true}
   ]);
  }catch(e){
   last=String(e?.shortMessage||e?.message||e);
   if(attempt<8) await sleep(800*attempt);
  }
 }
 throw new Error(scope+":"+last);
}

const out={
 lab_id:"DUAL-LST-RV-001",
 stage:"SOURCE_DATA_GATE_V0.1B",
 captured_at_utc:new Date().toISOString(),
 header_rpc:HEADER_RPC,
 archive_rpc:ARCHIVE_RPC,
 contracts:{reth:RETH,wsteth:WSTETH,steth:STETH,uniswap_v3_factory:FACTORY,multicall3:MULTI},
 fees:FEES,
 pool_discovery:[],
 sentinels:[],
 errors:[],
 future_returns_opened:false,
 convergence_outcomes_opened:false,
 direction_opened:false,
 pnl_opened:false,
 mutation:false,
 promotion_credit:0,
 classification:"SOURCE_BLOCKED"
};

try{
 const finalized=await header.getBlock("finalized");
 if(!finalized) throw new Error("FINALIZED_BLOCK_MISSING");
 const blocks=[...FIXED,Number(finalized.number)];
 out.finalized_block_selected={
  number:Number(finalized.number),
  hash:finalized.hash,
  timestamp:Number(finalized.timestamp)
 };

 for(const fee of FEES){
  try{
   const p=getAddress(await factory.getPool(RETH,WSTETH,fee));
   out.pool_discovery.push({fee,pool:p,nonzero:p!==ZeroAddress});
  }catch(e){
   out.pool_discovery.push({fee,pool:null,nonzero:false,error:String(e?.shortMessage||e?.message||e)});
  }
 }
 const discovered=out.pool_discovery.filter(x=>x.nonzero);

 for(const n of blocks){
  const row={block_number:n,pools:[],valid:false};
  try{
   const meta=(n===Number(finalized.number))?finalized:await header.getBlock(n);
   if(!meta) throw new Error("HEADER_MISSING");
   row.block_hash=meta.hash;
   row.block_timestamp=Number(meta.timestamp);

   const defs=[
    {scope:"reth_exchange_rate",target:RETH,allowFailure:false,data:rethI.encodeFunctionData("getExchangeRate")},
    {scope:"wsteth_stEthPerToken",target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("stEthPerToken")},
    {scope:"wsteth_getStETHByWstETH",target:WSTETH,allowFailure:true,data:wstI.encodeFunctionData("getStETHByWstETH",[10n**18n])},
    {scope:"steth_totalSupply",target:STETH,allowFailure:false,data:stI.encodeFunctionData("totalSupply")},
    {scope:"steth_getTotalPooledEther",target:STETH,allowFailure:false,data:stI.encodeFunctionData("getTotalPooledEther")}
   ];
   for(const p of discovered){
    defs.push(
     {scope:`pool_${p.fee}_token0`,target:p.pool,allowFailure:true,data:poolI.encodeFunctionData("token0"),fee:p.fee,pool:p.pool,field:"token0"},
     {scope:`pool_${p.fee}_token1`,target:p.pool,allowFailure:true,data:poolI.encodeFunctionData("token1"),fee:p.fee,pool:p.pool,field:"token1"},
     {scope:`pool_${p.fee}_slot0`,target:p.pool,allowFailure:true,data:poolI.encodeFunctionData("slot0"),fee:p.fee,pool:p.pool,field:"slot0"},
     {scope:`pool_${p.fee}_liquidity`,target:p.pool,allowFailure:true,data:poolI.encodeFunctionData("liquidity"),fee:p.fee,pool:p.pool,field:"liquidity"}
    );
   }

   const calldata=multiI.encodeFunctionData("aggregate3",[
    defs.map(d=>({target:d.target,allowFailure:d.allowFailure,callData:d.data}))
   ]);
   const raw=await archiveCallByHash(MULTI,calldata,meta.hash,"MULTICALL_BLOCK_"+n);
   const res=multiI.decodeFunctionResult("aggregate3",raw)[0];
   if(res.length!==defs.length) throw new Error("MULTICALL_RESULT_COUNT_MISMATCH");

   if(!res[0].success) throw new Error("RETH_ANCHOR_FAIL");
   const rr=BigInt(rethI.decodeFunctionResult("getExchangeRate",res[0].returnData)[0]);
   if(rr<=0n) throw new Error("RETH_ANCHOR_NONPOSITIVE");
   row.reth_exchange_rate_wei=rr.toString();

   let wPrimary=null,wFallback=null;
   if(res[1].success) wPrimary=BigInt(wstI.decodeFunctionResult("stEthPerToken",res[1].returnData)[0]);
   if(res[2].success) wFallback=BigInt(wstI.decodeFunctionResult("getStETHByWstETH",res[2].returnData)[0]);
   const wChosen=(wPrimary&&wPrimary>0n)?wPrimary:((wFallback&&wFallback>0n)?wFallback:null);
   if(wChosen===null) throw new Error("WSTETH_ANCHOR_FAIL");

   if(!res[3].success||!res[4].success) throw new Error("STETH_NUMERAIRE_CALL_FAIL");
   const stSupply=BigInt(stI.decodeFunctionResult("totalSupply",res[3].returnData)[0]);
   const pooled=BigInt(stI.decodeFunctionResult("getTotalPooledEther",res[4].returnData)[0]);
   if(stSupply<=0n||pooled<=0n) throw new Error("STETH_NUMERAIRE_NONPOSITIVE");
   if(stSupply!==pooled) throw new Error("STETH_SUPPLY_POOLED_ETHER_NOT_EXACT");

   row.wsteth_steth_per_token_wei=wChosen.toString();
   row.wsteth_method=(wPrimary&&wPrimary>0n)?"stEthPerToken":"getStETHByWstETH";
   row.steth_total_supply_wei=stSupply.toString();
   row.steth_total_pooled_ether_wei=pooled.toString();
   row.protocol_accounting_eth_per_steth_exact={numerator:pooled.toString(),denominator:stSupply.toString()};
   row.protocol_accounting_eth_per_wsteth_exact={
    numerator:(wChosen*pooled).toString(),
    denominator:(10n**18n*stSupply).toString()
   };
   row.relative_protocol_nav_wsteth_per_reth_exact={
    numerator:(rr*stSupply).toString(),
    denominator:(wChosen*pooled).toString()
   };
   row.wsteth_methods={
    stEthPerToken_success:Boolean(wPrimary&&wPrimary>0n),
    getStETHByWstETH_success:Boolean(wFallback&&wFallback>0n),
    exact_agreement:wPrimary!==null&&wFallback!==null?wPrimary===wFallback:null
   };

   let idx=5;
   for(const p of discovered){
    const r0=res[idx++],r1=res[idx++],rs=res[idx++],rl=res[idx++];
    const obs={fee:p.fee,pool:p.pool,valid:false};
    try{
     if(!r0.success||!r1.success||!rs.success||!rl.success) throw new Error("POOL_SUBCALL_FAIL");
     const t0=getAddress(poolI.decodeFunctionResult("token0",r0.returnData)[0]);
     const t1=getAddress(poolI.decodeFunctionResult("token1",r1.returnData)[0]);
     const s0=poolI.decodeFunctionResult("slot0",rs.returnData);
     const liq=BigInt(poolI.decodeFunctionResult("liquidity",rl.returnData)[0]);
     const pair=[t0.toLowerCase(),t1.toLowerCase()];
     const exact=new Set(pair).size===2 &&
       pair.includes(RETH.toLowerCase()) && pair.includes(WSTETH.toLowerCase());
     obs.token0=t0;obs.token1=t1;obs.pair_exact=exact;
     obs.sqrtPriceX96=s0.sqrtPriceX96.toString();
     obs.tick=Number(s0.tick);
     obs.liquidity=liq.toString();
     obs.positive_liquidity=liq>0n;
     obs.valid=exact&&liq>0n;
    }catch(e){
     obs.error=String(e?.shortMessage||e?.message||e);
    }
    row.pools.push(obs);
   }

   row.valid=true;
  }catch(e){
   row.error=String(e?.shortMessage||e?.message||e);
   out.errors.push({block_number:n,error:row.error});
  }
  out.sentinels.push(row);
 }

 const anchorPass=out.sentinels.length===4 && out.sentinels.every(r=>
  r.valid &&
  BigInt(r.reth_exchange_rate_wei||"0")>0n &&
  BigInt(r.wsteth_steth_per_token_wei||"0")>0n &&
  BigInt(r.steth_total_supply_wei||"0")>0n &&
  BigInt(r.steth_total_pooled_ether_wei||"0")>0n &&
  BigInt(r.steth_total_supply_wei)===BigInt(r.steth_total_pooled_ether_wei)
 );
 const poolAssess=out.pool_discovery.filter(x=>x.nonzero).map(p=>{
  const obs=out.sentinels.map(r=>(r.pools||[]).find(x=>x.pool?.toLowerCase()===p.pool.toLowerCase()));
  const valid=obs.filter(x=>x?.valid&&x.pair_exact&&x.positive_liquidity);
  return {fee:p.fee,pool:p.pool,sentinel_valid_count:valid.length,all_four_sentinels_valid:valid.length===4};
 });
 out.pool_assessment=poolAssess;
 out.classification=
  anchorPass &&
  poolAssess.some(x=>x.all_four_sentinels_valid) &&
  out.errors.length===0
  ? "SOURCE_PASS" : "SOURCE_BLOCKED";
}catch(e){
 out.errors.push({scope:"fatal",error:String(e?.shortMessage||e?.message||e)});
 out.classification="SOURCE_BLOCKED";
}

fs.mkdirSync("artifacts/dual_lst_rv_001",{recursive:true});
fs.writeFileSync(
 "artifacts/dual_lst_rv_001/DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json",
 JSON.stringify(out,null,2)+"\n"
);
console.log(JSON.stringify(out,null,2));
if(out.classification!=="SOURCE_PASS") process.exit(2);
