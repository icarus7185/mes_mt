"""Picks a random source image file from disk."""

import random
from pathlib import Path
from typing import Optional

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


class ImageService:
    """Picks image files from ``self.image_dir``."""

    def __init__(self, image_dir: Path) -> None:
        self.image_dir = image_dir

    def get_random_image_path(self) -> Optional[Path]:
        """Return the path of a randomly chosen image file in
        ``self.image_dir``, or ``None`` if the directory has no images.
        """
        if not self.image_dir.is_dir():
            return None
        files = [
            p
            for p in self.image_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if not files:
            return None
        return random.choice(files)
