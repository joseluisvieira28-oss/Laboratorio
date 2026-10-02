"""Reuse pinned complete artifacts; invoke frozen finalizer without source calls."""
import hashlib,io,json,os,subprocess,sys,urllib.request,zipfile
from pathlib import Path

BASE=Path('labs/DEFI_LIQUIDATION_SHOCK_001')
OUT=Path('source_resume_audit')
ROOT=OUT/'partitions'
ROOT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((BASE/'PROTECTED_2025_SOURCE_RECOVERY_MANIFEST_V0.3.json').read_text())
pins=manifest['reusable_pass_partitions']+[
 {'run':36997108868,'artifact':11229180032,'protocol':'marginfi','month':'01','digest':'sha256:93fac70facefa8b4bad5e7d09368e6b7cd3a9d470a5726e2433b525ec3387751'},
 {'run':36996055142,'artifact':11227286926,'protocol':'kamino','month':'05','digest':'sha256:3f6b77f60639d48ef17d0ab30b241829c99bce44c3e78039a1ebafb3e4ceb59e'},
 {'run':36996055142,'artifact':11234910191,'protocol':'kamino','month':'06','digest':'sha256:7ad351c7305b0edc3f5e3c2187e547f243241cbe4caf070524d5cb9c959860eb'}]
assert len(pins)==31 and len({(p['protocol'],p['month']) for p in pins})==31
expected_classes={'marginfi':'lending_account_liquidate','kamino':'liquidate_obligation_and_redeem_reserve_collateral','save0c':'LiquidateObligation','save11':'LiquidateObligationAndRedeemReserveCollateral'}
ledger=[]
class DownloadRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
  if redirected is not None:redirected.remove_header('Authorization')
  return redirected
opener=urllib.request.build_opener(DownloadRedirect())
for pin in pins:
 url=f'https://api.github.com/repos/joseluisvieira28-oss/Laboratorio/actions/artifacts/{pin["artifact"]}/zip'
 request=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
 with opener.open(request,timeout=90) as response:raw=response.read()
 assert 'sha256:'+hashlib.sha256(raw).hexdigest()==pin['digest'],'artifact_digest_mismatch'
 name=f'{pin["protocol"]}-2025{pin["month"]}.json'
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  assert z.testzip() is None,'artifact_crc'
  hits=[n for n in z.namelist() if n.replace('\\','/').split('/')[-1]==name]
  assert len(hits)==1,'receipt_member_count'
  data=z.read(hits[0])
 r=json.loads(data)
 assert r['classification']=='PROTECTED_2025_PROTOCOL_SOURCE_PASS','partition_not_pass'
 assert r['protocol']==pin['protocol'] and r['instruction_class']==expected_classes[pin['protocol']]
 m=int(pin['month']);start=f'2025-{m:02d}-01T00:00:00Z';end='2026-01-01T00:00:00Z' if m==12 else f'2025-{m+1:02d}-01T00:00:00Z'
 assert r['window_start']==start and r['window_end']==end,'partition_window'
 assert r['error_count']==0 and r['duplicate_count']==0
 assert len(r['rows'])==r['successful_instruction_count'],'row_count_mismatch'
 for k in ['prices_2025','returns_2025','pnl_2025','prices_2026','returns_2026','live_trading','orders','wallets','exchange_mutation','merge_main']:
  assert r['firewall'][k] is False,'firewall'
 (ROOT/name).write_bytes(data)
 ledger.append({**pin,'member':hits[0],'receipt_sha256':hashlib.sha256(data).hexdigest(),'rows':len(r['rows'])})
 print(json.dumps({'validated':name,'count':len(ledger)}),flush=True)
(OUT/'PINNED_ARTIFACT_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
result=subprocess.run([sys.executable,str(BASE/'source/finalize_protected_2025_source_v0_2.py'),'--root',str(ROOT)],check=False)
assert result.returncode in (0,2),'finalizer_execution_error'
receipt=json.loads((BASE/'PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.2.json').read_text())
assert receipt['partition_count']==31 and receipt['classification']=='PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED'
assert all(x['reason'] in ('partition_receipt_count','selected_partition_count') for x in receipt['errors']),'unexpected_source_conflict'
assert len([x for x in receipt['errors'] if x['reason']=='partition_receipt_count'])==17
receipt['resume_audit']={'date':'2026-10-02','run_id':os.environ['GITHUB_RUN_ID'],'commit':os.environ['GITHUB_SHA'],'acquisition_launched':False,'prior_active_run_preserved':36996055142,'ledger_sha256':hashlib.sha256((OUT/'PINNED_ARTIFACT_LEDGER.json').read_bytes()).hexdigest()}
(OUT/'DLS_PROTECTED_2025_SOURCE_RESUME_RECEIPT_V0.1.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'classification':receipt['classification'],'verified_partitions':31,'missing_partitions':17,'unexpected_conflicts':0}),flush=True)

