"""Manual public-data attempts. No scheduler, execution, credentials or PnL."""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import threading
import urllib.parse
import urllib.request
import urllib.error
import adapter

UTC=dt.timezone.utc
def now(): return dt.datetime.now(UTC)
def require(ok, reason):
    if not ok: raise ValueError(reason)
def write(path, raw):
    with path.open('xb') as f:
        f.write(raw); f.flush()
        import os
        os.fsync(f.fileno())
    return hashlib.sha256(raw).hexdigest()
def encoded(obj): return (json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def window(t,day):
    require(t.tzinfo is not None,'NAIVE_CLOCK')
    start=dt.datetime.combine(day,dt.time(8,5),UTC)
    require(start<=t<start+dt.timedelta(minutes=5),'OUTSIDE_FROZEN_WINDOW')

def select(metas,index,expiry):
    require(isinstance(index,(float,int)) and not isinstance(index,bool) and math.isfinite(index) and index>0,'INDEX')
    pairs={}
    for m in metas:
        if m.get('instrument_name','').startswith('BTC_USDC-') and m.get('expiration_timestamp')==int(expiry.timestamp()*1000):
            side=m.get('option_type'); strike=m.get('strike')
            require(isinstance(strike,(float,int)) and math.isfinite(strike) and strike>0,'STRIKE')
            require(side in ('call','put'),'SIDE')
            require(side not in pairs.setdefault(strike,{}),'DUPLICATE_METADATA')
            pairs[strike][side]=m
    strikes=[k for k,v in pairs.items() if set(v)=={'call','put'}]
    require(bool(strikes),'NO_PAIR')
    strike=min(strikes,key=lambda k:(abs(k-index),k))
    require(abs(strike/index-1)<=.01,'MONEYNESS')
    chosen=pairs[strike]
    for side,m in chosen.items():
        expected=dict(kind='option',base_currency='BTC',quote_currency='USDC',settlement_currency='USDC',
                      price_index='btc_usdc',contract_size=1,min_trade_amount=.01,taker_commission=.0003,is_active=True)
        require(all(m.get(k)==v for k,v in expected.items()),'METADATA')
        require(m.get('instrument_type','linear')=='linear','PRODUCT_TYPE')
        adapter.request_url(m['instrument_name'])
        month=('JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC')[expiry.month-1]
        require(m['instrument_name']==f"BTC_USDC-{expiry.day}{month}{expiry:%y}-{strike:g}-{'C' if side=='call' else 'P'}",'SYMBOL_METADATA')
        require(math.isfinite(m['tick_size']) and m['tick_size']>0,'TICK')
    return chosen

class PublicSource:
    def __init__(self,root,clock=now):
        self.root=root; self.clock=clock; self.manifest=[]; self.lock=threading.Lock()
    def get(self,name,method,**params):
        allowed={'instruments':('get_instruments',dict(currency='USDC',kind='option',expired='false')),
                 'index':('get_index_price',dict(index_name='btc_usdc'))}
        if name in ('call','put'):
            require(method=='get_order_book' and set(params)=={'instrument_name','depth'} and params['depth']==5,'ENDPOINT')
            url=adapter.request_url(params['instrument_name'])
        else:
            require(name in allowed and (method,params)==allowed[name],'ENDPOINT')
            url='https://www.deribit.com/api/v2/public/'+method+'?'+urllib.parse.urlencode(params)
        item=dict(name=name,url=url,started=self.clock().isoformat())
        with self.lock:
            require(len(self.manifest)<4 and not any(m['name']==name for m in self.manifest),'REQUEST_BUDGET')
            self.manifest.append(item)
        try:
            req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'CryptoLab-V3-readonly'})
            try:
                with urllib.request.build_opener(adapter.NoRedirect).open(req,timeout=15) as r:
                    raw=r.read(12000001); status=r.status
            except urllib.error.HTTPError as error:
                raw=error.read(12000001); status=error.code
            item.update(received=self.clock().isoformat(),bytes=len(raw),sha256=write(self.root/(name+'.json'),raw),http_status=status)
            require(status==200 and 0<len(raw)<=12000000,'HTTP_OR_SIZE')
            obj=json.loads(raw)
            require(obj.get('testnet') is False and 'error' not in obj,'SOURCE')
            return obj['result']
        except Exception as exc:
            item['error']=type(exc).__name__+':'+str(exc); raise

def collect(root,mode='controlled_observation',clock=now,source_factory=PublicSource):
    require(mode in ('controlled_observation','prospective'),'MODE')
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    # Exclusive day claim prevents repeated prospective snapshots/cherry picking.
    day=clock().astimezone(UTC).date()
    namespace=root/mode; namespace.mkdir(exist_ok=True)
    if mode=='prospective':
        valid=sum(json.loads(p.read_bytes()).get('prospective_v3') is True for p in namespace.glob('*/receipt.json'))
        require(valid<20,'COHORT_COMPLETE')
        write(namespace/(day.isoformat()+'.claim'),encoded(dict(day=str(day))))
    attempt=namespace/(day.isoformat()+'-'+__import__('uuid').uuid4().hex)
    attempt.mkdir()
    source=source_factory(attempt,clock)
    receipt=dict(mode=mode,session_utc=str(day),valid_technical=False,prospective_v3=False,
                 live_go=False,net_pnl=None,delivery_fee_status='UNVERIFIED',orders=0,
                 precommit_hash=hashlib.sha256((Path(__file__).parent/'PRE_REGISTRATION.md').read_bytes()).hexdigest(),
                 collector_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    receipt['fee_schedule_reference']='Deribit Fees updated 2026-11-05 09:16; BTC_USDC daily delivery UNVERIFIED'
    try:
        if mode=='prospective': window(clock(),day)
        expiry=dt.datetime.combine(day+dt.timedelta(days=1),dt.time(8),UTC)
        metas=source.get('instruments','get_instruments',currency='USDC',kind='option',expired='false')
        index=source.get('index','get_index_price',index_name='btc_usdc')['index_price']
        chosen=select(metas,index,expiry)
        receipt.update(expiry=expiry.isoformat(),spot=index,metadata=chosen)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures={side:pool.submit(source.get,side,'get_order_book',instrument_name=m['instrument_name'],depth=5) for side,m in chosen.items()}
            # Wait for both even if one fails; both raw responses remain retained.
        legs={}
        for side,future in futures.items():
            future.result()
            item=next(m for m in source.manifest if m['name']==side)
            raw=(attempt/(side+'.json')).read_bytes()
            legs[side]=adapter.decode(raw,chosen[side]['instrument_name'],dt.datetime.fromisoformat(item['received']).timestamp()*1000,'controlled_observation')
        index_item=next(m for m in source.manifest if m['name']=='index')
        receipt['synchronization']=adapter.synchronize(legs['call'],legs['put'],dt.datetime.fromisoformat(index_item['received']).timestamp()*1000)
        receipt['legs']=legs
        receipt['decision_at']=clock().isoformat()
        if mode=='prospective':
            require(len(source.manifest)==4,'SOURCE_SET')
            for item in source.manifest:
                start=dt.datetime.fromisoformat(item['started']); end=dt.datetime.fromisoformat(item['received'])
                window(start,day); window(end,day); require(start<=end<=clock(),'CHRONOLOGY')
            window(dt.datetime.fromisoformat(receipt['decision_at']),day)
        receipt.update(valid_technical=True,prospective_v3=mode=='prospective',status='TECHNICAL_PASS')
    except Exception as exc:
        receipt.update(status='INVALID_ATTEMPT',reject_reason=type(exc).__name__+':'+str(exc))
    finally:
        manifest=sorted(source.manifest,key=lambda m:m['name'])
        receipt['manifest_sha256']=write(attempt/'manifest.json',encoded(manifest))
        write(attempt/'receipt.json',encoded(receipt))
    return attempt,receipt

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--out',required=True)
    a=p.parse_args()
    path,r=collect(a.out)  # CLI deliberately diagnostic-only.
    print(json.dumps(dict(path=str(path),receipt=r),indent=2))
    raise SystemExit(0 if r['valid_technical'] else 2)
