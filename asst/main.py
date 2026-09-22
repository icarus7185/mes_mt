"""asst service entrypoint.

Receives a source image pushed by prod_line, runs it through YOLO, saves
the processed result to disk, and forwards the processed image to monitor.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI

from asst.routers import api
from asst.routers.api import yolo_service

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "asst.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yolo_service.load_model()
    app.state.http_client = httpx.AsyncClient(timeout=10.0, trust_env=False)
    try:
        yield
    finally:
        await app.state.http_client.aclose()


app = FastAPI(title="asst", lifespan=lifespan)
app.include_router(api.router)
