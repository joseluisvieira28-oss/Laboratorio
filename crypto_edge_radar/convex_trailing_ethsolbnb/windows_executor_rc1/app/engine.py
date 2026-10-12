"""Crypto Lab / Radar — single-owner prospective MEXC ETH SOL BNB long engine.

No scientific credit: venue real fills differ from historic next-hour-open OHLC.
Order mutation requires explicit local live authority; dry mode is the default.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, traceback
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import dataclass
from typing import Any
from convex_core import size_for_risk,initial_position,evaluate_closed_bar,TrailPosition
import market
from mexc_futures import MexcFutures,ExchangeError

ROOT=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) /'CryptoLab'/'ConvexRadarTrade'
STATE=ROOT/'state';STATE.mkdir(parents=True,exist_ok=True)
LEDGER=STATE/'ledger.json';AUTH=STATE/'LIVE_AUTHORITY.json';KILL=STATE/'KILL_SWITCH';LOG=STATE/'events.jsonl'
CONFIG=Path(__file__).resolve().parent.parent/'config.json'
SYMS=('ETH_USDT','SOL_USDT','BNB_USDT')
class EngineBlocked(RuntimeError):pass

def utc():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
_SINGLETON_HANDLE=None
def acquire_process_lock():
    """One owner per Windows user; operating system releases on crash."""
    global _SINGLETON_HANDLE
    if _SINGLETON_HANDLE is not None:raise EngineBlocked('PROCESS_ALREADY_OWNS_LOCK')
    fd=(STATE/'engine.lock').open('a+b');fd.seek(0)
    if os.name=='nt':
        import msvcrt
        if fd.seek(0,2)==0:fd.write(b'X');fd.flush()
        fd.seek(0)
        try:msvcrt.locking(fd.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            fd.close();raise EngineBlocked('OTHER_CONVEX_ENGINE_ALREADY_RUNNING')
    else:
        import fcntl
        try:fcntl.flock(fd.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            fd.close();raise EngineBlocked('OTHER_CONVEX_ENGINE_ALREADY_RUNNING')
    _SINGLETON_HANDLE=fd

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def read(path,default=None):
    if not path.exists():return default
    obj=json.loads(path.read_text(encoding='utf-8'))
    return obj

def event(category,**extra):
    obj={'utc':utc(),'kind':category,**extra}
    with LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True,default=str)+'\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(obj,ensure_ascii=False,default=str),flush=True)

def config():
    p=read(CONFIG)
    if not isinstance(p,dict) or p.get('candidate_id')!='BTC-CONVEX-PARENT-V5-NONLATCHED-TRAIL-ETHSOLBNB-001':
        raise EngineBlocked('CONFIG_IDENTITY_INVALID')
    if p.get('symbols')!=list(SYMS) or p.get('exit')!={'initial_stop_pct':4,'trail_activation_close_pct':5,'peak_offset_pct':12,'take_profit':None}:
        raise EngineBlocked('FROZEN_SCIENCE_IDENTITY_CHANGED')
    if not isinstance(p.get('leverage'),int) or not 1<=p['leverage']<=20:raise EngineBlocked('LEVERAGE_INVALID')
    if not .0001<=float(p.get('per_trade_risk_fraction',0))<=.025:raise EngineBlocked('RISK_CAP_INVALID')
    if not .0001<=float(p.get('aggregate_risk_fraction',0))<=.05:raise EngineBlocked('AGGREGATE_RISK_CAP_INVALID')
    if not 0<float(p.get('max_margin_fraction',0))<=.5:raise EngineBlocked('MARGIN_CAP_INVALID')
    return p

def ledger():
    s=read(LEDGER,{'format':2,'signals':{},'entries':{},'positions':{},'blocks':{},'history':[],'exits':{}})
    if not isinstance(s,dict) or s.get('format')!=2:raise EngineBlocked('LEDGER_BAD_OR_OLD')
    for k in ('signals','entries','positions','blocks','history','exits'):
        if k not in s:raise EngineBlocked('LEDGER_INCOMPLETE')
    return s

def save(s):atomic(LEDGER,s)
def oid(symbol,boundary,kind):
    digest=hashlib.sha256(f'{symbol}:{boundary}:{kind}:convex-v1'.encode()).hexdigest()[:21]
    return 'cv1-'+kind[:2]+'-'+digest

def frozen_authority():
    a=read(AUTH)
    if not isinstance(a,dict) or a.get('status')!='ARMED' or a.get('candidate_id')!=config()['candidate_id']:
        return False
    if KILL.exists():return False
    if a.get('config_sha256')!=hashlib.sha256(CONFIG.read_bytes()).hexdigest():return False
    return True

def account_snapshot(client):
    ps=client.positions();oo=client.orders();ss=client.stops();assets=client.assets()
    if not all(isinstance(v,list) for v in (ps,oo,ss,assets)):raise EngineBlocked('INVALID_ACCOUNT_READBACK_SHAPE')
    if int(client.position_mode())!=1:raise EngineBlocked('HEDGE_MODE_REQUIRED')
    return {'positions':ps,'orders':oo,'stops':ss,'assets':assets}

def positions_for_symbol(snap,sym):
    return [p for p in snap['positions'] if p.get('symbol')==sym and float(p.get('holdVol',p.get('vol',0)))>0]

def matching_stop(snap,position_id):
    found=[x for x in snap['stops'] if int(x.get('positionId',-1))==int(position_id)
           and float(x.get('stopLossPrice',0) or 0)>0 and int(x.get('isFinished',0))==0]
    if len(found)>1:raise EngineBlocked('MULTIPLE_POSITION_STOPS')
    return found[0] if found else None

def validated_stop(snap,position_id,volume,expected=None,unit=None):
    st=matching_stop(snap,position_id)
    if st is None:raise EngineBlocked('NO_EXCHANGE_STOP')
    if float(st.get('vol',0))<float(volume):raise EngineBlocked('STOP_COVERAGE_TOO_SMALL')
    if int(st.get('positionId',-1))!=int(position_id):raise EngineBlocked('STOP_OWNER_WRONG')
    if expected is not None and abs(float(st['stopLossPrice'])-float(expected))>max(float(unit or 0)*.501,abs(float(expected))*1e-7):
        raise EngineBlocked('STOP_PRICE_READBACK_MISMATCH')
    if float(st.get('takeProfitPrice',0) or 0)>0:raise EngineBlocked('UNEXPECTED_TP_NONORIGINAL')
    return st

def assert_clean_account(s,snap):
    owned={int(p['position_id']):sym for sym,p in s['positions'].items()}
    other=[p for p in snap['positions'] if int(p.get('positionId',0)) not in owned]
    if other:raise EngineBlocked('FOREIGN_POSITIONS_PRESENT_KEEP_EXISTING_RADAR_OWNER')
    if snap['orders']:raise EngineBlocked('OPEN_ORDERS_REQUIRE_OWNER_RECONCILIATION')
    for p in snap['positions']:
        pid=int(p.get('positionId',0));sym=owned.get(pid)
        if sym is None:raise EngineBlocked('POSITION_OWNER_NOT_KNOWN')
        if p.get('symbol')!=sym or int(p.get('positionType',1))!=1:
            raise EngineBlocked('OWNED_POSITION_IDENTITY_CHANGED')
    for st in snap['stops']:
        if int(st.get('positionId',0)) not in owned:raise EngineBlocked('FOREIGN_STOP_PRESENT')
    for sym,p in s['positions'].items():
        matching=[x for x in snap['positions'] if int(x.get('positionId',0))==int(p['position_id'])]
        if matching:
            validated_stop(snap,p['position_id'],p['contracts'])

def equity_and_available(snap):
    usdt=[x for x in snap['assets'] if str(x.get('currency','')).upper()=='USDT']
    if len(usdt)!=1:raise EngineBlocked('USDT_ASSET_MISSING_OR_DUPLICATE')
    a=usdt[0]
    def field(*keys):
        for k in keys:
            if k in a and a[k] is not None:return float(a[k])
        raise EngineBlocked('USDT_ACCOUNT_FIELD_MISSING:'+keys[0])
    equity=field('equity','equityUsdt','totalEquity')
    available=field('availableBalance','available','availableMargin')
    if equity<=0:raise EngineBlocked('BAD_ACCOUNT_EQUITY')
    if available<0:raise EngineBlocked('NEGATIVE_AVAILABLE')
    return equity,available

def record_block(s,symbol,msg):
    s['blocks'][symbol]={'reason':msg,'utc':utc()};save(s);event('BLOCKED',symbol=symbol,reason=msg)

def update_closed_position(s,symbol,candles,client,venue_snap,contract_spec,live):
    item=s['positions'][symbol]
    match=[p for p in venue_snap['positions'] if int(p.get('positionId',0))==int(item['position_id'])]
    if not match:
        s['history'].append({'symbol':symbol,'position_id':item['position_id'],'closed_observed_utc':utc(),'comment':'EXCHANGE_CLOSED_VERIFY_REALIZED_ACCOUNT'})
        del s['positions'][symbol]
        s['entries'].pop(symbol,None)
        s['exits'].pop(symbol,None)
        save(s);event('EXCHANGE_POSITION_CLOSED',symbol=symbol);return
    v=match[0]
    if int(float(v.get('holdVol',v.get('vol',0))))!=item['contracts']:
        raise EngineBlocked('POSITION_VOLUME_CHANGED_EXTERNALLY')
    st=validated_stop(venue_snap,item['position_id'],item['contracts'])
    if item.get('pending_stop'):
        wanted=item['pending_stop']['price']
        validated_stop(venue_snap,item['position_id'],item['contracts'],wanted,contract_spec['priceUnit'])
        item.update(item['pending_stop']['next_state']);item['pending_stop']=None;save(s)
        event('PENDING_STOP_READBACK_RESOLVED',symbol=symbol)
    pending_bars=[x for x in candles if x['boundary_ms']>int(item['last_boundary'])]
    if len(pending_bars)>1:raise EngineBlocked('MISSED_HOURLY_STOP_UPDATE_NO_RETROACTIVE_BROKER_REPLAY')
    for bar in pending_bars:
        p=TrailPosition(symbol,int(item['position_id']),float(item['entry']),float(item['peak']),
                        float(item['stop']),int(item['contracts']),int(item['last_boundary']),str(st['id']))
        res=evaluate_closed_bar(p,boundary=bar['boundary_ms'],open_price=bar['open'],high=bar['high'],low=bar['low'],close=bar['close'])
        if res['action']=='EXCHANGE_STOP_RECONCILIATION_REQUIRED':
            raise EngineBlocked('BAR_TOUCHED_PRIOR_STOP_YET_POSITION_OPEN_CHECK_EXCHANGE')
        if res['action']=='DUPLICATE_OR_OLD_BAR':continue
        nxt=res['position'];target=market.floor_price(float(nxt.active_stop),contract_spec['priceUnit'])
        ns={'last_boundary':bar['boundary_ms'],'peak':nxt.peak_high,'stop':target}
        if res['action']=='CHANGE_STOP' and abs(float(st['stopLossPrice'])-target)>contract_spec['priceUnit']*.51:
            if target>=bar['close']:
                raise EngineBlocked('NEXT_STOP_ABOVE_OR_EQUAL_CLOSING_PRICE__UNSUPPORTED_AT_BROKER')
            if not live:
                item.update(ns);save(s);event('DRY_TRAIL_PRICE',symbol=symbol,stop=target);continue
            # Durable intent BEFORE exchange mutation; ambiguous response never causes a blind re-send.
            item['pending_stop']={'id':str(st['id']),'price':target,'next_state':ns,'utc':utc()};save(s)
            client.revise_stop_only(str(st['id']),target)
            ss=client.stops()
            verified=validated_stop({'stops':ss},item['position_id'],item['contracts'],target,contract_spec['priceUnit'])
            st=verified
            item.update(ns);item['pending_stop']=None;save(s)
            event('TRAIL_UPDATED_AND_VERIFIED',symbol=symbol,stop=target)
        else:
            item.update(ns);save(s)

def entry_recovery(s,symbol,client):
    """Recover acknowledged/uncertain exchange order by deterministic externalOid. Never resend."""
    intent=s['entries'][symbol]
    try:order=client.order_by_external(symbol,intent['oid'])
    except Exception as e:raise EngineBlocked('ORDER_OUTCOME_UNKNOWN_MANUAL_REVIEW:'+type(e).__name__) from e
    if not isinstance(order,dict):raise EngineBlocked('ORDER_OUTCOME_MISSING_MANUAL_REVIEW')
    if int(order.get('side',0))!=1 or order.get('symbol')!=symbol or str(order.get('externalOid',''))!=intent['oid']:
        raise EngineBlocked('ORDER_READBACK_IDENTITY_MISMATCH')
    if int(order.get('state',0))!=3 or float(order.get('dealVol',0))<=0:
        raise EngineBlocked('ORDER_NOT_VERIFIED_FULLY_FILLED')
    if int(float(order['dealVol']))!=intent['contracts']:
        raise EngineBlocked('PARTIAL_FILL_NO_UNVERIFIED_STOP')
    entry=float(order['dealAvgPrice']);pid=int(order['positionId'])
    if entry<=0 or pid<=0:raise EngineBlocked('NO_FILL_PRICE_OR_POSITION_ID')
    snap=account_snapshot(client)
    matching=[x for x in snap['positions'] if int(x.get('positionId',0))==pid and x.get('symbol')==symbol]
    if len(matching)!=1:raise EngineBlocked('FILLED_POSITION_NOT_IN_ACCOUNT')
    st=matching_stop(snap,pid)
    if st is None:
        if intent.get('stop_place_attempted'):
            raise EngineBlocked('STOP_PLACE_UNKNOWN_MANUAL_REVIEW_NO_RETRY')
        intent['stop_place_attempted']=True;save(s)
        client.install_stop_only(pid,intent['contracts'],market.floor_price(entry*.96,intent['price_unit']))
        snap=account_snapshot(client)
        st=matching_stop(snap,pid)
    validated_stop(snap,pid,intent['contracts'])
    initial=market.floor_price(entry*.96,intent['price_unit'])
    # Attached initial stop may have been calculated off prefill ask; align after confirming original stop.
    if abs(float(st['stopLossPrice'])-initial)>intent['price_unit']*.51:
        if intent.get('initial_adjust_attempted'):
            raise EngineBlocked('INITIAL_STOP_ADJUST_UNKNOWN_NO_RETRY')
        intent['initial_adjust_attempted']=True;save(s)
        client.revise_stop_only(str(st['id']),initial)
        st=validated_stop({'stops':client.stops()},pid,intent['contracts'],initial,intent['price_unit'])
    s['positions'][symbol]={'position_id':pid,'entry':entry,'contracts':intent['contracts'],
        'peak':entry,'stop':initial,'stop_id':str(st['id']),'last_boundary':intent['boundary'],
        'pending_stop':None,'entry_oid':intent['oid'],'contract_size':intent['contract_size'],'owned_since_utc':utc()}
    intent['phase']='POSITION_OWNED_PROTECTED';save(s)
    event('ENTRY_VERIFIED_PROTECTED',symbol=symbol,position_id=pid,stop=initial,contracts=intent['contracts'])

def emergency_flatten_unprotected(s,client,snap):
    """One-shot position close if a tracked position suddenly has no broker stop.
    May itself be ambiguous; never blind-retry an unknown close response.
    """
    for sym,item in list(s['positions'].items()):
        pid=int(item['position_id'])
        still_open=any(int(p.get('positionId',0))==pid for p in snap['positions'])
        if not still_open:continue
        if matching_stop(snap,pid) is not None:continue
        if sym in s['exits']:
            raise EngineBlocked('UNPROTECTED_EXIT_ALREADY_ATTEMPTED_RECONCILE_MANUALLY')
        close_oid=oid(sym,item['last_boundary'],'emergency')
        s['exits'][sym]={'oid':close_oid,'pid':pid,'phase':'EMERGENCY_CLOSE_SUBMIT_MAY_HAVE_HAPPENED','utc':utc()}
        save(s);event('EMERGENCY_CLOSE_UNPROTECTED_POSITION',symbol=sym,position_id=pid)
        client.close_owned_long(sym,int(item['contracts']),pid,close_oid)
        raise EngineBlocked('EMERGENCY_CLOSE_SENT_WAIT_FOR_EXCHANGE_RECONCILIATION')

def prospective_entry(s,symbol,boundary,book,spec,cfg,client,snap,live):
    if symbol in s['positions'] or symbol in s['entries'] or symbol in s['blocks']:return
    equity,available=equity_and_available(snap)
    sizing=size_for_risk(equity_usdt=equity,market_ask=book['ask'],contract_size=spec['contractSize'],
             min_vol=spec['minVol'],vol_unit=spec['volUnit'],max_vol=spec['maxVol'],
             per_trade_risk=float(cfg['per_trade_risk_fraction']),leverage=int(cfg['leverage']),
             max_notional_fraction=float(cfg['max_margin_fraction']),per_side_fee_bps=8,slippage_bps=5)
    if sizing['status']!='SIZED':
        event('NO_ENTRY_LOT_RISK',symbol=symbol,detail=sizing);return
    if sizing['margin_estimate_usdt']>available*.8:raise EngineBlocked('ACCOUNT_AVAILABLE_MARGIN_INSUFFICIENT')
    active_risk=sum(p['contracts']*p['contract_size']*p['entry']*.0421 for p in s['positions'].values())  # intentionally conservative floor
    if sizing['estimated_loss_budget_usdt']+active_risk>equity*float(cfg['aggregate_risk_fraction']):
        event('NO_ENTRY_AGGREGATE_RISK',symbol=symbol);return
    stop=market.floor_price(book['ask']*.96,spec['priceUnit'])
    if stop<=0 or stop>=book['bid']:raise EngineBlocked('BAD_INITIAL_STOP_GEOMETRY')
    intent={'boundary':boundary,'oid':oid(symbol,boundary,'entry'),'contracts':int(sizing['contracts']),
            'leverage':int(cfg['leverage']),'stop_estimate':stop,'price_unit':spec['priceUnit'],'contract_size':spec['contractSize'],
            'phase':'PREPARED','at_utc':utc(),'stop_place_attempted':False,'initial_adjust_attempted':False}
    s['entries'][symbol]=intent;save(s)
    if not live:
        intent['phase']='DRY_RUN_NO_ORDER';save(s)
        event('DRY_SIGNAL',symbol=symbol,contracts=intent['contracts'],stop_estimate=stop,leverage=intent['leverage']);return
    # Phase journal first, including preflight of shared-account ownership.
    live_snapshot=account_snapshot(client);assert_clean_account(s,live_snapshot)
    client.prepare_long(symbol,intent['leverage'])
    intent['phase']='ORDER_SUBMIT_MAY_HAVE_HAPPENED';save(s)
    # Attached SL protects against gap before a separate stop-install response.
    ack=client.buy_with_initial_stop(symbol,intent['contracts'],intent['leverage'],intent['oid'],stop)
    intent['order_id']=str(ack['orderId']);intent['phase']='ORDER_ACKED';save(s)
    entry_recovery(s,symbol,client)

def tick(client=None,now=None,dry=False):
    cfg=config();s=ledger();now=int(now or time.time_ns()//1000000)
    live=bool(frozen_authority() and not dry)
    if KILL.exists():live=False
    if live and client is None:client=MexcFutures()
    # In DRY mode we never instantiate an authenticated client unless one is injected.
    if client is not None:
        snap=account_snapshot(client)
        # Recovery of a previously sent order must precede the foreign-position check.
        for symbol,intent in list(s['entries'].items()):
            if intent.get('phase')=='DRY_RUN_NO_ORDER':continue
            if symbol not in s['positions']:entry_recovery(s,symbol,client)
        snap=account_snapshot(client)
        if s['positions']:
            emergency_flatten_unprotected(s,client,snap)
        assert_clean_account(s,snap)
    else:
        snap={'positions':[],'orders':[],'stops':[],'assets':[]}
    for sym in SYMS:
        try:
            hist=market.bars(sym)
            if sym in s['positions']:
                if client is None:raise EngineBlocked('POSITION_EXISTS_BUT_NO_CREDENTIALS_FOR_EXIT_MANAGEMENT')
                update_closed_position(s,sym,hist,client,snap,market.spec(sym),bool(client))
                continue
            if sym in s['entries'] or sym in s['blocks']:continue
            boundary=hist[-1]['boundary_ms']
            if not 0<=now-boundary<=600000:continue
            # Do not score future/incomplete candles or stale delayed runs.
            if abs((time.time_ns()//1000000)-now)>60000:raise EngineBlocked('CLOCK_SKEW')
            identity=f'{sym}:{boundary}'
            if identity in s['signals']:continue
            result=market.signal_parent_v5(hist)
            s['signals'][identity]={'signal':result['signal'],'score':result['score'],'decided_at':utc(),'type':'LIVE_PUBLIC_CAUSAL_NO_PNL_CREDIT'}
            save(s);event('HOURLY_SIGNAL',symbol=sym,boundary=boundary,signal=result['signal'],score=result['score'])
            if not result['signal']:continue
            if not live:
                event('SIGNAL_OBSERVED_TRADING_DISARMED',symbol=sym);continue
            if client is None:raise EngineBlocked('NO_CREDENTIALS')
            b=market.book(sym)
            if b['as_of_ms']-boundary>600000:raise EngineBlocked('LATE_QUOTE')
            prospective_entry(s,sym,boundary,b,market.spec(sym),cfg,client,snap,live)
            snap=account_snapshot(client)
        except Exception as e:
            record_block(s,sym,type(e).__name__+':'+str(e)[:250])
    return {'mode':'LIVE_ARMED' if live else 'OBSERVE_ONLY','positions':len(s['positions']),
            'pending_entries':sum(1 for x in s['entries'].values() if x.get('phase') not in ('DRY_RUN_NO_ORDER','POSITION_OWNED_PROTECTED')),
            'blocked':list(s['blocks']),'utc':utc()}

def status():
    s=ledger();return {'utc':utc(),'authority':'ARMED' if frozen_authority() else 'DISARMED',
                         'kill_switch':KILL.exists(),'owned_positions':{k:{'position_id':v['position_id'],'stop':v['stop'],'contracts':v['contracts']} for k,v in s['positions'].items()},
                         'entries':{k:v['phase'] for k,v in s['entries'].items()},'blocks':s['blocks'],
                         'signal_count':len(s['signals'])}

def arm(client):
    if KILL.exists():raise EngineBlocked('KILL_SWITCH_MUST_BE_RESOLVED_WITH_POSITION_RECONCILIATION')
    cfg=config();s=ledger()
    if s['blocks'] or s['positions'] or any(x.get('phase')!='DRY_RUN_NO_ORDER' for x in s['entries'].values()):
        raise EngineBlocked('LIVE_HANDOVER_REQUIRES_CLEAN_LOCAL_LEDGER')
    snap=account_snapshot(client);assert_clean_account(s,snap)
    if snap['positions'] or snap['orders'] or snap['stops']:raise EngineBlocked('ACCOUNT_MUST_BE_EMPTY_FOR_INITIAL_HANDOVER')
    equity,available=equity_and_available(snap)
    if available<=0:raise EngineBlocked('NO_AVAILABLE_MARGIN')
    for sym in SYMS:
        client.fees(sym) # read-only proof of per-symbol API accessibility
        market.spec(sym);market.book(sym) # fresh public contract & quote
    a={'status':'ARMED','candidate_id':cfg['candidate_id'],'config_sha256':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
       'issued_at':utc(),'operator_confirmed_risk':True,'exchange_readonly_verified':True,
       'independently_live_stop_amend_tested':False}
    atomic(AUTH,a);event('LIVE_AUTHORITY_ARMED_LOCALLY',leverage=cfg['leverage'],equity_readonly=equity)
    return a

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['status','once','run','arm','kill','selftest']);p.add_argument('--interval',type=int,default=30)
    args=p.parse_args()
    if args.command=='status':print(json.dumps(status(),indent=2,ensure_ascii=False));return 0
    if args.command=='kill':KILL.touch();AUTH.unlink(missing_ok=True);event('KILL_NEW_ENTRIES');return 0
    if args.command=='arm':
        print('MEXC LIVE: O sistema enviara ordens de futuros quando aparecer um sinal.')
        print('Alavancagem ate 20x pode levar a liquidacao ANTES do SL. Nao ha garantia de fills.')
        ans=input('Para autorizar escreve exatamente ATIVAR TRADING REAL: ')
        if ans!='ATIVAR TRADING REAL':raise EngineBlocked('OPERATOR_DID_NOT_CONFIRM')
        a=arm(MexcFutures());print(json.dumps({'status':'ARMED','authorized_utc':a['issued_at']}));return 0
    if args.command=='selftest':
        assert market.signal_parent_v5([{'close':100,'vol':1} for _ in range(400)])['signal'] is False
        print('CORE_SELFTEST_PASS');return 0
    # An armed process always keeps its read-only reconciliation and protection management active even during kill.
    acquire_process_lock()
    while True:
        try:
            auth=frozen_authority();local=ledger();has_own=bool(local['positions'])
            has_unresolved_entry=any((it.get('phase') not in ('DRY_RUN_NO_ORDER','POSITION_OWNED_PROTECTED')) and sym not in local['positions']
                                     for sym,it in local['entries'].items())
            if auth or has_own or has_unresolved_entry:
                out=tick(MexcFutures())
            else:out=tick()
            atomic(STATE/'status.json',out);print(json.dumps(out,sort_keys=True),flush=True)
        except Exception as exc:
            # An unknown mutation outcome is never a retry signal. Operator must inspect the durable journal.
            event('SUPERVISOR_HARD_BLOCK',reason=type(exc).__name__+':'+str(exc)[:250])
            KILL.touch();AUTH.unlink(missing_ok=True)
            atomic(STATE/'status.json',{'status':'FAIL_CLOSED','error':str(exc),'utc':utc()})
            return 2
        if args.command=='once':return 0
        time.sleep(max(args.interval,15))

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        event('COMMAND_FAILED',reason=type(e).__name__+':'+str(e)[:350]);sys.exit(2)