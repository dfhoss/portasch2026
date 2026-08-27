from collections.abc import Callable
from typing import Annotated, TypeVar

from clients.json_store import (
    DuplicateResourceNameError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
)
from clients.locations import LocationRepository, get_locations_path
from clients.schedule import get_schedule_path
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/api/locations", tags=["admin-locations"])


class LocationInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class LocationResponse(BaseModel):
    id: str
    name: str


def get_location_repository() -> LocationRepository:
    return LocationRepository(get_locations_path(), get_schedule_path())


LocationRepo = Annotated[LocationRepository, Depends(get_location_repository)]
Result = TypeVar("Result")


def _run(operation: Callable[[], Result]) -> Result:
    try:
        return operation()
    except ResourceNotFoundError as error:
        raise _http_error(status.HTTP_404_NOT_FOUND, str(error)) from error
    except DuplicateResourceNameError as error:
        raise _http_error(status.HTTP_409_CONFLICT, str(error)) from error
    except ResourceInUseError as error:
        raise _http_error(status.HTTP_409_CONFLICT, str(error), error.references) from error
    except InvalidResourceNameError as error:
        raise _http_error(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except PersistenceError as error:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Não foi possível salvar as alterações",
        ) from error


def _http_error(
    status_code: int, message: str, references: list[str] | None = None
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "references": references or []},
    )


@router.get("", response_model=list[LocationResponse])
def list_locations(_: CurrentTokenData, repository: LocationRepo) -> list[dict]:
    return _run(repository.list)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocationResponse)
def create_location(payload: LocationInput, _: CurrentTokenData, repository: LocationRepo) -> dict:
    return _run(lambda: repository.create(payload.name.strip()))


@router.put("/{location_id}", response_model=LocationResponse)
def rename_location(
    location_id: str,
    payload: LocationInput,
    _: CurrentTokenData,
    repository: LocationRepo,
) -> dict:
    return _run(lambda: repository.rename(location_id, payload.name.strip()))


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: str, _: CurrentTokenData, repository: LocationRepo) -> None:
    _run(lambda: repository.delete(location_id))
