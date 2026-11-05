import zipfile
from decimal import Decimal

import httpx
import pytest

from mangashelf.archive import validate_cbz
from mangashelf.downloader import DownloadError, download_cbz
from mangashelf.library import chapter_filename, find_gaps, list_chapters
from mangashelf.state import State


def make_cbz(path, images=("001.jpg",)):
    with zipfile.ZipFile(path, "w") as zf:
        for name in images:
            zf.writestr(name, b"x")
    return path


def cbz_bytes(tmp_path):
    return make_cbz(tmp_path / "src.cbz").read_bytes()


def test_validate(tmp_path):
    assert validate_cbz(make_cbz(tmp_path / "a.cbz"))[0]
    assert not validate_cbz(make_cbz(tmp_path / "b.cbz", images=("x.txt",)))[0]
    (tmp_path / "c.cbz").write_bytes(b"")
    assert not validate_cbz(tmp_path / "c.cbz")[0]
    (tmp_path / "d.cbz").write_bytes(b"lixo")
    assert not validate_cbz(tmp_path / "d.cbz")[0]


def test_filenames_and_order(tmp_path):
    assert chapter_filename(Decimal("1")) == "Capitulo_001.cbz"
    assert chapter_filename(Decimal("10.5")) == "Capitulo_010.5.cbz"
    for n in ("2", "10", "1", "1.5"):
        make_cbz(tmp_path / chapter_filename(Decimal(n)))
    nums = [n for n, _ in list_chapters(tmp_path)]
    assert nums == [Decimal(x) for x in ("1", "1.5", "2", "10")]
    assert find_gaps([Decimal(1), Decimal(4)]) == [2, 3]


def test_download_ok_and_skip(tmp_path):
    data = cbz_bytes(tmp_path)
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    dest = tmp_path / "lib" / "Capitulo_001.cbz"
    download_cbz(client, "http://x/1", dest, tmp_path / "dl")
    download_cbz(client, "http://x/1", dest, tmp_path / "dl")  # já válido: ignora
    assert len(calls) == 1 and validate_cbz(dest)[0]
    assert not list((tmp_path / "dl").glob("*.part"))


def test_download_retries_then_fails(tmp_path):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(DownloadError):
        download_cbz(client, "http://x/1", tmp_path / "a.cbz", tmp_path / "dl", max_retries=2, backoff=0)
    assert not (tmp_path / "a.cbz").exists()


def test_download_invalid_content_not_moved(tmp_path):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"html")))
    with pytest.raises(DownloadError):
        download_cbz(client, "http://x/1", tmp_path / "a.cbz", tmp_path / "dl", max_retries=1, backoff=0)
    assert not (tmp_path / "a.cbz").exists()


def test_state(tmp_path):
    s = State(tmp_path / "s.db")
    s.upsert("S", Decimal(1), "u1")
    s.upsert("S", Decimal(2), "u2")
    s.mark("S", Decimal(1), "done")
    s.mark("S", Decimal(2), "failed", "boom")
    assert s.counts("S") == {"pending": 0, "done": 1, "failed": 1}
    assert s.failed("S") == [(Decimal(2), "boom")]


def test_example_discover():
    from mangashelf.sources.example import ExampleSource

    def handler(req):
        assert req.url.path == "/serie.json"
        return httpx.Response(200, json={"chapters": [{"number": 1, "url": "http://x/1"}, {"number": 2, "url": "http://x/2"}]})

    src = ExampleSource("https://x.invalid/", client=httpx.Client(transport=httpx.MockTransport(handler)))
    ch = src.discover("serie")
    assert [c.number for c in ch] == [Decimal(1), Decimal(2)]
    assert ch[0].url == "http://x/1"


def test_move_cross_device_fallback(tmp_path, monkeypatch):
    import os

    from mangashelf import downloader

    src = make_cbz(tmp_path / "src.part")
    dest = tmp_path / "out" / "a.cbz"
    dest.parent.mkdir()
    real = os.replace

    def fake(a, b):
        if str(a) == str(src):
            raise OSError(18, "Invalid cross-device link")
        return real(a, b)

    monkeypatch.setattr(downloader.os, "replace", fake)
    downloader._move(src, dest)
    assert validate_cbz(dest)[0] and not src.exists()


def test_validate_accepts_jfif(tmp_path):
    assert validate_cbz(make_cbz(tmp_path / "j.cbz", images=("001.jfif",)))[0]
