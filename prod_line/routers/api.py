"""Serves the most recently sent image to the index page."""

from fastapi import APIRouter, HTTPException, Response

from prod_line.record_state import record_history_state
from prod_line.state import producer_state

router = APIRouter(prefix="/api")


@router.get("/image/latest")
async def get_latest_image() -> Response:
    """Return the most recently sent image."""
    latest = await producer_state.get()
    if latest.image_bytes is None:
        raise HTTPException(status_code=404, detail="No image sent yet")
    return Response(content=latest.image_bytes, media_type="image/jpeg")


@router.get("/image/meta")
async def get_latest_meta() -> dict:
    """Return the file name and time the latest image was sent."""
    latest = await producer_state.get()
    if latest.sent_at is None:
        return {"sent_at": None, "filename": None, "success": None}
    return {
        "sent_at": latest.sent_at.strftime("%H:%M:%S"),
        "filename": latest.filename,
        "success": latest.success,
    }


@router.get("/records")
async def list_records() -> dict:
    """List tabular records read for sending to asst, newest first."""
    return {"records": await record_history_state.list_all()}
