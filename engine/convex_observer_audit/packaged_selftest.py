"""Packaged runtime smoke with positive parent signals. No network/credentials."""
import json
import tempfile
from engine.three_convex_v05.signals import Bar,Halt,MS5,closed_signal_decisions
from engine.three_convex_v11.experimental import experimental_signals

def run(version,queue_class):
    lanes=(('SOL_CONVEX_NATIVE_5M','SOL_USDT',1),('SOL_CONVEX_1H','SOL_USDT',12),('BNB_CONVEX_4H','BNB_USDT',48)) if version=='V07' else (('SOL_CONVEX_4H_EXPERIMENTAL','SOL_USDT',48),('BNB_CONVEX_30M_EXPERIMENTAL','BNB_USDT',6),('ETH_CONVEX_1H_EXPERIMENTAL','ETH_USDT',12))
    checked=[]
    for lane,symbol,n in lanes:
        bars=[]
        for i in range(260):
            price=100+i*.2 if i<230 else (160 if i<259 else 150)
            volume=1000 if i==259 else 10
            bars.extend(Bar((i*n+j)*MS5,price,price+1,price-1,price,volume) for j in range(n))
        close=260*n*MS5
        def compute(now):
            return closed_signal_decisions(symbol,bars,now) if version=='V07' else experimental_signals(symbol,bars,now,0)
        try:compute(close)
        except Halt:pass
        else:raise RuntimeError('OPEN_CANDLE_ACCEPTED')
        signal=next(s for s in compute(close+2000) if s['lane']==lane)
        with tempfile.TemporaryDirectory() as d:
            box=queue_class(d)
            sent=[]
            def fake_send(message):sent.append(message);return 123456
            if version=='V07':
                event=dict(kind='V5_SIGNAL_NOT_ORDER',lane=lane,symbol=symbol,close_utc='SYNTHETIC UTC',signal_id=signal['signal_id'])
                box.enqueue('SIGNAL:'+signal['signal_id'],event,close+2000)
                box.enqueue('SIGNAL:'+signal['signal_id'],event,close+2000)
                class Bot:send=staticmethod(fake_send)
                box.drain(Bot(),close+2000);box.drain(Bot(),close+2000)
            else:
                box.queue(signal);box.queue(signal)
                box.flush(fake_send,close+2000);box.flush(fake_send,close+2000)
            box.db.close()
            if len(sent)!=1 or 'NÃO É ORDEM' not in sent[0]:raise RuntimeError('OUTBOX_OR_MESSAGE_FAILED')
        checked.append(lane)
    result={'status':'OFFLINE_PACKAGED_SELFTEST_PASS','version':version,'lanes':checked,'real_telegram_sends':0,'exchange_requests':0,'secrets_used':False}
    print(json.dumps(result,sort_keys=True));return 0
