import { JsonRpcProvider, Contract, Interface, getAddress } from "ethers";
import fs from "fs";

const RPC=process.env.ETH_RPC_URL || "https://rpc-eth.blockmachine.io";
const provider=new JsonRpcProvider(RPC);
const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const BLOCKS=[20_000_000,22_000_000,24_000_000];

const rethI=new Interface([
 "function getExchangeRate() view returns (uint256)",
 "function getTotalCollateral() view returns (uint256)"
]);
const poolI=new Interface([
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multi=new Contract(MULTI,[
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
],provider);

const calls=[
 {name:"getExchangeRate",target:RETH,data:rethI.encodeFunctionData("getExchangeRate")},
 {name:"getTotalCollateral",target:RETH,data:rethI.encodeFunctionData("getTotalCollateral")},
 {name:"slot0",target:POOL,data:poolI.encodeFunctionData("slot0")},
 {name:"liquidity",target:POOL,data:poolI.encodeFunctionData("liquidity")}
];

const out={
 lab_id:"RETH-NAV-DISLOCATION-001",
 stage:"MULTICALL_TRANSPORT_EQUIVALENCE_V0.1B",
 captured_at_utc:new Date().toISOString(),
 rpc:RPC,multicall3:MULTI,blocks:[],errors:[],
 market_returns_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};

for(const block of BLOCKS){
 try{
  const meta=await provider.getBlock(block);
  if(!meta) throw new Error("BLOCK_NOT_FOUND");
  const direct={};
  for(const c of calls){
   direct[c.name]=await provider.call({to:c.target,data:c.data},block);
  }
  const results=await multi.aggregate3.staticCall(
    calls.map(c=>({target:c.target,allowFailure:false,callData:c.data})),
    {blockTag:block}
  );
  const comparisons=[];
  for(let i=0;i<calls.length;i++){
    const r=results[i];
    const same=Boolean(r.success)&&String(r.returnData).toLowerCase()===String(direct[calls[i].name]).toLowerCase();
    comparisons.push({
      name:calls[i].name,
      direct_return_data:direct[calls[i].name],
      multicall_success:Boolean(r.success),
      multicall_return_data:String(r.returnData),
      exact_bytes_equal:same
    });
  }
  out.blocks.push({
    block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
    comparisons,all_exact:comparisons.every(x=>x.exact_bytes_equal)
  });
 }catch(e){
  out.errors.push({block,error:String(e?.shortMessage||e?.message||e)});
 }
}

out.classification=
 out.errors.length===0 &&
 out.blocks.length===BLOCKS.length &&
 out.blocks.every(x=>x.all_exact)
 ? "MULTICALL_TRANSPORT_EQUIVALENCE_PASS"
 : "MULTICALL_TRANSPORT_EQUIVALENCE_FAIL";

fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/reth_multicall_transport_equivalence_v01b.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
if(out.classification!=="MULTICALL_TRANSPORT_EQUIVALENCE_PASS") process.exit(2);
