#!/usr/bin/env python3
import datetime as dt
from pathlib import Path
import importlib.util

P=Path(__file__).resolve().parent/"l2r_2025_source_clock_diagnostic_v01.py"
spec=importlib.util.spec_from_file_location("d",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

assert m.parse_env_ns("2025-01-01T04:00:00.123456789Z")==int(dt.datetime(2025,1,1,4,tzinfo=dt.timezone.utc).timestamp())*1_000_000_000+123456789
assert m.percentile([1,2,3,4],.5)==2.5
assert m.percentile([10],.95)==10
env=m.parse_env_ns("2025-01-01T04:00:00.100000000Z")
payload=1735704000200
assert payload*1_000_000-env==100_000_000
print("SOURCE_CLOCK_DIAGNOSTIC_SYNTHETIC_PASS 4/4")
print("NO_LEVELS_NO_PRICES_NO_OUTCOMES")
