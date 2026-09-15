import json

import pytest
from clients.institutions import InstitutionRepository, get_institutions_path
from clients.json_store import (
    DuplicateParticipantCpfError,
    DuplicateResourceNameError,
    InvalidResourceNameError,
    PersistenceError,
    ResourceInUseError,
    ResourceNotFoundError,
)
from clients.participants import ParticipantRepository, get_participants_path, normalize_cpf


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
    (tmp_path / "participants.json").write_text(
        '{"nextId": 1, "participants": []}', encoding="utf-8"
    )
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
    (tmp_path / "participants.json").write_text(
        '{"nextId": 1, "participants": []}', encoding="utf-8"
    )
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


@pytest.mark.parametrize("value", ["529.982.247-25", "52998224725"])
def test_normalize_cpf_accepts_valid_values(value):
    assert normalize_cpf(value) == "52998224725"


@pytest.mark.parametrize("value", ["111.111.111-11", "123", "529.982.247-26"])
def test_normalize_cpf_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        normalize_cpf(value)


def test_get_participants_path_reads_environment_each_call(monkeypatch, tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.setenv("PARTICIPANTS_PATH", str(first))
    assert get_participants_path() == first
    monkeypatch.setenv("PARTICIPANTS_PATH", str(second))
    assert get_participants_path() == second


def test_participant_repository_crud_normalizes_and_returns_defensive_copies(tmp_path):
    participants = tmp_path / "participants.json"
    institutions = tmp_path / "institutions.json"
    participants.write_text('{"nextId": 1, "participants": []}', encoding="utf-8")
    institutions.write_text(
        '{"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola", "state": "SC", "city": "Chapecó", "description": null}]}',
        encoding="utf-8",
    )
    repository = ParticipantRepository(participants, institutions)

    created = repository.create(
        "  Ana  ", "529.982.247-25", "  ana@example.org  ", "institution-001"
    )
    assert created == {
        "id": "participant-001",
        "name": "Ana",
        "cpf": "52998224725",
        "email": "ana@example.org",
        "institutionId": "institution-001",
    }
    created["name"] = "Alterada"
    assert repository.get("participant-001")["name"] == "Ana"
    updated = repository.update(
        "participant-001", "Bia", "529.982.247-25", "bia@example.org", "institution-001"
    )
    assert updated["id"] == "participant-001"
    repository.delete("participant-001")
    assert repository.list() == []


def test_participant_repository_rejects_duplicate_cpf_and_missing_institution(tmp_path):
    participants = tmp_path / "participants.json"
    institutions = tmp_path / "institutions.json"
    participants.write_text(
        '{"nextId": 2, "participants": [{"id": "participant-001", "name": "Ana", "cpf": "52998224725", "email": "ana@example.org", "institutionId": "institution-001"}]}',
        encoding="utf-8",
    )
    institutions.write_text(
        '{"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola", "state": "SC", "city": "Chapecó", "description": null}]}',
        encoding="utf-8",
    )
    repository = ParticipantRepository(participants, institutions)
    with pytest.raises(DuplicateParticipantCpfError):
        repository.create("Bia", "529.982.247-25", "bia@example.org", "institution-001")
    with pytest.raises(ResourceNotFoundError):
        repository.create("Bia", "935.411.347-80", "bia@example.org", "institution-999")


def test_institution_delete_is_blocked_by_participant_references(tmp_path):
    institutions = tmp_path / "institutions.json"
    participants = tmp_path / "participants.json"
    institutions.write_text(
        '{"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola", "state": "SC", "city": "Chapecó", "description": null}]}',
        encoding="utf-8",
    )
    participants.write_text(
        '{"nextId": 2, "participants": [{"id": "participant-001", "name": "Ana", "cpf": "52998224725", "email": "ana@example.org", "institutionId": "institution-001"}]}',
        encoding="utf-8",
    )
    before = institutions.read_text(encoding="utf-8")
    with pytest.raises(ResourceInUseError) as error:
        InstitutionRepository(institutions, participants).delete("institution-001")
    assert error.value.references == ["participant-001"]
    assert institutions.read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    "value", ["abc529.982.247-25", "529.982.247-25x", "５２９９８２２４７２５"]
)
def test_normalize_cpf_rejects_non_contract_formats(value):
    with pytest.raises(ValueError):
        normalize_cpf(value)


@pytest.mark.parametrize(
    "bad",
    [
        [{"id": "institution-001"}],
        [
            {
                "id": "institution-001",
                "name": "Escola",
                "state": "SC",
                "city": "Chapecó",
                "description": None,
                "extra": 1,
            }
        ],
        ["not-an-institution"],
    ],
)
def test_participant_repository_rejects_invalid_institution_catalog(tmp_path, bad):
    participants = tmp_path / "participants.json"
    institutions = tmp_path / "institutions.json"
    participants.write_text('{"nextId": 1, "participants": []}', encoding="utf-8")
    institutions.write_text(json.dumps({"nextId": 2, "institutions": bad}), encoding="utf-8")
    with pytest.raises(PersistenceError, match="catálogo de instituições"):
        ParticipantRepository(participants, institutions).create(
            "Ana", "52998224725", "a@e.com", "institution-001"
        )


def test_participant_repository_rejects_invalid_persisted_invariants(tmp_path):
    participants = tmp_path / "participants.json"
    institutions = tmp_path / "institutions.json"
    institutions.write_text(
        '{"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola", "state": "SC", "city": "Chapecó", "description": null}]}',
        encoding="utf-8",
    )
    participants.write_text(
        json.dumps(
            {
                "nextId": 3,
                "participants": [
                    {
                        "id": "participant-001",
                        "name": "Ana",
                        "cpf": "52998224726",
                        "email": "a@e.com",
                        "institutionId": "institution-001",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PersistenceError):
        ParticipantRepository(participants, institutions).list()


def test_public_institution_repository_protects_references(tmp_path):
    institutions = tmp_path / "institutions.json"
    participants = tmp_path / "participants.json"
    institutions.write_text(
        '{"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola", "state": "SC", "city": "Chapecó", "description": null}]}',
        encoding="utf-8",
    )
    participants.write_text(
        '{"nextId": 2, "participants": [{"id": "participant-001", "name": "Ana", "cpf": "52998224725", "email": "a@e.com", "institutionId": "institution-001"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ResourceInUseError):
        InstitutionRepository(institutions).delete("institution-001")
