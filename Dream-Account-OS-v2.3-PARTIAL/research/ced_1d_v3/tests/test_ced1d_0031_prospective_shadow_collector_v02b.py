#!/usr/bin/env python3
import importlib.util,io,zipfile
from datetime import date,datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"ced1d_0031_prospective_shadow_collector_v02b.py"
spec=importlib.util.spec_from_file_location("m",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def zcsv(name,header,rows):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        txt=",".join(header)+"\n"+"\n".join(",".join(map(str,r)) for r in rows)+"\n"
        z.writestr(name,txt)
    return b.getvalue()

# Boundary constants.
assert m.FIRST_SIGNAL_DAY==date(2026,9,21)
assert m.FIRST_SIGNAL_COMPLETION.isoformat()=="2026-09-22T00:00:00+00:00"
assert m.FIRST_ENTRY_TS==int(datetime(2026,9,22,0,1,tzinfo=timezone.utc).timestamp()*1000)

# Frozen public-source URL shapes.
assert m.daily_kline_url("klines",date(2026,9,21)).endswith("/klines/AVAXUSDT/1m/AVAXUSDT-1m-2026-09-21.zip")
assert m.daily_agg_url(date(2026,9,19)).endswith("/aggTrades/AVAXUSDT/AVAXUSDT-aggTrades-2026-09-19.zip")
assert m.daily_bookdepth_url(date(2026,9,19)).endswith("/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-09-19.zip")

# Corrected USD-M public funding transport.\nassert m.PUBLIC_API=="https://fapi.binance.com"\n\n# aggTrades proxy: BUY consumes wasBuyerMaker=false; SELL consumes true.
t=1_800_000_000_000
agg=[
 (t-1,10.0,100.0,False),
 (t+100,10.0,4.0,True),   # SELL-side visible quote 40
 (t+200,10.0,6.0,True),   # reaches 100
 (t+300,10.0,5.0,False),  # BUY quote 50
 (t+400,10.0,5.0,False),  # reaches 100
]
buy=m.agg_proxy(agg,t,"BUY");sell=m.agg_proxy(agg,t,"SELL")
assert buy["filled"] and abs(buy["vwap"]-10)<1e-12 and buy["latency_ms"]==400,buy
assert sell["filled"] and abs(sell["vwap"]-10)<1e-12 and sell["latency_ms"]==200,sell
late=m.agg_proxy([(t+5001,10,100,False)],t,"BUY")
assert not late["filled"],late

# bookDepth uses latest PRIOR snapshot, never future; BUY=+1, SELL=-1.
snaps={
 t-30_000:{-1.0:{"depth":1,"notional":90},1.0:{"depth":1,"notional":150}},
 t-10_000:{-1.0:{"depth":1,"notional":200},1.0:{"depth":1,"notional":250}},
 t+1_000:{-1.0:{"depth":1,"notional":9999},1.0:{"depth":1,"notional":9999}},
}
b=m.book_capacity(snaps,t,"BUY");s=m.book_capacity(snaps,t,"SELL")
assert b["snapshot_ts_ms"]==t-10_000 and b["capacity_ok"] and b["notional"]==250,b
assert s["snapshot_ts_ms"]==t-10_000 and s["capacity_ok"] and s["notional"]==200,s
stale=m.book_capacity({t-60_001:{1.0:{"depth":1,"notional":1000}}},t,"BUY")
assert not stale["snapshot_ok"] and not stale["capacity_ok"],stale

# Funding lower/upper formula exactly mirrors frozen 2025 runner.
entry=datetime(2026,9,22,0,1,tzinfo=timezone.utc)
exitd=datetime(2026,9,23,0,1,tzinfo=timezone.utc)
ft=int(datetime(2026,9,22,8,0,tzinfo=timezone.utc).timestamp()*1000)
minute=(ft//60000)*60000
ev=[{"event_id":"CED1D-0031:2026-09-21","signal_day":"2026-09-21","status":"TRADE","direction":1,
     "entry_day":"2026-09-22","exit_day":"2026-09-23","entry_ts_ms":int(entry.timestamp()*1000),
     "exit_ts_ms":int(exitd.timestamp()*1000),"entry_open":10.0,"reference_gross_bps":20.0}]
m.add_funding_bounds(ev,[{"fundingTime":ft,"fundingRate":0.001}],{minute:{"low":9.0,"high":11.0}})
# Long pays positive funding. coeff=-0.001/10; bounds are -11 and -9 bps.
assert abs(ev[0]["funding_lower_bps"]+11.0)<1e-9,ev[0]
assert abs(ev[0]["funding_upper_bps"]+9.0)<1e-9,ev[0]
assert abs(ev[0]["reference_base_lower_bps"]-(20-14-11))<1e-9,ev[0]

# Complete week counting: first full prospective week is Mon 2026-09-21.
assert m.complete_signal_weeks(date(2026,9,26))==[]
ws=m.complete_signal_weeks(date(2026,11,15))
assert len(ws)==8,ws
assert ws[0]==date(2026,9,21) and ws[-1]==date(2026,11,9),ws

# Accumulating routing must not make an early Tier-1 claim.
rows=[]
for i in range(10):
    sd=date(2026,9,21)+timedelta(days=i)
    ed=sd+timedelta(days=1); xd=sd+timedelta(days=2)
    rows.append({
      "event_id":f"CED1D-0031:{sd}","signal_day":sd.isoformat(),"status":"TRADE","direction":1,
      "entry_day":ed.isoformat(),"exit_day":xd.isoformat(),
      "reference_base_lower_bps":5.0,"reference_stress_lower_bps":1.0,
      "entry_agg_filled":True,"exit_agg_filled":True,"agg_complete_pair":True,
      "entry_agg_latency_ms":100,"exit_agg_latency_ms":100,
      "execution_base_funded_bps":5.0,"execution_stress_funded_bps":3.0,
      "execution_total_nonfunding_base_proxy_bps":8.0,
      "entry_book_snapshot_ok":True,"exit_book_snapshot_ok":True,
      "entry_book_capacity_ok":True,"exit_book_capacity_ok":True,
    })
met=m.metrics_and_routing(rows,date(2026,10,4))
assert met["operational_checkpoint_pass"] is True,met
assert met["tier1_minimum_sample_pass"] is False,met
assert met["routing"]=="SHADOW_ACCUMULATING",met

print("CED1D_0031_PROSPECTIVE_SHADOW_V02B_SYNTHETIC_QA_PASS")


# V0.2 warm-up acquisition must follow VALID observations, not calendar-day count.
_orig_build=m.build_price_bars
calls=[]
def _fake_build(start_day,end_day,role="SHADOW_PATH"):
    assert start_day==end_day or role=="SHADOW_SIGNAL_OR_PATH"
    if role=="SHADOW_SIGNAL_OR_PATH":
        # Main prospective path can be a minimal synthetic valid sequence for this pure acquisition test.
        rows=[]
        d=start_day
        while d<=end_day:
            rows.append({"date":d.isoformat(),"valid_day":True})
            d+=timedelta(days=1)
        return rows,[]
    calls.append(start_day)
    # Make one pre-boundary calendar day invalid; collector must walk one extra day backward.
    valid = start_day != date(2026,9,10)
    return [{"date":start_day.isoformat(),"valid_day":valid}],[{"role":role,"day":start_day.isoformat(),"valid_day":valid}]
m.build_price_bars=_fake_build
bars,src=m.build_shadow_price_bars(date(2026,9,21))
prior=[b for b in bars if b["date"]<"2026-09-21" and b["valid_day"]]
assert len(prior)==20,(len(prior),calls)
assert len(calls)==21,(len(calls),calls)
assert calls[0]==date(2026,9,20) and calls[-1]==date(2026,8,31),(calls[0],calls[-1])
assert all(x["role"]=="LOOKBACK_INPUT_ONLY" for x in src),src
m.build_price_bars=_orig_build

print("CED1D_0031_PROSPECTIVE_SHADOW_V02B_VALID_DAY_WARMUP_QA_PASS")
