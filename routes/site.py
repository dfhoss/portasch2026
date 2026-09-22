import os
from pathlib import Path

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

SITE_STATIC_DIR = Path(__file__).parents[1] / "static" / "site"


class PublicSiteStaticFiles(StaticFiles):
    """Serve os arquivos do site na raiz pública da aplicação."""

    def get_path(self, scope: Scope) -> str:
        request_path = scope["path"]
        relative_path = request_path.lstrip("/")
        return os.path.normpath(relative_path) if relative_path else ""
