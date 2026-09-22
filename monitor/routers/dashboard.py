"""Dashboard page route."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="monitor/templates")


@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request) -> HTMLResponse:
    """Render the dashboard showing the latest image received from asst."""
    return templates.TemplateResponse(request, "dashboard.html")
