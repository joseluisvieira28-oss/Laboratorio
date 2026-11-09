"""Offline, bounded recovery of ONE UTC day's public evidence. Never pushes.

The SHA256 must come from an independently retained Actions log/receipt.
No ZIP extractall, overwrites, retries, source requests or invented receipts.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

import cloud_runner
import v3_archive_audit

LIMIT = 64 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def allowed(name, day):
    p = PurePosixPath(name)
    if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts:
        return False
    if len(p.parts) == 2:
        return (p.parts[0] in ('reservations', 'completions', 'missed_windows')
                and p.parts[1] == day + '.json') or (
                    p.parts[0] == 'prospective' and p.parts[1] == day + '.claim')
    return (len(p.parts) == 3 and p.parts[0] == 'prospective'
            and p.parts[1].startswith(day + '-')
            and p.parts[2] in ('receipt.json', 'manifest.json', 'call.json',
                               'put.json', 'index.json', 'instruments.json'))


def pack(root, day, out):
    if dt.date.fromisoformat(day).isoformat() != day:
        raise ValueError('INVALID_DAY')
    root, out = Path(root), Path(out)
    files = {}
    total = 0
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('SYMLINK_FORBIDDEN')
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if not allowed(name, day):
            continue
        total += path.stat().st_size
        if total > LIMIT:
            raise ValueError('RECOVERY_SIZE_LIMIT')
        files[name] = path.read_bytes()
    if not files:
        raise ValueError('NO_RECOVERY_FILES')
    metadata = dict(day=day, kind='V3_RECOVERY_ONLY', orders=0, net_pnl=None,
                    files={k: digest(v) for k, v in files.items()})
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('recovery.json', json.dumps(metadata, sort_keys=True))
        for name, raw in files.items():
            archive.writestr(name, raw)
    return dict(status='RECOVERY_PACKED_NOT_ARCHIVED', day=day,
                sha256=digest(out.read_bytes()), bytes=out.stat().st_size,
                files=len(files), orders=0, net_pnl=None)


def restore(bundle, expected_sha256, root, source_dir=None):
    bundle, root = Path(bundle), Path(root)
    if bundle.stat().st_size > LIMIT or digest(bundle.read_bytes()) != expected_sha256:
        raise ValueError('RECOVERY_BUNDLE_HASH_OR_SIZE')
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or 'recovery.json' not in names:
            raise ValueError('RECOVERY_DUPLICATE_OR_METADATA')
        if len(names) > 16 or sum(i.file_size for i in infos) > LIMIT or any(
                stat.S_ISLNK(i.external_attr >> 16) for i in infos):
            raise ValueError('RECOVERY_SIZE_OR_SYMLINK')
        meta = json.loads(archive.read('recovery.json'))
        day = meta['day']
        if dt.date.fromisoformat(day).isoformat() != day:
            raise ValueError('INVALID_DAY')
        if meta.get('kind') != 'V3_RECOVERY_ONLY' or meta.get('orders') != 0 or meta.get('net_pnl') is not None:
            raise ValueError('RECOVERY_CLASSIFICATION')
        if set(names) != {'recovery.json', *meta['files']}:
            raise ValueError('RECOVERY_FILE_SET')
        files = {}
        for name, expected in meta['files'].items():
            if not allowed(name, day):
                raise ValueError('RECOVERY_PATH')
            raw = archive.read(name)
            if digest(raw) != expected:
                raise ValueError('RECOVERY_FILE_HASH')
            files[name] = raw
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise ValueError('SYMLINK_FORBIDDEN')
    if root.exists() and any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('SYMLINK_FORBIDDEN')
    # Validate a merged candidate before writing any live evidence. Existing
    # identical bytes are idempotent; conflicts require human reconciliation.
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / 'archive'
        if root.exists():
            shutil.copytree(root, candidate)
        else:
            candidate.mkdir()
        for name, raw in files.items():
            dest = candidate / name
            if dest.exists() and dest.read_bytes() != raw:
                raise ValueError('RECOVERY_CONFLICT')
            if not dest.exists():
                cloud_runner.immutable(dest, raw)
        cloud_runner.verify_reservations(candidate)
        report = v3_archive_audit.audit_archive(candidate, source_dir)
    for name, raw in files.items():
        dest = root / name
        if not dest.exists():
            cloud_runner.immutable(dest, raw)
    return dict(status='RESTORED_LOCALLY_REQUIRES_GIT_PUSH_AND_REMOTE_AUDIT',
                day=day, audit=report, orders=0, net_pnl=None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('pack')
    p.add_argument('--root', required=True)
    p.add_argument('--day', required=True)
    p.add_argument('--out', required=True)
    p = commands.add_parser('restore')
    p.add_argument('--bundle', required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--root', required=True)
    args = parser.parse_args()
    result = pack(args.root, args.day, args.out) if args.command == 'pack' else restore(
        args.bundle, args.sha256, args.root)
    print(json.dumps(result, indent=2))
