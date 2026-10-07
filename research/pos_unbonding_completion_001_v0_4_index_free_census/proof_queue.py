"""Historical successor traversal via non-membership proofs, NEVER subspace/latest."""
import base64,json,concurrent.futures
from census import ROOT,FREEZE,CHAINS,RPC,first,save,digest

def collect(chain,provider,limit=8):
 rpc=RPC(chain,provider);height=CHAINS[chain]['anchor'];out={'chain':chain,'provider':provider,'height':height,'freeze':FREEZE,'proof_verified':False,'prefix':'41','terminal':False,'steps':[]}
 try:
  out['canonical_next_header']=rpc.header(height+1)
  # Starting strictly at prefix finds first timeslice; suffix zero asks for successor.
  cursor=b'\x41'
  for _ in range(limit):
   result,receipt=rpc.get('abci_query',{'path':json.dumps('/store/staking/key'),'data':'0x'+cursor.hex(),'height':str(height),'prove':'true'})
   response=result['response']
   if int(response.get('code',-1))!=0 or int(response.get('height',0))!=height:raise ValueError('historical proof query failed')
   ops=(response.get('proofOps') or response.get('proof_ops') or {}).get('ops',[])
   if len(ops)!=2 or ops[0]['type']!='ics23:iavl':raise ValueError('unsupported proof scheme')
   cp=base64.b64decode(ops[0]['data']);non=first(cp,2)
   if not non:raise ValueError('successor cursor unexpectedly exists or proof lacks non-membership')
   if first(non,1)!=cursor:raise ValueError('proof cursor mismatch')
   right=first(non,3);next_key=first(right,1) if right else None;value=first(right,2) if right else None
   out['steps'].append({'cursor_hex':cursor.hex(),'next_key_hex':next_key.hex() if next_key else None,'next_key_time':next_key[1:].decode() if next_key and next_key[:1]==b'\x41' else None,'value_base64':base64.b64encode(value).decode() if value else None,'proof_ops':ops,'receipt':receipt})
   # Verifier must validate cryptographic neighbor adjacency before completeness can PASS.
   if not next_key or next_key[:1]!=b'\x41':out['terminal']=True;break
   if next_key<=cursor:raise ValueError('non-monotone successor')
   cursor=next_key+b'\x00'
  out['status']='COLLECTED_REQUIRES_ICS23_VERIFICATION'
 except Exception as e:out.update(status='PROOF_ROUTE_BLOCKED',error=str(e))
 out['receipts']=rpc.receipts;save(ROOT/'receipts'/f'proof-queue-{chain}-{provider}.json',out)
 return {'chain':chain,'provider':provider,'status':out['status'],'steps':len(out['steps']),'terminal':out['terminal'],'error':out.get('error')}

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  jobs=[(c,p) for c,s in CHAINS.items() for p in s['sources']]
  for x in ex.map(lambda t:collect(*t),jobs):print(json.dumps(x),flush=True)
