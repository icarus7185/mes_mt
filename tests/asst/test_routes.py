from io import BytesIO
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from asst.routers import api
from asst.services.image_service import ImageService


def _jpeg_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _client(monitor_client, raise_server_exceptions: bool = True) -> TestClient:
    app = FastAPI()
    app.include_router(api.router)
    app.state.http_client = monitor_client
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


@pytest.fixture
def image_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    in_dir, out_dir = tmp_path / "img_in", tmp_path / "img_out"
    monkeypatch.setattr(api, "image_in_service", ImageService(image_dir=in_dir))
    monkeypatch.setattr(api, "image_out_service", ImageService(image_dir=out_dir))
    return in_dir, out_dir


def _files_in(directory: Path) -> list[Path]:
    return list(directory.iterdir()) if directory.exists() else []


def _set_detection(monkeypatch: pytest.MonkeyPatch, detected: bool) -> None:
    result = (Image.new("RGB", (4, 4)), ["scratch"]) if detected else (None, [])
    monkeypatch.setattr(api.yolo_service, "predict", lambda image: result)


def test_image_without_detection_is_not_forwarded(
    image_dirs: tuple[Path, Path], fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_detection(monkeypatch, detected=False)
    monitor = fake_client_factory()

    response = _client(monitor).post(
        "/api/image", files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "normal", "file": "frame.jpg"}
    assert monitor.calls == []
    assert _files_in(image_dirs[0]) == []


def test_image_with_detection_is_forwarded_and_cleaned_up(
    image_dirs: tuple[Path, Path], fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_detection(monkeypatch, detected=True)
    monitor = fake_client_factory()

    response = _client(monitor).post(
        "/api/image", files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")}
    )

    body = response.json()
    assert response.status_code == 200
    assert body["classes"] == ["scratch"]
    assert body["saved_as"].startswith("frame_") and body["saved_as"].endswith(".jpg")
    assert len(monitor.calls) == 1
    assert monitor.calls[0]["url"] == api.settings.monitor_image_url
    assert monitor.calls[0]["files"]["file"][0] == body["saved_as"]
    assert _files_in(image_dirs[0]) == []
    assert _files_in(image_dirs[1]) == []


def test_image_forward_failure_keeps_output_file(
    image_dirs: tuple[Path, Path], fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_detection(monkeypatch, detected=True)
    monitor = fake_client_factory(error=httpx.ConnectError("monitor is down"))

    response = _client(monitor, raise_server_exceptions=False).post(
        "/api/image", files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")}
    )

    assert response.status_code == 500
    assert len(_files_in(image_dirs[1])) == 1


def test_image_without_file_is_rejected(fake_client_factory) -> None:
    assert _client(fake_client_factory()).post("/api/image").status_code == 422


def test_record_is_predicted_and_forwarded(
    fake_client_factory, monkeypatch: pytest.MonkeyPatch, sample_record: dict
) -> None:
    calls: list[tuple[dict, Path]] = []

    def fake_predict_one(record: dict, model_path: Path) -> float:
        calls.append((record, model_path))
        return 3.5

    monkeypatch.setattr(api, "predict_one", fake_predict_one)
    monitor = fake_client_factory()

    response = _client(monitor).post("/api/record", json=sample_record)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "Usage_kWh": 3.5}
    assert calls[0][1] == api.settings.analyst_model_path
    assert monitor.calls[0]["url"] == api.settings.monitor_record_url
    assert monitor.calls[0]["json"] == dict(sample_record, Usage_kWh=3.5)


def test_record_without_model_fails_and_is_not_forwarded(
    fake_client_factory, monkeypatch: pytest.MonkeyPatch, sample_record: dict
) -> None:
    def missing_model(record: dict, model_path: Path) -> float:
        raise FileNotFoundError(model_path)

    monkeypatch.setattr(api, "predict_one", missing_model)
    monitor = fake_client_factory()

    response = _client(monitor, raise_server_exceptions=False).post(
        "/api/record", json=sample_record
    )

    assert response.status_code == 500
    assert monitor.calls == []


def test_record_body_must_be_an_object(fake_client_factory) -> None:
    response = _client(fake_client_factory()).post("/api/record", json=[1, 2, 3])

    assert response.status_code == 422


def test_train_uses_configured_csv(fake_client_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def fake_train_model(training_csv_path: Path) -> dict:
        calls.append(training_csv_path)
        return {"mse": 1.0, "r2": 0.9, "model_path": "model.pkl"}

    monkeypatch.setattr(api, "train_model", fake_train_model)

    response = _client(fake_client_factory()).get("/api/train")

    assert response.json() == {"status": "success", "mse": 1.0, "r2": 0.9, "model_path": "model.pkl"}
    assert calls == [api.settings.training_csv_path]
