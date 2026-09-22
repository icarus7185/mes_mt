"""Settings for the monitor service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that received images are archived into.
    hist_dir: Path = Path("data/hist")

    # Maximum number of images to keep in hist_dir.
    hist_max_files: int = 10

    host: str = "0.0.0.0"
    port: int = 8003


settings = Settings()
