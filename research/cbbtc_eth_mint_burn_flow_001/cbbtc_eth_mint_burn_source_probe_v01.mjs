import { AbiCoder, getAddress, id } from "ethers";
import fs from "fs";

const RPC=process.env.ETH_RPC_URL || "https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const MEV_LOG_RPC="https://rpc.mevblocker.io";
const ONE_RPC="https://public.1rpc.io/eth";
const FLASHBOTS_RPC="https://rpc.flashbots.net";
const HEADER_RPCS=[RPC,ARCHIVE_RPC,ONE_RPC,FLASHBOTS_RPC];
const CODE_RPCS=[ARCHIVE_RPC,MEV_LOG_RPC,RPC];
const LOG_RPCS=[RPC,ARCHIVE_RPC,MEV_LOG_RPC];

const TOKEN=getAddress("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf");
const ZERO_TOPIC="0x"+"0".repeat(64);
const TRANSFER_TOPIC=id("Transfer(address,address,uint256)").toLowerCase();
const CHUNK=10_000;
const RPC_TIMEOUT_MS=10_000;
const RANGE_ATTEMPTS=2;
const FAILOVER_ATTEMPTS=3;
const SYMBOL_SELECTOR="0x95d89b41";
const DECIMALS_SELECTOR="0x313ce567";
const coder=AbiCoder.defaultAbiCoder();

const windows=[
  {id:"A",start_iso:"2024-09-12T00:00:00Z",end_iso:"2024-10-12T00:00:00Z"},
  {id:"B",start_iso:"2025-06-01T00:00:00Z",end_iso:"2025-07-01T00:00:00Z"}
];

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const hex=n=>"0x"+BigInt(n).toString(16);

function normalizeBlockTag(tag){
  if(typeof tag==="number") return "0x"+BigInt(tag).toString(16);
  if(typeof tag==="bigint") return "0x"+tag.toString(16);
  return String(tag);
}

async function rawRpc(endpoint,method,params,timeoutMs=RPC_TIMEOUT_MS){
  const res=await fetch(endpoint,{
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({jsonrpc:"2.0",id:1,method,params}),
    signal:AbortSignal.timeout(timeoutMs)
  });
  if(!res.ok) throw new Error("HTTP_"+res.status);
  const x=await res.json();
  if(x?.error) throw new Error("RPC_"+JSON.stringify(x.error));
  if(!Object.prototype.hasOwnProperty.call(x||{},"result")) throw new Error("RPC_RESULT_MISSING");
  return x.result;
}

async function rpcFailover(endpoints,method,params,scope){
  const failures=[];
  for(const endpoint of endpoints){
    let last=null;
    for(let attempt=1;attempt<=FAILOVER_ATTEMPTS;attempt++){
      try{
        return {result:await rawRpc(endpoint,method,params),endpoint};
      }catch(e){
        last=String(e?.shortMessage||e?.message||e);
        if(attempt<FAILOVER_ATTEMPTS) await sleep(300*attempt);
      }
    }
    failures.push({endpoint,error:last});
  }
  throw new Error(scope+":"+JSON.stringify(failures));
}

function rawBlockToInternal(x,endpoint){
  if(!x) throw new Error("NULL_BLOCK");
  return {
    number:Number(BigInt(x.number)),
    hash:String(x.hash),
    timestamp:Number(BigInt(x.timestamp)),
    header_rpc:endpoint
  };
}

async function getBlockWithRetry(tag,scope){
  const {result,endpoint}=await rpcFailover(
    HEADER_RPCS,
    "eth_getBlockByNumber",
    [normalizeBlockTag(tag),false],
    scope
  );
  return rawBlockToInternal(result,endpoint);
}

async function firstBlockAtOrAfter(ts,label){
  const latest=await getBlockWithRetry("latest","BOUNDARY_LATEST_FAILED_"+label);
  let lo=0, hi=Number(latest.number);
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const b=await getBlockWithRetry(mid,"BOUNDARY_MID_FAILED_"+label+"_"+mid);
    if(Number(b.timestamp)>=ts) hi=mid;
    else lo=mid+1;
    await sleep(25);
  }
  const b=await getBlockWithRetry(lo,"BOUNDARY_FINAL_FAILED_"+label+"_"+lo);
  return {number:Number(b.number),hash:b.hash,timestamp:Number(b.timestamp)};
}

async function currentIdentity(){
  const sym=await rpcFailover(
    HEADER_RPCS,
    "eth_call",
    [{to:TOKEN,data:SYMBOL_SELECTOR},"latest"],
    "CURRENT_SYMBOL_CALL_FAILED"
  );
  const dec=await rpcFailover(
    HEADER_RPCS,
    "eth_call",
    [{to:TOKEN,data:DECIMALS_SELECTOR},"latest"],
    "CURRENT_DECIMALS_CALL_FAILED"
  );
  return {
    symbol:String(coder.decode(["string"],sym.result)[0]),
    decimals:Number(coder.decode(["uint8"],dec.result)[0]),
    symbol_rpc:sym.endpoint,
    decimals_rpc:dec.endpoint
  };
}

async function historicalCode(blockNumber,scope){
  const {result,endpoint}=await rpcFailover(
    CODE_RPCS,
    "eth_getCode",
    [TOKEN,hex(blockNumber)],
    scope
  );
  return {code:result,endpoint};
}

async function rawLogs(fromBlock,toBlock,topics){
  const failures=[];
  for(const endpoint of LOG_RPCS){
    try{
      const result=await rawRpc(endpoint,"eth_getLogs",[{
        address:TOKEN,
        fromBlock:hex(fromBlock),
        toBlock:hex(toBlock),
        topics
      }]);
      if(!Array.isArray(result)) throw new Error("BAD_LOG_RESULT");
      return result.map(log=>({
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

async function queryLogsAdaptive(fromBlock,toBlock,topics,errors,depth=0){
  let last=null;
  for(let attempt=1;attempt<=RANGE_ATTEMPTS;attempt++){
    try{
      return await rawLogs(fromBlock,toBlock,topics);
    }catch(e){
      last=String(e?.shortMessage||e?.message||e);
      if(attempt<RANGE_ATTEMPTS) await sleep(250*attempt);
    }
  }
  if(fromBlock>=toBlock){
    errors.push({from_block:fromBlock,to_block:toBlock,error:last,depth});
    return [];
  }
  const mid=Math.floor((fromBlock+toBlock)/2);
  const left=await queryLogsAdaptive(fromBlock,mid,topics,errors,depth+1);
  const right=await queryLogsAdaptive(mid+1,toBlock,topics,errors,depth+1);
  return left.concat(right);
}

async function getLogsChunked(fromBlock,toBlock,topics,kind,windowId){
  const out=[];
  const errors=[];
  let n=0;
  const total=Math.floor((toBlock-fromBlock)/CHUNK)+1;
  for(let from=fromBlock;from<=toBlock;from+=CHUNK){
    const to=Math.min(toBlock,from+CHUNK-1);
    const logs=await queryLogsAdaptive(from,to,topics,errors,0);
    out.push(...logs);
    n++;
    if(n===1||n%25===0||n===total){
      console.log(JSON.stringify({
        progress:true,window:windowId,kind,chunk:n,total_chunks:total,
        from_block:from,to_block:to,logs_so_far:out.length,errors_so_far:errors.length
      }));
    }
    await sleep(20);
  }
  return {logs:out,errors};
}

function normalizeLog(log,kind){
  const topics=(log.topics||[]).map(x=>String(x).toLowerCase());
  if(String(log.address).toLowerCase()!==TOKEN.toLowerCase()) throw new Error("WRONG_CONTRACT");
  if(topics[0]!==TRANSFER_TOPIC) throw new Error("WRONG_TOPIC0");
  if(topics.length<3) throw new Error("TOPIC_COUNT_LT_3");
  if(kind==="MINT" && topics[1]!==ZERO_TOPIC) throw new Error("MINT_FROM_NOT_ZERO");
  if(kind==="BURN" && topics[2]!==ZERO_TOPIC) throw new Error("BURN_TO_NOT_ZERO");
  const amount=BigInt(log.data);
  return {
    kind,
    block_number:Number(log.blockNumber),
    block_hash:log.blockHash,
    transaction_hash:log.transactionHash,
    log_index:Number(log.index),
    from_topic:topics[1],
    to_topic:topics[2],
    amount_raw:amount.toString()
  };
}

const receipt={
  lab_id:"CBBTC-ETH-MINT-BURN-FLOW-001",
  stage:"SOURCE_GATE_V0.1",
  transport_revision:"V0.1M",
  captured_at_utc:new Date().toISOString(),
  rpc:RPC,
  archive_rpc:ARCHIVE_RPC,
  mev_log_rpc:MEV_LOG_RPC,
  network:"ethereum",
  token:TOKEN,
  transfer_topic:TRANSFER_TOPIC,
  zero_topic:ZERO_TOPIC,
  transport:{chunk_blocks:CHUNK,rpc_timeout_ms:RPC_TIMEOUT_MS,range_attempts:RANGE_ATTEMPTS,failover_attempts:FAILOVER_ATTEMPTS,log_rpc_failover_order:LOG_RPCS},
  windows:[],
  errors:[],
  decode_errors:[],
  duplicate_txhash_logindex_count:0,
  market_returns_opened:false,
  direction_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0,
  classification:"SOURCE_BLOCKED",
  source_gate_evaluated:false,
  completed_window_count:0
};

try{
  receipt.current_identity=await currentIdentity();

  for(const w of windows){
    console.log("BEGIN_WINDOW",w.id,w.start_iso,w.end_iso);
    const startTs=Math.floor(Date.parse(w.start_iso)/1000);
    const endTs=Math.floor(Date.parse(w.end_iso)/1000);
    const start=await firstBlockAtOrAfter(startTs,w.id+"_START");
    const endBoundary=await firstBlockAtOrAfter(endTs,w.id+"_END");
    const endBlock=endBoundary.number-1;
    const endMeta=await getBlockWithRetry(endBlock,"WINDOW_END_META_FAILED_"+w.id+"_"+endBlock);

    const codeCheck=await historicalCode(endBlock,"HISTORICAL_CODE_CHECK_FAILED_"+w.id);

    const mint=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,ZERO_TOPIC],"MINT",w.id);
    const burn=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,null,ZERO_TOPIC],"BURN",w.id);

    receipt.errors.push(...mint.errors.map(e=>({window:w.id,kind:"MINT",...e})));
    receipt.errors.push(...burn.errors.map(e=>({window:w.id,kind:"BURN",...e})));

    const rows=[];
    for(const [kind,logs] of [["MINT",mint.logs],["BURN",burn.logs]]){
      for(const log of logs){
        try{ rows.push(normalizeLog(log,kind)); }
        catch(e){ receipt.decode_errors.push({window:w.id,kind,error:String(e?.message||e),tx:log.transactionHash,index:Number(log.index)}); }
      }
    }

    rows.sort((a,b)=>a.block_number-b.block_number||a.log_index-b.log_index);
    const seen=new Set();
    let dup=0;
    for(const r of rows){
      const k=r.transaction_hash.toLowerCase()+":"+r.log_index;
      if(seen.has(k)) dup++;
      seen.add(k);
    }
    receipt.duplicate_txhash_logindex_count+=dup;

    const mints=rows.filter(x=>x.kind==="MINT");
    const burns=rows.filter(x=>x.kind==="BURN");
    const mintSum=mints.reduce((a,x)=>a+BigInt(x.amount_raw),0n);
    const burnSum=burns.reduce((a,x)=>a+BigInt(x.amount_raw),0n);

    receipt.windows.push({
      id:w.id,
      start_iso:w.start_iso,
      end_iso_exclusive:w.end_iso,
      start_block:start,
      end_block:{number:endBlock,hash:endMeta.hash,timestamp:Number(endMeta.timestamp)},
      end_boundary_block:endBoundary,
      historical_code_rpc:codeCheck.endpoint,
      contract_code_present:typeof codeCheck.code==="string" && codeCheck.code!=="0x",
      mint_count:mints.length,
      burn_count:burns.length,
      zero_address_event_count:rows.length,
      mint_amount_raw:mintSum.toString(),
      burn_amount_raw:burnSum.toString(),
      net_mint_minus_burn_raw:(mintSum-burnSum).toString(),
      first_event:rows[0]||null,
      last_event:rows[rows.length-1]||null
    });
    receipt.completed_window_count=receipt.windows.length;
    console.log("END_WINDOW",w.id,"events",rows.length,"mints",mints.length,"burns",burns.length);
  }

  receipt.source_gate_evaluated=receipt.windows.length===2;
  const totalMint=receipt.windows.reduce((a,w)=>a+w.mint_count,0);
  const totalBurn=receipt.windows.reduce((a,w)=>a+w.burn_count,0);
  const pass=
    receipt.windows.length===2 &&
    receipt.windows.every(w=>w.contract_code_present && w.zero_address_event_count>=1) &&
    totalMint>=1 &&
    totalBurn>=1 &&
    receipt.errors.length===0 &&
    receipt.decode_errors.length===0 &&
    receipt.duplicate_txhash_logindex_count===0;

  receipt.total_mint_count=totalMint;
  receipt.total_burn_count=totalBurn;
  receipt.classification=pass?"SOURCE_PASS":"SOURCE_BLOCKED";
}catch(e){
  receipt.errors.push({scope:"fatal",error:String(e?.shortMessage||e?.message||e)});
  receipt.classification="SOURCE_BLOCKED";
}

fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/CBBTC_ETH_MINT_BURN_SOURCE_GATE_RECEIPT_V0.1.json",JSON.stringify(receipt,null,2)+"\n");
console.log(JSON.stringify(receipt,null,2));
if(receipt.classification!=="SOURCE_PASS") process.exit(2);
