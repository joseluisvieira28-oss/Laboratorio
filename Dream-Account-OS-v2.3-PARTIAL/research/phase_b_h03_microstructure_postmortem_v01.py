from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import csv, hashlib, json, random, sys, zipfile
from io import BytesIO, TextIOWrapper
from math import isfinite
from pathlib import Path
from statistics import mean, median
from typing import Any

from research.phase_b_h03_binance_daily_manifest_v01 import EXPECTED_ARCHIVE_COUNT, expected_h03_daily_objects
from research.phase_b_h03_binance_offline_adapter_v01 import EXPECTED_FIELDS, TIMEFRAME_MS, adapt_binance_daily_archive_bytes
from research.phase_b_h03_discovery_runner_v01 import BASE_COSTS, PARAMETERS
from research.phase_b_h03_research_evaluator_v01 import evaluate_h03_universe

FREEZE_PATH = Path(__file__).with_name("PHASE_B_H03_MICROSTRUCTURE_POSTMORTEM_FREEZE_V0.1.json")
EXPECTED_FREEZE_FINGERPRINT = "192ff38c80df052520969e801de88433dc98b7a1dba31d6cd32dccc7644cce61"
EXPECTED_ARCHIVE_SET_FINGERPRINT = "82f72e6c6b480579296c7c7e996e627c0d0b0971dd6b52700eadb5e682e46040"
EXPECTED_DISCOVERY_RECEIPT_FINGERPRINT = "14a4bc14a6d95f9c812d697a41fae1079fa222267fe8b650ff99ff93b9edb299"
EXPECTED_RESOLVED = 151
LOOKBACK = 96
REPS = 5000
SEED = 230911
CONFIDENCE = 0.95

@dataclass(frozen=True)
class FlowBar:
    open_time: int
    volume: float
    trades: int
    taker_buy_base: float
    @property
    def imbalance(self) -> float:
        if self.volume <= 0:
            raise ValueError("zero volume")
        x = (2.0 * self.taker_buy_base - self.volume) / self.volume
        if not isfinite(x) or x < -1.000000000001 or x > 1.000000000001:
            raise ValueError("invalid flow imbalance")
        return max(-1.0, min(1.0, x))
    @property
    def avg_size(self) -> float:
        if self.trades <= 0:
            raise ValueError("non-positive trade count")
        return self.volume / self.trades

def _hash(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def _freeze() -> dict[str, Any]:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    unsigned = dict(raw); supplied = unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_FREEZE_FINGERPRINT or _hash(unsigned) != supplied:
        raise PermissionError("freeze fingerprint mismatch")
    if raw["status"] != "FROZEN_POSTHOC_HYPOTHESIS_GENERATION_ONLY":
        raise PermissionError("freeze status mismatch")
    dc = raw["data_contract"]
    if not dc["same_h03_corpus_only"] or not dc["reacquisition_for_reproducible_postmortem_authorized"]:
        raise PermissionError("same-corpus authorization missing")
    if dc["new_market_period_authorized"] or dc["mexc_2025_09_through_2025_12_authorized"] or dc["holdout_2026_authorized"]:
        raise PermissionError("holdout/new-period guard drift")
    if any(raw["governance"][k] for k in ("live_trading_authorized","exchange_mutation_authorized","main_merge_authorized","render_deploy_authorized")):
        raise PermissionError("governance guard drift")
    return raw

def _parse_flow(raw_bytes: bytes, filename: str) -> tuple[FlowBar, ...]:
    member = filename[:-4] + ".csv"
    out = []
    with zipfile.ZipFile(BytesIO(raw_bytes)) as zf:
        infos = zf.infolist()
        if len(infos) != 1 or infos[0].filename != member:
            raise ValueError("unexpected zip member")
        with zf.open(infos[0]) as binary:
            reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            first = True
            for row in reader:
                if not row or all(not c.strip() for c in row):
                    continue
                if first:
                    norm = tuple(c.strip().lower().replace(" ", "_") for c in row)
                    if norm and norm[0] == "open_time":
                        first = False
                        continue
                first = False
                if len(row) != EXPECTED_FIELDS:
                    raise ValueError("field count mismatch")
                ot, vol, trades, tb = int(row[0]), float(row[5]), int(row[8]), float(row[9])
                if not isfinite(vol) or not isfinite(tb) or vol < 0 or trades < 0 or tb < -1e-12 or tb > vol + max(1e-12, abs(vol)*1e-10):
                    raise ValueError("invalid flow fields")
                out.append(FlowBar(ot, vol, trades, tb))
    return tuple(out)

def _ratio(v: float, b: float) -> float:
    if b <= 0 or not isfinite(b): raise ValueError("invalid baseline")
    x = v / b
    if not isfinite(x): raise ValueError("non-finite ratio")
    return x

def _bundle(flow: dict[int, FlowBar], times: list[int], idxmap: dict[int, int], t: int) -> dict[str, float]:
    i = idxmap[t]
    if i < LOOKBACK: raise ValueError("insufficient history")
    prev_t = times[i-LOOKBACK:i]
    if prev_t[0] != t-LOOKBACK*TIMEFRAME_MS or prev_t[-1] != t-TIMEFRAME_MS or any(b-a != TIMEFRAME_MS for a,b in zip(prev_t,prev_t[1:])):
        raise ValueError("non-contiguous 96-bar baseline")
    target = flow[t]; prev = [flow[x] for x in prev_t]
    if target.volume <= 0 or target.trades <= 0 or any(x.volume <= 0 or x.trades <= 0 for x in prev):
        raise ValueError("zero-activity flow bar")
    return {
        "flow_imbalance": target.imbalance,
        "volume_shock": _ratio(target.volume, median(x.volume for x in prev)),
        "trade_count_shock": _ratio(float(target.trades), float(median(x.trades for x in prev))),
        "avg_trade_size_shock": _ratio(target.avg_size, median(x.avg_size for x in prev)),
    }

def _rate_diff(rows):
    p=[r for r in rows if r["flow_persistent"]]; n=[r for r in rows if not r["flow_persistent"]]
    if not p or not n: return None
    return mean(float(r["tp1_reached"]) for r in p)-mean(float(r["tp1_reached"]) for r in n)

def _q(vals, q):
    s=sorted(vals); pos=q*(len(s)-1); lo=int(pos); hi=min(lo+1,len(s)-1); f=pos-lo
    return s[lo]*(1-f)+s[hi]*f

def _bootstrap(rows):
    by={}
    for r in rows: by.setdefault(r["entry_day_utc"], []).append(r)
    days=sorted(by); point=_rate_diff(rows); rng=random.Random(SEED); vals=[]
    if point is not None:
        for _ in range(REPS):
            sample=[]
            for _ in days: sample.extend(by[rng.choice(days)])
            d=_rate_diff(sample)
            if d is not None: vals.append(d)
    a=1-CONFIDENCE
    return {"method":"UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP_OF_TP1_RATE_DIFFERENCE","repetitions":REPS,"valid_repetitions":len(vals),"sample_days":len(days),"seed":SEED,"confidence":CONFIDENCE,"point_estimate":point,"lower":_q(vals,a/2) if vals else None,"upper":_q(vals,1-a/2) if vals else None}

def _odds(rows):
    a=sum(r["flow_persistent"] and r["tp1_reached"] for r in rows)
    b=sum(r["flow_persistent"] and not r["tp1_reached"] for r in rows)
    c=sum((not r["flow_persistent"]) and r["tp1_reached"] for r in rows)
    d=sum((not r["flow_persistent"]) and (not r["tp1_reached"]) for r in rows)
    corr=0 in (a,b,c,d)
    o=((a+.5)*(d+.5))/((b+.5)*(c+.5)) if corr else (a*d)/(b*c)
    return {"tp1_and_persistent":a,"failed_and_persistent":b,"tp1_and_nonpersistent":c,"failed_and_nonpersistent":d,"odds_ratio":o,"haldane_anscombe_correction_used":corr}

def _summary(rows, field):
    y=[float(r[field]) for r in rows if r["tp1_reached"]]; n=[float(r[field]) for r in rows if not r["tp1_reached"]]
    return {"tp1_reached":{"n":len(y),"mean":mean(y),"median":median(y)},"tp1_not_reached":{"n":len(n),"mean":mean(n),"median":median(n)},"mean_difference_tp1_minus_failed":mean(y)-mean(n)}

def run(raw_root: Path, output: Path) -> dict[str, Any]:
    fr=_freeze(); objects=expected_h03_daily_objects()
    if len(objects) != EXPECTED_ARCHIVE_COUNT: raise RuntimeError("manifest cardinality drift")
    candles={s:[] for s in fr["data_contract"]["symbols"]}; flows={s:{} for s in candles}; shas={}
    for item in objects:
        s=item["symbol"]; ap=raw_root/s/item["archive_filename"]; cp=raw_root/s/(item["archive_filename"]+".CHECKSUM")
        if not ap.is_file() or not cp.is_file(): raise FileNotFoundError(str(ap))
        rb=ap.read_bytes(); ct=cp.read_text(encoding="utf-8")
        adapted=adapt_binance_daily_archive_bytes(symbol=s,day=item["date_utc"],archive_filename=item["archive_filename"],archive_bytes=rb,checksum_text=ct)
        if not adapted.status.startswith("PASS_BINANCE_DAILY"): raise RuntimeError(f"integrity block {s} {item['date_utc']}")
        candles[s].extend(adapted.candles); shas[f"{s}/{item['archive_filename']}"]=adapted.archive_sha256
        for bar in _parse_flow(rb,item["archive_filename"]):
            if bar.open_time in flows[s]: raise ValueError("duplicate flow timestamp")
            flows[s][bar.open_time]=bar
    afp=_hash(shas)
    if afp != EXPECTED_ARCHIVE_SET_FINGERPRINT: raise PermissionError("archive set mismatch")
    records,metrics,_=evaluate_h03_universe(candles,PARAMETERS,BASE_COSTS)
    resolved=[r for r in records if r.outcome.net_r is not None]
    if len(resolved) != EXPECTED_RESOLVED: raise RuntimeError("resolved-trade reproduction mismatch")
    cache={s:(sorted(v),{}) for s,v in flows.items()}
    cache={s:(ts,{t:i for i,t in enumerate(ts)}) for s,(ts,_) in cache.items()}
    rows=[]
    for r in resolved:
        ts,im=cache[r.symbol]
        b=_bundle(flows[r.symbol],ts,im,r.signal.breakout_open_time)
        x=_bundle(flows[r.symbol],ts,im,r.signal.retest_open_time)
        rows.append({
            "entry_day_utc":datetime.fromtimestamp(r.signal.entry_open_time/1000,tz=timezone.utc).date().isoformat(),
            "tp1_reached":bool(r.outcome.tp1_reached),
            "flow_persistent":b["flow_imbalance"]>0 and x["flow_imbalance"]>0,
            "breakout_flow_imbalance":b["flow_imbalance"],
            "retest_flow_imbalance":x["flow_imbalance"],
            "retest_minus_breakout_flow_imbalance":x["flow_imbalance"]-b["flow_imbalance"],
            "breakout_volume_shock_vs_prior_96_bar_median":b["volume_shock"],
            "retest_volume_shock_vs_prior_96_bar_median":x["volume_shock"],
            "breakout_trade_count_shock_vs_prior_96_bar_median":b["trade_count_shock"],
            "retest_trade_count_shock_vs_prior_96_bar_median":x["trade_count_shock"],
            "breakout_avg_trade_size_shock_vs_prior_96_bar_median":b["avg_trade_size_shock"],
            "retest_avg_trade_size_shock_vs_prior_96_bar_median":x["avg_trade_size_shock"],
        })
    p=[r for r in rows if r["flow_persistent"]]; n=[r for r in rows if not r["flow_persistent"]]
    primary={"n_total":len(rows),"n_persistent":len(p),"n_nonpersistent":len(n),"tp1_rate_persistent":mean(float(r["tp1_reached"]) for r in p) if p else None,"tp1_rate_nonpersistent":mean(float(r["tp1_reached"]) for r in n) if n else None,"tp1_rate_difference":_rate_diff(rows),"odds_table":_odds(rows)}
    secondary={f:_summary(rows,f) for f in fr["secondary_descriptive_features"]["features"]}
    body={
        "document_type":"PHASE_B_H03_MICROSTRUCTURE_POSTMORTEM_RECEIPT",
        "version":"0.1","status":"POSTHOC_DIAGNOSTIC_COMPLETE",
        "authority":"HYPOTHESIS_GENERATION_ONLY_NO_CLASSIFICATION_AUTHORITY",
        "freeze_fingerprint":EXPECTED_FREEZE_FINGERPRINT,
        "h03_discovery_receipt_fingerprint":EXPECTED_DISCOVERY_RECEIPT_FINGERPRINT,
        "archive_set_fingerprint":afp,
        "h03_reproduction":{"resolved_trade_count":metrics.resolved_trade_count,"net_expectancy_r":metrics.net_expectancy_r,"profit_factor_r":metrics.profit_factor_r,"tp1_reach_rate":metrics.tp1_reach_rate},
        "primary_feature":fr["primary_feature"],"primary_diagnostic":primary,"bootstrap":_bootstrap(rows),"secondary_descriptive":secondary,
        "guards":{"no_threshold_search_performed":True,"no_symbol_subgroup_search_performed":True,"no_time_subgroup_search_performed":True,"h03_reclassified":False,"h03_rescued":False,"mexc_validation_2025_accessed":False,"holdout_2026_accessed":False,"network_access_performed_by_module":False,"exchange_mutation_performed":False,"live_trading_performed":False},
    }
    body["fingerprint"]=_hash(body)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return body

def main(argv=None):
    a=list(sys.argv[1:] if argv is None else argv)
    if len(a)!=2: return 2
    try: receipt=run(Path(a[0]),Path(a[1]))
    except Exception as exc:
        print(f"H03_FLOW_POSTMORTEM_FATAL: {type(exc).__name__}: {exc}"); return 2
    print(json.dumps(receipt,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
