from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "prop_compat_001f_tfg_kraken"
UA = "PROP-COMPAT-001F TFG Kraken proxy research/1.0"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
SYM = {s: i for i, s in enumerate(SYMBOLS)}
START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2025, 10, 11, tzinfo=timezone.utc).timestamp() * 1000)
BAR_MS = 15 * 60 * 1000
N = (END_MS - START_MS) // BAR_MS
EXPECTED_TRADE_CORE_FP = "ab290487c693ad98cb20d1b87e2db2fcf11c97a54da303d7ff301e9d99dca9f8"
RAW_HEADER = ("open_time", "open", "high", "low", "close", "volume", "amount", "close_time")


def canonical_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str, retries: int = 4) -> bytes:
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as exc:
            last = exc
            if k + 1 < retries:
                time.sleep(2 ** k)
    raise RuntimeError(f"DOWNLOAD_FAILED:{url}:{type(last).__name__}:{last}")


def iso_j(j: int | None) -> str | None:
    if j is None or j < 0:
        return None
    return datetime.fromtimestamp((START_MS + int(j) * BAR_MS) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def month_from_file(name: str) -> str:
    stem = name.rsplit("-", 3)
    if len(stem) < 4:
        raise RuntimeError(f"BAD_FILE_NAME:{name}")
    return stem[-3] + "-" + stem[-2]


def load_authority(artifact_dir: Path):
    lp = artifact_dir / "PROP_COMPAT_001E_TFG_2025_REGENERATED_LEDGER_V0.1.json"
    mp = artifact_dir / "PROP_COMPAT_001E_TFG_2025_REACQUIRED_SOURCE_MANIFEST_V0.1.json"
    rp = artifact_dir / "PROP_COMPAT_001E_TFG_2025_BULK_REPLAY_RECEIPT_V0.1.json"
    ledger = json.loads(lp.read_text(encoding="utf-8"))
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    receipt = json.loads(rp.read_text(encoding="utf-8"))
    if receipt["status"] != "TFG_SEMANTIC_REPRODUCTION_PASS_BYTE_IDENTITY_NOT_RECOVERED":
        raise RuntimeError("RECOVERY_STATUS")
    if receipt["trade_core_fingerprint"] != EXPECTED_TRADE_CORE_FP:
        raise RuntimeError("RECOVERY_TRADE_CORE_FP")
    if canonical_hash(ledger["records"]) != EXPECTED_TRADE_CORE_FP:
        raise RuntimeError("LEDGER_TRADE_CORE_FP")
    if len(ledger["records"]) != 40:
        raise RuntimeError(f"LEDGER_COUNT:{len(ledger['records'])}")
    if manifest.get("2026_accessed") is not False:
        raise RuntimeError("MANIFEST_2026_FLAG")
    return sorted(ledger["records"], key=lambda r: (int(r["signal"]["entry_open_time"]), r["symbol"])), manifest, receipt


def parse_csv_into_arrays(raw: bytes, rec: dict, op, hi, lo, cl):
    if sha256_bytes(raw) != rec["current_sha256"]:
        raise RuntimeError(f"SOURCE_HASH_DRIFT:{rec['file']}")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if tuple(reader.fieldnames or ()) != RAW_HEADER:
        raise RuntimeError(f"HEADER_MISMATCH:{rec['file']}:{reader.fieldnames}")
    si = SYM[rec["symbol"]]
    rows = 0
    first = last = None
    prev = None
    used = 0
    for row in reader:
        t = int(row["open_time"])
        ct = int(row["close_time"])
        if t % BAR_MS != 0 or ct != t + BAR_MS:
            raise RuntimeError(f"TIME_ALIGNMENT:{rec['file']}:{t}:{ct}")
        if prev is not None and t - prev != BAR_MS:
            raise RuntimeError(f"INTERNAL_GAP:{rec['file']}:{prev}:{t}")
        o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
        if not all(math.isfinite(x) for x in (o, h, l, c)) or min(o, h, l, c) <= 0 or h < max(o, c, l) or l > min(o, c, h):
            raise RuntimeError(f"BAD_OHLC:{rec['file']}:{t}")
        rows += 1
        first = t if first is None else first
        last = t
        prev = t
        if START_MS <= t < END_MS:
            j = (t - START_MS) // BAR_MS
            op[si, j], hi[si, j], lo[si, j], cl[si, j] = o, h, l, c
            used += 1
    if rows != int(rec["rows"]) or first != int(rec["first_open_time_ms"]) or last != int(rec["last_open_time_ms"]):
        raise RuntimeError(f"SOURCE_META_DRIFT:{rec['file']}:{rows}:{first}:{last}")
    return used


def load_price_path(manifest: dict):
    op = np.full((6, N), np.nan)
    hi = np.full((6, N), np.nan)
    lo = np.full((6, N), np.nan)
    cl = np.full((6, N), np.nan)
    selected = []
    for rec in manifest["records"]:
        fn = rec["file"]
        month = month_from_file(fn)
        if rec["symbol"] not in SYM or not ("2025-01" <= month <= "2025-10"):
            continue
        raw = get(rec["masked_url"])
        used = parse_csv_into_arrays(raw, rec, op, hi, lo, cl)
        selected.append({
            "symbol": rec["symbol"], "file": fn, "month": month,
            "sha256": rec["current_sha256"], "rows": rec["rows"], "used_rows": used,
        })
        print("SOURCE_HASH_PASS", rec["symbol"], month, used, flush=True)
    if len(selected) != 60:
        raise RuntimeError(f"SELECTED_SOURCE_FILES:{len(selected)}")
    for si, s in enumerate(SYMBOLS):
        missing = np.isnan(cl[si]).sum()
        if missing:
            raise RuntimeError(f"SOURCE_INCOMPLETE:{s}:missing={int(missing)}")
    return op, hi, lo, cl, selected


def reconstruct_events(rows, op, hi, lo):
    entries = defaultdict(list)
    open_exits = defaultdict(list)
    intrabar_exits = defaultdict(list)
    diagnostics = {"entries": 0, "exits": 0, "stop_events": 0, "target_events": 0, "time_exit_events": 0, "same_day_target_seen_before_authoritative_stop": 0}
    for r in rows:
        s, o, symbol = r["signal"], r["outcome"], r["symbol"]
        si = SYM[symbol]
        entry_ms = int(s["entry_open_time"])
        if not (START_MS <= entry_ms < END_MS):
            raise RuntimeError(f"ENTRY_OUT_OF_RANGE:{symbol}:{entry_ms}")
        ej = (entry_ms - START_MS) // BAR_MS
        if abs(float(op[si, ej]) - float(s["entry"])) > max(1e-10, abs(float(s["entry"])) * 1e-10):
            raise RuntimeError(f"ENTRY_PRICE_MISMATCH:{symbol}:{entry_ms}:{op[si,ej]}:{s['entry']}")
        rr = {
            "symbol": symbol, "entry_j": int(ej), "entry_price": float(s["entry"]),
            "initial_risk_fraction": float(s["initial_risk_fraction"]), "stop": float(s["stop"]),
            "target": float(s["target"]), "frozen_exit_reason": o["exit_reason"],
            "frozen_exit_day_ms": int(o["exit_open_time"]), "frozen_exit_price": float(o["exit_price"]),
        }
        entries[int(ej)].append(rr)
        diagnostics["entries"] += 1
        exit_day = int(o["exit_open_time"])
        xj0 = (exit_day - START_MS) // BAR_MS
        if o["exit_reason"] == "TIME_EXIT_NEXT_OPEN":
            rr["exit_j"] = int(xj0); rr["proxy_exit_price"] = float(o["exit_price"]); rr["exit_at_open"] = True
            open_exits[int(xj0)].append(rr); diagnostics["time_exit_events"] += 1
        elif o["exit_reason"] == "STOP":
            stop, target = float(s["stop"]), float(s["target"])
            found = None; target_seen = False
            for j in range(int(xj0), min(int(xj0) + 96, N)):
                if op[si, j] >= target or hi[si, j] >= target: target_seen = True
                if op[si, j] <= stop: raise RuntimeError(f"STOP_GAP_CONFLICT_WITH_FROZEN_STOP:{symbol}:{iso_j(j)}")
                if lo[si, j] <= stop: found = j; break
            if found is None: raise RuntimeError(f"STOP_NOT_FOUND_15M:{symbol}:{exit_day}")
            if target_seen: diagnostics["same_day_target_seen_before_authoritative_stop"] += 1
            rr["exit_j"] = int(found); rr["proxy_exit_price"] = stop; rr["exit_at_open"] = False
            intrabar_exits[int(found)].append(rr); diagnostics["stop_events"] += 1
        elif o["exit_reason"] == "TARGET":
            target, stop = float(s["target"]), float(s["stop"])
            found = None
            for j in range(int(xj0), min(int(xj0) + 96, N)):
                if op[si, j] <= stop or lo[si, j] <= stop: raise RuntimeError(f"TARGET_DAY_STOP_CONFLICT:{symbol}:{iso_j(j)}")
                if op[si, j] >= target: found = (j, True); break
                if hi[si, j] >= target: found = (j, False); break
            if found is None: raise RuntimeError(f"TARGET_NOT_FOUND_15M:{symbol}:{exit_day}")
            j, at_open = found
            rr["exit_j"] = int(j); rr["proxy_exit_price"] = target; rr["exit_at_open"] = bool(at_open)
            (open_exits if at_open else intrabar_exits)[int(j)].append(rr); diagnostics["target_events"] += 1
        else:
            raise RuntimeError(f"UNKNOWN_EXIT_REASON:{o['exit_reason']}")
        if abs(float(rr["proxy_exit_price"]) - float(o["exit_price"])) > max(1e-9, abs(float(o["exit_price"])) * 1e-9):
            raise RuntimeError(f"EXIT_PRICE_MISMATCH:{symbol}:{rr['proxy_exit_price']}:{o['exit_price']}")
        diagnostics["exits"] += 1
    if diagnostics["entries"] != 40 or diagnostics["exits"] != 40:
        raise RuntimeError(f"EVENT_COUNT:{diagnostics}")
    return entries, open_exits, intrabar_exits, diagnostics


def scenarios():
    plans = {"STARTER": (10.0, 6.0), "INTERMEDIATE": (12.0, 5.0), "ADVANCED": (9.0, 3.0)}
    risks = [0.10, 0.15, 0.20, 0.25, 0.30]
    execs = {"BASE": (0.0010, 0.0010), "STRESS": (0.0015, 0.0015)}
    sizings = ["TFG_FROZEN_R_DENOM", "STOP_DISTANCE_ONLY_CONSERVATIVE"]
    out = []
    for plan, (target, mdd) in plans.items():
        for risk_pct in risks:
            for ex, (en, xx) in execs.items():
                for sizing in sizings:
                    common = dict(plan=plan, target=100.0 + target, mdd_floor=100.0 - mdd, risk=risk_pct / 100.0, risk_pct=risk_pct, execution_case=ex, en=en, xx=xx, rt=en + xx, sizing=sizing)
                    out.append({**common, "carry": "LEGAL_DAILY", "phase": -1, "phase15": -1})
                    for phase in range(240):
                        phase15 = ((phase + 14) // 15 * 15) % 240
                        out.append({**common, "carry": "SUPPORT_4H", "phase": phase, "phase15": phase15})
    return out


def simulate(rows, op, hi, lo, cl):
    entries, open_exits, intrabar_exits, event_diag = reconstruct_events(rows, op, hi, lo)
    sc = scenarios(); M = len(sc)
    bal = np.full(M, 100.0); daily_floor = np.full(M, 97.0)
    decided = np.zeros(M, dtype=bool); passed = np.zeros(M, dtype=bool); breached = np.zeros(M, dtype=bool); ambiguous = np.zeros(M, dtype=bool)
    decision_j = np.full(M, -1, dtype=np.int64); reason = np.array([""] * M, dtype=object)
    risk = np.array([x["risk"] for x in sc]); target = np.array([x["target"] for x in sc]); mdd = np.array([x["mdd_floor"] for x in sc])
    en = np.array([x["en"] for x in sc]); xx = np.array([x["xx"] for x in sc]); rt = np.array([x["rt"] for x in sc])
    exact_r = np.array([x["sizing"] == "TFG_FROZEN_R_DENOM" for x in sc]); legal = np.array([x["carry"] == "LEGAL_DAILY" for x in sc]); phase15 = np.array([x["phase15"] for x in sc], dtype=np.int16)
    qty = np.zeros((6, M)); entpx = np.zeros(6); active = [None] * 6
    ever_low = np.zeros(M, dtype=bool); ever_high = np.zeros(M, dtype=bool); first_low = np.full(M, -1, dtype=np.int64); first_high = np.full(M, -1, dtype=np.int64)
    max_close_dd = np.zeros(M); max_low_dd = np.zeros(M); max_daily_margin = np.zeros(M); max_total_notional = np.zeros(M); max_single_notional = np.zeros(M); max_concurrent = np.zeros(M, dtype=np.int16)
    total_carry = np.zeros(M); total_entry_cost = np.zeros(M); total_exit_cost = np.zeros(M)

    def equity(prices):
        pnl = np.zeros(M)
        for si in range(6):
            if active[si] is not None: pnl += qty[si] * (prices[si] - entpx[si])
        return bal + pnl

    def current_notional(prices):
        n = np.zeros(M)
        for si in range(6):
            if active[si] is not None: n += np.abs(qty[si]) * prices[si]
        return n

    def freeze(mask):
        if mask.any(): qty[:, mask] = 0.0

    first_j = min(entries); last_j = max(max(open_exits.keys(), default=first_j), max(intrabar_exits.keys(), default=first_j))
    for j in range(first_j, min(last_j + 2, N)):
        live = ~decided
        if not live.any(): break
        pxo = op[:, j]; minute_of_day = ((START_MS + j * BAR_MS) // 60000) % 1440; mod240 = int(minute_of_day % 240)
        cur_not = current_notional(pxo)
        cmask = live & legal & (minute_of_day == 0)
        if cmask.any():
            fee = cur_not[cmask] * 0.00033; bal[cmask] -= fee; total_carry[cmask] += fee
        cmask = live & (~legal) & (phase15 == mod240)
        if cmask.any():
            fee = cur_not[cmask] * 0.000055; bal[cmask] -= fee; total_carry[cmask] += fee
        if minute_of_day == 30: daily_floor[live] = bal[live] * 0.97

        for r in sorted(open_exits.get(j, []), key=lambda x: x["symbol"]):
            si = SYM[r["symbol"]]; mask = live & (qty[si] != 0)
            if mask.any():
                ep = float(r["proxy_exit_price"]); bal[mask] += qty[si, mask] * (ep - entpx[si]); fee = np.abs(qty[si, mask]) * ep * xx[mask]; bal[mask] -= fee; total_exit_cost[mask] += fee; qty[si, mask] = 0.0
            active[si] = None; entpx[si] = 0.0

        for r in sorted(entries.get(j, []), key=lambda x: x["symbol"]):
            si = SYM[r["symbol"]]
            if active[si] is not None: raise RuntimeError(f"ACTIVE_SYMBOL_ENTRY:{r['symbol']}:{iso_j(j)}")
            eq = equity(pxo); mask = live; amt = eq[mask] * risk[mask]; rf = float(r["initial_risk_fraction"]); denom = np.where(exact_r[mask], rf + rt[mask], rf); notion = amt / denom
            qty[si, mask] = notion / float(r["entry_price"]); fee = notion * en[mask]; bal[mask] -= fee; total_entry_cost[mask] += fee; entpx[si] = float(r["entry_price"]); active[si] = r; max_single_notional[mask] = np.maximum(max_single_notional[mask], notion)

        eqh = equity(hi[:, j]); eql = equity(lo[:, j]); low_possible = live & ((eql <= mdd) | (eql <= daily_floor)); high_possible = live & (eqh >= target)
        new_low = low_possible & (~ever_low); new_high = high_possible & (~ever_high); first_low[new_low] = j; first_high[new_high] = j; ever_low |= low_possible; ever_high |= high_possible; max_low_dd[live] = np.maximum(max_low_dd[live], 100.0 - eql[live])

        for r in sorted(intrabar_exits.get(j, []), key=lambda x: x["symbol"]):
            si = SYM[r["symbol"]]; mask = live & (qty[si] != 0)
            if mask.any():
                ep = float(r["proxy_exit_price"]); bal[mask] += qty[si, mask] * (ep - entpx[si]); fee = np.abs(qty[si, mask]) * ep * xx[mask]; bal[mask] -= fee; total_exit_cost[mask] += fee; qty[si, mask] = 0.0
            active[si] = None; entpx[si] = 0.0

        total_not = current_notional(cl[:, j]); conc = np.zeros(M, dtype=np.int16)
        for si in range(6): conc += (qty[si] != 0).astype(np.int16)
        max_total_notional[live] = np.maximum(max_total_notional[live], total_not[live]); max_concurrent[live] = np.maximum(max_concurrent[live], conc[live])
        eqc = equity(cl[:, j]); max_close_dd[live] = np.maximum(max_close_dd[live], 100.0 - eqc[live]); max_daily_margin[live] = np.maximum(max_daily_margin[live], daily_floor[live] - eqc[live])

        tmask = live & (eqc >= target)
        if tmask.any():
            safe = tmask & (~ever_low)
            if safe.any(): passed[safe] = True; decided[safe] = True; decision_j[safe] = j; reason[safe] = "TARGET_15M_CLOSE_ROBUST_TO_LOW_BOUND"; freeze(safe)
            uncertain = tmask & ever_low
            if uncertain.any(): ambiguous[uncertain] = True; decided[uncertain] = True; decision_j[uncertain] = j; reason[uncertain] = "TARGET_CLOSE_AFTER_INTRABAR_BREACH_LOWER_BOUND"; freeze(uncertain)
        live = ~decided; bmask = live & ((eqc <= mdd) | (eqc <= daily_floor))
        if bmask.any():
            uncertain = bmask & ever_high
            if uncertain.any(): ambiguous[uncertain] = True; decided[uncertain] = True; decision_j[uncertain] = j; reason[uncertain] = "BREACH_CLOSE_AFTER_TARGET_INTRABAR_UPPER_BOUND"; freeze(uncertain)
            obvious = bmask & (~ever_high)
            if obvious.any(): breached[obvious] = True; decided[obvious] = True; decision_j[obvious] = j; reason[obvious] = np.where(eqc[obvious] <= mdd[obvious], "MDD_15M_CLOSE_BREACH", "MDL_15M_CLOSE_BREACH"); freeze(obvious)

    results = []
    for k, x in enumerate(sc):
        if passed[k]: label = "ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED"
        elif breached[k]: label = "OBVIOUS_PROXY_BREACH"
        elif ambiguous[k] or ever_high[k] or ever_low[k]:
            label = "AMBIGUITY_MATERIAL"
            if decision_j[k] < 0 and not reason[k]: reason[k] = "INTRABAR_BOUND_TOUCHED_WITHOUT_CONFIRMED_15M_CLOSE_DECISION"
        else: label = "PROXY_INSUFFICIENT_HISTORY_NO_DECISION"
        results.append({**x, "classification": label, "decision_time_utc": iso_j(int(decision_j[k])) if decision_j[k] >= 0 else None, "reason": str(reason[k]), "ending_balance": float(bal[k]), "max_close_drawdown_pct_initial": float(max_close_dd[k]), "max_low_bound_drawdown_pct_initial": float(max_low_dd[k]), "max_daily_close_breach_margin_pct_initial": float(max_daily_margin[k]), "max_single_position_notional_multiple_initial": float(max_single_notional[k] / 100.0), "max_total_open_notional_multiple_initial": float(max_total_notional[k] / 100.0), "max_concurrent_positions": int(max_concurrent[k]), "total_carry_units": float(total_carry[k]), "total_entry_cost_units": float(total_entry_cost[k]), "total_exit_cost_units": float(total_exit_cost[k]), "target_upper_bound_possible": bool(ever_high[k]), "first_target_upper_bound_time_utc": iso_j(int(first_high[k])) if first_high[k] >= 0 else None, "breach_lower_bound_possible": bool(ever_low[k]), "first_breach_lower_bound_time_utc": iso_j(int(first_low[k])) if first_low[k] >= 0 else None})
    return results, event_diag


def classify_carry_group(rs):
    legal = [r for r in rs if r["carry"] == "LEGAL_DAILY"]; support = [r for r in rs if r["carry"] == "SUPPORT_4H"]
    if len(legal) != 1 or len(support) != 240: raise RuntimeError(f"CARRY_GROUP_COUNTS:{len(legal)}:{len(support)}")
    legal = legal[0]; counts = defaultdict(int)
    for r in support: counts[r["classification"]] += 1
    lc = legal["classification"]
    if lc == "ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED" and counts["ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED"] == 240: label = "ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED"
    elif lc == "OBVIOUS_PROXY_BREACH" and counts["OBVIOUS_PROXY_BREACH"] == 240: label = "OBVIOUS_PROXY_BREACH"
    elif lc == "AMBIGUITY_MATERIAL" or counts["AMBIGUITY_MATERIAL"] > 0: label = "AMBIGUITY_MATERIAL"
    elif lc == "PROXY_INSUFFICIENT_HISTORY_NO_DECISION" and counts["PROXY_INSUFFICIENT_HISTORY_NO_DECISION"] == 240: label = "PROXY_INSUFFICIENT_HISTORY_NO_DECISION"
    else: label = "CARRY_OR_SIZING_SENSITIVITY_MATERIAL"
    return label, legal, support, dict(counts)


def summarize(results, source_records, event_diag):
    groups = defaultdict(list)
    for r in results: groups[(r["plan"], r["risk_pct"], r["execution_case"], r["sizing"])].append(r)
    sizing_cells = []
    for key, rs in sorted(groups.items()):
        label, legal, support, counts = classify_carry_group(rs); decision_times = [r["decision_time_utc"] for r in support if r["decision_time_utc"]]
        sizing_cells.append({"plan": key[0], "risk_pct_per_1R": key[1], "execution_case": key[2], "sizing_translation": key[3], "cell_classification": label, "legal_daily": {k: legal[k] for k in ("classification", "decision_time_utc", "reason", "ending_balance", "max_close_drawdown_pct_initial", "max_low_bound_drawdown_pct_initial", "max_total_open_notional_multiple_initial", "max_concurrent_positions", "total_carry_units")}, "support_4h_phase_counts": counts, "support_4h_decision_time_range_utc": [min(decision_times) if decision_times else None, max(decision_times) if decision_times else None]})
    env_groups = defaultdict(list)
    for c in sizing_cells: env_groups[(c["plan"], c["risk_pct_per_1R"], c["execution_case"])].append(c)
    envelope_cells = []
    for key, cs in sorted(env_groups.items()):
        if len(cs) != 2: raise RuntimeError(f"SIZING_ENVELOPE_COUNT:{key}:{len(cs)}")
        labels = [c["cell_classification"] for c in cs]
        if all(x == "ROBUST_PROXY_SURVIVOR_EXACT_REPLAY_STILL_BLOCKED" for x in labels): env = "ROBUST_ACROSS_SIZING_ENVELOPE"
        elif all(x == "OBVIOUS_PROXY_BREACH" for x in labels): env = "OBVIOUS_BREACH_ACROSS_SIZING_ENVELOPE"
        elif any(x == "AMBIGUITY_MATERIAL" for x in labels): env = "AMBIGUITY_MATERIAL"
        elif all(x == "PROXY_INSUFFICIENT_HISTORY_NO_DECISION" for x in labels): env = "PROXY_INSUFFICIENT"
        else: env = "SIZING_SENSITIVITY_MATERIAL"
        envelope_cells.append({"plan": key[0], "risk_pct_per_1R": key[1], "execution_case": key[2], "envelope_classification": env, "sizing_results": {c["sizing_translation"]: c["cell_classification"] for c in cs}})
    sizing_counts = defaultdict(int); envelope_counts = defaultdict(int)
    for c in sizing_cells: sizing_counts[c["cell_classification"]] += 1
    for c in envelope_cells: envelope_counts[c["envelope_classification"]] += 1
    receipt = {"document_id": "PROP_COMPAT_001F_TFG_KRAKEN_PROXY_RECEIPT_V0.1", "campaign_id": "PROP-COMPAT-001F", "status": "TFG_KRAKEN_NON_DECISIONAL_PROXY_COMPLETE", "setup_id": "TFG-DONCHIAN-1D-001", "program": "KRAKEN_PROP", "decisional_authority": False, "official_phase3_risk_grid_run": False, "trade_core_fingerprint": EXPECTED_TRADE_CORE_FP, "source_validation": {"mexc_15m_files_downloaded_and_sha256_validated": len(source_records), "expected_files": 60, "start_utc": "2025-01-01T00:00:00Z", "end_utc_exclusive": "2025-10-11T00:00:00Z", "access_2026": False, "records": source_records}, "execution_event_reconstruction": event_diag, "scenario_paths": len(results), "base_sizing_cells": len(sizing_cells), "sizing_envelope_cells": len(envelope_cells), "sizing_cell_classification_counts": dict(sizing_counts), "envelope_classification_counts": dict(envelope_counts), "sizing_cells": sizing_cells, "envelope_cells": envelope_cells, "governance": {"no_best_plan_selection": True, "no_best_risk_selection": True, "no_best_sizing_translation_selection": True, "post_outcome_tuning": False, "challenge_purchase": False, "live_trading": False, "orders": False, "wallet_use": False, "exchange_mutation": False, "merge_to_main": False}}
    receipt["fingerprint"] = canonical_hash(receipt)
    return receipt


def main(argv):
    if len(argv) != 2: raise SystemExit("usage: runner RECOVERY_ARTIFACT_DIR")
    artifact_dir = Path(argv[1]); OUT.mkdir(parents=True, exist_ok=True)
    rows, manifest, _ = load_authority(artifact_dir); op, hi, lo, cl, source_records = load_price_path(manifest); results, event_diag = simulate(rows, op, hi, lo, cl); receipt = summarize(results, source_records, event_diag)
    out = OUT / "PROP_COMPAT_001F_TFG_KRAKEN_PROXY_RECEIPT_V0.1.json"; out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "scenario_paths": receipt["scenario_paths"], "sizing_cell_classification_counts": receipt["sizing_cell_classification_counts"], "envelope_classification_counts": receipt["envelope_classification_counts"], "event_diag": event_diag, "fingerprint": receipt["fingerprint"]}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
