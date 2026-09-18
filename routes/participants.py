from collections.abc import Callable
from typing import Annotated, TypeVar

from clients.institutions import get_institutions_path
from clients.json_store import (
    DuplicateParticipantCpfError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceNotFoundError,
)
from clients.participants import ParticipantRepository, get_participants_path
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

router = APIRouter(prefix="/participants", tags=["participants"])


class ParticipantInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cpf: str
    email: str = Field(min_length=1, max_length=254)
    institution_id: str = Field(alias="institutionId", min_length=1)
    model_config = {"populate_by_name": True}


class ParticipantResponse(BaseModel):
    id: str
    name: str
    cpf: str
    email: str
    institution_id: str = Field(alias="institutionId")
    model_config = {"populate_by_name": True}


class ParticipantListResponse(ParticipantResponse):
    cpf: str


def _mask_cpf(cpf: str) -> str:
    return f"***.***.***-{cpf[-2:]}"


def get_participant_repository() -> ParticipantRepository:
    return ParticipantRepository(get_participants_path(), get_institutions_path())


Repo = Annotated[ParticipantRepository, Depends(get_participant_repository)]
T = TypeVar("T")


def _run(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except ResourceNotFoundError as error:
        raise _error(404, str(error)) from error
    except DuplicateParticipantCpfError as error:
        raise _error(409, str(error)) from error
    except (InvalidResourceNameError, ValueError, ValidationError) as error:
        raise _error(422, str(error)) from error
    except PersistenceError as error:
        raise _error(500, "Não foi possível salvar as alterações") from error


def _error(code: int, message: str) -> HTTPException:
    return HTTPException(code, detail={"message": message, "references": []})


@router.get("", response_model=list[ParticipantListResponse])
def list_participants(_: CurrentTokenData, repository: Repo):
    return _run(lambda: [{**item, "cpf": _mask_cpf(item["cpf"])} for item in repository.list()])


@router.get("/{participant_id}", response_model=ParticipantResponse)
def get_participant(participant_id: str, _: CurrentTokenData, repository: Repo):
    return _run(lambda: repository.get(participant_id))


@router.post("", status_code=201, response_model=ParticipantResponse)
def create_participant(payload: ParticipantInput, _: CurrentTokenData, repository: Repo):
    return _run(
        lambda: repository.create(payload.name, payload.cpf, payload.email, payload.institution_id)
    )


@router.put("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    participant_id: str, payload: ParticipantInput, _: CurrentTokenData, repository: Repo
):
    return _run(
        lambda: repository.update(
            participant_id, payload.name, payload.cpf, payload.email, payload.institution_id
        )
    )


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(participant_id: str, _: CurrentTokenData, repository: Repo) -> None:
    _run(lambda: repository.delete(participant_id))
