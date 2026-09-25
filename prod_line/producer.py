"""Background loop: every ``settings.interval_seconds``, send a random
image from ``settings.image_in_dir`` to the asst service.

To simulate an overloaded line, each send has a configurable probability
(``settings.image_send_failure_rate``) of being skipped instead of
actually sent. Whether the send succeeds or fails, the picked image is
always shown on the index page, tagged with the outcome.
"""

import asyncio
import logging
import random

import httpx

from prod_line.config import settings
from prod_line.services.image_service import ImageService
from prod_line.state import producer_state

logger = logging.getLogger(__name__)

image_service = ImageService(image_dir=settings.image_in_dir)


async def send_once(client: httpx.AsyncClient) -> None:
    """Pick a random image and send it to asst, unless the simulated failure
    roll skips it. Sent or not, the image and its outcome are stored in
    ``producer_state`` for the index page.
    """
    image_path = image_service.get_random_image_path()
    if image_path is None:
        logger.warning("No source images found in %s", settings.image_in_dir)
        return

    data = image_path.read_bytes()
    success = random.random() >= settings.image_send_failure_rate

    if success:
        files = {"file": (image_path.name, data, "image/jpeg")}
        try:
            response = await client.post(settings.asst_image_url, files=files)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "Failed to send %s to asst at %s",
                image_path.name,
                settings.asst_image_url,
            )
            success = False
    else:
        logger.warning("Simulated overload: did not send %s to asst", image_path.name)

    await producer_state.set_sent(data, image_path.name, success=success)
    logger.info("%s %s to asst", "Sent" if success else "Did not send (simulated failure)", image_path.name)


async def producer_loop() -> None:
    """Call ``send_once`` every ``interval_seconds`` until cancelled; a failed
    tick is logged and the loop keeps going.
    """
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        while True:
            try:
                await send_once(client)
            except Exception:
                logger.exception("Failed to send image to asst")
            await asyncio.sleep(settings.interval_seconds)
