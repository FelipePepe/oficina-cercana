# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Python 3 script (`oficina_cercana.py`, stdlib only, no dependencies, no build, no linter config) that assigns each Spanish postal code (CP) its nearest office by straight-line (haversine) distance. Git repository with gitflow branches (`main`, `develop`, `feature/*`); there is no remote.

## Run

```
python oficina_cercana.py cps.csv oficinas.csv [--precision] [--max-km N]
```

- `cps.csv`: first column is the CP to assign (one per row).
- `oficinas.csv`: first column is the office CP, second is the office name.
- Output is always `asignacion.csv` in the current working directory (hardcoded `SALIDA`), overwritten on each run.
- Both options are opt-in and only append columns: `--precision` adds `localidades` and `dispersion_km`; `--max-km N` (N > 0) adds a last column `lejos` (`SI` when the exact distance exceeds N). Without them the output is byte-identical to the golden file.

The sample `cps.csv`, `oficinas.csv` and `asignacion.csv` are synthetic fixtures/example output (regenerate `asignacion.csv` by re-running the script after editing the inputs). They deliberately include edge cases:

- CP formats: unpadded (`8001`, `1001`), Excel floats (`41002.0`, office `18001.0`), leading/trailing spaces (` 46010`, `28013 `, office ` 47001 `), a blank line, and duplicated input CPs (`28013`, `08001`, `01001`, which yield one output row each).
- Extra columns: `29600;comentario extra` (only the first column is used). `cps.csv` has a header (`codigo_postal`), which is skipped.
- Invalid or unknown CPs: `99999`, `00000`, `ABC12`, `-28013`, `280130` (all output `SIN COORDENADAS`).
- Unusable office rows, skipped with a warning: CP without coordinates (`99999;Oficina Fantasma-Test`, `abc;Oficina Basura-Test`), no name column (`41002`) and empty name (`06001;`).
- Exact tie: `Oficina Sevilla-Duplicada` shares CP `41002` with Sevilla-Casco Antiguo; ties are broken by the lowest office CP and then the name (never by file order), and "Sevilla-Casco Antiguo" sorts before "Sevilla-Duplicada", so Sevilla-Duplicada never appears in the output. It is the only office that does not win a CP.
- Coverage: every other office wins at least one CP (Madrid-Norte wins `28033`, `28034`, `28050`; Logroño wins `01001`; Murcia wins `03001`), plus islands, Ceuta, Melilla, CPs averaged from several localities (`31700`) and far-away CPs (`10001` goes to Sevilla at 233 km).

## Tests

```
python3 -m pytest tests/ -q
```

`tests/test_golden.py` runs the script on `cps.csv` and `oficinas.csv` in a temporary directory (it needs `ES.txt` and writes `asignacion.csv` in the working directory) and compares:

- the produced `asignacion.csv` byte by byte with the committed one (the golden file: BOM, `;` delimiter and line endings included);
- the lines printed on stdout (the warnings for skipped office rows) with an expected list.

Three more tests write their own header-less inputs: a first row that is not a header (`ABC12`) is kept (as `SIN COORDENADAS` in `cps.csv`, with a warning in `oficinas.csv`), and two offices at the same CP in opposite file order give a byte-identical output with the alphabetically first office as winner.

`tests/test_golden.py` also covers `--precision` and `--max-km` (headers, column order, `SIN COORDENADAS` rows, rejection of non-positive values) through the `run_in(..., args=())` helper. `tests/test_download.py` checks the GeoNames download with a fake `urlopen` (timeout passed; a zip without `ES.txt`, garbage, a non-zip or a `URLError` exit and leave no `ES.txt`); the tests never use the network.

When behaviour changes on purpose, update the golden file deliberately: edit the fixtures if needed, run the script from the repo root, review `git diff asignacion.csv` and commit it together with the change. If `EXPECTED_STDOUT` in the test changes, update it too. Never regenerate the golden file just to make a failing test pass.

## Architecture

Everything lives in `main()` plus small helpers; the data flow is:

1. `carga_coordenadas()` returns `(coords, precision)` from GeoNames `ES.txt` (tab-separated; CP in column 1, lat/lon in columns 9/10): `coords[cp] = (lat, lon)`, averaging a CP that appears several times, and `precision[cp] = (localities, spread_km)` where the spread is the largest distance from a locality to that centroid. If `ES.txt` is missing in the **current working directory**, `descarga_geonames()` downloads `ES.zip` (30 s timeout), requires `ES.txt` inside it, sanity-checks it (at least 1000 lines, 12 tab columns), writes `ES.txt.part` and renames it, so a failure exits with a Spanish message and never leaves a partial `ES.txt`. It needs the network on first run. `ES.txt` (~3 MB) is checked in as a cache; the GeoNames attribution is in `NOTICE.md` (CC BY 4.0).
2. `lee_csv()` auto-detects the delimiter (`;`, `,` or tab) with `csv.Sniffer`, strips the BOM, and skips the first row only if its first cell contains no digit (`cp`, `codigo_postal`). A first row with a digit is data, so an invalid CP such as `ABC12` is never dropped silently; the tradeoff is that a header containing a digit (e.g. `cp2`) is read as data. `csv.Sniffer` fails when rows have different column counts, so the fallback picks the most frequent of `;`, `,`, tab in the sample (not plain comma).
3. `normaliza_cp()` is the single normalization point for CPs: strips whitespace and a `.0` suffix, zero-pads to 5 digits, returns `None` for non-numeric. Always use it before looking up coordinates.
4. For each CP, the nearest office is found with a single linear `min()` over `(distance, office CP, name)` tuples using `haversine()` (km, Earth radius 6371); the distance is computed once and reused for the output.
5. Arguments are parsed with `argparse` in `lee_argumentos()`; `km_positivo()` rejects non-numeric, zero, negative and NaN values for `--max-km`.

## Behavior to preserve

- Office rows with fewer than two columns or an empty name are skipped with a warning (no `IndexError`); offices whose CP has no coordinates are also skipped with a warning. The script exits if no valid office remains.
- Input CPs without coordinates are still written to the output with `SIN COORDENADAS` in `distancia_km` (blank office columns) rather than dropped.
- Output is `;`-delimited with a UTF-8 BOM (`utf-8-sig`) so Excel opens it correctly; keep this when changing the writer.
- Distance is straight-line, not road distance, and CP coordinates are GeoNames centroids, so results are approximate. `--max-km` only flags far assignments (sea crossings, rural outliers); it never changes the assigned office. Real road or sea-aware distance would need a routing service and is a product decision.
- Never save a partial or unchecked `ES.txt`; keep the attribution in `NOTICE.md` when touching the data files.
- User-facing messages and the docstring in the script are in Spanish. This file stays in English.
