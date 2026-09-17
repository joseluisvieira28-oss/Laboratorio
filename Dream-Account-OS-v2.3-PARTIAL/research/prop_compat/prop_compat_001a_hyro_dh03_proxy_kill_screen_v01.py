from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import time
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

MIN_MS = 60_000
DAY_MS = 86_400_000
THIRTY_DAYS_MS = 30 * DAY_MS
INITIAL_BALANCE = 100.0
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
RISK_GRID_PCT = [0.10, 0.15, 0.20, 0.25, 0.30]
COST_CASES = {
    "BASE": {"entry_half_pct": 0.10, "exit_half_pct": 0.10},
    "STRESS": {"entry_half_pct": 0.15, "exit_half_pct": 0.15},
}
UA = "PROP-COMPAT-001A DH03-HYRO proxy kill-screen/1.0"


@dataclass
class Trade:
    idx: int
    symbol: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    initial_risk_fraction: float
    exit_reason: str


@dataclass
class Position:
    trade: Trade
    entry_notional: float
    quantity: float
    entry_cost: float
    funding_pnl: float = 0.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_day_key(t_ms: int) -> str:
    return datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).date().isoformat()


def day_start_ms(t_ms: int) -> int:
    d = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc)
    z = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return int(z.timestamp() * 1000)


def get_bytes(url: str, cache_path: Path, expected_sha256: str, retries: int = 5) -> bytes:
    if cache_path.exists():
        b = cache_path.read_bytes()
        if sha256_bytes(b) == expected_sha256:
            return b
        cache_path.unlink()
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                if getattr(r, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {getattr(r, 'status', 'unknown')}")
                b = r.read()
            got = sha256_bytes(b)
            if got != expected_sha256:
                raise RuntimeError(f"SOURCE_VERSION_DRIFT expected={expected_sha256} got={got}")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(b)
            return b
        except Exception as e:
            last = e
            if k + 1 < retries:
                time.sleep(2 ** k)
    raise RuntimeError(f"download failed {url}: {last}")


def parse_binance_zip_rows(zbytes: bytes, expected_member: str):
    with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
        names = zf.namelist()
        if expected_member not in names:
            if len(names) == 1:
                member = names[0]
            else:
                raise RuntimeError(f"expected member {expected_member} not found")
        else:
            member = expected_member
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for row in reader:
                if not row:
                    continue
                try:
                    t = int(row[0])
                except ValueError:
                    continue
                if len(row) < 5:
                    raise RuntimeError(f"short kline row in {member}")
                o = float(row[1]); h = float(row[2]); l = float(row[3]); c = float(row[4])
                if not all(math.isfinite(x) for x in (o, h, l, c)):
                    raise RuntimeError(f"nonfinite price {member}:{t}")
                yield t, o, h, l, c


def load_trades(exec_dir: Path) -> List[Trade]:
    ledger_path = exec_dir / "DH-03-HO1_LEDGER.json"
    expected = "ec4e5dbc8d95a73d4eb9db55f4e1c0f264dba7eb724cbb7424f2c034a3a7eebd"
    got = sha256_file(ledger_path)
    if got != expected:
        raise RuntimeError(f"LEDGER_HASH_MISMATCH expected={expected} got={got}")
    rows = json.loads(ledger_path.read_text())
    if len(rows) != 148:
        raise RuntimeError(f"unexpected selected row count {len(rows)}")
    out = []
    unresolved = 0
    for i, r in enumerate(rows):
        if r.get("execution_path_unresolved"):
            unresolved += 1
            continue
        out.append(Trade(i, str(r["symbol"]), int(r["entry_time"]), int(r["exit_time"]), float(r["entry_price"]), float(r["exit_price"]), float(r["initial_risk_fraction"]), str(r["exit_reason"])))
    if unresolved != 2 or len(out) != 146:
        raise RuntimeError(f"resolved/unresolved mismatch {len(out)}/{unresolved}")
    out.sort(key=lambda x: (x.entry_time, x.symbol, x.idx))
    return out


def merge_intervals(trades: List[Trade]) -> Dict[str, List[Tuple[int, int]]]:
    raw = defaultdict(list)
    for tr in trades:
        raw[tr.symbol].append((tr.entry_time, tr.exit_time))
    merged = {}
    for sym, items in raw.items():
        items.sort(); acc = []
        for a, b in items:
            if not acc or a > acc[-1][1] + MIN_MS:
                acc.append([a, b])
            else:
                acc[-1][1] = max(acc[-1][1], b)
        merged[sym] = [(a, b) for a, b in acc]
    return merged


def required_months(intervals: Dict[str, List[Tuple[int, int]]]) -> Dict[str, set[str]]:
    out = defaultdict(set)
    for sym, ivs in intervals.items():
        for a, b in ivs:
            d = datetime.fromtimestamp(a / 1000, tz=timezone.utc)
            e = datetime.fromtimestamp(b / 1000, tz=timezone.utc)
            y, m = d.year, d.month
            while (y, m) <= (e.year, e.month):
                out[sym].add(f"{y:04d}-{m:02d}")
                if m == 12: y, m = y + 1, 1
                else: m += 1
    return out


def load_price_maps(source_dir: Path, trades: List[Trade], cache_dir: Path):
    gate = json.loads((source_dir / "HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_GATE_V0.1.json").read_text())
    if gate.get("status") != "SOURCE_DATA_PASS": raise RuntimeError("phase5 source gate not PASS")
    if gate.get("source_fingerprint") != "d1a95d51d99eba0bd5f66e91d75ddcd175f7a84d954ba28a44c2dcd39ef4c5cb": raise RuntimeError("source fingerprint mismatch")
    if gate.get("access_2025_performed") or gate.get("access_2026_performed"): raise RuntimeError("locked-year contamination")
    intervals = merge_intervals(trades); months = required_months(intervals)
    recmap = {(r["symbol"], r["month"]): r for r in gate["price_records"]}
    price_maps = {s: {} for s in SYMBOLS}; source_receipts = []
    for sym in SYMBOLS:
        ivs = intervals.get(sym, []); iv_idx = 0; prev_global_t = None
        for m in sorted(months[sym]):
            rec = recmap[(sym, m)]
            b = get_bytes(rec["archive_url"], cache_dir / rec["archive_name"], rec["local_sha256"])
            expected_member = rec["archive_name"].replace(".zip", ".csv")
            row_count = 0; kept = 0; first_t = None; last_t = None
            for t, o, h, l, c in parse_binance_zip_rows(b, expected_member):
                row_count += 1; first_t = t if first_t is None else first_t; last_t = t
                if prev_global_t is not None and t <= prev_global_t: raise RuntimeError(f"nonmonotonic source {sym}:{t}")
                prev_global_t = t
                while iv_idx < len(ivs) and t > ivs[iv_idx][1]: iv_idx += 1
                if iv_idx < len(ivs) and ivs[iv_idx][0] <= t <= ivs[iv_idx][1]:
                    price_maps[sym][t] = (o, c, l); kept += 1
            if row_count != int(rec["row_count"]): raise RuntimeError(f"row count mismatch {sym} {m}")
            source_receipts.append({"symbol":sym,"month":m,"archive_name":rec["archive_name"],"sha256":rec["local_sha256"],"row_count":row_count,"kept_active_window_rows":kept,"first_open_time":first_t,"last_open_time":last_t})
            print(f"PRICE_HASH_PASS {sym} {m} rows={row_count} kept={kept}", flush=True)
    for tr in trades:
        pm = price_maps[tr.symbol]; t = tr.entry_time
        while t <= tr.exit_time:
            if t not in pm: raise RuntimeError(f"MISSING_REQUIRED_1M_MARK:{tr.symbol}:{t}")
            t += MIN_MS
    return price_maps, source_receipts, gate


def load_funding(source_dir: Path):
    gate = json.loads((source_dir / "HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_GATE_V0.1.json").read_text()); out = {}
    for sym in SYMBOLS:
        p = source_dir / "canonical_funding" / f"{sym}_funding.csv"
        if sha256_file(p) != gate["audits"][sym]["canonical_funding_sha256"]: raise RuntimeError(f"FUNDING_HASH_MISMATCH:{sym}")
        arr = []
        with p.open(newline="") as f:
            r = csv.DictReader(f); prev = None
            for x in r:
                t = int(x["funding_time_ms"]); rate = float(x["funding_rate"])
                if prev is not None and t <= prev: raise RuntimeError(f"nonmonotonic funding {sym}")
                prev = t; arr.append((t, rate))
        if len(arr) != gate["audits"][sym]["funding_event_count"]: raise RuntimeError(f"funding count mismatch {sym}")
        out[sym] = arr
    return out


def build_event_maps(trades: List[Trade], funding_by_symbol):
    entries = defaultdict(list); exits = defaultdict(list); by_symbol = defaultdict(list)
    for tr in trades:
        entries[tr.entry_time].append(tr); exits[tr.exit_time].append(tr); by_symbol[tr.symbol].append(tr)
    funding_minute = defaultdict(list)
    for sym in SYMBOLS:
        trs = sorted(by_symbol[sym], key=lambda x: x.entry_time); starts = [x.entry_time for x in trs]
        for ft, rate in funding_by_symbol[sym]:
            i = bisect.bisect_left(starts, ft) - 1
            if i >= 0 and trs[i].entry_time < ft < trs[i].exit_time:
                funding_minute[(ft // MIN_MS) * MIN_MS].append((ft, sym, rate, trs[i].idx))
    return entries, exits, funding_minute


def position_unrealized(pos: Position, mark: float) -> float:
    return pos.quantity * (mark - pos.trade.entry_price)


def marked_equity(balance: float, positions: Dict[str, Position], price_maps, t: int, field: str) -> float:
    j = 0 if field == "open" else 1; eq = balance
    for sym, pos in positions.items(): eq += position_unrealized(pos, price_maps[sym][t][j])
    return eq


def evaluate_cell(trades, price_maps, funding_map, entries, exits, risk_pct: float, cost_case: str):
    risk_frac = risk_pct / 100.0; cc = COST_CASES[cost_case]
    entry_cost_frac = cc["entry_half_pct"] / 100.0; exit_cost_frac = cc["exit_half_pct"] / 100.0
    balance = INITIAL_BALANCE; positions = {}; entry_day_opened = defaultdict(int); closed = []; daily_realized = defaultdict(float); qualifying_days = set()
    last_close_time = None; activation_time = None; daily_floor = None; daily_start_equity = None; current_day = None
    status = "ACTIVE"; decision = None; decision_time = None; breach_reason = None; source_error = None
    min_equity = INITIAL_BALANCE; max_float_dd = 0.0; max_daily_dd_amt = 0.0; max_open_notional_mult = 0.0; max_margin_pct = 0.0; max_concurrent = 0
    max_balance = balance; max_balance_dd = 0.0; funding_event_count = 0; total_funding_pnl = 0.0; total_entry_cost = 0.0; total_exit_cost = 0.0; total_price_pnl = 0.0
    first_entry = min(x.entry_time for x in trades); t = day_start_ms(first_entry); end_t = int(datetime(2024,12,31,23,59,tzinfo=timezone.utc).timestamp()*1000)

    def add_realized(ts, cash):
        nonlocal balance, max_balance, max_balance_dd
        balance += cash; daily_realized[utc_day_key(ts)] += cash; max_balance = max(max_balance, balance); max_balance_dd = max(max_balance_dd, (max_balance-balance)/INITIAL_BALANCE*100.0)
    def record_equity(eq):
        nonlocal min_equity, max_float_dd, max_daily_dd_amt
        min_equity = min(min_equity, eq); max_float_dd = max(max_float_dd, (INITIAL_BALANCE-eq)/INITIAL_BALANCE*100.0)
        if daily_start_equity is not None: max_daily_dd_amt = max(max_daily_dd_amt, daily_start_equity-eq)
    def breach(eq, ts, phase):
        nonlocal status, decision, decision_time, breach_reason
        if daily_floor is not None and eq <= daily_floor + 1e-12:
            status="BREACH"; decision="OBVIOUS_PROXY_BREACH"; decision_time=ts; breach_reason=f"DAILY_DRAWDOWN_{phase}"; return True
        if eq <= 94.0 + 1e-12:
            status="BREACH"; decision="OBVIOUS_PROXY_BREACH"; decision_time=ts; breach_reason=f"MAXIMUM_LOSS_{phase}"; return True
        return False
    def update_qualifying(day):
        if entry_day_opened.get(day,0)<=0: return
        for rec in closed:
            if rec["exit_day"]==day and rec["entry_notional"]+1e-12>=5.0 and abs(rec["trade_net_pnl"])+1e-12>=0.01*rec["entry_notional"]:
                qualifying_days.add(day); return
    def pass_check(ts):
        nonlocal status, decision, decision_time
        profit = balance-INITIAL_BALANCE; best=max([v for v in daily_realized.values() if v>0], default=0.0); ratio=(best/profit if profit>0 else None)
        if profit+1e-12>=10.0 and len(qualifying_days)>=5 and ratio is not None and ratio<=0.40+1e-12:
            status="PASS"; decision="NO_OBVIOUS_PROXY_BREACH_BUT_EXACT_REPLAY_STILL_BLOCKED"; decision_time=ts; return True
        return False

    while t<=end_t and status=="ACTIVE":
        day=utc_day_key(t)
        if day!=current_day:
            current_day=day
            try: daily_start_equity = INITIAL_BALANCE if activation_time is None else marked_equity(balance,positions,price_maps,t,"open")
            except Exception as e: status="INSUFFICIENT"; decision="PROXY_INSUFFICIENT"; decision_time=t; source_error=str(e); break
            daily_floor=daily_start_equity-4.0; record_equity(daily_start_equity)
            if activation_time is not None and breach(daily_start_equity,t,"DAY_START_OPEN"): break
        if activation_time is not None:
            ref=last_close_time if last_close_time is not None else activation_time
            if t-ref>THIRTY_DAYS_MS:
                status="BREACH"; decision="OBVIOUS_PROXY_BREACH"; decision_time=t; breach_reason="INACTIVITY_OVER_30_DAYS"; break
        syms=set(positions)|{x.symbol for x in entries.get(t,[])}|{x.symbol for x in exits.get(t,[])}|{x[1] for x in funding_map.get(t,[])}
        if any(t not in price_maps[s] for s in syms):
            status="INSUFFICIENT"; decision="PROXY_INSUFFICIENT"; decision_time=t; source_error=f"missing required price at {t}"; break
        for tr in exits.get(t,[]):
            pos=positions.get(tr.symbol)
            if pos is None or pos.trade.idx!=tr.idx: status="INSUFFICIENT"; decision="PROXY_INSUFFICIENT"; decision_time=t; source_error=f"exit mismatch {tr.symbol}:{tr.idx}"; break
            price_pnl=pos.quantity*(tr.exit_price-tr.entry_price); exit_cost=exit_cost_frac*pos.entry_notional; add_realized(t,price_pnl-exit_cost)
            total_price_pnl+=price_pnl; total_exit_cost+=exit_cost
            trade_net=price_pnl+pos.funding_pnl-pos.entry_cost-exit_cost
            closed.append({"trade_idx":tr.idx,"symbol":tr.symbol,"exit_day":day,"entry_notional":pos.entry_notional,"trade_net_pnl":trade_net})
            del positions[tr.symbol]; last_close_time=t
        if status!="ACTIVE": break
        pre_eq=marked_equity(balance,positions,price_maps,t,"open") if positions else balance; record_equity(pre_eq)
        if activation_time is not None and breach(pre_eq,t,"POST_EXIT_OPEN"): break
        batch=entries.get(t,[])
        if batch:
            if activation_time is None: activation_time=t; daily_start_equity=INITIAL_BALANCE; daily_floor=96.0
            common_snapshot=pre_eq; entry_day_opened[day]+=len(batch)
            for tr in batch:
                if tr.symbol in positions: status="INSUFFICIENT"; decision="PROXY_INSUFFICIENT"; decision_time=t; source_error=f"pyramiding {tr.symbol}"; break
                risk_amount=common_snapshot*risk_frac; notional=risk_amount/tr.initial_risk_fraction; qty=notional/tr.entry_price; ec=entry_cost_frac*notional
                positions[tr.symbol]=Position(tr,notional,qty,ec); add_realized(t,-ec); total_entry_cost+=ec
            if status!="ACTIVE": break
            eq=marked_equity(balance,positions,price_maps,t,"open"); record_equity(eq)
            if breach(eq,t,"POST_ENTRY_COST_OPEN"): break
        for ft,sym,rate,trade_idx in funding_map.get(t,[]):
            pos=positions.get(sym)
            if pos is None or pos.trade.idx!=trade_idx or not(pos.trade.entry_time<ft<pos.trade.exit_time): continue
            current_notional=abs(pos.quantity*price_maps[sym][t][0]); cash=-rate*current_notional; pos.funding_pnl+=cash; add_realized(ft,cash); total_funding_pnl+=cash; funding_event_count+=1
            eq=marked_equity(balance,positions,price_maps,t,"open"); record_equity(eq)
            if breach(eq,t,"POST_FUNDING_OPEN"): break
        if status!="ACTIVE": break
        update_qualifying(day)
        if pass_check(t): break
        eq_close=marked_equity(balance,positions,price_maps,t,"close") if positions else balance; record_equity(eq_close)
        if activation_time is not None and breach(eq_close,t,"MINUTE_CLOSE"): break
        if exits.get(t):
            ids={x.idx for x in exits[t]}
            if any(r["trade_idx"] in ids and r["trade_net_pnl"]<-3.0-1e-12 for r in closed):
                status="BREACH"; decision="OBVIOUS_PROXY_BREACH"; decision_time=t; breach_reason="SINGLE_POSITION_REALIZED_LOSS_OVER_3PCT"; break
        if positions:
            total_notional=sum(abs(pos.quantity*price_maps[sym][t][1]) for sym,pos in positions.items()); max_open_notional_mult=max(max_open_notional_mult,total_notional/INITIAL_BALANCE); max_margin_pct=max(max_margin_pct,(total_notional/10.0)/INITIAL_BALANCE*100.0); max_concurrent=max(max_concurrent,len(positions))
        t+=MIN_MS
    if decision is None:
        decision="PROXY_INSUFFICIENT"; decision_time=min(t,end_t); status="INSUFFICIENT"; source_error=source_error or "history ended without qualifying pass or mandatory breach"
    for d in set(entry_day_opened): update_qualifying(d)
    profit=balance-INITIAL_BALANCE; best=max([v for v in daily_realized.values() if v>0], default=0.0); ratio=(best/profit if profit>0 else None)
    corr={str(n):{"full_R_loss_pct_initial":n*risk_pct,"below_4pct_daily_amount":n*risk_pct<4.0,"below_6pct_max_loss_amount":n*risk_pct<6.0} for n in (2,3,4,6)}
    return {"risk_pct_equity_per_1R":risk_pct,"cost_case":cost_case,"classification":decision,"status":status,"decision_time_utc":datetime.fromtimestamp(decision_time/1000,tz=timezone.utc).isoformat(),"breach_reason":breach_reason,"source_error":source_error,"ending_balance":balance,"net_realized_profit":profit,"min_equity":min_equity,"max_floating_drawdown_pct_initial":max_float_dd,"max_daily_drawdown_pct_initial":max_daily_dd_amt/INITIAL_BALANCE*100.0,"max_balance_drawdown_pct_initial":max_balance_dd,"qualifying_trading_days":len(qualifying_days),"qualifying_day_list":sorted(qualifying_days),"best_positive_realized_day":best,"consistency_ratio_best_day_over_net_profit":ratio,"closed_trades_before_decision":len(closed),"funding_event_count":funding_event_count,"total_funding_pnl":total_funding_pnl,"total_entry_cost":total_entry_cost,"total_exit_cost":total_exit_cost,"total_price_pnl":total_price_pnl,"max_concurrent_positions":max_concurrent,"funded_structural_diagnostics":{"max_open_notional_multiple_initial":max_open_notional_mult,"max_margin_pct_initial_at_10x":max_margin_pct,"notional_limit_2x_exceeded":max_open_notional_mult>2.0+1e-12,"margin_limit_25pct_exceeded_at_10x":max_margin_pct>25.0+1e-12,"decisional_authority":False},"correlation_stress_nominal":corr}


def self_test():
    tr=Trade(0,"BTCUSDT",0,60_000,100.0,90.0,0.10,"STOP"); p=Position(tr,1.0,0.01,0.001)
    assert abs(position_unrealized(p,110.0)-0.1)<1e-12; assert day_start_ms(86_400_000+1234)==86_400_000; assert utc_day_key(0)=="1970-01-01"; print("SELF_TEST_PASS")


def canonical_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--execution-dir",type=Path); ap.add_argument("--source-dir",type=Path); ap.add_argument("--cache-dir",type=Path,default=Path(".cache/prop_compat_001a")); ap.add_argument("--output-dir",type=Path,default=Path("research/local_data/prop_compat_001a_hyro_dh03_proxy")); ap.add_argument("--self-test",action="store_true"); args=ap.parse_args()
    if args.self_test: self_test(); return 0
    if args.execution_dir is None or args.source_dir is None: raise SystemExit("--execution-dir and --source-dir required")
    trades=load_trades(args.execution_dir); price_maps,source_receipts,gate=load_price_maps(args.source_dir,trades,args.cache_dir); funding=load_funding(args.source_dir); entries,exits,funding_map=build_event_maps(trades,funding)
    results=[]
    for risk in RISK_GRID_PCT:
        for cost in ("BASE","STRESS"):
            print(f"RUN_CELL risk={risk:.2f}% cost={cost}",flush=True); r=evaluate_cell(trades,price_maps,funding_map,entries,exits,risk,cost); results.append(r); print("CELL_RESULT",json.dumps(r,sort_keys=True),flush=True)
    out={"campaign_id":"PROP-COMPAT-001A","setup_id":"DH-03-HO1","prop_program":"HYROTRADER_ONE_STEP_SWING_CLEO","status":"PROXY_KILL_SCREEN_COMPLETE","decisional_authority":False,"official_prop_compat_phase3_risk_grid_run":False,"proxy_grid_values_pct_equity_per_1R":RISK_GRID_PCT,"ledger_sha256":"ec4e5dbc8d95a73d4eb9db55f4e1c0f264dba7eb724cbb7424f2c034a3a7eebd","source_fingerprint":gate["source_fingerprint"],"resolved_trade_count":len(trades),"downloaded_archive_count":len(source_receipts),"downloaded_archives":source_receipts,"results":results,"labels_count":dict(sorted({k:sum(x["classification"]==k for x in results) for k in {x["classification"] for x in results}}.items())),"governance":{"proxy_only":True,"no_best_risk_selection":True,"setup_rules_changed":False,"symbol_drops":False,"post_outcome_tuning":False,"challenge_purchase":False,"live_trading":False,"merge_to_main":False,"access_2025":False,"access_2026":False}}
    out["fingerprint"]=canonical_hash(out); args.output_dir.mkdir(parents=True,exist_ok=True); p=args.output_dir/"PROP_COMPAT_001A_HYRO_DH03_PROXY_KILL_SCREEN_RECEIPT_V0.1.json"; p.write_text(json.dumps(out,indent=2,sort_keys=True)); print("RECEIPT",p,out["fingerprint"],flush=True); return 0


if __name__=="__main__": raise SystemExit(main())
