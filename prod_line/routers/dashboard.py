"""Index page route."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from prod_line.record_producer import record_service

router = APIRouter()
templates = Jinja2Templates(directory="prod_line/templates")


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request) -> HTMLResponse:
    """Render the index page showing the image most recently sent to asst.

    Also re-rolls the tabular record reading position, so each page load
    starts a fresh random walk through the CSV.
    """
    record_service.reset_random_position()
    return templates.TemplateResponse(request, "index.html")
