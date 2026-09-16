import hashlib
import io
import json
import re
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FREEZE = ROOT / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_HOLDOUT_FREEZE_V0.1.json'
SOURCE = HERE / 'source_gate_v01' / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_GATE_V0.1.json'
OUTDIR = HERE / 'market_source_v01'
RAW = OUTDIR / 'raw'
OUT = OUTDIR / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_MARKET_SOURCE_V0.1.json'
BASE = 'https://data.binance.vision/data/spot/monthly/klines/BNBBTC/15m'
UA = {'User-Agent': 'Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-FINAL-PRESAMPLE-MARKET-SOURCE/1.0'}


def get(url, tries=6):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(min(15.0, 0.75 * (2 ** i)))
    raise last


def parse_checksum(raw, name):
    p = raw.decode('utf-8', 'replace').strip().split()
    dg = p[0].lower()
    if len(dg) != 64 or any(c not in '0123456789abcdef' for c in dg):
        raise RuntimeError('MALFORMED_CHECKSUM')
    if len(p) > 1 and p[-1].lstrip('*') != name:
        raise RuntimeError('CHECKSUM_FILENAME_MISMATCH')
    return dg


def parse_epoch(b):
    s = b.decode('ascii', 'strict').strip()
    if not re.fullmatch(r'\d{10,18}', s):
        return None
    x = int(s)
    sec = x / 1_000_000.0 if x > 10**14 else x / 1_000.0 if x > 10**11 else float(x)
    return int(round(sec))


def iso(sec):
    return datetime.fromtimestamp(sec, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def ym(sec):
    return datetime.fromtimestamp(sec, tz=timezone.utc).strftime('%Y-%m')


def ceil_next_15m(dt):
    # Strictly greater than publication timestamp, exactly as frozen.
    return ((int(dt.timestamp()) // 900) + 1) * 900


def selected_paths(events):
    ev = []
    for e in events:
        dt = datetime.fromisoformat(e['published_timestamp_utc'].replace('Z', '+00:00')).astimezone(timezone.utc)
        ev.append({'n': e['n'], 'symbol': e['symbol'], 'dt': dt, 'published': e['published_timestamp_utc']})
    ev.sort(key=lambda x: (x['dt'], x['n']))

    clusters = []
    for e in ev:
        if not clusters or (e['dt'] - clusters[-1][-1]['dt']).total_seconds() > 3600:
            clusters.append([e])
        else:
            clusters[-1].append(e)

    candidates = []
    for c in clusters:
        signal = c[0]
        ent = ceil_next_15m(signal['dt'])
        ex = ent + 86400
        candidates.append({
            'project_numbers': [x['n'] for x in c],
            'symbols': [x['symbol'] for x in c],
            'signal_time_utc': signal['published'],
            'entry_epoch': ent,
            'exit_epoch': ex,
            'entry_time_utc': iso(ent),
            'exit_time_utc': iso(ex),
        })

    selected = []
    suppressed = []
    active_exit = None
    for c in candidates:
        if active_exit is not None and c['entry_epoch'] < active_exit:
            suppressed.append(c)
            continue
        selected.append(c)
        active_exit = c['exit_epoch']
    return clusters, candidates, selected, suppressed


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    f = json.loads(FREEZE.read_text(encoding='utf-8'))
    s = json.loads(SOURCE.read_text(encoding='utf-8'))
    assert f['status'] == 'FROZEN_BEFORE_PRESAMPLE_SOURCE_ENUMERATION_OR_MARKET_OUTCOME_ACCESS'
    assert s['classification'] == 'SOURCE_DATA_PASS'
    assert s['recovered_count'] == 30
    assert s['missing_project_numbers'] == []
    assert s['market_prices_opened'] is False
    assert f['execution_rule_unchanged']['pair'] == 'BNBBTC SPOT'
    assert f['execution_rule_unchanged']['interval'] == '15m'

    clusters, candidates, selected, suppressed = selected_paths(s['canonical_events'])
    required_months = sorted(set(ym(x[t]) for x in selected for t in ('entry_epoch', 'exit_epoch')))
    if not required_months:
        raise RuntimeError('NO_REQUIRED_MONTHS')
    if any(m >= '2023-01' for m in required_months):
        raise RuntimeError('FORBIDDEN_POST_PRESAMPLE_MONTH')
    if any(m.startswith('2025-') or m.startswith('2026-') for m in required_months):
        raise RuntimeError('FORBIDDEN_2025_OR_2026_MONTH')

    manifest = []
    all_ts = []
    failures = []
    for month in required_months:
        name = f'BNBBTC-15m-{month}.zip'
        url = f'{BASE}/{name}'
        try:
            cb = get(url + '.CHECKSUM')
            official = parse_checksum(cb, name)
            zb = get(url)
            calc = hashlib.sha256(zb).hexdigest()
            if calc != official:
                raise RuntimeError('SHA256_MISMATCH')
            (RAW / name).write_bytes(zb)
            (RAW / (name + '.CHECKSUM')).write_bytes(cb)
            with zipfile.ZipFile(io.BytesIO(zb)) as z:
                bad = z.testzip()
                if bad is not None:
                    raise RuntimeError(f'ZIP_CRC_FAILURE:{bad}')
                members = [n for n in z.namelist() if not n.endswith('/')]
                if len(members) != 1:
                    raise RuntimeError('ZIP_MEMBER_COUNT_NOT_ONE')
                ts = []
                with z.open(members[0]) as fh:
                    for line in fh:
                        if not line.strip():
                            continue
                        sec = parse_epoch(line.split(b',', 1)[0])
                        if sec is not None:
                            ts.append(sec)
                if not ts:
                    raise RuntimeError('NO_TIMESTAMPS')
                if len(ts) != len(set(ts)):
                    raise RuntimeError('DUPLICATE_TIMESTAMP_WITHIN_MONTH')
                all_ts.extend(ts)
                manifest.append({
                    'month': month,
                    'archive': name,
                    'sha256': calc,
                    'timestamp_rows': len(ts),
                    'first_timestamp_utc': iso(min(ts)),
                    'last_timestamp_utc': iso(max(ts)),
                })
        except Exception as ex:
            failures.append({'month': month, 'error': f'{type(ex).__name__}:{ex}'})

    aset = set(all_ts)
    global_dupes = len(all_ts) - len(aset)
    path_fail = []
    for x in selected:
        req = list(range(x['entry_epoch'], x['exit_epoch'] + 1, 900))
        miss = [t for t in req if t not in aset]
        if miss:
            path_fail.append({
                'project_numbers': x['project_numbers'],
                'missing_count': len(miss),
                'first_missing_utc': iso(miss[0]),
            })

    ok = (
        len(manifest) == len(required_months)
        and not failures
        and global_dupes == 0
        and not path_fail
        and len(selected) >= f['path2_gates_all_required']['minimum_resolved_trades']
    )
    basis = ('\n'.join(
        f"{x['month']}|{x['sha256']}|{x['timestamp_rows']}|{x['first_timestamp_utc']}|{x['last_timestamp_utc']}"
        for x in manifest
    ) + '\n').encode('utf-8')
    strip = lambda x: {k: v for k, v in x.items() if not k.endswith('_epoch')}

    receipt = {
        'protocol_id': f['protocol_id'],
        'source_event_manifest_sha256': s['canonical_event_manifest_sha256'],
        'classification': 'MARKET_SOURCE_DATA_PASS' if ok else 'SOURCE_OR_EXECUTION_FAILURE',
        'required_months': required_months,
        'archive_count': len(manifest),
        'expected_archive_count': len(required_months),
        'archive_manifest_sha256': hashlib.sha256(basis).hexdigest(),
        'archive_manifest': manifest,
        'technical_failures': failures,
        'global_duplicate_timestamp_count': global_dupes,
        'project_events': len(s['canonical_events']),
        'event_clusters': len(clusters),
        'candidate_clusters': len(candidates),
        'selected_trade_paths': len(selected),
        'suppressed_trade_paths': len(suppressed),
        'selected': [strip(x) for x in selected],
        'suppressed': [strip(x) for x in suppressed],
        'execution_path_failures': path_fail,
        'market_price_values_opened': False,
        'open_parsed': False,
        'high_low_close_volume_parsed': False,
        'returns_computed': False,
        'new_2025_market_access': False,
        'access_2026_market': False,
        'live_trading_authorized': False,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        k: receipt[k] for k in [
            'classification', 'archive_count', 'event_clusters', 'selected_trade_paths',
            'suppressed_trade_paths', 'archive_manifest_sha256'
        ]
    }, indent=2))


if __name__ == '__main__':
    main()
