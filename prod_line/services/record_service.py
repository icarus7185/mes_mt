"""Walks the tabular CSV from a randomly chosen starting row, stepping by
``skip`` rows on each subsequent read, and stamps each record with the
current time while clearing its Usage_kWh value so asst can predict it.
"""

import random
from datetime import datetime
from pathlib import Path

import pandas as pd

DATE_FORMAT = "%d/%m/%Y %H:%M:%S"


class RecordService:
    def __init__(self, csv_path: Path, skip: int = 2) -> None:
        self._data = pd.read_csv(csv_path)
        self._skip = skip
        self._position = 0
        self.reset_random_position()

    def reset_random_position(self) -> None:
        """Jump to a random row; the next read starts from there."""
        self._position = random.randrange(len(self._data))

    def get_next_record(self) -> dict:
        """Return the record at the current position, then advance by ``skip``
        (wrapping at the end of the file).

        The record is a dict keyed by the CSV column names, with ``date`` set to
        now and ``Usage_kWh`` set to None.
        """
        row = self._data.iloc[self._position]
        record = {
            column: (value.item() if hasattr(value, "item") else value)
            for column, value in row.items()
        }
        record["date"] = datetime.now().strftime(DATE_FORMAT)
        record["Usage_kWh"] = None

        self._position = (self._position + self._skip) % len(self._data)
        return record
