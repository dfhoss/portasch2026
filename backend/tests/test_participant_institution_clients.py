import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_science_fair_keeps_section_without_participating_teams():
    payload = read_json(Path(__file__).parents[1] / "db" / "schedule.json")
    section = next(item for item in payload["sections"] if item["id"] == "science-fair")
    assert section["groups"] == []


def test_institutions_seed_contains_eleven_schools():
    payload = read_json(Path(__file__).parents[1] / "db" / "institutions.json")
    assert payload["nextId"] == 12
    assert len(payload["institutions"]) == 11
    assert {item["state"] for item in payload["institutions"]} == {"SC"}
    assert {item["city"] for item in payload["institutions"]} == {"Chapecó"}


def test_temporary_database_copies_institution_and_participant_catalogs(
    temporary_database,
):
    assert temporary_database.institutions.exists()
    assert temporary_database.participants.exists()
    assert read_json(temporary_database.participants) == {
        "nextId": 1,
        "participants": [],
    }
