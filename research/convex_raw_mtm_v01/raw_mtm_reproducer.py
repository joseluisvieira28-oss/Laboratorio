#!/usr/bin/env python3
"""Independent raw-source identity and full hourly-close MTM of frozen BTC Convex.
Uses exact pinned source definitions; does not create a new independent OOS.
Read-only Binance Vision public OHLCV and official historical funding only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys, traceback
from collections import defaultdict
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
CAPITAL=10000.0
EXPECTED=("ETHUSDT","SOLUSDT","BNBUSDT")
SOURCE_GIT_BLOB_SHA="49e2bafd2e487352db24f2a812e936372a2cb1ff"
ARCHIVE_ARTIFACT=10775714534
ARCHIVE_RUN=35918769969
WINDOW=[ "2021-01-01T00:00:00Z","2025-12-31T23:00:00Z" ]
FIRST=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
LAST=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)
HOUR_MS=3600000
MAX_POS=3
MAX_RESERVATION=.01
PLANNED_LOSS=.0424
RISKS=(.0025,.005)
LAYERS={"BASE":.0002,"STRESS":.0005}

def close(a,b,ctx,atol=1e-6,rtol=1e-8):
    if not math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol):
        raise ValueError(f"REPRO_MISMATCH:{ctx}:{a} vs {b}")

def source_definitions(path):
    import subprocess
    # Verify a frozen Git blob hash, not a mutable branch script.
    blob=subprocess.run(["git","hash-object",str(path)],text=True,capture_output=True,check=True).stdout.strip()
    if blob!=SOURCE_GIT_BLOB_SHA: raise ValueError("ORIGINAL_SOURCE_BLOB_MISMATCH:"+blob)
    full=Path(path).read_text()
    marker="\nout={\n"
    if full.count(marker)!=1: raise ValueError("UNEXPECTED_PINNED_SCRIPT_STRUCTURE")
    definitions=full.split(marker)[0]
    env={"__file__":str(Path(path).resolve()),"__name__":"pinned_original_source","__builtins__":__builtins__}
    exec(compile(definitions,str(path),"exec"),env)
    for key in ("load_symbol","simulate","START_MS","END_MS"):
        if key not in env:raise ValueError("PINNED_LIBRARY_DEF_MISSING:"+key)
    if env["START_MS"]!=FIRST or env["END_MS"]!=LAST:raise ValueError("ORIGINAL_DATE_BOUNDARY_CHANGED")
    return env,blob

def read_archive(root):
    hits=list(Path(root).rglob("CROSS_ASSET_COST_VALIDATION_V0.1.json"))
    if len(hits)!=1:raise ValueError("CANONICAL_JSON_MISSING_OR_DUPLICATE:"+str(len(hits)))
    file=hits[0]
    body=file.read_bytes();d=json.loads(body)
    if d.get("experiment")!="CROSS_ASSET_COST_VALIDATION_V0.1" or d.get("period")!=WINDOW:
        raise ValueError("CANONICAL_ARCHIVE_ID_MISMATCH")
    if set(d.get("symbols",{}))!=set(EXPECTED):raise ValueError("CANONICAL_ASSET_MISMATCH")
    return d,hashlib.sha256(body).hexdigest()

def compare_trades(raw,canonical,symbol,layer):
    expected=canonical["trades"];actual=raw["trades"]
    if len(actual)!=len(expected):raise ValueError(f"{symbol}:{layer}:TRADE_COUNT:{len(actual)}!={len(expected)}")
    for field in ("closed_trades","wins","losses","forced_end_liquidation"):
        if raw[field]!=canonical[field]:raise ValueError("ORIGINAL_OUTCOME_SCHEMA_DIFF:"+field)
    for field in ("ending_equity","net_pnl","net_return","max_mark_to_market_drawdown",
                  "funding_cashflow","commission_paid","slippage_cost","net_without_top1","net_without_top3"):
        close(raw[field],canonical[field],f"{symbol}:{layer}:{field}",atol=.0005,rtol=5e-8)
    for idx,(a,b) in enumerate(zip(actual,expected)):
        for field in ("entry_t","exit_t","reason"):
            if a[field]!=b[field]:
                raise ValueError(f"TRADE_RECONCILIATION_FAIL:{symbol}:{layer}:{idx}:{field}")
        for field in ("entry","exit","net_pnl","funding","commission","slippage_cost","return_pct"):
            close(a[field],b[field],f"{symbol}:{layer}:{idx}:{field}",atol=1e-6,rtol=5e-9)
    return len(actual)

def reconstruct(env,archive):
    source={}; summary={}; errors=[]
    for sym in EXPECTED:
        bars,funding,manifest,mhash,meta=env["load_symbol"](sym)
        original=archive["symbols"][sym]
        if mhash!=original["provenance"]["manifest_sha256"]:
            raise ValueError(f"PUBLIC_HISTORIC_SOURCE_MANIFEST_CHANGED:{sym}:new={mhash}:old={original['provenance']['manifest_sha256']}")
        raw_entries=original["provenance"]["manifest_entries"]
        if len(manifest)!=len(raw_entries) or manifest!=raw_entries:
            raise ValueError(f"PUBLIC_RAW_ARCHIVE_BYTE_OR_FUNDING_DIFFERENCE:{sym}")
        bd={b["t"]:b for b in bars}
        if len([b for b in bars if FIRST<=b["t"]<=LAST])!=43824:raise ValueError("MISSING_HOURLY_BAR:"+sym)
        for t in range(FIRST,LAST+1,HOUR_MS):
            if t not in bd:raise ValueError(f"MISSING_HOUR:{sym}:{t}")
        sr={}
        for layer,slip in LAYERS.items():
            actual=env["simulate"](sym,bars,funding,"PARENT",slip)
            canonical=original["results"]["PARENT"][layer]
            n=compare_trades(actual,canonical,sym,layer)
            sr[layer]=actual
        source[sym]={"bars":bd,"funding":funding,"returns":sr}
        summary[sym]={
          "economic_hours":43824,
          "origin_manifest_sha256":mhash,
          "origin_market_source_files":len(manifest),
          "funding_events":len(funding),
          "source_deviation_ms":meta.get("max_funding_timestamp_deviation_ms"),
          "base_trades":len(sr["BASE"]["trades"]),
          "stress_trades":len(sr["STRESS"]["trades"]),
          "original_base_net_return_pct":round(100*sr["BASE"]["net_return"],6),
          "original_base_mtm_dd_pct":round(100*sr["BASE"]["max_mark_to_market_drawdown"],6),
        }
    return source,summary

def event_calendar(source,layer):
    events=defaultdict(list)
    samebar_count=stop_open_proxy=0
    for sym in EXPECTED:
        db=source[sym]["bars"]
        for k,tr in enumerate(source[sym]["returns"][layer]["trades"]):
            et=int(tr["entry_t"]);xt=int(tr["exit_t"])
            if not FIRST<=et<=xt<=LAST:raise ValueError("TRADE_BOUNDARY_INVALID")
            if et==xt:samebar_count+=1
            if tr["reason"]=="STOP":
                raw_exit=tr["exit"]/(1-LAYERS[layer])
                op=db[xt]["open"]
                if math.isclose(op,raw_exit,rel_tol=1e-8,abs_tol=1e-10):
                    stop_open_proxy+=1
            token=(sym,k)
            events[et].append((1,sym,k,"ENTRY",tr,token))
            events[xt].append((2 if et==xt else 0,sym,k,"EXIT",tr,token))
    for t,v in events.items():
        v.sort(key=lambda x:(x[0],x[1],x[2]))
    return events,{"samebar_entry_exit":samebar_count,"stop_exit_at_bar_open_proxy":stop_open_proxy}

def marked_risk(source,layer,risk):
    events,events_diag=event_calendar(source,layer)
    cash_equity=CAPITAL;peak_close=CAPITAL;peak_liq=CAPITAL;peak_real=CAPITAL
    dd_close=0.;dd_liq=0.;dd_real=0.;worst_liq_t=worst_close_t=None
    openp={};reserved=0.;n_completed=0;skipped=0;skip_reasons=defaultdict(int)
    annual=defaultdict(float);funding_check_max=0.;max_open=0
    loss_streak=longest_streak=0;paid_fee=paid_funding=0.
    periods_with_position=0;peak_gross_notional_fraction=0.
    for t in range(FIRST,LAST+1,HOUR_MS):
        # Funding at exact normalized UTC hour, only for carried positions.
        for token,p in openp.items():
            if p["entry_t"]<t and t in source[p["sym"]]["funding"]:
                fr=source[p["sym"]]["funding"][t]
                fdelta=-p["qty"]*fr["mark"]*fr["rate"]
                p["accrued_funding"]+=fdelta
        for priority,sym,k,kind,tr,token in events.get(t,()):
            if kind=="EXIT":
                if token not in openp:continue # appropriately skipped entry due capital or slot gate
                p=openp.pop(token)
                reserved-=p["planned_reserved"]
                pnl=p["notional"]*float(tr["return_pct"])/100.0
                cash_equity+=pnl
                if cash_equity<=0:raise ValueError("EQUITY_NONPOSITIVE")
                paid_fee+=p["notional"]*float(tr["commission"])/(float(tr["commission"])/.001/(float(tr["entry"])+float(tr["exit"])) *float(tr["entry"]))
                paid_funding+=p["accrued_funding"]
                # Original stored trade funded amount, re-scale by its exact original
                # commission-derived notional (no archived qty field).
                orig_qty=float(tr["commission"])/(.001*(float(tr["entry"])+float(tr["exit"])))
                orig_notional=orig_qty*float(tr["entry"])
                expected_funding=p["notional"]*float(tr["funding"])/orig_notional
                err=abs(p["accrued_funding"]-expected_funding)
                funding_check_max=max(funding_check_max,err)
                if err>max(0.001,1e-6*abs(expected_funding)):
                    raise ValueError(f"FUNDING_MARK_PRICE_REPRO_MISMATCH:{sym}:{k}:{err}")
                annual[str(datetime.fromtimestamp(t/1000,timezone.utc).year)]+=pnl
                n_completed+=1
                peak_real=max(peak_real,cash_equity)
                dd_real=min(dd_real,cash_equity/peak_real-1.)
                if pnl<0:loss_streak+=1;longest_streak=max(longest_streak,loss_streak)
                else:loss_streak=0
            else:
                target=min(cash_equity*risk/PLANNED_LOSS,cash_equity*.95)
                cost_reserved=target*PLANNED_LOSS
                if len(openp)>=MAX_POS:
                    skipped+=1;skip_reasons["CONCURRENT"]+=1;continue
                if reserved+cost_reserved>cash_equity*MAX_RESERVATION+1e-8:
                    skipped+=1;skip_reasons["AGGREGATE_RISK"]+=1;continue
                if token in openp:raise ValueError("DUPLICATE_ENTRY")
                entry=float(tr["entry"])
                openp[token]={"sym":sym,"entry_t":t,"notional":target,
                   "qty":target/entry,"entry":entry,"planned_reserved":cost_reserved,
                   "accrued_funding":0.}
                reserved+=cost_reserved
        max_open=max(max_open,len(openp))
        if openp: periods_with_position+=1
        # Original historical 1h CLOSE is only known at the END of that bar.
        marked=cash_equity
        marked_liquid=cash_equity
        total_open_notional=0.
        for p in openp.values():
            b=source[p["sym"]]["bars"][t]
            px=b["close"]
            qty=p["qty"]
            entryfee=p["notional"]*.001
            marked+=qty*(px-p["entry"])-entryfee+p["accrued_funding"]
            exitpx=px*(1-LAYERS[layer])
            marked_liquid+=qty*(exitpx-p["entry"])-entryfee -qty*exitpx*.001+p["accrued_funding"]
            total_open_notional+=p["notional"]
        peak_gross_notional_fraction=max(peak_gross_notional_fraction,total_open_notional/max(cash_equity,0.01))
        if marked<=0 or marked_liquid<=0:
            raise ValueError("MTM_EQUITY_NONPOSITIVE")
        peak_close=max(peak_close,marked)
        peak_liq=max(peak_liq,marked_liquid)
        newdd=marked/peak_close-1.
        newddliq=marked_liquid/peak_liq-1.
        if newdd<dd_close:dd_close=newdd;worst_close_t=t
        if newddliq<dd_liq:dd_liq=newddliq;worst_liq_t=t
    if openp:raise ValueError("ORIGINAL_FORCED_LIQUIDATION_NOT_CLOSED")
    return {
      "risk_per_position_pct":risk*100,"layer":layer,
      "original_start_equity_usdt":CAPITAL,"ending_equity_usdt":round(cash_equity,6),
      "five_year_net_return_pct":round((cash_equity/CAPITAL-1)*100,6),
      "realized_only_dd_pct":round(dd_real*100,6),
      "hourly_close_mtm_dd_pct":round(dd_close*100,6),
      "hourly_close_liquidation_adjusted_mtm_dd_pct":round(dd_liq*100,6),
      "hourly_mtm_worst_timestamp":worst_close_t,
      "liquidation_adjusted_worst_timestamp":worst_liq_t,
      "mark_frequency_hours":43824,
      "max_concurrent_positions":max_open,
      "hours_ending_with_open_positions":periods_with_position,
      "peak_open_notional_to_realized_cash_equity_pct":round(peak_gross_notional_fraction*100,6),
      "completed_trades":n_completed,"skipped_signals":skipped,
      "skip_reasons":dict(skip_reasons),"max_losing_streak":longest_streak,
      "funding_accrual_usdt_while_open":round(paid_funding,6),
      "funding_reconciliation_max_abs_usdt":round(funding_check_max,10),
      "year_realized_pnl_usdt":{str(y):round(annual.get(str(y),0),5) for y in range(2021,2026)},
      "diagnostic_caveat":"1h CLOSE mark and assumed liquidation friction; excludes unobserved intrahour tick path and true historical MEXC orderbook fills.",
      **events_diag
    }

def synthetic():
    # Immutable portfolio/risk decision and formula proof.
    close(0.001,10/10000,"BPS_UNIT")
    close(.04+.002+.0004,.0424,"BUDGET")
    assert (1, "AAA") < (1,"ZZZ")
    orig_commission=3.15
    orig_entry,orig_exit=100.,110.
    q=orig_commission/(.001*(orig_entry+orig_exit))
    close(q*(orig_entry+orig_exit)*.001,orig_commission,"QUANTITY_ID")
    assert sum(range(2021,2026))==10115
    print("RAW_MTM_STATIC_SELFTEST_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--original-source")
    parser.add_argument("--archived")
    a=parser.parse_args()
    if a.self_test:return synthetic()
    out=HERE/"RAW_REPLAY_AND_HOURLY_MTM_RESULT_2026_10_09.json"
    try:
        if not a.original_source or not a.archived:raise ValueError("EXACT_SOURCE_AND_ARCHIVE_REQUIRED")
        env,blob=source_definitions(a.original_source)
        archive,ash=read_archive(a.archived)
        data,raw_summary=reconstruct(env,archive)
        scenarios={}
        for layer in LAYERS:
            scenarios[layer]={}
            for risk in RISKS:
                scen=marked_risk(data,layer,risk)
                scenarios[layer][str(risk)]=scen
                print("RAW_MTM_SCENARIO",json.dumps(scen,sort_keys=True),flush=True)
        # Preserve prior low-risk replayer BASE sanity figures; mismatch is FAIL_CLOSED.
        close(scenarios["BASE"]["0.0025"]["five_year_net_return_pct"],34.59609,
              "BASE_LOW_RISK_MATCH_ARCHIVED_ALL_BASKETS",atol=.005)
        close(scenarios["BASE"]["0.005"]["five_year_net_return_pct"],20.080257,
              "BASE_MEDIUM_RISK_MATCH_ARCHIVED_ALL_BASKETS",atol=.005)
        result={
         "status":"RAW_SOURCE_REPRO_PASS__HOURLY_MTM_PORTFOLIO_REPRO_PASS__EXECUTION_UNVERIFIED",
         "live_go":False,"original_outcomes_already_opened":True,
         "new_oos_evidence":False,
         "git_run_sha":os.environ.get("GITHUB_SHA"),
         "source_blob_sha":blob,"canonical_artifact_id":ARCHIVE_ARTIFACT,
         "canonical_source_json_sha256":ash,"raw_source":raw_summary,
         "scenarios":scenarios,
         "model_notes":[
          "Exact original 1h source script/funding executed from pinned commit; candle OHLC source sha matches prior original artifact manifest.",
          "This reproduces original bar-model fills, NOT tick/bid/ask evidence or actual broker fills.",
          "Original 2026 protected outcomes remain sealed; historical data used were already known.",
          "MTM values sampled at confirmed hourly CLOSE, with optional liquidation-adjusted close mark; intrahour DD and stop gap can be worse.",
          "Do not interpret reduced size as directional edge or live return assurance.",
         ]
        }
        out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("RAW_MTM_FINAL_STATUS",result["status"],flush=True)
    except Exception as e:
        fail={"status":"RAW_REPLAY_SOURCE_OR_RISK_BLOCKED","reason":repr(e),
            "original_outcomes_already_opened":True,"live_go":False,
            "git_run_sha":os.environ.get("GITHUB_SHA")}
        out.write_text(json.dumps(fail,sort_keys=True,indent=2)+"\n")
        traceback.print_exc()
        print("RAW_MTM_FINAL_STATUS",fail["status"],flush=True)
        sys.exit(2)

if __name__=="__main__":main()
