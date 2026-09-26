import { JsonRpcProvider, Contract, Interface, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const RPC=process.env.ETH_RPC_URL || "https://rpc-eth.blockmachine.io";
const provider=new JsonRpcProvider(RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const EQ="research/reth_nav_dislocation_001/MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1B.json";

if(!fs.existsSync(EQ)) throw new Error("MULTICALL_EQUIVALENCE_RECEIPT_MISSING");
const eq=JSON.parse(fs.readFileSync(EQ,"utf8"));
if(eq.classification!=="MULTICALL_TRANSPORT_EQUIVALENCE_PASS") throw new Error("MULTICALL_EQUIVALENCE_NOT_PASS");

const START_BLOCK=20_000_000;
const STEP=7_200;
const TOTAL=556;
const START_INDEX=Number(process.env.START_INDEX);
const END_INDEX=Number(process.env.END_INDEX);
if(!Number.isInteger(START_INDEX)||!Number.isInteger(END_INDEX)||START_INDEX<0||END_INDEX>=TOTAL||START_INDEX>END_INDEX) throw new Error("BAD_INDEX_RANGE");

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

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function point(index){
  const block=START_BLOCK+STEP*index;
  let last=null;
  for(let attempt=1;attempt<=8;attempt++){
    try{
      const meta=await provider.getBlock(block);
      if(!meta) throw new Error("BLOCK_NOT_FOUND");
      const res=await multi.aggregate3.staticCall(
        calls.map(c=>({target:c.target,allowFailure:false,callData:c.data})),
        {blockTag:block}
      );
      if(res.length!==4||res.some(x=>!x.success)) throw new Error("MULTICALL_SUBCALL_FAIL");
      const rate=rethI.decodeFunctionResult("getExchangeRate",res[0].returnData)[0];
      const collateral=rethI.decodeFunctionResult("getTotalCollateral",res[1].returnData)[0];
      const s0=poolI.decodeFunctionResult("slot0",res[2].returnData);
      const liq=poolI.decodeFunctionResult("liquidity",res[3].returnData)[0];
      const L=BigInt(liq);
      if(L<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");
      const sqrt=BigInt(s0.sqrtPriceX96);
      const q192=1n<<192n;
      const r=BigInt(rate);
      const marketNum=sqrt*sqrt;
      const marketDen=q192;
      const ratioNum=marketNum*1_000_000_000_000_000_000n;
      const ratioDen=marketDen*r;
      const disNum=ratioNum-ratioDen;
      const ppb=(disNum*1_000_000_000n)/ratioDen;
      return {
        index,block_number:block,block_hash:meta.hash,block_timestamp:Number(meta.timestamp),
        exchange_rate_wei_per_reth:r.toString(),total_collateral_wei:BigInt(collateral).toString(),
        sqrtPriceX96:sqrt.toString(),tick:Number(s0.tick),liquidity:L.toString(),
        market_weth_per_reth_exact:{numerator:marketNum.toString(),denominator:marketDen.toString()},
        dislocation_exact:{numerator:disNum.toString(),denominator:ratioDen.toString()},
        dislocation_ppb_trunc:ppb.toString(),
        transport:"MULTICALL3",multicall3:MULTI,block_pinned:true,valid:true,attempt
      };
    }catch(e){
      last=String(e?.shortMessage||e?.message||e);
      if(attempt<8) await sleep(1200*attempt);
    }
  }
  return {index,block_number:block,valid:false,block_pinned:true,transport:"MULTICALL3",error:last};
}

const rows=[];
for(let i=START_INDEX;i<=END_INDEX;i++){
  rows.push(await point(i));
  if((i-START_INDEX+1)%10===0) console.log("progress",i,rows.length);
  await sleep(100);
}

const body={
  lab_id:"RETH-NAV-DISLOCATION-001",
  stage:"PREDICTOR_ONLY_CENSUS_MULTICALL_CHUNK_V0.1B",
  captured_at_utc:new Date().toISOString(),
  rpc:RPC,multicall3:MULTI,
  equivalence_receipt_sha256:crypto.createHash("sha256").update(fs.readFileSync(EQ)).digest("hex"),
  start_index:START_INDEX,end_index:END_INDEX,expected_count:END_INDEX-START_INDEX+1,
  valid_count:rows.filter(x=>x.valid).length,invalid_count:rows.filter(x=>!x.valid).length,
  rows,
  market_returns_opened:false,direction_opened:false,pnl_opened:false,mutation:false,promotion_credit:0
};
body.rows_sha256=crypto.createHash("sha256").update(JSON.stringify(rows)).digest("hex");
fs.mkdirSync("artifacts",{recursive:true});
const out=`artifacts/reth_predictor_census_chunk_${START_INDEX}_${END_INDEX}_v01.json`;
fs.writeFileSync(out,JSON.stringify(body,null,2)+"\n");
console.log(JSON.stringify({...body,rows:undefined},null,2));
if(body.invalid_count!==0) process.exit(2);
