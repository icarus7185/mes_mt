"""Index page route."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="prod_line/templates")


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request) -> HTMLResponse:
    """Render the index page showing the image most recently sent to asst."""
    return templates.TemplateResponse(request, "index.html")
