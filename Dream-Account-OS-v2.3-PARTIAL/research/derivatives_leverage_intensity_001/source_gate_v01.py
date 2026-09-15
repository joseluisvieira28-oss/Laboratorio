import csv
import hashlib
import io
import json
import math
import time
import urllib.request
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / 'source_evidence'
OUT = OUTDIR / 'DLI_SOURCE_DATA_GATE_V01.json'
START = datetime(2021,1,1,tzinfo=timezone.utc)
END = datetime(2024,12,31,tzinfo=timezone.utc)
EXPECTED_DAYS = 1461
UA = {'User-Agent':'Mozilla/5.0 DLI-BTC-FUTSPOT-TURNOVER-001/1.0'}
BASES = {
    'spot': 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d',
    'futures_um': 'https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d',
}
GUARDS = {
    'ohlc_price_fields_used': False,
    'market_price_values_opened': False,
    'returns_computed': False,
    'pnl_computed': False,
    'performance_statistics_computed': False,
    'ratio_values_persisted_or_inspected': False,
    'year_2025_opened': False,
    'year_2026_opened': False,
    'live_trading': False,
    'exchange_mutation': False,
}

def get(url, attempts=4):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:
            last=e
            time.sleep(0.5*(2**i))
    raise last

def months():
    out=[]
    for y in range(2021,2025):
        for m in range(1,13):
            out.append(f'{y:04d}-{m:02d}')
    return out

def ts_to_dt(raw):
    x=int(raw)
    # Binance historical klines in this frozen window are expected in ms.
    # Accept microseconds defensively by magnitude without changing date semantics.
    if x > 10**14:
        sec=x/1_000_000.0
    elif x > 10**11:
        sec=x/1_000.0
    else:
        sec=float(x)
    return datetime.fromtimestamp(sec, tz=timezone.utc)

def verify_checksum(zip_bytes, checksum_bytes):
    expected=checksum_bytes.decode('utf-8','replace').strip().split()[0].lower()
    actual=hashlib.sha256(zip_bytes).hexdigest().lower()
    ok=(len(expected)==64 and expected==actual)
    return ok, expected, actual

def parse_archive(zip_bytes):
    dates=[]
    volumes=[]
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names=[n for n in z.namelist() if not n.endswith('/')]
        if len(names)!=1:
            raise RuntimeError(f'expected exactly one CSV member, got {len(names)}')
        raw=z.read(names[0]).decode('utf-8-sig','replace')
    reader=csv.reader(io.StringIO(raw))
    for row in reader:
        if not row:
            continue
        # Ignore optional header row only.
        try:
            dt=ts_to_dt(row[0])
        except Exception:
            if str(row[0]).strip().lower() in {'open_time','opentime'}:
                continue
            raise
        if len(row) < 8:
            raise RuntimeError('kline row has fewer than 8 columns')
        qv=float(row[7])
        if not math.isfinite(qv) or qv <= 0:
            raise RuntimeError('non-positive or non-finite quote_asset_volume')
        dates.append(dt.date())
        volumes.append(qv)
    return dates, volumes

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    expected_dates=[]
    d=START.date()
    while d <= END.date():
        expected_dates.append(d)
        d += timedelta(days=1)
    expected_set=set(expected_dates)

    venue_dates={}
    venue_volumes={}
    files=[]
    failures=[]

    for venue,base in BASES.items():
        all_dates=[]; all_vols=[]
        for ym in months():
            zip_url=f'{base}/BTCUSDT-1d-{ym}.zip'
            checksum_url=zip_url+'.CHECKSUM'
            # Hard firewall: generated URLs must remain inside 2021-2024.
            if '/2025-' in zip_url or '/2026-' in zip_url:
                raise RuntimeError('protected-period URL generation attempted')
            try:
                zb=get(zip_url)
                cb=get(checksum_url)
                ok,expected_sha,actual_sha=verify_checksum(zb,cb)
                if not ok:
                    failures.append({'venue':venue,'month':ym,'classification':'PROVENANCE_FAILURE','reason':'CHECKSUM_MISMATCH','expected_sha256':expected_sha,'actual_sha256':actual_sha})
                    continue
                ds,vs=parse_archive(zb)
                all_dates.extend(ds); all_vols.extend(vs)
                files.append({'venue':venue,'month':ym,'zip_sha256':actual_sha,'row_count':len(ds),'checksum_verified':True})
            except Exception as e:
                failures.append({'venue':venue,'month':ym,'classification':'SOURCE_ACCESS_BLOCKED','reason':type(e).__name__+':'+str(e)})
        venue_dates[venue]=all_dates
        venue_volumes[venue]=all_vols

    diagnostics={}
    data_failure=False
    for venue in BASES:
        ds=venue_dates[venue]
        s=set(ds)
        duplicates=len(ds)-len(s)
        missing=sorted(expected_set-s)
        outside=sorted(s-expected_set)
        diagnostics[venue]={
            'row_count':len(ds),
            'unique_day_count':len(s),
            'duplicate_day_count':duplicates,
            'missing_day_count':len(missing),
            'outside_window_day_count':len(outside),
            'first_day':min(s).isoformat() if s else None,
            'last_day':max(s).isoformat() if s else None,
            'all_quote_asset_volume_positive_finite':len(ds)==len(venue_volumes[venue]) and all(math.isfinite(x) and x>0 for x in venue_volumes[venue]),
        }
        if len(ds)!=EXPECTED_DAYS or len(s)!=EXPECTED_DAYS or duplicates!=0 or missing or outside:
            data_failure=True
        if not diagnostics[venue]['all_quote_asset_volume_positive_finite']:
            data_failure=True

    sets_equal=set(venue_dates['spot'])==set(venue_dates['futures_um'])
    ratio_finite_count=0
    if sets_equal and not data_failure and not failures:
        spot=dict(zip(venue_dates['spot'],venue_volumes['spot']))
        fut=dict(zip(venue_dates['futures_um'],venue_volumes['futures_um']))
        for day in expected_dates:
            r=fut[day]/spot[day]
            if math.isfinite(r) and r>0:
                ratio_finite_count += 1
        if ratio_finite_count != EXPECTED_DAYS:
            data_failure=True

    if failures:
        if any(x['classification']=='PROVENANCE_FAILURE' for x in failures):
            classification='PROVENANCE_FAILURE'
        else:
            classification='SOURCE_ACCESS_BLOCKED'
    elif data_failure or not sets_equal:
        classification='DATA_FAILURE'
    else:
        classification='SOURCE_DATA_PASS'

    receipt={
        'lab_id':'DERIVATIVES-LEVERAGE-INTENSITY-001',
        'mve_id':'DLI-BTC-FUTSPOT-TURNOVER-001',
        'mode':'SOURCE_DATA_GATE_ONLY',
        'classification':classification,
        'source_window':{'start':'2021-01-01','end':'2024-12-31','expected_days':EXPECTED_DAYS},
        'expected_archives_total':96,
        'verified_archive_count':sum(1 for x in files if x['checksum_verified']),
        'failed_archive_count':len(failures),
        'venue_diagnostics':diagnostics,
        'identical_utc_date_sets':sets_equal,
        'ratio_finite_count_only':ratio_finite_count,
        'ratio_values_persisted':False,
        'archive_manifest':files,
        'failures':failures,
        'guards':GUARDS,
        'next_action':'If SOURCE_DATA_PASS, STOP and freeze FINAL_PRE_DISCOVERY_PROTOCOL before any market price, future return, PnL, threshold or horizon test.'
    }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['classification','verified_archive_count','failed_archive_count','venue_diagnostics','identical_utc_date_sets','ratio_finite_count_only','guards']},indent=2,sort_keys=True))

    if classification=='SOURCE_ACCESS_BLOCKED':
        raise SystemExit(21)
    if classification=='PROVENANCE_FAILURE':
        raise SystemExit(22)
    if classification=='DATA_FAILURE':
        raise SystemExit(23)

if __name__=='__main__':
    main()
