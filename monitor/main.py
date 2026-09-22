"""monitor service entrypoint.

Serves a dashboard showing the most recent processed image pushed by
asst, along with the time it was received.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from monitor.routers import api, dashboard

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

app = FastAPI(title="monitor")
app.mount("/static", StaticFiles(directory="monitor/static"), name="static")
app.include_router(dashboard.router)
app.include_router(api.router)
