import re
import subprocess
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
ADMIN_SCRIPT = PROJECT_ROOT / "static" / "admin" / "admin.js"
ADMIN_STYLES = PROJECT_ROOT / "static" / "admin" / "admin.css"
ADMIN_DESIGN = PROJECT_ROOT / "DESIGN.md"


def test_location_form_only_asks_for_name(client):
    html = client.get("/admin").text
    fragment = html.split('id="location-form"', 1)[1].split("</form>", 1)[0]
    assert 'name="name"' in fragment
    assert 'name="block"' not in fragment
    assert 'name="room"' not in fragment


def test_axis_form_only_asks_for_name(client):
    html = client.get("/admin").text
    fragment = html.split('id="knowledge-axis-form"', 1)[1].split("</form>", 1)[0]
    assert 'name="name"' in fragment
    assert 'name="id"' not in fragment


def test_catalog_script_exposes_crud_and_safe_in_use_feedback(client):
    script = client.get("/admin/static/admin.js").text
    for function_name in (
        "renderLocations",
        "saveLocation",
        "deleteLocation",
        "renderKnowledgeAxes",
        "saveKnowledgeAxis",
        "deleteKnowledgeAxis",
    ):
        assert re.search(rf"function {function_name}\b", script)
    assert "Este registro ainda está em uso" in script
    assert "detail.message" in script
    assert "escapeHtml" in script


def test_more_action_icon_is_solid_without_changing_other_icons():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    more_css = css.split(".action-icon--more", 1)[1].split("}", 1)[0]
    assert 'name === "more"' in script
    assert "fill: currentColor;" in more_css
    assert "stroke: none;" in more_css
    assert ".action-icon {" in css
    assert "fill: none;" in css.split("\n.action-icon {", 1)[1].split("}", 1)[0]


def run_node_case(case: str) -> None:
    harness = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class FakeElement {
  constructor(id = "") { this.id = id; this.hidden = false; this.innerHTML = ""; this.textContent = ""; this.value = ""; this.dataset = {}; this.isConnected = true; this.listeners = new Map(); this.elements = {namedItem: () => null}; }
      addEventListener(type, callback) { this.listeners.set(type, callback); }
      setAttribute(name, value) { this[name] = value; }
      removeAttribute(name) { delete this[name]; }
  dispatchEvent(event) { return this.listeners.get(event.type)?.(event); }
  append() {}
  querySelector(selector) { return selector === "input, textarea, select" ? new FakeElement("field") : null; }
  querySelectorAll() { return []; }
  closest() { return null; }
  focus() { this.focused = true; }
  showModal() { this.open = true; }
  close() { this.open = false; this.dispatchEvent({type: "close"}); }
}
const elements = new Map();
function elementFor(selector) { if (!elements.has(selector)) elements.set(selector, new FakeElement(selector)); return elements.get(selector); }
const storage = new Map();
let confirmResult = true;
const context = { console, URLSearchParams, Headers, setTimeout, clearTimeout, confirm: () => confirmResult,
  sessionStorage: {getItem: (k) => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,v), removeItem: (k) => storage.delete(k)},
  document: {querySelector: elementFor, createElement: () => new FakeElement(), activeElement: null},
  CSS: {escape: (value) => value}, FormData: class FormData { constructor() {} },
};
context.globalThis = context; vm.createContext(context);
const source = fs.readFileSync(process.argv[2], "utf8");
vm.runInContext(source + `\n;globalThis.editorUnderTest = {state, loadAdminData, renderLocations, renderKnowledgeAxes, openLocationEditor, openKnowledgeAxisEditor, saveLocation, saveKnowledgeAxis, deleteLocation, deleteKnowledgeAxis, handleEditorClick};`, context, {filename: "admin.js"});
const api = context.editorUnderTest;
(async () => { __CASE__ })().catch((error) => { console.error(error); process.exitCode = 1; });
"""
    completed = subprocess.run(
        ["node", "-", str(ADMIN_SCRIPT)],
        input=harness.replace("__CASE__", textwrap.dedent(case)),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_location_create_adopts_canonical_and_sends_name_only():
    run_node_case(
        """
        api.state.locations = [];
        api.renderLocations();
        api.openLocationEditor(null);
        const fields = new Map([["name", {value: "  Auditório novo  ", focus() {}}]]);
        const form = {elements: {namedItem: (name) => fields.get(name)}};
        let request;
        context.fetch = async (path, options) => { request = {path, options}; return {ok: true, status: 201, json: async () => ({id: "loc-secret", name: "Auditório novo"})}; };
        await api.saveLocation(form);
        assert.equal(request.path, "/admin/api/locations");
        assert.equal(request.options.method, "POST");
        assert.deepEqual(JSON.parse(request.options.body), {name: "Auditório novo"});
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), [{id: "loc-secret", name: "Auditório novo"}]);
        assert.equal(elementFor("#editor-content").innerHTML.includes("loc-secret"), false);
        """
    )


def test_axis_group_counts_come_from_schedule_without_exposing_ids():
    run_node_case(
        """
        api.state.schedule = {sections: [{groups: [{knowledgeAxis: "axis-secret"}, {knowledgeAxis: null}, {}]}]};
        api.state.knowledgeAxes = [{id: "axis-secret", name: "Ciência <mar>"}];
        api.renderKnowledgeAxes();
        const html = elementFor("#editor-content").innerHTML;
        assert.match(html, /Ciência &lt;mar&gt;/);
        assert.match(html, /1 grupo/);
        assert.equal(html.includes("axis-secret"), false);
        """
    )


def test_catalog_headers_share_schedule_toolbar_and_primary_action_structure():
    run_node_case(
        r"""
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.renderLocations();
        let html = elementFor("#editor-content").innerHTML;
        assert.match(html, /content-header[\s\S]*toolbar-actions[\s\S]*primary-action[\s\S]*Adicionar sala/);
        assert.match(html, /class="menu card-menu"[\s\S]*data-action="edit-location"[\s\S]*data-action="delete-location"/);
        assert.equal((html.match(/data-action="add-location"/g) || []).length, 1);
        assert.equal((html.match(/data-action="edit-location"/g) || []).length, 1);
        assert.equal((html.match(/data-action="delete-location"/g) || []).length, 1);

        api.state.knowledgeAxes = [{id: "axis-1", name: "Geral"}];
        api.renderKnowledgeAxes();
        html = elementFor("#editor-content").innerHTML;
        assert.match(html, /content-header[\s\S]*toolbar-actions[\s\S]*primary-action[\s\S]*Adicionar eixo/);
        assert.match(html, /class="menu card-menu"[\s\S]*data-action="edit-axis"[\s\S]*data-action="delete-axis"/);
        assert.equal((html.match(/data-action="edit-axis"/g) || []).length, 1);
        assert.equal((html.match(/data-action="delete-axis"/g) || []).length, 1);
        """
    )


def test_secondary_action_uses_established_surface_and_border_tokens():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    secondary_css = css.split(".secondary-action", 1)[1].split("}", 1)[0]
    secondary_hover_css = css.split(".secondary-action:hover", 1)[1].split("}", 1)[0]
    assert "padding: var(--space-2) var(--space-3);" in secondary_css
    assert "border: var(--border-width) solid var(--color-border-strong);" in secondary_css
    assert "border-radius: var(--radius-md);" in secondary_css
    assert "background: var(--color-surface);" in secondary_css
    assert "color: var(--color-text);" in secondary_css
    assert "background: var(--color-surface-selected);" in secondary_hover_css


def test_empty_location_group_is_rendered_after_reload():
    run_node_case(
        """
        api.state.locations = [];
        api.state.locationGroups = [{id: "group-c", name: "Bloco C", category: "blocos"}];
        api.renderLocations();
        const html = elementFor("#editor-content").innerHTML;
        assert.match(html, /Bloco C/);
        assert.match(html, /Nenhuma sala encontrada neste grupo/);
        """
    )


def test_location_groups_start_collapsed_and_explain_interactions():
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Sala 101", category: "blocos", groupId: "group-c", groupName: "Bloco C"}];
        api.state.locationGroups = [{id: "group-c", name: "Bloco C", category: "blocos"}];
        api.renderLocations();
        const html = elementFor("#editor-content").innerHTML;
        assert.match(html, /id="location-group-nav"/);
        assert.match(html, /data-action="select-location-group"/);
        assert.match(html, /aria-current="true"/);
        assert.match(html, /class="menu-trigger card-menu-trigger"[^>]*>[\s\S]*class="action-icon"/);
        assert.equal((html.match(/>Ações<\/span>/g) || []).length, 0);
        assert.equal((html.match(/<details class="location-group"/g) || []).length, 0);
        """
    )


def test_locations_use_group_navigation_and_compact_room_grid():
    run_node_case(
        """
        api.state.locations = [
          {id: "loc-1", name: "Sala 101", roomNumber: "101", category: "blocos", groupId: "group-a", groupName: "Bloco A"},
          {id: "loc-2", name: "Sala 102", roomNumber: "102", category: "blocos", groupId: "group-a", groupName: "Bloco A"},
        ];
        api.state.locationGroups = [
          {id: "group-a", name: "Bloco A", category: "blocos"},
          {id: "group-c", name: "Bloco C", category: "blocos"},
        ];
        api.renderLocations();
        const html = elementFor("#editor-content").innerHTML;
        assert.match(html, /id="location-group-nav"/);
        assert.match(html, /data-action="select-location-group"/);
        assert.match(html, /class="catalog-list location-rooms-grid"/);
        assert.match(html, /id="location-search"/);
        assert.match(html, /class="locations-workspace"[\s\S]*class="location-toolbar"[\s\S]*class="locations-workspace-body"/);
        assert.match(html, /class="location-group-add-card"[\s\S]*>Novo grupo/);
        assert.match(html, /data-action="edit-location-group"/);
        assert.equal((html.match(/class="catalog-card location-room-card"/g) || []).length, 2);
        """
    )


def test_location_group_edit_action_lives_in_selected_panel_header():
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Sala 101", groupId: "group-a", category: "blocos"}];
        api.state.locationGroups = [{id: "group-a", name: "Bloco A", category: "blocos"}];
        api.renderLocations();
        const html = elementFor("#editor-content").innerHTML;
        const nav = html.slice(html.indexOf('id="location-group-nav"'), html.indexOf("</nav>"));
        const panel = html.slice(html.indexOf('class="locations-room-panel"'), html.indexOf("</section>"));
        assert.equal(nav.includes('data-action="edit-location-group"'), false);
        assert.match(panel, /class="secondary-action location-group-edit"/);
        assert.match(panel, /data-action="edit-location-group"/);
        assert.match(panel, /Editar grupo/);
        """
    )


def test_location_search_restores_focus_and_selection_after_filter_render():
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    input_handler = script.split('editorContent.addEventListener("input"', 1)[1].split(
        'editorView.addEventListener("click"', 1
    )[0]
    assert "const selectionStart = searchInput.selectionStart;" in input_handler
    assert "const selectionEnd = searchInput.selectionEnd;" in input_handler
    assert 'document.querySelector("#location-search")' in input_handler
    assert "nextSearchInput?.focus();" in input_handler
    assert "nextSearchInput?.setSelectionRange(selectionStart, selectionEnd);" in input_handler


def test_location_room_menu_escapes_scroll_grid_and_opens_below_trigger():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    room_menu_css = css.split(".location-room-card .menu-panel", 1)[1].split("}", 1)[0]
    assert "position: fixed;" in room_menu_css
    assert "top: var(--location-menu-top);" in room_menu_css
    assert "left: var(--location-menu-left);" in room_menu_css
    assert "function positionLocationMenu" in script
    assert "positionLocationMenu(menu);" in script
    locations_render = script.split("function renderLocations", 1)[1].split("function axisGroupCount", 1)[0]
    assert "initializeMenuDefaultWidth();" not in locations_render


def test_location_group_navigation_reserves_space_for_add_card_before_scrolling_groups():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    nav_css = css.split(".location-group-nav {", 1)[1].split("}", 1)[0]
    list_css = css.split(".location-group-nav-list {", 1)[1].split("}", 1)[0]
    add_css = css.split(".location-group-add-card {", 1)[1].split("}", 1)[0]
    assert "overflow: hidden;" in nav_css
    assert "flex: 1 1 auto;" in list_css
    assert "overflow-y: auto;" in list_css
    assert "min-height: 0;" in list_css
    assert "flex: 0 0 auto;" in add_css


def test_locations_search_and_room_header_share_catalog_card_inset():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    toolbar_css = css.split(".locations-workspace .location-toolbar {", 1)[1].split("}", 1)[0]
    panel_css = css.split(".locations-room-panel {", 1)[1].split("}", 1)[0]
    header_css = css.split(".locations-page-header {", 1)[1].split("}", 1)[0]
    room_header_css = css.split(".locations-room-panel > header {", 1)[1].split("}", 1)[0]
    assert "padding-left: var(--space-1);" in header_css
    assert "padding-right: var(--space-0);" in header_css
    assert "padding-left: var(--space-1);" in room_header_css
    assert "padding-right: var(--space-2);" in room_header_css
    assert "margin: var(--space-4) var(--space-4) var(--space-3);" in toolbar_css
    assert "padding-right: var(--space-2);" in toolbar_css
    assert "padding: var(--panel-padding);" in panel_css
    assert ".locations-room-panel { padding: var(--panel-padding); }" in css


def test_group_navigation_styles_do_not_override_three_dot_menu_alignment():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    assert ".location-group-nav button {" not in css
    assert ".location-group-select {" in css
    assert ".location-group-select:hover" in css
    assert ".menu-item {" in css
    assert "text-align: left;" in css.split(".menu-item {", 1)[1].split("}", 1)[0]


def test_popup_menus_share_intrinsic_width_based_on_the_longest_option():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    menu_css = css.split(".menu-panel {", 1)[1].split("}", 1)[0]
    item_css = css.split(".menu-item {", 1)[1].split("}", 1)[0]
    assert "width: max-content;" in menu_css
    assert "min-width: var(--menu-default-width);" in menu_css
    assert "max-width: calc(100vw - var(--space-8));" in menu_css
    assert "white-space: nowrap;" in item_css
    assert ".toolbar-menu-panel { min-width:" not in css
    assert "min-width: 12rem;" not in css.split(".card-menu .menu-panel", 1)[1].split("}", 1)[0]
    assert "function syncMenuDefaultWidth" not in script
    assert "document.body.append(probe)" not in script
    assert "--menu-default-width: 130.625px;" in css


def test_editor_dialog_uses_rendered_section_width_as_shared_responsive_default():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    dialog_css = css.split("dialog {", 1)[1].split("}", 1)[0]
    assert "--dialog-width-default: 672px;" in css
    assert "width: var(--dialog-width-default);" in dialog_css
    assert "max-width: calc(100vw - var(--space-8));" in dialog_css


def test_danger_action_uses_shared_button_tokens_outside_catalog_cards():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    shared_rule = css.split(".primary-action", 1)[0]
    assert ".danger-action" in shared_rule
    assert ".danger-action:hover" in css


def test_card_menus_have_shared_accessible_design_contract():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    design = ADMIN_DESIGN.read_text(encoding="utf-8")
    menu_css = css.split(".menu-panel {", 1)[1].split("}", 1)[0]
    for source in (css, design):
        assert ".menu" in source
        assert ".menu-trigger" in source
        assert ".menu-panel" in source
        assert "focus-visible" in source
    assert "três pontos" in design
    assert "chevron SVG" in design
    assert "ícone" in design
    assert "background: transparent" in css
    assert "background: var(--color-surface);" in menu_css
    assert "padding-block: var(--space-0);" in menu_css
    assert ".menu-panel .menu-item" in css
    assert "border: 0;" in css.split(".menu-panel .menu-item", 1)[1].split("}", 1)[0]
    assert "box-shadow: var(--shadow-dialog);" in menu_css
    assert "border: var(--border-width) solid var(--color-border);" in menu_css
    assert "border-radius: var(--radius-md);" in menu_css
    assert "border: 0" in css
    assert "pointer-events: auto" in css
    assert "z-index: 20" in css
    assert ".schedule-group {" in css
    assert "overflow: visible" in css
    assert "border-radius: var(--radius-lg) var(--radius-lg) 0 0;" in css
    assert "border-radius: 0 0 var(--radius-lg) var(--radius-lg);" in css


def test_schedule_group_header_aligns_toggle_and_menu_without_leaking_corners():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    header_css = css.split(".group-header {", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: minmax(0, 1fr) auto;" in header_css
    assert "align-items: center;" in header_css


def test_group_toggle_indicator_uses_the_same_explicit_icon_box_as_action_icon():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    indicator_css = css.split(".group-toggle-indicator {", 1)[1].split("}", 1)[0]
    assert "width: 1.15rem;" in indicator_css
    assert "height: 1.15rem;" in indicator_css
    assert ".group-toggle-indicator .action-icon" in css
    indicator_icon_css = css.split(".group-toggle-indicator .action-icon", 1)[1].split("}", 1)[0]
    assert "display: block;" in indicator_icon_css
    assert "line-height: 0;" in indicator_css
    assert ".group-toggle-copy" in css


def test_dropdown_chevron_uses_a_block_svg_inside_an_explicit_box():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    chevron_css = css.split(".menu-chevron {", 1)[1].split("}", 1)[0]
    chevron_icon_css = css.split(".menu-chevron .action-icon", 1)[1].split("}", 1)[0]
    assert "display: grid;" in chevron_css
    assert "place-items: center;" in chevron_css
    assert "width: 1.15rem;" in chevron_css
    assert "height: 1.15rem;" in chevron_css
    assert "line-height: 0;" in chevron_css
    assert "display: block;" in chevron_icon_css


def test_agent_rules_require_research_after_an_ineffective_visual_adjustment():
    agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Se um ajuste visual não produzir o efeito esperado" in agents
    assert "pesquise referências técnicas" in agents


def test_schedule_group_menu_can_escape_its_card_and_stay_in_foreground():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    assert ".menu { position: relative; z-index: 3; }" in css
    assert ".menu-panel {" in css
    assert "z-index: 20;" in css


def test_opening_any_popup_closes_other_open_popups_including_toolbar_menus():
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    toolbar_branch = script.split('const toolbarTrigger = event.target.closest?.("summary.menu-trigger");', 1)[1]
    toolbar_branch = toolbar_branch.split('const trigger = event.target.closest?.("summary.menu-trigger");', 1)[0]
    assert "closeOpenMenus(menu);" in toolbar_branch
    assert "closeOpenMenus(menu);" in script.split('if (trigger) {', 1)[1].split("return;", 1)[0]


def test_group_toggle_uses_only_stateful_accessible_label():
    design = ADMIN_DESIGN.read_text(encoding="utf-8")
    assert "Não exiba “Expandir”/“Recolher”" in design
    assert "Abrir grupo" in design


def test_dropdown_menu_items_define_their_own_vertical_size():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    item_css = css.split(".menu-item {", 1)[1].split("}", 1)[0]
    assert "padding: var(--space-2) var(--space-3);" in item_css
    assert "min-height: var(--control-height);" in item_css


def test_contextual_creation_icons_are_not_generic_plus_icons():
    script = ADMIN_SCRIPT.read_text(encoding="utf-8")
    assert 'collection: ' in script
    assert 'activity: ' in script


def test_crud_hierarchy_is_documented():
    design = ADMIN_DESIGN.read_text(encoding="utf-8")
    assert "Hierarquia CRUD" in design
    assert "Adicionar" in design
    assert "Editar" in design
    assert "Excluir" in design
    assert "última opção" in design


def test_scrollbars_are_hidden_without_disabling_scroll():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    assert "scrollbar-width: none" in css
    assert "::-webkit-scrollbar" in css
    assert "body.modal-open" in css


def test_links_do_not_use_underlines():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    assert "a { text-decoration: none; }" in css


def test_section_add_button_centers_its_icon_inside_the_pill():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    button_css = css.split(".section-add-button {", 1)[1].split("}", 1)[0]
    icon_css = css.split(".section-add-icon {", 1)[1].split("}", 1)[0]
    assert "align-items: center;" in button_css
    assert "justify-content: center;" in button_css
    assert "display: inline-grid;" in button_css
    assert "grid-template-columns: auto auto;" in button_css
    assert "margin: 0;" in button_css
    assert "display: grid;" in icon_css
    assert "place-items: center;" in icon_css
    assert "width: 1rem;" in icon_css
    assert "height: 1rem;" in icon_css


def test_section_add_button_uses_a_pill_shape_for_visible_clarity():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    button_css = css.split(".section-add-button {", 1)[1].split("}", 1)[0]
    assert "border-radius: var(--radius-md);" in button_css
    assert "gap: var(--space-2);" in button_css
    assert "font-size: var(--font-size-sm);" in button_css
    assert "font-weight: var(--font-weight-regular);" in button_css


def test_dialog_save_uses_shared_primary_button_contract_and_stays_right():
    css = ADMIN_STYLES.read_text(encoding="utf-8")
    shared_rule = css.split(".primary-action", 1)[0]
    assert "#modal-apply" in shared_rule
    assert "#modal-apply { margin-left: auto; }" in css


def test_location_rename_refreshes_schedule_and_locations_atomically():
    run_node_case(
        """
        const oldSchedule = {version: 1, eventDate: "2026-10-26", sections: [{id: "secao", title: "Seção", groups: []}]};
        api.state.schedule = oldSchedule;
        api.state.locations = [{id: "loc-secret", name: "Antigo"}];
        api.openLocationEditor(api.state.locations[0]);
        const form = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        const refreshedSchedule = {version: 2, eventDate: "2026-10-26", sections: [{id: "secao", title: "Seção", groups: []}]};
        const refreshedLocations = [{id: "loc-secret", name: "Novo"}];
        const calls = [];
        context.fetch = async (path, options = {}) => {
          calls.push({path, options});
          if (path.includes("loc-secret")) return {ok: true, status: 200, json: async () => ({id: "loc-secret", name: "Novo"})};
          if (path.endsWith("/locations")) return {ok: true, status: 200, json: async () => refreshedLocations};
          return {ok: true, status: 200, json: async () => refreshedSchedule};
        };
        await api.saveLocation(form);
        assert.equal(calls[0].path, "/admin/api/locations/loc-secret");
        assert.equal(calls[0].options.method, "PUT");
        assert.deepEqual(JSON.parse(calls[0].options.body), {name: "Novo"});
        assert.equal(calls.some((call) => call.path === "/admin/api/locations"), true);
        assert.equal(calls.some((call) => call.path === "/admin/api/schedule"), true);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), refreshedSchedule);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), refreshedLocations);
        """
    )


def test_catalog_delete_cancellation_does_not_request_or_mutate():
    run_node_case(
        """
        const location = {id: "loc-secret", name: "Auditório"};
        api.state.locations = [location];
        confirmResult = false;
        let fetchCalls = 0;
        context.fetch = async () => { fetchCalls += 1; };
        await api.deleteLocation(location);
        assert.equal(fetchCalls, 0);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), [location]);
        """
    )


def test_catalog_in_use_error_uses_references_without_detail_message_or_html_execution():
    run_node_case(
        """
        api.state.locations = [{id: "loc-secret", name: "Auditório"}];
        api.openLocationEditor(api.state.locations[0]);
        const form = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        context.fetch = async () => ({ok: false, status: 409, json: async () => ({detail: {
          message: "O local loc-secret ainda está em uso", references: ["<script>alert(1)</script>"]
        }})});
        await api.saveLocation(form);
        const message = elementFor("#editor-message").textContent;
        assert.match(message, /Este registro ainda está em uso/);
        assert.match(message, /&lt;script&gt;/);
        assert.equal(message.includes("loc-secret"), false);
        assert.equal(api.state.locations[0].name, "Auditório");
        """
    )


def test_catalog_401_is_left_to_api_fetch_without_catalog_error():
    run_node_case(
        """
        const location = {id: "loc-secret", name: "Auditório"};
        api.state.locations = [location];
        api.openLocationEditor(location);
        const form = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        storage.set("adminToken", "secret");
        elementFor("#editor-message").textContent = "";
        context.fetch = async () => ({ok: false, status: 401});
        await api.saveLocation(form);
        assert.equal(storage.has("adminToken"), false);
        assert.equal(elementFor("#editor-message").textContent, "");
        assert.match(elementFor("#login-message").textContent, /sessão expirou/);
        assert.equal(api.state.locations[0], location);
        """
    )


def test_axis_crud_adopts_canonical_records_and_uses_private_id_for_paths():
    run_node_case(
        """
        api.state.knowledgeAxes = [];
        api.openKnowledgeAxisEditor(null);
        const createForm = {elements: {namedItem: (name) => name === "name" ? {value: "  Novo eixo  "} : null}};
        let request;
        context.fetch = async (path, options) => {
          request = {path, options};
          return {ok: true, status: 201, json: async () => ({id: "axis-secret", name: "Novo eixo"})};
        };
        await api.saveKnowledgeAxis(createForm);
        assert.equal(request.path, "/admin/api/knowledge-axes");
        assert.equal(request.options.method, "POST");
        assert.deepEqual(JSON.parse(request.options.body), {name: "Novo eixo"});
        const record = api.state.knowledgeAxes[0];
        api.openKnowledgeAxisEditor(record);
        const renameForm = {elements: {namedItem: (name) => name === "name" ? {value: "Eixo atualizado"} : null}};
        context.fetch = async (path, options) => {
          request = {path, options};
          return {ok: true, status: 200, json: async () => ({id: "axis-secret", name: "Eixo atualizado"})};
        };
        await api.saveKnowledgeAxis(renameForm);
        assert.equal(request.path, "/admin/api/knowledge-axes/axis-secret");
        assert.equal(request.options.method, "PUT");
        assert.deepEqual(JSON.parse(request.options.body), {name: "Eixo atualizado"});
        assert.equal(api.state.knowledgeAxes[0].name, "Eixo atualizado");
        context.fetch = async (path, options) => { request = {path, options}; return {ok: true, status: 204}; };
        await api.deleteKnowledgeAxis(api.state.knowledgeAxes[0]);
        assert.equal(request.path, "/admin/api/knowledge-axes/axis-secret");
        assert.equal(request.options.method, "DELETE");
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), []);
        """
    )


def test_catalog_delete_409_without_references_is_still_reported_as_in_use():
    run_node_case(
        """
        const axis = {id: "axis-secret", name: "Geral"};
        api.state.knowledgeAxes = [axis];
        context.fetch = async () => ({ok: false, status: 409, json: async () => ({detail: {
          message: "O eixo axis-secret está em uso", references: []
        }})});
        await api.deleteKnowledgeAxis(axis);
        assert.match(elementFor("#editor-message").textContent, /Este registro ainda está em uso/);
        assert.equal(elementFor("#editor-message").textContent.includes("axis-secret"), false);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
        """
    )


def test_malformed_successful_catalog_response_preserves_state_and_is_safe():
    run_node_case(
        """
        api.state.locations = [];
        api.openLocationEditor(null);
        const createForm = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        context.fetch = async () => ({ok: true, status: 201, json: async () => ({id: "", name: "Novo"})});
        await api.saveLocation(createForm);
        assert.deepEqual(api.state.locations, []);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);

        const axis = {id: "axis-secret", name: "Geral"};
        api.state.knowledgeAxes = [axis];
        api.openKnowledgeAxisEditor(axis);
        const renameForm = {elements: {namedItem: (name) => name === "name" ? {value: "Atualizado"} : null}};
        context.fetch = async () => ({ok: true, status: 200, json: async () => ({id: "axis-secret"})});
        await api.saveKnowledgeAxis(renameForm);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);
        """
    )


def test_malformed_location_refresh_response_preserves_both_catalog_dependencies():
    run_node_case(
        """
        const oldSchedule = {version: 1, eventDate: "2026-10-26", sections: [{id: "secao", title: "Seção", groups: []}]};
        const oldLocations = [{id: "loc-secret", name: "Antigo"}];
        api.state.schedule = oldSchedule;
        api.state.locations = oldLocations;
        api.openLocationEditor(oldLocations[0]);
        const form = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        let call = 0;
        context.fetch = async (path) => {
          call += 1;
          if (call === 1) return {ok: true, status: 200, json: async () => ({id: "loc-secret", name: "Novo"})};
          if (path.endsWith("/locations")) return {ok: true, status: 200, json: async () => [{id: "loc-secret"}]};
        return {ok: true, status: 200, json: async () => ({version: 2, eventDate: "2026-10-26", sections: []})};
        };
        await api.saveLocation(form);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), oldSchedule);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), oldLocations);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);
        """
    )


def test_malformed_schedule_refresh_response_preserves_schedule_and_locations():
    run_node_case(
        """
        const oldSchedule = {version: 1, eventDate: "2026-10-26", sections: [{id: "secao", title: "Seção", groups: []}]};
        const oldLocations = [{id: "loc-secret", name: "Antigo"}];
        api.state.schedule = oldSchedule;
        api.state.locations = oldLocations;
        api.openLocationEditor(oldLocations[0]);
        const form = {elements: {namedItem: (name) => name === "name" ? {value: "Novo"} : null}};
        let call = 0;
        context.fetch = async (path) => {
          call += 1;
          if (call === 1) return {ok: true, status: 200, json: async () => ({id: "loc-secret", name: "Novo"})};
          if (path.endsWith("/locations")) return {ok: true, status: 200, json: async () => oldLocations};
          return {ok: true, status: 200, json: async () => ({sections: [], version: 2})};
        };
        await api.saveLocation(form);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), oldSchedule);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), oldLocations);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);
        """
    )


def test_malformed_schedule_initial_response_preserves_existing_state():
    run_node_case(
        """
        const oldSchedule = {version: 1, eventDate: "2026-10-26", sections: [{id: "secao", title: "Seção", groups: []}]};
        const oldLocations = [{id: "loc-secret", name: "Antigo"}];
        const oldAxes = [{id: "axis-secret", name: "Geral"}];
        api.state.schedule = oldSchedule;
        api.state.locations = oldLocations;
        api.state.knowledgeAxes = oldAxes;
        let call = 0;
        context.fetch = async () => {
          call += 1;
          if (call === 1) return {ok: true, status: 200, json: async () => []};
          if (call === 2) return {ok: true, status: 200, json: async () => oldLocations};
          return {ok: true, status: 200, json: async () => oldAxes};
        };
        try { await api.loadAdminData(); } catch (_error) {}
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), oldSchedule);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), oldLocations);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), oldAxes);
        """
    )


def test_axis_delete_cancellation_preserves_axis_without_request():
    run_node_case(
        """
        const axis = {id: "axis-secret", name: "Geral"};
        api.state.knowledgeAxes = [axis];
        confirmResult = false;
        let fetchCalls = 0;
        context.fetch = async () => { fetchCalls += 1; };
        await api.deleteKnowledgeAxis(axis);
        assert.equal(fetchCalls, 0);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
        """
    )


def test_axis_in_use_error_lists_escaped_references_without_raw_detail():
    run_node_case(
        """
        const axis = {id: "axis-secret", name: "Geral"};
        api.state.knowledgeAxes = [axis];
        context.fetch = async () => ({ok: false, status: 409, json: async () => ({detail: {
          message: "O eixo axis-secret está em uso", references: ["<Atividade> & roteiro"]
        }})});
        await api.deleteKnowledgeAxis(axis);
        const message = elementFor("#editor-message").textContent;
        assert.match(message, /Este registro ainda está em uso/);
        assert.match(message, /&lt;Atividade&gt; &amp; roteiro/);
        assert.equal(message.includes("axis-secret"), false);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
        """
    )


def test_catalog_failures_are_safe_and_preserve_axis_state():
    run_node_case(
        """
        const axis = {id: "axis-secret", name: "Geral"};
        const failures = [
          {status: 404, message: "Falha para axis-secret"},
          {status: 422, message: "Detalhe privado axis-secret"},
          {status: 500, message: "filesystem axis-secret"},
        ];
        for (const failure of failures) {
          api.state.knowledgeAxes = [axis];
          api.openKnowledgeAxisEditor(axis);
          const form = {elements: {namedItem: (name) => name === "name" ? {value: "Atualizado"} : null}};
          context.fetch = async () => ({ok: false, status: failure.status, json: async () => ({detail: {message: failure.message, references: []}})});
          await api.saveKnowledgeAxis(form);
          assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
          assert.equal(elementFor("#editor-message").textContent.includes("axis-secret"), false);
        }
        api.state.knowledgeAxes = [axis];
        api.openKnowledgeAxisEditor(axis);
        context.fetch = async () => { throw new Error("offline axis-secret"); };
        await api.saveKnowledgeAxis({elements: {namedItem: (name) => name === "name" ? {value: "Atualizado"} : null}});
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), [axis]);
        assert.equal(elementFor("#editor-message").textContent.includes("axis-secret"), false);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);
        """
    )
