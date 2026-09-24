import re

from monitor.services.record_service import RecordHistoryService


def test_records_are_bounded_and_newest_first() -> None:
    service = RecordHistoryService(max_items=2)

    for i in range(3):
        service.add({"NSM": i})

    records = service.list_all()
    assert [r["NSM"] for r in records] == [2, 1]
    assert all(re.fullmatch(r"\d{2}:\d{2}:\d{2}", r["received_at"]) for r in records)


def test_add_does_not_mutate_the_input(sample_record: dict) -> None:
    original = dict(sample_record)

    RecordHistoryService(max_items=5).add(sample_record)

    assert sample_record == original
