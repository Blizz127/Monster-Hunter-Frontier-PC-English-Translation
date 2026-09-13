# Client numeric-table repair

Status: corrected in `2026.09.13`. With the repair installed, the user confirmed
that Mezeporta loads and the equipment/skills menus work normally. This is a
bounded runtime check; every gameplay path has not been tested.

The legacy `pac/skills/description` extraction configuration treated the
region bounded by header pointers at `0xB8` and `0xC0` in this client version's
decompressed `mhfpac.bin` as text pointers. Comparison with the original file
shows that the region contains numeric records. The earlier translation
import changed 1,958 four-byte fields in that 9,336-byte region, including
values `10001` and `1`, into offsets to appended strings.

The repair restores the original bytes at `[0x141180, 0x1435F8)`.
All bytes outside that range remain identical to the translated plaintext,
and extraction of the other 32 configured PAC sections is unchanged. Strict
decompression and encryption round trips pass. The legacy description
mapping must not be used to import translations for this supported version.
These offsets are version-specific, not a recipe for modifying other builds.

| File state | SHA-256 |
| --- | --- |
| Original source | `3f357366fbcd397bcdf4edfb681eb38f323f1ed7bfb1a2fd446a1fb93afd308c` |
| Affected released translation | `f5523498d47021012df3d29fe6e10023d6adb5f4085254d0cf93cb5ae10940f3` |
| Corrected translation | `0bf1eb07ac12628e95e385730f17dbf1c96f6bb61edb705d68ee642cee29a851` |

The earlier Mezeporta, clerk and Felyne checks passed, but did not detect this
numeric-data issue. The bundle's apply/restore tests prove that it reproduces
the recorded hashes; they do not prove correctness of every inherited edit.
The gameplay impact of the damaged records has not been established.

Use `client-english-2026.09.13.zip` for a new installation. If the first release
is already installed, close the game and apply `client-repair-from-2026.09.12.zip`
using the patcher. Both bundles produce the corrected hash above. Keep your
backups: restoring the repair backup returns the affected first-release file;
then restoring the original translation backup returns the original client.
Do not manually copy plaintext offsets into an encrypted client file.

The server bundle does not contain `mhfpac.bin`. Its separately documented
972 excluded quest files and incomplete runtime coverage still apply.
