import unittest, tempfile, pathlib, json
from unittest.mock import patch
import census

def wire(n,v):
 def var(x):
  b=b''
  while x>127:b+=bytes([(x&127)|128]);x>>=7
  return b+bytes([x])
 return var(n*8+2)+var(len(v))+v

class ScientificFirewall(unittest.TestCase):
 def test_malformed_never_empty(self):
  for b in (b'\x0a\xff',b'\x0a\x05xx',b'\x00'):
   with self.assertRaises(ValueError):list(census.fields(b))
 def test_undelegate_decode(self):
  coin=wire(1,b'uatom')+wire(2,b'1234')
  msg=wire(1,b'del')+wire(2,b'val')+wire(3,coin)
  anymsg=wire(1,b'/cosmos.staking.v1beta1.MsgUndelegate')+wire(2,msg)
  rows=census.messages(wire(1,wire(1,anymsg)))
  self.assertEqual(rows[0]['amount'],'1234');self.assertEqual(rows[0]['message_index'],0)
 def test_missing_execution_code_blocks_checkpoint(self):
  import base64
  raw=wire(1,wire(1,wire(1,b'/other')+wire(2,b'')))
  def get(rpc,method,params):
   if method=='block':return {'block':{'header':{'height':'20000000','chain_id':'cosmoshub-4','time':'2024-04-14T20:16:23Z','app_hash':'a'},'data':{'txs':[base64.b64encode(raw).decode()]}},'block_id':{'hash':'b'}},{'sha256':'c'}
   return {'height':'20000000','txs_results':[{}]},{'sha256':'d'}
  with patch.object(census.RPC,'get',get), patch.object(census,'save') as saved, patch.object(pathlib.Path,'exists',return_value=False):
   p=census.ROOT/'test-checkpoint.json';out=census.scan('ATOM','citizenweb3',20000000,20000000,p)
   self.assertFalse(out['complete']);self.assertEqual(out['covered'],0)
 def test_boundary_adjacent_and_genesis(self):
  class Fake:
   def header(self,h):return {'height':h,'time':f'2023-01-01T00:00:{h:02d}Z'}
  self.assertEqual(census.lower_bound(Fake(),1,10,'2023-01-01T00:00:05Z')['first']['height'],5)
  self.assertTrue(census.lower_bound(Fake(),1,10,'2023-01-01T00:00:00Z')['genesis_boundary'])

if __name__=='__main__':unittest.main()
