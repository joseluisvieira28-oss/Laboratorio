"""Independent ZIP auditor. Standard library; never imports collector/replay."""
import gzip,hashlib,json,math,sys,zipfile
from collections import Counter
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
def audit(path):
 with zipfile.ZipFile(path) as z:
  manifest=json.loads(z.read('manifest.json')); claimed=json.loads(z.read('report.json'))
  compressed=z.read('raw.jsonl.gz'); raw=gzip.decompress(compressed)
  assert H(compressed)==manifest['gzip_sha256'],'GZIP_HASH'
  assert H(raw)==manifest['raw_sha256'],'RAW_HASH'
  assert H(z.read('PROTOCOL.md'))==manifest['protocol_sha256'],'PROTOCOL_HASH'
  assert H(z.read('source.py'))==manifest['code_sha256'],'CODE_HASH'
  state={v:dict(ack=False,pong=-1e12,book=-1e12,version=None,payload=None) for v in ('bybit','mexc')}
  counts=Counter(); quarantine=0; tick=1; good=[]; bad=[]; previous=None; first=None; seen=set(); liq=[]; trades=[]; cooldown=-1; episodes=[]; raw_burst_frame_windows=0; contract=None; disconnects=[]; segments=[]; ping={v:[] for v in state}; invalids=[]; stale_windows=[]; last_book_receipt={}; book_gaps={v:[] for v in state}
  def clear(t,reason):
   nonlocal quarantine
   quarantine=t+30; liq.clear(); trades.clear(); counts['reset:'+reason]+=1
   for s in state.values(): s['book']=-1e12
  def healthy(t): return t>=quarantine and all(s['ack'] and 0<=t-s['book']<=1 and 0<=t-s['pong']<=35 for s in state.values())
  def grid(t):
   stale=[v for v,s in state.items() if s['book']>-1e11 and t-s['book']>1]
   if stale: stale_windows.append({'second':t,'venues':stale}); clear(t,'STALE_BOOK')
   (good if healthy(t) else bad).append(t)
  def number(x):
   value=float(x)
   if value<=0 or not math.isfinite(value): raise ValueError('nonpositive/nonfinite')
   return value
  def stamp(x,r):
   if not r['utc_ms']-1500<=float(x)<=r['utc_ms']+250: raise ValueError('SOURCE_CLOCK')
  for index,line in enumerate(raw.splitlines(),1):
   r=json.loads(line); t=r['elapsed']; v=r['venue']; k=r['kind']; s=state.get(v)
   assert r['seq']==index,'RECEIPT_SEQUENCE'
   if first is None: first=r
   assert abs((r['mono_ns']-first['mono_ns'])/1e9-(t-first['elapsed']))<1e-6,'ELAPSED_CLOCK_MISMATCH'
   if previous:
    assert r['mono_ns']>=previous['mono_ns'],'MONOTONIC_REVERSE'
    if r['utc_ms']<previous['utc_ms'] or abs((r['utc_ms']-previous['utc_ms'])-(r['mono_ns']-previous['mono_ns'])/1e6)>250:
     counts['integrity']+=1; clear(t,'CLOCK_SEQUENCE')
   previous=r
   while tick<t: grid(tick); tick+=1
   try:
    if k=='start':
     metadata=json.loads(r['raw']); assert metadata['code_sha256']==manifest['code_sha256']; assert metadata['protocol_sha256']==manifest['protocol_sha256']
    elif k=='contract':
     m=json.loads(r['raw']); d=m['data']; d=next(x for x in d if x['symbol']=='BTC_USDT') if isinstance(d,list) else d
     if m['success'] is not True or d['symbol']!='BTC_USDT': raise ValueError('CONTRACT')
     contract=number(d['contractSize'])
    elif k=='connect':
     segments.append({'venue':v,'segment':r['segment'],'elapsed':t}); s.update(ack=False,pong=-1e12,book=-1e12,version=None,payload=None); clear(t,'CONNECT')
    elif k=='ping': ping[v].append(t)
    elif k in ('disconnect','fault'):
     if s: s.update(ack=False,book=-1e12)
     clear(t,k); counts[v+':'+k]+=1
     disconnects.append({'venue':v,'elapsed':t,'segment':r['segment'],'raw':r['raw']})
    elif k=='frame':
     counts[v+':frames']+=1; m=json.loads(r['raw'])
     if m.get('success') is False or (m.get('channel','').startswith('rs.') and m.get('data') not in (0,'0','success')): raise ValueError('SUB_REJECT')
     if v=='mexc' and m.get('channel')=='rs.sub.depth.full' and m.get('data') in (0,'0','success'): s['ack']=True
     if v=='bybit' and m.get('op')=='subscribe' and m.get('success') is True: s['ack']=True
     if (v=='mexc' and m.get('channel')=='pong') or (v=='bybit' and (m.get('op')=='pong' or m.get('ret_msg')=='pong')): s['pong']=t; counts[v+':pong']+=1
     topic=m.get('topic','')
     if (v=='mexc' and m.get('channel')=='push.depth.full') or (v=='bybit' and topic=='orderbook.1.BTCUSDT'):
      if v in last_book_receipt: book_gaps[v].append(t-last_book_receipt[v])
      last_book_receipt[v]=t
      stamp(m['ts'],r); d=m['data']; bybit=v=='bybit'
      if bybit and (m['type']!='snapshot' or d['s']!='BTCUSDT'): raise ValueError('BYBIT_SNAPSHOT_SYMBOL')
      if not bybit and m['symbol']!='BTC_USDT': raise ValueError('MEXC_SYMBOL')
      best=[]
      for key,descending in zip(('b','a') if bybit else ('bids','asks'),(True,False)):
       levels=d[key]
       if len(levels)<(1 if bybit else 5): raise ValueError('SHORT_BOOK')
       prices=[number(x[0]) for x in levels]
       for x in levels: number(x[1])
       if prices!=sorted(set(prices),reverse=descending): raise ValueError('UNSORTED')
       best.append(prices[0])
      if best[0]>=best[1]: raise ValueError('CROSSED')
      version=int(d['u' if bybit else 'version']); payload=json.dumps(d,sort_keys=True)
      if version==s['version'] and payload==s['payload']: counts[v+':duplicate_book']+=1
      else:
       if s['version'] is not None and version<=s['version']: raise ValueError('VERSION_REGRESSION_CONFLICT')
       s.update(book=t,version=version,payload=payload); counts[v+':book']+=1
     if v=='bybit' and topic in ('allLiquidation.BTCUSDT','publicTrade.BTCUSDT'):
      isliq=topic.startswith('allLiquidation')
      for d in m['data']:
       stamp(d['T'],r)
       if d['s']!='BTCUSDT' or d['S'] not in ('Buy','Sell'): raise ValueError('EVENT_SYMBOL_SIDE')
       value=number(d['p'])*number(d['v']); key=('liq',d['T'],d['s'],d['S'],d['v'],d['p']) if isliq else ('trade',d['i'])
       if key in seen: counts['duplicates']+=1; continue
       seen.add(key); counts['liquidations' if isliq else 'trades']+=1; (liq if isliq else trades).append((t,d['S'],value))
     if v=='bybit':
      liq[:]=[x for x in liq if 0<=t-x[0]<=10]; trades[:]=[x for x in trades if 0<=t-x[0]<=1]
      if any(len([x for x in liq if x[1]==side])>=2 and sum(x[2] for x in liq if x[1]==side)>=100000 for side in ('Buy','Sell')): raw_burst_frame_windows+=1
      if t>=cooldown:
       for side in ('Buy','Sell'):
        events=[x for x in liq if x[1]==side]
        if len(events)<2 or sum(x[2] for x in events)<100000: continue
        flow=sum(x[2] for x in trades if x[1]==side)>=10000
        qualified=bool(flow and 120000<=r['utc_ms']%28800000<=28680000 and healthy(t) and contract)
        episodes.append({'elapsed':t,'utc_ms':r['utc_ms'],'side':side,'children':len(events),'notional_proxy':sum(x[2] for x in events),'flow':flow,'joint_good':healthy(t),'qualified':qualified}); cooldown=t+120; break
   except (ValueError,TypeError,KeyError,IndexError,OverflowError) as e:
    invalids.append({'seq':index,'venue':v,'elapsed':t,'reason':str(e)}); counts['invalid:'+str(e)]+=1; clear(t,'INVALID')
   if tick==t: grid(tick); tick+=1
  assert index==manifest['receipt_rows'],'ROW_COUNT'
  assert r['kind']=='end','MISSING_END'
  goodset=set(good); n=len(good)+len(bad); minutes=sum(sum(x in goodset for x in range(m*60+1,m*60+61))>=57 for m in range(n//60))
  intervals=[]
  for x in bad:
   if intervals and intervals[-1][1]==x-1: intervals[-1][1]=x
   else: intervals.append([x,x])
  for key,value in [('seconds',n),('joint_good_seconds',len(good)),('good_full_minutes',minutes),('bad_second_intervals',intervals),('counts',dict(counts)),('episodes',episodes),('contract_size',contract)]: assert claimed[key]==value, 'REPORT_MISMATCH:'+key
  passed=n>=7200 and len(good)/max(n,1)>=.95 and minutes>=100 and not counts['integrity'] and r['raw']=='WALL_LIMIT' and sum(counts[v+':disconnect'] for v in state)<=8 and counts['liquidations']>=1
  verdict='SOURCE_PASS_LIMITED' if passed else 'SOURCE_BLOCKED'; assert claimed['source_verdict']==verdict
  return {'audit':'VERIFIED_INDEPENDENT_RECONSTRUCTION','zip_sha256':H(Path(path).read_bytes()),'manifest':manifest,'source_verdict':verdict,'seconds':n,'start_utc_ms':first['utc_ms'],'end_utc_ms':r['utc_ms'],'recorded_wall_seconds':r['elapsed']-first['elapsed'],'joint_good_seconds':len(good),'joint_coverage':len(good)/max(n,1),'good_full_minutes':minutes,'bad_second_intervals':intervals,'counts':dict(counts),'episodes':episodes,'raw_burst_frame_windows':raw_burst_frame_windows,'raw_burst_window_definition':'Overlapping qualifying trailing-10s liquidation windows evaluated on each Bybit frame; not independent episodes or trades','segments':segments,'interruptions':disconnects,'invalid_frames':invalids,'stale_windows':stale_windows,'book_receive_gaps':{v:{'maximum_seconds':max(x,default=None),'over_1s':sum(g>1 for g in x),'over_3s':sum(g>3 for g in x)} for v,x in book_gaps.items()},'ping_count':{v:len(x) for v,x in ping.items()},'max_ping_interval':{v:max((b-a for a,b in zip(x,x[1:])),default=None) for v,x in ping.items()},'economic_verdict':'ECONOMIC_INSUFFICIENT','live_verdict':'NO_LIVE_GO','pnl':'NOT_COMPUTED_GATE_CLOSED'}
if __name__=='__main__':
 result=audit(Path(sys.argv[1])); output=Path(sys.argv[2]); output.write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
