import { Interface } from 'ethers';
import fs from 'node:fs';
import crypto from 'node:crypto';

export const BLOCK=16000000;
export const CBETH='0xBe9895146f7AF43049ca1c1AE358B0541Ea49704';
const iface=new Interface(['function exchangeRate() view returns (uint256)']);
export function validHeader(x) {
  return x && x.number===`0x${BLOCK.toString(16)}` && /^0x[0-9a-fA-F]{64}$/.test(x.hash) && /^0x[0-9a-fA-F]+$/.test(x.timestamp);
}
export function validRate(x) { return typeof x==='string' && /^0x[0-9a-fA-F]{64}$/.test(x) && BigInt(x)>0n; }
export async function run() {
  const out={parent_sha:'41909a1ac0f86166e7fac4a3deb9f9c9a120b35d',classification:'SOURCE_BLOCKED',scope:'necessary anchor transport only',started_at:new Date().toISOString(),routes:[],market_outcomes_opened:false,protected_2026_opened:false,pnl_opened:false,mutation:false};
  const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
  const root='receipts/diamond_cbeth_20261020'; fs.mkdirSync(root,{recursive:true});
  async function request(endpoint,method,params,tag) {
    const body=JSON.stringify({jsonrpc:'2.0',id:1,method,params});
    const rec={endpoint,method,params,started_at:new Date().toISOString(),request_sha256:hash(body)};
    try {
      const r=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json'},body,signal:AbortSignal.timeout(12000)});
      const bytes=Buffer.from(await r.arrayBuffer()); fs.writeFileSync(`${root}/${tag}.raw`,bytes);
      rec.http_status=r.status;rec.raw_file=`${tag}.raw`;rec.response_sha256=hash(bytes);
      if(!r.ok) throw Error(`HTTP_${r.status}`);
      const j=JSON.parse(bytes.toString('utf8'));
      if(j.jsonrpc!=='2.0'||j.id!==1||j.error) throw Error(`RPC_ENVELOPE:${JSON.stringify(j.error)}`);
      rec.result=j.result;
    } catch(e) {rec.error=String(e.message); if(e.cause) rec.cause=String(e.cause.message);}
    rec.arrived_at=new Date().toISOString();return rec;
  }
  for(const [i,archive] of ['https://rpc-eth.blockmachine.io','https://ethereum-rpc.publicnode.com'].entries()) {
    const route={header:'https://ethereum-rpc.publicnode.com',archive,requests:[],pass:false};
    const h=await request(route.header,'eth_getBlockByNumber',[`0x${BLOCK.toString(16)}`,false],`route${i}_header`);route.requests.push(h);
    if(validHeader(h.result)) {
      const r=await request(archive,'eth_call',[{to:CBETH,data:iface.encodeFunctionData('exchangeRate')},{blockHash:h.result.hash,requireCanonical:true}],`route${i}_rate`);route.requests.push(r);
      route.pass=validRate(r.result);
    }
    out.routes.push(route);
    if(route.pass) {out.classification='NECESSARY_ANCHOR_PASS_ONLY';break;}
  }
  out.finished_at=new Date().toISOString();
  const bytes=JSON.stringify(out,null,2)+'\n';fs.writeFileSync(`${root}/result.json`,bytes);fs.writeFileSync(`${root}/result.sha256`,hash(bytes)+'\n');
  console.log(JSON.stringify({classification:out.classification,routes:out.routes.map(r=>({archive:r.archive,pass:r.pass,requests:r.requests.map(x=>({method:x.method,http:x.http_status,error:x.error,cause:x.cause}))})),sha256:hash(bytes)}));
  return out;
}
if(process.argv[1] && import.meta.url.endsWith(process.argv[1].replaceAll('\\','/'))) await run();
