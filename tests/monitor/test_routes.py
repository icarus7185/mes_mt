import asyncio
import csv
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from monitor.routers import api, dashboard
from monitor.services.history_service import HistoryService
from monitor.services.record_csv_service import RecordCsvService
from monitor.services.record_service import RecordHistoryService


@pytest.fixture
def hist_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "img"
    monkeypatch.setattr(api.settings, "hist_dir", path)
    monkeypatch.setattr(api, "history_service", HistoryService(hist_dir=path, max_files=10))
    return path


@pytest.fixture
def csv_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "tabular"
    monkeypatch.setattr(api, "record_history_service", RecordHistoryService(max_items=20))
    monkeypatch.setattr(api, "record_csv_service", RecordCsvService(csv_dir=path))
    return path


@pytest.fixture
def client(hist_dir: Path, csv_dir: Path) -> TestClient:
    app = FastAPI()
    app.include_router(dashboard.router)
    app.include_router(api.router)
    return TestClient(app)


def _post_image(client: TestClient, filename: str, data: bytes) -> None:
    response = client.post("/api/image", files={"file": (filename, data, "image/jpeg")})
    assert response.json() == {"status": "ok"}


def test_endpoints_are_empty_before_anything_is_received(client: TestClient) -> None:
    assert client.get("/api/image/latest").status_code == 404
    assert client.get("/api/image/meta").json() == {"received_at": None, "filename": None}
    assert client.get("/api/hist").json() == {"images": []}
    assert client.get("/api/records").json() == {"records": []}


def test_received_image_is_archived_and_served(client: TestClient, hist_dir: Path) -> None:
    _post_image(client, "alert_101503.jpg", b"jpeg-bytes")

    latest = client.get("/api/image/latest")
    meta = client.get("/api/image/meta").json()
    album = client.get("/api/hist").json()["images"]
    single = client.get("/api/hist/alert_101503.jpg")

    assert (hist_dir / "alert_101503.jpg").read_bytes() == b"jpeg-bytes"
    assert latest.content == b"jpeg-bytes"
    assert latest.headers["content-type"] == "image/jpeg"
    assert meta["filename"] == "alert_101503.jpg"
    assert [image["filename"] for image in album] == ["alert_101503.jpg"]
    assert single.content == b"jpeg-bytes"


def test_image_without_file_is_rejected(client: TestClient) -> None:
    assert client.post("/api/image").status_code == 422


def test_unknown_history_image_returns_404(client: TestClient) -> None:
    assert client.get("/api/hist/missing.jpg").status_code == 404


def test_history_image_outside_archive_is_refused(hist_dir: Path) -> None:
    hist_dir.mkdir(parents=True)
    (hist_dir.parent / "secret.txt").write_text("secret")

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(api.get_history_image("../secret.txt"))

    assert excinfo.value.status_code == 404


def test_received_record_is_listed_and_logged(
    client: TestClient, csv_dir: Path, sample_record: dict
) -> None:
    record = dict(sample_record, Usage_kWh=3.5)

    response = client.post("/api/record", json=record)

    listed = client.get("/api/records").json()["records"]
    with (csv_dir / "records_history.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert response.json() == {"status": "ok"}
    assert len(listed) == 1
    assert listed[0]["Usage_kWh"] == 3.5
    assert "received_at" in listed[0]
    assert len(rows) == 1
    assert rows[0]["Usage_kWh"] == "3.5"


def test_record_body_must_be_an_object(client: TestClient) -> None:
    assert client.post("/api/record", json=[1, 2, 3]).status_code == 422


def test_dashboard_page_renders(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
