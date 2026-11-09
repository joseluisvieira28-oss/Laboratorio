"""Synthetic artifact transport drill; all Git remotes are local, no market."""
import argparse
import json
import os
from pathlib import Path
import socket
import tempfile

import cloud_runner as runner
import recovery
import test_cloud_runner as git_fixture
import test_collector as fixture
import v3_archive_audit


def denied(*args, **kwargs):
    raise RuntimeError('MARKET_NETWORK_FORBIDDEN')


def prepare(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'synthetic-only'
        attempt, _ = fixture.CollectorTests().run_attempt(root)
        day = str(fixture.T.date())
        runner.immutable(root / 'reservations' / (day + '.json'), runner.canonical(
            dict(day=day, status='RESERVED_BEFORE_MARKET', orders=0)))
        runner.immutable(root / 'completions' / (day + '.json'), runner.canonical(dict(
            attempt=attempt.name, receipt_sha256=runner.sha((attempt / 'receipt.json').read_bytes()))))
        result = recovery.pack(root, day, directory / 'evidence.zip')
    print(json.dumps(dict(kind='SYNTHETIC_RECOVERY_DRILL', production_sessions=0, **result)))
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('sha256=' + result['sha256'] + '\n')


def restore(directory, checksum):
    with tempfile.TemporaryDirectory() as tmp:
        work, bare = git_fixture.repo(tmp)
        root = work / runner.REL
        runner.immutable(root / '.gitattributes', b'* -text\n')
        recovery.restore(directory / 'evidence.zip', checksum, root)
        runner.publish(work, root, 'synthetic recovered artifact')
        fresh = Path(tmp) / 'fresh'
        git_fixture.git(tmp, '-c', 'core.longpaths=true', 'clone', '-b', runner.BRANCH, str(bare), str(fresh))
        report = v3_archive_audit.audit_archive(fresh / runner.REL)
        assert report['independent_valid'] == 1
        print(json.dumps(dict(status='CLOUD_ARTIFACT_ROUNDTRIP_PASS', synthetic=True,
                              fixture_valid=1, production_sessions=0, market_requests=0,
                              git_remote='LOCAL_BARE_ONLY', orders=0, net_pnl=None)))


if __name__ == '__main__':
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'restore'])
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    prepare(args.directory) if args.mode == 'prepare' else restore(args.directory, args.sha256)
