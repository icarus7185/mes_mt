from typing import Any, Optional

import numpy as np
import pytest
from PIL import Image

from asst.services import yolo_service as yolo_service_module
from asst.services.yolo_service import YoloService


class _FakeClassIds:
    def __init__(self, ids: list[float]) -> None:
        self._ids = ids

    def tolist(self) -> list[float]:
        return list(self._ids)


class _FakeBoxes:
    def __init__(self, ids: list[float]) -> None:
        self.cls = _FakeClassIds(ids)

    def __len__(self) -> int:
        return len(self.cls.tolist())


class _FakeResult:
    names = {0: "crazing", 1: "scratch"}

    def __init__(self, ids: Optional[list[float]], plotted: Optional[np.ndarray] = None) -> None:
        self.boxes = None if ids is None else _FakeBoxes(ids)
        self._plotted = plotted

    def plot(self) -> Optional[np.ndarray]:
        return self._plotted


class _FakeModel:
    def __init__(self, result: _FakeResult) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def predict(self, image: Image.Image, **kwargs: Any) -> list[_FakeResult]:
        self.calls.append(kwargs)
        return [self.result]


def _service_with(result: _FakeResult) -> YoloService:
    service = YoloService(repo_id="repo", filename="weights.pt", confidence_threshold=0.6)
    service.model = _FakeModel(result)
    return service


@pytest.mark.parametrize("ids", [None, []], ids=["no-boxes", "empty-boxes"])
def test_predict_returns_nothing_without_detection(ids: Optional[list[float]]) -> None:
    service = _service_with(_FakeResult(ids))

    assert service.predict(Image.new("RGB", (2, 2))) == (None, [])


def test_predict_returns_classes_and_rgb_image() -> None:
    plotted_bgr = np.zeros((2, 2, 3), dtype=np.uint8)
    plotted_bgr[..., 0] = 255
    service = _service_with(_FakeResult([1.0, 0.0, 1.0], plotted_bgr))

    image, classes = service.predict(Image.new("RGB", (2, 2)))

    assert classes == ["scratch", "crazing", "scratch"]
    assert image.getpixel((0, 0)) == (0, 0, 255)


def test_predict_passes_threshold_and_image_size() -> None:
    service = _service_with(_FakeResult(None))

    service.predict(Image.new("RGB", (2, 2)))

    assert service.model.calls == [{"imgsz": 1024, "conf": 0.6}]


def test_load_model_downloads_weights_from_the_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    downloads: list[tuple[str, str]] = []

    def fake_download(repo_id: str, filename: str) -> str:
        downloads.append((repo_id, filename))
        return "/cache/weights.pt"

    monkeypatch.setattr(yolo_service_module, "hf_hub_download", fake_download)
    monkeypatch.setattr(yolo_service_module, "YOLO", lambda weights: f"model:{weights}")
    service = YoloService(repo_id="repo", filename="weights.pt", confidence_threshold=0.6)

    service.load_model()

    assert downloads == [("repo", "weights.pt")]
    assert service.model == "model:/cache/weights.pt"
