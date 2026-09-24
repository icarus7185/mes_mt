import os
import time
from pathlib import Path

from monitor.services.history_service import HistoryService


def _write_with_age(path: Path, age_seconds: int) -> None:
    path.write_bytes(path.name.encode())
    timestamp = time.time() - age_seconds
    os.utime(path, (timestamp, timestamp))


def test_list_files_is_empty_when_directory_is_missing(tmp_path: Path) -> None:
    assert HistoryService(hist_dir=tmp_path / "missing", max_files=10).list_files() == []


def test_save_creates_the_directory(tmp_path: Path) -> None:
    service = HistoryService(hist_dir=tmp_path / "img", max_files=10)

    path = service.save(b"image", "alert.jpg")

    assert path == tmp_path / "img" / "alert.jpg"
    assert path.read_bytes() == b"image"


def test_save_keeps_only_the_newest_files(tmp_path: Path) -> None:
    _write_with_age(tmp_path / "oldest.jpg", age_seconds=200)
    _write_with_age(tmp_path / "older.jpg", age_seconds=100)
    service = HistoryService(hist_dir=tmp_path, max_files=2)

    service.save(b"image", "new.jpg")

    assert [p.name for p in service.list_files()] == ["new.jpg", "older.jpg"]
    assert not (tmp_path / "oldest.jpg").exists()


def test_save_with_same_name_overwrites(tmp_path: Path) -> None:
    service = HistoryService(hist_dir=tmp_path, max_files=10)

    service.save(b"first", "alert.jpg")
    service.save(b"second", "alert.jpg")

    assert [p.name for p in service.list_files()] == ["alert.jpg"]
    assert (tmp_path / "alert.jpg").read_bytes() == b"second"
