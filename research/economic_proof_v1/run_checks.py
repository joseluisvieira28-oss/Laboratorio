"""Offline test harness; deny outbound sockets and keep temporary files local."""
from pathlib import Path
import argparse
import hashlib
import json
import socket
import tempfile
import unittest


def deny(*args, **kwargs):
    raise RuntimeError("NETWORK_FORBIDDEN_DURING_OFFLINE_TESTS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", help="Create a new local verification JSON; never overwrite")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    scratch = root / ".economic-proof-test-tmp"
    scratch.mkdir(exist_ok=True)
    tempfile.tempdir = str(scratch)
    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    # Separate discover calls avoid namespace ambiguity in these script-based labs.
    import sys
    sys.path.insert(0, str(root/"research/economic_proof_v1"))
    sys.path.insert(0, str(root/"research/deribit_diamante_v2"))
    suite = unittest.TestSuite()
    for directory in ("deribit_diamante_v2", "economic_proof_v1"):
        suite.addTests(unittest.defaultTestLoader.discover(str(root/"research"/directory), pattern="test_*.py", top_level_dir=str(root/"research"/directory)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.receipt:
        receipt = dict(status="PASS" if result.wasSuccessful() else "FAIL", tests=result.testsRun,
                       failures=len(result.failures), errors=len(result.errors), market_requests=0,
                       network="socket connections denied", synthetic_fixtures_are_not_trades=True,
                       source_commit="7a7d58336f68ea483e00a3c7623c4e5777263da5",
                       python_sources_sha256={str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                                              for directory in ("economic_proof_v1", "deribit_diamante_v2")
                                              for p in sorted((root/"research"/directory).glob("*.py"))})
        with Path(args.receipt).open("x") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
    raise SystemExit(not result.wasSuccessful())
