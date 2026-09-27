import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";
import crypto from "crypto";

const HEADER_RPC=process.env.ETH_HEADER_RPC_URL || "https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);

const CBETH=getAddress("0xBe9895146f7AF43049ca1c1AE358B0541Ea49704");
const WETH=getAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2");
const SOURCE="research/cbeth_redemption_basis_001/SOURCE_GATE_RECEIPT_V0.1.json";
const EQ="research/cbeth_redemption_basis_001/MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json";
const MULTI=getAddress("0xcA11bde05977b3631167028862bE2a173976CA11");
const START_DAY="2023-01-01";
const END_DAY="2024-12-31";
const OBS_HOUR_UTC=17;

if(!fs.existsSync(SOURCE)) throw new Error("SOURCE_GATE_RECEIPT_MISSING");
if(!fs.existsSync(EQ)) throw new Error("MULTICALL_EQUIVALENCE_RECEIPT_MISSING");
const source=JSON.parse(fs.readFileSync(SOURCE,"utf8"));
const equivalence=JSON.parse(fs.readFileSync(EQ,"utf8"));
if(source.classification!=="SOURCE_PASS") throw new Error("SOURCE_GATE_NOT_PASS");
if(equivalence.classification!=="MULTICALL_TRANSPORT_EQUIVALENCE_PASS") throw new Error("MULTICALL_EQUIVALENCE_NOT_PASS");

const cbI=new Interface(["function exchangeRate() view returns (uint256)"]);
const poolI=new Interface([
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)",
 "function liquidity() view returns (uint128)"
]);
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function rpc(endpoint,method,params,timeoutMs=30_000){
  const res=await fetch(endpoint,{
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(timeoutMs)
  });
  if(!res.ok) throw new Error("HTTP_"+res.status);
  const x=await res.json();
  if(x?.error) throw new Error("RPC_"+JSON.stringify(x.error));
  return x?.result;
}

async function retry(fn,scope,max=8){
  let last=null;
  for(let attempt=1;attempt<=max;attempt++){
    try{return await fn(attempt);}
    catch(e){
      last=String(e?.shortMessage||e?.message||e);
      if(attempt<max) await sleep(800*attempt);
    }
  }
  throw new Error(scope+":"+last);
}

function isoDayRange(start,end){
  const out=[];
  for(let d=new Date(start+"T00:00:00Z");d<=new Date(end+"T00:00:00Z");d=new Date(d.getTime()+86_400_000)){
    out.push(d.toISOString().slice(0,10));
  }
  return out;
}

async function rawHeader(n){
  const x=await retry(()=>rpc(HEADER_RPC,"eth_getBlockByNumber",["0x"+BigInt(n).toString(16),false]),"HEADER_"+n);
  if(!x) throw new Error("HEADER_NULL_"+n);
  return {number:Number(BigInt(x.number)),hash:String(x.hash),timestamp:Number(BigInt(x.timestamp))};
}

async function latestHeader(){
  const x=await retry(()=>rpc(HEADER_RPC,"eth_getBlockByNumber",["latest",false]),"LATEST_HEADER");
  if(!x) throw new Error("LATEST_NULL");
  return {number:Number(BigInt(x.number)),hash:String(x.hash),timestamp:Number(BigInt(x.timestamp))};
}

async function firstBlockAtOrAfterGlobal(targetTs){
  const latest=await latestHeader();
  let lo=0,hi=latest.number;
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const h=await rawHeader(mid);
    if(h.timestamp>=targetTs) hi=mid; else lo=mid+1;
    await sleep(80);
  }
  return await rawHeader(lo);
}

async function nextDailyBoundary(previousBlock,targetTs){
  let lo=previousBlock+1;
  let hi=lo+10_000;
  let h=await rawHeader(hi);
  while(h.timestamp<targetTs){
    lo=hi+1;
    hi+=10_000;
    h=await rawHeader(hi);
  }
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const m=await rawHeader(mid);
    if(m.timestamp>=targetTs) hi=mid; else lo=mid+1;
    await sleep(50);
  }
  return await rawHeader(lo);
}

async function archiveCall(to,data,hash,scope){
  return await retry(()=>rpc(ARCHIVE_RPC,"eth_call",[
    {to,data},
    {blockHash:hash,requireCanonical:true}
  ]),scope);
}

function selectPool(){
  const finalizedNumber=Number(source.finalized_block.number);
  const sentinels=new Set(source.fixed_historical_sentinels.map(Number));
  const candidates=[];
  for(const p of source.pools||[]){
    if(!p.discovered||p.token_order_verified!==true) continue;
    const hist=(p.historical_reads||[]).filter(x=>sentinels.has(Number(x.number))&&x.positive_liquidity===true);
    const fin=(p.historical_reads||[]).find(x=>Number(x.number)===finalizedNumber&&x.positive_liquidity===true);
    if(hist.length<4||!fin) continue;
    candidates.push({
      fee:Number(p.fee),
      pool:getAddress(p.pool),
      token0:getAddress(p.token0),
      token1:getAddress(p.token1),
      historical_positive_count:hist.length,
      finalized_liquidity:BigInt(fin.liquidity)
    });
  }
  candidates.sort((a,b)=>{
    if(a.historical_positive_count!==b.historical_positive_count) return b.historical_positive_count-a.historical_positive_count;
    if(a.finalized_liquidity!==b.finalized_liquidity) return a.finalized_liquidity>b.finalized_liquidity?-1:1;
    return a.fee-b.fee;
  });
  if(!candidates.length) throw new Error("NO_SOURCE_QUALIFIED_POOL");
  return candidates[0];
}

function exactMarket(token0,token1,sqrt){
  const q192=1n<<192n;
  const s=BigInt(sqrt);
  const raw=s*s;
  if(token0.toLowerCase()===CBETH.toLowerCase()&&token1.toLowerCase()===WETH.toLowerCase()){
    return {numerator:raw,denominator:q192};
  }
  if(token0.toLowerCase()===WETH.toLowerCase()&&token1.toLowerCase()===CBETH.toLowerCase()){
    return {numerator:q192,denominator:raw};
  }
  throw new Error("BAD_POOL_TOKEN_ORDER");
}

const selected=selectPool();
if(
  Number(equivalence.selected_pool?.fee)!==selected.fee ||
  String(equivalence.selected_pool?.pool||"").toLowerCase()!==selected.pool.toLowerCase()
) throw new Error("EQUIVALENCE_SELECTED_POOL_MISMATCH");

const aggregateCalls=[
  {target:CBETH,allowFailure:false,callData:cbI.encodeFunctionData("exchangeRate")},
  {target:selected.pool,allowFailure:false,callData:poolI.encodeFunctionData("slot0")},
  {target:selected.pool,allowFailure:false,callData:poolI.encodeFunctionData("liquidity")}
];
const aggregateCalldata=multiI.encodeFunctionData("aggregate3",[aggregateCalls]);

const days=isoDayRange(START_DAY,END_DAY);
const rows=[];
const errors=[];
let previousBlock=null;

for(let i=0;i<days.length;i++){
  const day=days[i];
  const targetTs=Math.floor(Date.parse(day+"T17:00:00Z")/1000);
  try{
    const meta=previousBlock===null
      ? await firstBlockAtOrAfterGlobal(targetTs)
      : await nextDailyBoundary(previousBlock,targetTs);
    previousBlock=meta.number;

    if(meta.timestamp<targetTs) throw new Error("BOUNDARY_BEFORE_TARGET");
    if(meta.number>0){
      const prev=await rawHeader(meta.number-1);
      if(prev.timestamp>=targetTs) throw new Error("NOT_FIRST_BLOCK_AT_OR_AFTER");
    }

    const aggregateRaw=await archiveCall(
      MULTI,aggregateCalldata,meta.hash,"MULTICALL_"+day
    );
    const aggregate=multiI.decodeFunctionResult("aggregate3",aggregateRaw)[0];
    if(aggregate.length!==3||aggregate.some(x=>!x.success)) throw new Error("MULTICALL_SUBCALL_FAIL");

    const rate=BigInt(cbI.decodeFunctionResult("exchangeRate",aggregate[0].returnData)[0]);
    const slot=poolI.decodeFunctionResult("slot0",aggregate[1].returnData);
    const liquidity=BigInt(poolI.decodeFunctionResult("liquidity",aggregate[2].returnData)[0]);
    if(rate<=0n) throw new Error("NONPOSITIVE_PROTOCOL_RATE");
    if(liquidity<=0n) throw new Error("NONPOSITIVE_POOL_LIQUIDITY");

    const market=exactMarket(selected.token0,selected.token1,slot.sqrtPriceX96);
    const basisDen=market.denominator*rate;
    const basisNum=market.numerator*1_000_000_000_000_000_000n-basisDen;
    const ppb=(basisNum*1_000_000_000n)/basisDen;

    rows.push({
      utc_day:day,
      target_timestamp_utc:day+"T17:00:00Z",
      block_number:meta.number,
      block_hash:meta.hash,
      block_timestamp:meta.timestamp,
      protocol_exchange_rate_wei_per_cbeth:rate.toString(),
      sqrtPriceX96:BigInt(slot.sqrtPriceX96).toString(),
      tick:Number(slot.tick),
      liquidity:liquidity.toString(),
      market_weth_per_cbeth_exact:{numerator:market.numerator.toString(),denominator:market.denominator.toString()},
      signed_basis_exact:{numerator:basisNum.toString(),denominator:basisDen.toString()},
      signed_basis_ppb_trunc:ppb.toString(),
      block_pinned_by_hash:true,
      transport:"MULTICALL3_EQUIVALENCE_VERIFIED",
      valid:true
    });
  }catch(e){
    errors.push({utc_day:day,error:String(e?.message||e)});
    rows.push({utc_day:day,target_timestamp_utc:day+"T17:00:00Z",valid:false,error:String(e?.message||e)});
  }
  if((i+1)%25===0) console.log("progress",i+1,days.length,"errors",errors.length);
  await sleep(150);
}

const canonicalRows=rows.map(x=>({...x}));
const rowSha=crypto.createHash("sha256").update(JSON.stringify(canonicalRows)).digest("hex");
const valid=rows.filter(x=>x.valid);
const ppb=valid.map(x=>BigInt(x.signed_basis_ppb_trunc));
const sum=xs=>xs.reduce((a,b)=>a+b,0n);
const min=xs=>xs.reduce((a,b)=>a<b?a:b);
const max=xs=>xs.reduce((a,b)=>a>b?a:b);
function q(xs,p){
  const s=[...xs].sort((a,b)=>a<b?-1:a>b?1:0);
  const rank=Math.max(1,Math.ceil(p*s.length));
  return s[rank-1];
}

const classification=errors.length===0&&valid.length===days.length
  ?"PREDICTOR_CENSUS_PASS"
  :"PREDICTOR_CENSUS_BLOCKED";

const receipt={
  lab_id:"CBETH-REDEMPTION-BASIS-001",
  stage:"PREDICTOR_ONLY_DAILY_BASIS_CENSUS_V0.1",
  captured_at_utc:new Date().toISOString(),
  classification,
  selected_pool:{
    fee:selected.fee,
    pool:selected.pool,
    token0:selected.token0,
    token1:selected.token1,
    historical_positive_count:selected.historical_positive_count,
    finalized_liquidity:selected.finalized_liquidity.toString(),
    selection_rule:"historical valid count > finalized liquidity > lower fee"
  },
  transport:{
    archive_rpc:ARCHIVE_RPC,
    multicall3:MULTI,
    equivalence_stage:equivalence.stage,
    equivalence_classification:equivalence.classification,
    block_binding:"EIP-1898 blockHash requireCanonical"
  },
  period:{start_day:START_DAY,end_day:END_DAY,observation_time_utc:"17:00:00"},
  expected_day_count:days.length,
  valid_day_count:valid.length,
  invalid_day_count:days.length-valid.length,
  row_set_sha256:rowSha,
  basis_stats_ppb:ppb.length?{
    min:min(ppb).toString(),
    max:max(ppb).toString(),
    mean_trunc:(sum(ppb)/BigInt(ppb.length)).toString(),
    p01:q(ppb,.01).toString(),
    p05:q(ppb,.05).toString(),
    p10:q(ppb,.10).toString(),
    p50:q(ppb,.50).toString(),
    p90:q(ppb,.90).toString(),
    p95:q(ppb,.95).toString(),
    p99:q(ppb,.99).toString()
  }:null,
  errors:errors.slice(0,200),
  future_mechanism_outcomes_opened:false,
  market_returns_opened:false,
  oos_2025_opened:false,
  protected_2026_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0
};

fs.mkdirSync("artifacts/cbeth_census",{recursive:true});
fs.writeFileSync("artifacts/cbeth_census/CBETH_PREDICTOR_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/cbeth_census/CBETH_PREDICTOR_CENSUS_ROWS_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,row_set_sha256:rowSha,rows:canonicalRows},null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(classification!=="PREDICTOR_CENSUS_PASS") process.exit(2);
