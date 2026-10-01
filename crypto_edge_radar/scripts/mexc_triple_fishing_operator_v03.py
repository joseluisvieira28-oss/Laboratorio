from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

from radar.bnb_operator_source_v03 import BNBOperatorSourceV03
from radar.dh03_operator_source_v03 import DH03OperatorSourceV03
from radar.global_fishing_dispatcher_v02 import arbitrate_due_signals
from radar.mexc_auth_readonly import MEXCCredentials
from radar.operator_futures_engine_v02 import OperatorFuturesEngineV02
from radar.options_v21_operator_source_v03 import OptionsV21OperatorSourceV03


BNB = "BNB-LAUNCHPOOL-DEMAND-001"
OPTIONS = "OPTIONS-SPOTPERP-001-V2.1"
DH03 = "HTF-DH03-12H-STANDALONE-FORWARD-V1"

SOURCE_POLL_SECONDS = {
    BNB: 30.0,
    OPTIONS: 10.0,
    DH03: 0.20,
}
ENGINE_ACTIVE_POLL_SECONDS = 1.0
MAIN_LOOP_FLOOR_SECONDS = 0.10


def _atomic_write(path: str | Path, payload: dict[str, Any]) -> None:
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix(target.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _utc(value: Any) -> datetime:
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


class TripleFishingOperatorV03:
    """Single-process owner for BNB, OPTIONS and DH03 operator lanes.

    Public sources may all observe concurrently. Only this supervisor owns the
    generic MEXC engine, and the engine owns one persistent account-wide slot.
    """

    def __init__(
        self,
        *,
        engine: OperatorFuturesEngineV02,
        bnb_source: BNBOperatorSourceV03,
        options_source: OptionsV21OperatorSourceV03,
        dh03_source: DH03OperatorSourceV03,
        state_path: str,
        meta_observer: Any | None = None,
    ) -> None:
        self.engine=engine
        self.sources={
            BNB:bnb_source,
            OPTIONS:options_source,
            DH03:dh03_source,
        }
        self.state_path=Path(state_path)
        self.meta_observer=meta_observer
        self.meta_state:dict[str,dict[str,Any]]={}
        self.pending:dict[str,dict[str,Any]]={}
        self.source_state:dict[str,dict[str,Any]]={}
        now=time.monotonic()
        self.next_poll={candidate:now for candidate in self.sources}
        self.next_engine_poll=now
        self.last_engine:dict[str,Any]={"status":"NOT_CHECKED"}

    @staticmethod
    def _pending_key(signal:dict[str,Any])->str:
        candidate=str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        key=str(signal.get("immutable_signal_key") or "")
        if not candidate or not key:
            raise RuntimeError("pending signal identity missing")
        return f"{candidate}|{key}"

    def _save(self, status:str, **extra:Any)->dict[str,Any]:
        payload={
            "version":"TRIPLE_FISHING_OPERATOR_V0.3",
            "status":status,
            "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "lanes":[BNB,OPTIONS,DH03],
            "max_simultaneous_positions":1,
            "pending_signal_count":len(self.pending),
            "pending_signals":[
                {
                    "candidate_id":s.get("candidate_id"),
                    "signal_identity":s.get("immutable_signal_key"),
                    "entry_target_utc":s.get("entry_target_utc"),
                }
                for s in sorted(
                    self.pending.values(),
                    key=lambda x:(str(x.get("entry_target_utc")),str(x.get("candidate_id")),str(x.get("immutable_signal_key"))),
                )
            ],
            "source_state":self.source_state,
            "engine":self.last_engine,
            "meta_layer":{"enabled":self.meta_observer is not None,"state":self.meta_state},
            **extra,
        }
        _atomic_write(self.state_path,payload)
        return payload

    def _mark(self, candidate_id:str, signal_identity:str, status:str)->None:
        source=self.sources.get(candidate_id)
        if source is not None and hasattr(source,"mark"):
            source.mark(signal_identity,status)
        self.pending.pop(f"{candidate_id}|{signal_identity}",None)

    def _ingest(self,candidate_id:str,result:dict[str,Any])->None:
        self.source_state[candidate_id]=result
        raw_signals: list[dict[str,Any]]=[]
        if isinstance(result.get("signals"),list):
            raw_signals=[x for x in result["signals"] if isinstance(x,dict)]
        elif isinstance(result.get("signal"),dict):
            raw_signals=[result["signal"]]
        for signal in raw_signals:
            if str(signal.get("candidate_id") or "")!=candidate_id:
                continue
            self.pending[self._pending_key(signal)]=signal

    def _observe_meta(self, signals:list[dict[str,Any]], captured_at:datetime)->None:
        if self.meta_observer is None:
            return
        captured=captured_at.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
        frozen=[dict(s) for s in signals]
        for signal in frozen:
            candidate=str(signal.get("candidate_id") or "")
            key=str(signal.get("immutable_signal_key") or "")
            identity=f"{candidate}|{key}"
            try:
                result=self.meta_observer.observe(
                    signal=dict(signal),
                    captured_at_utc=captured,
                    simultaneous_signals=[dict(s) for s in frozen],
                )
                self.meta_state[identity]=result if isinstance(result,dict) else {"status":"RECORDED"}
            except Exception as exc:
                self.meta_state[identity]={
                    "status":"RECORDER_FAIL_CLOSED_PARENT_UNCHANGED",
                    "error":f"{type(exc).__name__}:{exc}",
                }

    def _poll_sources(self)->None:
        now_mono=time.monotonic()
        now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
        for candidate,source in self.sources.items():
            if now_mono<self.next_poll[candidate]:
                continue
            self.next_poll[candidate]=now_mono+SOURCE_POLL_SECONDS[candidate]
            try:
                if candidate in {BNB,DH03}:
                    result=source.poll(now_ms=now_ms)
                else:
                    result=source.poll(now_utc=datetime.now(timezone.utc))
                if not isinstance(result,dict):
                    raise RuntimeError("source poll did not return object")
                self._ingest(candidate,result)
            except Exception as exc:
                self.source_state[candidate]={
                    "status":"FAIL_CLOSED_SOURCE",
                    "error":f"{type(exc).__name__}:{exc}",
                    "orders_created":False,
                    "exchange_mutation_performed":False,
                }

    def _manage_engine(self)->None:
        now=time.monotonic()
        if now<self.next_engine_poll:
            return
        self.next_engine_poll=now+ENGINE_ACTIVE_POLL_SECONDS
        try:
            self.last_engine=self.engine.manage_active()
        except Exception as exc:
            self.last_engine={
                "status":"ENGINE_MANAGEMENT_FAIL_CLOSED",
                "error":f"{type(exc).__name__}:{exc}",
            }

    def _drop_expired_rejected(self, decision:dict[str,Any])->None:
        for row in decision.get("rejected",[]):
            if not isinstance(row,dict):
                continue
            reason=str(row.get("reason") or "")
            if reason!="MISSED_NO_CHASE":
                continue
            candidate=str(row.get("candidate_id") or "")
            signal=str(row.get("signal_identity") or "")
            if candidate and signal:
                self._mark(candidate,signal,"MISSED_LATE_NO_CHASE")

    def run_cycle(self)->dict[str,Any]:
        self._poll_sources()
        self._manage_engine()

        now=datetime.now(timezone.utc)
        signals=list(self.pending.values())
        self._observe_meta(signals,now)
        probe=arbitrate_due_signals(
            signals,
            now=now,
            global_slot_occupied=False,
        )
        self._drop_expired_rejected(probe)

        # Re-evaluate after dropping expired rows.
        signals=list(self.pending.values())
        if not signals:
            return self._save("WATCHING_THREE_LANES")

        # manage_active is authoritative for a locally owned position/reservation.
        engine_status=str(self.last_engine.get("status") or "")
        slot_occupied=engine_status not in {
            "IDLE_NO_OPERATOR_POSITION",
            "CLOSED_RECONCILED",
            "NOT_CHECKED",
        }
        if not slot_occupied:
            try:
                slot_occupied=self.engine.global_slot.current() is not None
            except Exception as exc:
                return self._save(
                    "FAIL_CLOSED_GLOBAL_SLOT_STATE",
                    error=f"{type(exc).__name__}:{exc}",
                )

        decision=arbitrate_due_signals(
            signals,
            now=now,
            global_slot_occupied=slot_occupied,
        )
        self._drop_expired_rejected(decision)

        for loser in decision.get("losers",[]):
            candidate=str(loser.get("candidate_id") or "")
            signal=str(loser.get("signal_identity") or "")
            if candidate and signal:
                self._mark(candidate,signal,str(loser.get("reason") or "MISSED_CONFLICT_NO_CHASE"))

        winner=decision.get("winner")
        if not isinstance(winner,dict):
            if decision.get("status")=="GLOBAL_SLOT_OCCUPIED":
                return self._save(
                    "MANAGING_GLOBAL_SLOT_WITH_THREE_SOURCES_WATCHING",
                    arbitration=decision,
                )
            return self._save(
                "WATCHING_OR_PREARMED",
                arbitration=decision,
            )

        candidate=str(winner["candidate_id"])
        key=str(winner["immutable_signal_key"])
        try:
            result=self.engine.enter_signal(winner)
        except Exception as exc:
            result={
                "status":"ENTRY_FAIL_CLOSED_EXCEPTION",
                "error":f"{type(exc).__name__}:{exc}",
            }
        status=str(result.get("status") or "")

        if status=="FILLED_EXIT_PENDING":
            self._mark(candidate,key,"CONSUMED_ACTIVE_REAL_MONEY")
            self.next_engine_poll=time.monotonic()
        elif status=="WAITING_ENTRY_TARGET":
            pass
        elif status=="ENTRY_RECONCILIATION_REQUIRED":
            self._mark(candidate,key,"ENTRY_RECONCILIATION_REQUIRED")
            self.next_engine_poll=time.monotonic()
        else:
            # A due signal is never re-tried after a failed entry gate.
            self._mark(candidate,key,"BLOCKED_AT_ENTRY_NO_CHASE")

        self.last_engine=result
        return self._save(
            status,
            arbitration=decision,
            entry_result=result,
        )

    def run_forever(self)->None:
        while True:
            started=time.monotonic()
            self.run_cycle()
            elapsed=time.monotonic()-started
            time.sleep(max(0.02,MAIN_LOOP_FLOOR_SECONDS-elapsed))


def main()->int:
    ap=argparse.ArgumentParser(
        description="Single-owner BNB + OPTIONS + DH03 MEXC operator supervisor."
    )
    ap.add_argument("--receipt-root",required=True)
    ap.add_argument("--armed-path",required=True)
    ap.add_argument("--kill-switch",required=True)
    ap.add_argument("--status-path",required=True)
    ap.add_argument("--global-slot-path",required=True)
    ap.add_argument("--supervisor-state",required=True)
    ap.add_argument("--bnb-state",required=True)
    ap.add_argument("--options-db",required=True)
    ap.add_argument("--options-state",required=True)
    ap.add_argument("--dh03-market-db",required=True)
    ap.add_argument("--dh03-evidence-db",required=True)
    ap.add_argument("--dh03-state",required=True)
    args=ap.parse_args()

    credentials=MEXCCredentials.from_env()
    engine=OperatorFuturesEngineV02(
        credentials=credentials,
        receipt_root=args.receipt_root,
        armed_path=args.armed_path,
        kill_switch_path=args.kill_switch,
        status_path=args.status_path,
        global_slot_path=args.global_slot_path,
    )
    supervisor=TripleFishingOperatorV03(
        engine=engine,
        bnb_source=BNBOperatorSourceV03(state_path=args.bnb_state),
        options_source=OptionsV21OperatorSourceV03(
            db_path=args.options_db,
            state_path=args.options_state,
        ),
        dh03_source=DH03OperatorSourceV03(
            data_db=args.dh03_market_db,
            evidence_db=args.dh03_evidence_db,
            state_path=args.dh03_state,
        ),
        state_path=args.supervisor_state,
    )
    supervisor.run_forever()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
