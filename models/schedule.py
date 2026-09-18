import re
import unicodedata
from copy import deepcopy
from datetime import date, time
from typing import Any, Self
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


def slugify_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


class Session(BaseModel):
    start_time: time = Field(alias="startTime")
    end_time: time = Field(alias="endTime")
    locations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_location(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        migrated = dict(value)
        if "locations" not in migrated and "location" in migrated:
            migrated["locations"] = [migrated.pop("location")] if migrated["location"] else []
        return migrated

    @field_validator("locations")
    @classmethod
    def validate_locations(cls, value: list[str]) -> list[str]:
        if any(not isinstance(location, str) or not location.strip() for location in value):
            raise ValueError("Os locais devem ser textos não vazios")
        if len(set(value)) != len(value):
            raise ValueError("Uma sessão não pode repetir o mesmo local")
        return [location.strip() for location in value]

    @property
    def location(self) -> str | None:
        """Compatibility accessor for consumers that display one location."""
        return self.locations[0] if self.locations else None

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return value.strftime("%H:%M")

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if any(value.second or value.microsecond for value in (self.start_time, self.end_time)):
            raise ValueError("Os horários devem ter precisão de minutos")
        if self.end_time <= self.start_time:
            raise ValueError("O horário final deve ser posterior ao inicial")
        return self


class Activity(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    sessions: list[Session] = Field(default_factory=list)
    link: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("link")
    @classmethod
    def validate_link(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        candidate = (
            value if re.match(r"^[a-z][a-z\d+.-]*://", value, re.IGNORECASE) else f"https://{value}"
        )
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("O link deve conter um domínio válido")
        if any(not label for label in parsed.hostname.split(".")):
            raise ValueError("O link deve conter um domínio válido")
        return value.strip()


class ScheduleGroup(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    knowledge_axis: str | None = Field(default=None, alias="knowledgeAxis")
    items: list[Activity]

    model_config = ConfigDict(populate_by_name=True)


class Section(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    groups: list[ScheduleGroup]

    model_config = ConfigDict(populate_by_name=True)


class ScheduleDocument(BaseModel):
    version: int = Field(ge=1)
    event_date: date = Field(alias="eventDate")
    sections: list[Section]

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def canonicalize_and_validate_ids(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        document = deepcopy(value)
        records = list(_id_records(document))
        used_ids: set[str] = set()
        duplicate_ids: set[str] = set()

        for record in records:
            identifier = record.get("id")
            if isinstance(identifier, str) and identifier.strip():
                if identifier in used_ids:
                    duplicate_ids.add(identifier)
                used_ids.add(identifier)

        if duplicate_ids:
            duplicates = ", ".join(sorted(duplicate_ids))
            raise ValueError(f"IDs duplicados no documento: {duplicates}")

        for record in records:
            identifier = record.get("id")
            if identifier is None or (isinstance(identifier, str) and not identifier.strip()):
                title = record.get("title")
                base_id = slugify_id(title) if isinstance(title, str) else ""
                if not base_id:
                    raise ValueError("Não foi possível gerar um ID a partir do título")

                generated_id = base_id
                suffix = 2
                while generated_id in used_ids:
                    generated_id = f"{base_id}-{suffix}"
                    suffix += 1
                record["id"] = generated_id
                used_ids.add(generated_id)

        return document


def _id_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    sections = document.get("sections")
    if not isinstance(sections, list):
        return records

    for section in sections:
        if not isinstance(section, dict):
            continue
        records.append(section)
        groups = section.get("groups")
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            records.append(group)
            items = group.get("items")
            if not isinstance(items, list):
                continue
            records.extend(item for item in items if isinstance(item, dict))
    return records
