import json
from pathlib import Path


def test_admin_page_is_served_without_embedding_schedule(client):
    """Embedding schedule data in the public shell must make this fail."""
    response = client.get("/admin")

    assert response.status_code == 200
    assert 'id="login-view"' in response.text
    assert "Programação completa" not in response.text


def test_admin_javascript_is_served(client):
    """Removing the browser authentication asset must make this fail."""
    response = client.get("/admin/static/admin.js")

    assert response.status_code == 200
    assert "sessionStorage" in response.text


def test_admin_static_assets_are_public_and_data_free(client):
    """Serving the shell from protected APIs or embedding catalog data must make this fail."""
    css_response = client.get("/admin/static/admin.css")
    script_response = client.get("/admin/static/admin.js")

    assert css_response.status_code == 200
    assert script_response.status_code == 200
    assert "Auditórios dos Blocos A e B" not in script_response.text
    assert "Programação completa" not in script_response.text


def test_browser_authentication_contract_validates_identity_before_loading_data(client):
    """Loading editor data before identity validation or storing extra login data must fail."""
    script = client.get("/admin/static/admin.js").text

    assert 'sessionStorage.setItem("adminToken", token.access_token)' in script
    assert script.count("sessionStorage.setItem(") == 1
    editor_start = script.index("async function showEditor")
    assert script.index('apiFetch("/auth/users/me/")', editor_start) < script.index(
        "await loadAdminData()", editor_start
    )
    assert 'sessionStorage.removeItem("adminToken")' in script


def test_load_database_resolves_configured_path_at_call_time(monkeypatch, tmp_path: Path):
    """Binding DATABASE_PATH at import time must make this isolated read fail."""
    from clients.db import load_database

    users_path = tmp_path / "isolated-users.json"
    users_path.write_text(json.dumps({"users": [{"username": "isolated"}]}), encoding="utf-8")
    monkeypatch.setenv("DATABASE_PATH", str(users_path))

    assert load_database() == {"users": [{"username": "isolated"}]}
