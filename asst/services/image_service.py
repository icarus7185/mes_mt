"""Decodes/encodes images and saves processed results to disk."""

from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image


class ImageService:
    """Converts image bytes to/from PIL and saves results under ``self.image_dir``."""

    def __init__(self, image_dir: Path) -> None:
        self.image_dir = image_dir

    def bytes_to_image(self, data: bytes) -> Image.Image:
        return Image.open(BytesIO(data)).convert("RGB")

    def save_bytes(self, data: bytes, filename: str) -> Path:
        """Save raw ``data`` into ``self.image_dir`` under ``filename``."""
        self.image_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.image_dir / filename
        out_path.write_bytes(data)
        return out_path

    def image_to_bytes(self, image: Image.Image, format: str = "JPEG") -> bytes:
        buffer = BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    def save_image(self, image: Image.Image, source_filename: str) -> Path:
        """Save ``image`` into ``self.image_dir``, naming it after
        ``source_filename`` with the current HHMMSS time appended.
        """
        self.image_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(source_filename).stem
        suffix = Path(source_filename).suffix or ".jpg"
        timestamp = datetime.now().strftime("%H%M%S")
        out_path = self.image_dir / f"{stem}_{timestamp}{suffix}"
        image.save(out_path)
        return out_path
