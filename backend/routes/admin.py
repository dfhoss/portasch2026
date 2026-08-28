import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

router = APIRouter(tags=["admin"])

ADMIN_STATIC_DIR = Path(__file__).parents[1] / "static" / "admin"
ADMIN_INDEX_PATH = ADMIN_STATIC_DIR / "index.html"


class AdminStaticFiles(StaticFiles):
    """Serve the admin assets with or without the application's API root path."""

    def get_path(self, scope: Scope) -> str:
        request_path = scope["path"]
        prefix = "/admin/static"
        if request_path.startswith(prefix):
            return os.path.normpath(request_path.removeprefix(prefix).lstrip("/"))
        return super().get_path(scope)


@router.get("/admin", include_in_schema=False)
def read_admin_page() -> FileResponse:
    return FileResponse(ADMIN_INDEX_PATH)
