from collections.abc import Callable
from typing import Annotated, TypeVar

from clients.institutions import InstitutionRepository, get_institutions_path
from clients.json_store import (
    DuplicateResourceNameError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
)
from clients.participants import get_participants_path
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/institutions", tags=["institutions"])


class InstitutionInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class InstitutionResponse(BaseModel):
    id: str
    name: str
    state: str
    city: str
    description: str | None


def get_institution_repository() -> InstitutionRepository:
    return InstitutionRepository(get_institutions_path(), get_participants_path())


Repo = Annotated[InstitutionRepository, Depends(get_institution_repository)]
T = TypeVar("T")


def _run(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except ResourceNotFoundError as error:
        raise _error(404, str(error)) from error
    except (DuplicateResourceNameError, ResourceInUseError) as error:
        raise _error(409, str(error), getattr(error, "references", [])) from error
    except (InvalidResourceNameError, ValueError) as error:
        raise _error(422, str(error)) from error
    except PersistenceError as error:
        raise _error(500, "Não foi possível salvar as alterações") from error


def _error(code: int, message: str, references: list[str] | None = None) -> HTTPException:
    return HTTPException(code, detail={"message": message, "references": references or []})


@router.get("", response_model=list[InstitutionResponse])
def list_institutions(_: CurrentTokenData, repository: Repo):
    return _run(repository.list)


@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: str, _: CurrentTokenData, repository: Repo):
    return _run(lambda: repository.get(institution_id))


@router.post("", status_code=201, response_model=InstitutionResponse)
def create_institution(payload: InstitutionInput, _: CurrentTokenData, repository: Repo):
    return _run(
        lambda: repository.create(payload.name, payload.state, payload.city, payload.description)
    )


@router.put("/{institution_id}", response_model=InstitutionResponse)
def update_institution(
    institution_id: str, payload: InstitutionInput, _: CurrentTokenData, repository: Repo
):
    return _run(
        lambda: repository.update(
            institution_id, payload.name, payload.state, payload.city, payload.description
        )
    )


@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_institution(institution_id: str, _: CurrentTokenData, repository: Repo) -> None:
    _run(lambda: repository.delete(institution_id))
