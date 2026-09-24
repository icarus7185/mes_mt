import asyncio

import httpx
import pytest

from prod_line import record_producer
from prod_line.record_state import RecordHistoryState


class _StubRecordService:
    def __init__(self, record: dict) -> None:
        self._record = record

    def get_next_record(self) -> dict:
        return dict(self._record)


@pytest.fixture
def history(monkeypatch: pytest.MonkeyPatch, sample_record: dict) -> RecordHistoryState:
    fresh = RecordHistoryState(max_items=5)
    monkeypatch.setattr(record_producer, "record_history_state", fresh)
    monkeypatch.setattr(record_producer, "record_service", _StubRecordService(sample_record))
    return fresh


def _send_record_once(client, history: RecordHistoryState) -> list[dict]:
    async def run() -> list[dict]:
        await record_producer.send_record_once(client)
        return await history.list_all()

    return asyncio.run(run())


def test_sends_record_to_asst(
    history: RecordHistoryState,
    fake_client_factory,
    monkeypatch: pytest.MonkeyPatch,
    sample_record: dict,
) -> None:
    monkeypatch.setattr(record_producer.settings, "record_send_failure_rate", 0.0)
    client = fake_client_factory()

    records = _send_record_once(client, history)

    assert len(client.calls) == 1
    assert client.calls[0]["url"] == record_producer.settings.asst_record_url
    assert client.calls[0]["json"] == sample_record
    assert len(records) == 1
    assert records[0]["send_success"] is True


def test_simulated_failure_skips_the_call_but_keeps_the_record(
    history: RecordHistoryState, fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(record_producer.settings, "record_send_failure_rate", 1.0)
    client = fake_client_factory()

    records = _send_record_once(client, history)

    assert client.calls == []
    assert len(records) == 1
    assert records[0]["send_success"] is False


def test_http_error_marks_record_as_failed(
    history: RecordHistoryState, fake_client_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(record_producer.settings, "record_send_failure_rate", 0.0)
    client = fake_client_factory(error=httpx.ConnectError("asst is down"))

    records = _send_record_once(client, history)

    assert len(client.calls) == 1
    assert records[0]["send_success"] is False
