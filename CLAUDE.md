# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Python 3 script (`oficina_cercana.py`, stdlib only, no dependencies, no tests, no build, no linter config) that assigns each Spanish postal code (CP) its nearest office by straight-line (haversine) distance. This directory is not a git repository.

## Run

```
python oficina_cercana.py cps.csv oficinas.csv
```

- `cps.csv`: first column is the CP to assign (one per row).
- `oficinas.csv`: first column is the office CP, second is the office name.
- Output is always `asignacion.csv` in the current working directory (hardcoded `SALIDA`), overwritten on each run.

The sample `cps.csv`, `oficinas.csv` and `asignacion.csv` are synthetic fixtures/example output (regenerate `asignacion.csv` by re-running the script after editing the inputs). They deliberately include edge cases:

- CP formats: unpadded (`8001`, `1001`), Excel floats (`41002.0`, office `18001.0`), surrounding spaces (` 46010`, office ` 47001 `), a blank line, and a duplicated input CP (`28013`, which yields two output rows).
- Invalid or unknown CPs: `99999`, `00000`, `ABC12` (all output `SIN COORDENADAS`), and offices with unusable CPs (`99999;Oficina Fantasma-Test`, `abc;Oficina Basura-Test`), which are skipped with a warning.
- Malformed office row: a bare `41002` with no name, which is skipped with a warning.
- Exact tie: `Oficina Madrid-Norte` shares CP `28013` with Madrid-Centro; the first office in the CSV wins.
- Coverage: every office wins at least one CP; islands, Ceuta and Melilla are included.

## Architecture

Everything lives in `main()` plus small helpers; the data flow is:

1. `carga_coordenadas()` builds `{cp: (lat, lon)}` from GeoNames `ES.txt` (tab-separated; CP in column 1, lat/lon in columns 9/10). A CP appearing several times is averaged. If `ES.txt` is missing in the **current working directory**, `descarga_geonames()` downloads `ES.zip` from GeoNames and extracts it there (needs network on first run). `ES.txt` (~3 MB) is checked in as a cache.
2. `lee_csv()` auto-detects the delimiter (`;`, `,` or tab) with `csv.Sniffer`, strips the BOM, and skips the first row only if its first cell is not a valid CP (header detection via `normaliza_cp`). `csv.Sniffer` fails when rows have different column counts, so the fallback picks the most frequent of `;`, `,`, tab in the sample (not plain comma).
3. `normaliza_cp()` is the single normalization point for CPs: strips whitespace and a `.0` suffix, zero-pads to 5 digits, returns `None` for non-numeric. Always use it before looking up coordinates.
4. For each CP, the nearest office is found with a linear `min()` over all offices using `haversine()` (km, Earth radius 6371).

## Behavior to preserve

- Office rows with fewer than two columns or an empty name are skipped with a warning (no `IndexError`); offices whose CP has no coordinates are also skipped with a warning. The script exits if no valid office remains.
- Input CPs without coordinates are still written to the output with `SIN COORDENADAS` in `distancia_km` (blank office columns) rather than dropped.
- Output is `;`-delimited with a UTF-8 BOM (`utf-8-sig`) so Excel opens it correctly; keep this when changing the writer.
- Distance is straight-line, not road distance, and CP coordinates are GeoNames centroids, so results are approximate.
- User-facing messages and the docstring in the script are in Spanish. This file stays in English.
