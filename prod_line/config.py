"""Settings for the prod_line service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that source images are randomly picked from.
    image_in_dir: Path = Path("prod_line/data/from_camera")

    # How often, in seconds, to pick and send a new image.
    interval_seconds: float = 15.0

    # URL of the asst service's image-intake endpoint.
    asst_image_url: str = "http://localhost:8002/api/image"

    # CSV file that tabular records are randomly picked from.
    tabular_csv_path: Path = Path("prod_line/data/tabular/Steel_industry_data.csv")

    # How often, in seconds, to pick and send a new tabular record.
    record_interval_seconds: float = 60.0

    # URL of the asst service's record-intake endpoint.
    asst_record_url: str = "http://localhost:8002/api/record"

    # Number of rows to advance in the CSV between consecutive reads.
    record_skip: int = 2

    # Maximum number of tabular records to keep for the dashboard grid.
    record_max_items: int = 20

    host: str = "0.0.0.0"
    port: int = 8001


settings = Settings()
