from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from io import TextIOWrapper
from pathlib import Path
from statistics import mean, median
import zipfile
from zoneinfo import ZoneInfo

FREEZE_PATH = Path(__file__).with_name("NEWS_SHOCK_LAB_V01_CPI_NFP_REPLICATION_FREEZE.json")
EXPECTED_FREEZE_FINGERPRINT = "55bba04ab42e1c457427a9ba87231c6ff4df52e9f0e083e320700618c38b2f70"
NY = ZoneInfo("America/New_York")
ONE_MIN_MS = 60_000
SYMBOLS = ("BTCUSDT", "ETHUSDT")
POST_WINDOWS = (5, 15, 30, 60, 120)
PRE_WINDOWS = (5, 15, 60)
CONTROL_LAGS = (7, 14, 21, 28)


@dataclass(frozen=True)
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int
    taker_buy_base: float


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_freeze() -> dict:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_FREEZE_FINGERPRINT or canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.1 freeze fingerprint mismatch")
    guards = raw["governance"]
    if guards["no_2026"] is not True or guards["mexc_2025_09_through_2025_12_untouched"] is not True:
        raise PermissionError("holdout guard drift")
    return raw


def load_manifest(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if canonical_hash(unsigned) != supplied:
        raise PermissionError("BLS manifest fingerprint mismatch")
    if raw.get("status") != "OFFICIAL_BLS_SCHEDULE_MANIFEST_COMPLETE":
        raise PermissionError("BLS manifest status mismatch")
    if raw.get("freeze_fingerprint") != EXPECTED_FREEZE_FINGERPRINT:
        raise PermissionError("BLS manifest freeze binding mismatch")
    if raw.get("event_counts") != {"CPI": 56, "NFP": 56} or raw.get("event_count_total") != 112:
        raise PermissionError("BLS manifest cardinality mismatch")
    if raw.get("guards", {}).get("market_data_accessed") is not False:
        raise PermissionError("BLS manifest provenance guard mismatch")
    if any(e["event_date"].startswith("2026-") for e in raw["events"]):
        raise PermissionError("2026 event in manifest")
    return raw


def norm_ts(value: int) -> int:
    return value // 1000 if abs(value) >= 100_000_000_000_000 else value


def parse_checksum(text: str, filename: str) -> str:
    parts = text.strip().split()
    if len(parts) < 2:
        raise ValueError("invalid checksum")
    digest = parts[0].lower()
    fname = parts[-1].lstrip("*")
    if fname != filename or len(digest) != 64:
        raise ValueError("checksum filename/format mismatch")
    return digest


def parse_day(root: Path, symbol: str, day: str) -> dict[int, Bar]:
    filename = f"{symbol}-1m-{day}.zip"
    zip_path = root / symbol / filename
    checksum_path = root / symbol / (filename + ".CHECKSUM")
    raw = zip_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != parse_checksum(checksum_path.read_text(encoding="utf-8"), filename):
        raise ValueError(f"checksum mismatch {symbol} {day}")
    member = filename[:-4] + ".csv"
    out: dict[int, Bar] = {}
    with zipfile.ZipFile(zip_path) as zf:
        if zf.namelist() != [member]:
            raise ValueError(f"zip member mismatch {symbol} {day}")
        with zf.open(member) as binary:
            reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            for row in reader:
                if not row or not row[0].strip().lstrip("-").isdigit():
                    continue
                if len(row) != 12:
                    raise ValueError("field count")
                open_time = norm_ts(int(row[0]))
                op, hi, lo, cl, volume = map(float, row[1:6])
                trades = int(row[8])
                taker_buy = float(row[9])
                if open_time % ONE_MIN_MS != 0:
                    raise ValueError(f"timestamp alignment {symbol} {day}")
                if not all(math.isfinite(x) for x in (op, hi, lo, cl, volume, taker_buy)):
                    raise ValueError("nonfinite row")
                if min(op, hi, lo, cl) <= 0 or volume < 0 or trades < 0 or taker_buy < 0:
                    raise ValueError("invalid values")
                if taker_buy > volume + max(1e-12, abs(volume) * 1e-10):
                    raise ValueError("taker buy exceeds volume")
                if open_time in out:
                    raise ValueError("duplicate open time")
                out[open_time] = Bar(open_time, op, hi, lo, cl, volume, trades, taker_buy)
    return out


def sign(value: float | None, eps: float = 1e-15) -> int:
    if value is None:
        return 0
    return 1 if value > eps else (-1 if value < -eps else 0)


def ret(start_price: float, end_price: float) -> float:
    return end_price / start_price - 1.0


def aggregate_flow(bars: list[Bar]) -> float | None:
    total = sum(b.volume for b in bars)
    if total <= 0:
        return None
    taker = sum(b.taker_buy_base for b in bars)
    return (2.0 * taker - total) / total


def event_ts_ms(event_date: str) -> int:
    d = date.fromisoformat(event_date)
    local = datetime(d.year, d.month, d.day, 8, 30, tzinfo=NY)
    return int(local.astimezone(timezone.utc).timestamp() * 1000)


def control_ts_ms(control_date: date) -> int:
    local = datetime(control_date.year, control_date.month, control_date.day, 8, 30, tzinfo=NY)
    return int(local.astimezone(timezone.utc).timestamp() * 1000)


def event_metrics(series: dict[int, Bar], ts: int) -> dict:
    if ts not in series:
        raise ValueError("event minute missing")
    base = series[ts].open
    out: dict[str, object] = {}
    for horizon in POST_WINDOWS:
        endpoint = ts + horizon * ONE_MIN_MS
        if endpoint not in series:
            raise ValueError(f"post endpoint missing {horizon}")
        window: list[Bar] = []
        for i in range(horizon):
            key = ts + i * ONE_MIN_MS
            if key not in series:
                raise ValueError(f"post window gap {horizon}")
            window.append(series[key])
        cumulative = ret(base, series[endpoint].open)
        out[f"ret_{horizon}m"] = cumulative
        out[f"abs_ret_{horizon}m"] = abs(cumulative)
        out[f"volume_{horizon}m"] = sum(b.volume for b in window)
        out[f"trades_{horizon}m"] = sum(b.trades for b in window)
        out[f"flow_{horizon}m"] = aggregate_flow(window)
    for horizon in PRE_WINDOWS:
        start = ts - horizon * ONE_MIN_MS
        if start not in series:
            raise ValueError(f"pre endpoint missing {horizon}")
        out[f"pre_ret_{horizon}m"] = ret(series[start].open, base)
    for a, b in ((5, 15), (15, 60), (15, 120)):
        start = ts + a * ONE_MIN_MS
        end = ts + b * ONE_MIN_MS
        out[f"incremental_ret_{a}_{b}m"] = ret(series[start].open, series[end].open)
    out["continuation_5_to_15"] = (
        sign(out["ret_5m"]) != 0
        and sign(out["incremental_ret_5_15m"]) == sign(out["ret_5m"])
    )
    out["continuation_15_to_60"] = (
        sign(out["ret_15m"]) != 0
        and sign(out["incremental_ret_15_60m"]) == sign(out["ret_15m"])
    )
    out["continuation_15_to_120"] = (
        sign(out["ret_15m"]) != 0
        and sign(out["incremental_ret_15_120m"]) == sign(out["ret_15m"])
    )
    out["reversal_5_60"] = sign(out["ret_5m"]) * sign(out["ret_60m"]) == -1
    out["reversal_15_120"] = sign(out["ret_15m"]) * sign(out["ret_120m"]) == -1
    out["flow_align_5m"] = sign(out["ret_5m"]) != 0 and sign(out["flow_5m"]) == sign(out["ret_5m"])
    out["flow_align_15m"] = sign(out["ret_15m"]) != 0 and sign(out["flow_15m"]) == sign(out["ret_15m"])
    out["flow_direction_persist_5_to_15"] = sign(out["flow_5m"]) != 0 and sign(out["flow_5m"]) == sign(out["flow_15m"])
    return out


def valid_control_dates(event_date: str, event_dates: set[str]) -> list[date]:
    d = date.fromisoformat(event_date)
    result = []
    for lag in CONTROL_LAGS:
        candidate = d - timedelta(days=lag)
        if candidate.isoformat() in event_dates:
            continue
        result.append(candidate)
    return result


def required_days(manifest: dict) -> tuple[str, ...]:
    event_dates = {e["event_date"] for e in manifest["events"]}
    days = set(event_dates)
    for event in manifest["events"]:
        for control in valid_control_dates(event["event_date"], event_dates):
            days.add(control.isoformat())
    return tuple(sorted(days))


def _rate(rows: list[dict], key: str) -> float:
    return sum(bool(r[key]) for r in rows) / len(rows)


def summarize_group(rows: list[dict]) -> dict:
    result: dict[str, object] = {"observations": len(rows)}
    for horizon in POST_WINDOWS:
        returns = [float(r[f"ret_{horizon}m"]) for r in rows]
        result[f"{horizon}m"] = {
            "mean_return": mean(returns),
            "median_return": median(returns),
            "mean_abs_return": mean(abs(x) for x in returns),
            "median_abs_return": median(abs(x) for x in returns),
            "up_rate": sum(x > 0 for x in returns) / len(returns),
            "down_rate": sum(x < 0 for x in returns) / len(returns),
            "median_volume_ratio_vs_controls": median(float(r[f"volume_ratio_{horizon}m"]) for r in rows),
            "median_trade_ratio_vs_controls": median(float(r[f"trade_ratio_{horizon}m"]) for r in rows),
            "mean_flow_imbalance": mean(float(r[f"flow_{horizon}m"]) for r in rows if r[f"flow_{horizon}m"] is not None),
        }
    result["incremental"] = {
        "mean_5_to_15": mean(float(r["incremental_ret_5_15m"]) for r in rows),
        "mean_15_to_60": mean(float(r["incremental_ret_15_60m"]) for r in rows),
        "mean_15_to_120": mean(float(r["incremental_ret_15_120m"]) for r in rows),
        "continuation_5_to_15_rate": _rate(rows, "continuation_5_to_15"),
        "continuation_15_to_60_rate": _rate(rows, "continuation_15_to_60"),
        "continuation_15_to_120_rate": _rate(rows, "continuation_15_to_120"),
    }
    result["prepositioning"] = {
        f"mean_pre_return_{h}m": mean(float(r[f"pre_ret_{h}m"]) for r in rows)
        for h in PRE_WINDOWS
    }
    result["reversal_5m_vs_60m_rate"] = _rate(rows, "reversal_5_60")
    result["reversal_15m_vs_120m_rate"] = _rate(rows, "reversal_15_120")
    result["flow_alignment_5m_rate"] = _rate(rows, "flow_align_5m")
    result["flow_alignment_15m_rate"] = _rate(rows, "flow_align_15m")
    result["flow_direction_persistence_5_to_15_rate"] = _rate(rows, "flow_direction_persist_5_to_15")
    return result


def event_consensus_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["event_type"], row["event_date"]), []).append(row)
    out: list[dict] = []
    for (event_type, event_date), items in sorted(grouped.items()):
        if {r["symbol"] for r in items} != set(SYMBOLS):
            raise RuntimeError("event consensus missing symbol")
        one = {
            "event_type": event_type,
            "event_date": event_date,
            "release_utc": items[0]["release_utc"],
        }
        numeric_average_keys = [
            *(f"ret_{h}m" for h in POST_WINDOWS),
            *(f"abs_ret_{h}m" for h in POST_WINDOWS),
            *(f"pre_ret_{h}m" for h in PRE_WINDOWS),
            "incremental_ret_5_15m",
            "incremental_ret_15_60m",
            "incremental_ret_15_120m",
            *(f"flow_{h}m" for h in POST_WINDOWS),
            *(f"volume_ratio_{h}m" for h in POST_WINDOWS),
            *(f"trade_ratio_{h}m" for h in POST_WINDOWS),
        ]
        for key in numeric_average_keys:
            vals = [r[key] for r in items if r[key] is not None]
            one[key] = mean(float(v) for v in vals) if vals else None
        one["continuation_5_to_15"] = sign(one["ret_5m"]) != 0 and sign(one["incremental_ret_5_15m"]) == sign(one["ret_5m"])
        one["continuation_15_to_60"] = sign(one["ret_15m"]) != 0 and sign(one["incremental_ret_15_60m"]) == sign(one["ret_15m"])
        one["continuation_15_to_120"] = sign(one["ret_15m"]) != 0 and sign(one["incremental_ret_15_120m"]) == sign(one["ret_15m"])
        one["reversal_5_60"] = sign(one["ret_5m"]) * sign(one["ret_60m"]) == -1
        one["reversal_15_120"] = sign(one["ret_15m"]) * sign(one["ret_120m"]) == -1
        one["flow_align_5m"] = sign(one["ret_5m"]) != 0 and sign(one["flow_5m"]) == sign(one["ret_5m"])
        one["flow_align_15m"] = sign(one["ret_15m"]) != 0 and sign(one["flow_15m"]) == sign(one["ret_15m"])
        one["flow_direction_persist_5_to_15"] = sign(one["flow_5m"]) != 0 and sign(one["flow_5m"]) == sign(one["flow_15m"])
        out.append(one)
    return out


def run(raw_root: Path, manifest_path: Path, output_path: Path) -> dict:
    freeze = load_freeze()
    manifest = load_manifest(manifest_path)
    event_dates = {e["event_date"] for e in manifest["events"]}
    days = required_days(manifest)
    if any(d.startswith("2026-") for d in days):
        raise PermissionError("2026 required-day guard violation")
    cache: dict[str, dict[str, dict[int, Bar]]] = {s: {} for s in SYMBOLS}
    for symbol in SYMBOLS:
        for day in days:
            cache[symbol][day] = parse_day(raw_root, symbol, day)
    rows: list[dict] = []
    for symbol in SYMBOLS:
        for event in manifest["events"]:
            event_date = event["event_date"]
            ts = event_ts_ms(event_date)
            metrics = event_metrics(cache[symbol][event_date], ts)
            controls = []
            for control_date in valid_control_dates(event_date, event_dates):
                control_day = control_date.isoformat()
                cts = control_ts_ms(control_date)
                controls.append(event_metrics(cache[symbol][control_day], cts))
            if len(controls) < int(freeze["control_contract"]["minimum_valid_controls"]):
                raise RuntimeError(f"insufficient controls {event_date}")
            row = {
                "symbol": symbol,
                "event_type": event["event_type"],
                "event_date": event_date,
                "release_utc": event["release_utc"],
                "control_count": len(controls),
            }
            row.update(metrics)
            for horizon in POST_WINDOWS:
                control_volume = mean(float(c[f"volume_{horizon}m"]) for c in controls)
                control_trades = mean(float(c[f"trades_{horizon}m"]) for c in controls)
                row[f"volume_ratio_{horizon}m"] = float(metrics[f"volume_{horizon}m"]) / control_volume if control_volume > 0 else None
                row[f"trade_ratio_{horizon}m"] = float(metrics[f"trades_{horizon}m"]) / control_trades if control_trades > 0 else None
            rows.append(row)
    summaries: dict[str, object] = {}
    for event_type in ("CPI", "NFP"):
        summaries[event_type] = {
            symbol: summarize_group([r for r in rows if r["event_type"] == event_type and r["symbol"] == symbol])
            for symbol in SYMBOLS
        }
    consensus = event_consensus_rows(rows)
    consensus_summary = {
        event_type: summarize_group([r for r in consensus if r["event_type"] == event_type])
        for event_type in ("CPI", "NFP")
    }
    largest = sorted(rows, key=lambda r: abs(float(r["ret_60m"])), reverse=True)[:20]
    body = {
        "document_type": "NEWS_SHOCK_LAB_V01_CPI_NFP_REPLICATION_RECEIPT",
        "version": "0.1",
        "status": "DIAGNOSTIC_COMPLETE",
        "authority": "HISTORICAL_REPLICATION_ONLY_NO_TRADING_AUTHORITY",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "schedule_manifest_fingerprint": manifest["fingerprint"],
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "event_counts": manifest["event_counts"],
        "symbols": list(SYMBOLS),
        "timeframe": "1m",
        "market_days_loaded": len(days),
        "asset_event_observations": len(rows),
        "event_consensus_observations": len(consensus),
        "summary_by_event_type_and_symbol": summaries,
        "summary_event_consensus": consensus_summary,
        "largest_abs_60m_moves": [
            {
                "event_type": r["event_type"],
                "symbol": r["symbol"],
                "event_date": r["event_date"],
                "ret_5m": r["ret_5m"],
                "ret_15m": r["ret_15m"],
                "incremental_ret_15_60m": r["incremental_ret_15_60m"],
                "ret_60m": r["ret_60m"],
                "flow_15m": r["flow_15m"],
                "volume_ratio_15m": r["volume_ratio_15m"],
            }
            for r in largest
        ],
        "all_event_rows": rows,
        "event_consensus_rows": consensus,
        "guards": {
            "live_trading": False,
            "exchange_mutation": False,
            "main_merge": False,
            "render_deploy": False,
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
            "directional_rule_defined": False,
            "trading_edge_claimed": False,
        },
    }
    body["fingerprint"] = canonical_hash(body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: runner <raw_root> <schedule_manifest.json> <out_receipt.json>")
    receipt = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps({
        "status": receipt["status"],
        "fingerprint": receipt["fingerprint"],
        "event_counts": receipt["event_counts"],
        "asset_event_observations": receipt["asset_event_observations"],
        "event_consensus_observations": receipt["event_consensus_observations"],
        "summary_by_event_type_and_symbol": receipt["summary_by_event_type_and_symbol"],
        "summary_event_consensus": receipt["summary_event_consensus"],
        "largest_abs_60m_moves": receipt["largest_abs_60m_moves"],
        "guards": receipt["guards"],
    }, indent=2, sort_keys=True))
