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
    category: str = Field(
        default="outros", pattern="^(blocos|laboratorios|estacionamentos|outros)$"
    )
    group_id: str | None = Field(default=None, alias="groupId")
    room_number: str = Field(default="", alias="roomNumber", max_length=80)
    description: str | None = Field(default=None, max_length=500)

    model_config = {"populate_by_name": True}


class LocationResponse(BaseModel):
    id: str
    name: str
    category: str
    room_number: str = Field(alias="roomNumber")
    description: str | None
    group_id: str | None = Field(alias="groupId")
    group_name: str = Field(alias="groupName")

    model_config = {"populate_by_name": True}


class LocationGroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(pattern="^(blocos|laboratorios|estacionamentos|outros)$")


class LocationGroupResponse(BaseModel):
    id: str
    name: str
    category: str


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


@router.get("/groups", response_model=list[LocationGroupResponse])
def list_location_groups(_: CurrentTokenData, repository: LocationRepo) -> list[dict]:
    return _run(repository.list_groups)


@router.post("/groups", status_code=status.HTTP_201_CREATED, response_model=LocationGroupResponse)
def create_location_group(
    payload: LocationGroupInput, _: CurrentTokenData, repository: LocationRepo
) -> dict:
    return _run(lambda: repository.create_group(payload.name, payload.category))


@router.put("/groups/{group_id}", response_model=LocationGroupResponse)
def rename_location_group(
    group_id: str,
    payload: LocationGroupInput,
    _: CurrentTokenData,
    repository: LocationRepo,
) -> dict:
    return _run(lambda: repository.rename_group(group_id, payload.name, payload.category))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocationResponse)
def create_location(payload: LocationInput, _: CurrentTokenData, repository: LocationRepo) -> dict:
    return _run(
        lambda: repository.create(
            payload.name,
            payload.category,
            payload.group_id,
            payload.room_number,
            payload.description,
        )
    )


@router.put("/{location_id}", response_model=LocationResponse)
def rename_location(
    location_id: str,
    payload: LocationInput,
    _: CurrentTokenData,
    repository: LocationRepo,
) -> dict:
    return _run(
        lambda: repository.rename(
            location_id,
            payload.name,
            payload.category,
            payload.group_id,
            payload.room_number,
            payload.description,
        )
    )


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: str, _: CurrentTokenData, repository: LocationRepo) -> None:
    _run(lambda: repository.delete(location_id))
