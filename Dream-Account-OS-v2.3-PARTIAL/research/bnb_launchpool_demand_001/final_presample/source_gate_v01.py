import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FREEZE = ROOT / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_HOLDOUT_FREEZE_V0.1.json'
AMEND = ROOT / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_ROUTE_AMENDMENT_V0.1.json'
SEED = ROOT / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_SEED_V0.1.json'
OUTDIR = HERE / 'source_gate_v01'
RAW = OUTDIR / 'raw'
OUT = OUTDIR / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_GATE_V0.1.json'
DETAIL = 'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={}'
UA = {
    'User-Agent': 'Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-FINAL-HOLDOUT/1.1',
    'Accept': 'application/json,text/plain,*/*',
}
HEX = re.compile(r'^[0-9a-fA-F]{32}$')


def get(url, tries=7):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            retry_after = e.headers.get('Retry-After') if e.headers else None
            if e.code == 429:
                wait = float(retry_after) if retry_after and retry_after.isdigit() else min(30.0, 2.0 * (2 ** i))
            else:
                wait = min(12.0, 0.75 * (2 ** i))
            time.sleep(wait)
        except Exception as e:
            last = e
            time.sleep(min(12.0, 0.75 * (2 ** i)))
    raise last


def walk_dicts(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk_dicts(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_dicts(v)


def flatten(x):
    vals = []
    if isinstance(x, dict):
        for v in x.values():
            vals.append(flatten(v))
    elif isinstance(x, list):
        for v in x:
            vals.append(flatten(v))
    elif isinstance(x, str):
        vals.append(x)
    text = ' '.join(vals)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    return re.sub(r'\s+', ' ', text).strip()


def iso_from_epoch(v):
    x = float(v)
    if x > 1e14:
        x /= 1e6
    elif x > 1e11:
        x /= 1e3
    return datetime.fromtimestamp(x, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def extract_publish_time(obj):
    candidates = []
    for d in walk_dicts(obj):
        for key in ('publishDate', 'releaseDate', 'publishedAt', 'publishTime'):
            v = d.get(key)
            if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
                try:
                    candidates.append(iso_from_epoch(v))
                except Exception:
                    pass
    # Article-detail responses can repeat metadata. Earliest plausible CMS publication timestamp is authoritative.
    plausible = [x for x in candidates if '2019-' <= x <= '2023-01-01T00:00:00Z']
    return min(plausible) if plausible else (min(candidates) if candidates else None)


def symbol_present(text, symbol):
    return re.search(r'(?<![A-Z0-9])' + re.escape(symbol.upper()) + r'(?![A-Z0-9])', text.upper()) is not None


def main():
    freeze = json.loads(FREEZE.read_text(encoding='utf-8'))
    amend = json.loads(AMEND.read_text(encoding='utf-8'))
    seed = json.loads(SEED.read_text(encoding='utf-8'))
    assert freeze['status'] == 'FROZEN_BEFORE_PRESAMPLE_SOURCE_ENUMERATION_OR_MARKET_OUTCOME_ACCESS'
    assert amend['status'] == 'FROZEN_BEFORE_ANY_PRESAMPLE_MARKET_PRICE_OR_RETURN_ACCESS'
    assert seed['status'] == 'FROZEN_BEFORE_ANY_PRESAMPLE_MARKET_PRICE_OR_RETURN_ACCESS'
    assert amend['scientific_rules_unchanged'] is True
    assert amend['trading_rules_unchanged'] is True
    assert amend['promotion_gates_unchanged'] is True
    assert seed['unique_article_count'] == 27
    assert seed['project_number_count'] == 30

    # Frozen completeness check before any network call.
    nums = []
    codes = []
    for a in seed['articles']:
        assert HEX.fullmatch(a['article_code'])
        codes.append(a['article_code'].lower())
        nums.extend(a['project_numbers'])
    assert len(codes) == len(set(codes)) == 27
    assert sorted(nums) == list(range(1, 31))
    assert len(nums) == len(set(nums)) == 30

    OUTDIR.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    project_records = {}
    article_records = []
    failures = []

    for idx, a in enumerate(seed['articles']):
        code = a['article_code'].lower()
        try:
            body = get(DETAIL.format(code))
            raw_sha = hashlib.sha256(body).hexdigest()
            (RAW / f'{code}.json').write_bytes(body)
            obj = json.loads(body.decode('utf-8'))
            text = flatten(obj)
            low = text.lower()
            publish_utc = extract_publish_time(obj)

            launchpool_ok = 'launchpool' in low
            bnb_ok = re.search(r'\bbnb\b', low) is not None
            staking_ok = any(term in low for term in ('stake', 'staking', 'lock', 'locking', 'farm', 'farming'))
            symbols_ok = {s: symbol_present(text, s) for s in a['expected_symbols']}
            date_ok = publish_utc is not None and '2020-01-01T00:00:00Z' <= publish_utc < '2023-01-01T00:00:00Z'

            checks = {
                'launchpool': launchpool_ok,
                'bnb': bnb_ok,
                'staking_locking_or_farming': staking_ok,
                'all_expected_symbols': all(symbols_ok.values()),
                'publish_timestamp_plausible_presample': date_ok,
            }
            article_records.append({
                'article_code': code,
                'project_numbers': a['project_numbers'],
                'expected_symbols': a['expected_symbols'],
                'official_support_url': f'https://www.binance.com/en/support/announcement/detail/{code}',
                'published_timestamp_utc': publish_utc,
                'raw_response_sha256': raw_sha,
                'checks': checks,
                'symbol_checks': symbols_ok,
            })
            if not all(checks.values()):
                failures.append({'article_code': code, 'project_numbers': a['project_numbers'], 'error': 'OFFICIAL_DETAIL_VALIDATION_FAIL', 'checks': checks, 'symbol_checks': symbols_ok})
            else:
                # Expand combined official pages to project-level source records.
                for n, sym in zip(a['project_numbers'], a['expected_symbols']):
                    if n in project_records:
                        failures.append({'project_number': n, 'error': 'DUPLICATE_PROJECT_NUMBER'})
                        continue
                    project_records[n] = {
                        'n': n,
                        'symbol': sym,
                        'article_code': code,
                        'official_support_url': f'https://www.binance.com/en/support/announcement/detail/{code}',
                        'published_timestamp_utc': publish_utc,
                        'bnb_pool_present': True,
                        'staking_or_locking_present': True,
                        'raw_response_sha256': raw_sha,
                    }
        except Exception as e:
            failures.append({'article_code': code, 'project_numbers': a['project_numbers'], 'error': f'{type(e).__name__}:{e}'})

        # Deliberate throttle: finite 27-call route, no catalog brute-force.
        if idx + 1 < len(seed['articles']):
            time.sleep(1.0)

    missing = [n for n in range(1, 31) if n not in project_records]
    ordered = [project_records[n] for n in sorted(project_records)]
    manifest_bytes = ('\n'.join(
        f"{r['n']}|{r['symbol']}|{r['article_code']}|{r['published_timestamp_utc']}|{r['raw_response_sha256']}"
        for r in ordered
    ) + '\n').encode('utf-8')
    classification = 'SOURCE_DATA_PASS' if not missing and not failures and len(ordered) == 30 else 'SOURCE_DATA_FAILURE'

    out = {
        'protocol_id': freeze['protocol_id'],
        'source_route_amendment_id': amend['amendment_id'],
        'seed_id': seed['seed_id'],
        'classification': classification,
        'recovered_count': len(ordered),
        'unique_validated_articles': sum(1 for x in article_records if all(x['checks'].values())),
        'missing_project_numbers': missing,
        'ineligible_project_numbers': [],
        'detail_failures': failures,
        'canonical_event_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
        'canonical_events': ordered,
        'canonical_articles': article_records,
        'market_prices_opened': False,
        'returns_computed': False,
        'pnl_computed': False,
        'new_2025_market_access': False,
        'access_2026_market': False,
        'live_trading_authorized': False,
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'classification': classification,
        'recovered_count': len(ordered),
        'unique_validated_articles': out['unique_validated_articles'],
        'missing_project_numbers': missing,
        'failure_count': len(failures),
        'canonical_event_manifest_sha256': out['canonical_event_manifest_sha256'],
    }, indent=2))


if __name__ == '__main__':
    main()
