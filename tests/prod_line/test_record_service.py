from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from prod_line.services import record_service as record_service_module
from prod_line.services.record_service import DATE_FORMAT, RecordService


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    path = tmp_path / "records.csv"
    pd.DataFrame(
        {
            "date": [f"01/01/2018 00:{i:02d}" for i in range(5)],
            "Usage_kWh": [float(i) for i in range(5)],
            "NSM": [i * 900 for i in range(5)],
            "Load_Type": ["Light_Load"] * 5,
        }
    ).to_csv(path, index=False)
    return path


def _service_starting_at(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch, start: int, skip: int
) -> RecordService:
    monkeypatch.setattr(record_service_module.random, "randrange", lambda n: start)
    return RecordService(csv_path, skip=skip)


def test_next_record_clears_usage_and_stamps_current_time(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service_starting_at(csv_path, monkeypatch, start=1, skip=1)

    before = datetime.now().replace(microsecond=0)
    record = service.get_next_record()
    after = datetime.now()

    assert record["Usage_kWh"] is None
    assert before <= datetime.strptime(record["date"], DATE_FORMAT) <= after
    assert record["NSM"] == 900
    assert record["Load_Type"] == "Light_Load"


def test_next_record_returns_native_python_types(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _service_starting_at(csv_path, monkeypatch, start=0, skip=1).get_next_record()

    assert type(record["NSM"]) is int


def test_position_advances_by_skip_and_wraps_around(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service_starting_at(csv_path, monkeypatch, start=3, skip=2)

    nsm_values = [service.get_next_record()["NSM"] for _ in range(4)]

    assert nsm_values == [3 * 900, 0, 2 * 900, 4 * 900]


def test_reset_random_position_moves_the_cursor(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    requested_bounds: list[int] = []
    positions = iter([1, 4])

    def fake_randrange(n: int) -> int:
        requested_bounds.append(n)
        return next(positions)

    monkeypatch.setattr(record_service_module.random, "randrange", fake_randrange)
    service = RecordService(csv_path, skip=1)

    assert service.get_next_record()["NSM"] == 900
    service.reset_random_position()
    assert service.get_next_record()["NSM"] == 4 * 900
    assert requested_bounds == [5, 5]
