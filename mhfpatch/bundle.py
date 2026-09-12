"""Hash-pinned binary deltas, complete preflight, atomic writes and rollback."""
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

import bsdiff4
from .crypto import decode_ecd, encrypt

MAX_FILE = 256 * 1024 * 1024
MAX_PATCH = 64 * 1024 * 1024
BACKUPS = '.mhf-translation-backups'


class PatchError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_relative(relative):
    if not isinstance(relative, str) or any(c in relative for c in ('\\', ':', '\0')):
        raise PatchError('Invalid manifest path')
    name = PurePosixPath(relative)
    if (name.is_absolute() or '..' in name.parts or not name.parts
            or name.as_posix() != relative or name.parts[0] == BACKUPS):
        raise PatchError(f'Unsafe manifest path: {relative}')


def safe_path(root, relative):
    validate_relative(relative)
    root = Path(root).resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise PatchError(f'Path escapes target directory: {relative}')
    return target


def require_client_closed():
    names = {'mhf.exe', 'mhfo.exe', 'mhfo-hd.exe'}
    if sys.platform == 'win32':
        try:
            result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True,
                                    text=True, check=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:
            raise PatchError('Cannot verify that Monster Hunter is closed') from exc
        active = [row[0] for row in csv.reader(io.StringIO(result.stdout)) if row and row[0].lower() in names]
    elif sys.platform.startswith('linux'):
        if Path('/proc/1/comm').read_text().strip() != 'systemd':
            raise PatchError('Run the patcher on the Linux host, outside process containers')
        active = []
        for path in Path('/proc').glob('[0-9]*/comm'):
            try:
                name = path.read_text().strip().lower()
            except (FileNotFoundError, ProcessLookupError):
                continue
            if name in names:
                active.append(path.parent.name)
    else:
        raise PatchError('Client installation supports Windows and Linux hosts')
    if active:
        raise PatchError('Close Monster Hunter before changing files: ' + ', '.join(active))


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise PatchError('Invalid patch manifest')
    if manifest.get('schema') != 1 or manifest.get('kind') not in {'client', 'server'}:
        raise PatchError('Unsupported patch manifest')
    rows = manifest.get('files')
    if not isinstance(rows, list):
        raise PatchError('Missing patch file list')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise PatchError('Invalid patch file entry')
        validate_relative(row.get('path'))
        folded = row['path'].casefold()
        if folded in seen:
            raise PatchError('Duplicate patch target: ' + row['path'])
        seen.add(folded)
        for key in ('source_sha256', 'target_sha256', 'patch_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', row.get(key, '')):
                raise PatchError('Invalid SHA256 in manifest')
        for key in ('source_size', 'target_size'):
            if not isinstance(row.get(key), int) or not 0 <= row[key] <= MAX_FILE:
                raise PatchError('Invalid file size in manifest')
        if row.get('encoding') not in {'raw', 'ecd'}:
            raise PatchError('Unsupported patch encoding')
        if row.get('patch') != 'patches/' + row['patch_sha256'] + '.bsdiff':
            raise PatchError('Invalid patch member name')
        if row['encoding'] == 'ecd':
            try:
                header = bytes.fromhex(row['target_header'])
                valid = (len(header) == 16 and header[:4] == b'ecd\x1a'
                         and struct.unpack_from('<I', header, 8)[0] + 16 == row['target_size'])
            except (KeyError, ValueError, struct.error):
                valid = False
            if not valid:
                raise PatchError('Invalid ECD target header')
    return manifest


def load_manifest(archive):
    names = archive.namelist()
    if len(set(names)) != len(names):
        raise PatchError('Duplicate members in patch bundle')
    if archive.getinfo('manifest.json').file_size > 128 * 1024 * 1024:
        raise PatchError('Patch manifest is too large')
    return validate_manifest(json.loads(archive.read('manifest.json')))


def patch_bytes(archive, row):
    if archive.getinfo(row['patch']).file_size > MAX_PATCH:
        raise PatchError('Patch payload is too large')
    data = archive.read(row['patch'])
    if sha(data) != row['patch_sha256']:
        raise PatchError('Corrupt patch: ' + row['path'])
    expected = row['target_size'] - (16 if row['encoding'] == 'ecd' else 0)
    if len(data) < 32 or data[:8] != b'BSDIFF40' or int.from_bytes(data[24:32], 'little') != expected:
        raise PatchError('Patch output size does not match manifest: ' + row['path'])
    return data


def build_bundle(output, source_root, target_root, paths, kind, metadata=None, progress=None):
    output = Path(output)
    if output.exists():
        raise PatchError('Refusing to overwrite an existing bundle')
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []; stored = set()
    try:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for index, relative in enumerate(paths):
                source = safe_path(source_root, relative).read_bytes()
                target = safe_path(target_root, relative).read_bytes()
                if len(source) > MAX_FILE or len(target) > MAX_FILE:
                    raise PatchError('Input exceeds file size bound: ' + relative)
                if source == target:
                    continue
                ecd = source[:4] == target[:4] == b'ecd\x1a'
                before = decode_ecd(source) if ecd else source
                after = decode_ecd(target) if ecd else target
                delta = bsdiff4.diff(before, after)
                if len(delta) > MAX_PATCH:
                    raise PatchError('Generated delta exceeds size bound: ' + relative)
                if bsdiff4.patch(before, delta) != after:
                    raise PatchError('Generated delta failed verification: ' + relative)
                if ecd and encrypt(after, meta=target[:16]) != target:
                    raise PatchError('Target encryption is not reproducible: ' + relative)
                digest = sha(delta); member = 'patches/' + digest + '.bsdiff'
                if digest not in stored:
                    archive.writestr(member, delta); stored.add(digest)
                row = dict(path=relative, source_sha256=sha(source), target_sha256=sha(target),
                           source_size=len(source), target_size=len(target),
                           encoding='ecd' if ecd else 'raw', patch=member, patch_sha256=digest)
                if ecd:
                    row['target_header'] = target[:16].hex()
                rows.append(row)
                if progress:
                    progress(index + 1, len(paths), relative)
            manifest = dict(schema=1, kind=kind, metadata=metadata or {}, files=rows)
            validate_manifest(manifest)
            archive.writestr('manifest.json', json.dumps(manifest, separators=(',', ':')))
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return dict(files=len(rows), unique_deltas=len(stored), bytes=output.stat().st_size, sha256=sha(output.read_bytes()))


def preflight(archive, root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise PatchError('Target directory does not exist')
    manifest = load_manifest(archive)
    ready = []; already = 0; checked = {}
    for row in manifest['files']:
        path = safe_path(root, row['path'])
        if not path.is_file():
            raise PatchError('Missing required file: ' + row['path'])
        if path.stat().st_size > MAX_FILE:
            raise PatchError('Unexpected file size: ' + row['path'])
        current = sha(path.read_bytes())
        if current == row['target_sha256']:
            already += 1
        elif current == row['source_sha256']:
            ready.append(row)
        else:
            raise PatchError('Unsupported version or newer edits: ' + row['path'])
        if row['patch'] not in checked:
            patch_bytes(archive, row)
            checked[row['patch']] = row['target_size'] - (16 if row['encoding'] == 'ecd' else 0)
        elif checked[row['patch']] != row['target_size'] - (16 if row['encoding'] == 'ecd' else 0):
            raise PatchError('Shared patch has conflicting output sizes')
    return manifest, ready, already


def check_bundle(bundle, root):
    with zipfile.ZipFile(bundle) as archive:
        manifest, ready, already = preflight(archive, root)
    return dict(kind=manifest['kind'], ready=len(ready), already_patched=already,
                verified=len(manifest['files']))


def atomic_copy(source, target, observed, expected):
    fd, temporary = tempfile.mkstemp(prefix='.mhf-patch-', dir=target.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temporary)
        if sha(Path(temporary).read_bytes()) != expected:
            raise PatchError('Staged copy verification failed: ' + str(target))
        if sha(target.read_bytes()) != observed:
            raise PatchError('File changed during operation: ' + str(target))
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_journal(path, journal):
    fd, temporary = tempfile.mkstemp(prefix='.journal-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(journal, output, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply_bundle(bundle, root, progress=None):
    root = Path(root).resolve()
    with zipfile.ZipFile(bundle) as archive:
        manifest, ready, already = preflight(archive, root)
        if not ready:
            return dict(changed=0, already_patched=already, backup=None)
        if manifest['kind'] == 'client':
            require_client_closed()
        parent = root / BACKUPS
        if parent.is_symlink():
            raise PatchError('Backup directory must not be a symlink')
        parent.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-'), dir=parent))
        # Prepare every output and backup before changing any installed file.
        try:
            for row in ready:
                path = safe_path(root, row['path']); source = path.read_bytes()
                if sha(source) != row['source_sha256']:
                    raise PatchError('File changed during preparation: ' + row['path'])
                plain = decode_ecd(source) if row['encoding'] == 'ecd' else source
                output = bsdiff4.patch(plain, patch_bytes(archive, row))
                if row['encoding'] == 'ecd':
                    output = encrypt(output, meta=bytes.fromhex(row['target_header']))
                if len(output) != row['target_size'] or sha(output) != row['target_sha256']:
                    raise PatchError('Rebuilt file hash mismatch: ' + row['path'])
                original = backup / 'originals' / row['path']
                staged = backup / 'staged' / row['path']
                original.parent.mkdir(parents=True, exist_ok=True)
                staged.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, original)
                if sha(original.read_bytes()) != row['source_sha256']:
                    raise PatchError('Backup verification failed: ' + row['path'])
                staged.write_bytes(output)
                shutil.copymode(path, staged)
            for row in ready:
                if sha(safe_path(root, row['path']).read_bytes()) != row['source_sha256']:
                    raise PatchError('File changed before installation: ' + row['path'])
        except Exception:
            shutil.rmtree(backup)
            raise
        journal = dict(schema=1, kind=manifest['kind'], root=str(root), state='prepared', files=ready)
        write_journal(backup / 'backup.json', journal)
        try:
            for index, row in enumerate(ready):
                if manifest['kind'] == 'client':
                    require_client_closed()
                atomic_copy(backup / 'staged' / row['path'], safe_path(root, row['path']),
                            row['source_sha256'], row['target_sha256'])
                if progress:
                    progress(index + 1, len(ready), row['path'])
            for row in ready:
                if sha(safe_path(root, row['path']).read_bytes()) != row['target_sha256']:
                    raise PatchError('Installed file changed: ' + row['path'])
            journal['state'] = 'applied'
            write_journal(backup / 'backup.json', journal)
        except Exception as exc:
            raise PatchError(f'{exc}. Rollback backup: {backup}') from exc
        shutil.rmtree(backup / 'staged')
    return dict(changed=len(ready), already_patched=already, backup=str(backup))


def restore_backup(backup, root, progress=None):
    backup = Path(backup).resolve(); root = Path(root).resolve()
    manifest = validate_manifest(json.loads((backup / 'backup.json').read_text()))
    if manifest.get('root') != str(root):
        raise PatchError('Backup belongs to a different target directory')
    plan = []
    for row in manifest['files']:
        path = safe_path(root, row['path'])
        original = safe_path(backup / 'originals', row['path'])
        if sha(original.read_bytes()) != row['source_sha256']:
            raise PatchError('Backup hash mismatch: ' + row['path'])
        current = sha(path.read_bytes())
        if current not in {row['source_sha256'], row['target_sha256']}:
            raise PatchError('Newer edits would be overwritten: ' + row['path'])
        if current != row['source_sha256']:
            plan.append(row)
    for index, row in enumerate(plan):
        if manifest['kind'] == 'client':
            require_client_closed()
        atomic_copy(safe_path(backup / 'originals', row['path']), safe_path(root, row['path']),
                    row['target_sha256'], row['source_sha256'])
        if progress:
            progress(index + 1, len(plan), row['path'])
    return dict(changed=len(plan), verified=len(manifest['files']))
