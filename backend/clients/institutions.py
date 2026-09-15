import builtins
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from clients.json_store import (
    InvalidResourceNameError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
    atomic_write_json,
    clean_resource_name,
    ensure_unique_name,
    normalized_resource_name,
    read_json,
)
from models.institutions import Institution

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_institutions_path() -> Path:
    override = os.environ.get("INSTITUTIONS_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "institutions.json"


class InstitutionRepository:
    def __init__(self, path: Path, participants_path: Path | None = None) -> None:
        self.path = path
        self.participants_path = participants_path or path.parent / "participants.json"

    def list(self) -> builtins.list[dict[str, Any]]:
        return deepcopy(self._load_catalog()["institutions"])

    def get(self, institution_id: str) -> dict[str, Any]:
        institution = self._find(self._load_catalog()["institutions"], institution_id)
        return deepcopy(institution)

    def create(self, name: str, state: str, city: str, description: str | None) -> dict[str, Any]:
        catalog = self._load_catalog()
        institution = self._normalized_record(
            f"institution-{catalog['nextId']:03d}", name, state, city, description
        )
        ensure_unique_name(catalog["institutions"], institution["name"], "instituição")
        catalog["institutions"].append(institution)
        catalog["nextId"] += 1
        self._persist_catalog(catalog)
        return deepcopy(institution)

    def update(
        self,
        institution_id: str,
        name: str,
        state: str,
        city: str,
        description: str | None,
    ) -> dict[str, Any]:
        catalog = self._load_catalog()
        self._find(catalog["institutions"], institution_id)
        institution = self._normalized_record(institution_id, name, state, city, description)
        ensure_unique_name(
            catalog["institutions"], institution["name"], "instituição", institution_id
        )
        catalog["institutions"] = [
            institution if item["id"] == institution_id else item
            for item in catalog["institutions"]
        ]
        self._persist_catalog(catalog)
        return deepcopy(institution)

    def delete(self, institution_id: str) -> None:
        catalog = self._load_catalog()
        self._find(catalog["institutions"], institution_id)
        try:
            from clients.participants import ParticipantRepository

            participants = ParticipantRepository(self.participants_path, self.path)._load()
        except (OSError, ValueError, TypeError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de participantes") from error
        except ResourceNotFoundError as error:
            raise PersistenceError("Catálogo de participantes inválido") from error
        if participants:
            references = [
                item["id"]
                for item in participants["participants"]
                if item["institutionId"] == institution_id
            ]
            if references:
                raise ResourceInUseError("Instituição", institution_id, references)
        catalog["institutions"] = [
            item for item in catalog["institutions"] if item["id"] != institution_id
        ]
        self._persist_catalog(catalog)

    def _load_catalog(self) -> dict[str, Any]:
        try:
            payload = read_json(self.path)
        except (OSError, ValueError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de instituições") from error
        return self._validate_catalog(payload)

    def _validate_catalog(self, payload: dict[str, Any]) -> dict[str, Any]:
        if set(payload) != {"nextId", "institutions"}:
            raise ValueError("Catálogo de instituições inválido")
        if type(payload["nextId"]) is not int or payload["nextId"] < 1:
            raise ValueError("Catálogo de instituições inválido")
        institutions = payload.get("institutions")
        if not isinstance(institutions, list):
            raise ValueError("Catálogo de instituições inválido")
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for item in institutions:
            if not isinstance(item, dict):
                raise ValueError("Catálogo de instituições inválido")
            if set(item) != {"id", "name", "state", "city", "description"}:
                raise ValueError("Catálogo de instituições inválido")
            try:
                normalized = self._normalized_record(
                    item.get("id"),
                    item.get("name"),
                    item.get("state"),
                    item.get("city"),
                    item.get("description"),
                )
            except TypeError, ValueError:
                raise ValueError("Catálogo de instituições inválido") from None
            if (
                normalized["id"] in seen_ids
                or normalized_resource_name(normalized["name"]) in seen_names
            ):
                raise ValueError("Catálogo de instituições inválido")
            seen_ids.add(normalized["id"])
            seen_names.add(normalized_resource_name(normalized["name"]))
        return payload

    def _normalized_record(
        self, institution_id: str, name: str, state: str, city: str, description: str | None
    ) -> dict[str, Any]:
        if not isinstance(institution_id, str):
            raise ValueError("ID inválido")
        values = {"name": name, "state": state, "city": city}
        for field, value in values.items():
            if not isinstance(value, str):
                raise InvalidResourceNameError("instituição")
            values[field] = clean_resource_name(value, field)
        if description is not None and not isinstance(description, str):
            raise ValueError("Descrição inválida")
        cleaned_description = (
            clean_resource_name(description, "descrição")
            if description and description.strip()
            else None
        )
        record = {"id": institution_id, **values, "description": cleaned_description}
        Institution.model_validate(record)
        return record

    def _find(
        self, institutions: builtins.list[dict[str, Any]], institution_id: str
    ) -> dict[str, Any]:
        for institution in institutions:
            if institution["id"] == institution_id:
                return institution
        raise ResourceNotFoundError("Instituição", institution_id)

    def _persist_catalog(self, catalog: dict[str, Any]) -> None:
        self._validate_catalog(catalog)
        try:
            atomic_write_json(self.path, catalog)
        except OSError as error:
            raise PersistenceError(
                "Não foi possível persistir o catálogo de instituições"
            ) from error
