import csv
import hashlib
import io
import json
import math
import random
import time
import urllib.request
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / 'FINAL_PRE_DISCOVERY_PROTOCOL_V01.json'
SOURCE_RECEIPT_PATH = HERE / 'source_evidence' / 'DLI_SOURCE_DATA_GATE_V01.json'
OUTDIR = HERE / 'discovery_evidence'
OUT = OUTDIR / 'DLI_DISCOVERY_RESULT_V01.json'
START = datetime(2021, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 12, 31, tzinfo=timezone.utc)
UA = {'User-Agent': 'Mozilla/5.0 DLI-BTC-FUTSPOT-TURNOVER-001-DISCOVERY/1.0'}
BASES = {
    'spot': 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d',
    'futures_um': 'https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d',
}
GUARDS = {
    'market_price_values_opened': True,
    'price_fields_used': ['spot_high', 'spot_low'],
    'close_to_close_returns_computed': False,
    'directional_returns_computed': False,
    'pnl_computed': False,
    'transaction_costs_applied': False,
    'strategy_performance_backtest': False,
    'year_2025_opened': False,
    'year_2026_opened': False,
    'live_trading': False,
    'exchange_mutation': False,
    'orders': False,
    'alerts_or_webhooks': False,
}


def get(url, attempts=4):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(0.5 * (2 ** i))
    raise last


def months():
    return [f'{y:04d}-{m:02d}' for y in range(2021, 2025) for m in range(1, 13)]


def ts_to_date(raw):
    x = int(raw)
    if x > 10**14:
        sec = x / 1_000_000.0
    elif x > 10**11:
        sec = x / 1_000.0
    else:
        sec = float(x)
    return datetime.fromtimestamp(sec, tz=timezone.utc).date()


def parse_archive(zip_bytes, venue):
    rows = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = [n for n in z.namelist() if not n.endswith('/')]
        if len(names) != 1:
            raise RuntimeError(f'{venue}: expected exactly one CSV member, got {len(names)}')
        raw = z.read(names[0]).decode('utf-8-sig', 'replace')
    for row in csv.reader(io.StringIO(raw)):
        if not row:
            continue
        try:
            d = ts_to_date(row[0])
        except Exception:
            if str(row[0]).strip().lower() in {'open_time', 'opentime'}:
                continue
            raise
        if len(row) < 8:
            raise RuntimeError(f'{venue}: row has fewer than 8 columns')
        qv = float(row[7])
        if not math.isfinite(qv) or qv <= 0:
            raise RuntimeError(f'{venue}: invalid quote_asset_volume')
        rec = {'date': d, 'qv': qv}
        if venue == 'spot':
            high = float(row[2]); low = float(row[3])
            if not (math.isfinite(high) and math.isfinite(low) and high > 0 and low > 0 and high >= low):
                raise RuntimeError('spot: invalid high/low')
            rec['high'] = high; rec['low'] = low
        rows.append(rec)
    return rows


def expected_dates():
    out = []
    d = START.date()
    while d <= END.date():
        out.append(d)
        d += timedelta(days=1)
    return out


def hac_ols(y, X, lags=7):
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    S = np.zeros((k, k), dtype=float)
    for t in range(n):
        xt = X[t:t+1].T
        S += (resid[t] ** 2) * (xt @ xt.T)
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        for t in range(lag, n):
            xt = X[t:t+1].T
            xl = X[t-lag:t-lag+1].T
            S += w * resid[t] * resid[t-lag] * (xt @ xl.T + xl @ xt.T)
    cov = xtx_inv @ S @ xtx_inv
    if n > k:
        cov *= n / (n - k)
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    return beta, se


def moving_block_bootstrap(values, events, block_len, reps, seed):
    rng = random.Random(seed)
    n = len(values)
    starts = list(range(0, n - block_len + 1))
    diffs = []
    for _ in range(reps):
        idx = []
        while len(idx) < n:
            s = rng.choice(starts)
            idx.extend(range(s, min(s + block_len, n)))
        idx = idx[:n]
        ev = [values[i] for i in idx if events[i] == 1]
        ct = [values[i] for i in idx if events[i] == 0]
        if not ev or not ct:
            continue
        diffs.append(float(np.mean(ev) - np.mean(ct)))
    if len(diffs) < int(reps * 0.99):
        raise RuntimeError('bootstrap produced too many invalid replicates')
    diffs.sort()
    lo_i = max(0, int(math.floor(0.025 * len(diffs))))
    hi_i = min(len(diffs) - 1, int(math.ceil(0.975 * len(diffs))) - 1)
    return {
        'replications_requested': reps,
        'replications_valid': len(diffs),
        'ci95_lower': diffs[lo_i],
        'ci95_upper': diffs[hi_i],
        'median': float(np.median(diffs)),
    }


def main():
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding='utf-8'))
    source = json.loads(SOURCE_RECEIPT_PATH.read_text(encoding='utf-8'))
    if protocol['status'] != 'FROZEN_FINAL_PRE_DISCOVERY_OUTCOME_BLIND':
        raise RuntimeError('final protocol not frozen')
    if source['classification'] != 'SOURCE_DATA_PASS':
        raise RuntimeError('source gate not PASS')
    if source['expected_archives_total'] != 96 or source['verified_archive_count'] != 96:
        raise RuntimeError('source receipt archive count mismatch')
    if protocol['protected_period']['2025_access'] or protocol['protected_period']['2026_access']:
        raise RuntimeError('protected-period protocol violation')

    expected_sha = {(x['venue'], x['month']): x['zip_sha256'] for x in source['archive_manifest']}
    if len(expected_sha) != 96:
        raise RuntimeError('source receipt manifest does not contain 96 unique archive identities')

    data = {}
    discovery_manifest = []
    for venue, base in BASES.items():
        combined = []
        for ym in months():
            zip_url = f'{base}/BTCUSDT-1d-{ym}.zip'
            checksum_url = zip_url + '.CHECKSUM'
            if '/2025-' in zip_url or '/2026-' in zip_url:
                raise RuntimeError('protected-period URL generation attempted')
            zb = get(zip_url)
            cb = get(checksum_url)
            current_sha = hashlib.sha256(zb).hexdigest().lower()
            official_sha = cb.decode('utf-8', 'replace').strip().split()[0].lower()
            frozen_sha = expected_sha.get((venue, ym))
            if current_sha != official_sha:
                raise RuntimeError(f'{venue} {ym}: current official checksum mismatch')
            if current_sha != frozen_sha:
                raise RuntimeError(f'{venue} {ym}: archive identity changed versus source gate')
            part = parse_archive(zb, venue)
            combined.extend(part)
            discovery_manifest.append({'venue': venue, 'month': ym, 'zip_sha256': current_sha, 'row_count': len(part)})
        data[venue] = combined

    days = expected_dates()
    if len(data['spot']) != 1461 or len(data['futures_um']) != 1461:
        raise RuntimeError('unexpected Discovery row count')
    spot = {x['date']: x for x in data['spot']}
    fut = {x['date']: x for x in data['futures_um']}
    if set(spot) != set(days) or set(fut) != set(days):
        raise RuntimeError('Discovery date set mismatch')

    log_ratio = []
    ranges = []
    for d in days:
        ratio = fut[d]['qv'] / spot[d]['qv']
        if not math.isfinite(ratio) or ratio <= 0:
            raise RuntimeError('invalid futures/spot turnover ratio')
        r = 10000.0 * math.log(spot[d]['high'] / spot[d]['low'])
        if not math.isfinite(r) or r <= 0:
            raise RuntimeError('invalid daily realized log range')
        log_ratio.append(math.log(ratio))
        ranges.append(r)

    eligible = []
    for i in range(180, len(days) - 1):
        prev = sorted(log_ratio[i-180:i])
        threshold = prev[143]
        event = 1 if log_ratio[i] >= threshold else 0
        eligible.append({
            'date': days[i],
            'event': event,
            'current_range_bps': ranges[i],
            'next_range_bps': ranges[i+1],
            'year': days[i].year,
        })

    n = len(eligible)
    events = [x['event'] for x in eligible]
    event_n = sum(events)
    control_n = n - event_n
    event_vals = [x['next_range_bps'] for x in eligible if x['event'] == 1]
    control_vals = [x['next_range_bps'] for x in eligible if x['event'] == 0]

    year_diffs = {}
    positive_years = 0
    for y in [2021, 2022, 2023, 2024]:
        ev = [x['next_range_bps'] for x in eligible if x['year'] == y and x['event'] == 1]
        ct = [x['next_range_bps'] for x in eligible if x['year'] == y and x['event'] == 0]
        diff = (float(np.mean(ev) - np.mean(ct)) if ev and ct else None)
        year_diffs[str(y)] = {'event_n': len(ev), 'control_n': len(ct), 'event_minus_control_bps': diff}
        if diff is not None and diff > 0:
            positive_years += 1

    yvec = []
    X = []
    for x in eligible:
        yvec.append(math.log(x['next_range_bps']))
        X.append([
            1.0,
            float(x['event']),
            math.log(x['current_range_bps']),
            1.0 if x['year'] == 2022 else 0.0,
            1.0 if x['year'] == 2023 else 0.0,
            1.0 if x['year'] == 2024 else 0.0,
        ])
    beta, se = hac_ols(yvec, X, lags=7)
    event_beta = float(beta[1])
    event_se = float(se[1])
    ci_lo = event_beta - 1.96 * event_se
    ci_hi = event_beta + 1.96 * event_se

    raw_event_mean = float(np.mean(event_vals)) if event_vals else None
    raw_control_mean = float(np.mean(control_vals)) if control_vals else None
    raw_diff = (raw_event_mean - raw_control_mean) if event_vals and control_vals else None
    boot = moving_block_bootstrap(
        [x['next_range_bps'] for x in eligible], events,
        protocol['bootstrap']['block_length_days'],
        protocol['bootstrap']['replications'],
        protocol['bootstrap']['seed'],
    )

    gate = protocol['promotion_gate']
    checks = {
        'minimum_eligible_observations': n >= gate['minimum_eligible_observations'],
        'minimum_event_observations': event_n >= gate['minimum_event_observations'],
        'event_beta_positive': event_beta > 0,
        'event_beta_hac_ci95_lower_gt_zero': ci_lo > 0,
        'raw_event_mean_gt_control_mean': raw_diff is not None and raw_diff > 0,
        'block_bootstrap_mean_difference_ci95_lower_gt_zero': boot['ci95_lower'] > 0,
        'minimum_positive_calendar_years': positive_years >= gate['minimum_calendar_years_with_positive_event_minus_control_difference'],
    }

    if n < gate['minimum_eligible_observations'] or event_n < gate['minimum_event_observations']:
        classification = protocol['classification']['insufficient']
    elif all(checks.values()):
        classification = protocol['classification']['pass']
    else:
        classification = protocol['classification']['fail']

    result = {
        'lab_id': protocol['lab_id'],
        'mve_id': protocol['mve_id'],
        'mode': 'FROZEN_MECHANISM_DISCOVERY_ONLY',
        'classification': classification,
        'sample': {
            'eligible_observations': n,
            'event_observations': event_n,
            'control_observations': control_n,
            'first_eligible_signal_day': eligible[0]['date'].isoformat() if eligible else None,
            'last_eligible_signal_day': eligible[-1]['date'].isoformat() if eligible else None,
        },
        'primary_model': {
            'event_beta_log_next_range': event_beta,
            'event_beta_hac_se': event_se,
            'event_beta_hac_ci95_lower': ci_lo,
            'event_beta_hac_ci95_upper': ci_hi,
            'hac_lags': 7,
        },
        'raw_comparison': {
            'event_mean_next_day_range_bps': raw_event_mean,
            'control_mean_next_day_range_bps': raw_control_mean,
            'event_minus_control_bps': raw_diff,
        },
        'year_differences': year_diffs,
        'positive_calendar_year_count': positive_years,
        'bootstrap': boot,
        'promotion_gate_checks': checks,
        'all_promotion_conditions_pass': all(checks.values()),
        'source_revalidation': {
            'archives_revalidated': len(discovery_manifest),
            'all_archive_sha256_equal_frozen_source_receipt': True,
            'all_current_official_checksums_passed': True,
        },
        'guards': GUARDS,
        'post_result_rule': protocol['post_result_rule'],
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
