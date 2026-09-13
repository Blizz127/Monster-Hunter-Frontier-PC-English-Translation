# Experimental translation update: 2026.09.13-preview.1

This preview is **not in-game verified** and is not the stable release. It does
not claim 100% English coverage. Use the stable 2026.09.13 release for the
previously tested Mezeporta and equipment/skills-menu repair.

## Client

Apply this three-file upgrade only after the stable 2026.09.13 client patch.
It contains cumulative weapon/equipment text work in `mhfdat.bin`, plus the
two Mezeporta archives. The latest description pass adds 30 reviewed entries to the cumulative 741-entry description pass;
394 entries remain in the current plain-text shortening queue. Other review
queues, artwork and runtime checks also remain.

Town changes reflow 574 distinct plain-text passages, two previously tested
greetings and two colored Route Quest Counter greetings. The new reflows
include Mama Grocer's farewell (split “be”), the Winner Quest Counter (split
“members”) and Route Quest Counter (split “surveying”). Words, color controls
and paragraph separators are preserved. The 38-cell trial width is not a
measured font-pixel limit. Long pages and dynamic substitutions still need review.

Close the game. With the existing patcher environment active:

```console
python patch.py check client-english-2026.09.13-preview.1.zip --target "C:\Games\MHF\dat"
python patch.py apply client-english-2026.09.13-preview.1.zip --target "C:\Games\MHF\dat"
```

Unknown source hashes are rejected. An earlier private spacing test may be
rejected; restore its own backup before applying the public upgrade. Keep the
backup printed by `apply`. See the main README for rollback instructions.
Test normal town entry, equipment/skills menus and all three screenshot
passages. No game installation was changed while preparing this preview.

## Server

The separate server preview adds 972 quests withheld from the stable server
bundle. Each rebuilt event-list entry fits the 896-byte bound. The files retain
non-text bytes except the eight text pointers; strict codec round trips pass.
153 dialogue sets have reviewed overrides. Some subtarget A/B interpretations
remain unresolved, and these quests have not received gameplay acceptance.

Stop Erupe before applying. Point the target at the directory containing
`quests`, using the same patcher as the stable release:

```console
python patch.py check server-english-2026.09.13-preview.1.zip --target /path/to/quest-data
python patch.py apply server-english-2026.09.13-preview.1.zip --target /path/to/quest-data
```

This adds the withheld files to the stable server translation; it does not
replace the full stable bundle. No running server was modified for publication.

## Review material

`translations/preview-2026.09.13/` records the latest description edits,
word-preserving town reflows and server dialogue overrides. Its `dat/` folder
preserves the cumulative working CSV snapshot; it is not fully reviewed. Bundle manifests
pin every input and output SHA-256. The assets are binary differences requiring
matching client/server data; full game archives are not included in the source.
