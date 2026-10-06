#!/usr/bin/env python3
import importlib.util, json, re
from pathlib import Path

P=Path(__file__).with_name("source_gate_v01.py")
spec=importlib.util.spec_from_file_location("sg",P)
sg=importlib.util.module_from_spec(spec); spec.loader.exec_module(sg)

CODES=[
 "e71da970ed29453c96018af9bf107311",
 "70c0260ac77048e2895689425b1fac00",
 "9c88b57603534ad68444e209ea9d9c28",
]
for code in CODES:
    ep,r,obj=sg.detail(code)
    data=obj.get("data",{})
    raw=data.get("body","")
    rendered=sg.render_body_json(raw)
    joined=sg.norm(sg.body_plain_text(raw))
    lo=joined.lower()
    affected=bool(re.search(r"existing positions.{0,120}will be affected",lo,re.S) or "avoid any potential liquidation" in lo)
    not_affected=bool(re.search(r"existing positions.{0,120}will not be affected",lo,re.S))
    funding=("funding rate settlement frequency" in lo or
             "capped funding rate multiplier" in lo or
             "capped funding rate" in lo or
             "funding rate cap" in lo)
    times=sg.times_in_text(joined)
    ev,tables=sg.parse_tightening_tables(rendered,data.get("title",""),times)
    print("UNIT_CODE="+code)
    print("UNIT_AFFECTED="+str(affected))
    print("UNIT_NOT_AFFECTED="+str(not_affected))
    print("UNIT_FUNDING_CONFOUND="+str(funding))
    print("UNIT_TIMES="+json.dumps([x.isoformat() for x in times]))
    print("UNIT_TABLE_COUNT="+str(len(tables)))
    print("UNIT_TIGHTENING_EVENTS="+json.dumps(ev,sort_keys=True))
    print("UNIT_TABLE_META="+json.dumps(tables,sort_keys=True)[:5000])
print("UNIT_SAFETY: official source only; no market endpoints/outcomes")
