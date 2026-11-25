"""Golden-file regression tests for oficina_cercana.py.

The script is run on the committed fixtures (cps.csv, oficinas.csv) inside a
temporary directory, because it reads ES.txt and writes asignacion.csv in the
current working directory. The committed asignacion.csv is the golden file and
is never touched by the tests.
"""
import difflib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "oficina_cercana.py"
GOLDEN = ROOT / "asignacion.csv"

EXPECTED_STDOUT = [
    "Aviso: la oficina ['Oficina Fantasma-Test'] tiene un CP sin coordenadas (99999)",
    "Aviso: la oficina ['Oficina Basura-Test'] tiene un CP sin coordenadas (abc)",
    "Aviso: fila de oficinas sin nombre, se ignora (41002)",
    "Aviso: fila de oficinas sin nombre, se ignora (06001)",
    "Hecho: asignacion.csv",
    "5 CPs sin coordenadas (marcados en el fichero).",
]


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    """Run the script once in a scratch directory; return (code, stdout, output bytes)."""
    work = tmp_path_factory.mktemp("golden")
    for name in ("cps.csv", "oficinas.csv", "ES.txt"):
        shutil.copy(ROOT / name, work / name)
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "cps.csv", "oficinas.csv"],
        cwd=work,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    out = work / "asignacion.csv"
    return done.returncode, done.stdout, out.read_bytes() if out.exists() else b""


def test_output_matches_golden(run):
    code, _, produced = run
    assert code == 0
    expected = GOLDEN.read_bytes()
    if produced != expected:
        diff = difflib.unified_diff(
            expected.decode("utf-8-sig").splitlines(),
            produced.decode("utf-8-sig", errors="replace").splitlines(),
            "asignacion.csv (golden)",
            "asignacion.csv (produced)",
            lineterm="",
        )
        text = "\n".join(diff) or "(same text: the BOM or the line endings differ)"
        pytest.fail("Output differs from the golden file:\n" + text)


def test_warnings_match(run):
    _, stdout, _ = run
    assert stdout.splitlines() == EXPECTED_STDOUT
