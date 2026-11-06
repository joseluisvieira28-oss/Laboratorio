"""Offline isolated verification; never initiates market observation."""
import hashlib
import json
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
def deny(*args, **kwargs): raise RuntimeError('NETWORK_FORBIDDEN')
if __name__=='__main__':
    socket.socket.connect=deny
    socket.socket.connect_ex=deny
    socket.create_connection=deny
    scratch=ROOT/'.v3-test-tmp'; scratch.mkdir(exist_ok=True); tempfile.tempdir=str(scratch)
    suite=unittest.TestSuite()
    dirs=['deribit_diamante_v2','economic_proof_v1','deribit_v3_microstructure']
    for directory in dirs:
        path=str(ROOT/'research'/directory); sys.path.insert(0,path)
        suite.addTests(unittest.TestLoader().discover(path,pattern='test_*.py',top_level_dir=path))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    import offline_compare
    replay=offline_compare.compute()
    out=ROOT/'research/deribit_v3_microstructure/verification'
    out.mkdir(exist_ok=True)
    receipt=dict(python=platform.python_version(),tested_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        status='PASS' if result.wasSuccessful() else 'FAIL',network='socket connections denied',market_requests=0,
        historical_replay=replay, forward_sessions=0, live_go=False,
        hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                for d in dirs for p in sorted((ROOT/'research'/d).glob('*.py'))})
    with (out/'receipt.json').open('x') as f: json.dump(receipt,f,indent=2,allow_nan=False)
    raise SystemExit(not result.wasSuccessful())
