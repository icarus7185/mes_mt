"""Settings for the asst service."""

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Directory that incoming images are temporarily saved to before processing.
    image_in_dir: Path = Path("asst/data/img_in")

    # Directory that YOLO-processed images are saved to.
    image_out_dir: Path = Path("asst/data/img_out")

    # URL of the monitor service's image-intake endpoint.
    monitor_image_url: str = "http://localhost:8003/api/image"

    # Hugging Face Hub repo id of the YOLO model to load.
    hf_model_repo_id: str = "steven0226/steel-defect-segmentation"

    # File name/path of the model weights within the repo.
    hf_model_filename: str = "steel_defect_yolo26s_seg_best.pt"

    # Minimum confidence required for a YOLO detection.
    yolo_confidence_threshold: float = 0.7

    # CSV file used to train the energy-usage prediction model.
    training_csv_path: Path = Path("asst/data/train/Steel_industry_data.csv")

    # Saved energy-usage model used to predict Usage_kWh for incoming records.
    analyst_model_path: Path = Path("asst/data/model/analyst_model.pkl")

    # URL of the monitor service's record-intake endpoint.
    monitor_record_url: str = "http://localhost:8003/api/record"

    host: str = "0.0.0.0"
    port: int = 8002


settings = Settings()
