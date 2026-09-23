"""Settings for the monitor service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that received images are archived into.
    hist_dir: Path = Path("monitor/data/img")

    # Maximum number of images to keep in hist_dir.
    hist_max_files: int = 10

    # Maximum number of predicted tabular records to keep for the dashboard grid.
    record_max_items: int = 20

    # Directory that predicted tabular records are archived into as CSV history.
    tabular_dir: Path = Path("monitor/data/tabular")

    host: str = "0.0.0.0"
    port: int = 8003


settings = Settings()
