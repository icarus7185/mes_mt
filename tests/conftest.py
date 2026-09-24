"""Fixtures shared by the tests of all three services."""

from pathlib import Path
from typing import Any, Optional

import httpx
import pandas as pd
import pytest

SAMPLE_RECORD = {
    "date": "24/09/2026 10:15:03",
    "Usage_kWh": None,
    "Lagging_Current_Reactive.Power_kVarh": 2.95,
    "Leading_Current_Reactive_Power_kVarh": 0.0,
    "CO2(tCO2)": 0.0,
    "Lagging_Current_Power_Factor": 73.21,
    "Leading_Current_Power_Factor": 100.0,
    "NSM": 900,
    "WeekStatus": "Weekday",
    "Day_of_week": "Monday",
    "Load_Type": "Light_Load",
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LOAD_TYPES = ["Light_Load", "Medium_Load", "Maximum_Load"]


class FakeAsyncClient:
    """Stands in for ``httpx.AsyncClient``: records every ``post`` call and
    answers with ``status_code``, or raises ``error`` when one is given.
    """

    def __init__(self, status_code: int = 200, error: Optional[Exception] = None) -> None:
        self.status_code = status_code
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        self.calls.append({"url": url, **kwargs})
        if self.error is not None:
            raise self.error
        return httpx.Response(self.status_code, request=httpx.Request("POST", url))


@pytest.fixture
def fake_client_factory() -> type[FakeAsyncClient]:
    return FakeAsyncClient


@pytest.fixture
def sample_record() -> dict:
    return dict(SAMPLE_RECORD)


@pytest.fixture(scope="session")
def steel_csv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A small dataset with the same columns as ``Steel_industry_data.csv``."""
    rows = []
    for i in range(60):
        day = DAYS[i % 7]
        rows.append(
            {
                "date": f"01/01/2018 {i // 4:02d}:{(i % 4) * 15:02d}",
                "Usage_kWh": round(2 + i * 0.5, 2),
                "Lagging_Current_Reactive.Power_kVarh": round(1 + i * 0.3, 2),
                "Leading_Current_Reactive_Power_kVarh": 0.0 if i % 2 else 1.5,
                "CO2(tCO2)": 0.0,
                "Lagging_Current_Power_Factor": 70.0 + i % 20,
                "Leading_Current_Power_Factor": 100.0,
                "NSM": (i * 900) % 86400,
                "WeekStatus": "Weekend" if day in ("Saturday", "Sunday") else "Weekday",
                "Day_of_week": day,
                "Load_Type": LOAD_TYPES[i % 3],
            }
        )
    path = tmp_path_factory.mktemp("data") / "steel.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path
