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
