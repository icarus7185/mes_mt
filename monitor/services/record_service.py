"""Keeps a bounded, newest-first history of predicted tabular records
received from asst.
"""

from collections import deque
from datetime import datetime


class RecordHistoryService:
    def __init__(self, max_items: int) -> None:
        self._records: deque[dict] = deque(maxlen=max_items)

    def add(self, record: dict) -> None:
        entry = dict(record)
        entry["received_at"] = datetime.now().strftime("%H:%M:%S")
        self._records.appendleft(entry)

    def list_all(self) -> list[dict]:
        return list(self._records)
