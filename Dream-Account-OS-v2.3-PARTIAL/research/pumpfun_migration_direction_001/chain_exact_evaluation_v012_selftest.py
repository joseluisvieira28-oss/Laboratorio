#!/usr/bin/env python3
"""Synthetic positive-control self-test for PMD-001 V0.12 evaluator."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def main() -> None:
    here=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        outcomes=[]
        features=[]
        for i in range(1012):
            mint=f"synthetic_{i:04d}"
            # Stable monotone synthetic return in [-0.30,+0.30].
            y=(i-505.5)/1685.0
            outcomes.append({
                "mint":mint,"net_return_5m":y,"execution_available":True,
                "corpus_t0":f"2026-01-{1+(i%28):02d}T00:00:00+00:00",
            })
            if i<600:
                features.append({
                    "lab":"PMD-001","stage":"CHAIN_EXACT_FEATURES_V012",
                    "economic_outcomes_opened":False,"promotion_authority":False,
                    "mint":mint,"t0":f"2026-01-{1+(i%28):02d}T00:00:00+00:00",
                    "decoder_complete_w30":True,"decoder_complete_w60":True,"decoder_complete_w300":True,
                    "net_flow_sol_w60":float(i),
                })
        fp=root/'features.jsonl';op=root/'outcomes.csv';out=root/'evaluation.json'
        fp.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in features),encoding='utf-8')
        pd.DataFrame(outcomes).to_csv(op,index=False)
        subprocess.run([
            sys.executable,str(here/'evaluate_chain_exact_features_v012.py'),
            '--features',str(fp),'--outcomes',str(op),'--out',str(out),
        ],check=True)
        r=json.loads(out.read_text())
        assert r['verdict']=='V012_REPLICATION_CANDIDATE',r['verdict']
        assert 'net_flow_sol_w60' in r['replication_candidates'],r['replication_candidates']
        assert r['promotion_authority'] is False
        print('PMD-001 V0.12 evaluator positive-control self-test: PASS')


if __name__=='__main__':
    main()
