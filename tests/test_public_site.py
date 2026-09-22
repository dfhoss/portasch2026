import json
import re
from pathlib import Path

import pytest


def test_public_site_is_served_from_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "UFFS de Portas Abertas" in response.text


def test_public_site_shell_does_not_embed_persisted_schedule_data(client):
    html = client.get("/").text

    assert "Recepção nos Auditórios dos Blocos A e B" not in html
    assert "eventDate" not in html
    assert "data-schedule-item" not in html
    assert 'class="activity-card"' not in html
    assert 'aria-busy="true"' in html
    assert "<noscript>" in html


def test_public_site_shell_has_unique_label_targets_and_decorative_arrow_icons(client):
    html = client.get("/").text
    ids = re.findall(r'\bid="([^"]+)"', html)
    labelled_by = re.findall(r'aria-labelledby="([^"]+)"', html)
    arrow_svgs = re.findall(
        r'<button class="carousel-btn (?:prev|next)"[^>]*>(.*?)</button>',
        html,
        flags=re.DOTALL,
    )

    assert len(ids) == len(set(ids))
    assert all(target in ids for target in labelled_by)
    assert len(arrow_svgs) == 2
    assert all('aria-hidden="true"' in svg for svg in arrow_svgs)


@pytest.mark.parametrize(
    "file_name",
    ["schedule.json", "knowledge_axes.json", "locations.json", "settings.json"],
)
def test_public_json_route_serves_only_the_allowlisted_documents(client, file_name):
    response = client.get(f"/db/{file_name}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["cache-control"] == "no-cache"


@pytest.mark.parametrize("file_name", ["users.json", "participants.json", "../users.json"])
def test_public_json_route_hides_non_public_files(client, file_name):
    response = client.get(f"/db/{file_name}")

    assert response.status_code == 404
    assert "users" not in response.text
    assert "participants" not in response.text


def test_public_json_route_resolves_schedule_and_settings_paths_per_request(
    client, configured_environment, monkeypatch, tmp_path: Path
):
    first_schedule = client.get("/db/schedule.json")
    first_settings = client.get("/db/settings.json")
    assert first_schedule.status_code == 200
    assert first_settings.status_code == 200

    replacement_schedule = tmp_path / "replacement-schedule.json"
    schedule_payload = first_schedule.json()
    schedule_payload["version"] = 42
    replacement_schedule.write_text(json.dumps(schedule_payload), encoding="utf-8")

    replacement_settings = tmp_path / "replacement-settings.json"
    settings_payload = first_settings.json()
    settings_payload["eventDate"] = "2027-01-02"
    replacement_settings.write_text(json.dumps(settings_payload), encoding="utf-8")

    monkeypatch.setenv("SCHEDULE_PATH", str(replacement_schedule))
    monkeypatch.setenv("SETTINGS_PATH", str(replacement_settings))

    second_schedule = client.get("/db/schedule.json")
    second_settings = client.get("/db/settings.json")

    assert second_schedule.json()["version"] == 42
    assert second_settings.json()["eventDate"] == "2027-01-02"
    assert str(configured_environment.schedule) not in second_schedule.text
    assert str(configured_environment.settings) not in second_settings.text


@pytest.mark.parametrize(
    ("file_name", "environment_name", "path_kind"),
    [
        ("schedule.json", "SCHEDULE_PATH", "missing"),
        ("settings.json", "SETTINGS_PATH", "directory"),
    ],
)
def test_public_json_route_hides_missing_or_directory_paths(
    client, monkeypatch, tmp_path: Path, file_name, environment_name, path_kind
):
    target = tmp_path / "unavailable" / file_name
    if path_kind == "directory":
        target.mkdir(parents=True)
    monkeypatch.setenv(environment_name, str(target))

    response = client.get(f"/db/{file_name}")

    assert response.status_code == 404
    assert str(target) not in response.text
