from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request
import zipfile
from typing import Any

import numpy as np
import pandas as pd


STRATEGY_ID = "CRYPTO-INTRAWEEK-RV-001 / CIRV-HAR-DOW-BTCETH-001"
FORWARD_ID = "CIRV-BTCETH-FORWARD-001"
ASSETS = ("BTCUSDT", "ETHUSDT")
BASE = "https://data.binance.vision/data/futures/um"

# 21-22 Sep are immutable missed-forward targets. No backfill.
FIRST_CLEAN_TARGET = pd.Timestamp("2026-09-23", tz="UTC")
WINDOW_START_MINUTE_UTC = 9 * 60
WINDOW_END_MINUTE_UTC = 10 * 60 + 30

# Lineage pins. Scientific calculations below are intentionally the same
# HAR/HAR-DOW construction as the frozen CIRV forward watcher V0.1.
CANONICAL_WATCHER_GIT_BLOB_SHA = "f83445cf98681ed24465ffe9dfd7bff173fb63ff"
OPS_AMENDMENT_COMMIT = "187c7eba80ca47b7e096d5b5a179811ef9864851"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _fetch_zip(url: str) -> tuple[bytes, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-CIRV-Forward/0.1"})
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        data = archive.read(archive.namelist()[0])
    return raw, data


def _parse_kline(data: bytes, symbol: str) -> pd.DataFrame:
    frame = pd.read_csv(io.BytesIO(data), header=None)
    if frame.shape[1] < 7:
        raise RuntimeError("kline schema")
    frame = frame.iloc[:, :12].copy()
    frame.columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_base",
        "taker_quote", "ignore",
    ]
    frame = frame[["open_time", "close"]]
    frame["symbol"] = symbol
    return frame


def _ptime(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    med = float(numeric.dropna().abs().median()) if numeric.notna().any() else 0
    unit = "us" if med > 1e14 else ("ms" if med > 1e11 else "s")
    return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce").astype("datetime64[ns, UTC]")


def _fetch_history_through(cutoff: pd.Timestamp) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    start = pd.Period(cutoff - pd.Timedelta(days=900), freq="M")
    end_prev = pd.Period(cutoff.replace(day=1) - pd.Timedelta(days=1), freq="M")
    monthly = pd.period_range(start, end_prev, freq="M").astype(str).tolist()
    first_current = cutoff.replace(day=1)
    daily = pd.date_range(first_current, cutoff, freq="D", tz="UTC")
    frames: list[pd.DataFrame] = []
    hashes: list[tuple[str, str]] = []
    tasks: list[tuple[str, str]] = []
    for symbol in ASSETS:
        for month in monthly:
            tasks.append((symbol, f"{BASE}/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip"))
        for dt in daily:
            ds = dt.strftime("%Y-%m-%d")
            tasks.append((symbol, f"{BASE}/daily/klines/{symbol}/5m/{symbol}-5m-{ds}.zip"))

    def one(task: tuple[str, str]) -> tuple[pd.DataFrame, str, str]:
        symbol, url = task
        raw, data = _fetch_zip(url)
        return _parse_kline(data, symbol), hashlib.sha256(raw).hexdigest(), url

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for frame, digest, url in executor.map(one, tasks):
            frames.append(frame)
            hashes.append((url, digest))
    return pd.concat(frames, ignore_index=True), hashes


def _daily_rv(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    raw["ts"] = _ptime(raw["open_time"])
    raw["close"] = pd.to_numeric(raw["close"], errors="coerce")
    raw = (
        raw[raw["ts"].notna() & (raw["close"] > 0)]
        .sort_values(["symbol", "ts"])
        .drop_duplicates(["symbol", "ts"], keep="last")
    )
    raw["prev_ts"] = raw.groupby("symbol")["ts"].shift(1)
    raw["prev_close"] = raw.groupby("symbol")["close"].shift(1)
    gap = (raw["ts"] - raw["prev_ts"]).dt.total_seconds() / 60
    raw["ret"] = np.where(gap.eq(5), np.log(raw["close"] / raw["prev_close"]), np.nan)
    raw["date"] = raw["ts"].dt.floor("D")
    daily = (
        raw.groupby(["symbol", "date"])
        .agg(
            rv=("ret", lambda x: float(np.nansum(np.square(x.to_numpy(float))))),
            nret=("ret", lambda x: int(np.isfinite(x.to_numpy(float)).sum())),
        )
        .reset_index()
    )
    return daily[(daily["nret"] >= 270) & (daily["rv"] > 0)].copy()


def _features(daily: pd.DataFrame, symbol: str, target: pd.Timestamp) -> tuple[pd.DataFrame, pd.Series]:
    x = daily[daily["symbol"] == symbol].sort_values("date").copy().set_index("date")
    x["x1"] = np.log(x["rv"])
    x["x5"] = np.log(x["rv"].rolling(5, min_periods=5).mean())
    x["x22"] = np.log(x["rv"].rolling(22, min_periods=22).mean())
    train = x.dropna(subset=["x1", "x5", "x22"]).copy()
    train["next_date"] = train.index.to_series().shift(-1)
    train["y"] = np.log(train["rv"].shift(-1))
    train["target_dow"] = train["next_date"].dt.weekday
    train = train[(train["next_date"] - train.index.to_series()).dt.days.eq(1)].dropna(
        subset=["y", "target_dow"]
    )
    train = train[train["next_date"] < target].tail(730)
    prev = target - pd.Timedelta(days=1)
    if prev not in x.index:
        raise RuntimeError(f"{symbol} missing previous-day RV")
    row = x.loc[prev]
    if any(pd.isna(row[column]) for column in ("x1", "x5", "x22")):
        raise RuntimeError(f"{symbol} incomplete predictors")
    return train, row


def _design_df(data: pd.DataFrame, dow: bool) -> np.ndarray:
    base = np.column_stack([np.ones(len(data)), data["x1"], data["x5"], data["x22"]])
    if not dow:
        return base
    dummies = np.column_stack(
        [(data["target_dow"].astype(int).to_numpy() == k).astype(float) for k in range(1, 7)]
    )
    return np.column_stack([base, dummies])


def _design_row(row: pd.Series, target_dow: int, dow: bool) -> np.ndarray:
    base = np.array([1.0, row["x1"], row["x5"], row["x22"]], float)
    if not dow:
        return base
    dummies = np.array([1.0 if target_dow == k else 0.0 for k in range(1, 7)], float)
    return np.r_[base, dummies]


def _daily_archive_url(symbol: str, day: pd.Timestamp) -> str:
    ds = day.strftime("%Y-%m-%d")
    return f"{BASE}/daily/klines/{symbol}/5m/{symbol}-5m-{ds}.zip"


class CIRVLocalWatcher:
    """Prospective, read-only CIRV forecast collector for the Windows Radar.

    This is deliberately not a trading adapter. It never requests target-day
    market data and it has no order, wallet, account or exchange mutation path.
    """

    def __init__(self, *, root: str = "data", poll_seconds: float = 60.0) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.status_path = self.root / "cirv_local_status.json"
        self.poll_seconds = max(float(poll_seconds), 30.0)

    def _forecast_path(self, target: pd.Timestamp) -> Path:
        return self.root / f"cirv_forward_forecast_{target.date().isoformat()}.json"

    def _resolution_path(self, target: pd.Timestamp) -> Path:
        return self.root / f"cirv_forward_resolution_{target.date().isoformat()}.json"

    def _head_ok(self, url: str) -> bool:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CryptoLab-CIRV-Radar/0.1"},
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return int(getattr(response, "status", 200)) == 200
        except Exception:
            return False

    def _source_ready(self, cutoff: pd.Timestamp) -> tuple[bool, dict[str, bool]]:
        checks = {
            symbol: self._head_ok(_daily_archive_url(symbol, cutoff))
            for symbol in ASSETS
        }
        return all(checks.values()), checks

    def _resolve_previous(
        self,
        *,
        daily: pd.DataFrame,
        target: pd.Timestamp,
    ) -> dict[str, Any] | None:
        forecast_path = self._forecast_path(target)
        resolution_path = self._resolution_path(target)
        if resolution_path.exists() or not forecast_path.exists():
            if resolution_path.exists():
                return json.loads(resolution_path.read_text(encoding="utf-8"))
            return None

        forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
        rows: list[dict[str, Any]] = []
        for item in forecast.get("forecasts", []):
            symbol = str(item["asset"])
            actual_rows = daily[(daily["symbol"] == symbol) & (daily["date"] == target)]
            if len(actual_rows) != 1:
                raise RuntimeError(f"{symbol} missing actual RV for {target.date().isoformat()}")
            actual_rv = float(actual_rows.iloc[0]["rv"])
            if actual_rv <= 0:
                raise RuntimeError(f"{symbol} invalid actual RV")
            actual_log = float(np.log(actual_rv))
            har = float(item["forecast_har_rv"])
            dow = float(item["forecast_har_dow_rv"])
            if har <= 0 or dow <= 0:
                raise RuntimeError(f"{symbol} invalid forecast RV")
            q_har = float(np.log(har) + actual_rv / har)
            q_dow = float(np.log(dow) + actual_rv / dow)
            m_har = float((actual_log - np.log(har)) ** 2)
            m_dow = float((actual_log - np.log(dow)) ** 2)
            rows.append(
                {
                    "asset": symbol,
                    "target_date": target.date().isoformat(),
                    "actual_rv": actual_rv,
                    "forecast_har_rv": har,
                    "forecast_har_dow_rv": dow,
                    "qlike_har": q_har,
                    "qlike_har_dow": q_dow,
                    "qlike_diff_baseline_minus_dow": q_har - q_dow,
                    "logmse_har": m_har,
                    "logmse_har_dow": m_dow,
                    "logmse_diff_baseline_minus_dow": m_har - m_dow,
                }
            )

        payload = {
            "forward_id": FORWARD_ID,
            "strategy_id": STRATEGY_ID,
            "mode": "RESOLUTION",
            "target_date": target.date().isoformat(),
            "resolved_after_target_complete": True,
            "rows": rows,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        _atomic_json(resolution_path, payload)
        return payload

    def _metrics(self) -> dict[str, Any]:
        rows_by_asset: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in ASSETS}
        targets: set[str] = set()
        for path in sorted(self.root.glob("cirv_forward_resolution_*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            target = payload.get("target_date")
            if target:
                targets.add(str(target))
            for row in payload.get("rows", []):
                symbol = str(row.get("asset") or "")
                if symbol in rows_by_asset:
                    rows_by_asset[symbol].append(row)
        per_asset: dict[str, Any] = {}
        for symbol, rows in rows_by_asset.items():
            q = [float(row["qlike_diff_baseline_minus_dow"]) for row in rows]
            m = [float(row["logmse_diff_baseline_minus_dow"]) for row in rows]
            per_asset[symbol] = {
                "N": len(rows),
                "mean_qlike_diff_baseline_minus_dow": float(np.mean(q)) if q else None,
                "mean_logmse_diff_baseline_minus_dow": float(np.mean(m)) if m else None,
            }
        return {
            "resolved_clean_targets": len(targets),
            "assets": per_asset,
            "automatic_tier_promotion": False,
            "economic_trading_edge_claimed": False,
        }

    def _compute_forecast(self, target: pd.Timestamp) -> tuple[dict[str, Any], pd.DataFrame]:
        cutoff = target - pd.Timedelta(days=1)
        raw, hashes = _fetch_history_through(cutoff)
        daily = _daily_rv(raw)
        digest = hashlib.sha256(
            ("\n".join(url + " " + digest for url, digest in sorted(hashes))).encode()
        ).hexdigest()

        forecasts: list[dict[str, Any]] = []
        for symbol in ASSETS:
            train, row = _features(daily, symbol, target)
            if len(train) < 500:
                raise RuntimeError(f"{symbol} insufficient training rows")
            y = train["y"].to_numpy(float)
            x0 = _design_df(train, False)
            x1 = _design_df(train, True)
            b0 = np.linalg.lstsq(x0, y, rcond=None)[0]
            b1 = np.linalg.lstsq(x1, y, rcond=None)[0]
            dow = int(target.weekday())
            p0 = float(_design_row(row, dow, False) @ b0)
            p1 = float(_design_row(row, dow, True) @ b1)
            forecasts.append(
                {
                    "target_date": target.date().isoformat(),
                    "asset": symbol,
                    "forecast_har_rv": float(np.exp(p0)),
                    "forecast_har_dow_rv": float(np.exp(p1)),
                    "model_training_end_date": cutoff.date().isoformat(),
                    "training_rows": int(len(train)),
                    "source_digest": digest,
                }
            )

        payload = {
            "forward_id": FORWARD_ID,
            "strategy_id": STRATEGY_ID,
            "mode": "FORECAST",
            "target_date": target.date().isoformat(),
            "classification": "PROSPECTIVE_BLIND_DELAYED_SOURCE",
            "generated_without_target_outcome": True,
            "canonical_watcher_git_blob_sha": CANONICAL_WATCHER_GIT_BLOB_SHA,
            "ops_amendment_commit": OPS_AMENDMENT_COMMIT,
            "forecasts": forecasts,
            "orders_created": False,
            "authenticated_exchange_api_used": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        return payload, daily

    def run_once(self, *, now: pd.Timestamp | None = None) -> dict[str, Any]:
        now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")
        target = now.floor("D")
        checked_at = now.isoformat()
        base = {
            "strategy_id": STRATEGY_ID,
            "forward_id": FORWARD_ID,
            "classification": "PROSPECTIVE_BLIND_DELAYED_SOURCE",
            "checked_at_utc": checked_at,
            "target_date": target.date().isoformat(),
            "first_clean_target": FIRST_CLEAN_TARGET.date().isoformat(),
            "window_utc": "09:00-10:30",
            "canonical_watcher_git_blob_sha": CANONICAL_WATCHER_GIT_BLOB_SHA,
            "ops_amendment_commit": OPS_AMENDMENT_COMMIT,
            "no_backfill_dates": ["2026-09-21", "2026-09-22"],
            "orders_created": False,
            "authenticated_exchange_api_used": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }

        if target < FIRST_CLEAN_TARGET:
            state = {
                **base,
                "status": "WATCHING",
                "runtime_phase": "WAITING_FIRST_CLEAN_TARGET",
                "metrics": self._metrics(),
            }
            _atomic_json(self.status_path, state)
            return state

        forecast_path = self._forecast_path(target)
        if forecast_path.exists():
            forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
            state = {
                **base,
                "status": "FORECAST_READY",
                "runtime_phase": "TODAY_FORECAST_ALREADY_PERSISTED",
                "forecast": forecast,
                "metrics": self._metrics(),
            }
            _atomic_json(self.status_path, state)
            return state

        minute = now.hour * 60 + now.minute
        if minute < WINDOW_START_MINUTE_UTC:
            state = {
                **base,
                "status": "WATCHING",
                "runtime_phase": "WAITING_SOURCE_WINDOW",
                "metrics": self._metrics(),
            }
            _atomic_json(self.status_path, state)
            return state
        if minute > WINDOW_END_MINUTE_UTC:
            state = {
                **base,
                "status": "FAIL_CLOSED",
                "runtime_phase": "MISSED_FORWARD_TARGET_NO_FORECAST",
                "reason": "NO_BACKFILL_AFTER_DAILY_EXECUTION_WINDOW",
                "metrics": self._metrics(),
            }
            _atomic_json(self.status_path, state)
            return state

        cutoff = target - pd.Timedelta(days=1)
        ready, source_checks = self._source_ready(cutoff)
        if not ready:
            state = {
                **base,
                "status": "WATCHING",
                "runtime_phase": "WAITING_CANONICAL_D_MINUS_1_ARCHIVES",
                "source_checks": source_checks,
                "metrics": self._metrics(),
            }
            _atomic_json(self.status_path, state)
            return state

        forecast, daily = self._compute_forecast(target)
        previous_resolution = self._resolve_previous(daily=daily, target=cutoff)
        _atomic_json(forecast_path, forecast)
        state = {
            **base,
            "status": "FORECAST_READY",
            "runtime_phase": "FORECAST_PERSISTED",
            "source_checks": source_checks,
            "forecast": forecast,
            "previous_target_resolution": previous_resolution,
            "metrics": self._metrics(),
        }
        _atomic_json(self.status_path, state)
        return state

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception as exc:
                now = pd.Timestamp.now(tz="UTC")
                state = {
                    "strategy_id": STRATEGY_ID,
                    "forward_id": FORWARD_ID,
                    "status": "FAIL_CLOSED",
                    "runtime_phase": "RUNTIME_EXCEPTION",
                    "checked_at_utc": now.isoformat(),
                    "error": f"{type(exc).__name__}:{exc}",
                    "classification": "PROSPECTIVE_BLIND_DELAYED_SOURCE",
                    "orders_created": False,
                    "authenticated_exchange_api_used": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                _atomic_json(self.status_path, state)
            time.sleep(self.poll_seconds)
