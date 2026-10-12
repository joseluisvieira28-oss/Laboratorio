"""Public, post-close 1h MEXC Futures market source with bounded freshness.
Signed account endpoints are in mexc_futures.py; this module has no secrets.
"""
from __future__ import annotations
import json, math, statistics, time
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE='https://api.mexc.com'  # MEXC Futures new domain since 2026-01
HOUR_MS=3600000
SYMBOLS=('ETH_USDT','SOL_USDT','BNB_USDT')
class MarketError(RuntimeError):pass

def fetch(path,params=None,opener=urlopen):
    if not (path=='/api/v1/contract/detail' or path.startswith('/api/v1/contract/kline/') or path.startswith('/api/v1/contract/depth/')):
        raise MarketError('PUBLIC_PATH_NOT_ALLOWED')
    url=BASE+path+('?' + urlencode(params) if params else '')
    before=time.time_ns()//1000000
    try:
        with opener(Request(url,headers={'User-Agent':'CryptoLab-ConvexRadar/1.0'}),timeout=12) as response:
            raw=response.read()
    except Exception as e:raise MarketError('PUBLIC_HTTP_ERROR:'+type(e).__name__) from e
    after=time.time_ns()//1000000
    if after-before>3500:raise MarketError('SLOW_SOURCE')
    try:p=json.loads(raw)
    except (ValueError,TypeError) as e:raise MarketError('PUBLIC_BAD_JSON') from e
    if not isinstance(p,dict) or p.get('success') is not True or p.get('code')!=0:raise MarketError('PUBLIC_REJECTED')
    return p.get('data'),{'before_ms':before,'after_ms':after,'latency_ms':after-before}

def spec(symbol,client=fetch):
    if symbol not in SYMBOLS:raise MarketError('SYMBOL_DENIED')
    data,_=client('/api/v1/contract/detail',{'symbol':symbol})
    rows=data if isinstance(data,list) else [data]
    matched=[r for r in rows if isinstance(r,dict) and r.get('symbol')==symbol]
    if len(matched)!=1:raise MarketError('SPEC_NOT_FOUND')
    s=matched[0]
    if s.get('state')!=0 or s.get('quoteCoin')!='USDT' or s.get('settleCoin')!='USDT' or s.get('futureType')!=1:
        raise MarketError('CONTRACT_NOT_ACTIVE_USDT_PERP')
    vals={k:float(s[k]) for k in ('contractSize','minVol','volUnit','maxVol','priceUnit')}
    if not all(math.isfinite(v) and v>0 for v in vals.values()):raise MarketError('INVALID_SPEC')
    vals['symbol']=symbol
    if s.get('apiAllowed') is False:raise MarketError('CONTRACT_API_NOT_ALLOWED')
    return vals

def book(symbol,client=fetch):
    data,meta=client('/api/v1/contract/depth/'+symbol,{'limit':20})
    if not isinstance(data,dict) or not data.get('asks') or not data.get('bids'):raise MarketError('NO_BOOK')
    try:
        ask=float(data['asks'][0][0]);bid=float(data['bids'][0][0]);ts=int(data['timestamp'])
    except (TypeError,ValueError,KeyError,IndexError) as e:raise MarketError('BAD_BOOK') from e
    if not (0<bid<ask):raise MarketError('BAD_BID_ASK')
    age=meta['after_ms']-ts
    if not 0<=age<=2500:raise MarketError('STALE_BOOK')
    if (ask-bid)/ask>0.003:raise MarketError('SPREAD_TOO_WIDE')
    return {'ask':ask,'bid':bid,'age_ms':age,'as_of_ms':meta['after_ms']}

def bars(symbol,clock_ms=None,client=fetch):
    now=int(clock_ms if clock_ms is not None else time.time_ns()//1000000)
    boundary=now//HOUR_MS*HOUR_MS
    raw,meta=client('/api/v1/contract/kline/'+symbol,
                    {'interval':'Min60','start':boundary//1000-440*3600,'end':boundary//1000})
    keys=('time','open','high','low','close','vol')
    if not isinstance(raw,dict) or any(not isinstance(raw.get(k),list) for k in keys):raise MarketError('KLINE_BAD_SHAPE')
    n=len(raw['time'])
    if n<400 or any(len(raw[k])!=n for k in keys):raise MarketError('KLINE_INSUFFICIENT')
    result=[]
    for i in range(n):
        t=int(raw['time'][i])*1000
        if t%HOUR_MS:raise MarketError('KLINE_UNALIGNED')
        o,h,l,c,v=[float(raw[k][i]) for k in keys[1:]]
        if not all(math.isfinite(x) for x in (o,h,l,c,v)) or min(o,h,l,c)<=0 or v<0 or h<max(o,c) or l>min(o,c):
            raise MarketError('BAD_OHLC')
        if t<boundary:result.append({'open_ms':t,'boundary_ms':t+HOUR_MS,'open':o,'high':h,'low':l,'close':c,'vol':v})
    result.sort(key=lambda x:x['open_ms'])
    if len(result)<400:raise MarketError('INCOMPLETE_CLOSED_CANDLES')
    result=result[-400:]
    if result[-1]['boundary_ms']!=boundary or any(b['open_ms']-a['open_ms']!=HOUR_MS for a,b in zip(result,result[1:])):
        raise MarketError('CANDLE_GAP_OR_STALE')
    if meta['latency_ms']>3500:raise MarketError('CANDLES_SLOW')
    return result

def signal_parent_v5(candles):
    if len(candles)<400:raise MarketError('NOT_ENOUGH_HISTORY')
    close=[r['close'] for r in candles];vol=[r['vol'] for r in candles]
    sma20=sum(close[-20:])/20;sd=statistics.pstdev(close[-20:]);sma200=sum(close[-200:])/200
    gains=[max(close[i]-close[i-1],0) for i in range(1,len(close))]
    losses=[max(close[i-1]-close[i],0) for i in range(1,len(close))]
    ag=sum(gains[:14])/14;al=sum(losses[:14])/14
    for g,l in zip(gains[14:],losses[14:]):ag=(ag*13+g)/14;al=(al*13+l)/14
    rsi=100 if al==0 else 100-100/(1+ag/al)
    z=(close[-1]-sma20)/sd if sd>0 else None
    flags={'rsi_lt30':rsi<30,'z_below_minus2':z is not None and z< -2,
           'below_bb_lower':sd>0 and close[-1]<sma20-2*sd,'volume_above20':vol[-1]>sum(vol[-20:])/20}
    score=sum(flags.values());regime=close[-1]>sma200
    return {'signal':bool(regime and score>=3),'score':score,'rsi':rsi,'regime':regime,'flags':flags}

def floor_price(price,unit):
    if price<=0 or unit<=0:raise MarketError('BAD_PRICE_UNIT')
    return float((Decimal(str(price))//Decimal(str(unit)))*Decimal(str(unit)))