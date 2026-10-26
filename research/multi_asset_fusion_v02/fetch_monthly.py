"""Download only the frozen 319 public monthly ZIP/CHECKSUM pairs.
Cached files remain subject to run.py's hash and content checks.
"""
import argparse,json
from pathlib import Path
import reference_replay as r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);x=p.parse_args()
    receipts=r.fetch_all(x.cache)
    r.write_json(x.cache/'fetch_receipts.json',receipts)
    raise SystemExit(2 if any(v['status']=='SOURCE_BLOCKED' for v in receipts) else 0)
