import pathlib,json,hashlib,subprocess,datetime
P=pathlib.Path(__file__).resolve().parent
checks=[]
for manifest in ['acquisition_receipt.json','historical_version_inventory.json']:
 obj=json.loads((P/manifest).read_text())
 for r in obj['records']:
  if r['status']=='RETRIEVED':
   f=P/r['file']; checks.append({'file':r['file'],'pass':f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']})
g=json.loads((P/'genesis_pin.json').read_text()); raw=(P/g['file']).read_bytes();gen=json.loads(raw)
checks.append({'file':'genesis_pin.json','pass':gen['chain_id']=='coreum-mainnet-1' and hashlib.sha256(raw).hexdigest()==g['sha256']})
anchors=json.loads((P/'transport_anchors.json').read_text()); expected={5000000:'D8A6B584C70FE38CD7D160A7F5151974E595AD9E241700F80D45AF15F53B0FF9',10000000:'227EE3C00731C6544D88478F9022100214767E0DF8779C66433BF5C0BB810F47',15000000:'DE285C3282D4EAC0EA6AF0FDAB0EF3F45273D5BB96289A76EA501CEDB52B1516'}
checks.append({'file':'transport_anchors.json','pass':all(a['reported_block_hash']==expected[a['height']] and a['chain_id']=='coreum-mainnet-1' for a in anchors if a['height'] in expected)})
# Byte-integrity audit only: this deliberately cannot produce a replay pass.
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'artifact_integrity_pass':all(x['pass'] for x in checks),'replay_pass':False,'source_gate_pass':False,'census_authorized':False}
(P/'integrity_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':len(checks),'integrity_pass':result['artifact_integrity_pass'],'replay_pass':False}));raise SystemExit(0 if result['artifact_integrity_pass'] else 1)
