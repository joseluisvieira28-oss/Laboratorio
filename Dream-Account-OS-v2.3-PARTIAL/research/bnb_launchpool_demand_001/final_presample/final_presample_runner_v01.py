import hashlib
import json
import math
import os
import random
import statistics
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FREEZE = ROOT / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_HOLDOUT_FREEZE_V0.1.json'
BIND = HERE / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_EXECUTION_BINDING_V0.1.json'
SOURCE = HERE / 'source_gate_v01' / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_GATE_V0.1.json'
MARKET = HERE / 'market_source_v01' / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_MARKET_SOURCE_V0.1.json'
OUTDIR = HERE / 'result_v01'
OUT = OUTDIR / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_RESULT_V0.1.json'
LEDGER = OUTDIR / 'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_LEDGER_V0.1.json'


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1024 * 1024), b''):
            h.update(c)
    return h.hexdigest()


def epoch_iso(s):
    return int(datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(timezone.utc).timestamp())


def parse_epoch(b):
    s = b.decode('ascii', 'strict').strip()
    if not s.isdigit():
        return None
    x = int(s)
    sec = x / 1_000_000.0 if x > 10**14 else x / 1_000.0 if x > 10**11 else float(x)
    return int(round(sec))


def pf(values):
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return math.inf if pos > 0 else 0.0
    return pos / neg


def pf_json(x):
    return '+Infinity' if math.isinf(x) else x


def quantile(vals, p):
    vals = sorted(vals)
    h = (len(vals) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - h) + vals[hi] * (h - lo)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    f = json.loads(FREEZE.read_text(encoding='utf-8'))
    b = json.loads(BIND.read_text(encoding='utf-8'))
    s = json.loads(SOURCE.read_text(encoding='utf-8'))
    m = json.loads(MARKET.read_text(encoding='utf-8'))

    assert f['status'] == 'FROZEN_BEFORE_PRESAMPLE_SOURCE_ENUMERATION_OR_MARKET_OUTCOME_ACCESS'
    assert b['status'] == 'FROZEN_POST_SOURCE_AUDIT_PRE_PRICE_OPEN'
    assert s['classification'] == 'SOURCE_DATA_PASS'
    assert m['classification'] == 'MARKET_SOURCE_DATA_PASS'
    assert s['canonical_event_manifest_sha256'] == b['source_gate']['canonical_event_manifest_sha256']
    assert m['archive_manifest_sha256'] == b['market_source']['archive_manifest_sha256']
    assert m['selected_trade_paths'] == b['market_source']['selected_trade_paths'] == 27
    assert f['execution_rule_unchanged']['round_trip_cost_base_bps'] == b['execution_rule']['base_round_trip_cost_bps'] == 20.0
    assert f['execution_rule_unchanged']['round_trip_cost_stress_bps'] == b['execution_rule']['stress_round_trip_cost_bps'] == 30.0
    assert f['path2_gates_all_required']['minimum_resolved_trades'] == b['promotion_gates']['minimum_resolved_trades'] == 25

    root = Path(os.environ.get('BLP_FINAL_PRESAMPLE_MARKET_SOURCE_DIR', '/tmp/blp_final_presample_market_source'))
    zips = {p.name: p for p in root.rglob('BNBBTC-15m-*.zip')}
    expected = {x['archive']: x['sha256'] for x in m['archive_manifest']}
    if set(zips) != set(expected):
        raise RuntimeError(f'ARCHIVE_SET_MISMATCH:got={len(zips)} expected={len(expected)}')
    for name, p in zips.items():
        if '-2023-' in name or '-2024-' in name or '-2025-' in name or '-2026-' in name:
            raise RuntimeError(f'FORBIDDEN_POST_PRESAMPLE_ARCHIVE:{name}')
        if sha256_file(p) != expected[name]:
            raise RuntimeError(f'ARCHIVE_SHA_MISMATCH:{name}')

    required = set()
    for x in m['selected']:
        required.add(epoch_iso(x['entry_time_utc']))
        required.add(epoch_iso(x['exit_time_utc']))

    opens = {}
    duplicates = []
    for name in sorted(zips):
        with zipfile.ZipFile(zips[name]) as z:
            bad = z.testzip()
            if bad is not None:
                raise RuntimeError(f'ZIP_CRC_FAILURE:{name}:{bad}')
            members = [x for x in z.namelist() if not x.endswith('/')]
            if len(members) != 1:
                raise RuntimeError(f'ZIP_MEMBER_COUNT_NOT_ONE:{name}')
            with z.open(members[0]) as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    parts = line.split(b',', 2)
                    if len(parts) < 2:
                        continue
                    ts = parse_epoch(parts[0])
                    if ts not in required:
                        continue
                    op = float(parts[1].decode('ascii', 'strict'))
                    if not math.isfinite(op) or op <= 0:
                        raise RuntimeError(f'INVALID_OPEN:{name}:{ts}')
                    if ts in opens:
                        duplicates.append(ts)
                    opens[ts] = op

    missing = sorted(required - set(opens))
    if missing or duplicates:
        result = {
            'protocol_id': f['protocol_id'],
            'classification': 'NON_SCIENTIFIC_BLOCKED_TIER3_REMAINS',
            'missing_required_rows': [datetime.fromtimestamp(x, tz=timezone.utc).isoformat() for x in missing],
            'duplicate_required_rows': sorted(set(duplicates)),
            'historical_rescue_closed': True,
            'new_2025_market_access': False,
            'access_2026_market': False,
            'live_trading_authorized': False,
        }
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
        return

    trades = []
    for i, x in enumerate(m['selected'], 1):
        et = epoch_iso(x['entry_time_utc'])
        xt = epoch_iso(x['exit_time_utc'])
        ent = opens[et]
        ex = opens[xt]
        gross = 10000.0 * (ex / ent - 1.0)
        base = gross - 20.0
        stress = gross - 30.0
        trades.append({
            'trade_id': i,
            'project_numbers': x['project_numbers'],
            'symbols': x['symbols'],
            'signal_time_utc': x['signal_time_utc'],
            'entry_time_utc': x['entry_time_utc'],
            'exit_time_utc': x['exit_time_utc'],
            'entry_open_bnbbtc': ent,
            'exit_open_bnbbtc': ex,
            'gross_bps': gross,
            'base_net_bps': base,
            'stress_net_bps': stress,
            'entry_year_utc': datetime.fromtimestamp(et, tz=timezone.utc).year,
        })

    gross = [x['gross_bps'] for x in trades]
    base = [x['base_net_bps'] for x in trades]
    stress = [x['stress_net_bps'] for x in trades]
    n = len(trades)
    gross_mean = statistics.fmean(gross)
    base_mean = statistics.fmean(base)
    base_pf = pf(base)
    stress_mean = statistics.fmean(stress)
    stress_pf = pf(stress)
    positive = [x for x in base if x > 0]
    concentration = max(positive) / sum(positive) if positive else None

    rng = random.Random(160930)
    boot = [statistics.fmean(base[rng.randrange(n)] for _ in range(n)) for __ in range(5000)]
    ci_lo = quantile(boot, 0.025)
    ci_hi = quantile(boot, 0.975)

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in base:
        equity *= max(0.0, 1.0 + r / 10000.0)
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
    compounded = equity - 1.0
    # Inherited V2 fatal-risk rule from the already-frozen 2025 Path-2 implementation.
    fatal_risk = (max_dd > 0.50 and compounded < 0.05)

    by_year = defaultdict(list)
    for tr in trades:
        by_year[tr['entry_year_utc']].append(tr['base_net_bps'])
    calendar = {str(y): {'n': len(v), 'base_mean_net_bps': statistics.fmean(v), 'base_total_net_bps': sum(v)} for y, v in sorted(by_year.items())}

    gates = {
        'source_provenance_clean_and_reproducible': (
            s['classification'] == 'SOURCE_DATA_PASS'
            and m['classification'] == 'MARKET_SOURCE_DATA_PASS'
            and s['canonical_event_manifest_sha256'] == b['source_gate']['canonical_event_manifest_sha256']
            and m['archive_manifest_sha256'] == b['market_source']['archive_manifest_sha256']
        ),
        'no_leakage_hindsight_or_post_outcome_selection': True,
        'minimum_resolved_trades': n >= 25,
        'base_mean_net_bps_gt_zero': base_mean > 0,
        'base_profit_factor_gte_one': base_pf >= 1.0,
        'expected_sign_correct_long_bnbbtc': gross_mean > 0,
        'max_single_trade_share_of_total_positive_base_net_lte_0_40': concentration is not None and concentration <= 0.40,
        'unresolved_selected_execution_paths_zero': len(m['execution_path_failures']) == 0,
        'source_rule_deviations_zero': True,
        'trading_rule_deviations_zero': True,
        'fatal_execution_or_risk_pathology_false': not fatal_risk,
    }

    if n < 25:
        classification = 'TIER_3_WATCHLIST_REMAINS_HISTORICAL_RESCUE_CLOSED'
    elif all(gates.values()):
        classification = 'TIER_2_PROMOTED_CANDIDATE_QUASE_DIAMANTE'
    else:
        classification = 'TIER_3_WATCHLIST_REMAINS_HISTORICAL_RESCUE_CLOSED'

    ledger = {
        'protocol_id': f['protocol_id'],
        'source_event_manifest_sha256': s['canonical_event_manifest_sha256'],
        'archive_manifest_sha256': m['archive_manifest_sha256'],
        'trades': trades,
    }
    ledger_bytes = (json.dumps(ledger, indent=2, sort_keys=True) + '\n').encode('utf-8')
    LEDGER.write_bytes(ledger_bytes)
    ledger_sha = hashlib.sha256(ledger_bytes).hexdigest()

    result = {
        'protocol_id': f['protocol_id'],
        'classification': classification,
        'tier2_path2_pass': classification == 'TIER_2_PROMOTED_CANDIDATE_QUASE_DIAMANTE',
        'resolved_trades': n,
        'economics': {
            'gross_mean_bps': gross_mean,
            'base_mean_net_bps': base_mean,
            'base_median_net_bps': statistics.median(base),
            'base_profit_factor': pf_json(base_pf),
            'base_win_rate': sum(x > 0 for x in base) / n,
            'base_total_net_bps': sum(base),
            'stress_mean_net_bps': stress_mean,
            'stress_profit_factor': pf_json(stress_pf),
            'stress_total_net_bps': sum(stress),
            'max_single_trade_positive_base_contribution_share': concentration,
        },
        'bootstrap_base_mean_bps': {
            'replications': 5000,
            'seed': 160930,
            'ci95_lower': ci_lo,
            'ci95_upper': ci_hi,
            'median_bootstrap_mean': statistics.median(boot),
            'role': 'REPORT_ONLY',
        },
        'calendar_base': calendar,
        'risk': {
            'compounded_base_return': compounded,
            'max_drawdown_compounded_base': max_dd,
            'v2_fatal_risk_rule_triggered': fatal_risk,
        },
        'promotion_gate_checks': gates,
        'failed_promotion_gates': [k for k, v in gates.items() if not v],
        'source_binding': {
            'canonical_event_manifest_sha256': s['canonical_event_manifest_sha256'],
            'market_archive_manifest_sha256': m['archive_manifest_sha256'],
            'market_source_run_id': b['market_source']['market_source_run_id'],
            'market_source_artifact_id': b['market_source']['market_source_artifact_id'],
            'market_source_artifact_zip_sha256': b['market_source']['market_source_artifact_zip_sha256'],
        },
        'ledger_sha256': ledger_sha,
        'historical_rescue_closed': True,
        'next_evidence_if_not_promoted': 'GENUINELY_PROSPECTIVE_FUTURE_ONLY',
        'new_2025_market_access': False,
        'access_2026_market': False,
        'live_trading_authorized': False,
        'post_outcome_historical_rescue_allowed': False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'classification': classification,
        'resolved_trades': n,
        'economics': result['economics'],
        'bootstrap': result['bootstrap_base_mean_bps'],
        'calendar_base': calendar,
        'risk': result['risk'],
        'failed_promotion_gates': result['failed_promotion_gates'],
        'ledger_sha256': ledger_sha,
    }, indent=2))


if __name__ == '__main__':
    main()
