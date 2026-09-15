import builtins
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from clients.json_store import (
    DuplicateParticipantCpfError,
    PersistenceError,
    ResourceNotFoundError,
    atomic_write_json,
    clean_resource_name,
    read_json,
)
from models.participants import Participant

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_participants_path() -> Path:
    override = os.environ.get("PARTICIPANTS_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "participants.json"


def normalize_cpf(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("CPF inválido")
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError("CPF inválido")
    numbers = [int(digit) for digit in digits]
    for length in (9, 10):
        check = sum(number * (length + 1 - index) for index, number in enumerate(numbers[:length]))
        digit = (check * 10) % 11 % 10
        if numbers[length] != digit:
            raise ValueError("CPF inválido")
    return digits


class ParticipantRepository:
    def __init__(self, path: Path, institutions_path: Path) -> None:
        self.path = path
        self.institutions_path = institutions_path

    def list(self) -> builtins.list[dict[str, Any]]:
        return deepcopy(self._load()["participants"])

    def get(self, participant_id: str) -> dict[str, Any]:
        return deepcopy(self._find(self._load()["participants"], participant_id))

    def create(self, name: str, cpf: str, email: str, institution_id: str) -> dict[str, Any]:
        catalog = self._load()
        self._ensure_institution(institution_id)
        record = self._record(
            f"participant-{catalog['nextId']:03d}", name, cpf, email, institution_id
        )
        self._ensure_unique(catalog["participants"], record["cpf"])
        catalog["participants"].append(record)
        catalog["nextId"] += 1
        self._persist(catalog)
        return deepcopy(record)

    def update(
        self, participant_id: str, name: str, cpf: str, email: str, institution_id: str
    ) -> dict[str, Any]:
        catalog = self._load()
        self._find(catalog["participants"], participant_id)
        self._ensure_institution(institution_id)
        record = self._record(participant_id, name, cpf, email, institution_id)
        self._ensure_unique(catalog["participants"], record["cpf"], participant_id)
        catalog["participants"] = [
            record if item["id"] == participant_id else item for item in catalog["participants"]
        ]
        self._persist(catalog)
        return deepcopy(record)

    def delete(self, participant_id: str) -> None:
        catalog = self._load()
        self._find(catalog["participants"], participant_id)
        catalog["participants"] = [
            item for item in catalog["participants"] if item["id"] != participant_id
        ]
        self._persist(catalog)

    def _load(self) -> dict[str, Any]:
        try:
            payload = read_json(self.path)
        except (OSError, ValueError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de participantes") from error
        if (
            set(payload) != {"nextId", "participants"}
            or type(payload["nextId"]) is not int
            or payload["nextId"] < 1
            or not isinstance(payload["participants"], list)
        ):
            raise ValueError("Catálogo de participantes inválido")
        for item in payload["participants"]:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "name",
                "cpf",
                "email",
                "institutionId",
            }:
                raise ValueError("Catálogo de participantes inválido")
            Participant.model_validate(item)
        return payload

    def _ensure_institution(self, institution_id: str) -> None:
        try:
            catalog = read_json(self.institutions_path)
            if set(catalog) != {"nextId", "institutions"} or not isinstance(
                catalog["institutions"], list
            ):
                raise ValueError
        except (OSError, ValueError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de instituições") from error
        if not any(item.get("id") == institution_id for item in catalog["institutions"]):
            raise ResourceNotFoundError("Instituição", institution_id)

    @staticmethod
    def _record(
        identifier: str, name: str, cpf: str, email: str, institution_id: str
    ) -> dict[str, str]:
        record = {
            "id": identifier,
            "name": clean_resource_name(name, "participante"),
            "cpf": normalize_cpf(cpf),
            "email": clean_resource_name(email, "e-mail"),
            "institutionId": institution_id,
        }
        Participant.model_validate(record)
        return record

    @staticmethod
    def _ensure_unique(
        records: builtins.list[dict[str, Any]], cpf: str, excluded_id: str | None = None
    ) -> None:
        if any(item["cpf"] == cpf and item["id"] != excluded_id for item in records):
            raise DuplicateParticipantCpfError("Já existe participante com este CPF")

    @staticmethod
    def _find(records: builtins.list[dict[str, Any]], identifier: str) -> dict[str, Any]:
        for item in records:
            if item["id"] == identifier:
                return item
        raise ResourceNotFoundError("Participante", identifier)

    def _persist(self, catalog: dict[str, Any]) -> None:
        try:
            atomic_write_json(self.path, catalog)
        except OSError as error:
            raise PersistenceError(
                "Não foi possível persistir o catálogo de participantes"
            ) from error
