import asyncio
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prod_line.record_state import RecordHistoryState
from prod_line.routers import api, dashboard
from prod_line.state import ProducerState


class _StubRecordService:
    def __init__(self) -> None:
        self.reset_calls = 0

    def reset_random_position(self) -> None:
        self.reset_calls += 1


@pytest.fixture
def producer_state(monkeypatch: pytest.MonkeyPatch) -> ProducerState:
    fresh = ProducerState()
    monkeypatch.setattr(api, "producer_state", fresh)
    return fresh


@pytest.fixture
def record_history(monkeypatch: pytest.MonkeyPatch) -> RecordHistoryState:
    fresh = RecordHistoryState(max_items=5)
    monkeypatch.setattr(api, "record_history_state", fresh)
    return fresh


@pytest.fixture
def record_service(monkeypatch: pytest.MonkeyPatch) -> _StubRecordService:
    stub = _StubRecordService()
    monkeypatch.setattr(dashboard, "record_service", stub)
    return stub


@pytest.fixture
def client(
    producer_state: ProducerState,
    record_history: RecordHistoryState,
    record_service: _StubRecordService,
) -> TestClient:
    app = FastAPI()
    app.include_router(dashboard.router)
    app.include_router(api.router)
    return TestClient(app)


def test_endpoints_are_empty_before_anything_is_sent(client: TestClient) -> None:
    assert client.get("/api/image/latest").status_code == 404
    assert client.get("/api/image/meta").json() == {
        "sent_at": None,
        "filename": None,
        "success": None,
    }
    assert client.get("/api/records").json() == {"records": []}


def test_latest_image_and_meta(client: TestClient, producer_state: ProducerState) -> None:
    asyncio.run(producer_state.set_sent(b"jpeg-bytes", "frame.jpg", success=False))

    image = client.get("/api/image/latest")
    meta = client.get("/api/image/meta").json()

    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert image.content == b"jpeg-bytes"
    assert meta["filename"] == "frame.jpg"
    assert meta["success"] is False
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", meta["sent_at"])


def test_records_are_listed_newest_first(
    client: TestClient, record_history: RecordHistoryState
) -> None:
    async def fill() -> None:
        await record_history.add({"NSM": 0}, success=True)
        await record_history.add({"NSM": 900}, success=False)

    asyncio.run(fill())

    records = client.get("/api/records").json()["records"]

    assert [r["NSM"] for r in records] == [900, 0]
    assert [r["send_success"] for r in records] == [False, True]


def test_index_page_resets_the_record_cursor(
    client: TestClient, record_service: _StubRecordService
) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert record_service.reset_calls == 1
