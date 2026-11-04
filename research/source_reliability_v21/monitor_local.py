"""Incrementally read growing gzip evidence without altering it."""
import json,time,zlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from source import Observer
p=Path(sys.argv[1]); offset=0; decoder=zlib.decompressobj(16+zlib.MAX_WBITS); pending=b''; o=Observer(); last=None
while True:
 if p.exists():
  with p.open('rb') as f:
   f.seek(offset); chunk=f.read(); offset+=len(chunk)
  if chunk:
   pending+=decoder.decompress(chunk)
   lines=pending.split(b'\n'); pending=lines.pop()
   for line in lines:
    last=json.loads(line); o.feed(last)
 if last:
  r=o.report('MONITOR_ONLY')
  status={'elapsed_seconds':round(last['elapsed'],1),'compressed_mib':round(offset/1024**2,2),'joint_good_seconds':r['joint_good_seconds'],'joint_coverage_pct':round(r['joint_coverage']*100,2),'good_full_minutes':r['good_full_minutes'],'liquidations':o.count['liquidations'],'bursts':len(o.episodes),'qualified':r['qualified_signals'],'interruptions':sum(o.count[v+':disconnect'] for v in o.state),'invalid':sum(n for k,n in o.count.items() if k.startswith('invalid:')),'pongs':{v:o.count[v+':pong'] for v in o.state},'last_kind':last['kind']}
  print(json.dumps(status),flush=True)
  if last['kind']=='end': break
 time.sleep(50)
