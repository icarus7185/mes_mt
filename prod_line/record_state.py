"""In-memory, bounded history of tabular records read to send to asst."""

import asyncio
from collections import deque
from datetime import datetime

from prod_line.config import settings


class RecordHistoryState:
    def __init__(self, max_items: int) -> None:
        self._lock = asyncio.Lock()
        self._records: deque[dict] = deque(maxlen=max_items)

    async def add(self, record: dict, success: bool) -> None:
        entry = dict(record)
        entry["added_at"] = datetime.now().strftime("%H:%M:%S")
        entry["send_success"] = success
        async with self._lock:
            self._records.appendleft(entry)

    async def list_all(self) -> list[dict]:
        async with self._lock:
            return list(self._records)


record_history_state = RecordHistoryState(max_items=settings.record_max_items)
