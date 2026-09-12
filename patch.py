#!/usr/bin/env python3
"""Apply or restore a client/server translation bundle using matching originals."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

from mhfpatch.bundle import build_bundle, check_bundle, apply_bundle, restore_backup, PatchError


def progress(done, total, name):
    if total < 300 or done % 1000 == 0 or done == total:
        print(f'{done}/{total}: {name}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('check', 'apply'):
        sub = commands.add_parser(command)
        sub.add_argument('bundle', type=Path)
        sub.add_argument('--target', type=Path, required=True,
                         help='Client dat directory or Erupe bin directory')
    restore = commands.add_parser('restore')
    restore.add_argument('backup', type=Path)
    restore.add_argument('--target', type=Path, required=True)
    build = commands.add_parser('build', help='Maintainer: build a delta bundle from two file trees')
    build.add_argument('--source', type=Path, required=True)
    build.add_argument('--translated', type=Path, required=True)
    build.add_argument('--kind', choices=['client', 'server'], required=True)
    build.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'check':
            result = check_bundle(args.bundle, args.target)
        elif args.command == 'apply':
            result = apply_bundle(args.bundle, args.target, progress)
        elif args.command == 'restore':
            result = restore_backup(args.backup, args.target, progress)
        else:
            paths = sorted(str(p.relative_to(args.translated).as_posix())
                           for p in args.translated.rglob('*') if p.is_file()
                           and not any(part.startswith('.') for part in p.relative_to(args.translated).parts))
            result = build_bundle(args.output, args.source, args.translated, paths, args.kind, progress=progress)
    except (PatchError, OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
