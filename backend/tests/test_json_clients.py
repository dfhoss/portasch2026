import json
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
from clients.json_store import (
    DuplicateResourceNameError,
    InvalidResourceNameError,
    InvalidScheduleReferenceError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
    atomic_write_json,
    read_json,
)
from clients.knowledge_axes import KnowledgeAxisRepository, get_knowledge_axes_path
from clients.locations import LocationRepository, get_locations_path
from clients.schedule import get_schedule_path, load_schedule, replace_schedule, save_schedule
from loguru import logger
from models.schedule import ScheduleDocument

AXIS_PAIRS = [
    ("geral", "Geral"),
    (
        "agricultura-silvicultura-pesca-e-veterinaria",
        "Agricultura, silvicultura, pesca e veterinária",
    ),
    ("administracao-negocios-e-direito", "Administração, negócios e direito"),
    (
        "computacao-e-tecnologia-da-informacao",
        "Computação e tecnologia da informação",
    ),
    ("educacao", "Educação"),
    ("artes-e-humanidades", "Artes e humanidades"),
    ("engenharia-industria-e-construcao", "Engenharia, indústria e construção"),
    (
        "ciencias-naturais-matematica-e-estatistica",
        "Ciências naturais, matemática e estatística",
    ),
    ("saude-e-bem-estar", "Saúde e bem-estar"),
    (
        "ciencias-sociais-comunicacao-e-informacao",
        "Ciências sociais, comunicação e informação",
    ),
]

ENGLISH_AXIS_IDS = {
    "agriculture-forestry-fisheries-and-veterinary",
    "arts-and-humanities",
    "business-administration-and-law",
    "computing-and-ict",
    "education",
    "engineering-manufacturing-and-construction",
    "general",
    "health-and-welfare",
    "natural-sciences-mathematics-and-statistics",
    "social-sciences-communication-and-information",
}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def empty_schedule() -> dict:
    return {"version": 1, "eventDate": "2026-10-26", "sections": []}


def referenced_schedule(location: str | None = "Auditório", axis: str | None = "educacao") -> dict:
    return {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [
            {
                "id": "secao",
                "title": "Seção",
                "groups": [
                    {
                        "id": "grupo",
                        "title": "Grupo",
                        "knowledgeAxis": axis,
                        "items": [
                            {
                                "id": "atividade",
                                "title": "Atividade referenciada",
                                "sessions": [
                                    {
                                        "startTime": "09:00",
                                        "endTime": "10:00",
                                        "location": location,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def catalog_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    locations_path = tmp_path / "locations.json"
    axes_path = tmp_path / "knowledge_axes.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        locations_path,
        {"nextId": 2, "locations": [{"id": "loc-001", "name": "Auditório"}]},
    )
    write_json(
        axes_path,
        {"knowledgeAxes": [{"id": "educacao", "name": "Educação"}]},
    )
    write_json(schedule_path, referenced_schedule())
    return locations_path, axes_path, schedule_path


def test_json_client_interfaces_are_importable():
    """Removing any public persistence interface must make this test fail."""
    assert callable(read_json)
    assert callable(atomic_write_json)
    assert callable(load_schedule)
    assert callable(save_schedule)
    assert LocationRepository is not None
    assert KnowledgeAxisRepository is not None


def test_atomic_write_serializes_utf8_json_with_final_newline(tmp_path: Path):
    """Removing UTF-8 preservation or atomic serialization must make this test fail."""
    path = tmp_path / "data.json"

    atomic_write_json(path, {"value": "São José"})

    assert read_json(path) == {"value": "São José"}
    assert path.read_bytes().endswith(b"\n")
    assert b"S\xc3\xa3o Jos\xc3\xa9" in path.read_bytes()


def test_atomic_write_keeps_original_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Replacing before a complete temp write must make this test fail."""
    path = tmp_path / "data.json"
    write_json(path, {"value": "original"})
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("falha")))

    with pytest.raises(OSError, match="falha"):
        atomic_write_json(path, {"value": "novo"})

    assert read_json(path) == {"value": "original"}
    assert list(tmp_path.glob("*.tmp")) == []


def test_schedule_round_trip_uses_json_aliases(tmp_path: Path):
    """Serializing Python field names instead of JSON aliases must make this test fail."""
    path = tmp_path / "schedule.json"
    document = ScheduleDocument.model_validate(referenced_schedule())

    save_schedule(document, path)

    loaded = load_schedule(path)
    assert loaded == document
    assert read_json(path)["eventDate"] == "2026-10-26"
    assert read_json(path)["sections"][0]["groups"][0]["knowledgeAxis"] == "educacao"


def test_path_getters_are_late_bound_and_defaults_ignore_process_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Caching environment paths or resolving defaults from cwd must make this test fail."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SCHEDULE_PATH", raising=False)
    monkeypatch.delenv("LOCATIONS_PATH", raising=False)
    monkeypatch.delenv("KNOWLEDGE_AXES_PATH", raising=False)

    assert get_schedule_path().name == "schedule.json"
    assert get_schedule_path().parent.name == "db"
    assert get_locations_path().parent.name == "db"
    assert get_knowledge_axes_path().parent.name == "db"
    assert get_schedule_path().parent.parent.name == "backend"

    monkeypatch.setenv("SCHEDULE_PATH", str(tmp_path / "other-schedule.json"))
    monkeypatch.setenv("LOCATIONS_PATH", str(tmp_path / "other-locations.json"))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(tmp_path / "other-axes.json"))
    assert get_schedule_path() == tmp_path / "other-schedule.json"
    assert get_locations_path() == tmp_path / "other-locations.json"
    assert get_knowledge_axes_path() == tmp_path / "other-axes.json"


def test_replace_schedule_validates_all_catalog_references_before_saving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Saving unknown locations or axes must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    locations_path = tmp_path / "locations.json"
    axes_path = tmp_path / "knowledge_axes.json"
    write_json(schedule_path, empty_schedule())
    write_json(locations_path, {"nextId": 1, "locations": []})
    write_json(axes_path, {"knowledgeAxes": []})
    monkeypatch.setenv("LOCATIONS_PATH", str(locations_path))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(axes_path))
    document = ScheduleDocument.model_validate(
        referenced_schedule(location="Sala inexistente", axis="eixo-inexistente")
    )

    with pytest.raises(InvalidScheduleReferenceError) as error:
        replace_schedule(document, schedule_path)

    assert error.value.locations == ["Sala inexistente"]
    assert error.value.knowledge_axes == ["eixo-inexistente"]
    assert read_json(schedule_path) == empty_schedule()


def test_replace_schedule_accepts_null_references_and_returns_canonical_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Treating null references as catalog lookups must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    locations_path = tmp_path / "locations.json"
    axes_path = tmp_path / "knowledge_axes.json"
    write_json(locations_path, {"nextId": 1, "locations": []})
    write_json(axes_path, {"knowledgeAxes": []})
    monkeypatch.setenv("LOCATIONS_PATH", str(locations_path))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(axes_path))
    payload = referenced_schedule(location=None, axis=None)
    payload["sections"][0]["id"] = ""
    payload["sections"][0]["title"] = "Nova seção"
    document = ScheduleDocument.model_validate(payload)

    result = replace_schedule(document, schedule_path)

    assert result.sections[0].id == "nova-secao"
    assert load_schedule(schedule_path) == result


def test_replace_schedule_exposes_atomic_write_failure_as_persistence_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Leaking a filesystem error from the replacement boundary must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    locations_path = tmp_path / "locations.json"
    axes_path = tmp_path / "knowledge_axes.json"
    write_json(schedule_path, empty_schedule())
    write_json(locations_path, {"nextId": 1, "locations": []})
    write_json(axes_path, {"knowledgeAxes": []})
    monkeypatch.setenv("LOCATIONS_PATH", str(locations_path))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(axes_path))
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("disco cheio")))
    document = ScheduleDocument.model_validate(empty_schedule())

    with pytest.raises(PersistenceError, match="agenda"):
        replace_schedule(document, schedule_path)

    assert read_json(schedule_path) == empty_schedule()


def test_location_ids_are_generated_and_not_reused(tmp_path: Path):
    """Deriving IDs from list length must make this test fail after a deletion."""
    path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(path, {"nextId": 3, "locations": [{"id": "loc-002", "name": "Hall"}]})
    write_json(schedule_path, empty_schedule())
    repository = LocationRepository(path, schedule_path)

    created = repository.create("  Auditório  ")

    assert created == {
        "id": "loc-003",
        "name": "Auditório",
        "category": "outros",
        "groupId": None,
        "groupName": "Outros",
        "roomNumber": "",
        "description": None,
    }
    assert [item["name"] for item in repository.list()] == ["Auditório", "Hall"]
    assert read_json(path)["nextId"] == 4


def test_location_group_can_be_updated_without_changing_its_id(tmp_path: Path):
    locations_path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        locations_path,
        {
            "nextId": 2,
            "nextGroupId": 2,
            "groups": [{"id": "group-001", "name": "Bloco D", "category": "blocos"}],
            "locations": [
                {"id": "loc-001", "name": "Sala 1", "category": "blocos", "groupId": "group-001"}
            ],
        },
    )
    write_json(schedule_path, empty_schedule())

    updated = LocationRepository(locations_path, schedule_path).rename_group(
        "group-001", "Laboratório D", "laboratorios"
    )

    assert updated == {"id": "group-001", "name": "Laboratório D", "category": "laboratorios"}
    assert LocationRepository(locations_path, schedule_path).list()[0]["groupId"] == "group-001"


@pytest.mark.parametrize(
    ("repository_name", "duplicate"),
    [("location", "  AUDITÓRIO   CENTRAL  "), ("axis", "  EDUCAÇÃO   ESPECIAL  ")],
)
def test_catalogs_reject_unicode_case_and_whitespace_duplicate_names(
    tmp_path: Path, repository_name: str, duplicate: str
):
    """Comparing only raw display strings must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    write_json(schedule_path, empty_schedule())
    if repository_name == "location":
        path = tmp_path / "locations.json"
        write_json(
            path,
            {"nextId": 2, "locations": [{"id": "loc-001", "name": "Auditório Central"}]},
        )
        repository = LocationRepository(path, schedule_path)
    else:
        path = tmp_path / "axes.json"
        write_json(
            path,
            {"knowledgeAxes": [{"id": "educacao-especial", "name": "Educação Especial"}]},
        )
        repository = KnowledgeAxisRepository(path, schedule_path)

    with pytest.raises(DuplicateResourceNameError):
        repository.create(duplicate)


@pytest.mark.parametrize("repository_name", ["location", "axis"])
def test_catalogs_reject_duplicate_name_on_rename(tmp_path: Path, repository_name: str):
    """Checking duplicates only during creation must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    write_json(schedule_path, empty_schedule())
    if repository_name == "location":
        path = tmp_path / "locations.json"
        write_json(
            path,
            {
                "nextId": 3,
                "locations": [
                    {"id": "loc-001", "name": "Auditório"},
                    {"id": "loc-002", "name": "Hall"},
                ],
            },
        )
        repository = LocationRepository(path, schedule_path)
        resource_id = "loc-002"
    else:
        path = tmp_path / "axes.json"
        write_json(
            path,
            {
                "knowledgeAxes": [
                    {"id": "educacao", "name": "Educação"},
                    {"id": "geral", "name": "Geral"},
                ]
            },
        )
        repository = KnowledgeAxisRepository(path, schedule_path)
        resource_id = "geral"

    with pytest.raises(DuplicateResourceNameError):
        repository.rename(
            resource_id, "  AUDITÓRIO  " if repository_name == "location" else "educação"
        )


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_catalogs_reject_empty_cleaned_names(tmp_path: Path, name: str):
    """Allowing a blank display name must make this test fail."""
    locations_path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(locations_path, {"nextId": 1, "locations": []})
    write_json(schedule_path, empty_schedule())

    with pytest.raises(InvalidResourceNameError):
        LocationRepository(locations_path, schedule_path).create(name)


def test_axis_create_rejects_nonempty_name_that_cannot_produce_slug(tmp_path: Path):
    """Raising a generic ValueError for a non-sluggable axis name must make this test fail."""
    axes_path = tmp_path / "axes.json"
    schedule_path = tmp_path / "schedule.json"
    original_catalog = {"knowledgeAxes": []}
    write_json(axes_path, original_catalog)
    write_json(schedule_path, empty_schedule())

    with pytest.raises(InvalidResourceNameError) as error:
        KnowledgeAxisRepository(axes_path, schedule_path).create("!!!")

    assert error.value.resource == "eixo de conhecimento"
    assert read_json(axes_path) == original_catalog


def test_location_rename_propagates_exact_name_to_every_session(catalog_paths):
    """Updating only the catalog must make this test fail."""
    locations_path, _, schedule_path = catalog_paths
    repository = LocationRepository(locations_path, schedule_path)

    renamed = repository.rename("loc-001", "  Auditório Novo  ")

    assert renamed["id"] == "loc-001"
    assert renamed["name"] == "Auditório Novo"
    schedule = read_json(schedule_path)
    assert schedule["sections"][0]["groups"][0]["items"][0]["sessions"][0]["locations"] == [
        "Auditório Novo"
    ]


def test_location_rename_validates_schedule_before_writing_catalog(tmp_path: Path):
    """Writing the catalog before validating the schedule must make this test fail."""
    locations_path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        locations_path,
        {"nextId": 2, "locations": [{"id": "loc-001", "name": "Auditório"}]},
    )
    invalid_schedule = referenced_schedule()
    invalid_schedule["sections"][0]["groups"][0]["items"][0]["sessions"][0]["endTime"] = "08:00"
    write_json(schedule_path, invalid_schedule)
    original_catalog = locations_path.read_bytes()

    with pytest.raises(ValueError, match="posterior ao inicial"):
        LocationRepository(locations_path, schedule_path).rename("loc-001", "Novo nome")

    assert locations_path.read_bytes() == original_catalog


def test_location_rename_restores_catalog_when_schedule_replace_fails(
    catalog_paths, monkeypatch: pytest.MonkeyPatch
):
    """Leaving the first file renamed after the second write fails must make this test fail."""
    locations_path, _, schedule_path = catalog_paths
    original_replace = os.replace

    def fail_schedule_replace(source, target):
        if Path(target) == schedule_path:
            raise OSError("schedule indisponível")
        original_replace(source, target)

    monkeypatch.setattr(os, "replace", fail_schedule_replace)

    with pytest.raises(PersistenceError, match="agenda"):
        LocationRepository(locations_path, schedule_path).rename("loc-001", "Novo nome")

    assert read_json(locations_path)["locations"][0]["name"] == "Auditório"
    assert read_json(schedule_path) == referenced_schedule()


def test_location_rename_reports_and_logs_rollback_failure(
    catalog_paths, monkeypatch: pytest.MonkeyPatch
):
    """Hiding a failed catalog restoration must make this test fail."""
    locations_path, _, schedule_path = catalog_paths
    original_replace = os.replace
    location_replaces = 0
    critical_messages: list[str] = []

    def fail_schedule_and_rollback(source, target):
        nonlocal location_replaces
        if Path(target) == schedule_path:
            raise OSError("schedule indisponível")
        if Path(target) == locations_path:
            location_replaces += 1
            if location_replaces == 2:
                raise OSError("rollback indisponível")
        original_replace(source, target)

    sink_id = logger.add(
        lambda message: critical_messages.append(str(message)),
        level="CRITICAL",
        format="{message}",
    )
    monkeypatch.setattr(os, "replace", fail_schedule_and_rollback)
    try:
        with pytest.raises(PersistenceError, match="restaurar"):
            LocationRepository(locations_path, schedule_path).rename("loc-001", "Novo nome")
    finally:
        logger.remove(sink_id)

    assert read_json(locations_path)["locations"][0]["name"] == "Novo nome"
    assert read_json(schedule_path) == referenced_schedule()
    assert any("rollback indisponível" in message for message in critical_messages)


def test_location_delete_reports_all_activity_titles_that_use_it(catalog_paths):
    """Deleting a referenced location or omitting references must make this test fail."""
    locations_path, _, schedule_path = catalog_paths

    with pytest.raises(ResourceInUseError) as error:
        LocationRepository(locations_path, schedule_path).delete("loc-001")

    assert error.value.references == ["Atividade referenciada"]
    assert len(LocationRepository(locations_path, schedule_path).list()) == 1


def test_location_delete_removes_unused_item_without_reusing_id(tmp_path: Path):
    """Failing to persist deletion or decrementing nextId must make this test fail."""
    locations_path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        locations_path,
        {"nextId": 3, "locations": [{"id": "loc-002", "name": "Hall"}]},
    )
    write_json(schedule_path, empty_schedule())
    repository = LocationRepository(locations_path, schedule_path)

    repository.delete("loc-002")

    assert repository.list() == []
    assert read_json(locations_path)["nextId"] == 3


def test_axis_create_uses_portuguese_slug_and_collision_suffix(tmp_path: Path):
    """Overwriting a colliding slug or changing the base slug must make this test fail."""
    axes_path = tmp_path / "axes.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        axes_path,
        {"knowledgeAxes": [{"id": "saude-e-bem-estar", "name": "Saúde e bem-estar"}]},
    )
    write_json(schedule_path, empty_schedule())
    repository = KnowledgeAxisRepository(axes_path, schedule_path)

    created = repository.create("Saúde - e bem-estar")

    assert created == {"id": "saude-e-bem-estar-2", "name": "Saúde - e bem-estar"}
    assert created in repository.list()


def test_axis_rename_keeps_id_and_does_not_rewrite_schedule(catalog_paths):
    """Generating a new ID or rewriting schedule axis references must make this test fail."""
    _, axes_path, schedule_path = catalog_paths
    original_schedule_bytes = schedule_path.read_bytes()
    repository = KnowledgeAxisRepository(axes_path, schedule_path)

    renamed = repository.rename("educacao", "Educação e ensino")

    assert renamed == {"id": "educacao", "name": "Educação e ensino"}
    assert schedule_path.read_bytes() == original_schedule_bytes


def test_axis_delete_reports_activity_titles_that_use_it(catalog_paths):
    """Deleting a referenced axis must make this test fail."""
    _, axes_path, schedule_path = catalog_paths

    with pytest.raises(ResourceInUseError) as error:
        KnowledgeAxisRepository(axes_path, schedule_path).delete("educacao")

    assert error.value.references == ["Atividade referenciada"]


def test_axis_delete_removes_unused_item(tmp_path: Path):
    """Failing to persist deletion of an unused axis must make this test fail."""
    axes_path = tmp_path / "axes.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(axes_path, {"knowledgeAxes": [{"id": "geral", "name": "Geral"}]})
    write_json(schedule_path, empty_schedule())
    repository = KnowledgeAxisRepository(axes_path, schedule_path)

    repository.delete("geral")

    assert repository.list() == []


@pytest.mark.parametrize("repository_name", ["location", "axis"])
def test_catalog_operations_raise_stable_not_found_error(tmp_path: Path, repository_name: str):
    """Silently ignoring an unknown resource ID must make this test fail."""
    schedule_path = tmp_path / "schedule.json"
    write_json(schedule_path, empty_schedule())
    if repository_name == "location":
        path = tmp_path / "locations.json"
        write_json(path, {"nextId": 1, "locations": []})
        repository = LocationRepository(path, schedule_path)
    else:
        path = tmp_path / "axes.json"
        write_json(path, {"knowledgeAxes": []})
        repository = KnowledgeAxisRepository(path, schedule_path)

    with pytest.raises(ResourceNotFoundError):
        repository.rename("missing", "Novo nome")
    with pytest.raises(ResourceNotFoundError):
        repository.delete("missing")


def test_catalog_write_failure_is_exposed_as_persistence_error(
    catalog_paths, monkeypatch: pytest.MonkeyPatch
):
    """Leaking filesystem errors from repository operations must make this test fail."""
    locations_path, _, schedule_path = catalog_paths
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("disco cheio")))

    with pytest.raises(PersistenceError, match="locais"):
        LocationRepository(locations_path, schedule_path).create("Sala nova")

    assert read_json(locations_path)["nextId"] == 2


def test_repository_seed_catalogs_and_schedule_are_canonical(tmp_path: Path):
    """An incomplete catalog or surviving English axis ID must make this test fail."""
    backend_root = Path(__file__).parents[1]
    copies = {}
    for filename in ("schedule.json", "locations.json", "knowledge_axes.json"):
        destination = tmp_path / filename
        shutil.copyfile(backend_root / "db" / filename, destination)
        copies[filename] = read_json(destination)

    schedule = copies["schedule.json"]
    locations = copies["locations.json"]
    axes = copies["knowledge_axes.json"]
    used_locations = sorted(
        {
            session["location"]
            for section in schedule["sections"]
            for group in section["groups"]
            for activity in group["items"]
            for session in activity.get("sessions", [])
            if session.get("location") is not None
        }
    )
    used_axes = {
        group["knowledgeAxis"]
        for section in schedule["sections"]
        for group in section["groups"]
        if group.get("knowledgeAxis") is not None
    }

    used_locations = sorted(
        location for item in locations["locations"] for location in [item["name"]]
    )
    assert list(locations) == ["nextId", "nextGroupId", "groups", "locations"]
    assert sorted(item["name"] for item in locations["locations"]) == used_locations
    assert len(locations["groups"]) > 0
    assert locations["nextId"] > len(used_locations)
    assert list(axes) == ["knowledgeAxes"]
    assert [(item["id"], item["name"]) for item in axes["knowledgeAxes"]] == AXIS_PAIRS
    assert ENGLISH_AXIS_IDS.isdisjoint(used_axes)
    assert used_axes == {axis_id for axis_id, _ in AXIS_PAIRS}


def test_location_group_can_be_renamed_without_changing_its_id(tmp_path: Path):
    locations_path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    write_json(
        locations_path,
        {
            "nextId": 2,
            "nextGroupId": 2,
            "groups": [{"id": "group-001", "name": "Bloco C", "category": "blocos"}],
            "locations": [
                {"id": "loc-001", "name": "Sala 1", "category": "blocos", "groupId": "group-001"}
            ],
        },
    )
    write_json(schedule_path, empty_schedule())

    updated = LocationRepository(locations_path, schedule_path).rename_group(
        "group-001", "Laboratório C", "laboratorios"
    )

    assert updated == {"id": "group-001", "name": "Laboratório C", "category": "laboratorios"}
    catalog = LocationRepository(locations_path, schedule_path)
    assert catalog.list_groups() == [updated]
    assert catalog.list()[0]["groupName"] == "Laboratório C"


def test_seed_catalog_splits_auditoriums_between_block_groups():
    catalog = read_json(Path(__file__).parents[1] / "db" / "locations.json")
    auditorium_names = {
        item["name"] for item in catalog["locations"] if "Auditório" in item["name"]
    }

    assert auditorium_names == {"Auditório do Bloco A", "Auditório do Bloco B"}
    assert all(item["category"] == "blocos" for item in catalog["locations"] if item["name"] in auditorium_names)
    assert all(item["groupId"] != "group-001" for item in catalog["locations"])
