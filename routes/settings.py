from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from clients.json_store import PersistenceError
from clients.settings import get_settings_path, load_settings, replace_settings
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from models.settings import SettingsDocument

router = APIRouter(prefix="/settings", tags=["settings"])

SettingsReplacerFunction = Callable[[SettingsDocument, Path | None], SettingsDocument]


def get_settings_file_path() -> Path:
    return get_settings_path()


def get_settings_replacer() -> SettingsReplacerFunction:
    return replace_settings


SettingsPath = Annotated[Path, Depends(get_settings_file_path)]
SettingsReplacer = Annotated[SettingsReplacerFunction, Depends(get_settings_replacer)]


@router.get("", response_model=SettingsDocument, response_model_exclude_none=True)
def read_settings(_: CurrentTokenData, path: SettingsPath) -> dict:
    try:
        document = load_settings(path)
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível carregar as configurações", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)


@router.put("", response_model=SettingsDocument, response_model_exclude_none=True)
def update_settings(
    payload: SettingsDocument,
    _: CurrentTokenData,
    path: SettingsPath,
    replace: SettingsReplacer,
) -> dict:
    try:
        document = replace(payload, path)
    except PersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível salvar as configurações", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)
