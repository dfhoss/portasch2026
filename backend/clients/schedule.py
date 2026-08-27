import os
from pathlib import Path

from clients.json_store import (
    InvalidScheduleReferenceError,
    PersistenceError,
    atomic_write_json,
    read_json,
)
from models.schedule import ScheduleDocument

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_schedule_path() -> Path:
    override = os.environ.get("SCHEDULE_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "schedule.json"


def load_schedule(path: Path) -> ScheduleDocument:
    return ScheduleDocument.model_validate(read_json(path))


def save_schedule(document: ScheduleDocument, path: Path) -> None:
    atomic_write_json(
        path,
        document.model_dump(by_alias=True, exclude_unset=True, mode="json"),
    )


def replace_schedule(document: ScheduleDocument, path: Path | None = None) -> ScheduleDocument:
    from clients.knowledge_axes import get_knowledge_axes_path
    from clients.locations import get_locations_path

    location_payload = read_json(get_locations_path())
    axes_payload = read_json(get_knowledge_axes_path())
    registered_locations = {
        item["name"]
        for item in location_payload.get("locations", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    registered_axes = {
        item["id"]
        for item in axes_payload.get("knowledgeAxes", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    used_locations = {
        session.location
        for section in document.sections
        for group in section.groups
        for activity in group.items
        for session in activity.sessions
        if session.location is not None
    }
    used_axes = {
        group.knowledge_axis
        for section in document.sections
        for group in section.groups
        if group.knowledge_axis is not None
    }
    unknown_locations = sorted(used_locations - registered_locations)
    unknown_axes = sorted(used_axes - registered_axes)
    if unknown_locations or unknown_axes:
        raise InvalidScheduleReferenceError(unknown_locations, unknown_axes)

    destination = path or get_schedule_path()
    try:
        save_schedule(document, destination)
    except OSError as error:
        raise PersistenceError("Não foi possível persistir a agenda") from error
    return document
