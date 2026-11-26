"""Tests for descarga_geonames(): no network, urlopen is replaced by a fake."""
import io
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import oficina_cercana  # noqa: E402


def make_zip(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in members.items():
            z.writestr(name, text)
    return buf.getvalue()


def fake_es_txt(lines=1500, columns=12):
    row = "\t".join(["ES"] + ["x"] * (columns - 1))
    return "\n".join([row] * lines) + "\n"


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.data


def patch_urlopen(monkeypatch, data=None, error=None):
    calls = []

    def fake(url, *args, **kwargs):
        calls.append(kwargs)
        if error is not None:
            raise error
        return FakeResponse(data)

    monkeypatch.setattr("urllib.request.urlopen", fake)
    return calls


def test_valid_zip_creates_es_txt_with_timeout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = patch_urlopen(monkeypatch, make_zip({"ES.txt": fake_es_txt()}))
    oficina_cercana.descarga_geonames()
    assert (tmp_path / "ES.txt").exists()
    assert not (tmp_path / "ES.txt.part").exists()
    assert "timeout" in calls[0]


@pytest.mark.parametrize("case", ["no_member", "garbage", "few_lines", "urlerror", "not_zip"])
def test_failures_exit_and_leave_no_files(tmp_path, monkeypatch, case):
    monkeypatch.chdir(tmp_path)
    if case == "no_member":
        patch_urlopen(monkeypatch, make_zip({"otro.txt": fake_es_txt()}))
    elif case == "garbage":
        patch_urlopen(monkeypatch, make_zip({"ES.txt": "basura sin tabuladores\n" * 2000}))
    elif case == "few_lines":
        patch_urlopen(monkeypatch, make_zip({"ES.txt": fake_es_txt(lines=10)}))
    elif case == "urlerror":
        patch_urlopen(monkeypatch, error=urllib.error.URLError("sin red"))
    else:
        patch_urlopen(monkeypatch, b"esto no es un zip")
    with pytest.raises(SystemExit) as exc:
        oficina_cercana.descarga_geonames()
    assert isinstance(exc.value.code, str) and exc.value.code
    assert list(tmp_path.iterdir()) == []
