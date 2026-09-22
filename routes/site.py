import os
from collections.abc import Callable
from pathlib import Path

from clients.knowledge_axes import get_knowledge_axes_path
from clients.locations import get_locations_path
from clients.schedule import get_schedule_path
from clients.settings import get_settings_path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

SITE_STATIC_DIR = Path(__file__).parents[1] / "static" / "site"
PUBLIC_JSON_PATH_FACTORIES: dict[str, Callable[[], Path]] = {
    "schedule.json": get_schedule_path,
    "locations.json": get_locations_path,
    "knowledge_axes.json": get_knowledge_axes_path,
    "settings.json": get_settings_path,
}

router = APIRouter()


@router.get("/db/{file_name}", include_in_schema=False)
def public_json(file_name: str) -> FileResponse:
    factory = PUBLIC_JSON_PATH_FACTORIES.get(file_name)
    if factory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
    path = factory()
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
    return FileResponse(
        path,
        media_type="application/json",
        headers={"Cache-Control": "no-cache"},
    )


class PublicSiteStaticFiles(StaticFiles):
    """Serve os arquivos do site na raiz pública da aplicação."""

    def get_path(self, scope: Scope) -> str:
        request_path = scope["path"]
        relative_path = request_path.lstrip("/")
        return os.path.normpath(relative_path) if relative_path else ""
