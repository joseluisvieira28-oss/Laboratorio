import { JsonRpcProvider, Contract, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const RPC = process.env.ETH_RPC_URL || "https://rpc-eth.blockmachine.io";
const provider = new JsonRpcProvider(RPC);

const RETH=getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const POOL=getAddress("0x553e9C493678d8606d6a5ba284643dB2110Df823");
const START_BLOCK=20_000_000;
const STEP=7_200;
const TOTAL=556;
const START_INDEX=Number(process.env.START_INDEX);
const END_INDEX=Number(process.env.END_INDEX);

if (!Number.isInteger(START_INDEX)||!Number.isInteger(END_INDEX)||START_INDEX<0||END_INDEX>=TOTAL||START_INDEX>END_INDEX) {
  throw new Error("BAD_INDEX_RANGE");
}

const reth=new Contract(RETH,[
  "function getExchangeRate() view returns (uint256)",
  "function getTotalCollateral() view returns (uint256)"
],provider);
const pool=new Contract(POOL,[
  "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
  "function liquidity() view returns (uint128)"
],provider);

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function point(index){
  const block=START_BLOCK+STEP*index;
  let lastErr=null;
  for(let attempt=1;attempt<=4;attempt++){
    try{
      const [meta,rate,collateral,s0,liq]=await Promise.all([
        provider.getBlock(block),
        reth.getExchangeRate({blockTag:block}),
        reth.getTotalCollateral({blockTag:block}),
        pool.slot0({blockTag:block}),
        pool.liquidity({blockTag:block})
      ]);
      if(!meta) throw new Error("BLOCK_NOT_FOUND");
      const liquidity=BigInt(liq);
      if(liquidity<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");
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
        index,
        block_number:block,
        block_hash:meta.hash,
        block_timestamp:Number(meta.timestamp),
        exchange_rate_wei_per_reth:r.toString(),
        total_collateral_wei:BigInt(collateral).toString(),
        sqrtPriceX96:sqrt.toString(),
        tick:Number(s0.tick),
        liquidity:liquidity.toString(),
        market_weth_per_reth_exact:{numerator:marketNum.toString(),denominator:marketDen.toString()},
        dislocation_exact:{numerator:disNum.toString(),denominator:ratioDen.toString()},
        dislocation_ppb_trunc:ppb.toString(),
        block_pinned:true,
        valid:true,
        attempt
      };
    }catch(e){
      lastErr=String(e?.shortMessage||e?.message||e);
      if(attempt<4) await sleep(600*attempt);
    }
  }
  return {index,block_number:block,valid:false,error:lastErr,block_pinned:true};
}

const rows=[];
for(let i=START_INDEX;i<=END_INDEX;i++){
  rows.push(await point(i));
  if((i-START_INDEX+1)%10===0) console.log("progress",i,rows.length);
}

const body={
  lab_id:"RETH-NAV-DISLOCATION-001",
  stage:"PREDICTOR_ONLY_CENSUS_CHUNK_V0.1",
  captured_at_utc:new Date().toISOString(),
  rpc:RPC,
  start_index:START_INDEX,
  end_index:END_INDEX,
  expected_count:END_INDEX-START_INDEX+1,
  valid_count:rows.filter(x=>x.valid).length,
  invalid_count:rows.filter(x=>!x.valid).length,
  rows,
  market_returns_opened:false,
  direction_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0
};
const hash=crypto.createHash("sha256").update(JSON.stringify(rows)).digest("hex");
body.rows_sha256=hash;
fs.mkdirSync("artifacts",{recursive:true});
const out=`artifacts/reth_predictor_census_chunk_${START_INDEX}_${END_INDEX}_v01.json`;
fs.writeFileSync(out,JSON.stringify(body,null,2)+"\n");
console.log(JSON.stringify({...body,rows:undefined},null,2));
if(body.invalid_count!==0) process.exit(2);
