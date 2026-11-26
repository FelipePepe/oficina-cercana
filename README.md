# oficina_cercana

Assigns each Spanish postal code (CP) to its nearest office by straight-line (haversine) distance. A single Python 3 script, standard library only.

## Quick start

```
python3 oficina_cercana.py cps.csv oficinas.csv
```

The result is written to `asignacion.csv` in the current working directory (overwritten on every run).

| Input | First column | Second column |
| --- | --- | --- |
| `cps.csv` | CP to assign | (ignored) |
| `oficinas.csv` | CP of the office | office name |

Both files may use `;`, `,` or tab as delimiter (detected automatically), may start with a header row, and may be saved by Excel (BOM, CPs such as `8001` or `41002.0`).

Output (`;`-delimited, UTF-8 with BOM so Excel opens it directly):

```
codigo_postal;oficina;cp_oficina;distancia_km
28045;Oficina Madrid-Centro;28013;2.8
99999;;;SIN COORDENADAS
```

## Behaviour worth knowing

- Coordinates come from [GeoNames](https://download.geonames.org/export/zip/) (`ES.txt`, versioned in this repo). If the file is missing, it is downloaded on the first run. A CP that appears in several localities uses the average of their coordinates.
- A CP without coordinates is kept in the output and marked `SIN COORDENADAS`; it is never dropped.
- Office rows with no name, or with a CP that has no coordinates, are skipped with a warning on stdout.
- The first row is treated as a header only when its first cell contains no digit (`cp`, `codigo_postal`). A first row such as `ABC12` is data.
- On an exact tie, the office with the lowest CP wins, then the first name alphabetically. The result never depends on the order of `oficinas.csv`.
- Distances are straight lines between CP centroids: they ignore sea, mountains and roads, so treat long distances as approximate.

## Tests

```
python3 -m pytest tests/ -q
```

`tests/test_golden.py` runs the script on the committed `cps.csv` and `oficinas.csv` in a temporary directory and compares the output with the committed `asignacion.csv` (the golden file) byte by byte, plus the warnings printed on stdout. When behaviour changes on purpose, regenerate the golden file, review `git diff asignacion.csv` and commit it with the change.

## Repository

| Path | Purpose |
| --- | --- |
| `oficina_cercana.py` | The script |
| `cps.csv`, `oficinas.csv`, `asignacion.csv` | Synthetic fixtures and their expected output |
| `ES.txt` | GeoNames postal code data for Spain |
| `tests/` | Golden-file tests |
| `docs/informe-tecnico.md` | Technical report (in Spanish): measurements, weaknesses, next steps |
| `CHANGELOG.md` | Release notes |
| `CLAUDE.md` | Guidance for Claude Code |

Git workflow: gitflow. Work happens on `feature/*` and `fix/*` branches merged into `develop`; releases go through `release/x.y.z` into `main`, tagged `vx.y.z`.

## Data and licence

`ES.txt` is GeoNames data, which is distributed under a Creative Commons Attribution licence; check the current terms in the GeoNames readme and keep the attribution before redistributing this repository. This project has no licence file yet.
