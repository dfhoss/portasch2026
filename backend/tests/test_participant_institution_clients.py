import json

import pytest
from clients.institutions import InstitutionRepository, get_institutions_path
from clients.json_store import (
    DuplicateResourceNameError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceNotFoundError,
)


def test_catalogos_iniciais_contem_instituicoes_e_feira_de_ciencias(
    temporary_database,
):
    schedule = json.loads(temporary_database.schedule.read_text(encoding="utf-8"))
    institutions = json.loads(temporary_database.institutions.read_text(encoding="utf-8"))
    participants = json.loads(temporary_database.participants.read_text(encoding="utf-8"))

    science_fair = next(
        section for section in schedule["sections"] if section["id"] == "science-fair"
    )
    assert science_fair["groups"] == []
    assert institutions["nextId"] == 12
    assert len(institutions["institutions"]) == 11
    assert {item["state"] for item in institutions["institutions"]} == {"SC"}
    assert {item["city"] for item in institutions["institutions"]} == {"Chapecó"}
    assert participants == {"nextId": 1, "participants": []}


def test_institution_repository_normalizes_values_and_generates_id(tmp_path):
    path = tmp_path / "institutions.json"
    path.write_text('{"nextId": 1, "institutions": []}', encoding="utf-8")

    created = InstitutionRepository(path).create(
        "  Escola   Nova ", " SC ", " Chapecó ", "  texto  "
    )

    assert created == {
        "id": "institution-001",
        "name": "Escola Nova",
        "state": "SC",
        "city": "Chapecó",
        "description": "texto",
    }


def test_institution_repository_supports_crud_and_defensive_copies(tmp_path):
    path = tmp_path / "institutions.json"
    path.write_text('{"nextId": 1, "institutions": []}', encoding="utf-8")
    repository = InstitutionRepository(path)

    created = repository.create("Escola Nova", "SC", "Chapecó", None)
    created["name"] = "Alterada"
    assert repository.get("institution-001")["name"] == "Escola Nova"
    updated = repository.update("institution-001", "Outra", "PR", "Curitiba", "  ")
    assert updated["description"] is None
    assert repository.list() == [updated]
    repository.delete("institution-001")
    assert repository.list() == []
    with pytest.raises(ResourceNotFoundError):
        repository.get("institution-001")


def test_institution_repository_rejects_duplicate_names_and_invalid_fields(tmp_path):
    path = tmp_path / "institutions.json"
    path.write_text(
        json.dumps(
            {
                "nextId": 2,
                "institutions": [
                    {
                        "id": "institution-001",
                        "name": "Escola Nova",
                        "state": "SC",
                        "city": "Chapecó",
                        "description": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    repository = InstitutionRepository(path)
    with pytest.raises(DuplicateResourceNameError):
        repository.create(" ESCOLA   NOVA ", "SC", "Chapecó", None)
    with pytest.raises(InvalidResourceNameError):
        repository.create(" ", "SC", "Chapecó", None)
    with pytest.raises(ValueError):
        repository.create("x" * 201, "SC", "Chapecó", None)


def test_institution_repository_validates_catalog_structure(tmp_path):
    path = tmp_path / "institutions.json"
    path.write_text('{"nextId": 0, "institutions": []}', encoding="utf-8")
    with pytest.raises(ValueError):
        InstitutionRepository(path).list()


@pytest.mark.parametrize(
    "payload",
    [
        {"nextId": 1, "institutions": [], "unexpected": True},
        {
            "nextId": 1,
            "institutions": [
                {
                    "id": "institution-001",
                    "name": "Escola Nova",
                    "state": "SC",
                    "city": "Chapecó",
                    "description": None,
                    "unexpected": True,
                }
            ],
        },
    ],
)
def test_institution_repository_rejects_extra_catalog_keys(tmp_path, payload):
    path = tmp_path / "institutions.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Catálogo de instituições inválido"):
        InstitutionRepository(path).list()


def test_institution_repository_converts_malformed_json_to_stable_persistence_error(
    tmp_path,
):
    path = tmp_path / "catalogo-secreto.json"
    path.write_text('{"nextId": 1,', encoding="utf-8")

    with pytest.raises(
        PersistenceError,
        match="^Não foi possível ler o catálogo de instituições$",
    ) as error:
        InstitutionRepository(path).list()

    assert str(path) not in str(error.value)


def test_institution_repository_converts_non_object_json_to_stable_persistence_error(
    tmp_path,
):
    path = tmp_path / "raiz-lista-secreta.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(
        PersistenceError,
        match="^Não foi possível ler o catálogo de instituições$",
    ) as error:
        InstitutionRepository(path).list()

    assert str(path) not in str(error.value)


def test_get_institutions_path_reads_environment_each_call(monkeypatch, tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.setenv("INSTITUTIONS_PATH", str(first))
    assert get_institutions_path() == first
    monkeypatch.setenv("INSTITUTIONS_PATH", str(second))
    assert get_institutions_path() == second


def test_institution_repository_converts_filesystem_errors(tmp_path):
    path = tmp_path / "institutions.json"
    path.write_text('{"nextId": 1, "institutions": []}', encoding="utf-8")
    repository = InstitutionRepository(path)
    path.unlink()
    path.mkdir()
    with pytest.raises(PersistenceError):
        repository.create("Escola", "SC", "Chapecó", None)
