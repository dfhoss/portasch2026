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
    assert document.model_dump(by_alias=True, mode="json") == {
        "eventDate": "2026-10-26"
    }


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
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "eventDate": "2026-09-22"
    }


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

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "eventDate": "2026-10-26"
    }
    assert not list(Path(tmp_path).glob("*.tmp"))
