"""Background loop: every ``settings.interval_seconds``, send a random
image from ``settings.image_in_dir`` to the asst service.
"""

import asyncio
import logging

import httpx

from prod_line.config import settings
from prod_line.services.image_service import ImageService
from prod_line.state import producer_state

logger = logging.getLogger(__name__)

image_service = ImageService(image_dir=settings.image_in_dir)


async def send_once(client: httpx.AsyncClient) -> None:
    image_path = image_service.get_random_image_path()
    if image_path is None:
        logger.warning("No source images found in %s", settings.image_in_dir)
        return

    data = image_path.read_bytes()
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
        return

    await producer_state.set_sent(data, image_path.name)
    logger.info("Sent %s to asst", image_path.name)


async def producer_loop() -> None:
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        while True:
            try:
                await send_once(client)
            except Exception:
                logger.exception("Failed to send image to asst")
            await asyncio.sleep(settings.interval_seconds)
