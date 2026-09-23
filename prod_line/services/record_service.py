"""Picks a random tabular record, stamps it with the current time, and
clears its Usage_kWh value so asst can fill in a fresh prediction.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

DATE_FORMAT = "%d/%m/%Y %H:%M"


class RecordService:
    def __init__(self, csv_path: Path) -> None:
        self._data = pd.read_csv(csv_path)

    def get_random_record(self) -> dict:
        row = self._data.sample(n=1).iloc[0]
        record = {
            column: (value.item() if hasattr(value, "item") else value)
            for column, value in row.items()
        }
        record["date"] = datetime.now().strftime(DATE_FORMAT)
        record["Usage_kWh"] = None
        return record
