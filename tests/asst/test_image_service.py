from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from asst.services import image_service as image_service_module
from asst.services.image_service import ImageService


class _FixedDatetime:
    @staticmethod
    def now() -> datetime:
        return datetime(2026, 9, 24, 10, 15, 3)


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (4, 3), (255, 0, 0, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_bytes_to_image_converts_to_rgb(tmp_path: Path) -> None:
    image = ImageService(image_dir=tmp_path).bytes_to_image(_png_bytes())

    assert image.mode == "RGB"
    assert image.size == (4, 3)


def test_save_bytes_creates_the_directory(tmp_path: Path) -> None:
    service = ImageService(image_dir=tmp_path / "nested" / "img_in")

    path = service.save_bytes(b"raw", "frame.jpg")

    assert path == tmp_path / "nested" / "img_in" / "frame.jpg"
    assert path.read_bytes() == b"raw"


def test_image_to_bytes_encodes_jpeg(tmp_path: Path) -> None:
    data = ImageService(image_dir=tmp_path).image_to_bytes(Image.new("RGB", (4, 4)))

    assert Image.open(BytesIO(data)).format == "JPEG"


@pytest.mark.parametrize(
    ("source_filename", "expected_name"),
    [("frame.png", "frame_101503.png"), ("frame", "frame_101503.jpg")],
)
def test_save_image_appends_time_to_the_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_filename: str,
    expected_name: str,
) -> None:
    monkeypatch.setattr(image_service_module, "datetime", _FixedDatetime)
    service = ImageService(image_dir=tmp_path / "img_out")

    path = service.save_image(Image.new("RGB", (4, 4)), source_filename)

    assert path == tmp_path / "img_out" / expected_name
    assert path.is_file()
