"""Settings for the prod_line service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that source images are randomly picked from.
    image_in_dir: Path = Path("data/from_camera")

    # How often, in seconds, to pick and send a new image.
    interval_seconds: float = 10.0

    # URL of the asst service's image-intake endpoint.
    asst_image_url: str = "http://localhost:8002/api/image"

    host: str = "0.0.0.0"
    port: int = 8001


settings = Settings()
