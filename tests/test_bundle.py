import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch
import zipfile

from mhfpatch.bundle import build_bundle, check_bundle, apply_bundle, restore_backup, PatchError
from mhfpatch.crypto import encrypt


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / 'original'
        self.translated = self.root / 'translated'
        self.game = self.root / 'game'
        for p in (self.original, self.translated, self.game):
            (p / 'stage').mkdir(parents=True)
        self.before = {'data.bin': b'original data bytes',
                       'stage/st200.pac': encrypt(b'original dialogue', filename='st200.pac')}
        self.after = {'data.bin': b'English data bytes',
                      'stage/st200.pac': encrypt(b'English dialogue', filename='st200.pac')}
        for relative in self.before:
            (self.original / relative).write_bytes(self.before[relative])
            (self.game / relative).write_bytes(self.before[relative])
            (self.translated / relative).write_bytes(self.after[relative])
        self.bundle = self.root / 'client.zip'
        build_bundle(self.bundle, self.original, self.translated, list(self.before), 'client')
        self.guard = patch('mhfpatch.bundle.require_client_closed')
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_apply_exact_outputs_restore_exact_originals(self):
        report = check_bundle(self.bundle, self.game)
        self.assertEqual(report['ready'], 2)
        result = apply_bundle(self.bundle, self.game)
        self.assertEqual(result['changed'], 2)
        for name, data in self.after.items():
            self.assertEqual((self.game / name).read_bytes(), data)
        restored = restore_backup(Path(result['backup']), self.game)
        self.assertEqual(restored['changed'], 2)
        for name, data in self.before.items():
            self.assertEqual((self.game / name).read_bytes(), data)

    def test_check_and_repeat_apply_are_read_only(self):
        check_bundle(self.bundle, self.game)
        self.assertFalse((self.game / '.mhf-translation-backups').exists())
        apply_bundle(self.bundle, self.game)
        self.assertEqual(apply_bundle(self.bundle, self.game)['changed'], 0)

    def test_unknown_later_file_aborts_before_first_write(self):
        (self.game / 'stage/st200.pac').write_bytes(b'newer player edit')
        with self.assertRaises(PatchError):
            apply_bundle(self.bundle, self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.before['data.bin'])

    def test_corrupt_payload_aborts_before_writes(self):
        with zipfile.ZipFile(self.bundle, 'a') as z:
            manifest = json.loads(z.read('manifest.json'))
            member = manifest['files'][-1]['patch']
            z.writestr(member, b'bad patch')
        with self.assertRaises(PatchError):
            apply_bundle(self.bundle, self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.before['data.bin'])

    def test_restore_refuses_newer_user_edits(self):
        result = apply_bundle(self.bundle, self.game)
        (self.game / 'stage/st200.pac').write_bytes(b'newer edit')
        with self.assertRaises(PatchError):
            restore_backup(Path(result['backup']), self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.after['data.bin'])

    def test_running_client_refuses_install(self):
        with patch('mhfpatch.bundle.require_client_closed', side_effect=PatchError('client running')):
            with self.assertRaises(PatchError):
                apply_bundle(self.bundle, self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.before['data.bin'])

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(PatchError):
            build_bundle(self.root / 'bad.zip', self.original, self.translated, ['../outside'], 'client')

    def test_symlink_outside_target_is_rejected(self):
        target = self.game / 'data.bin'
        target.unlink()
        try:
            target.symlink_to(self.original / 'data.bin')
        except OSError:
            self.skipTest('symlink creation not permitted')
        with self.assertRaises(PatchError):
            apply_bundle(self.bundle, self.game)

    def test_server_bundle_does_not_require_game_to_be_closed(self):
        bundle = self.root / 'server.zip'
        build_bundle(bundle, self.original, self.translated, ['data.bin'], 'server')
        with patch('mhfpatch.bundle.require_client_closed', side_effect=PatchError('client running')):
            self.assertEqual(apply_bundle(bundle, self.game)['changed'], 1)

    def test_already_translated_files_are_not_reverted_by_backup(self):
        (self.game / 'data.bin').write_bytes(self.after['data.bin'])
        result = apply_bundle(self.bundle, self.game)
        restore_backup(Path(result['backup']), self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.after['data.bin'])

    def test_interrupted_install_retains_usable_rollback(self):
        from mhfpatch.bundle import atomic_copy
        calls = 0
        def interrupt(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated disk failure')
            return atomic_copy(*args)
        with patch('mhfpatch.bundle.atomic_copy', side_effect=interrupt):
            with self.assertRaisesRegex(PatchError, 'Rollback backup'):
                apply_bundle(self.bundle, self.game)
        backups = list((self.game / '.mhf-translation-backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual(restore_backup(backups[0], self.game)['changed'], 1)
        for name, data in self.before.items():
            self.assertEqual((self.game / name).read_bytes(), data)

    def test_backup_symlink_is_rejected(self):
        try:
            (self.game / '.mhf-translation-backups').symlink_to(self.original, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation not permitted')
        with self.assertRaisesRegex(PatchError, 'symlink'):
            apply_bundle(self.bundle, self.game)
        self.assertEqual((self.game / 'data.bin').read_bytes(), self.before['data.bin'])

    def test_change_during_install_is_detected_without_overwrite(self):
        def edit_later_file(done, total, name):
            if done == 1:
                (self.game / 'stage/st200.pac').write_bytes(b'concurrent edit')
        with self.assertRaisesRegex(PatchError, 'changed during operation'):
            apply_bundle(self.bundle, self.game, edit_later_file)
        self.assertEqual((self.game / 'stage/st200.pac').read_bytes(), b'concurrent edit')

    def test_cli_check_and_wrong_version_exit_status(self):
        script = Path(__file__).resolve().parents[1] / 'patch.py'
        args = [sys.executable, str(script), 'check', str(self.bundle), '--target', str(self.game)]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ready'], 2)
        (self.game / 'data.bin').write_bytes(b'unknown version')
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Unsupported version', result.stderr)


if __name__ == '__main__':
    unittest.main()
