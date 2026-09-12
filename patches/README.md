# Toolkit source fixes

Players should use the release bundles and `patch.py`; this source patch is for
translation-tool maintainers.

`FrontierTextHandler-checksum-compression.patch` applies to
[Houmgaor/FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler)
commit `625c7efcb02895fa4140e73adc3f6f9bdf322be0`. It includes the ECD filename
checksum fix and the LZ compressor improvements used by the accepted town
rebuild: one-byte lazy matching, a larger candidate chain, corrected short
match cost and the long-match bound that excludes the literal-run marker.

In a separate checkout at that commit:

```console
git apply --check /path/to/FrontierTextHandler-checksum-compression.patch
git apply /path/to/FrontierTextHandler-checksum-compression.patch
python -m unittest discover -s tests -v
```

Stage writers must explicitly pass the output filename:

```python
encrypted = encrypt(rebuilt_payload, meta=original_header, filename=output_path.name)
```

Omitting `filename` intentionally preserves legacy metadata behavior. Do not
carry the old checksum into a changed town payload. See
[the format notes](../docs/format-fixes.md) for the directory layout, checksum
formula, accepted controls and remaining runtime acceptance requirements.

The patch changes only `src/crypto.py` and `src/jkr_compress.py`. It does not
contain local installation paths, game assets, credentials or translation API
configuration. Code remains under FrontierTextHandler's GPL-3.0 license.
