from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

import jwt
from playwright.sync_api import Dialog, Page, expect

from .conftest import TEST_JWT_SECRET, TEST_PASSWORD, TEST_USERNAME


def login(page: Page, password: str = TEST_PASSWORD) -> None:
    page.get_by_label("Usuário").fill(TEST_USERNAME)
    page.get_by_label("Senha").fill(password)
    page.get_by_role("button", name="Entrar").click()
    expect(page.locator("#editor-view")).to_be_visible(timeout=10_000)
    expect(page.get_by_role("heading", name="Programação", exact=True)).to_be_visible()
    expect(page.locator("#schedule-sections")).to_contain_text(
        "Programação completa", timeout=10_000
    )


def accept_dialog(dialog: Dialog) -> None:
    dialog.accept()


def apply_modal(page: Page) -> None:
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator("#editor-modal")).to_be_hidden(timeout=500)


def test_invalid_login_never_requests_admin_data(admin_page: Page) -> None:
    requests: list[str] = []
    admin_page.on("request", lambda request: requests.append(request.url))
    admin_page.get_by_label("Usuário").fill(TEST_USERNAME)
    admin_page.get_by_label("Senha").fill("wrong-password")
    admin_page.get_by_role("button", name="Entrar").click()
    expect(admin_page.get_by_role("status").first).to_contain_text("inválidos")
    assert not any("/admin/api/" in request for request in requests)
    assert admin_page.evaluate("Object.keys(sessionStorage)") == []


def test_valid_login_orders_identity_before_admin_requests_and_limits_storage(
    admin_page: Page,
) -> None:
    requests: list[str] = []
    admin_page.on("request", lambda request: requests.append(request.url))
    login(admin_page)
    token_index = next(index for index, path in enumerate(requests) if path.endswith("/auth/token"))
    identity_index = next(index for index, path in enumerate(requests) if "/auth/users/me/" in path)
    first_admin_index = next(index for index, path in enumerate(requests) if "/admin/api/" in path)
    assert token_index < identity_index < first_admin_index
    assert admin_page.evaluate("Object.keys(sessionStorage)") == ["adminToken"]


def test_malformed_token_is_removed_and_returns_to_login(live_server_url: str, browser) -> None:
    page = browser.new_page()
    page.add_init_script("sessionStorage.setItem('adminToken', 'malformed-token')")
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(f"{live_server_url}/admin", wait_until="networkidle")
    expect(page.locator("#login-view")).to_be_visible()
    expect(page.get_by_text("Sua sessão expirou. Entre novamente.")).to_be_visible()
    assert page.evaluate("Object.keys(sessionStorage)") == []
    assert not any("/admin/api/" in request for request in requests)
    page.close()


def test_expired_token_is_removed_and_never_loads_admin_data(live_server_url: str, browser) -> None:
    expired_token = jwt.encode(
        {"sub": TEST_USERNAME, "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    page = browser.new_page()
    page.add_init_script(f"sessionStorage.setItem('adminToken', {json.dumps(expired_token)})")
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(f"{live_server_url}/admin", wait_until="networkidle")
    expect(page.locator("#login-view")).to_be_visible()
    expect(page.get_by_text("Sua sessão expirou. Entre novamente.")).to_be_visible()
    assert page.evaluate("Object.keys(sessionStorage)") == []
    assert not any("/admin/api/" in request for request in requests)
    page.close()


def test_navigation_and_modal_escape_apply_restore_focus(admin_page: Page) -> None:
    login(admin_page)
    for name, heading in (
        ("Locais", "Locais"),
        ("Eixos", "Eixos de conhecimento"),
        ("Minha conta", None),
    ):
        admin_page.get_by_role("button", name=name).click()
        if heading:
            expect(admin_page.get_by_role("heading", name=heading)).to_be_visible()
    admin_page.get_by_role("button", name="Programação").click()
    add_section = admin_page.get_by_role("button", name="Adicionar seção")
    add_section.click()
    expect(admin_page.locator("#editor-modal")).to_be_visible()
    expect(admin_page.get_by_label("Título")).to_be_focused()
    admin_page.keyboard.press("Escape")
    expect(admin_page.locator("#editor-modal")).to_be_hidden()
    expect(add_section).to_be_focused()
    add_section.click()
    admin_page.get_by_label("Título").fill("Foco E2E")
    apply_modal(admin_page)
    expect(admin_page.get_by_role("button", name="Adicionar seção")).to_be_focused()


def test_delayed_initial_data_keeps_editor_hidden_until_schedule_exists(admin_page: Page) -> None:
    admin_page.evaluate(
        """() => {
          const originalFetch = window.fetch;
          window.fetch = async (...args) => {
            if (String(args[0]).includes('/admin/api/schedule')) {
              await new Promise((resolve) => setTimeout(resolve, 2000));
            }
            return originalFetch(...args);
          };
        }"""
    )
    admin_page.get_by_label("Usuário").fill(TEST_USERNAME)
    admin_page.get_by_label("Senha").fill(TEST_PASSWORD)
    admin_page.get_by_role("button", name="Entrar").click()
    assert admin_page.locator("#editor-view").get_attribute("hidden") is not None
    expect(admin_page.locator("#editor-view")).to_be_visible(timeout=10_000)


def test_schedule_create_edit_session_validation_and_reload_persistence(admin_page: Page) -> None:
    login(admin_page)
    add_section = admin_page.get_by_role("button", name="Adicionar seção")
    add_section.click()
    title = admin_page.get_by_label("Título")
    title.fill("Seção E2E")
    title.press("Tab")
    apply_modal(admin_page)

    admin_page.get_by_role("button", name="Adicionar grupo").click()
    admin_page.get_by_label("Título").fill("Grupo E2E")
    apply_modal(admin_page)
    admin_page.locator("#add-activity").click()
    admin_page.get_by_label("Título").fill("Atividade E2E")
    admin_page.get_by_role("button", name="Adicionar horário").click()
    sessions = admin_page.locator(".session-editor")
    sessions.last.get_by_label("Início").fill("10:00")
    sessions.last.get_by_label("Fim").fill("09:00")
    apply_modal(admin_page)
    admin_page.get_by_role("button", name="Salvar programação").click()
    expect(admin_page.get_by_text("O horário final deve ser posterior ao inicial.")).to_be_visible()

    activity = admin_page.locator(".schedule-activity").filter(has_text="Atividade E2E")
    activity.get_by_role("button", name="Editar").click()
    sessions = admin_page.locator(".session-editor")
    sessions.last.get_by_label("Fim").fill("11:00")
    apply_modal(admin_page)
    admin_page.get_by_role("button", name="Salvar programação").click()
    expect(admin_page.get_by_text("Programação salva com sucesso.")).to_be_visible(timeout=10_000)

    admin_page.reload(wait_until="networkidle")
    admin_page.get_by_role("button", name="Seção E2E").click()
    admin_page.locator(".schedule-group").filter(has_text="Grupo E2E").get_by_role(
        "button", name=re.compile("Expandir")
    ).click()
    expect(admin_page.get_by_text("Atividade E2E")).to_be_visible(timeout=10_000)
    expect(admin_page.get_by_text("10:00–11:00")).to_be_visible()


def test_created_location_can_be_selected_in_a_session(admin_page: Page) -> None:
    login(admin_page)
    admin_page.get_by_role("button", name="Locais").click()
    admin_page.get_by_role("button", name="Adicionar local").click()
    admin_page.get_by_label("Nome do local").fill("Local de sessão E2E")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.locator("#editor-modal")).to_be_hidden(timeout=500)

    admin_page.get_by_role("button", name="Programação").click()
    group = admin_page.locator(".schedule-group").filter(has_text="ADMINISTRAÇÃO")
    group.get_by_role("button", name=re.compile("Expandir")).click()
    activity = admin_page.locator(".schedule-activity").filter(
        has_text="Voz e Ação: conhecendo o curso de Administração"
    )
    activity.get_by_role("button", name="Editar").click()
    admin_page.locator('select[name="location"]').first.select_option(label="Local de sessão E2E")
    apply_modal(admin_page)
    admin_page.get_by_role("button", name="Salvar programação").click()
    expect(admin_page.get_by_text("Programação salva com sucesso.")).to_be_visible(timeout=10_000)


def test_created_axis_can_be_selected_and_persists_after_reload(admin_page: Page) -> None:
    login(admin_page)
    admin_page.get_by_role("button", name="Eixos").click()
    admin_page.get_by_role("button", name="Adicionar eixo").click()
    admin_page.get_by_label("Nome do eixo").fill("Eixo de persistência E2E")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.get_by_text("Eixo de persistência E2E")).to_be_visible()

    admin_page.get_by_role("button", name="Programação").click()
    admin_page.locator("#add-group").click()
    admin_page.get_by_label("Título").fill("Grupo com eixo E2E")
    admin_page.get_by_label("Eixo de conhecimento").select_option(label="Eixo de persistência E2E")
    apply_modal(admin_page)
    admin_page.locator("#save-schedule").click()
    expect(admin_page.get_by_text("Programação salva com sucesso.")).to_be_visible(timeout=10_000)

    admin_page.reload(wait_until="networkidle")
    group = admin_page.locator(".schedule-group").filter(has_text="Grupo com eixo E2E")
    expect(group.get_by_role("button", name=re.compile("Eixo de persistência E2E"))).to_be_visible()


def test_stale_catalog_references_are_visible_but_ids_remain_hidden(admin_page: Page) -> None:
    def add_stale_reference(route) -> None:
        response = route.fetch()
        payload = response.json()
        payload["sections"][0]["groups"][0]["knowledgeAxis"] = "axis-secret"
        payload["sections"][0]["groups"][0]["items"][0]["sessions"][0]["location"] = "loc-secret"
        route.fulfill(response=response, json=payload)

    admin_page.route("**/admin/api/schedule", add_stale_reference)
    login(admin_page)
    group = admin_page.locator(".schedule-group").filter(has_text="Atividades gerais")
    group.get_by_role("button", name=re.compile("Expandir")).click()
    group.get_by_role("button", name="Editar").first.click()
    expect(admin_page.locator('select[name="knowledgeAxis"] option:checked')).to_have_text(
        "Eixo não cadastrado"
    )
    expect(admin_page.locator("body")).not_to_contain_text("axis-secret")
    admin_page.get_by_role("button", name="Fechar").click()
    activity = admin_page.locator(".schedule-activity").filter(has_text="Recepção nos Auditórios")
    activity.get_by_role("button", name="Editar").click()
    expect(admin_page.locator('select[name="location"] option:checked')).to_have_text(
        "Local não cadastrado"
    )
    expect(admin_page.locator("body")).not_to_contain_text("loc-secret")


def test_year_zero_is_rejected_without_put_request(admin_page: Page) -> None:
    login(admin_page)
    requests: list[str] = []
    admin_page.on("request", lambda request: requests.append(request.method + " " + request.url))
    admin_page.locator("#schedule-date").evaluate(
        "(element) => { element.value = '0000-01-01'; element.dispatchEvent(new Event('change', {bubbles: true})); }"
    )
    admin_page.get_by_role("button", name="Salvar programação").click()
    expect(admin_page.get_by_text("Informe uma data válida para o evento.")).to_be_visible()
    assert not any(
        request.startswith("PUT ") and "/admin/api/schedule" in request for request in requests
    )


def test_catalog_crud_rename_reference_conflict_cancel_and_hidden_ids(admin_page: Page) -> None:
    login(admin_page)
    admin_page.get_by_role("button", name="Locais").click()
    admin_page.get_by_role("button", name="Adicionar local").click()
    admin_page.get_by_label("Nome do local").fill("Local E2E")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.get_by_text("Local E2E")).to_be_visible()
    card = admin_page.locator(".catalog-card").filter(has_text="Local E2E")
    card.get_by_role("button", name="Editar").click()
    admin_page.get_by_label("Nome do local").fill("Local E2E renomeado")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.get_by_text("Local E2E renomeado")).to_be_visible()
    admin_page.once("dialog", accept_dialog)
    card = admin_page.locator(".catalog-card").filter(has_text="Local E2E renomeado")
    card.get_by_role("button", name="Excluir").click()
    expect(admin_page.get_by_text("Local excluído com sucesso.")).to_be_visible()

    existing = admin_page.locator(".catalog-card").filter(has_text="Bloco A - Sala 105")
    admin_page.once("dialog", accept_dialog)
    existing.get_by_role("button", name="Excluir").click()
    expect(admin_page.get_by_text("Este registro ainda está em uso.")).to_be_visible()
    expect(
        admin_page.get_by_text("Voz e Ação: conhecendo o curso de Administração")
    ).to_be_visible()
    expect(admin_page.locator("body")).not_to_contain_text("loc-004")
    admin_page.get_by_role("button", name="Adicionar local").click()
    admin_page.get_by_label("Nome do local").fill("Cancelado")
    admin_page.get_by_role("button", name="Fechar").click()
    expect(admin_page.locator("body")).not_to_contain_text("Cancelado")

    admin_page.get_by_role("button", name="Eixos").click()
    admin_page.get_by_role("button", name="Adicionar eixo").click()
    admin_page.get_by_label("Nome do eixo").fill("Eixo E2E")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.get_by_text("Eixo E2E")).to_be_visible()
    axis = admin_page.locator(".catalog-card").filter(has_text="Eixo E2E")
    axis.get_by_role("button", name="Editar").click()
    admin_page.get_by_label("Nome do eixo").fill("Eixo E2E renomeado")
    admin_page.get_by_role("button", name="Salvar").click()
    expect(admin_page.get_by_text("Eixo E2E renomeado")).to_be_visible()
    admin_page.once("dialog", accept_dialog)
    axis = admin_page.locator(".catalog-card").filter(has_text="Eixo E2E renomeado")
    axis.get_by_role("button", name="Excluir").click()
    expect(admin_page.get_by_text("Eixo excluído com sucesso.")).to_be_visible()


def test_axis_in_use_delete_is_safe_and_null_axis_is_visible(admin_page: Page) -> None:
    login(admin_page)
    admin_page.get_by_role("button", name="Eixos").click()
    expect(admin_page.get_by_text("Geral")).to_be_visible()
    admin_page.once("dialog", accept_dialog)
    admin_page.locator(".catalog-card").filter(
        has_text="Administração, negócios e direito"
    ).get_by_role("button", name="Excluir").click()
    expect(admin_page.get_by_text("Este registro ainda está em uso.")).to_be_visible()
    expect(
        admin_page.get_by_text("Voz e Ação: conhecendo o curso de Administração")
    ).to_be_visible()
    expect(admin_page.locator("body")).not_to_contain_text("administracao-negocios-e-direito")
    admin_page.get_by_role("button", name="Programação").click()
    admin_page.get_by_role("button", name="Adicionar grupo").click()
    admin_page.get_by_label("Título").fill("Grupo sem eixo")
    expect(admin_page.get_by_label("Eixo de conhecimento")).to_have_value("")


def test_dismissed_delete_confirmation_preserves_location(admin_page: Page) -> None:
    login(admin_page)
    admin_page.get_by_role("button", name="Locais").click()
    card = admin_page.locator(".catalog-card").filter(has_text="Bloco A - Sala 105")
    admin_page.once("dialog", lambda dialog: dialog.dismiss())
    card.get_by_role("button", name="Excluir").click()
    expect(card).to_be_visible()
    expect(admin_page.get_by_text("Bloco A - Sala 105")).to_be_visible()
