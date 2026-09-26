import { JsonRpcProvider, Contract, getAddress, id } from "ethers";
import fs from "fs";

const RPC=process.env.ETH_RPC_URL || "https://ethereum-rpc.publicnode.com";
const provider=new JsonRpcProvider(RPC);
const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const archiveProvider=new JsonRpcProvider(ARCHIVE_RPC);

const TOKEN=getAddress("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf");
const ZERO_TOPIC="0x"+"0".repeat(64);
const TRANSFER_TOPIC=id("Transfer(address,address,uint256)").toLowerCase();
const CHUNK=20_000;

const windows=[
  {id:"A",start_iso:"2024-09-12T00:00:00Z",end_iso:"2024-10-12T00:00:00Z"},
  {id:"B",start_iso:"2025-06-01T00:00:00Z",end_iso:"2025-07-01T00:00:00Z"}
];

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const hex=n=>"0x"+BigInt(n).toString(16);

async function firstBlockAtOrAfter(ts){
  const latest=await provider.getBlock("latest");
  let lo=0, hi=Number(latest.number);
  while(lo<hi){
    const mid=Math.floor((lo+hi)/2);
    const b=await provider.getBlock(mid);
    if(!b) throw new Error("BLOCK_LOOKUP_FAILED_"+mid);
    if(Number(b.timestamp)>=ts) hi=mid;
    else lo=mid+1;
  }
  const b=await provider.getBlock(lo);
  if(!b) throw new Error("BOUNDARY_BLOCK_MISSING_"+lo);
  return {number:Number(b.number),hash:b.hash,timestamp:Number(b.timestamp)};
}

async function getLogsChunked(fromBlock,toBlock,topics){
  const out=[];
  const errors=[];
  for(let from=fromBlock;from<=toBlock;from+=CHUNK){
    const to=Math.min(toBlock,from+CHUNK-1);
    let ok=false,last=null;
    for(let attempt=1;attempt<=6;attempt++){
      try{
        const logs=await provider.getLogs({address:TOKEN,fromBlock:from,toBlock:to,topics});
        out.push(...logs);
        ok=true;
        break;
      }catch(e){
        last=String(e?.shortMessage||e?.message||e);
        if(attempt<6) await sleep(700*attempt);
      }
    }
    if(!ok) errors.push({from_block:from,to_block:to,error:last});
    await sleep(80);
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
  captured_at_utc:new Date().toISOString(),
  rpc:RPC,
  archive_rpc:ARCHIVE_RPC,
  network:"ethereum",
  token:TOKEN,
  transfer_topic:TRANSFER_TOPIC,
  zero_topic:ZERO_TOPIC,
  windows:[],
  errors:[],
  decode_errors:[],
  duplicate_txhash_logindex_count:0,
  market_returns_opened:false,
  direction_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0,
  classification:"SOURCE_BLOCKED"
};

try{
  const token=new Contract(TOKEN,[
    "function symbol() view returns (string)",
    "function decimals() view returns (uint8)"
  ],provider);
  receipt.current_identity={
    symbol:await token.symbol(),
    decimals:Number(await token.decimals())
  };

  for(const w of windows){
    const startTs=Math.floor(Date.parse(w.start_iso)/1000);
    const endTs=Math.floor(Date.parse(w.end_iso)/1000);
    const start=await firstBlockAtOrAfter(startTs);
    const endBoundary=await firstBlockAtOrAfter(endTs);
    const endBlock=endBoundary.number-1;
    const endMeta=await provider.getBlock(endBlock);
    if(!endMeta) throw new Error("WINDOW_END_META_MISSING_"+w.id);

    let code;
    try{
      code=await archiveProvider.send("eth_getCode",[TOKEN,hex(endBlock)]);
    }catch(e){
      throw new Error("HISTORICAL_CODE_CHECK_FAILED_"+w.id+":"+String(e?.shortMessage||e?.message||e));
    }
    const mint=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,ZERO_TOPIC]);
    const burn=await getLogsChunked(start.number,endBlock,[TRANSFER_TOPIC,null,ZERO_TOPIC]);

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
      contract_code_present:typeof code==="string" && code!=="0x",
      mint_count:mints.length,
      burn_count:burns.length,
      zero_address_event_count:rows.length,
      mint_amount_raw:mintSum.toString(),
      burn_amount_raw:burnSum.toString(),
      net_mint_minus_burn_raw:(mintSum-burnSum).toString(),
      first_event:rows[0]||null,
      last_event:rows[rows.length-1]||null
    });
  }

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
