import {createHash} from 'node:crypto'
import {readdir,readFile,writeFile,mkdir} from 'node:fs/promises'
const DIR='artifacts/all',OUT='artifacts/lcod_sqd_sdk_parallel_universe_v05.json',MIN=24720899
const sha=s=>createHash('sha256').update(s).digest('hex')
const files=await readdir(DIR)
const prep=JSON.parse(await readFile(DIR+'/'+files.find(x=>x==='lcod_parallel_prepare_v05.json'),'utf8'))
const chunkFiles=files.filter(x=>/^lcod_parallel_chunk_\d+_v05\.json$/.test(x)).sort()
const chunks=[];for(const f of chunkFiles)chunks.push(JSON.parse(await readFile(DIR+'/'+f,'utf8')))
chunks.sort((a,b)=>a.from_block-b.from_block)
let contiguous=chunks.length===prep.chunk_count&&chunks.length===16&&chunks[0]?.from_block===MIN&&chunks.at(-1)?.to_block===prep.latest_block
for(let i=1;i<chunks.length;i++)if(chunks[i].from_block!==chunks[i-1].to_block+1)contiguous=false
const allChunkPass=chunks.every(x=>x.classification==='CHUNK_PASS')
const decodeErrors=chunks.reduce((s,x)=>s+Number(x.decode_error_count||0),0)
const events=chunks.reduce((s,x)=>s+Number(x.borrow_event_count||0),0)
const pairs=new Set();for(const c of chunks)for(const h of c.pair_hashes||[])pairs.add(h)
const current=new Set(prep.current_mcp_pair_hashes||[])
const missing=[...current].filter(x=>!pairs.has(x)).sort()
const coverage=current.size?(current.size-missing.length)/current.size:0
const fixtureChunks=chunks.filter(x=>x.fixture_expected_in_chunk)
const fixture=fixtureChunks.length===1&&fixtureChunks[0].fixture_tx_present===true
const corpusHash=sha(chunks.map(x=>x.chunk_id+':'+x.canonical_stream_sha256).join('\n'))
const pass=prep.classification==='PREPARE_PASS'&&contiguous&&allChunkPass&&decodeErrors===0&&events>0&&fixture&&coverage===1
const out={lab_id:'LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001',stage:'SQD_SDK_PARALLEL_BORROW_UNIVERSE_V0.5',
 captured_at_utc:new Date().toISOString(),classification:pass?'SQD_SDK_PARALLEL_BORROW_UNIVERSE_PASS':'SQD_SDK_PARALLEL_BORROW_UNIVERSE_BLOCKED',
 sdk:'@subsquid/evm-stream@0.1.5',range_from_block:MIN,range_to_latest_block:prep.latest_block,
 expected_chunk_count:16,received_chunk_count:chunks.length,contiguous_complete_coverage:contiguous,
 all_chunks_pass:allChunkPass,borrow_event_count:events,unique_event_pair_hash_count:pairs.size,
 current_mcp_pair_count:current.size,current_mcp_covered_count:current.size-missing.length,current_mcp_coverage:coverage,
 missing_current_mcp_pair_count:missing.length,missing_current_mcp_pair_hashes:missing.slice(0,100),
 truth_fixture_present:fixture,event_decode_error_count:decodeErrors,canonical_chunk_corpus_sha256:corpusHash,
 chunk_summaries:chunks.map(x=>({id:x.chunk_id,from:x.from_block,to:x.to_block,events:x.borrow_event_count,pairs:x.unique_pair_count,batches:x.batch_count,classification:x.classification})),
 raw_wallet_addresses_retained:false,curve_computed:false,market_returns_opened:false,liquidation_outcomes_opened:false,pnl_opened:false,mutation:false}
await mkdir('artifacts',{recursive:true});await writeFile(OUT,JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out,null,2));if(!pass)process.exitCode=2
