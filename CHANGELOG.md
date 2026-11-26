# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `--precision` appends `localidades` and `dispersion_km` (how many localities GeoNames lists
  for the CP and how far the farthest one is from the centroid used).
- `--max-km N` appends `lejos` (`SI` when the distance exceeds N km). The assignment does not change.
- `NOTICE.md` with the GeoNames attribution; the licence (CC BY 4.0) was verified against the
  GeoNames readme.
- Download tests with a fake network (`tests/test_download.py`).

### Changed

- Exact ties are broken by the lowest office CP and then the name, not by the order of
  `oficinas.csv`.
- Arguments are parsed with `argparse`; the positional usage is unchanged and a usage error now
  exits with code 2.
- The distance to the nearest office is computed once per CP.

### Fixed

- The GeoNames download now has a 30 s timeout, requires `ES.txt` inside the zip, checks the
  content and writes it atomically, so a failed download never leaves a partial `ES.txt`.

## [0.1.3] - 2026-11-25

### Added

- `README.md`: usage, input and output formats, behaviour notes, tests, repository layout,
  gitflow and the data licence caveat.

## [0.1.2] - 2026-11-25

### Changed

- `docs/informe-tecnico.md`: weaknesses 1 (first row dropped silently) and 7 (no automated
  tests) are marked as resolved in the tables and in the recommended steps, and the code
  line references match v0.1.0.

## [0.1.1] - 2026-11-25

### Added

- `docs/informe-tecnico.md`: technical report (in Spanish) with the architecture, the
  measurements on the GeoNames data, the fixture coverage matrix, the known weaknesses
  and the recommended next steps.

## [0.1.0] - 2026-11-25

First release.

### Added

- `oficina_cercana.py`: assigns each Spanish postal code (CP) to its nearest office by
  straight-line (haversine) distance, using GeoNames coordinates (`ES.txt`).
- Synthetic fixtures (`cps.csv`, `oficinas.csv`) covering header rows, extra columns,
  unpadded CPs, Excel floats, stray spaces, invalid CPs, nameless offices, exact ties,
  islands, Ceuta and Melilla; `asignacion.csv` is the expected output.
- Golden-file regression tests (`tests/test_golden.py`, run with `python3 -m pytest tests/ -q`).
- `CLAUDE.md` with the architecture, the commands and the behaviours to preserve.

### Fixed

- `IndexError` when an office row had fewer than two columns; such rows are now skipped
  with a warning.
- Delimiter detection: when `csv.Sniffer` fails on rows of different width, the most
  frequent of `;`, `,` and tab is used instead of falling back to a comma.
- A first row that is not a header (for example `ABC12`) was dropped silently. Only a
  first cell with no digit is now treated as a header.

### Known limitations

- Distances are straight lines between GeoNames centroids: they ignore sea, mountains and
  roads, and CPs spanning several localities are averaged.
- GeoNames data is redistributed in `ES.txt`; its licence and the required attribution
  have not been verified yet.
