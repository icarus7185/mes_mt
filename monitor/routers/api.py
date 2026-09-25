"""Receives processed images pushed by asst, archives them into a bounded
history folder, and serves the latest image plus the recent history to
the dashboard.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response, UploadFile

from monitor.config import settings
from monitor.services.history_service import IMAGE_EXTENSIONS, HistoryService
from monitor.services.record_csv_service import RecordCsvService
from monitor.services.record_service import RecordHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

history_service = HistoryService(hist_dir=settings.hist_dir, max_files=settings.hist_max_files)
record_history_service = RecordHistoryService(max_items=settings.record_max_items)
record_csv_service = RecordCsvService(csv_dir=settings.tabular_dir)


def _received_at(path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M:%S")


@router.post("/image")
async def receive_image(file: UploadFile) -> dict:
    """Archive the processed image pushed by asst into the history folder."""
    logger.info("Received request file=%s", file.filename)
    data = await file.read()
    history_service.save(data, file.filename or "image.jpg")
    return {"status": "ok"}


@router.get("/image/latest")
async def get_latest_image() -> Response:
    """Return the most recently archived image as JPEG, or 404 if none yet."""
    files = history_service.list_files()
    if not files:
        raise HTTPException(status_code=404, detail="No image received yet")
    return Response(content=files[0].read_bytes(), media_type="image/jpeg")


@router.get("/image/meta")
async def get_latest_meta() -> dict:
    """Return the file name and time the latest image was received.

    Returns ``{"received_at": "HH:MM:SS", "filename": <name>}``, with both
    fields null when no image has been received yet.
    """
    files = history_service.list_files()
    if not files:
        return {"received_at": None, "filename": None}
    return {"received_at": _received_at(files[0]), "filename": files[0].name}


@router.get("/hist")
async def list_history() -> dict:
    """List the archived images, newest first, for the dashboard album.

    Returns ``{"images": [{"filename", "received_at"}, ...]}``.
    """
    return {
        "images": [
            {"filename": path.name, "received_at": _received_at(path)}
            for path in history_service.list_files()
        ]
    }


@router.post("/record")
async def receive_record(record: dict) -> dict:
    """Store a predicted tabular record pushed by asst.

    The record goes into the in-memory dashboard grid and is appended to the
    permanent CSV history. Returns ``{"status": "ok"}``.
    """
    logger.info("Received record date=%s Usage_kWh=%s", record.get("date"), record.get("Usage_kWh"))
    record_history_service.add(record)
    record_csv_service.append(record)
    return {"status": "ok"}


@router.get("/records")
async def list_records() -> dict:
    """List predicted tabular records, newest first, for the dashboard grid."""
    return {"records": record_history_service.list_all()}


@router.get("/hist/{filename}")
async def get_history_image(filename: str) -> Response:
    """Return one archived image by file name.

    Returns 404 if the file is missing, is not an image (e.g.
    ``.placeholder``), or resolves outside the archive folder.
    """
    path = (settings.hist_dir / filename).resolve()
    hist_root = settings.hist_dir.resolve()
    if (
        not path.is_relative_to(hist_root)
        or not path.is_file()
        or path.suffix.lower() not in IMAGE_EXTENSIONS
    ):
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=path.read_bytes(), media_type="image/jpeg")
