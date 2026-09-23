"""prod_line service entrypoint.

Every ``settings.interval_seconds``, reads a random image from
``settings.image_in_dir`` and pushes it to the asst service. Serves an
index page showing the image most recently sent and when it was sent.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from prod_line.producer import producer_loop
from prod_line.record_producer import record_producer_loop
from prod_line.routers import api, dashboard

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "prod_line.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(producer_loop())
    record_task = asyncio.create_task(record_producer_loop())
    try:
        yield
    finally:
        task.cancel()
        record_task.cancel()


app = FastAPI(title="prod_line", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="prod_line/static"), name="static")
app.include_router(dashboard.router)
app.include_router(api.router)
