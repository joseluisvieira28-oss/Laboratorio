#!/usr/bin/env python3
"""Crypto Lab Fusion shadow ONLY: BTC spot 20D / AVAX USD-M 20D context.

No orders, no private exchange endpoints, no PnL claims. Only 2026-10-27 ..
2026-11-09 prospective observations; no backfill or 2026 research holdout replay.
Python 3.10+ stdlib. Default public-data observation, Telegram opt-in.
"""
from __future__ import annotations
import argparse
from datetime import datetime, date, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

UTC = timezone.utc
DAY_MS = 86_400_000
START = date(2026, 10, 27)
END_EXCLUSIVE = date(2026, 11, 10)
MAX_WINDOW_DELAY_SECONDS = 240
BARS = 21  # closes D-21 .. D-1, return close[D-1]/close[D-21]-1
CONTRACT_SIZE_AVAX = 0.1  # validated against public MEXC metadata every observation
SOURCES = {
    'btc_spot': ('https://api.binance.com/api/v3/klines', 'BTCUSDT'),
    'avax_um_futures': ('https://fapi.binance.com/fapi/v1/klines', 'AVAXUSDT'),
}
DEPTH_URL = 'https://contract.mexc.com/api/v1/contract/depth/AVAX_USDT?limit=20'
CONTRACT_URL = 'https://contract.mexc.com/api/v1/contract/detail?symbol=AVAX_USDT'
HEADERS = {'User-Agent': 'CryptoLab-FusionShadow-V07-research-readonly/0.7', 'Accept':'application/json'}


class SourceBlocked(Exception):
    pass


def check(ok, reason):
    if not ok:
        raise SourceBlocked(reason)


def utc_midnight_ms(day:date)->int:
    return int(datetime(day.year,day.month,day.day,tzinfo=UTC).timestamp()*1000)


def bounded_window(now:datetime)->tuple[date,str]:
    check(now.tzinfo is not None and now.utcoffset() is not None, 'NAIVE_CLOCK')
    now = now.astimezone(UTC)
    day=now.date()
    check(START <= day < END_EXCLUSIVE, 'OUTSIDE_FROZEN_FORWARD_WINDOW')
    check(now.hour in (1,2) and now.minute < 4, 'OUTSIDE_UTC_COLLECTION_WINDOW')
    check((now.minute*60+now.second+now.microsecond/1e6)<MAX_WINDOW_DELAY_SECONDS,
          'LATE_OBSERVATION')
    return day, 'entry' if now.hour==1 else 'exit'


def get_json(url:str, *, timeout=10)->tuple[object,str]:
    check(url.startswith(('https://api.binance.com/', 'https://fapi.binance.com/',
                          'https://contract.mexc.com/')), 'UNAUTHORIZED_HOST')
    req=urllib.request.Request(url, headers=HEADERS, method='GET')
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            check(resp.status == 200, 'SOURCE_HTTP_STATUS')
            data=resp.read(900_001)
            check(len(data)<900_001,'SOURCE_RESPONSE_TOO_LARGE')
    except (urllib.error.URLError, TimeoutError, OSError):
        raise SourceBlocked('PUBLIC_SOURCE_NETWORK_BLOCKED') from None
    try:
        return json.loads(data),hashlib.sha256(data).hexdigest()
    except (ValueError,UnicodeError):
        raise SourceBlocked('PUBLIC_SOURCE_NOT_JSON') from None


def validate_klines(payload, day:date)->dict:
    check(isinstance(payload,list) and len(payload)==BARS,'DAILY_KLINE_COUNT')
    earliest=day-timedelta(days=21)
    latest=day-timedelta(days=1)
    closes=[]
    for i,row in enumerate(payload):
        check(isinstance(row,list) and len(row)>6,'DAILY_KLINE_FORMAT')
        expected=utc_midnight_ms(earliest+timedelta(days=i))
        try:
            open_ms=int(row[0]); close_ms=int(row[6]); close=float(row[4]); op=float(row[1])
        except (ValueError,TypeError,OverflowError):
            raise SourceBlocked('BAD_DAILY_BAR') from None
        check(open_ms==expected and close_ms==expected+DAY_MS-1,'MISSING_OR_OPEN_DAILY_BAR')
        check(math.isfinite(close) and close>0 and math.isfinite(op) and op>0,
              'INVALID_DAILY_PRICE')
        closes.append(close)
    check(len(closes)==21,'INSUFFICIENT_HISTORY')
    delta=closes[-1]/closes[0]-1
    side='UP' if delta>0 else 'DOWN' if delta<0 else 'FLAT'
    return {'asof_last_closed_date':latest.isoformat(),'old_close':closes[0],
            'latest_close':closes[-1], 'return_20d':delta,'state':side}


def read_context(day:date)->dict:
    out={}
    for key,(url,symbol) in SOURCES.items():
        start_ms=utc_midnight_ms(day-timedelta(days=21))
        end_ms=utc_midnight_ms(day)-1
        query=urllib.parse.urlencode({'symbol':symbol,'interval':'1d',
                                      'startTime':start_ms,'endTime':end_ms,
                                      'limit':BARS})
        bars,digest=get_json(url+'?'+query)
        out[key]={**validate_klines(bars,day),'provider':'BINANCE',
                  'market':'SPOT' if key=='btc_spot' else 'USD-M_PERPETUAL',
                  'symbol':symbol,'response_sha256':digest}
    b=out['btc_spot']['state'];a=out['avax_um_futures']['state']
    out['confluence']='LONG_CONTEXT' if a==b=='UP' else (
        'SHORT_CONTEXT' if a==b=='DOWN' else 'NO_CONFLUENCE')
    return out


def validate_contract(payload)->dict:
    check(isinstance(payload,dict) and payload.get('success') is True and payload.get('code')==0,
          'MEXC_METADATA_API_FAILURE')
    data=payload.get('data')
    if isinstance(data,list):
        data=[d for d in data if isinstance(d,dict) and d.get('symbol')=='AVAX_USDT']
        check(len(data)==1, 'AVAX_CONTRACT_NOT_UNAMBIGUOUS')
        data=data[0]
    check(isinstance(data,dict) and data.get('symbol')=='AVAX_USDT',
          'AVAX_CONTRACT_IDENTITY_MISMATCH')
    try:size=float(data.get('contractSize'))
    except (ValueError,TypeError):raise SourceBlocked('AVAX_CONTRACT_SIZE_UNKNOWN') from None
    check(math.isfinite(size) and abs(size-CONTRACT_SIZE_AVAX)<1e-12,
          'AVAX_CONTRACT_SIZE_CHANGED')
    return {'symbol':'AVAX_USDT','contract_size_avax':size}


def validate_depth(payload,now:datetime)->dict:
    check(isinstance(payload,dict) and payload.get('success') is True and payload.get('code')==0,
          'MEXC_DEPTH_API_FAILURE')
    data=payload.get('data')
    check(isinstance(data,dict),'MEXC_DEPTH_FORMAT')
    try:ts=int(data['timestamp'])
    except (ValueError,TypeError,KeyError):raise SourceBlocked('MEXC_DEPTH_NO_CLOCK') from None
    recv_ms=int(now.timestamp()*1000)
    # Clock cannot be future by >3 seconds, and must be <= 30 seconds old.
    check(-3000 <= recv_ms-ts <= 30000,'MEXC_DEPTH_STALE_OR_FUTURE')
    ladders={}
    for side in ('asks','bids'):
        levels=data.get(side)
        check(isinstance(levels,list) and 1<=len(levels)<=20,'DEPTH_LEVEL_COUNT_'+side)
        parsed=[]
        for level in levels:
            check(isinstance(level,list) and len(level)>=2,'DEPTH_LEVEL_FORMAT')
            try:price=float(level[0]);contracts=float(level[1])
            except (ValueError,TypeError):raise SourceBlocked('DEPTH_NON_NUMERIC') from None
            check(math.isfinite(price) and price>0 and math.isfinite(contracts) and contracts>0,
                  'DEPTH_INVALID_PRICE_OR_VOLUME')
            parsed.append((price,contracts))
        check(all((parsed[i][0]>parsed[i-1][0] if side=='asks' else
                   parsed[i][0]<parsed[i-1][0]) for i in range(1,len(parsed))),
              'DEPTH_NOT_SORTED')
        ladders[side]=parsed
    bid=ladders['bids'][0][0];ask=ladders['asks'][0][0]
    check(bid<ask,'CROSSED_OR_LOCKED_BOOK')
    mid=(bid+ask)/2
    return {'best_bid':bid,'best_ask':ask,'spread_bps':(ask-bid)/mid*10000,
            'exchange_timestamp_utc':datetime.fromtimestamp(ts/1000,UTC).isoformat(),
            'exchange_timestamp_ms':ts,
            'best_bid_contracts':ladders['bids'][0][1],
            'best_ask_contracts':ladders['asks'][0][1],
            'bid_top_notional_usdt':bid*ladders['bids'][0][1]*CONTRACT_SIZE_AVAX,
            'ask_top_notional_usdt':ask*ladders['asks'][0][1]*CONTRACT_SIZE_AVAX,
            'levels_each':{'bids':len(ladders['bids']),'asks':len(ladders['asks'])}}


def read_book(now:datetime)->dict:
    raw_meta,meta_sha=get_json(CONTRACT_URL)
    contract=validate_contract(raw_meta)
    raw_depth,depth_sha=get_json(DEPTH_URL)
    depth=validate_depth(raw_depth,now)
    return {'provider':'MEXC','instrument':'AVAX_USDT_PERPETUAL',
            **contract,**depth,'contract_metadata_response_sha256':meta_sha,
            'depth_response_sha256':depth_sha}


def format_alert(receipt:dict)->str:
    day=receipt['utc_date'];phase=receipt['phase'];status=receipt['status']
    base=f'🔬 FUSION SHADOW V0.7 — {day} {phase.upper()} UTC\n'
    if status!='OBSERVED':return base+f'⚠️ {status}: {receipt.get("error_code", "UNKNOWN")}\nSem sinal. Nenhuma ordem.'
    book=receipt['mexc_book']
    base+=(f'MEXC AVAX_USDT bid {book["best_bid"]:.4f} / ask {book["best_ask"]:.4f}\n'
           f'Spread observado: {book["spread_bps"]:.3f} bps (snapshot, não custo real)\n')
    if phase=='entry':
        c=receipt['context']
        base+=(f'BTC20 {c["btc_spot"]["state"]}; AVAX20 {c["avax_um_futures"]["state"]}\n'
               f'Confluência: {c["confluence"]}\n')
    return base+'⚠️ INVESTIGAÇÃO / OBSERVAÇÃO APENAS. Não é recomendação nem autorização de trade.'


def send_telegram_once(receipt:dict):
    token=os.environ.get('FUSION_TELEGRAM_BOT_TOKEN','').strip()
    chat=os.environ.get('FUSION_TELEGRAM_CHAT_ID','').strip()
    if not token or not chat:return 'NOT_CONFIGURED'
    if not token.replace(':','').replace('_','').replace('-','').isalnum() or len(token)>120:
        return 'INVALID_LOCAL_CREDENTIAL_FORMAT'
    message=format_alert(receipt)
    data=urllib.parse.urlencode({'chat_id':chat,'text':message,
                                  'disable_web_page_preview':'true'}).encode('utf-8')
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',
                               data=data,method='POST',headers={'Content-Type':'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            check(r.status==200, 'TELEGRAM_HTTP_NON200')
            payload=json.load(r)
        return 'CONFIRMED' if payload.get('ok') is True else 'UNCONFIRMED'
    except Exception:
        # Never leak Telegram bot token in exception strings or logs.
        return 'UNCONFIRMED_NO_AUTOMATIC_RETRY'


def cycle(now:datetime,root:Path,notify:bool=False)->dict:
    day,phase=bounded_window(now)
    root.mkdir(parents=True,exist_ok=True)
    path=root/f'{day.isoformat()}_{phase}.json'
    # Reserve the one allowed attempt atomically before GET or Telegram send.
    # If process crashes, leave a pending receipt and NEVER blindly retry.
    try:
        with path.open('x',encoding='utf-8') as f:
            f.write(json.dumps({'status':'PENDING_NO_RETRY','utc_date':day.isoformat(),
                                'phase':phase,'created_at_utc':now.isoformat()},indent=2)+'\n')
    except FileExistsError:
        raise SourceBlocked('DUPLICATE_WINDOW_NO_RETRY') from None
    receipt={'schema_version':'0.7','utc_date':day.isoformat(),'phase':phase,
             'observed_at_utc':now.astimezone(UTC).isoformat(),
             'window':f'{START.isoformat()}..{(END_EXCLUSIVE-timedelta(days=1)).isoformat()}',
             'status':'SOURCE_BLOCKED','execution_authority':False,'trading':'NO_ORDERS',
             'sealed_research_holdout_files':'NOT_ACCESSED_PUBLIC_FORWARD_CONTEXT_ONLY','assumed_fee_bps':None,
             'live_pnl':None}
    try:
        if phase=='entry':receipt['context']=read_context(day)
        # Use actual receive time just after public request, not run-start time.
        # read_book validates against clock sampled before request; small differences
        # are bounded by freshness limit, do not backdate snapshot timestamps.
        receipt['mexc_book']=read_book(datetime.now(UTC))
        receipt['status']='OBSERVED'
    except SourceBlocked as e:
        receipt['error_code']=str(e)
    except Exception:
        receipt['error_code']='UNEXPECTED_SOURCE_FAILURE'
    # Only entry sends an optional Telegram notification; exit is ledger-only.
    if notify and phase=='entry':
        receipt['telegram_delivery']=send_telegram_once(receipt)
    else:receipt['telegram_delivery']='DISABLED_OR_EXIT'
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    os.replace(tmp,path)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycle',action='store_true',help='Collect a live 01 or 02 UTC window, public GET only')
    p.add_argument('--notify-telegram',action='store_true',help='Opt-in 01 UTC Telegram research alert')
    p.add_argument('--root',type=Path,default=Path('shadow_ledger_v07'))
    opts=p.parse_args()
    if not opts.cycle:
        print('NOT_RUNNING: pass --cycle during frozen 01:00/02:00 UTC windows. No API orders.');return 0
    now=datetime.now(UTC)
    try:
        result=cycle(now,opts.root,opts.notify_telegram)
        print(json.dumps({'status':result['status'],'date':result['utc_date'],
                          'phase':result['phase'],'telegram':result['telegram_delivery'],
                          'error_code':result.get('error_code','')},ensure_ascii=False))
        return 0 if result['status']=='OBSERVED' else 3
    except SourceBlocked as e:
        print('FAIL_CLOSED:'+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
