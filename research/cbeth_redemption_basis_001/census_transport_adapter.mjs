// Executes the original source-only census with deterministic transport changes.
import fs from 'node:fs';
const root='research/cbeth_redemption_basis_001/';
let s=fs.readFileSync(root+'cbeth_predictor_census_v01.mjs','utf8').replaceAll('\r\n','\n');
function replaceOnce(a,b) {
 if(s.split(a).length!==2) throw Error('ADAPTER_SOURCE_DRIFT:'+a.slice(0,50));
 s=s.replace(a,b);
}
replaceOnce('const latest=await latestHeader();','const latest=await censusSearchUpperBound;');
replaceOnce('let previousBlock=null;','const censusSearchUpperBound=latestHeader();\nlet completed=0;\nfs.mkdirSync("artifacts/cbeth_census/checkpoints",{recursive:true});');
replaceOnce('for(let i=0;i<days.length;i++){','async function oneDay(i){');
replaceOnce('const meta=previousBlock===null\n      ? await firstBlockAtOrAfterGlobal(targetTs)\n      : await nextDailyBoundary(previousBlock,targetTs);\n    previousBlock=meta.number;','const meta=await firstBlockAtOrAfterGlobal(targetTs);');
replaceOnce('rows.push({\n      utc_day:day,','rows[i]={\n      utc_day:day,');
replaceOnce('      valid:true\n    });','      valid:true\n    };');
replaceOnce('rows.push({utc_day:day,target_timestamp_utc:day+"T17:00:00Z",valid:false,error:String(e?.message||e)});','rows[i]={utc_day:day,target_timestamp_utc:day+"T17:00:00Z",valid:false,error:String(e?.message||e)};');
replaceOnce('  if((i+1)%25===0) console.log("progress",i+1,days.length,"errors",errors.length);','  fs.writeFileSync("artifacts/cbeth_census/checkpoints/"+day+".json",JSON.stringify(rows[i])+"\\n");\n  completed++;\n  if(completed%25===0) console.log("progress",completed,days.length,"errors",errors.length);');
replaceOnce('const canonicalRows=rows.map(x=>({...x}));','let cursor=0;\nawait Promise.all(Array.from({length:8},async()=>{while(cursor<days.length){const i=cursor++;await oneDay(i);}}));\nconst canonicalRows=rows.map(x=>({...x}));');
const dest=root+'.census_transport_runtime.mjs';
fs.writeFileSync(dest,s);
try {await import('./.census_transport_runtime.mjs');} finally {fs.unlinkSync(dest);}
