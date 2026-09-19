from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .evidence import EvidenceStore, PostgresEvidenceStore
from .strategies.ema6h_50x200_regime_forward import (
    DAY_MS,
    FIFTEEN_MIN_MS,
    SIX_HOUR_MS,
    FIRST_ELIGIBLE_SIGNAL_CLOSE_MS,
    HOLD_BARS,
    WARMUP_15M_MS,
    WARMUP_1D_MS,
    FROZEN_UNIVERSE,
    BinanceSpotKlineFeed,
    EMA6HRegimeSourceError,
    ForwardTrade,
    aggregate_15m_to_6h,
    detect_cross,
    latest_certifiable_signal_close_ms,
    materialize_trade,
    regime_state,
    resolve_trade,
    utc_iso,
)

Store = EvidenceStore | PostgresEvidenceStore
BOUNDARY_EVENT="EMA6H_REGIME_FORWARD_BOUNDARY"
SIGNAL_EVENT="EMA6H_REGIME_FORWARD_SIGNAL"
RESOLUTION_EVENT="EMA6H_REGIME_FORWARD_RESOLUTION"
DEVIATION_EVENT="EMA6H_REGIME_FORWARD_RULE_DEVIATION"

def _expected_boundaries(latest:int)->list[int]:
    if latest<FIRST_ELIGIBLE_SIGNAL_CLOSE_MS:return []
    return list(range(FIRST_ELIGIBLE_SIGNAL_CLOSE_MS,latest+1,SIX_HOUR_MS))

def _boundary_key(ms:int)->str:
    return f"EMA6H-50X200-REGIME:{ms}"

def _signal_key(symbol:str,ms:int)->str:
    return f"EMA6H-50X200-REGIME:{symbol}:{ms}"

class EMA6HRegimeForwardWatcher:
    watcher_id="EMA6H-50X200-REGIME-DEPENDENCY-001-FORWARD-SHADOW"

    def __init__(self,*,store:Store,feed:BinanceSpotKlineFeed|None=None)->None:
        self.store=store
        self.feed=feed or BinanceSpotKlineFeed()

    def _audited_boundaries(self)->set[int]:
        out=set()
        for p in self.store.read_payloads(BOUNDARY_EVENT):
            v=p.get("signal_close_ms")
            if isinstance(v,int):out.add(v)
        return out

    def _resolve_due(self,*,now_ms:int)->dict[str,int]:
        signals=self.store.read_payloads(SIGNAL_EVENT)
        resolutions=self.store.read_payloads(RESOLUTION_EVENT)
        resolved={str(x.get("event_key")) for x in resolutions}
        due=[x for x in signals if str(x.get("event_key")) not in resolved and isinstance((x.get("paper_trade") or {}).get("exit_open_ms"),int) and now_ms>=int(x["paper_trade"]["exit_open_ms"])+FIFTEEN_MIN_MS]
        inserted=duplicates=0
        by_symbol={}
        for x in due:by_symbol.setdefault(x["paper_trade"]["symbol"],[]).append(x)
        for symbol,items in by_symbol.items():
            lo=min(int(x["paper_trade"]["exit_open_ms"]) for x in items)
            hi=max(int(x["paper_trade"]["exit_open_ms"]) for x in items)+2*FIFTEEN_MIN_MS
            src=self.feed.klines(symbol,"15m",start_ms=lo,end_ms=hi,now_ms=now_ms)
            for x in items:
                p=x["paper_trade"]
                trade=ForwardTrade(
                    symbol=p["symbol"],direction=int(p["direction"]),signal_close_ms=int(p["signal_close_ms"]),
                    entry_open_ms=int(p["entry_open_ms"]),entry=float(p["entry"]),exit_open_ms=int(p["exit_open_ms"]),
                    regime_state=p["regime_state"],regime_bucket=p["regime_bucket"])
                outcome=resolve_trade(trade,src)
                if outcome is None:raise EMA6HRegimeSourceError(f"exit bar unavailable for {x['event_key']}")
                payload={
                    "watcher_id":self.watcher_id,"mode":"PUBLIC_SHADOW_ONLY","event_key":x["event_key"],
                    "signal_close_utc":utc_iso(trade.signal_close_ms),"paper_trade":asdict(trade),"outcome":asdict(outcome),
                    "authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False
                }
                r=self.store.append_once(RESOLUTION_EVENT,x["event_key"],payload)
                inserted+=int(bool(r["inserted"]));duplicates+=int(not bool(r["inserted"]))
        return {"due":len(due),"inserted":inserted,"duplicates":duplicates}

    def run_once(self,*,now_ms:int|None=None)->dict[str,Any]:
        if now_ms is None:now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
        latest=latest_certifiable_signal_close_ms(now_ms)
        if latest is None:
            return {
                "watcher_id":self.watcher_id,"status":"WAITING_FIRST_ELIGIBLE_BOUNDARY",
                "first_eligible_signal_close_utc":utc_iso(FIRST_ELIGIBLE_SIGNAL_CLOSE_MS),
                "authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False
            }

        expected=_expected_boundaries(latest);audited_before=self._audited_boundaries()
        missing=[b for b in expected if b not in audited_before]
        inserted_signals=duplicate_signals=0
        boundaries_inserted=0

        if missing:
            earliest=min(missing)
            daily=self.feed.klines("BTCUSDT","1d",start_ms=earliest-WARMUP_1D_MS,end_ms=latest,now_ms=now_ms)
            source_15m={};bars_6h={};incomplete={}
            for symbol in FROZEN_UNIVERSE:
                src=self.feed.klines(symbol,"15m",start_ms=earliest-WARMUP_15M_MS,end_ms=latest+2*FIFTEEN_MIN_MS,now_ms=now_ms)
                h6,inc=aggregate_15m_to_6h(src)
                source_15m[symbol]=src;bars_6h[symbol]=h6;incomplete[symbol]=inc

            for boundary in missing:
                rg=regime_state(daily,signal_close_ms=boundary)
                cross_count=0
                for symbol in FROZEN_UNIVERSE:
                    sig=detect_cross(symbol,bars_6h[symbol],signal_close_ms=boundary)
                    if sig is None:continue
                    trade=materialize_trade(sig,source_15m[symbol],rg)
                    if trade is None:raise EMA6HRegimeSourceError(f"entry bar unavailable {symbol} {utc_iso(boundary)}")
                    key=_signal_key(symbol,boundary)
                    payload={
                        "watcher_id":self.watcher_id,"mode":"PUBLIC_SHADOW_ONLY","event_key":key,
                        "signal_close_utc":utc_iso(boundary),"signal":asdict(sig),"regime":rg,"paper_trade":asdict(trade),
                        "authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False
                    }
                    receipt=self.store.append_once(SIGNAL_EVENT,key,payload)
                    inserted_signals+=int(bool(receipt["inserted"]));duplicate_signals+=int(not bool(receipt["inserted"]))
                    cross_count+=1
                bpay={
                    "watcher_id":self.watcher_id,"signal_close_ms":boundary,"signal_close_utc":utc_iso(boundary),
                    "regime":rg,"cross_count":cross_count,"symbols_scanned":list(FROZEN_UNIVERSE),
                    "incomplete_6h_buckets_seen":incomplete,
                    "authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False
                }
                rr=self.store.append_once(BOUNDARY_EVENT,_boundary_key(boundary),bpay)
                boundaries_inserted+=int(bool(rr["inserted"]))

        resolution=self._resolve_due(now_ms=now_ms)
        audited_after=self._audited_boundaries()
        missing_after=[b for b in expected if b not in audited_after]
        status="OK" if not missing_after else "FAIL_CLOSED_MISSING_BOUNDARY_AUDIT"
        if missing_after:
            self.store.append_once(DEVIATION_EVENT,f"missing:{missing_after[0]}",{
                "watcher_id":self.watcher_id,"reason":"MISSING_EXPECTED_BOUNDARY_AUDIT",
                "missing_boundaries_utc":[utc_iso(x) for x in missing_after],
                "scientific_rules_changed":False,"orders_created":False,"exchange_mutation_performed":False
            })
        return {
            "watcher_id":self.watcher_id,"status":status,"mode":"PUBLIC_SHADOW_ONLY","provider":self.feed.provider,
            "first_eligible_signal_close_utc":utc_iso(FIRST_ELIGIBLE_SIGNAL_CLOSE_MS),
            "latest_certifiable_signal_close_utc":utc_iso(latest),
            "expected_boundaries":len(expected),"audited_boundaries":len(audited_after),"new_boundaries":boundaries_inserted,
            "inserted_signals":inserted_signals,"duplicate_signals":duplicate_signals,
            "due_resolutions":resolution["due"],"inserted_resolutions":resolution["inserted"],
            "duplicate_resolutions":resolution["duplicates"],"missing_boundaries":len(missing_after),
            "evidence_backend":self.store.backend,
            "authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False
        }
