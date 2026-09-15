import csv, hashlib, io, json, math, sys, time, urllib.request, zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source_gate_evidence/full_static_latest/TUE_FULL_STATIC_BINANCE_ROUTE_GATE_V01.json'
PROTOCOL=HERE/'FINAL_PRE_DISCOVERY_PROTOCOL_V01.json'
OUT=HERE/'signal_evidence/TUE_UNLOCK_PRESSURE_CALIBRATION_V01.json'
BASE='https://data.binance.vision/data/spot/daily/klines'
Q=0.67


def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha256(b): return hashlib.sha256(b).hexdigest()

def quantile_linear(xs,q):
    xs=sorted(xs); pos=(len(xs)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:return xs[lo]
    return xs[lo]+(xs[hi]-xs[lo])*(pos-lo)

def fetch(url, attempts=4):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'TOKEN-UNLOCK-EVENT-001-signal-calibration/1.0'})
            with urllib.request.urlopen(req,timeout=30) as r:return r.read()
        except Exception as e:
            last=e; time.sleep(0.4*(2**i))
    raise last

def daily_urls(sym,d):
    pair=f'{sym}USDT'; ds=d.isoformat(); root=f'{BASE}/{pair}/1d/{pair}-1d-{ds}.zip'
    return root, root+'.CHECKSUM'

def load_daily_volume(key):
    sym,d=key; zip_url, chk_url=daily_urls(sym,d)
    chk=fetch(chk_url).decode('utf-8','replace').strip().split()[0].lower()
    if len(chk)!=64: raise RuntimeError(f'bad checksum metadata {sym} {d}')
    raw=fetch(zip_url)
    if sha256(raw)!=chk: raise RuntimeError(f'checksum mismatch {sym} {d}')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if len(names)!=1: raise RuntimeError(f'unexpected zip members {sym} {d}')
        text=z.read(names[0]).decode('utf-8')
    rows=list(csv.reader(io.StringIO(text)))
    if len(rows)!=1: raise RuntimeError(f'expected one daily row {sym} {d}, got {len(rows)}')
    row=rows[0]
    if len(row)<6: raise RuntimeError('bad kline row')
    ts=int(row[0]); dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc).date()
    if dt!=d: raise RuntimeError(f'date mismatch {sym} expected {d} got {dt}')
    vol=float(row[5])
    if not math.isfinite(vol) or vol<=0: raise RuntimeError(f'nonpositive volume {sym} {d}')
    return {'symbol':sym,'date':d.isoformat(),'volume':vol,'archive_sha256':chk}

def composite_events(qualified):
    groups=defaultdict(list)
    for e in qualified:
        dt=datetime.fromisoformat(str(e['scheduled_at_utc']).replace('Z','+00:00')).astimezone(timezone.utc)
        groups[(str(e['symbol']),dt.date())].append((dt,e))
    out=[]
    for (sym,day), items in sorted(groups.items(), key=lambda x:(x[0][1],x[0][0])):
        amount=sum(float(e['scheduled_unlock_tokens']) for _,e in items)
        anchor=min(dt for dt,_ in items)
        out.append({'symbol':sym,'event_date':day.isoformat(),'anchor_timestamp_utc':anchor.isoformat().replace('+00:00','Z'),'composite_unlock_tokens':amount,'constituent_count':len(items)})
    return out

def main():
    src=load(SOURCE); protocol=load(PROTOCOL)
    r=src['receipt']
    assert r['classification']=='SOURCE_DATA_FEASIBLE'
    assert protocol['status']=='FROZEN_PRE_DISCOVERY_OUTCOME_BLIND'
    comps=composite_events(src['qualified_events'])
    needed=set()
    for c in comps:
        ed=date.fromisoformat(c['event_date']); entry=ed-timedelta(days=7)
        c['entry_day']=entry.isoformat()
        c['signal_window_start']=(entry-timedelta(days=30)).isoformat()
        c['signal_window_end']=(entry-timedelta(days=1)).isoformat()
        for i in range(30):
            d=entry-timedelta(days=30-i)
            if d.year>=2025: raise RuntimeError('2025 signal firewall breach')
            needed.add((c['symbol'],d))
    cache={}; failures={}
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs={ex.submit(load_daily_volume,k):k for k in sorted(needed,key=lambda x:(x[0],x[1]))}
        for fut in as_completed(futs):
            k=futs[fut]
            try: cache[k]=fut.result()
            except Exception as e: failures[k]=f'{type(e).__name__}:{e}'
    resolved=[]; excluded=[]
    for c in comps:
        entry=date.fromisoformat(c['entry_day']); keys=[(c['symbol'],entry-timedelta(days=30-i)) for i in range(30)]
        missing=[k for k in keys if k not in cache]
        if missing:
            excluded.append({**c,'reason':'PRE_ENTRY_30D_VOLUME_DATA_INCOMPLETE','missing_days':[d.isoformat() for _,d in missing]}); continue
        vols=[cache[k]['volume'] for k in keys]; avg=sum(vols)/30.0
        p=c['composite_unlock_tokens']/avg
        resolved.append({**c,'trailing_30d_average_daily_base_volume':avg,'unlock_pressure_days':p,'log1p_unlock_pressure':math.log1p(p),'volume_archive_sha256s':[cache[k]['archive_sha256'] for k in keys]})
    tokens=sorted({x['symbol'] for x in resolved}); years=sorted({int(x['event_date'][:4]) for x in resolved})
    if len(resolved)<100 or len(tokens)<15 or len(years)<2:
        classification='INSUFFICIENT_SAMPLE'; threshold=None; high=[]
    else:
        threshold=quantile_linear([x['unlock_pressure_days'] for x in resolved],Q)
        high=[x for x in resolved if x['unlock_pressure_days']>=threshold]
        ht=sorted({x['symbol'] for x in high})
        classification='SIGNAL_CALIBRATION_PASS' if len(high)>=40 and len(ht)>=10 else 'INSUFFICIENT_SAMPLE'
    receipt={
      'lab_id':'TOKEN-UNLOCK-EVENT-001','mve_id':'TUE-CLIFF-ADV30-001','mode':'SIGNAL_ONLY_CAUSAL_CALIBRATION_V01','classification':classification,
      'source_route_qualified_events':len(src['qualified_events']),'composite_events':len(comps),'signal_resolved_events':len(resolved),'signal_resolved_tokens':len(tokens),'signal_resolved_years':years,
      'excluded_signal_events':len(excluded),'unique_daily_archives_requested':len(needed),'daily_archive_failures':len(failures),'high_pressure_quantile':Q,
      'frozen_high_pressure_threshold_unlock_pressure_days':threshold,'high_pressure_events':len(high),'high_pressure_tokens':len({x['symbol'] for x in high}),
      'source_gate_identity_manifest_fingerprint_sha256':r['identity_manifest_fingerprint_sha256'],
      'protocol_sha256':sha256(PROTOCOL.read_bytes()),
      'guards':{'only_pre_entry_rows_accessed':True,'latest_signal_row_relative_to_entry_days':-1,'forward_event_window_prices_accessed':False,'returns_computed':False,'pnl_computed':False,'profit_factor_computed':False,'year_2025_opened':False,'year_2026_opened':False,'live_trading':False,'exchange_mutation':False},
      'next_action':'If SIGNAL_CALIBRATION_PASS, persist this numeric threshold immutably before any forward outcome access; otherwise stop.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'receipt':receipt,'signals':resolved,'excluded':excluded,'download_failures':{f'{s}|{d.isoformat()}':v for (s,d),v in failures.items()}},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    print('PRE-ENTRY VOLUME ONLY / NO FORWARD PRICES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
    return 0 if classification=='SIGNAL_CALIBRATION_PASS' else 4

if __name__=='__main__': sys.exit(main())
