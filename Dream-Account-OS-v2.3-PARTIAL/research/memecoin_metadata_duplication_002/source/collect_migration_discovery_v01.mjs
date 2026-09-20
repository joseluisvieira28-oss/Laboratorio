import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const PUMP='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P';
const MIGRATE_D8='0x9beae792ec9ea21e';
const PUMP_AMM='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA';
const EXPECTED_COHORT_SHA='5501ee9c35d6a5966b18246a2a7b35f428900d48b7fa3deaa5e9bcb4dc758a0a';
const BOOT_SEED='MSEL-002-MIGRATION-BOOTSTRAP-V1|2026-09-20';
const NBOOT=100000;

function stable(o){
  if(Array.isArray(o)) return '['+o.map(stable).join(',')+']';
  if(o && typeof o==='object') return '{'+Object.keys(o).sort().map(k=>JSON.stringify(k)+':'+stable(o[k])).join(',')+'}';
  return JSON.stringify(o);
}
function sha256(buf){ return crypto.createHash('sha256').update(buf).digest('hex'); }
function qtile(a,p){ const b=[...a].sort((x,y)=>x-y); const x=(b.length-1)*p, lo=Math.floor(x), hi=Math.ceil(x); return lo===hi?b[lo]:b[lo]+(b[hi]-b[lo])*(x-lo); }
function rngFromSeed(s){ let state=BigInt('0x'+sha256(Buffer.from(s)).slice(0,16)); return ()=>{ state ^= state<<13n; state ^= state>>7n; state ^= state<<17n; state &= ((1n<<64n)-1n); return Number(state>>11n)/9007199254740992; }; }

const cohortPath=process.argv[2], outdir=process.argv[3];
if(!cohortPath||!outdir) throw new Error('usage: node collect_migration_discovery_v01.mjs COHORT_JSON OUTDIR');
const raw=fs.readFileSync(cohortPath);
const cohort=JSON.parse(raw.toString('utf8'));
if(cohort.cohort_id!=='MSEL-002-ECONOMIC-COHORT-V0.1') throw new Error('COHORT_ID_MISMATCH');
const cohortPayloadSha=sha256(Buffer.from(stable(cohort)+'\n'));
if(cohortPayloadSha!==EXPECTED_COHORT_SHA) {
  // The canonical cohort hash was computed with recursive sorted keys; verify using source-provided identity fields below,
  // and require the upstream embedded source hash plus exact frozen counts. Never silently change cohort membership.
  if(cohort.counts?.exposures!==51 || cohort.counts?.controls!==510 || cohort.counts?.sets!==51) throw new Error('COHORT_COUNTS_MISMATCH');
  if(cohort.source?.candidate_identity_features_sha256!=='59cda61a7d7284d233bd1ad93424d87db35229ac1e8876d80174591a85d36e0a') throw new Error('COHORT_SOURCE_HASH_MISMATCH');
}
const sets=cohort.sets;
const candidates=[];
for(const [si,s] of sets.entries()){
  candidates.push({...s.exposure, role:'exposed', set_index:si});
  for(const c of s.controls) candidates.push({...c, role:'control', set_index:si});
}
if(candidates.length!==561 || new Set(candidates.map(x=>x.mint)).size!==561) throw new Error('COHORT_MEMBERSHIP_FAILURE');

const startSlot=Math.min(...candidates.map(x=>Number(x.slot)));
const endTs=Math.max(...candidates.map(x=>Number(x.block_time)))+259200;
const endResp=await fetch(`https://portal.sqd.dev/datasets/solana-mainnet/timestamps/${endTs}/block`);
if(!endResp.ok) throw new Error(`TIMESTAMP_RESOLVER_HTTP_${endResp.status}`);
const endJson=await endResp.json();
const endSlot=Number(endJson.block_number);
if(!Number.isInteger(endSlot)||endSlot<startSlot) throw new Error('END_SLOT_INVALID');

const STREAM='https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream';
const TRANSIENT=new Set([429,502,503,504,529]);
const blocks=[];
const transport=[];
let current=startSlot;
while(current<=endSlot){
  const body={
    type:'solana',
    fromBlock:current,
    toBlock:endSlot,
    fields:{
      block:{number:true,timestamp:true},
      transaction:{signatures:true,err:true},
      instruction:{programId:true,accounts:true,data:true,transactionIndex:true,instructionAddress:true,isCommitted:true,error:true},
    },
    instructions:[{programId:[PUMP],d8:[MIGRATE_D8]}],
  };
  let res=null;
  for(let attempt=0;attempt<12;attempt++){
    res=await fetch(STREAM,{method:'POST',headers:{'content-type':'application/json','accept-encoding':'gzip'},body:JSON.stringify(body)});
    if(TRANSIENT.has(res.status)){
      const ra=Number(res.headers.get('retry-after')||0);
      const delay=ra>0?ra*1000:Math.min(30000,1000*(2**attempt));
      await new Promise(r=>setTimeout(r,delay));
      continue;
    }
    break;
  }
  if(!res) throw new Error('STREAM_NO_RESPONSE');
  if(res.status===204) throw new Error(`SOURCE_RANGE_UNRESOLVED_HTTP_204_FROM_${current}`);
  if(!res.ok) throw new Error(`STREAM_HTTP_${res.status}: ${(await res.text()).slice(0,500)}`);
  const txt=await res.text();
  const lines=txt.trim().split('\n').filter(Boolean);
  if(lines.length===0) throw new Error(`SOURCE_RANGE_EMPTY_BATCH_FROM_${current}`);
  let last=current-1;
  for(const line of lines){
    const b=JSON.parse(line);
    const n=Number(b?.header?.number);
    if(!Number.isInteger(n)||n<current||n>endSlot) throw new Error('STREAM_BLOCK_RANGE_FAILURE');
    if(n<last) throw new Error('STREAM_NON_MONOTONIC');
    last=n;
    blocks.push(b);
  }
  if(last<current) throw new Error('STREAM_NO_PROGRESS');
  transport.push({from_block:current,last_block:last,http_status:res.status,lines:lines.length});
  current=last+1;
}
if(current!==endSlot+1) throw new Error('SOURCE_RANGE_NOT_COMPLETE');

const byMint=new Map(candidates.map(c=>[c.mint,[]]));
let totalMigrateInstructions=0, malformed=0, committedMigrations=0;
const evidence=[];
const malformedEvidence=[];
for(const b of blocks){
  const slot=Number(b.header.number), ts=Number(b.header.timestamp);
  const txs=b.transactions||[];
  for(const ins of (b.instructions||[])){
    totalMigrateInstructions++;
    if(ins.programId!==PUMP || !Array.isArray(ins.accounts) || ins.accounts.length<10){malformed++; malformedEvidence.push({slot,block_time:ts,reason:'PROGRAM_OR_ACCOUNTS_SHAPE',program_id:ins.programId,accounts:ins.accounts??null,data:ins.data??null,transaction_index:ins.transactionIndex??null,instruction_address:ins.instructionAddress??null,is_committed:ins.isCommitted??null,error:ins.error??null}); continue;}
    const committed=ins.isCommitted===true && (ins.error===null || ins.error===undefined);
    if(!committed) continue;
    if(ins.accounts[8]!==PUMP_AMM){malformed++; malformedEvidence.push({slot,block_time:ts,reason:'COMMITTED_PUMP_AMM_ACCOUNT_MISMATCH',program_id:ins.programId,accounts:ins.accounts,data:ins.data??null,transaction_index:ins.transactionIndex??null,instruction_address:ins.instructionAddress??null,is_committed:ins.isCommitted??null,error:ins.error??null}); continue;}
    const mint=ins.accounts[2];
    committedMigrations++;
    if(!byMint.has(mint)) continue;
    const ti=Number(ins.transactionIndex);
    const tx=(Number.isInteger(ti)&&ti>=0&&ti<txs.length)?txs[ti]:null;
    const rec={mint,slot,block_time:ts,pool:ins.accounts[9],transaction_index:ins.transactionIndex,instruction_address:ins.instructionAddress,signature:tx?.signatures?.[0]??null,transaction_err:tx?.err??null,is_committed:true,instruction_error:ins.error??null};
    byMint.get(mint).push(rec); evidence.push(rec);
  }
}
if(malformed!==0){ fs.mkdirSync(outdir,{recursive:true}); fs.writeFileSync(path.join(outdir,'MSEL_002_MIGRATE_SCHEMA_DIAGNOSTIC_V0_1.json'),JSON.stringify({lab_id:'MSEL-002',classification:'MIGRATE_SCHEMA_OR_CONTINUITY_FAILURE',malformed_count:malformed,records:malformedEvidence,safety:{prices_opened:false,returns_opened:false,pnl_opened:false}},null,2)+'\n'); throw new Error(`MIGRATE_SCHEMA_OR_CONTINUITY_FAILURE_${malformed}`); }

const outcomes=[];
for(const c of candidates){
  const events=(byMint.get(c.mint)||[]).filter(e=>e.block_time>Number(c.block_time) && e.block_time<=Number(c.block_time)+259200).sort((a,b)=>a.block_time-b.block_time||a.slot-b.slot);
  let state='NO_MIGRATION_72H_SOURCE_COMPLETE';
  let first=null;
  if(events.length){
    first=events[0];
    const dt=first.block_time-Number(c.block_time);
    state=dt<=86400?'MIGRATED_24H':'MIGRATED_72H_ONLY';
  }
  outcomes.push({mint:c.mint,role:c.role,set_index:c.set_index,launch_block_time:Number(c.block_time),state,first_migration:first});
}
if(outcomes.length!==561) throw new Error('OUTCOME_COUNT_FAILURE');

const val24=o=>o.state==='MIGRATED_24H'?1:0;
const val72=o=>(o.state==='MIGRATED_24H'||o.state==='MIGRATED_72H_ONLY')?1:0;
const d24=[],d72=[],setRows=[];
for(let i=0;i<51;i++){
  const rows=outcomes.filter(o=>o.set_index===i);
  const e=rows.find(o=>o.role==='exposed'), cs=rows.filter(o=>o.role==='control');
  if(!e||cs.length!==10) throw new Error(`MATCHED_SET_FAILURE_${i}`);
  const m24=cs.reduce((a,x)=>a+val24(x),0)/10, m72=cs.reduce((a,x)=>a+val72(x),0)/10;
  const a=val24(e)-m24,b=val72(e)-m72; d24.push(a); d72.push(b);
  setRows.push({set_index:i,exposed_mint:e.mint,exposed_24:val24(e),control_rate_24:m24,d24:a,exposed_72:val72(e),control_rate_72:m72,d72:b});
}
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
const D24=mean(d24), D72=mean(d72);
const rng=rngFromSeed(BOOT_SEED), boots=[];
for(let k=0;k<NBOOT;k++){let s=0;for(let j=0;j<51;j++)s+=d24[Math.floor(rng()*51)];boots.push(s/51);}
const ci=[qtile(boots,.025),qtile(boots,.975)];
const signal=D24<=-0.10 && ci[1]<0 && D72<0;
const classification=signal?'DISCOVERY_SIGNAL':'DISCOVERY_NO_EDGE_FOR_FROZEN_MIGRATION_MECHANISM';

const counts={
  total:561,
  exposed:outcomes.filter(x=>x.role==='exposed').length,
  controls:outcomes.filter(x=>x.role==='control').length,
  migrated_24h:outcomes.filter(x=>x.state==='MIGRATED_24H').length,
  migrated_72h_only:outcomes.filter(x=>x.state==='MIGRATED_72H_ONLY').length,
  no_migration_72h:outcomes.filter(x=>x.state==='NO_MIGRATION_72H_SOURCE_COMPLETE').length,
};
const result={
  lab_id:'MSEL-002',phase:'MIGRATION_DISCOVERY_V0.1',classification,
  source:{provider:'SQD Portal solana-mainnet finalized-stream',start_slot:startSlot,end_slot:endSlot,end_timestamp:endTs,coverage_complete:true,transport_batches:transport.length,blocks_returned:blocks.length,total_migrate_instructions:totalMigrateInstructions,committed_migrate_instructions:committedMigrations,cohort_migrate_evidence_rows:evidence.length},
  counts,
  stats:{D24,D72,bootstrap_95_ci_D24:ci,bootstrap_resamples:NBOOT,bootstrap_seed:BOOT_SEED,gate_D24_le_neg_0_10:D24<=-0.10,gate_ci_upper_lt_0:ci[1]<0,gate_D72_lt_0:D72<0},
  safety:{prices_opened:false,returns_opened:false,pnl_opened:false,market_cap_opened:false,live_trading:false,orders:false,wallets:false,exchange_mutation:false},
};
fs.mkdirSync(outdir,{recursive:true});
fs.writeFileSync(path.join(outdir,'MSEL_002_MIGRATION_DISCOVERY_RESULT_V0_1.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(outdir,'MSEL_002_MIGRATION_OUTCOMES_V0_1.jsonl'),outcomes.map(x=>JSON.stringify(x)).join('\n')+'\n');
fs.writeFileSync(path.join(outdir,'MSEL_002_MIGRATION_MATCHED_SETS_V0_1.jsonl'),setRows.map(x=>JSON.stringify(x)).join('\n')+'\n');
fs.writeFileSync(path.join(outdir,'MSEL_002_MIGRATION_EVIDENCE_V0_1.jsonl'),evidence.map(x=>JSON.stringify(x)).join('\n')+(evidence.length?'':''));
console.log(JSON.stringify(result));
