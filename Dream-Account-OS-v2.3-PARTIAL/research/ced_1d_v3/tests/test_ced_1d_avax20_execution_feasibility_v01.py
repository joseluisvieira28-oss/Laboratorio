#!/usr/bin/env python3
import importlib.util,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"ced_1d_avax20_execution_feasibility_v01.py"
spec=importlib.util.spec_from_file_location("x",P)
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)

# Side mapping + 100 USDT VWAP fill.
t=1736208060000
groups={(t,"BUY"):{"target_ts_ms":t,"side":"BUY","legs":[{"event_id":"e1","leg":"ENTRY"}],
                    "required_quote":100.0,"filled_quote":0.0,"base_qty":0.0,"quote_value":0.0,
                    "last_fill_ts_ms":None,"vwap":None,"filled":False}}
x.consume_trade(groups,t,10.0,4.0,False)     # 40 USDT buyer-taker
x.consume_trade(groups,t+200,12.0,10.0,False) # clips remaining 60 USDT
g=groups[(t,"BUY")]
assert g["filled"] is True
assert math.isclose(g["filled_quote"],100.0,abs_tol=1e-9)
expected_qty=4.0+60.0/12.0
assert math.isclose(g["vwap"],100.0/expected_qty,rel_tol=0,abs_tol=1e-12)
assert g["last_fill_ts_ms"]==t+200

# Wrong side must not fill.
groups={(t,"SELL"):{"target_ts_ms":t,"side":"SELL","legs":[{"event_id":"e2","leg":"ENTRY"}],
                    "required_quote":100.0,"filled_quote":0.0,"base_qty":0.0,"quote_value":0.0,
                    "last_fill_ts_ms":None,"vwap":None,"filled":False}}
x.consume_trade(groups,t,10.0,20.0,False)
assert groups[(t,"SELL")]["filled_quote"]==0.0
x.consume_trade(groups,t+100,10.0,20.0,True)
assert groups[(t,"SELL")]["filled"] is True

# 5s boundary included; after boundary forbidden.
groups={(t,"BUY"):{"target_ts_ms":t,"side":"BUY","legs":[{"event_id":"e3","leg":"ENTRY"}],
                    "required_quote":100.0,"filled_quote":0.0,"base_qty":0.0,"quote_value":0.0,
                    "last_fill_ts_ms":None,"vwap":None,"filled":False}}
x.consume_trade(groups,t+5001,10.0,20.0,False)
assert groups[(t,"BUY")]["filled"] is False
x.consume_trade(groups,t+5000,10.0,20.0,False)
assert groups[(t,"BUY")]["filled"] is True

# Simultaneous same-side legs require aggregate capacity, not reused capacity.
events=[
 {"event_id":"a","entry_ts_ms":t,"exit_ts_ms":t+86400000,"direction":1},
 {"event_id":"b","entry_ts_ms":t,"exit_ts_ms":t+86400000,"direction":1},
]
gs=x.build_groups(events)
assert gs[(t,"BUY")]["required_quote"]==200.0

assert x.as_bool("true") is True
assert x.as_bool("false") is False
assert x.norm_ms(1736208060000000)==1736208060000

print("CED1D_AVAX20_EXECUTION_SYNTHETIC_QA_PASS")
