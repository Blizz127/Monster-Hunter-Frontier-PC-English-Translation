# Compatibility and coverage

Use the patcher's `check` command before installing. Compatibility is defined
by the exact original and translated SHA-256 hashes in each bundle's manifest,
not by a filename or a broad claim that every MHF build is supported. Unknown
edits are rejected. Obtain an original copy of the affected files from your own
backup when another translation or mod conflicts.

## Client

The initial release reproduces the locally accepted set of 102 changed files:
seven root data files, 91 `load` scripts, `extend/mazpac.bin`,
`my_gallery/mhf_bin.bin`, and `stage/st200.pac` plus `stage/st397.pac`.

User-observed acceptance: normal launch, successful Mezeporta entry, English
general-store clerk dialogue, and Felyne dialogue. All dialogue branches, quests,
and areas have not been walked. This is an incremental translation release;
additional area translations are still being prepared and tested.

The Mezeporta checksum repair is explained in [format-fixes.md](format-fixes.md).
The package contains differences, not a complete client or launcher.

## Server

Server patches target matching binary quest/scenario files under Erupe's `bin`
directory. Source lineage is the local copy of the
[xl3lackout/MHFZ-Quest-Files](https://github.com/xl3lackout/MHFZ-Quest-Files)
dataset; the manifest's hashes are the authoritative version check.

The prepared translation tree contains 54,954 quests and 145,376 scenarios.
Every one matched its counterpart on the running server during a checksum-only
comparison on 2026-09-12. Files whose translated quest listing exceeds the
inspected Erupe ZZ event-entry limit of 896 bytes are withheld from this release.
They retain their original dialogue when patching an original dataset. The release includes 53,982 changed quest files and 145,376 changed scenario
files. See the release catalog and exclusions list for exact coverage.

These are translated data files, not an Erupe executable or server setup. Keep
your existing Erupe version, database, configuration and service definition.
Stop Erupe before installation so cached data and on-disk files cannot disagree;
restart after successful installation. Select English in your server/client
language settings as appropriate for your setup. No automatic server restart
or database migration is performed.

Data compatibility and exhaustive in-game acceptance are separate. The server
bundle receives full apply/restore hash verification on an isolated copy, but
all quests and scenario branches have not been tested in-game. Report the file
or quest ID and reproduction steps for dialogue or layout problems.

## Recovery

Each install records a backup manifest before replacing files. If interrupted,
use the printed backup directory with `restore`; already-original files are
accepted. Do not delete `.mhf-translation-backups` until you no longer need
rollback. Restoring a moved installation requires returning it to its original
path because backups are bound to their target directory.

Do not mix translation bundles from unrelated sources without checking their
hashes. Install only bundles you trust: SHA-256 verifies data integrity and
version compatibility; it is not a publisher signature.
