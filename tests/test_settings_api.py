import json
import os
from pathlib import Path

import pytest
from clients.json_store import PersistenceError
from clients.settings import get_settings_path, load_settings, replace_settings
from models.settings import SettingsDocument
from pydantic import ValidationError


def test_settings_document_uses_event_date_alias_and_serializes_iso_date():
    document = SettingsDocument.model_validate({"eventDate": "2026-10-26"})

    assert document.event_date.isoformat() == "2026-10-26"
    assert document.model_dump(by_alias=True, mode="json") == {"eventDate": "2026-10-26"}


def test_settings_rejects_invalid_event_date():
    with pytest.raises(ValidationError):
        SettingsDocument.model_validate({"eventDate": "2026-02-30"})


def test_settings_path_is_resolved_at_call_time(tmp_path, monkeypatch):
    first = tmp_path / "first-settings.json"
    second = tmp_path / "second-settings.json"
    monkeypatch.setenv("SETTINGS_PATH", str(first))
    assert get_settings_path() == first
    monkeypatch.setenv("SETTINGS_PATH", str(second))
    assert get_settings_path() == second


def test_replace_settings_persists_only_the_canonical_document(tmp_path):
    path = tmp_path / "settings.json"
    document = SettingsDocument.model_validate({"eventDate": "2026-09-22"})

    assert replace_settings(document, path) == document
    assert json.loads(path.read_text(encoding="utf-8")) == {"eventDate": "2026-09-22"}


def test_load_settings_reads_the_canonical_document(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"eventDate": "2026-10-26"}', encoding="utf-8")

    assert load_settings(path).event_date.isoformat() == "2026-10-26"


def test_replace_settings_converts_replace_failure_and_preserves_previous_file(
    tmp_path, monkeypatch
):
    path = tmp_path / "settings.json"
    path.write_text('{"eventDate": "2026-10-26"}', encoding="utf-8")
    document = SettingsDocument.model_validate({"eventDate": "2026-09-22"})

    def fail_replace(source: os.PathLike[str] | str, target: os.PathLike[str] | str) -> None:
        raise OSError("disco indisponível")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(PersistenceError, match="configurações"):
        replace_settings(document, path)

    assert json.loads(path.read_text(encoding="utf-8")) == {"eventDate": "2026-10-26"}
    assert not list(Path(tmp_path).glob("*.tmp"))


def test_settings_routes_require_authentication(client):
    assert client.get("/api/settings").status_code == 401
    assert client.put("/api/settings", json={"eventDate": "2026-09-22"}).status_code == 401


def test_settings_api_persists_and_returns_iso_date(client, auth_headers, temporary_database):
    response = client.put(
        "/api/settings",
        json={"eventDate": "2026-09-22"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"eventDate": "2026-09-22"}
    assert json.loads(temporary_database.settings.read_text(encoding="utf-8")) == response.json()


def test_schedule_api_never_returns_event_date(client, auth_headers):
    response = client.get("/api/schedule", headers=auth_headers)

    assert response.status_code == 200
    assert "eventDate" not in response.json()


@pytest.mark.parametrize("event_date", ["0000-01-01", "2026-02-30"])
def test_settings_api_rejects_invalid_event_dates(client, auth_headers, event_date):
    response = client.put(
        "/api/settings",
        json={"eventDate": event_date},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.parametrize("payload", ['{"eventDate":', '{"eventDate": "not-a-date"}'])
def test_settings_api_read_failures_are_structured_and_non_leaking(
    client, auth_headers, temporary_database, payload
):
    temporary_database.settings.write_text(payload, encoding="utf-8")

    response = client.get("/api/settings", headers=auth_headers)

    assert response.status_code == 500
    assert response.json() == {
        "detail": {"message": "Não foi possível carregar as configurações", "references": []}
    }
    assert str(temporary_database.settings) not in response.text


def test_settings_api_missing_file_is_structured_and_non_leaking(
    client, auth_headers, temporary_database
):
    temporary_database.settings.unlink()

    response = client.get("/api/settings", headers=auth_headers)

    assert response.status_code == 500
    assert response.json() == {
        "detail": {"message": "Não foi possível carregar as configurações", "references": []}
    }
    assert str(temporary_database.settings) not in response.text


def test_settings_api_persistence_failure_is_structured_and_non_leaking(client, auth_headers):
    from app import app
    from routes.settings import get_settings_replacer

    def fail_replace(document, path):
        raise PersistenceError("filesystem path and internal secret")

    app.dependency_overrides[get_settings_replacer] = lambda: fail_replace

    response = client.put(
        "/api/settings",
        json={"eventDate": "2026-09-22"},
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {"message": "Não foi possível salvar as configurações", "references": []}
    }
    assert "filesystem" not in response.text
