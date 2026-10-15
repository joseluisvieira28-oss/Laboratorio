import { JsonRpcProvider, Contract, Interface, getAddress, ZeroAddress } from "ethers";
import fs from "fs";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const WSTETH=getAddress("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0");
const FACTORY=getAddress("0x1F98431c8aD98523631AE4a59f267346ea31F984");
const FEES=[100,500,3000,10000];
const FIXED=[20_000_000,22_000_000,24_000_000];

const factory=new Contract(FACTORY,["function getPool(address,address,uint24) view returns (address)"],archive);
const rethI=new Interface(["function getExchangeRate() view returns (uint256)"]);
const wstI=new Interface([
 "function stEthPerToken() view returns (uint256)",
 "function getStETHByWstETH(uint256) view returns (uint256)"
]);
const poolI=new Interface([
 "function token0() view returns (address)",
 "function token1() view returns (address)",
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);

const raw=async(to,data,tag)=>archive.send("eth_call",[{to,data},tag]);
const hex=n=>"0x"+BigInt(n).toString(16);
const out={
 lab_id:"DUAL-LST-RV-001",stage:"SOURCE_DATA_GATE_V0.1",
 captured_at_utc:new Date().toISOString(),
 header_rpc:HEADER_RPC,archive_rpc:ARCHIVE_RPC,
 contracts:{reth:RETH,wsteth:WSTETH,uniswap_v3_factory:FACTORY},
 fees:FEES,sentinels:[],pool_discovery:[],
 future_returns_opened:false,convergence_outcomes_opened:false,direction_opened:false,pnl_opened:false,mutation:false,promotion_credit:0,
 errors:[]
};

const finalized=await header.getBlock("finalized");
if(!finalized) throw new Error("FINALIZED_BLOCK_MISSING");
const blocks=[...FIXED,Number(finalized.number)];

for(const fee of FEES){
 try{
  const p=getAddress(await factory.getPool(RETH,WSTETH,fee));
  out.pool_discovery.push({fee,pool:p,nonzero:p!==ZeroAddress});
 }catch(e){out.pool_discovery.push({fee,pool:null,nonzero:false,error:String(e?.shortMessage||e?.message||e)});}
}

for(const n of blocks){
 const row={block_number:n};
 try{
  const meta=await header.getBlock(n);
  if(!meta) throw new Error("HEADER_MISSING");
  row.block_hash=meta.hash; row.block_timestamp=Number(meta.timestamp);
  const tag=hex(n);

  const rr=await raw(RETH,rethI.encodeFunctionData("getExchangeRate"),tag);
  row.reth_exchange_rate_wei=rethI.decodeFunctionResult("getExchangeRate",rr)[0].toString();

  let wr=null, wmethod=null;
  try{
    const x=await raw(WSTETH,wstI.encodeFunctionData("stEthPerToken"),tag);
    wr=wstI.decodeFunctionResult("stEthPerToken",x)[0]; wmethod="stEthPerToken";
  }catch{
    const x=await raw(WSTETH,wstI.encodeFunctionData("getStETHByWstETH",[10n**18n]),tag);
    wr=wstI.decodeFunctionResult("getStETHByWstETH",x)[0]; wmethod="getStETHByWstETH";
  }
  row.wsteth_steth_per_token_wei=wr.toString(); row.wsteth_method=wmethod;

  row.pools=[];
  for(const d of out.pool_discovery.filter(x=>x.nonzero)){
   try{
    const t0=getAddress(poolI.decodeFunctionResult("token0",await raw(d.pool,poolI.encodeFunctionData("token0"),tag))[0]);
    const t1=getAddress(poolI.decodeFunctionResult("token1",await raw(d.pool,poolI.encodeFunctionData("token1"),tag))[0]);
    const s0=poolI.decodeFunctionResult("slot0",await raw(d.pool,poolI.encodeFunctionData("slot0"),tag));
    const liq=BigInt(poolI.decodeFunctionResult("liquidity",await raw(d.pool,poolI.encodeFunctionData("liquidity"),tag))[0]);
    row.pools.push({
      fee:d.fee,pool:d.pool,token0:t0,token1:t1,
      pair_exact:new Set([t0.toLowerCase(),t1.toLowerCase()]).size===2 &&
        [t0.toLowerCase(),t1.toLowerCase()].includes(RETH.toLowerCase()) &&
        [t0.toLowerCase(),t1.toLowerCase()].includes(WSTETH.toLowerCase()),
      sqrtPriceX96:s0.sqrtPriceX96.toString(),tick:Number(s0.tick),liquidity:liq.toString(),positive_liquidity:liq>0n,valid:true
    });
   }catch(e){
    row.pools.push({fee:d.fee,pool:d.pool,valid:false,error:String(e?.shortMessage||e?.message||e)});
   }
  }
  row.valid=true;
 }catch(e){
  row.valid=false; row.error=String(e?.shortMessage||e?.message||e); out.errors.push({block_number:n,error:row.error});
 }
 out.sentinels.push(row);
}

const fixedRows=out.sentinels.slice(0,3);
const anchorPass=fixedRows.every(r=>r.valid && BigInt(r.reth_exchange_rate_wei)>0n && BigInt(r.wsteth_steth_per_token_wei)>0n);
const pools=out.pool_discovery.filter(x=>x.nonzero);
const poolAssess=pools.map(p=>{
 const obs=fixedRows.map(r=>(r.pools||[]).find(x=>x.pool?.toLowerCase()===p.pool.toLowerCase()));
 const validObs=obs.filter(x=>x?.valid&&x.pair_exact&&x.positive_liquidity);
 return {fee:p.fee,pool:p.pool,fixed_sentinel_valid_count:validObs.length,all_three_fixed_sentinels_valid:validObs.length===3};
});
out.pool_assessment=poolAssess;
out.classification=anchorPass && poolAssess.some(x=>x.all_three_fixed_sentinels_valid) && out.errors.length===0
 ? "SOURCE_PASS" : "SOURCE_BLOCKED";

fs.mkdirSync("artifacts/dual_lst_rv_001",{recursive:true});
fs.writeFileSync("artifacts/dual_lst_rv_001/DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
if(out.classification!=="SOURCE_PASS") process.exit(2);
