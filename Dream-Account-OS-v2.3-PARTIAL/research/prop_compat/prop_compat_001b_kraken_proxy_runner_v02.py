from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from research.prop_compat import prop_compat_001b_kraken_proxy_runner_v01 as v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'research' / 'local_data' / 'prop_compat_001b_kraken_v02'
START_MS = v1.START_MS
END_MS = v1.END_MS
MIN_MS = v1.MIN_MS
N = v1.N
SYMBOLS = v1.SYMBOLS
SYM = v1.SYM


def iso_from_j(j: int) -> str:
    return datetime.fromtimestamp((START_MS + int(j) * MIN_MS) / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def simulate(rows, op, hi, lo, cl):
    sc = v1.scenarios()
    M = len(sc)

    bal = np.full(M, 100.0)
    daily = np.full(M, 97.0)
    decided = np.zeros(M, dtype=bool)
    passed = np.zeros(M, dtype=bool)
    breached = np.zeros(M, dtype=bool)
    ambig = np.zeros(M, dtype=bool)
    decision = np.full(M, -1, dtype=np.int64)
    reason = np.array([''] * M, dtype=object)

    risk = np.array([x['risk'] for x in sc])
    target = np.array([x['target'] for x in sc])
    mdd = np.array([x['mdd_floor'] for x in sc])
    en = np.array([x['en'] for x in sc])
    xx = np.array([x['xx'] for x in sc])
    legal = np.array([x['carry'] == 'LEGAL' for x in sc])
    phase = np.array([x['phase'] for x in sc], dtype=np.int16)

    qty = np.zeros((6, M))
    entpx = np.zeros(6)
    active = [None] * 6

    entries = defaultdict(list)
    exits = defaultdict(list)
    for r in rows:
        entries[(r['entry_time'] - START_MS) // MIN_MS].append(r)
        exits[(r['exit_time'] - START_MS) // MIN_MS].append(r)

    first = min(entries)

    max_close_dd = np.zeros(M)
    max_low_dd = np.zeros(M)
    max_daily_close_margin = np.zeros(M)
    max_single_notional = np.zeros(M)
    max_total_notional = np.zeros(M)
    max_concurrent = np.zeros(M, dtype=np.int16)

    ever_low_floor_possible = np.zeros(M, dtype=bool)
    ever_high_target_possible = np.zeros(M, dtype=bool)
    first_high_target_j = np.full(M, -1, dtype=np.int64)
    first_low_floor_j = np.full(M, -1, dtype=np.int64)

    def equity(prices):
        pnl = np.zeros(M)
        for si in range(6):
            if active[si] is not None:
                pnl += qty[si] * (prices[si] - entpx[si])
        return bal + pnl

    def freeze_decided(mask):
        if mask.any():
            qty[:, mask] = 0.0

    for j in range(first, N):
        live = ~decided
        if not live.any():
            break

        mod = j % 1440
        pxopen = op[:, j]

        current_notional = np.zeros(M)
        for si in range(6):
            if active[si] is not None:
                current_notional += np.abs(qty[si]) * pxopen[si]

        # Carry is debited on positions open immediately before this minute's ledger events.
        mask = live & legal & (mod == 0)
        if mask.any():
            bal[mask] -= current_notional[mask] * 0.00033

        mask = live & (~legal) & (phase == (mod % 240))
        if mask.any():
            bal[mask] -= current_notional[mask] * 0.000055

        # Kraken operational support: MDL resets at 00:30 UTC from account balance.
        if mod == 30:
            daily[live] = bal[live] - 3.0

        # Official frozen ledger exits first, symbol ascending.
        for r in sorted(exits.get(j, []), key=lambda x: x['symbol']):
            si = SYM[r['symbol']]
            mask = live & (qty[si] != 0)
            if mask.any():
                ep = float(r['exit_price'])
                bal[mask] += qty[si, mask] * (ep - entpx[si])
                bal[mask] -= np.abs(qty[si, mask]) * ep * xx[mask]
                qty[si, mask] = 0.0
            active[si] = None
            entpx[si] = 0.0

        # Official frozen ledger entries next, symbol ascending.
        for r in sorted(entries.get(j, []), key=lambda x: x['symbol']):
            si = SYM[r['symbol']]
            eq = equity(pxopen)
            mask = live
            amt = eq[mask] * risk[mask]
            notion = amt / float(r['initial_risk_fraction'])
            qty[si, mask] = notion / float(r['entry_price'])
            bal[mask] -= notion * en[mask]
            entpx[si] = float(r['entry_price'])
            active[si] = r
            max_single_notional[mask] = np.maximum(max_single_notional[mask], notion)

        total_notional = np.zeros(M)
        conc = np.zeros(M, dtype=np.int16)
        for si in range(6):
            total_notional += np.abs(qty[si]) * pxopen[si]
            conc += (qty[si] != 0).astype(np.int16)

        max_total_notional[live] = np.maximum(max_total_notional[live], total_notional[live])
        max_concurrent[live] = np.maximum(max_concurrent[live], conc[live])

        eqc = equity(cl[:, j])
        eqh = equity(hi[:, j])
        eql = equity(lo[:, j])

        max_close_dd[live] = np.maximum(max_close_dd[live], 100.0 - eqc[live])
        max_low_dd[live] = np.maximum(max_low_dd[live], 100.0 - eql[live])
        max_daily_close_margin[live] = np.maximum(max_daily_close_margin[live], daily[live] - eqc[live])

        # Mathematical lower bound only: cross-symbol lows need not be synchronous.
        low_possible = live & ((eql <= mdd) | (eql <= daily))
        new_low = low_possible & (~ever_low_floor_possible)
        first_low_floor_j[new_low] = j
        ever_low_floor_possible |= low_possible

        # Mathematical upper bound only: cross-symbol highs need not be synchronous.
        high_possible = live & (eqh >= target)
        new_high = high_possible & (~ever_high_target_possible)
        first_high_target_j[new_high] = j
        ever_high_target_possible |= high_possible

        # Confirmed proxy pass requires synchronized close target and no prior low-bound floor possibility.
        tmask = live & (eqc >= target)
        if tmask.any():
            safe = tmask & (~ever_low_floor_possible)
            if safe.any():
                passed[safe] = True
                decided[safe] = True
                decision[safe] = j
                reason[safe] = 'TARGET_CLOSE_ROBUST_TO_LOW_BOUND'
                freeze_decided(safe)

            uncertain = tmask & ever_low_floor_possible
            if uncertain.any():
                ambig[uncertain] = True
                decided[uncertain] = True
                decision[uncertain] = j
                reason[uncertain] = 'TARGET_CLOSE_AFTER_INTRAMINUTE_BREACH_LOWER_BOUND'
                freeze_decided(uncertain)

        # Confirmed synchronized-close breach is only obvious if no earlier/current target upper bound was possible.
        live = ~decided
        bmask = live & ((eqc <= mdd) | (eqc <= daily))
        if bmask.any():
            uncertain = bmask & ever_high_target_possible
            if uncertain.any():
                ambig[uncertain] = True
                decided[uncertain] = True
                decision[uncertain] = j
                reason[uncertain] = 'BREACH_CLOSE_AFTER_TARGET_INTRAMINUTE_UPPER_BOUND'
                freeze_decided(uncertain)

            obvious = bmask & (~ever_high_target_possible)
            if obvious.any():
                breached[obvious] = True
                decided[obvious] = True
                decision[obvious] = j
                reason[obvious] = np.where(
                    eqc[obvious] <= mdd[obvious],
                    'MDD_CLOSE_BREACH',
                    'MDL_CLOSE_BREACH',
                )
                freeze_decided(obvious)

    out = []
    for k, x in enumerate(sc):
        if passed[k]:
            label = 'ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
        elif breached[k]:
            label = 'OBVIOUS_PROXY_BREACH'
        elif ambig[k] or ever_high_target_possible[k]:
            label = 'AMBIGUITY_MATERIAL'
            if decision[k] < 0:
                reason[k] = 'TARGET_INTRAMINUTE_UPPER_BOUND_WITHOUT_CONFIRMED_CLOSE_DECISION'
        else:
            label = 'PROXY_INSUFFICIENT_HISTORY_NO_DECISION'

        out.append({
            **x,
            'classification': label,
            'decision_time_utc': None if decision[k] < 0 else iso_from_j(decision[k]),
            'reason': str(reason[k]),
            'ending_balance': float(bal[k]),
            'max_close_drawdown_pct_initial': float(max_close_dd[k]),
            'max_low_bound_drawdown_pct_initial': float(max_low_dd[k]),
            'max_daily_close_breach_margin_pct_initial': float(max_daily_close_margin[k]),
            'max_single_position_notional_multiple_initial': float(max_single_notional[k] / 100.0),
            'max_total_open_notional_multiple_initial': float(max_total_notional[k] / 100.0),
            'max_concurrent_positions': int(max_concurrent[k]),
            'target_upper_bound_possible': bool(ever_high_target_possible[k]),
            'first_target_upper_bound_time_utc': None if first_high_target_j[k] < 0 else iso_from_j(first_high_target_j[k]),
            'breach_lower_bound_possible': bool(ever_low_floor_possible[k]),
            'first_breach_lower_bound_time_utc': None if first_low_floor_j[k] < 0 else iso_from_j(first_low_floor_j[k]),
        })
    return out


def summarize(results, archives):
    groups = defaultdict(list)
    for r in results:
        groups[(r['plan'], r['risk'], r['exec'])].append(r)

    cells = []
    for key, rs in sorted(groups.items()):
        legal = [r for r in rs if r['carry'] == 'LEGAL'][0]
        support = [r for r in rs if r['carry'] == 'SUPPORT']
        counts = defaultdict(int)
        for r in support:
            counts[r['classification']] += 1

        if (
            legal['classification'] == 'ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
            and counts['ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'] == 240
        ):
            cell = 'ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED'
        elif (
            legal['classification'] == 'OBVIOUS_PROXY_BREACH'
            and counts['OBVIOUS_PROXY_BREACH'] == 240
        ):
            cell = 'OBVIOUS_PROXY_BREACH'
        elif (
            legal['classification'] == 'PROXY_INSUFFICIENT_HISTORY_NO_DECISION'
            or counts['PROXY_INSUFFICIENT_HISTORY_NO_DECISION'] > 0
        ):
            cell = 'PROXY_INSUFFICIENT'
        else:
            cell = 'AMBIGUITY_MATERIAL'

        cells.append({
            'plan': key[0],
            'risk_pct_per_1R': round(key[1] * 100, 2),
            'execution_case': key[2],
            'cell_classification': cell,
            'legal_daily': {
                k: legal[k]
                for k in [
                    'classification',
                    'decision_time_utc',
                    'reason',
                    'ending_balance',
                    'max_close_drawdown_pct_initial',
                    'max_low_bound_drawdown_pct_initial',
                    'max_total_open_notional_multiple_initial',
                    'max_concurrent_positions',
                    'target_upper_bound_possible',
                    'first_target_upper_bound_time_utc',
                    'breach_lower_bound_possible',
                    'first_breach_lower_bound_time_utc',
                ]
            },
            'support_4h_phase_counts': dict(counts),
            'support_4h_decision_time_range_utc': [
                min((r['decision_time_utc'] for r in support if r['decision_time_utc']), default=None),
                max((r['decision_time_utc'] for r in support if r['decision_time_utc']), default=None),
            ],
            'support_4h_first_target_upper_bound_range_utc': [
                min((r['first_target_upper_bound_time_utc'] for r in support if r['first_target_upper_bound_time_utc']), default=None),
                max((r['first_target_upper_bound_time_utc'] for r in support if r['first_target_upper_bound_time_utc']), default=None),
            ],
        })

    cc = defaultdict(int)
    for c in cells:
        cc[c['cell_classification']] += 1

    return {
        'campaign_id': 'PROP-COMPAT-001B',
        'status': 'KRAKEN_PROP_1M_AMBIGUITY_ENVELOPE_COMPLETE_V02',
        'setup_id': 'DH-03-HO1',
        'decisional_authority': False,
        'official_phase3_risk_grid_run': False,
        'source_validation': {
            'binance_1m_archives_downloaded_and_hash_validated': archives,
            'access_2025': False,
            'access_2026': False,
        },
        'implementation_authority': 'PROP_COMPAT_001B_KRAKEN_PROP_IMPLEMENTATION_CLARIFICATION_02',
        'base_cells': 30,
        'support_phase_paths': 7200,
        'cell_classification_counts': dict(cc),
        'cells': cells,
        'governance': {
            'no_best_plan_selection': True,
            'no_best_risk_selection': True,
            'post_outcome_tuning': False,
            'challenge_purchase': False,
            'live_trading': False,
            'merge_to_main': False,
        },
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit('usage: runner_v02 SOURCE_ARTIFACT_DIR EXECUTION_ARTIFACT_DIR')
    src = Path(argv[1])
    ex = Path(argv[2])
    OUT.mkdir(parents=True, exist_ok=True)

    rows = v1.load_ledger(ex)
    op, hi, lo, cl, archives = v1.load_sources(src)
    receipt = summarize(simulate(rows, op, hi, lo, cl), archives)
    raw = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    receipt['fingerprint'] = hashlib.sha256(raw).hexdigest()
    out = OUT / 'PROP_COMPAT_001B_KRAKEN_PROP_1M_AMBIGUITY_ENVELOPE_RECEIPT_V0.2.json'
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        'status': receipt['status'],
        'cell_classification_counts': receipt['cell_classification_counts'],
        'fingerprint': receipt['fingerprint'],
    }, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main(sys.argv))
