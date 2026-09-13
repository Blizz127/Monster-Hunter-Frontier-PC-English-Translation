# Changelog

## 2026.09.12

- Initial public client and server delta bundles with matching-original checks.
- 102 client files, including English Mezeporta town dialogue and the ECD
  filename/payload checksum repair that resolves the reproduced town freeze.
- Server quest and scenario translations, excluding 972 quest listings that
  exceed the inspected Erupe ZZ event-entry size limit.
- Full preflight, staged output verification, dated backups and guarded rollback.
- Source fixes for the FrontierTextHandler checksum and LZ compressor.
- Tests for codec/checksum behavior, wrong versions, corruption, interrupted
  installation, concurrent edits, path escape and rollback.

This is a partial translation release. Mezeporta clerk and Felyne dialogue were
checked in-game; other dialogue branches and all server quests were not.

## 2026.09.13-preview.1 (experimental)

- Publish cumulative client text and town wrapping candidates for testing.
- Add a separate 972-quest server preview with reviewed dialogue and bounded event entries.
- Preserve stable 2026.09.13 as the in-game-tested client release.

## 2026.09.13-preview.2 (experimental)

- Add 36 source-reviewed equipment and melee-weapon description entries.
- Reduce the remaining reviewed shortening queue to 963 entries.
- Keep runtime status explicitly pending; the stable release is unchanged.
