import json

import pytest
from models.schedule import ScheduleDocument, Session, slugify_id
from pydantic import ValidationError


def test_rejects_session_when_end_is_not_after_start():
    """Removing chronological validation must make this test fail."""
    payload = {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [
            {
                "id": "s",
                "title": "S",
                "groups": [
                    {
                        "id": "g",
                        "title": "G",
                        "items": [
                            {
                                "id": "a",
                                "title": "A",
                                "sessions": [
                                    {
                                        "startTime": "10:00",
                                        "endTime": "09:00",
                                        "location": "Sala",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError, match="posterior ao inicial"):
        ScheduleDocument.model_validate(payload)


def test_rejects_second_precision_session_times():
    """Removing minute-precision validation must make this test fail."""
    with pytest.raises(ValidationError, match="precisão de minutos"):
        Session.model_validate(
            {
                "startTime": "09:00:30",
                "endTime": "10:00:30",
                "location": "Sala",
            }
        )


def test_slugify_id_uses_portuguese_text_without_accents():
    """Removing accent normalization or hyphen cleanup must make this test fail."""
    assert slugify_id("Saúde e bem-estar") == "saude-e-bem-estar"


def test_rejects_duplicate_ids_anywhere_in_the_document():
    """Removing document-wide ID validation must make this test fail."""
    payload = {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [
            {
                "id": "duplicado",
                "title": "Seção",
                "groups": [
                    {
                        "id": "grupo",
                        "title": "Grupo",
                        "items": [{"id": "duplicado", "title": "Atividade"}],
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError, match="IDs duplicados"):
        ScheduleDocument.model_validate(payload)


def test_canonicalizes_missing_ids_with_document_wide_collision_suffixes():
    """Removing missing-ID generation or collision handling must make this test fail."""
    payload = {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [
            {
                "id": "",
                "title": "Programação",
                "groups": [
                    {
                        "title": "Programação",
                        "items": [{"id": None, "title": "Programação"}],
                    }
                ],
            }
        ],
    }

    document = ScheduleDocument.model_validate(payload)

    assert document.sections[0].id == "programacao"
    assert document.sections[0].groups[0].id == "programacao-2"
    assert document.sections[0].groups[0].items[0].id == "programacao-3"


def test_accepts_json_aliases_and_defaults_optional_activity_fields():
    """Removing aliases or optional defaults must make this test fail."""
    document = ScheduleDocument.model_validate(
        {
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
                            "knowledgeAxis": "education",
                            "items": [{"id": "atividade", "title": "Atividade"}],
                        }
                    ],
                }
            ],
        }
    )

    group = document.sections[0].groups[0]
    activity = group.items[0]
    assert document.event_date.isoformat() == "2026-10-26"
    assert group.knowledge_axis == "education"
    assert activity.description is None
    assert activity.sessions == []
    assert activity.link is None
    assert document.model_dump(by_alias=True, mode="json")["eventDate"] == "2026-10-26"
    assert (
        document.model_dump(by_alias=True, mode="json")["sections"][0]["groups"][0]["knowledgeAxis"]
        == "education"
    )


def test_round_trips_a_temporary_copy_of_the_current_schedule_without_field_loss(
    schedule_copy,
):
    """Dropping recognized JSON fields during serialization must make this test fail."""
    with schedule_copy.open(encoding="utf-8") as schedule_file:
        original = json.load(schedule_file)

    document = ScheduleDocument.model_validate(original)

    assert document.model_dump(by_alias=True, exclude_unset=True, mode="json") == original
