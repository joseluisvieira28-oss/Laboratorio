import { JsonRpcProvider, Interface, getAddress, ZeroAddress } from "ethers";
import fs from "fs";

const HEADER_RPC=process.env.ETH_HEADER_RPC_URL || "https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC=process.env.ETH_ARCHIVE_RPC_URL || "https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);

const CBETH=getAddress("0xBe9895146f7AF43049ca1c1AE358B0541Ea49704");
const WETH=getAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2");
const FACTORY=getAddress("0x1F98431c8aD98523631AE4a59f267346ea31F984");
const SENTINELS=[16_000_000,18_000_000,20_000_000,22_000_000,24_000_000];
const FEES=[100,500,3000,10000];

const cbI=new Interface([
 "function exchangeRate() view returns (uint256)",
 "function totalSupply() view returns (uint256)"
]);
const factoryI=new Interface(["function getPool(address,address,uint24) view returns (address)"]);
const poolI=new Interface([
 "function token0() view returns (address)",
 "function token1() view returns (address)",
 "function liquidity() view returns (uint128)",
 "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)"
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
      if(attempt<max) await sleep(700*attempt);
    }
  }
  throw new Error(scope+":"+last);
}

async function headerMeta(n){
  const b=await retry(()=>header.getBlock(n),"HEADER_"+n);
  if(!b) throw new Error("HEADER_NULL_"+n);
  return {number:Number(b.number),hash:b.hash,timestamp:Number(b.timestamp)};
}

async function finalizedMeta(){
  const x=await retry(()=>rpc(HEADER_RPC,"eth_getBlockByNumber",["finalized",false]),"FINALIZED_HEADER");
  if(!x) throw new Error("FINALIZED_NULL");
  return {number:Number(BigInt(x.number)),hash:x.hash,timestamp:Number(BigInt(x.timestamp))};
}

async function archiveCall(to,data,blockHash,scope){
  return await retry(()=>rpc(ARCHIVE_RPC,"eth_call",[
    {to,data},
    {blockHash,requireCanonical:true}
  ]),scope);
}

async function latestCall(to,data,scope){
  return await retry(()=>rpc(HEADER_RPC,"eth_call",[{to,data},"latest"]),scope);
}

function exactWethPerCbeth(token0,token1,sqrtPriceX96){
  const q192=1n<<192n;
  const s=BigInt(sqrtPriceX96);
  const raw=s*s;
  if(token0.toLowerCase()===CBETH.toLowerCase()&&token1.toLowerCase()===WETH.toLowerCase()){
    return {numerator:raw.toString(),denominator:q192.toString(),orientation:"WETH_PER_CBETH"};
  }
  if(token0.toLowerCase()===WETH.toLowerCase()&&token1.toLowerCase()===CBETH.toLowerCase()){
    return {numerator:q192.toString(),denominator:raw.toString(),orientation:"WETH_PER_CBETH_INVERTED"};
  }
  throw new Error("TOKEN_ORDER_NOT_CBETH_WETH");
}

const out={
  lab_id:"CBETH-REDEMPTION-BASIS-001",
  stage:"SOURCE_GATE_V0.1",
  captured_at_utc:new Date().toISOString(),
  classification:"SOURCE_BLOCKED",
  source:{
    header_rpc:HEADER_RPC,
    archive_rpc:ARCHIVE_RPC,
    cbeth:CBETH,
    weth:WETH,
    uniswap_v3_factory:FACTORY,
    block_binding:"EIP-1898 blockHash requireCanonical"
  },
  fixed_historical_sentinels:SENTINELS,
  fee_tiers_probed:FEES,
  protocol_anchor:[],
  pools:[],
  errors:[],
  silent_latest_fallback:false,
  market_returns_opened:false,
  direction_opened:false,
  pnl_opened:false,
  mutation:false,
  promotion_credit:0
};

try{
  const finalized=await finalizedMeta();
  out.finalized_block=finalized;
  const metas=[];
  for(const n of SENTINELS) metas.push(await headerMeta(n));
  metas.push(finalized);

  for(const m of metas){
    try{
      const [rateRaw,supplyRaw]=await Promise.all([
        archiveCall(CBETH,cbI.encodeFunctionData("exchangeRate"),m.hash,"CBETH_RATE_"+m.number),
        archiveCall(CBETH,cbI.encodeFunctionData("totalSupply"),m.hash,"CBETH_SUPPLY_"+m.number)
      ]);
      const rate=cbI.decodeFunctionResult("exchangeRate",rateRaw)[0];
      const supply=cbI.decodeFunctionResult("totalSupply",supplyRaw)[0];
      out.protocol_anchor.push({
        ...m,
        exchange_rate_wei_per_cbeth:BigInt(rate).toString(),
        total_supply_raw:BigInt(supply).toString(),
        block_pinned_by_hash:true
      });
    }catch(e){
      out.errors.push({scope:"protocol_anchor",block_number:m.number,error:String(e?.message||e)});
    }
  }

  for(const fee of FEES){
    const poolRaw=await latestCall(
      FACTORY,
      factoryI.encodeFunctionData("getPool",[CBETH,WETH,fee]),
      "FACTORY_POOL_"+fee
    );
    const poolAddr=getAddress(factoryI.decodeFunctionResult("getPool",poolRaw)[0]);
    const entry={fee,pool:poolAddr,discovered:poolAddr!==ZeroAddress,historical_reads:[],errors:[]};
    if(poolAddr===ZeroAddress){out.pools.push(entry);continue;}

    try{
      const [t0Raw,t1Raw]=await Promise.all([
        latestCall(poolAddr,poolI.encodeFunctionData("token0"),"TOKEN0_"+fee),
        latestCall(poolAddr,poolI.encodeFunctionData("token1"),"TOKEN1_"+fee)
      ]);
      entry.token0=getAddress(poolI.decodeFunctionResult("token0",t0Raw)[0]);
      entry.token1=getAddress(poolI.decodeFunctionResult("token1",t1Raw)[0]);
      entry.token_order_verified=
        [entry.token0.toLowerCase(),entry.token1.toLowerCase()].sort().join(":")===
        [CBETH.toLowerCase(),WETH.toLowerCase()].sort().join(":");
    }catch(e){
      entry.errors.push({scope:"pool_identity",error:String(e?.message||e)});
    }

    if(entry.token_order_verified){
      for(const m of metas){
        try{
          const [slotRaw,liqRaw]=await Promise.all([
            archiveCall(poolAddr,poolI.encodeFunctionData("slot0"),m.hash,"SLOT0_"+fee+"_"+m.number),
            archiveCall(poolAddr,poolI.encodeFunctionData("liquidity"),m.hash,"LIQ_"+fee+"_"+m.number)
          ]);
          const slot=poolI.decodeFunctionResult("slot0",slotRaw);
          const liq=poolI.decodeFunctionResult("liquidity",liqRaw)[0];
          const exact=exactWethPerCbeth(entry.token0,entry.token1,slot.sqrtPriceX96);
          entry.historical_reads.push({
            ...m,
            sqrtPriceX96:BigInt(slot.sqrtPriceX96).toString(),
            tick:Number(slot.tick),
            liquidity:BigInt(liq).toString(),
            positive_liquidity:BigInt(liq)>0n,
            exact_weth_per_cbeth:exact,
            block_pinned_by_hash:true
          });
        }catch(e){
          entry.errors.push({scope:"historical_pool_state",block_number:m.number,error:String(e?.message||e)});
        }
      }
    }
    out.pools.push(entry);
  }

  const allPoints=[...SENTINELS,finalized.number];
  const anchorBlocks=new Set(out.protocol_anchor.filter(x=>BigInt(x.exchange_rate_wei_per_cbeth)>0n).map(x=>x.number));
  const anchorPass=allPoints.every(n=>anchorBlocks.has(n));

  const qualifying=out.pools.filter(p=>{
    if(!p.discovered||p.token_order_verified!==true) return false;
    const hist=p.historical_reads.filter(x=>SENTINELS.includes(x.number)&&x.positive_liquidity);
    const fin=p.historical_reads.find(x=>x.number===finalized.number&&x.positive_liquidity);
    return hist.length>=4 && Boolean(fin);
  });

  out.gates={
    protocol_anchor_all_fixed_plus_finalized:anchorPass,
    discovered_nonzero_pool_count:out.pools.filter(p=>p.discovered).length,
    qualifying_direct_pool_count:qualifying.length,
    qualifying_direct_pools:qualifying.map(p=>({fee:p.fee,pool:p.pool})),
    silent_latest_fallback:false
  };
  out.classification=anchorPass&&qualifying.length>=1?"SOURCE_PASS":"SOURCE_BLOCKED";
}catch(e){
  out.errors.push({scope:"fatal",error:String(e?.message||e)});
  out.classification="SOURCE_BLOCKED";
}

fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/CBETH_REDEMPTION_BASIS_SOURCE_GATE_RECEIPT_V0.1.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
if(out.classification!=="SOURCE_PASS") process.exit(2);
