# Monster Hunter Frontier PC English Translation

English client and Erupe server patches, with exact file-version checks,
automatic backups and rollback.

The first supported client set contains 102 changed files: seven main data
files, 91 scene scripts, two pointer-table files, and the two Mezeporta town
files. Mezeporta loads successfully, and the general-store clerk and Felyne
dialogue have been checked in-game. Translation of the other areas is ongoing.

Download the patcher source and bundles from the
[2026.09.12 release](https://github.com/Blizz127/Monster-Hunter-Frontier-PC-English-Translation/releases/tag/v2026.09.12).
Download `mhf-translation-patcher-2026.09.12.zip` and the client bundle for your
game. Download the server bundle as well if you operate Erupe. Extract the
patcher, then place the bundle ZIP files in its folder without extracting them.
See [compatibility and coverage](docs/compatibility.md) and the
[release catalog](releases/2026.09.12.json) for exact counts, hashes and limits.

## Requirements

- Your own matching Monster Hunter Frontier client or Erupe quest/scenario data.
- Python 3.12 and the package in `requirements.txt`.
- Windows or a Linux host for client installation. Close Monster Hunter first.
- For server patching, stop Erupe while applying or restoring the bundle.

The patcher checks SHA-256 hashes against the bundle manifest. It refuses
unsupported versions and unknown edits before changing any installed files.
The bundles contain binary differences and require matching original data.

## Install the patcher

Download this repository, extract it, and open a terminal in its folder.
Create a private Python environment so system packages remain separate.

Windows (Command Prompt):

```console
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Linux:

```console
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Keep that environment active for the commands below. Reopen it with the
activation command if you start a new terminal.

## Client patch

Point `--target` at the client's **dat** folder, not its saves or Wine prefix.
Replace the example paths and bundle filename with your actual locations.

```console
python patch.py check client-english-2026.09.12.zip --target "C:\Games\MHF\dat"
python patch.py apply client-english-2026.09.12.zip --target "C:\Games\MHF\dat"
```

`check` is read-only. `apply` verifies and prepares every output before the first
game-file replacement. It keeps the original files in a dated
`.mhf-translation-backups` folder inside the target, and prints the backup path.
Applying the same bundle again leaves already-patched files alone.

After applying, launch normally, enter Mezeporta, and test the clerk and Felyne
dialogue. Other scenes and dialogue branches have not all been observed.

## Erupe server patch

Point `--target` at the server's **bin** directory containing `quests` and
`scenarios`. Stop your Erupe service or container before `apply`, then start it
again after the command succeeds. These commands operate on files; they do not
change your database, accounts, configuration, or service settings.

```console
python patch.py check server-english-2026.09.12.zip --target /path/to/erupe/bin
python patch.py apply server-english-2026.09.12.zip --target /path/to/erupe/bin
```

Keep the printed backup path. Check the server logs and load a quest after
restarting. The bundle withholds 972 oversized quest listings pending corrections; those
files stay original. All quests and scenarios have not been played.

## Rollback

Close the game, or stop Erupe for a server rollback, then pass the exact backup
path printed by `apply`:

```console
python patch.py restore "C:\Games\MHF\dat\.mhf-translation-backups\BACKUP-NAME" --target "C:\Games\MHF\dat"
```

Rollback verifies the backup and refuses to overwrite newer edits. It only
restores files changed by that installation, retaining any files that were
already translated beforehand. A backup also covers an interrupted installation.

## Building bundles

Maintainers can generate a bundle from original and verified translated trees:

```console
python patch.py build --kind client --source /path/to/original/dat --translated /path/to/translated/dat --output dist/client-english-2026.09.12.zip
python patch.py build --kind server --source /path/to/original/bin --translated /path/to/translated/bin --output dist/server-english-2026.09.12.zip
python -m unittest discover -s tests -v
```

Encrypted ECD files are diffed after decryption, so unchanged encrypted game
assets are not copied wholesale into each delta. Applying the delta reconstructs
the exact accepted encrypted file and verifies its full SHA-256 hash.

## Credits and license

Maintainers can also use the [toolkit source fixes](patches/README.md).

The ECD codec and codec tests are adapted from [Houmgaor's FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler),
based on [ReFrontier](https://github.com/Houmgaor/ReFrontier), with original
reverse-engineering contributions credited to enler. Local fixes add the
filename/payload checksum used by the stage loader.

Code is distributed under GPL-3.0; see [LICENSE](LICENSE). Monster Hunter and
its original game assets belong to Capcom. This project supplies translation
patches for users' own files.
