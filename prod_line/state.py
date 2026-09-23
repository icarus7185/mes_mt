"""In-memory holder for the most recently sent image."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LastSent:
    image_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    sent_at: Optional[datetime] = None
    success: Optional[bool] = None


class ProducerState:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._last_sent = LastSent()

    async def set_sent(self, data: bytes, filename: str, success: bool) -> None:
        async with self._lock:
            self._last_sent = LastSent(
                image_bytes=data, filename=filename, sent_at=datetime.now(), success=success
            )

    async def get(self) -> LastSent:
        async with self._lock:
            return LastSent(
                image_bytes=self._last_sent.image_bytes,
                filename=self._last_sent.filename,
                sent_at=self._last_sent.sent_at,
                success=self._last_sent.success,
            )


producer_state = ProducerState()
