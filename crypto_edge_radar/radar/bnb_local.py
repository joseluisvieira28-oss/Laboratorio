from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

from .bnb_launchpool_watcher import BNBLaunchpoolForwardShadowWatcher


def normalized_bnb_local_interval(value: float) -> float:
    value=float(value)
    if value<=0:
        raise ValueError("BNB local interval must be positive")
    return max(30.0,value)


def _atomic_json(path: str, payload: dict[str,Any]) -> None:
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix(target.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    tmp.replace(target)


@dataclass
class BNBLocalFastMonitor:
    watcher: BNBLaunchpoolForwardShadowWatcher
    status_path: str
    interval_seconds: float=30.0

    def __post_init__(self)->None:
        self.interval_seconds=normalized_bnb_local_interval(self.interval_seconds)

    def run_cycle(self, *, now_ms:int|None=None)->dict[str,Any]:
        if now_ms is None:
            now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
        started=time.monotonic()
        state=self.watcher.run_once(now_ms=now_ms)
        duration_ms=(time.monotonic()-started)*1000.0
        receipt={
            "status":"OK" if state.get("status")=="OK" else "FAIL_CLOSED",
            "mode":"PUBLIC_SHADOW_ONLY",
            "watcher_id":state.get("watcher_id"),
            "poll_interval_seconds":self.interval_seconds,
            "poll_started_utc":datetime.fromtimestamp(now_ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
            "poll_duration_ms":duration_ms,
            "eligible_events_visible":state.get("eligible_events_visible",0),
            "clusters_visible":state.get("clusters_visible",0),
            "inserted_events":state.get("inserted_events",0),
            "authenticated_exchange_api_used":False,
            "orders_created":False,
            "exchange_mutation_performed":False,
            "live_capital_enabled":False,
            "micro_live_execution_enabled":False,
            "source_state":state,
        }
        _atomic_json(self.status_path,receipt)
        return receipt

    def run_forever(self)->None:
        while True:
            started=time.monotonic()
            try:
                self.run_cycle()
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                _atomic_json(self.status_path,{
                    "status":"FAIL_CLOSED",
                    "mode":"PUBLIC_SHADOW_ONLY",
                    "poll_interval_seconds":self.interval_seconds,
                    "error":f"{type(exc).__name__}:{exc}",
                    "authenticated_exchange_api_used":False,
                    "orders_created":False,
                    "exchange_mutation_performed":False,
                    "live_capital_enabled":False,
                    "micro_live_execution_enabled":False,
                })
            elapsed=time.monotonic()-started
            time.sleep(max(1.0,self.interval_seconds-elapsed))
