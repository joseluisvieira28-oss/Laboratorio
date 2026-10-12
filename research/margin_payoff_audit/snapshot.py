"""Copy only already-published research evidence from pinned Git objects. No network."""
import subprocess, pathlib, hashlib, json
ROOT = pathlib.Path(__file__).resolve().parent
SPECS = {
 'btc-convex-trend-capture-001-v0.1': lambda p: p.startswith('labs/btc-convex-trend-capture-001/') and (p.endswith(('.md','.pine','.b64','.json'))),
 'tfg-donchian-1d-oos-2025-v01': lambda p: '/timeframe_gap/' in p and ('DONCHIAN_1D_001' in p or 'EMA_PULLBACK_1D_001' in p) and p.endswith(('.md','.json')),
 'dream-account-phase-b-signal-research-v0.1': lambda p: 'PHASE_B_P00_DISCOVERY_CLOSEOUT' in p or 'PHASE_B_PRE_DATA_RESEARCH_FREEZE' in p,
 'audit/power-premia-ensemble-stop-2026-10-08': lambda p: p.startswith('research/crypto_lab_v2/') and p.endswith('.md'),
}
def git(*args):
 return subprocess.check_output(['git',*args])
def main():
 manifest=[]
 prior=json.loads((ROOT/'source_manifest.json').read_text()) if (ROOT/'source_manifest.json').exists() else []
 pinned={row['ref']:row['commit'] for row in prior}
 for ref,predicate in SPECS.items():
  sha=pinned.get(ref) or git('rev-parse','origin/'+ref).decode().strip()
  for line in git('ls-tree','-r',sha).decode().splitlines():
   metadata,path=line.split('\t',1)
   if not predicate(path): continue
   blob=metadata.split()[2]
   raw=git('cat-file','blob',blob)
   target=ROOT/'evidence'/ref.replace('/','_')/path
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(raw)
   manifest.append(dict(ref=ref,commit=sha,path=path,blob=blob,sha256=hashlib.sha256(raw).hexdigest(),local_path=target.relative_to(ROOT).as_posix()))
 (ROOT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('Snapshot:',len(manifest),'published evidence files')
if __name__=='__main__': main()
