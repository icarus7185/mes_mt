"""Receives source images from prod_line, runs YOLO on them, saves the
result to disk, and forwards the processed image to monitor.
"""

import logging

from fastapi import APIRouter, Request, UploadFile

from asst.config import settings
from asst.services.image_service import ImageService
from asst.services.yolo_service import YoloService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

image_in_service = ImageService(image_dir=settings.image_in_dir)
image_out_service = ImageService(image_dir=settings.image_out_dir)
yolo_service = YoloService(
    repo_id=settings.hf_model_repo_id,
    filename=settings.hf_model_filename,
)


@router.post("/image")
async def receive_image(request: Request, file: UploadFile) -> dict:
    """Save the uploaded image, run YOLO on it, save+forward the result to
    monitor, and clean up the temporary input/output files along the way.
    """
    logger.info("Received request file=%s", file.filename)

    data = await file.read()
    filename = file.filename or "image.jpg"
    in_path = image_in_service.save_bytes(data, filename)

    original_image = image_in_service.bytes_to_image(data)
    processed_image, class_names = yolo_service.predict(original_image)
    in_path.unlink(missing_ok=True)

    if processed_image is None:
        logger.info("No detection, normal result file=%s", filename)
        return {"status": "normal", "file": filename}

    out_path = image_out_service.save_image(processed_image, filename)
    logger.info("Saved processed file=%s classes=%s", out_path.name, class_names)

    processed_bytes = image_out_service.image_to_bytes(processed_image)
    response = await request.app.state.http_client.post(
        settings.monitor_image_url,
        files={"file": (out_path.name, processed_bytes, "image/jpeg")},
    )
    response.raise_for_status()
    logger.info("Forwarded file=%s to monitor", out_path.name)

    out_path.unlink(missing_ok=True)

    return {"saved_as": out_path.name, "classes": class_names}
