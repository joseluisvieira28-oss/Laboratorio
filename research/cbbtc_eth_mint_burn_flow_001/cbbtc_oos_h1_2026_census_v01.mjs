import { JsonRpcProvider, getAddress, id } from "ethers";
import fs from "fs";
import crypto from "crypto";

const RPC=process.env.ETH_RPC_URL || "https://ethereum-rpc.publicnode.com";
const provider=new JsonRpcProvider(RPC);
const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const MEV_LOG_RPC="https://rpc.mevblocker.io";
const ONE_RPC="https://public.1rpc.io/eth";
const FLASHBOTS_RPC="https://rpc.flashbots.net";
const HEADER_RPCS=[RPC,ARCHIVE_RPC,ONE_RPC,FLASHBOTS_RPC];
const LOG_RPCS=[RPC,ARCHIVE_RPC,MEV_LOG_RPC];
const archiveProvider=new JsonRpcProvider(ARCHIVE_RPC);

const TOKEN=getAddress("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf");
const START_ISO="2025-12-31T00:00:00Z";
const END_ISO="2026-07-01T00:00:00Z";
const TRANSFER_TOPIC=id("Transfer(address,address,uint256)").toLowerCase();
const ZERO_TOPIC="0x"+"0".repeat(64);
const CHUNK=10_000;
const RPC_TIMEOUT_MS=10_000;
const HEADER_ATTEMPTS=3;
const ARCHIVE_ATTEMPTS=3;
const RANGE_ATTEMPTS=2;
const TOTAL_SUPPLY_SELECTOR="0x18160ddd";
const hex=n=>"0x"+BigInt(n).toString(16);

if(process.env.CBBTC_OOS_OPEN_AUTHORITY!=="AUTHORIZED") throw new Error("PROTECTED_2026_OPEN_AUTHORITY_MISSING");

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function normalizeBlockTag(tag){
  if(tag==="latest"||tag==="finalized"||tag==="safe") return tag;
  if(typeof tag==="number") return "0x"+BigInt(tag).toString(16);
  return String(tag);
}

async function rawRpc(endpoint,method,params){
  const res=await fetch(endpoint,{
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(RPC_TIMEOUT_MS)
  });
  if(!res.ok) throw new Error("HTTP_"+res.status);
  const x=await res.json();
  if(x?.error) throw new Error("RPC_"+JSON.stringify(x.error));
  return x?.result;
}

function rawBlockToInternal(x){
  if(!x) throw new Error("NULL_BLOCK");
  return {
    number:Number(BigInt(x.number)),
    hash:String(x.hash),
    timestamp:Number(BigInt(x.timestamp))
  };
}

async function getBlockWithRetry(tag,scope){
  const failures=[];
  for(const endpoint of HEADER_RPCS){
    let last=null;
    for(let attempt=1;attempt<=HEADER_ATTEMPTS;attempt++){
      try{
        const x=await rawRpc(endpoint,"eth_getBlockByNumber",[normalizeBlockTag(tag),false]);
        return rawBlockToInternal(x);
      }catch(e){
        last=String(e?.shortMessage||e?.message||e);
        if(attempt<HEADER_ATTEMPTS) await sleep(300*attempt);
      }
    }
    failures.push({endpoint,error:last});
  }
  throw new Error(scope+":"+JSON.stringify(failures));
}

async function firstBlockAtOrAfter(ts,label){
  const latest=await getBlockWithRetry("latest","BOUNDARY_LATEST_FAILED_"+label);
  let lo=0,hi=Number(latest.number);
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const b=await getBlockWithRetry(mid,"BOUNDARY_MID_FAILED_"+label+"_"+mid);
    if(Number(b.timestamp)>=ts) hi=mid; else lo=mid+1;
    await sleep(100);
  }
  const b=await getBlockWithRetry(lo,"BOUNDARY_FINAL_FAILED_"+label+"_"+lo);
  return {number:Number(b.number),hash:b.hash,timestamp:Number(b.timestamp)};
}

async function archiveSendWithRetry(method,params,scope){
  const failures=[];
  for(const endpoint of [ARCHIVE_RPC,MEV_LOG_RPC]){
    let last=null;
    for(let attempt=1;attempt<=ARCHIVE_ATTEMPTS;attempt++){
      try{
        const result=await rawRpc(endpoint,method,params);
        console.log("ARCHIVE_RPC_USED",scope,endpoint);
        return {result,endpoint};
      }catch(e){
        last=String(e?.shortMessage||e?.message||e);
        if(attempt<ARCHIVE_ATTEMPTS) await sleep(400*attempt);
      }
    }
    failures.push({endpoint,error:last});
  }
  throw new Error(scope+":"+JSON.stringify(failures));
}

async function rawLogs(fromBlock,toBlock,topics){
  const failures=[];
  for(const endpoint of LOG_RPCS){
    try{
      const logs=await rawRpc(endpoint,"eth_getLogs",[{
        address:TOKEN,
        fromBlock:hex(fromBlock),
        toBlock:hex(toBlock),
        topics
      }]);
      if(!Array.isArray(logs)) throw new Error("BAD_LOG_RESULT");
      return logs.map(log=>({
        address:log.address,
        topics:log.topics||[],
        data:log.data,
        blockNumber:Number(BigInt(log.blockNumber)),
        blockHash:log.blockHash,
        transactionHash:log.transactionHash,
        index:Number(BigInt(log.logIndex))
      }));
    }catch(e){
      failures.push({endpoint,error:String(e?.shortMessage||e?.message||e).slice(0,500)});
    }
  }
  throw new Error("LOG_RPC_FAILOVER_EXHAUSTED:"+JSON.stringify(failures));
}

async function queryLogsAdaptive(fromBlock,toBlock,topics,kind,errors,depth=0){
  let last=null;
  for(let attempt=1;attempt<=RANGE_ATTEMPTS;attempt++){
    try{
      return await rawLogs(fromBlock,toBlock,topics);
    }catch(e){
      last=String(e?.shortMessage||e?.message||e);
      if(attempt<RANGE_ATTEMPTS) await sleep(300*attempt);
    }
  }
  if(fromBlock>=toBlock){
    errors.push({kind,from_block:fromBlock,to_block:toBlock,error:last,depth});
    return [];
  }
  const mid=Math.floor((fromBlock+toBlock)/2);
  const left=await queryLogsAdaptive(fromBlock,mid,topics,kind,errors,depth+1);
  await sleep(120);
  const right=await queryLogsAdaptive(mid+1,toBlock,topics,kind,errors,depth+1);
  return left.concat(right);
}

async function getLogsChunked(fromBlock,toBlock,topics,kind){
  const out=[],errors=[];
  for(let from=fromBlock;from<=toBlock;from+=CHUNK){
    const to=Math.min(toBlock,from+CHUNK-1);
    const logs=await queryLogsAdaptive(from,to,topics,kind,errors,0);
    out.push(...logs);
    if(((from-fromBlock)/CHUNK+1)%100===0) console.log(kind,"chunk",from,to,"logs",out.length,"errors",errors.length);
    await sleep(100);
  }
  return {logs:out,errors};
}

function normalize(log,kind){
  const topics=(log.topics||[]).map(x=>String(x).toLowerCase());
  if(String(log.address).toLowerCase()!==TOKEN.toLowerCase()) throw new Error("WRONG_CONTRACT");
  if(topics[0]!==TRANSFER_TOPIC) throw new Error("WRONG_TOPIC0");
  if(topics.length<3) throw new Error("TOPIC_COUNT_LT_3");
  if(kind==="MINT"&&topics[1]!==ZERO_TOPIC) throw new Error("MINT_FROM_NOT_ZERO");
  if(kind==="BURN"&&topics[2]!==ZERO_TOPIC) throw new Error("BURN_TO_NOT_ZERO");
  return {
    kind,
    block_number:Number(log.blockNumber),
    block_hash:log.blockHash,
    transaction_hash:log.transactionHash,
    log_index:Number(log.index),
    amount_raw:BigInt(log.data).toString()
  };
}

async function batchBlockHeaders(blockNumbers){
  const result=new Map();
  const nums=[...new Set(blockNumbers)].sort((a,b)=>a-b);
  for(let i=0;i<nums.length;i++){
    const n=nums[i];
    const h=await getBlockWithRetry(n,"EVENT_HEADER_FAILED_"+n);
    result.set(n,h);
    if(i===0||(i+1)%50===0||i===nums.length-1){
      console.log("HEADER_PROGRESS",i+1,nums.length,n,h.header_rpc||"unknown");
    }
    await sleep(40);
  }
  return result;
}

function utcDay(ts){ return new Date(ts*1000).toISOString().slice(0,10); }
function dateRange(start,endExclusive){
  const out=[];
  for(let d=new Date(start);d<new Date(endExclusive);d=new Date(d.getTime()+86400000)) out.push(d.toISOString().slice(0,10));
  return out;
}
function sha(x){return crypto.createHash("sha256").update(JSON.stringify(x)).digest("hex");}
function qBig(xs,p){
  const s=[...xs].sort((a,b)=>a<b?-1:a>b?1:0);
  const rank=Math.max(1,Math.ceil(p*s.length));
  return s[rank-1];
}

const receipt={
  lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",
  stage:"OOS_H1_2026_PREDICTOR_CENSUS_V0.1",
  captured_at_utc:new Date().toISOString(),
  rpc:RPC,
  archive_rpc:ARCHIVE_RPC,
  token:TOKEN,
  period:{start_iso:START_ISO,end_iso_exclusive:END_ISO},
  classification:"OOS_SOURCE_BLOCKED",
  errors:[],
  decode_errors:[],
  duplicate_txhash_logindex_count:0,
  market_returns_opened:false,
  price_data_opened:false,
  direction_opened:false,
  pnl_opened:false,
  protected_2026_opened:true,
  mutation:false,
  promotion_credit:0
};

try{
  const start=await firstBlockAtOrAfter(Math.floor(Date.parse(START_ISO)/1000),"CENSUS_START");
  const endBoundary=await firstBlockAtOrAfter(Math.floor(Date.parse(END_ISO)/1000),"CENSUS_END");
  const endBlock=endBoundary.number-1;
  const endMeta=await getBlockWithRetry(endBlock,"END_META_FAILED_"+endBlock);
  const startAnchorBlock=start.number-1;
  if(startAnchorBlock<0) throw new Error("BAD_START_ANCHOR_BLOCK");
  const startAnchorMeta=await getBlockWithRetry(startAnchorBlock,"START_ANCHOR_META_FAILED_"+startAnchorBlock);
  const startSupplyCall=await archiveSendWithRetry(
    "eth_call",
    [{to:TOKEN,data:TOTAL_SUPPLY_SELECTOR},{blockHash:startAnchorMeta.hash,requireCanonical:true}],
    "START_SUPPLY_BLOCKHASH_CALL_FAILED"
  );
  const endSupplyCall=await archiveSendWithRetry(
    "eth_call",
    [{to:TOKEN,data:TOTAL_SUPPLY_SELECTOR},{blockHash:endMeta.hash,requireCanonical:true}],
    "END_SUPPLY_BLOCKHASH_CALL_FAILED"
  );
  const archiveStartSupply=BigInt(startSupplyCall.result);
  const archiveEndSupply=BigInt(endSupplyCall.result);
  receipt.boundaries={start_block:start,end_block:{number:endBlock,hash:endMeta.hash,timestamp:Number(endMeta.timestamp)},end_boundary_block:endBoundary};
  receipt.supply_anchor={
    block_binding:"EIP-1898 blockHash requireCanonical",
    start_anchor_block:startAnchorBlock,
    start_anchor_hash:startAnchorMeta.hash,
    end_anchor_block:endBlock,
    end_anchor_hash:endMeta.hash,
    archive_start_total_supply_raw:archiveStartSupply.toString(),
    archive_end_total_supply_raw:archiveEndSupply.toString(),
    archive_start_rpc:startSupplyCall.endpoint,
    archive_end_rpc:endSupplyCall.endpoint
  };

  const mint=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,ZERO_TOPIC],"MINT");
  const burn=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,null,ZERO_TOPIC],"BURN");
  receipt.errors.push(...mint.errors,...burn.errors);

  const ledger=[];
  for(const [kind,logs] of [["MINT",mint.logs],["BURN",burn.logs]]){
    for(const log of logs){
      try{ledger.push(normalize(log,kind));}
      catch(e){receipt.decode_errors.push({kind,tx:log.transactionHash,index:Number(log.index),error:String(e?.message||e)});}
    }
  }
  ledger.sort((a,b)=>a.block_number-b.block_number||a.log_index-b.log_index);

  const seen=new Set();
  for(const r of ledger){
    const k=r.transaction_hash.toLowerCase()+":"+r.log_index;
    if(seen.has(k)) receipt.duplicate_txhash_logindex_count++;
    seen.add(k);
  }

  const headers=await batchBlockHeaders(ledger.map(x=>x.block_number));
  for(const r of ledger){
    const h=headers.get(r.block_number);
    if(!h) throw new Error("HEADER_NOT_FOUND_"+r.block_number);
    if(String(h.hash).toLowerCase()!==String(r.block_hash).toLowerCase()) throw new Error("LOG_HEADER_HASH_MISMATCH_"+r.block_number);
    r.block_timestamp=h.timestamp;
    r.utc_day=utcDay(h.timestamp);
  }

  const days=dateRange(START_ISO,END_ISO);
  const map=new Map(days.map(d=>[d,{utc_day:d,mint_count:0,burn_count:0,mint_amount_raw:"0",burn_amount_raw:"0",net_mint_minus_burn_raw:"0",gross_flow_raw:"0",first_event_block:null,last_event_block:null}]));
  for(const r of ledger){
    const d=map.get(r.utc_day);
    if(!d) throw new Error("EVENT_OUTSIDE_FROZEN_PERIOD_"+r.utc_day);
    const amt=BigInt(r.amount_raw);
    if(r.kind==="MINT"){d.mint_count++;d.mint_amount_raw=(BigInt(d.mint_amount_raw)+amt).toString();}
    else {d.burn_count++;d.burn_amount_raw=(BigInt(d.burn_amount_raw)+amt).toString();}
    d.first_event_block=d.first_event_block===null?r.block_number:Math.min(d.first_event_block,r.block_number);
    d.last_event_block=d.last_event_block===null?r.block_number:Math.max(d.last_event_block,r.block_number);
  }
  let reconstructedSupply=archiveStartSupply;
  const daily=days.map(day=>{
    const d=map.get(day);
    const m=BigInt(d.mint_amount_raw),b=BigInt(d.burn_amount_raw);
    const net=m-b;
    const priorSupply=reconstructedSupply;
    const endSupply=priorSupply+net;
    if(endSupply<0n) throw new Error("NEGATIVE_RECONSTRUCTED_SUPPLY_"+day);
    d.net_mint_minus_burn_raw=net.toString();
    d.gross_flow_raw=(m+b).toString();
    d.prior_supply_raw=priorSupply.toString();
    d.end_supply_raw=endSupply.toString();
    d.net_flow_rate_exact=priorSupply>0n?{numerator:net.toString(),denominator:priorSupply.toString()}:null;
    reconstructedSupply=endSupply;
    return d;
  });
  receipt.supply_reconciliation={
    reconstructed_end_total_supply_raw:reconstructedSupply.toString(),
    archive_end_total_supply_raw:archiveEndSupply.toString(),
    exact_equal:reconstructedSupply===archiveEndSupply
  };

  const ledgerCanonical=ledger.map(r=>({...r}));
  const dailyCanonical=daily.map(r=>({...r}));
  const net=daily.map(r=>BigInt(r.net_mint_minus_burn_raw));
  const gross=daily.map(r=>BigInt(r.gross_flow_raw));

  receipt.ledger_event_count=ledger.length;
  receipt.mint_event_count=ledger.filter(x=>x.kind==="MINT").length;
  receipt.burn_event_count=ledger.filter(x=>x.kind==="BURN").length;
  receipt.daily_row_count=daily.length;
  receipt.active_flow_day_count=daily.filter(x=>BigInt(x.gross_flow_raw)>0n).length;
  receipt.zero_flow_day_count=daily.filter(x=>BigInt(x.gross_flow_raw)===0n).length;
  receipt.ledger_sha256=sha(ledgerCanonical);
  receipt.daily_series_sha256=sha(dailyCanonical);
  receipt.daily_net_flow_stats={
    min_raw:net.reduce((a,b)=>a<b?a:b).toString(),
    max_raw:net.reduce((a,b)=>a>b?a:b).toString(),
    mean_raw_trunc:(net.reduce((a,b)=>a+b,0n)/BigInt(net.length)).toString(),
    p05:qBig(net,.05).toString(),
    p10:qBig(net,.10).toString(),
    p50:qBig(net,.50).toString(),
    p90:qBig(net,.90).toString(),
    p95:qBig(net,.95).toString()
  };
  receipt.daily_gross_flow_stats={
    min_raw:gross.reduce((a,b)=>a<b?a:b).toString(),
    max_raw:gross.reduce((a,b)=>a>b?a:b).toString(),
    mean_raw_trunc:(gross.reduce((a,b)=>a+b,0n)/BigInt(gross.length)).toString(),
    p50:qBig(gross,.50).toString(),
    p90:qBig(gross,.90).toString(),
    p95:qBig(gross,.95).toString()
  };

  const expectedDays=days.length;
  const pass=
    receipt.errors.length===0 &&
    receipt.decode_errors.length===0 &&
    receipt.duplicate_txhash_logindex_count===0 &&
    ledger.length>0 &&
    receipt.mint_event_count>0 &&
    receipt.burn_event_count>0 &&
    receipt.supply_reconciliation?.exact_equal===true &&
    daily.length===expectedDays &&
    daily[0].utc_day==="2025-12-31" &&
    daily[daily.length-1].utc_day==="2026-06-30";

  receipt.classification=pass?"OOS_PREDICTOR_CENSUS_PASS":"OOS_SOURCE_BLOCKED";

  fs.mkdirSync("artifacts/oos_h1_2026",{recursive:true});
  fs.writeFileSync("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
  fs.writeFileSync("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_FLOW_LEDGER_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,ledger_sha256:receipt.ledger_sha256,events:ledgerCanonical},null,2)+"\n");
  fs.writeFileSync("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_DAILY_FLOW_V0.1.json",JSON.stringify({lab_id:receipt.lab_id,daily_series_sha256:receipt.daily_series_sha256,days:dailyCanonical},null,2)+"\n");
}catch(e){
  receipt.errors.push({scope:"fatal",error:String(e?.shortMessage||e?.message||e)});
  fs.mkdirSync("artifacts/oos_h1_2026",{recursive:true});
  fs.writeFileSync("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_CENSUS_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
}

console.log(JSON.stringify(receipt,null,2));
if(receipt.classification!=="OOS_PREDICTOR_CENSUS_PASS") process.exit(2);
