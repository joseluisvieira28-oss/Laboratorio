"""Convex three-symbol integration draft for the EXISTING Crypto Lab Radar.
Default SIMULATED. This module is not authority to enable trading.
Machine states are durable, and failed/ambiguous network responses never re-send orders.
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from dataclasses import asdict
from pathlib import Path
from convex_core import (SYMBOLS, TrailPosition, initial_position, evaluate_closed_bar, size_for_risk)
from mexc_futures import MexcFutures, ExchangeError

ROOT=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'CryptoLab' / 'ConvexRadar'
STATE=ROOT/'state'; STATE.mkdir(parents=True,exist_ok=True)
LEDGER=STATE/'execution_ledger.json'
# This proof implementation does not have an authenticated, verified stop revision receipt yet.
# Explicitly fail closed before creating any real order; this invariant cannot be overridden
# by a config.json flag or an armed marker.
PRODUCTION_ORDER_TRANSPORT_CERTIFIED=False


def atomic(path, obj):
    tmp=path.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,sort_keys=True); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)


def load():
    if not LEDGER.exists():return {'format':1,'mode':'NOT_LIVE','signals':{},'positions':{},'alerts':[]}
    v=json.loads(LEDGER.read_text(encoding='utf-8'))
    if not isinstance(v,dict):raise RuntimeError('INVALID_PERSISTED_LEDGER')
    return v


def register_signal(ledger, symbol, utc_boundary, is_signal):
    if symbol not in SYMBOLS:raise ValueError('SYMBOL_NOT_ALLOWED')
    key=f'{symbol}:{utc_boundary}'
    if key in ledger['signals']:return False
    # Persist identity BEFORE any would-be order submission.
    ledger['signals'][key]={'signal':bool(is_signal),'status':'RESEARCH_CAPTURED_NOT_DISPATCHED'}
    atomic(LEDGER,ledger)
    return True


def verified_order_authority():
    """Fails closed until signed-off, real broker stop-install/revise/reconnect cycle verified.
    Enabling this requires code review/new release, not merely editing a text file.
    """
    return PRODUCTION_ORDER_TRANSPORT_CERTIFIED


def status():
    v=load()
    return {'status':'MEXC_CONVEX_INTEGRATION_BUILD__LIVE_BLOCKED',
            'max_leverage_designed':20,'symbols':SYMBOLS,
            'real_order_authority':verified_order_authority(),
            'signal_identities':len(v['signals']), 'owned_positions':len(v['positions'])}


def snapshot_read_only(client):
    ps=client.positions(); orders=client.orders(); stops=client.stops(); assets=client.assets()
    if not all(isinstance(x,list) for x in (ps,orders,stops,assets)):
        raise RuntimeError('ACCOUNT_SHAPE_MISSING')
    return {'positions':ps,'orders':orders,'stops':stops,'asset_currencies':[str(r.get('currency')) for r in assets]}


def safety_gate(preview, ledger):
    owned_ids={int(x['position_id']) for x in ledger['positions'].values()}
    foreign=[p for p in preview['positions'] if int(p.get('positionId',0)) not in owned_ids]
    if foreign:raise RuntimeError('FOREIGN_OPEN_POSITION__PRESERVE_EXISTING_OWNER')
    if preview['orders']:raise RuntimeError('UNKNOWN_OPEN_ORDERS__PRESERVE_EXISTING_OWNER')
    if any(int(p.get('positionId',0)) in owned_ids for p in preview['positions']):
        if not preview['stops']:raise RuntimeError('OWNED_POSITION_WITHOUT_EXCHANGE_STOP')
    return True


def watch_once():
    """Read existing watcher evidence. No credentials, no order side effects."""
    data=STATE/'signal_events.jsonl'
    if not data.exists():return status()
    ledger=load()
    # The small local file never backfills trading eligibility; only persists observation identities.
    for line in data.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        row=json.loads(line)
        if row.get('symbol') in SYMBOLS and 'utc' in row:
            register_signal(ledger,row['symbol'],row['utc'],row.get('signal',False))
    return status()


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['status','capture','account-snapshot'])
    args=p.parse_args()
    if args.action=='status':out=status()
    elif args.action=='capture':out=watch_once()
    else:
        client=MexcFutures()
        snap=snapshot_read_only(client)
        safety_gate(snap,load())
        out={'status':'ACCOUNT_READONLY_CLEAN__NOT_LIVE',
             'positions':len(snap['positions']),'orders':len(snap['orders']),
             'tpsl':len(snap['stops']),'real_order_authority':False}
    print(json.dumps(out,indent=2,default=str))
if __name__=='__main__':main()