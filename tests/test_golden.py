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


def run_in(work, cps_text=None, oficinas_text=None):
    """Run the script in `work`; return (code, stdout, output bytes).

    cps.csv and oficinas.csv are the committed fixtures unless a text is given.
    ES.txt is always copied from the repo, so no network is used.
    """
    shutil.copy(ROOT / "ES.txt", work / "ES.txt")
    for name, text in (("cps.csv", cps_text), ("oficinas.csv", oficinas_text)):
        if text is None:
            shutil.copy(ROOT / name, work / name)
        else:
            (work / name).write_text(text, encoding="utf-8")
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


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    """Run the script once on the committed fixtures."""
    return run_in(tmp_path_factory.mktemp("golden"))


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


def test_first_cp_row_without_header_is_kept(tmp_path):
    """A first row that is not a header must never vanish silently."""
    code, _, produced = run_in(tmp_path, cps_text="ABC12\n28013\n")
    rows = produced.decode("utf-8-sig").splitlines()
    assert code == 0
    assert rows[1] == "ABC12;;;SIN COORDENADAS"
    assert rows[2].startswith("28013;Oficina Madrid-Centro;28013;")


def test_exact_tie_does_not_depend_on_file_order(tmp_path_factory):
    """Offices at the same CP tie exactly; the winner must not depend on file order."""
    zeta_first = "28013;Oficina Zeta\n28013;Oficina Alfa\n"
    alfa_first = "28013;Oficina Alfa\n28013;Oficina Zeta\n"
    out_a = run_in(tmp_path_factory.mktemp("a"), "28013\n", zeta_first)[2]
    out_b = run_in(tmp_path_factory.mktemp("b"), "28013\n", alfa_first)[2]
    assert out_a == out_b
    assert out_a.decode("utf-8-sig").splitlines()[1].startswith("28013;Oficina Alfa;")


def test_first_office_row_without_header_is_reported(tmp_path):
    oficinas = "ABC12;Oficina Basura-Test\n28013;Oficina Madrid-Centro\n"
    code, stdout, produced = run_in(tmp_path, cps_text="28045\n", oficinas_text=oficinas)
    rows = produced.decode("utf-8-sig").splitlines()
    assert code == 0
    assert "tiene un CP sin coordenadas (ABC12)" in stdout
    assert rows[1].startswith("28045;Oficina Madrid-Centro;28013;")
