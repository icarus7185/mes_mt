"""Settings for the asst service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that incoming images are temporarily saved to before processing.
    image_in_dir: Path = Path("data/img_in")

    # Directory that YOLO-processed images are saved to.
    image_out_dir: Path = Path("data/img_out")

    # URL of the monitor service's image-intake endpoint.
    monitor_image_url: str = "http://localhost:8003/api/image"

    # Hugging Face Hub repo id of the YOLO model to load.
    hf_model_repo_id: str = "steven0226/steel-defect-segmentation"

    # File name/path of the model weights within the repo.
    hf_model_filename: str = "steel_defect_yolo26s_seg_best.pt"

    host: str = "0.0.0.0"
    port: int = 8002


settings = Settings()
