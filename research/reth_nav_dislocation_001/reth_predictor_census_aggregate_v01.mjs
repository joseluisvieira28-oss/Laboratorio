import fs from "fs";
import path from "path";
import crypto from "crypto";

const TOTAL=556;
const START_BLOCK=20_000_000;
const STEP=7_200;

function walk(dir){
  let out=[];
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) out=out.concat(walk(p));
    else if(/reth_predictor_census_chunk_\d+_\d+_v01\.json$/.test(ent.name)) out.push(p);
  }
  return out;
}
const files=walk("artifacts/chunks");
const chunks=files.map(f=>JSON.parse(fs.readFileSync(f,"utf8")));
let rows=chunks.flatMap(x=>x.rows||[]).sort((a,b)=>a.index-b.index);
const errors=[];

if(rows.length!==TOTAL) errors.push(`ROW_COUNT:${rows.length}`);
for(let i=0;i<TOTAL;i++){
  const r=rows[i];
  if(!r){errors.push(`MISSING_INDEX:${i}`);continue;}
  if(r.index!==i) errors.push(`INDEX_MISMATCH:${i}:${r.index}`);
  if(r.block_number!==START_BLOCK+STEP*i) errors.push(`BLOCK_GRID_MISMATCH:${i}`);
  if(r.valid!==true) errors.push(`INVALID_POINT:${i}:${r.error||"unknown"}`);
  if(r.block_pinned!==true) errors.push(`NOT_BLOCK_PINNED:${i}`);
  if(!r.block_hash) errors.push(`MISSING_HASH:${i}`);
  if(BigInt(r.exchange_rate_wei_per_reth||"0")<=0n) errors.push(`BAD_RATE:${i}`);
  if(BigInt(r.total_collateral_wei||"0")<0n) errors.push(`BAD_COLLATERAL:${i}`);
  if(BigInt(r.liquidity||"0")<=0n) errors.push(`BAD_LIQUIDITY:${i}`);
  if(i>0 && rows[i-1] && Number(r.block_timestamp)<=Number(rows[i-1].block_timestamp)) errors.push(`NONMONOTONIC_TIMESTAMP:${i}`);
}

const ppb=rows.filter(x=>x.valid).map(x=>BigInt(x.dislocation_ppb_trunc));
const collateral=rows.filter(x=>x.valid).map(x=>BigInt(x.total_collateral_wei));
const liquidity=rows.filter(x=>x.valid).map(x=>BigInt(x.liquidity));

function min(xs){return xs.reduce((a,b)=>a<b?a:b);}
function max(xs){return xs.reduce((a,b)=>a>b?a:b);}
function sum(xs){return xs.reduce((a,b)=>a+b,0n);}
function quantileNearestRank(xs,p){
  const s=[...xs].sort((a,b)=>a<b?-1:a>b?1:0);
  const rank=Math.max(1,Math.ceil(p*s.length));
  return s[rank-1];
}
const stats=ppb.length?{
  min_ppb:min(ppb).toString(),
  max_ppb:max(ppb).toString(),
  mean_ppb_trunc:(sum(ppb)/BigInt(ppb.length)).toString(),
  negative_count:ppb.filter(x=>x<0n).length,
  zero_count:ppb.filter(x=>x===0n).length,
  positive_count:ppb.filter(x=>x>0n).length,
  quantiles_ppb:{
    p01:quantileNearestRank(ppb,0.01).toString(),
    p05:quantileNearestRank(ppb,0.05).toString(),
    p10:quantileNearestRank(ppb,0.10).toString(),
    p25:quantileNearestRank(ppb,0.25).toString(),
    p50:quantileNearestRank(ppb,0.50).toString(),
    p75:quantileNearestRank(ppb,0.75).toString(),
    p90:quantileNearestRank(ppb,0.90).toString(),
    p95:quantileNearestRank(ppb,0.95).toString(),
    p99:quantileNearestRank(ppb,0.99).toString()
  }
}:null;

const canonicalRows=rows.map(r=>({
  index:r.index,block_number:r.block_number,block_hash:r.block_hash,block_timestamp:r.block_timestamp,
  exchange_rate_wei_per_reth:r.exchange_rate_wei_per_reth,total_collateral_wei:r.total_collateral_wei,
  sqrtPriceX96:r.sqrtPriceX96,tick:r.tick,liquidity:r.liquidity,
  market_weth_per_reth_exact:r.market_weth_per_reth_exact,
  dislocation_exact:r.dislocation_exact,dislocation_ppb_trunc:r.dislocation_ppb_trunc,
  block_pinned:r.block_pinned,valid:r.valid
}));
const rowSetSha=crypto.createHash("sha256").update(JSON.stringify(canonicalRows)).digest("hex");
const classification=errors.length===0?"PREDICTOR_SOURCE_CENSUS_PASS":"PREDICTOR_SOURCE_CENSUS_BLOCKED";

const receipt={
  lab_id:"RETH-NAV-DISLOCATION-001",
  stage:"PREDICTOR_ONLY_CENSUS_V0.1",
  captured_at_utc:new Date().toISOString(),
  classification,
  source:{
    rpc:"https://rpc-eth.blockmachine.io",
    reth:"0xae78736Cd615f374D3085123A210448E74Fc6393",
    uniswap_v3_reth_weth_fee100_pool:"0x553e9C493678d8606d6a5ba284643dB2110Df823"
  },
  grid:{start_block:START_BLOCK,end_boundary:24_000_000,step_blocks:STEP,expected_count:TOTAL,last_block:START_BLOCK+STEP*(TOTAL-1)},
  received_chunk_count:chunks.length,
  received_row_count:rows.length,
  valid_count:rows.filter(x=>x.valid).length,
  invalid_count:rows.filter(x=>!x.valid).length,
  min_timestamp:rows.length?Math.min(...rows.map(x=>Number(x.block_timestamp))):null,
  max_timestamp:rows.length?Math.max(...rows.map(x=>Number(x.block_timestamp))):null,
  row_set_sha256:rowSetSha,
  predictor_dislocation_stats:stats,
  total_collateral_wei_stats:collateral.length?{min:min(collateral).toString(),max:max(collateral).toString(),mean_trunc:(sum(collateral)/BigInt(collateral.length)).toString()}:null,
  pool_liquidity_stats:liquidity.length?{min:min(liquidity).toString(),max:max(liquidity).toString(),mean_trunc:(sum(liquidity)/BigInt(liquidity.length)).toString()}:null,
  errors:errors.slice(0,200),
  market_returns_opened:false,
  direction_opened:false,
  holding_horizon_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0
};
fs.mkdirSync("artifacts/out",{recursive:true});
fs.writeFileSync("artifacts/out/RETH_PREDICTOR_ONLY_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
fs.writeFileSync("artifacts/out/RETH_PREDICTOR_ONLY_CENSUS_ROWS_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,stage:receipt.stage,row_set_sha256:rowSetSha,rows:canonicalRows},null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(classification!=="PREDICTOR_SOURCE_CENSUS_PASS") process.exit(2);
