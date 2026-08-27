import builtins
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from clients.json_store import (
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
    atomic_write_json,
    clean_resource_name,
    ensure_unique_name,
    normalized_resource_name,
    read_json,
)
from clients.schedule import save_schedule
from loguru import logger
from models.schedule import ScheduleDocument

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_locations_path() -> Path:
    override = os.environ.get("LOCATIONS_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "locations.json"


class LocationRepository:
    def __init__(self, path: Path, schedule_path: Path) -> None:
        self.path = path
        self.schedule_path = schedule_path

    def list(self) -> builtins.list[dict]:
        return deepcopy(self._load_catalog()["locations"])

    def create(self, name: str) -> dict:
        catalog = self._load_catalog()
        cleaned_name = clean_resource_name(name, "local")
        ensure_unique_name(catalog["locations"], cleaned_name, "local")
        location = {"id": f"loc-{catalog['nextId']:03d}", "name": cleaned_name}
        catalog["locations"].append(location)
        catalog["locations"].sort(key=lambda item: normalized_resource_name(item["name"]))
        catalog["nextId"] += 1
        self._persist_catalog(catalog)
        return deepcopy(location)

    def rename(self, location_id: str, name: str) -> dict:
        original_catalog = self._load_catalog()
        catalog = deepcopy(original_catalog)
        location = self._find(catalog["locations"], location_id)
        cleaned_name = clean_resource_name(name, "local")
        ensure_unique_name(catalog["locations"], cleaned_name, "local", location_id)

        original_name = location["name"]
        location["name"] = cleaned_name
        catalog["locations"].sort(key=lambda item: normalized_resource_name(item["name"]))
        self._validate_catalog(catalog)

        schedule_payload = read_json(self.schedule_path)
        ScheduleDocument.model_validate(schedule_payload)
        for section in schedule_payload["sections"]:
            for group in section["groups"]:
                for activity in group["items"]:
                    for session in activity.get("sessions", []):
                        if session.get("location") == original_name:
                            session["location"] = cleaned_name
        propagated_schedule = ScheduleDocument.model_validate(schedule_payload)

        try:
            atomic_write_json(self.path, catalog)
        except OSError as error:
            raise PersistenceError("Não foi possível persistir o catálogo de locais") from error

        try:
            save_schedule(propagated_schedule, self.schedule_path)
        except OSError as schedule_error:
            try:
                atomic_write_json(self.path, original_catalog)
            except OSError as rollback_error:
                logger.critical(
                    "Falha ao restaurar o catálogo de locais após erro na agenda: {}",
                    rollback_error,
                )
                raise PersistenceError(
                    "Não foi possível persistir a agenda nem restaurar o catálogo de locais"
                ) from rollback_error
            raise PersistenceError(
                "Não foi possível persistir a agenda; o catálogo de locais foi restaurado"
            ) from schedule_error
        return deepcopy(location)

    def delete(self, location_id: str) -> None:
        catalog = self._load_catalog()
        location = self._find(catalog["locations"], location_id)
        schedule = ScheduleDocument.model_validate(read_json(self.schedule_path))
        references = _location_references(schedule, location["name"])
        if references:
            raise ResourceInUseError("local", location_id, references)
        catalog["locations"] = [item for item in catalog["locations"] if item["id"] != location_id]
        self._persist_catalog(catalog)

    def _load_catalog(self) -> dict[str, Any]:
        return self._validate_catalog(read_json(self.path))

    def _validate_catalog(self, payload: dict[str, Any]) -> dict[str, Any]:
        next_id = payload.get("nextId")
        locations = payload.get("locations")
        if not isinstance(next_id, int) or next_id < 1 or not isinstance(locations, list):
            raise ValueError("Catálogo de locais inválido")
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for item in locations:
            if not isinstance(item, dict):
                raise ValueError("Catálogo de locais inválido")
            location_id = item.get("id")
            name = item.get("name")
            if not isinstance(location_id, str) or not isinstance(name, str) or not name.strip():
                raise ValueError("Catálogo de locais inválido")
            normalized = normalized_resource_name(name)
            if location_id in seen_ids or normalized in seen_names:
                raise ValueError("Catálogo de locais inválido")
            seen_ids.add(location_id)
            seen_names.add(normalized)
        return payload

    def _find(self, locations: builtins.list[dict], location_id: str) -> dict:
        for location in locations:
            if location["id"] == location_id:
                return location
        raise ResourceNotFoundError("Local", location_id)

    def _persist_catalog(self, catalog: dict) -> None:
        self._validate_catalog(catalog)
        try:
            atomic_write_json(self.path, catalog)
        except OSError as error:
            raise PersistenceError("Não foi possível persistir o catálogo de locais") from error


def _location_references(schedule: ScheduleDocument, location_name: str) -> list[str]:
    references: list[str] = []
    for section in schedule.sections:
        for group in section.groups:
            for activity in group.items:
                if any(session.location == location_name for session in activity.sessions):
                    if activity.title not in references:
                        references.append(activity.title)
    return references
