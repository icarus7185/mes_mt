import asyncio
import re

from prod_line.record_state import RecordHistoryState
from prod_line.state import LastSent, ProducerState


def test_producer_state_is_empty_before_first_send() -> None:
    latest = asyncio.run(ProducerState().get())

    assert latest == LastSent()


def test_producer_state_keeps_the_latest_send() -> None:
    async def run() -> LastSent:
        state = ProducerState()
        await state.set_sent(b"first", "first.jpg", success=True)
        await state.set_sent(b"second", "second.jpg", success=False)
        return await state.get()

    latest = asyncio.run(run())

    assert latest.image_bytes == b"second"
    assert latest.filename == "second.jpg"
    assert latest.success is False
    assert latest.sent_at is not None


def test_record_history_is_bounded_and_newest_first() -> None:
    async def run() -> list[dict]:
        state = RecordHistoryState(max_items=2)
        for i in range(3):
            await state.add({"NSM": i}, success=i != 1)
        return await state.list_all()

    records = asyncio.run(run())

    assert [r["NSM"] for r in records] == [2, 1]
    assert [r["send_success"] for r in records] == [True, False]
    assert all(re.fullmatch(r"\d{2}:\d{2}:\d{2}", r["added_at"]) for r in records)


def test_record_history_does_not_mutate_the_input(sample_record: dict) -> None:
    original = dict(sample_record)

    asyncio.run(RecordHistoryState(max_items=5).add(sample_record, success=True))

    assert sample_record == original
