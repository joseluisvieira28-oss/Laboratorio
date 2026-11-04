import tempfile,zipfile,gzip,hashlib,json
from pathlib import Path
from audit_zip import audit
from source import Observer
import unittest
class ZipAuditTests(unittest.TestCase):
 def test_zip_reconstructs_and_rejects_tampering(self):
  rows=[{'seq':1,'utc_ms':100000,'mono_ns':0,'elapsed':0.,'venue':'system','kind':'start','segment':0,'raw':json.dumps({'code_sha256':hashlib.sha256(b'code').hexdigest(),'protocol_sha256':hashlib.sha256(b'protocol').hexdigest()})},{'seq':2,'utc_ms':161000,'mono_ns':61000000000,'elapsed':61.,'venue':'system','kind':'end','segment':0,'raw':'RETRY_EXHAUSTED'}]
  o=Observer()
  for r in rows:o.feed(r)
  raw=b''.join((json.dumps(r)+'\n').encode() for r in rows); compressed=gzip.compress(raw)
  manifest={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(compressed).hexdigest(),'protocol_sha256':hashlib.sha256(b'protocol').hexdigest(),'code_sha256':hashlib.sha256(b'code').hexdigest(),'receipt_rows':2}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'evidence.zip'
   def build(tamper=False):
    with zipfile.ZipFile(p,'w') as z:
     z.writestr('raw.jsonl.gz',compressed); z.writestr('manifest.json',json.dumps(manifest)); z.writestr('report.json',json.dumps(o.report('RETRY_EXHAUSTED'))); z.writestr('source.py',b'bad' if tamper else b'code'); z.writestr('PROTOCOL.md',b'protocol')
   build(); r=audit(p); self.assertEqual(r['seconds'],61); self.assertEqual(r['source_verdict'],'SOURCE_BLOCKED')
   build(True)
   with self.assertRaisesRegex(AssertionError,'CODE_HASH'): audit(p)
 def test_causal_warmup_and_good_minute_reconstruct(self):
  import unittest
  from source import sha
  rows=[]; o=Observer()
  def add(t,v,k,m):
   r={'seq':len(rows)+1,'utc_ms':100000+int(t*1000),'mono_ns':int(t*1e9),'elapsed':t,'venue':v,'kind':k,'segment':1,'raw':json.dumps(m) if not isinstance(m,str) else m}; rows.append(r); o.feed(r)
  code=b'code'; protocol=b'protocol'; h=lambda b:hashlib.sha256(b).hexdigest()
  add(0,'system','start',{'code_sha256':h(code),'protocol_sha256':h(protocol)})
  for v in ('bybit','mexc'):add(0,v,'connect','public')
  add(0,'bybit','frame',{'op':'subscribe','success':True}); add(0,'mexc','frame',{'channel':'rs.sub.depth.full','data':'success'})
  for n in range(481):
   t=n/4
   if n%60==0:
    add(t,'bybit','frame',{'op':'pong'}); add(t,'mexc','frame',{'channel':'pong'})
   add(t,'bybit','frame',{'topic':'orderbook.1.BTCUSDT','ts':100000+int(t*1000),'type':'snapshot','data':{'s':'BTCUSDT','u':n+1,'b':[['100','1']],'a':[['101','1']]}})
   add(t,'mexc','frame',{'channel':'push.depth.full','symbol':'BTC_USDT','ts':100000+int(t*1000),'data':{'version':n+1,'bids':[[100-i,1] for i in range(5)],'asks':[[101+i,1] for i in range(5)]}})
  add(120.001,'system','end','RETRY_EXHAUSTED'); raw=b''.join((json.dumps(r)+'\n').encode() for r in rows); compressed=gzip.compress(raw)
  manifest={'raw_sha256':h(raw),'gzip_sha256':h(compressed),'protocol_sha256':h(protocol),'code_sha256':h(code),'receipt_rows':len(rows)}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'evidence.zip'
   with zipfile.ZipFile(p,'w') as z:
    for name,data in {'raw.jsonl.gz':compressed,'manifest.json':json.dumps(manifest),'report.json':json.dumps(o.report('RETRY_EXHAUSTED')),'source.py':code,'PROTOCOL.md':protocol}.items():z.writestr(name,data)
   r=audit(p); self.assertEqual(r['joint_good_seconds'],91); self.assertEqual(r['good_full_minutes'],1)
