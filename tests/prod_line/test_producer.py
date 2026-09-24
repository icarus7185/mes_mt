import asyncio
from pathlib import Path

import httpx
import pytest

from prod_line import producer
from prod_line.services.image_service import ImageService
from prod_line.state import LastSent, ProducerState


@pytest.fixture
def state(monkeypatch: pytest.MonkeyPatch) -> ProducerState:
    fresh = ProducerState()
    monkeypatch.setattr(producer, "producer_state", fresh)
    return fresh


@pytest.fixture
def image_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "frame.jpg").write_bytes(b"jpeg-bytes")
    monkeypatch.setattr(producer, "image_service", ImageService(image_dir=tmp_path))
    return tmp_path


def _send_once(client, state: ProducerState) -> LastSent:
    async def run() -> LastSent:
        await producer.send_once(client)
        return await state.get()

    return asyncio.run(run())


@pytest.mark.usefixtures("image_dir")
def test_sends_image_to_asst(
    state: ProducerState, fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(producer.settings, "image_send_failure_rate", 0.0)
    client = fake_client_factory()

    latest = _send_once(client, state)

    assert len(client.calls) == 1
    assert client.calls[0]["url"] == producer.settings.asst_image_url
    assert client.calls[0]["files"] == {"file": ("frame.jpg", b"jpeg-bytes", "image/jpeg")}
    assert latest.success is True
    assert latest.filename == "frame.jpg"
    assert latest.image_bytes == b"jpeg-bytes"


@pytest.mark.usefixtures("image_dir")
def test_simulated_failure_skips_the_call_but_keeps_the_image(
    state: ProducerState, fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(producer.settings, "image_send_failure_rate", 1.0)
    client = fake_client_factory()

    latest = _send_once(client, state)

    assert client.calls == []
    assert latest.success is False
    assert latest.filename == "frame.jpg"


@pytest.mark.usefixtures("image_dir")
@pytest.mark.parametrize(
    "client_kwargs",
    [{"error": httpx.ConnectError("asst is down")}, {"status_code": 500}],
    ids=["connection-error", "server-error"],
)
def test_http_error_marks_send_as_failed(
    state: ProducerState,
    fake_client_factory,
    monkeypatch: pytest.MonkeyPatch,
    client_kwargs: dict,
) -> None:
    monkeypatch.setattr(producer.settings, "image_send_failure_rate", 0.0)

    latest = _send_once(fake_client_factory(**client_kwargs), state)

    assert latest.success is False
    assert latest.filename == "frame.jpg"


def test_no_source_image_changes_nothing(
    state: ProducerState,
    fake_client_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(producer, "image_service", ImageService(image_dir=tmp_path))
    client = fake_client_factory()

    latest = _send_once(client, state)

    assert client.calls == []
    assert latest == LastSent()
