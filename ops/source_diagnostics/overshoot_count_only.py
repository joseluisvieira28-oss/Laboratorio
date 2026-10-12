"""Count-only live transport diagnostic using exact unchanged V024 caches."""
import json,sys,time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,"research/mexc_global_assets")
import mexc_globalasset_intraday_overshoot_shadow_v024 as m
assert len(m.B["candidates"])==35
caches={"mexc":m.MexcKlineCache(m.B["candidates"]),"bitget":m.BitgetKlineCache(m.B["candidates"]),"binance":m.base.BinanceKlineCache(m.B["candidates"])}
started=datetime.now(timezone.utc).isoformat()
for c in caches.values():c.start()
time.sleep(125)
result={"started_utc":started,"observed_utc":datetime.now(timezone.utc).isoformat(),"duration_seconds":125,"scope":"SOURCE_COUNTS_ONLY_OUT_OF_SESSION_NO_ECONOMICS","economic_outcomes_scored":False,"scientific_code_changed":False,"venues":{}}
for venue,c in caches.items():
    with c.lock:
        rows=[]
        for sym in c.symbols:
            keys=sorted(c.data.get(sym.upper(),{}))
            pending=sorted(getattr(c,"pending",{}).get(sym.upper(),{}))
            rows.append({"symbol":sym,"closed_points":len(keys),"closed_timestamps":keys,"pending_points":len(pending),"pending_timestamps":pending})
    result["venues"][venue]={"connected":c.connected,"connection_errors":c.connection_errors,"symbols":rows,"symbols_with_closed_points":sum(x["closed_points"]>0 for x in rows)}
for c in caches.values():c.stop()
Path("evidence").mkdir(exist_ok=True)
Path("evidence/OVERSHOOT_SOURCE_COUNTS_2026-10-12.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,sort_keys=True))
