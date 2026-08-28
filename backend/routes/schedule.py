from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from clients.json_store import InvalidScheduleReferenceError, PersistenceError
from clients.schedule import get_schedule_path, load_schedule, replace_schedule
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from models.schedule import ScheduleDocument

router = APIRouter(prefix="/admin/api/schedule", tags=["admin-schedule"])

ScheduleReplacerFunction = Callable[[ScheduleDocument, Path | None], ScheduleDocument]


def get_schedule_file_path() -> Path:
    return get_schedule_path()


def get_schedule_replacer() -> ScheduleReplacerFunction:
    return replace_schedule


SchedulePath = Annotated[Path, Depends(get_schedule_file_path)]
ScheduleReplacer = Annotated[ScheduleReplacerFunction, Depends(get_schedule_replacer)]


@router.get("", response_model=ScheduleDocument, response_model_exclude_none=True)
def read_schedule(_: CurrentTokenData, path: SchedulePath) -> dict:
    try:
        document = load_schedule(path)
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível carregar a agenda", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)


@router.put("", response_model=ScheduleDocument, response_model_exclude_none=True)
def update_schedule(
    payload: ScheduleDocument,
    _: CurrentTokenData,
    path: SchedulePath,
    replace: ScheduleReplacer,
) -> dict:
    try:
        document = replace(payload, path)
    except InvalidScheduleReferenceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(error),
                "references": [*error.locations, *error.knowledge_axes],
            },
        ) from error
    except PersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível salvar as alterações", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)
