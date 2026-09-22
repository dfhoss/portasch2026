import os
from pathlib import Path

from clients.json_store import PersistenceError, atomic_write_json, read_json
from models.settings import SettingsDocument

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_settings_path() -> Path:
    override = os.environ.get("SETTINGS_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "settings.json"


def load_settings(path: Path) -> SettingsDocument:
    return SettingsDocument.model_validate(read_json(path))


def save_settings(document: SettingsDocument, path: Path) -> None:
    atomic_write_json(
        path,
        document.model_dump(by_alias=True, exclude_unset=True, mode="json"),
    )


def replace_settings(document: SettingsDocument, path: Path | None = None) -> SettingsDocument:
    destination = path or get_settings_path()
    try:
        save_settings(document, destination)
    except OSError as error:
        raise PersistenceError("Não foi possível persistir as configurações") from error
    return document
