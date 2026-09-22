"""Interface for the Hugging Face YOLO model."""

from typing import Any, Optional

from huggingface_hub import hf_hub_download
from PIL import Image
from ultralytics import YOLO


class YoloService:
    """Loads a YOLO model from the Hugging Face Hub and runs inference."""

    def __init__(self, repo_id: str, filename: str) -> None:
        self.repo_id = repo_id
        self.filename = filename
        self.model: Optional[Any] = None

    def load_model(self) -> None:
        weights = hf_hub_download(self.repo_id, self.filename)
        self.model = YOLO(weights)

    def predict(self, image: Image.Image) -> tuple[Optional[Image.Image], list[str]]:
        """Run inference and return the plotted image and the detected
        class names, or ``(None, [])`` when nothing was detected.
        """
        result = self.model.predict(image, imgsz=1024)[0]
        if result.boxes is None or len(result.boxes) == 0:
            return None, []

        class_names = [result.names[int(class_id)] for class_id in result.boxes.cls.tolist()]
        plotted_bgr = result.plot()
        plotted_image = Image.fromarray(plotted_bgr[:, :, ::-1])
        return plotted_image, class_names
