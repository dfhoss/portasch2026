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
from models.schedule import ScheduleDocument, slugify_id

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_knowledge_axes_path() -> Path:
    override = os.environ.get("KNOWLEDGE_AXES_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "knowledge_axes.json"


class KnowledgeAxisRepository:
    def __init__(self, path: Path, schedule_path: Path) -> None:
        self.path = path
        self.schedule_path = schedule_path

    def list(self) -> builtins.list[dict]:
        return deepcopy(self._load_catalog()["knowledgeAxes"])

    def create(self, name: str) -> dict:
        catalog = self._load_catalog()
        cleaned_name = clean_resource_name(name, "eixo de conhecimento")
        axes = catalog["knowledgeAxes"]
        ensure_unique_name(axes, cleaned_name, "eixo de conhecimento")
        base_id = slugify_id(cleaned_name)
        if not base_id:
            raise InvalidResourceNameError("eixo de conhecimento")
        used_ids = {axis["id"] for axis in axes}
        axis_id = base_id
        suffix = 2
        while axis_id in used_ids:
            axis_id = f"{base_id}-{suffix}"
            suffix += 1
        axis = {"id": axis_id, "name": cleaned_name}
        axes.append(axis)
        axes.sort(key=lambda item: normalized_resource_name(item["name"]))
        self._persist_catalog(catalog)
        return deepcopy(axis)

    def rename(self, axis_id: str, name: str) -> dict:
        catalog = self._load_catalog()
        axis = self._find(catalog["knowledgeAxes"], axis_id)
        cleaned_name = clean_resource_name(name, "eixo de conhecimento")
        ensure_unique_name(
            catalog["knowledgeAxes"],
            cleaned_name,
            "eixo de conhecimento",
            axis_id,
        )
        axis["name"] = cleaned_name
        catalog["knowledgeAxes"].sort(key=lambda item: normalized_resource_name(item["name"]))
        self._persist_catalog(catalog)
        return deepcopy(axis)

    def delete(self, axis_id: str) -> None:
        catalog = self._load_catalog()
        self._find(catalog["knowledgeAxes"], axis_id)
        schedule = ScheduleDocument.model_validate(read_json(self.schedule_path))
        in_use, references = _axis_references(schedule, axis_id)
        if in_use:
            raise ResourceInUseError("Eixo de conhecimento", axis_id, references)
        catalog["knowledgeAxes"] = [
            item for item in catalog["knowledgeAxes"] if item["id"] != axis_id
        ]
        self._persist_catalog(catalog)

    def _load_catalog(self) -> dict[str, Any]:
        return self._validate_catalog(read_json(self.path))

    def _validate_catalog(self, payload: dict[str, Any]) -> dict[str, Any]:
        axes = payload.get("knowledgeAxes")
        if not isinstance(axes, list):
            raise ValueError("Catálogo de eixos de conhecimento inválido")
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for item in axes:
            if not isinstance(item, dict):
                raise ValueError("Catálogo de eixos de conhecimento inválido")
            axis_id = item.get("id")
            name = item.get("name")
            if (
                not isinstance(axis_id, str)
                or not axis_id
                or not isinstance(name, str)
                or not name.strip()
            ):
                raise ValueError("Catálogo de eixos de conhecimento inválido")
            normalized = normalized_resource_name(name)
            if axis_id in seen_ids or normalized in seen_names:
                raise ValueError("Catálogo de eixos de conhecimento inválido")
            seen_ids.add(axis_id)
            seen_names.add(normalized)
        return payload

    def _find(self, axes: builtins.list[dict], axis_id: str) -> dict:
        for axis in axes:
            if axis["id"] == axis_id:
                return axis
        raise ResourceNotFoundError("Eixo de conhecimento", axis_id)

    def _persist_catalog(self, catalog: dict) -> None:
        self._validate_catalog(catalog)
        try:
            atomic_write_json(self.path, catalog)
        except OSError as error:
            raise PersistenceError(
                "Não foi possível persistir o catálogo de eixos de conhecimento"
            ) from error


def _axis_references(schedule: ScheduleDocument, axis_id: str) -> tuple[bool, list[str]]:
    in_use = False
    references: list[str] = []
    for section in schedule.sections:
        for group in section.groups:
            if group.knowledge_axis != axis_id:
                continue
            in_use = True
            for activity in group.items:
                if activity.title not in references:
                    references.append(activity.title)
    return in_use, references
