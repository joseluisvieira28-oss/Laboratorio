import { JsonRpcProvider, Interface, getAddress } from "ethers";
import fs from "fs";

const HEADER_RPC="https://ethereum-rpc.publicnode.com";
const ARCHIVE_RPC="https://rpc-eth.blockmachine.io";
const header=new JsonRpcProvider(HEADER_RPC);
const archive=new JsonRpcProvider(ARCHIVE_RPC);

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
const multiI=new Interface([
 "function aggregate3(tuple(address target,bool allowFailure,bytes callData)[] calls) payable returns (tuple(bool success,bytes returnData)[] returnData)"
]);

const calls=[
 {name:"getExchangeRate",target:RETH,data:rethI.encodeFunctionData("getExchangeRate")},
 {name:"getTotalCollateral",target:RETH,data:rethI.encodeFunctionData("getTotalCollateral")},
 {name:"slot0",target:POOL,data:poolI.encodeFunctionData("slot0")},
 {name:"liquidity",target:POOL,data:poolI.encodeFunctionData("liquidity")}
];

function hexBlock(n){ return "0x"+BigInt(n).toString(16); }
function norm(x){ return String(x).toLowerCase(); }

async function rawCall(provider,to,data,tag){
 return await provider.send("eth_call",[{to,data},tag]);
}

const out={
 lab_id:"RETH-NAV-DISLOCATION-001",
 stage:"SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_V0.1C",
 captured_at_utc:new Date().toISOString(),
 header_rpc:HEADER_RPC,
 archive_rpc:ARCHIVE_RPC,
 multicall3:MULTI,
 blocks:[],
 errors:[],
 market_returns_opened:false,
 pnl_opened:false,
 mutation:false,
 promotion_credit:0
};

for(const n of BLOCKS){
 try{
  const [hb,ab]=await Promise.all([header.getBlock(n),archive.getBlock(n)]);
  if(!hb||!ab) throw new Error("BLOCK_METADATA_MISSING");
  const hashesEqual=norm(hb.hash)===norm(ab.hash);

  const direct={};
  for(const c of calls){
   direct[c.name]=await rawCall(archive,c.target,c.data,hexBlock(n));
  }

  const calldata=multiI.encodeFunctionData("aggregate3",[
    calls.map(c=>({target:c.target,allowFailure:false,callData:c.data}))
  ]);
  const byNumberRaw=await rawCall(archive,MULTI,calldata,hexBlock(n));
  const byHashRaw=await rawCall(archive,MULTI,calldata,{blockHash:hb.hash,requireCanonical:true});
  const byNumber=multiI.decodeFunctionResult("aggregate3",byNumberRaw)[0];
  const byHash=multiI.decodeFunctionResult("aggregate3",byHashRaw)[0];

  const comparisons=calls.map((c,i)=>{
    const num=String(byNumber[i].returnData);
    const hash=String(byHash[i].returnData);
    return {
      name:c.name,
      direct_return_data:direct[c.name],
      multicall_number_success:Boolean(byNumber[i].success),
      multicall_hash_success:Boolean(byHash[i].success),
      multicall_by_number_return_data:num,
      multicall_by_hash_return_data:hash,
      direct_equals_multicall_number:norm(direct[c.name])===norm(num),
      multicall_number_equals_hash:norm(num)===norm(hash)
    };
  });

  out.blocks.push({
    block_number:n,
    public_header_hash:hb.hash,
    archive_header_hash:ab.hash,
    block_timestamp:Number(hb.timestamp),
    block_hash_equal:hashesEqual,
    comparisons,
    all_exact:hashesEqual && comparisons.every(x=>
      x.multicall_number_success &&
      x.multicall_hash_success &&
      x.direct_equals_multicall_number &&
      x.multicall_number_equals_hash
    )
  });
 }catch(e){
  out.errors.push({block_number:n,error:String(e?.shortMessage||e?.message||e)});
 }
}

out.classification=
 out.errors.length===0 &&
 out.blocks.length===BLOCKS.length &&
 out.blocks.every(x=>x.all_exact)
 ? "SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS"
 : "SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_FAIL";

fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify(out,null,2));
if(out.classification!=="SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS") process.exit(2);
