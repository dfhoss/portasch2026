import json
import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


class ResourceNotFoundError(LookupError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} não encontrado: {resource_id}")
        self.resource = resource
        self.resource_id = resource_id


class DuplicateResourceNameError(ValueError):
    def __init__(self, resource: str, name: str) -> None:
        super().__init__(f"Já existe {resource} com o nome: {name}")
        self.resource = resource
        self.name = name


class InvalidResourceNameError(ValueError):
    def __init__(self, resource: str) -> None:
        super().__init__(f"O nome de {resource} não pode ficar vazio")
        self.resource = resource


class ResourceInUseError(RuntimeError):
    def __init__(self, resource: str, resource_id: str, references: list[str]) -> None:
        super().__init__(f"{resource} está em uso: {resource_id}")
        self.resource = resource
        self.resource_id = resource_id
        self.references = references


class InvalidScheduleReferenceError(ValueError):
    def __init__(self, locations: list[str], knowledge_axes: list[str]) -> None:
        details = []
        if locations:
            details.append(f"locais: {', '.join(locations)}")
        if knowledge_axes:
            details.append(f"eixos de conhecimento: {', '.join(knowledge_axes)}")
        super().__init__(f"Referências inválidas na agenda ({'; '.join(details)})")
        self.locations = locations
        self.knowledge_axes = knowledge_axes


class PersistenceError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"A raiz de {path} deve ser um objeto JSON")
    return payload


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def clean_resource_name(name: str, resource: str) -> str:
    cleaned = " ".join(unicodedata.normalize("NFC", name).split())
    if not cleaned:
        raise InvalidResourceNameError(resource)
    return cleaned


def normalized_resource_name(name: str) -> str:
    cleaned = " ".join(unicodedata.normalize("NFKC", name).split())
    return cleaned.casefold()


def ensure_unique_name(
    records: list[dict[str, Any]],
    name: str,
    resource: str,
    excluded_id: str | None = None,
) -> None:
    normalized = normalized_resource_name(name)
    if any(
        record.get("id") != excluded_id
        and isinstance(record.get("name"), str)
        and normalized_resource_name(record["name"]) == normalized
        for record in records
    ):
        raise DuplicateResourceNameError(resource, name)
