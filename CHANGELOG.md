# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

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
