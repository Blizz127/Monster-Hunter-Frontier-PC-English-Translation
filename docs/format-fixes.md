# Mezeporta freeze repair

Recompressing the original dialogue caused Mezeporta to freeze even before
translation. Keeping that exact compressed payload and correcting ECD header
bytes 6–7 made the town load. The subsequent English town files also loaded,
and the general-store clerk and Felyne dialogue were checked in-game.

For ECD keys 4 and 5, those two bytes are a filename/payload checksum. They are
neither padding nor a static per-file value. The stage loader checks them:

```python
check = ((zlib.crc32(basename.upper().encode('ascii'), payload_crc32 ^ 0xffffffff)
          ^ 0xffffffff) >> 7) & 0xffff
```

The filename includes the extension and excludes directories. Store the result
as little-endian uint16 at offset 6. `payload_crc32` is the ECD plaintext CRC at
offset 12. All 404 untouched encrypted stage files in the inspected client
matched this formula. Some other loaders decode ECD directly, so their accepted
files can carry legacy zero/check bytes. The patcher preserves each release's
exact target header instead of changing those accepted bytes.

The town PAC directory contains a little-endian count followed by `(offset,
size)` pairs. The two town files have 32 entries and a 0x104-byte header. Reading
these pairs as shifted size/end values invents a section and omits the final
asset block. Translation builders must verify all section bounds, pointer-table
round trips, text tokens, strict decompression, and the final encrypted hash.

The accepted town rebuild translates 2,032 dialogue slots per file. Its shared
compressed dialogue occupies 82,247 bytes within the original 84,692-byte
section, with 2,445 bytes of padding. No dialogue was clipped to fit.

Native validation evidence comes from the locally inspected `mhfo.dll`: the
CRC routine at preferred VA `0x11568500`, validation at `0x115686c0`, and the
comparison at `0x1156879d`. These addresses describe that binary version;
regression tests use fixed input/checksum vectors and do not require it.
