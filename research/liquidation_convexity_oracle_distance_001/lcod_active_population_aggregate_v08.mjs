import {readdir,readFile,writeFile,mkdir} from 'node:fs/promises'
import {createHash} from 'node:crypto'
const DIR='artifacts/all',sha=s=>createHash('sha256').update(s).digest('hex')
const files=await readdir(DIR)
const prep=JSON.parse(await readFile(DIR+'/lcod_active_population_prepare_v08.json','utf8'))
const fs=files.filter(x=>/^lcod_active_population_chunk_\d+_v08\.json$/.test(x)).sort()
const chunks=[];for(const f of fs)chunks.push(JSON.parse(await readFile(DIR+'/'+f,'utf8')))
chunks.sort((a,b)=>a.from_block-b.from_block)
let contiguous=chunks.length===16&&chunks[0]?.from_block===prep.min_block&&chunks.at(-1)?.to_block===prep.finalized_block_number
for(let i=1;i<chunks.length;i++)if(chunks[i].from_block!==chunks[i-1].to_block+1)contiguous=false
const pairs=new Set(),active=new Set(),inactive=new Set()
for(const c of chunks){for(const h of c.pair_hashes||[])pairs.add(h);for(const h of c.active_pair_hashes||[])active.add(h);for(const h of c.inactive_pair_hashes||[])inactive.add(h)}
const overlap=[...active].filter(x=>inactive.has(x))
const union=new Set([...active,...inactive])
const chunkPass=chunks.every(c=>c.classification==='ACTIVE_CHUNK_PASS'&&c.finalized_block_number===prep.finalized_block_number&&c.finalized_block_hash===prep.finalized_block_hash)
const decodeErrors=chunks.reduce((s,c)=>s+Number(c.decode_error_count||0),0),uadErrors=chunks.reduce((s,c)=>s+Number(c.uad_error_count||0),0)
const pass=prep.classification==='PREP_PASS'&&contiguous&&chunkPass&&decodeErrors===0&&uadErrors===0&&overlap.length===0&&union.size===pairs.size&&active.size>0
const out={lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',stage:'BLOCK_PINNED_ACTIVE_POPULATION_V0.8',
 captured_at_utc:new Date().toISOString(),classification:pass?'BLOCK_PINNED_ACTIVE_POPULATION_PASS':'BLOCK_PINNED_ACTIVE_POPULATION_BLOCKED',
 ethereum_block_number:prep.finalized_block_number,ethereum_block_hash:prep.finalized_block_hash,block_tag_policy:'finalized',
 range_from_block:prep.min_block,range_to_block:prep.finalized_block_number,expected_chunk_count:16,received_chunk_count:chunks.length,
 contiguous_complete_coverage:contiguous,all_chunks_pass:chunkPass,borrow_event_count:chunks.reduce((s,c)=>s+Number(c.borrow_event_count||0),0),
 historical_candidate_pair_count:pairs.size,active_debt_pair_count:active.size,inactive_pair_count:inactive.size,
 active_plus_inactive_equals_candidates:union.size===pairs.size,active_inactive_overlap_count:overlap.length,
 borrow_decode_error_count:decodeErrors,uad_error_count:uadErrors,
 canonical_historical_pair_set_sha256:sha([...pairs].sort().join('\n')),canonical_active_pair_set_sha256:sha([...active].sort().join('\n')),
 active_pair_hash_sample:[...active].sort().slice(0,20),
 chunk_summaries:chunks.map(c=>({id:c.chunk_id,from:c.from_block,to:c.to_block,events:c.borrow_event_count,pairs:c.historical_pair_count,active:c.active_pair_count,inactive:c.inactive_pair_count,classification:c.classification})),
 raw_wallet_addresses_retained:false,all_uad_calls_block_pinned:true,curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile('artifacts/lcod_block_pinned_active_population_v08.json',JSON.stringify(out,null,2)+'\n')
console.log(JSON.stringify(out,null,2));if(!pass)process.exitCode=2
