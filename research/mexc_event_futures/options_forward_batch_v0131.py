#!/usr/bin/env python3
"""Bounded continuation batch for the already frozen OPTIONS-VOL-FWD-001 V0.1 rule."""
import argparse
import asyncio
import hashlib
import json
import time

import options_forward_smoke_v013 as base

PRIOR={
    "run_id":37074644170,
    "job_id":111061698944,
    "artifact_id":11255948065,
    "artifact_digest":"sha256:c4e5379eeebfc99a4109872d8e50005137e3b9377986791259a9a9dbb69b4ebe",
    "resolved_n":0,
    "outcomes_opened":0,
    "pending_n":0,
    "rule_hash":"edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517",
}
assert PRIOR["rule_hash"]==base.RULE_HASH
assert PRIOR["resolved_n"]==0 and PRIOR["outcomes_opened"]==0 and PRIOR["pending_n"]==0

async def run_batch(boundary_ms, accept_seconds, evidence):
    if accept_seconds<=0 or accept_seconds>10800:
        raise ValueError("accept_seconds outside frozen batch bound")
    stream=base.IndexStream(evidence)
    capture=base.ProductCapture(evidence)
    task=asyncio.create_task(stream.run())
    pending={}
    resolved=[]
    seen=set()
    attempts=[]
    started=base.now_ms()
    preflight=False
    error=None
    source_rounds=0

    async def settle(opened):
        target=opened["expiry_target_ts_ms"]
        try:
            tick=await stream.first(opened["symbol"],target,0,max(0,(target-base.now_ms())/1000)+5)
            if tick["ts"]-target>5000:
                raise ValueError("BLOCKED_MISSING_EXPIRY_INDEX")
            outcome,ret=base.resolve(opened["direction"],opened["decision_index"],tick["price"],opened["payout"])
            row={**opened,
                "expiry_ts_ms":tick["ts"],
                "expiry_index":tick["price"],
                "expiry_index_raw_sha256":tick["raw_sha256"],
                "outcome":outcome,
                "unit_return":ret,
                "status":"RESOLVED",
                "source_integrity_ok":True}
            base.validate_event(row)
            base.journal(evidence,"resolved_events.jsonl",row)
            resolved.append(row)
        except Exception as exc:
            base.journal(evidence,"blocked_events.jsonl",{**opened,"status":"BLOCKED","reason":str(exc)})

    try:
        await capture.start()
        snap=await capture.capture(initial=True)
        for symbol in base.RULE["symbols"]:
            tick=await stream.first(symbol,snap["received_at_ms"],snap["received_at_ms"],5)
            if not 0<=tick["received_at_ms"]-snap["received_at_ms"]<=5000:
                raise ValueError("PREFLIGHT_STALE_JOIN")
            for direction in ("UP","DOWN"):
                base.payout(snap,symbol,direction)
        preflight=True
        base.journal(evidence,"continuity_receipt.jsonl",{
            "status":"CONTINUITY_PASS",
            "prior":PRIOR,
            "rule_hash":base.RULE_HASH,
            "observed_at_ms":base.now_ms(),
            "research_outcomes_carried":0,
            "pending_carried":0,
        })
        base.journal(evidence,"runtime_preflight.jsonl",{
            "status":"RUNTIME_PREFLIGHT_PASS",
            "observed_at_ms":base.now_ms(),
            "payout_source_sha256":snap["raw_sha256"],
            "outcomes_opened":0,
        })

        deadline=time.monotonic()+accept_seconds
        last_minute=None
        round_id=0
        while time.monotonic()<deadline:
            minute=base.now_ms()//60000
            if minute==last_minute:
                await asyncio.sleep(.1)
                continue
            last_minute=minute
            round_id+=1
            source_rounds+=1
            pairs,errors=await asyncio.to_thread(base.options_round,evidence,f'batch-{round_id}')
            base.journal(evidence,"source_rounds.jsonl",{"minute":minute,"pairs":pairs,"errors":errors})
            for currency,pair in pairs.items():
                signal=base.condition(currency,pair,boundary_ms)
                if signal is None:
                    attempts.append({"currency":currency,"minute":minute,"status":"NO_SIGNAL_OR_INVALID_SOURCE"})
                    continue
                symbol=signal["symbol"]
                if signal["signal_id"] in seen:
                    attempts.append({"signal_id":signal["signal_id"],"status":"SKIPPED_DUPLICATE"})
                    continue
                seen.add(signal["signal_id"])
                base.journal(evidence,"condition_receipts.jsonl",signal)
                if symbol in pending and not pending[symbol].done():
                    attempts.append({"signal_id":signal["signal_id"],"status":"SKIPPED_OVERLAP"})
                    continue
                try:
                    if not base.fresh(signal["signal_source_ts_ms"],base.now_ms()):
                        raise ValueError("BLOCKED_STALE_SIGNAL")
                    snapshot=await capture.capture()
                    q=base.payout(snapshot,symbol,signal["direction"])
                    tick=await stream.first(symbol,snapshot["received_at_ms"],snapshot["received_at_ms"],5)
                    if tick["received_at_ms"]-snapshot["received_at_ms"]>5000:
                        raise ValueError("BLOCKED_STALE_DECISION_JOIN")
                    if not base.fresh(signal["signal_source_ts_ms"],tick["ts"]):
                        raise ValueError("BLOCKED_STALE_SIGNAL_AT_DECISION")
                    opened={k:signal[k] for k in (
                        "family_id","family_version","signal_id","symbol","direction",
                        "direction_policy","horizon_minutes","condition_payload_hash","rule_hash"
                    )}
                    opened.update(
                        decision_ts_ms=tick["ts"],
                        decision_index=tick["price"],
                        payout=q,
                        break_even_probability=base.break_even(q),
                        expiry_target_ts_ms=tick["ts"]+600000,
                        payout_source_sha256=snapshot["raw_sha256"],
                        decision_index_raw_sha256=tick["raw_sha256"],
                        signal_source_ts_ms=signal["signal_source_ts_ms"],
                        signal_received_at_ms=signal["signal_received_at_ms"],
                        payout_received_at_ms=snapshot["received_at_ms"],
                        decision_received_at_ms=tick["received_at_ms"],
                        status="OPEN",
                    )
                    base.journal(evidence,"opened_events.jsonl",opened)
                    pending[symbol]=asyncio.create_task(settle(opened))
                    attempts.append({"signal_id":signal["signal_id"],"symbol":symbol,"status":"OPEN"})
                except Exception as exc:
                    attempts.append({"signal_id":signal["signal_id"],"symbol":symbol,"status":"BLOCKED","reason":str(exc)})

        if pending:
            await asyncio.wait_for(asyncio.gather(*pending.values()),base.RULE["expiry_drain_seconds"])
    except Exception as exc:
        error=type(exc).__name__+": "+str(exc)
    finally:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        if hasattr(capture,"browser"):
            await capture.close()

    status="INSUFFICIENT_N" if preflight else "FROZEN_RUNTIME_BLOCKED"
    receipt={
        "family_id":base.RULE["family_id"],
        "family_version":base.RULE["family_version"],
        "rule_hash":base.RULE_HASH,
        "status":status,
        "preflight_pass":preflight,
        "started_at_ms":started,
        "finished_at_ms":base.now_ms(),
        "forward_boundary_ms":boundary_ms,
        "continuity_prior":PRIOR,
        "accept_seconds":accept_seconds,
        "source_rounds":source_rounds,
        "resolved_n":len(resolved),
        "outcomes_opened":sum(r.get("status")=="OPEN" for r in attempts),
        "attempts":attempts,
        "error":error,
        "min_n_per_symbol":100,
        "statistics_run":False,
        "continuous_collector":False,
        "bounded_forward_batch":True,
        "blocked_non_get_requests":capture.blocked_non_get,
        "blocked_sensitive_gets":capture.blocked_sensitive,
        "blocked_authenticated_requests":capture.auth_blocked,
    }
    base.journal(evidence,"session_receipt.json",receipt)
    for p in sorted(evidence.root.glob("*.jsonl")):
        evidence.entries.append({
            "path":p.name,
            "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes":p.stat().st_size,
        })
    evidence.finish(receipt)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--boundary-ms",type=int,required=True)
    ap.add_argument("--accept-seconds",type=int,default=10800)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    if args.boundary_ms>=base.now_ms():
        raise SystemExit("forward boundary must precede run")
    asyncio.run(run_batch(args.boundary_ms,args.accept_seconds,base.ShadowEvidence(args.output)))
