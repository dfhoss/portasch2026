import json
import re
from html.parser import HTMLParser
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


def test_hidden_admin_views_are_not_overridden_by_layout_css(client):
    """A visible hidden login/editor view must make this fail."""
    css = client.get("/admin/static/admin.css").text

    hidden_rule = css_rule(css, "[hidden]")
    assert "display: none !important" in hidden_rule


def test_admin_visual_identity_is_driven_by_semantic_design_tokens(client):
    """Removing semantic tokens or bypassing them in key surfaces must make this fail."""
    css = client.get("/admin/static/admin.css").text

    root_rule = css_rule(css, ":root")
    for token in (
        "--color-page:",
        "--color-surface:",
        "--color-text:",
        "--color-action-primary:",
        "--color-navigation:",
        "--color-focus:",
        "--space-4:",
        "--radius-lg:",
    ):
        assert token in root_rule

    assert "var(--color-page)" in css_rule(css, "body")
    assert "var(--color-navigation)" in css_rule(css, ".editor-sidebar")
    assert "var(--color-action-primary)" in css_rule(css, ".primary-action")
    assert "var(--color-focus)" in css_rule(css, "button:focus-visible")


def test_login_message_is_between_password_and_submit_and_uses_error_tone(client):
    """Session errors must be prominent and appear next to the action they explain."""
    html = client.get("/admin").text
    password_end = html.index('id="password"')
    message_position = html.index('id="login-message"')
    submit_position = html.index('type="submit"')

    assert password_end < message_position < submit_position

    css = client.get("/admin/static/admin.css").text
    message_rule = css_rule(css, "#editor-message:not(:empty), #login-message:not(:empty)")
    login_color_rule = css_rule(css, ".login-card #login-message:not(:empty)")
    assert "border: var(--border-width) solid var(--green-200)" in message_rule
    assert "background: var(--color-surface-selected)" in message_rule
    assert "border-color: var(--color-danger)" in login_color_rule
    assert "background: var(--color-danger-surface)" in login_color_rule
    assert "color: var(--color-danger-text)" in login_color_rule
    assert "display: none" in css_rule(css, "#login-message:empty")


def test_login_password_disables_browser_persistence(client):
    html = client.get("/admin").text

    assert 'id="login-form" class="login-card" autocomplete="off"' in html
    assert 'id="password" name="password" type="password" autocomplete="off"' in html


class EditorShellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[dict[str, str]] = []
        self.sidebar_contents: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        self.stack.append({"tag": tag, **attributes})
        if any(item.get("class") == "editor-sidebar" for item in self.stack):
            self.sidebar_contents.append({"tag": tag, **attributes})

    def handle_endtag(self, tag: str) -> None:
        if self.stack and self.stack[-1]["tag"] == tag:
            self.stack.pop()


def css_rule(css: str, selector: str, start: int = 0) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css[start:])
    assert match, f"Missing CSS rule for {selector}"
    return match.group(1)


def test_editor_navigation_is_sidebar_on_desktop_and_top_bar_below_750px(client):
    """Placing the navigation beside the sidebar or keeping it horizontal on desktop must fail."""
    page = client.get("/admin").text
    css = client.get("/admin/static/admin.css").text
    parser = EditorShellParser()
    parser.feed(page)

    sidebar_tags = [item for item in parser.sidebar_contents if item["tag"] == "aside"]
    assert sidebar_tags
    assert any(item["tag"] == "nav" for item in parser.sidebar_contents)
    assert any(item.get("id") == "editor-title" for item in parser.sidebar_contents)
    assert any(item.get("id") == "logout-button" for item in parser.sidebar_contents)

    desktop_css, _, mobile_css = css.partition("@media (max-width: 749px)")
    assert "grid-column: 1" in css_rule(desktop_css, ".editor-sidebar")
    assert "flex-direction: column" in css_rule(desktop_css, ".editor-sidebar nav")
    assert "flex-direction: row" in css_rule(mobile_css, ".editor-sidebar nav")


def test_browser_authentication_contract_validates_identity_before_loading_data(client):
    """Loading data early or storing anything beyond token and view state must make this fail."""
    script = client.get("/admin/static/admin.js").text

    assert 'sessionStorage.setItem("adminToken", token.access_token)' in script
    assert 'const ADMIN_VIEW_STATE_KEY = "adminViewState"' in script
    assert script.count("sessionStorage.setItem(") == 2
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
