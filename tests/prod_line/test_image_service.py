from pathlib import Path

from prod_line.services.image_service import ImageService


def test_returns_none_when_directory_is_missing(tmp_path: Path) -> None:
    assert ImageService(image_dir=tmp_path / "missing").get_random_image_path() is None


def test_returns_none_when_directory_has_no_images(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("not an image")

    assert ImageService(image_dir=tmp_path).get_random_image_path() is None


def test_picks_only_image_files(tmp_path: Path) -> None:
    (tmp_path / "frame.JPG").write_bytes(b"image")
    (tmp_path / "notes.txt").write_text("not an image")
    (tmp_path / "folder.jpg").mkdir()
    service = ImageService(image_dir=tmp_path)

    picked = {service.get_random_image_path() for _ in range(20)}

    assert picked == {tmp_path / "frame.JPG"}
