"""ECD filename-check regressions grounded in the installed client validator."""
import struct
import unittest

from mhfpatch import crypto


class TestECDFilenameChecksum(unittest.TestCase):
    def test_native_town_header_vectors(self):
        # mhfo.dll 0x1156879d checks these against header bytes 6-7.
        # The first two come from untouched files; the latter two are the
        # corrected checks for original-dialogue controls that froze.
        for crc, name, expected in (
            (0x1669a4ae, 'st200.pac', 0x6497),
            (0x5483adf0, 'st397.pac', 0xea3c),
            (0x7005ba21, 'st200.pac', 0xa8db),
            (0x2a5c7e37, 'st397.pac', 0xc43c),
        ):
            with self.subTest(name=name, crc=crc):
                self.assertEqual(crypto.ecd_filename_checksum(crc, name), expected)

    def test_filename_is_uppercase_basename_including_extension(self):
        for name in ('st200.pac', 'St200.PaC', '/game/dat/stage/st200.pac',
                     r'X:\game\dat\stage\st200.pac'):
            self.assertEqual(crypto.ecd_filename_checksum(0x1669a4ae, name), 0x6497)

    def test_invalid_filename_is_rejected(self):
        for name in ('', '/stage/', '.', '..', 'st200\0.pac', '町.pac'):
            with self.subTest(name=name), self.assertRaises(crypto.CryptoError):
                crypto.ecd_filename_checksum(0, name)

    def test_changed_payload_recomputes_stale_metadata_checksum(self):
        original = crypto.encrypt(b'old dialogue', filename='st200.pac')
        payload = b'changed dialogue'
        stale = crypto.encrypt(payload, meta=original[:16])
        fixed = crypto.encrypt(payload, meta=original[:16], filename='st200.pac')
        self.assertNotEqual(stale[6:8], fixed[6:8])
        self.assertEqual(stale[:6], fixed[:6])
        self.assertEqual(stale[8:], fixed[8:])
        self.assertEqual(crypto.decode_ecd(fixed), payload)
        crc = struct.unpack_from('<I', fixed, 12)[0]
        self.assertEqual(struct.unpack_from('<H', fixed, 6)[0],
                         crypto.ecd_filename_checksum(crc, 'st200.pac'))

    def test_unchanged_payload_and_name_reproduce_original(self):
        original = crypto.encrypt(b'original dialogue', filename='st397.pac')
        payload, meta = crypto.decrypt(original)
        self.assertEqual(crypto.encrypt(payload, meta=meta, filename='st397.pac'), original)

    def test_filename_omitted_preserves_legacy_spare_bytes(self):
        original = crypto.encode_ecd(b'old', spare=b'\x12\x34')
        self.assertEqual(crypto.encode_ecd_with_meta(b'new', original[:16])[6:8], b'\x12\x34')
        self.assertEqual(crypto.encrypt(b'new')[6:8], b'\0\0')

    def test_keys_below_four_keep_their_unchecked_field(self):
        for key in range(4):
            encoded = crypto.encode_ecd(b'data', key, spare=b'\x12\x34', filename='st200.pac')
            self.assertEqual(encoded[6:8], b'\x12\x34')
            self.assertEqual(crypto.decode_ecd(encoded), b'data')

    def test_key_five_uses_filename_check(self):
        encoded = crypto.encode_ecd(b'data', 5, filename='st200.pac')
        crc = struct.unpack_from('<I', encoded, 12)[0]
        self.assertEqual(struct.unpack_from('<H', encoded, 6)[0],
                         crypto.ecd_filename_checksum(crc, 'st200.pac'))
        self.assertEqual(crypto.decode_ecd(encoded), b'data')
