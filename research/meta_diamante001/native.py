import sys
from pathlib import Path
root=Path(__file__).resolve().parent
from legacy_replay import get,src
from research.convex_8alt_5m_common_20261013 import native5m
for a in ['BNB','SOL']:
    sys.argv=['native','--symbol',a+'USDT','--output-dir',str(root/'out/legacy'/(a+'5m'))]
    native5m.main()
