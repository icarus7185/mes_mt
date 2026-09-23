"""Background loop: every ``settings.record_interval_seconds``, send the
next tabular record (with Usage_kWh cleared) to the asst service for
prediction. Reading starts from a randomly chosen row and advances
``settings.record_skip`` rows at a time.

To simulate an overloaded line, each send has a configurable probability
(``settings.record_send_failure_rate``) of being skipped instead of
actually sent. Whether the send succeeds or fails, the record is always
pushed to the dashboard grid, tagged with the outcome.
"""

import asyncio
import logging
import random

import httpx

from prod_line.config import settings
from prod_line.record_state import record_history_state
from prod_line.services.record_service import RecordService

logger = logging.getLogger(__name__)

record_service = RecordService(csv_path=settings.tabular_csv_path, skip=settings.record_skip)


async def send_record_once(client: httpx.AsyncClient) -> None:
    record = record_service.get_next_record()
    success = random.random() >= settings.record_send_failure_rate

    if success:
        try:
            response = await client.post(settings.asst_record_url, json=record)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "Failed to send record to asst at %s",
                settings.asst_record_url,
            )
            success = False
    else:
        logger.warning("Simulated overload: did not send record date=%s to asst", record["date"])

    await record_history_state.add(record, success=success)
    logger.info(
        "%s record date=%s to asst",
        "Sent" if success else "Did not send (simulated failure)",
        record["date"],
    )


async def record_producer_loop() -> None:
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        while True:
            try:
                await send_record_once(client)
            except Exception:
                logger.exception("Failed to send record to asst")
            await asyncio.sleep(settings.record_interval_seconds)
