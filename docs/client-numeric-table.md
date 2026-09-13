# Client numeric-table repair

Status: confirmed data corruption in the `2026.09.12` client bundle; a repair
has passed offline checks and is installed locally for an in-game test.
A corrected public client bundle has not yet been released.

The legacy `pac/skills/description` extraction configuration treated the
region bounded by header pointers at `0xB8` and `0xC0` in this client version's
decompressed `mhfpac.bin` as text pointers. Comparison with the original file
shows that the region contains numeric records. The earlier translation
import changed 1,958 four-byte fields in that 9,336-byte region, including
values `10001` and `1`, into offsets to appended strings.

The staged repair restores the original bytes at `[0x141180, 0x1435F8)`.
All bytes outside that range remain identical to the translated plaintext,
and extraction of the other 32 configured PAC sections is unchanged. Strict
decompression and encryption round trips pass. The legacy description
mapping must not be used to import translations for this supported version.
These offsets are version-specific, not a recipe for modifying other builds.

| File state | SHA-256 |
| --- | --- |
| Original source | `3f357366fbcd397bcdf4edfb681eb38f323f1ed7bfb1a2fd446a1fb93afd308c` |
| Affected released translation | `f5523498d47021012df3d29fe6e10023d6adb5f4085254d0cf93cb5ae10940f3` |
| Repair awaiting runtime acceptance | `0bf1eb07ac12628e95e385730f17dbf1c96f6bb61edb705d68ee642cee29a851` |

The earlier Mezeporta, clerk and Felyne checks passed, but did not detect this
numeric-data issue. The bundle's apply/restore tests prove that it reproduces
the recorded hashes; they do not prove correctness of every inherited edit.
The gameplay impact of the damaged records has not been established.

Please defer new installations of `client-english-2026.09.12.zip`. If it is
already installed, close the game and use the patcher's `restore` command with
the backup directory printed during installation. That restores the files
changed by that installation. Keep the backup for recovery. Do not manually
copy plaintext offsets into an encrypted client file.

The server bundle does not contain `mhfpac.bin`. Its separately documented
972 excluded quest files and incomplete runtime coverage still apply.
