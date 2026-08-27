from collections.abc import Callable
from typing import Annotated, TypeVar

from clients.json_store import (
    DuplicateResourceNameError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
)
from clients.knowledge_axes import KnowledgeAxisRepository, get_knowledge_axes_path
from clients.schedule import get_schedule_path
from dependencies import CurrentTokenData
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/api/knowledge-axes", tags=["admin-knowledge-axes"])


class KnowledgeAxisInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class KnowledgeAxisResponse(BaseModel):
    id: str
    name: str


def get_knowledge_axis_repository() -> KnowledgeAxisRepository:
    return KnowledgeAxisRepository(get_knowledge_axes_path(), get_schedule_path())


KnowledgeAxisRepo = Annotated[KnowledgeAxisRepository, Depends(get_knowledge_axis_repository)]
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


@router.get("", response_model=list[KnowledgeAxisResponse])
def list_knowledge_axes(_: CurrentTokenData, repository: KnowledgeAxisRepo) -> list[dict]:
    return _run(repository.list)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=KnowledgeAxisResponse)
def create_knowledge_axis(
    payload: KnowledgeAxisInput,
    _: CurrentTokenData,
    repository: KnowledgeAxisRepo,
) -> dict:
    return _run(lambda: repository.create(payload.name.strip()))


@router.put("/{axis_id}", response_model=KnowledgeAxisResponse)
def rename_knowledge_axis(
    axis_id: str,
    payload: KnowledgeAxisInput,
    _: CurrentTokenData,
    repository: KnowledgeAxisRepo,
) -> dict:
    return _run(lambda: repository.rename(axis_id, payload.name.strip()))


@router.delete("/{axis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_axis(axis_id: str, _: CurrentTokenData, repository: KnowledgeAxisRepo) -> None:
    _run(lambda: repository.delete(axis_id))
