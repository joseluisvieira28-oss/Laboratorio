#!/usr/bin/env python3
"""Public notice capture only; never reads market endpoints or prices."""
import hashlib, json, re, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URL='https://bitwiseinvestments.com/indexes/rebalance-notifications/bitwise-crypto-asset-indexes'

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def main():
    out=Path('bitwise_forward_source'); out.mkdir(exist_ok=True)
    receipt={'url':URL,'status':'CAPTURE_BLOCKED','market_outcomes_opened':False,'signal_authorized':False}
    try:
        req=urllib.request.Request(URL,headers={'User-Agent':'CryptoLabBitwiseSource/1.0'})
        with urllib.request.urlopen(req,timeout=30) as r:
            if r.geturl()!=URL: raise ValueError('unexpected redirect')
            raw=r.read()
        seen=datetime.now(timezone.utc)
        p=Text(); p.feed(raw.decode('utf-8'))
        full=' '.join(p.parts)
        start=full.find('Date:')
        end=full.find('A team of crypto experts',start)
        if start<0 or end<start: raise ValueError('unrecognized notification layout')
        notice=full[start:end].strip()
        digest=hashlib.sha256(raw).hexdigest()
        nid=hashlib.sha256(notice.encode()).hexdigest()
        impl=re.search(r'at the\s+([A-Za-z]+ \d{1,2}, \d{4})\s+rebalance',notice)
        effective=None
        if impl: effective=datetime.strptime(impl.group(1),'%B %d, %Y').date().isoformat()
        status='FUTURE_NOTICE_CAPTURED_SOURCE_ONLY' if effective and effective>seen.date().isoformat() else 'STALE_OR_AMBIGUOUS_NOTICE_NO_ACTIVATION'
        receipt.update(status=status,observed_at_utc=seen.isoformat(),raw_sha256=digest,notice_sha256=nid,effective_date=effective,notice=notice)
        # Observed timestamp never replaced with publisher date. Preserve every new body.
        snap=out/(digest+'.html')
        if not snap.exists(): snap.write_bytes(raw)
        log=out/'receipts.jsonl'
        with log.open('a') as f: f.write(json.dumps(receipt,sort_keys=True)+'\n')
    except Exception as e:
        receipt['error']=f'{type(e).__name__}: {e}'
    (out/'latest.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__': main()
