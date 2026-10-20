"""Bounded anonymous source-only GET receipts; NOT a signal/PnL collector.
No historical candles, settlement history, accounts, credentials, order code or daemon.
"""
import argparse,hashlib,json,time
from decimal import Decimal,ROUND_FLOOR
from pathlib import Path
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener
from urllib.parse import urlsplit

HOSTS={'api.mexc.com','contract.mexc.com','fapi.binance.com'}
SYMBOLS=('SOL','BNB')
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args):raise ValueError('REDIRECT_REJECTED')

def allowed(url):
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password or u.fragment: return False
    if u.hostname=='fapi.binance.com':return u.path in {'/fapi/v1/time','/fapi/v1/ticker/bookTicker'}
    return u.path in {'/api/v1/contract/ping','/api/v1/contract/detail/country','/api/v1/contract/detail'} or any(u.path==f'/api/v1/contract/{kind}/{sym}_USDT' for kind in ['depth','funding_rate'] for sym in SYMBOLS)

def walk(levels,contracts):
    want=Decimal(str(contracts));left=want;cash=Decimal(0)
    if want<=0:raise ValueError('NONPOSITIVE_SIZE')
    for row in levels:
        price=Decimal(str(row[0]));qty=Decimal(str(row[1]))
        if not price.is_finite() or not qty.is_finite() or price<=0 or qty<=0:raise ValueError('BAD_BOOK')
        take=min(left,qty);cash+=take*price;left-=take
        if left==0:return float(cash/want)
    return None

def summarize(meta,book):
    for key in ['contractSize','minVol','volUnit','priceUnit']:
        if Decimal(str(meta[key]))<=0:raise ValueError('BAD_CONTRACT')
    cs=Decimal(str(meta['contractSize']));step=Decimal(str(meta['volUnit']));minimum=Decimal(str(meta['minVol']))
    asks=book['asks'];bids=book['bids']
    if not asks or not bids:raise ValueError('EMPTY_BOOK')
    ask=Decimal(str(asks[0][0]));bid=Decimal(str(bids[0][0]))
    if ask<=0 or bid<=0 or bid>=ask:raise ValueError('LOCKED_OR_CROSSED_BOOK')
    # Validate full visible book, avoid silently accepting corrupt far levels.
    for levels,ascending in [(asks,True),(bids,False)]:
        prices=[Decimal(str(x[0])) for x in levels]
        if prices!=sorted(prices,reverse=not ascending):raise ValueError('UNSORTED_BOOK')
        for x in levels:walk([x],Decimal(str(x[1])))
    sizes=[]
    for label,n in [('min_contract',None),('20_USDT',20),('200_USDT',200),('2000_USDT',2000)]:
        vol=minimum if n is None else (Decimal(n)/(ask*cs)/step).to_integral_value(rounding=ROUND_FLOOR)*step
        if vol<minimum:sizes.append(dict(label=label,status='BELOW_MINIMUM',contracts=str(vol)));continue
        if vol%step:raise ValueError('MIN_NOT_ON_STEP')
        av=walk(asks,vol);bv=walk(bids,vol);notional=vol*cs*ask
        sizes.append(dict(label=label,contracts=str(vol),base_qty=str(vol*cs),entry_notional_at_ask=str(notional),static_ask_vwap=av,static_bid_vwap=bv,ask_depth_walk_bps=None if av is None else (av/float(ask)-1)*10000,spread_bps=float((ask-bid)/((ask+bid)/2)*10000),initial_nominal_1R_USDT=str(notional*Decimal('.04')),margin_1x_reference_USDT=str(notional),margin_10x_arithmetic_only_USDT=str(notional/10),actual_fill_proven=False))
    return dict(contract={k:meta.get(k) for k in ['symbol','baseCoin','quoteCoin','settleCoin','futureType','contractSize','minVol','volUnit','priceUnit','minLeverage','maxLeverage','initialMarginRate','maintenanceMarginRate','state','apiAllowed','takerFeeRate','feeRateMode','feeRateType','stopOnlyFair']},book_timestamp=book.get('timestamp'),sizes=sizes)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
    if out.exists():raise SystemExit('OUTPUT_MUST_BE_NEW')
    out.mkdir(parents=True);raw=out/'raw';raw.mkdir();receipts=[];decoded={};opener=build_opener(NoRedirect())
    urls=[]
    for host in ['api.mexc.com','contract.mexc.com']:
        urls.append(f'https://{host}/api/v1/contract/ping')
        for sym in SYMBOLS:
            # Current + legacy publicly documented metadata; bounded fallback, no retry loop.
            path='detail/country' if host=='api.mexc.com' else 'detail'
            urls.extend([f'https://{host}/api/v1/contract/{path}?symbol={sym}_USDT',f'https://{host}/api/v1/contract/depth/{sym}_USDT?limit=20',f'https://{host}/api/v1/contract/funding_rate/{sym}_USDT'])
    urls+=['https://fapi.binance.com/fapi/v1/time']+[f'https://fapi.binance.com/fapi/v1/ticker/bookTicker?symbol={s}USDT' for s in SYMBOLS]
    assert len(urls)==17
    for i,url in enumerate(urls):
        assert allowed(url);start=time.time_ns()//1000000;mono=time.monotonic();r=dict(url=url,requested_at_ms=start,method='GET',authenticated=False)
        try:
            with opener.open(Request(url,headers={'User-Agent':'ConvexSourceAudit/1.0','Accept':'application/json'}),timeout=5) as response:
                body=response.read(2_000_001)
                if len(body)>2_000_000:raise ValueError('RESPONSE_SIZE_LIMIT')
                r['http_status']=response.status;r['content_type']=response.headers.get('Content-Type')
                file=f'{i:02}.json';(raw/file).write_bytes(body);r.update(raw_file='raw/'+file,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body));doc=json.loads(body);decoded[url]=doc;r['json_decoded']=True
        except Exception as exc:r.update(error_type=type(exc).__name__,error=str(exc)[:500])
        r.update(received_at_ms=time.time_ns()//1000000,rtt_ms=round((time.monotonic()-mono)*1000,3));receipts.append(r)
    summaries=[]
    for host in ['api.mexc.com','contract.mexc.com']:
        for sym in SYMBOLS:
            key='detail/country' if host=='api.mexc.com' else 'detail'
            try:
                md=decoded[f'https://{host}/api/v1/contract/{key}?symbol={sym}_USDT']['data']
                if isinstance(md,list):md=next(m for m in md if m['symbol']==sym+'_USDT')
                bk=decoded[f'https://{host}/api/v1/contract/depth/{sym}_USDT?limit=20']['data']
                assert md['symbol']==sym+'_USDT';summaries.append(dict(host=host,symbol=sym,status='STATIC_SOURCE_ONLY',**summarize(md,bk)))
            except Exception as exc:summaries.append(dict(host=host,symbol=sym,status='SOURCE_UNVERIFIED',error_type=type(exc).__name__,error=str(exc)[:200]))
    report=dict(status='SOURCE_ONLY_NO_ALPHA_NO_PNL',freeze_path='FREEZE_V1.md',freeze_sha256=hashlib.sha256(Path(__file__).with_name('FREEZE_V1.md').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),requests=receipts,summaries=summaries,continuous_collector_active=False,eligible_prospective_trades=0,funding_settlements_verified=0)
    (out/'RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'requests':len(receipts),'http_success':sum(r.get('http_status')==200 for r in receipts),'continuous':False,'summaries':summaries},indent=2))
if __name__=='__main__':main()
