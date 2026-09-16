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
    value = value.strip()
    if len(value) == 11 and all("0" <= character <= "9" for character in value):
        digits = value
    elif len(value) == 14 and all(
        (index in (3, 7) and character == ".")
        or (index == 11 and character == "-")
        or (index not in (3, 7, 11) and "0" <= character <= "9")
        for index, character in enumerate(value)
    ):
        digits = value.replace(".", "").replace("-", "")
    else:
        raise ValueError("CPF inválido")
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
        if not isinstance(payload, dict) or (
            set(payload) != {"nextId", "participants"}
            or type(payload["nextId"]) is not int
            or payload["nextId"] < 1
            or not isinstance(payload["participants"], list)
        ):
            raise PersistenceError("Catálogo de participantes inválido")
        seen_ids: set[str] = set()
        seen_cpfs: set[str] = set()
        for item in payload["participants"]:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "name",
                "cpf",
                "email",
                "institutionId",
            }:
                raise PersistenceError("Catálogo de participantes inválido")
            try:
                if item["id"] in seen_ids:
                    raise ValueError
                cpf = normalize_cpf(item["cpf"])
                if cpf != item["cpf"] or cpf in seen_cpfs:
                    raise ValueError
                Participant.model_validate(item)
            except TypeError, ValueError:
                raise PersistenceError("Catálogo de participantes inválido") from None
            seen_ids.add(item["id"])
            seen_cpfs.add(cpf)
        self._validate_institution_catalog()
        institution_ids = {item["id"] for item in self._load_institutions()["institutions"]}
        if any(item["institutionId"] not in institution_ids for item in payload["participants"]):
            raise PersistenceError("Catálogo de participantes inválido")
        return payload

    def _ensure_institution(self, institution_id: str) -> None:
        try:
            catalog = self._load_institutions()
        except (OSError, ValueError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de instituições") from error
        if not any(item["id"] == institution_id for item in catalog["institutions"]):
            raise ResourceNotFoundError("Instituição", institution_id)

    def _load_institutions(self) -> dict[str, Any]:
        from clients.institutions import InstitutionRepository

        try:
            payload = read_json(self.institutions_path)
            return InstitutionRepository(self.institutions_path)._validate_catalog(payload)
        except (OSError, ValueError, TypeError) as error:
            raise PersistenceError("Não foi possível ler o catálogo de instituições") from error

    def _validate_institution_catalog(self) -> None:
        self._load_institutions()

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
