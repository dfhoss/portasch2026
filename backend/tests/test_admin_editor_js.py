import subprocess
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
ADMIN_SCRIPT = PROJECT_ROOT / "static" / "admin" / "admin.js"


NODE_HARNESS = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(id = "") {
    this.id = id;
    this.hidden = false;
    this.innerHTML = "";
    this.textContent = "";
    this.value = "";
    this.dataset = {};
    this.isConnected = true;
    this.listeners = new Map();
    this.children = [];
    this.elements = {namedItem: () => null};
  }
      addEventListener(type, callback) { this.listeners.set(type, callback); }
      setAttribute(name, value) { this[name] = value; }
      removeAttribute(name) { delete this[name]; }
  dispatchEvent(event) { return this.listeners.get(event.type)?.(event); }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren() {}
  setAttribute() {}
  removeAttribute() {}
  querySelector() { return null; }
  querySelectorAll() { return []; }
  closest() { return null; }
  focus() { this.focused = true; }
  showModal() { this.open = true; }
  close() { this.open = false; this.dispatchEvent({type: "close"}); }
}

const elements = new Map();
function elementFor(selector) {
  if (!elements.has(selector)) elements.set(selector, new FakeElement(selector));
  return elements.get(selector);
}

const storage = new Map();
let confirmResult = true;
const context = {
  console,
  URL,
  URLSearchParams,
  Headers,
  setTimeout,
  clearTimeout,
  confirm: () => confirmResult,
  sessionStorage: {
    getItem: (key) => storage.has(key) ? storage.get(key) : null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  },
  document: {
    querySelector: elementFor,
    createElement: () => new FakeElement(),
    createDocumentFragment: () => new FakeElement(),
  },
  CSS: {escape: (value) => value},
  FormData: class FormData {
    constructor() {}
    get() { return null; }
  },
};
context.globalThis = context;
vm.createContext(context);

const source = fs.readFileSync(process.argv[2], "utf8");
vm.runInContext(source + `\n;globalThis.editorUnderTest = {
  state, loadAdminData, renderEditorSection, renderSections, renderGroups, openActivityEditor,
  addSession, validateDraft, saveSchedule, applyModalDraft, openSectionEditor,
  openGroupEditor, handleEditorClick, showApiError
};`, context, {filename: "admin.js"});

const api = context.editorUnderTest;
const validSchedule = () => ({
  version: 1,
  eventDate: "2026-10-26",
  sections: [{
    id: "secao",
    title: "Seção",
    groups: [{
      id: "grupo",
      title: "Grupo",
      knowledgeAxis: "geral",
      items: [{
        id: "atividade",
        title: "Atividade",
        sessions: [{
          startTime: "09:00",
          endTime: "10:00",
          location: "Auditório",
        }],
      }],
    }],
  }],
});

(async () => {
  __CASE__
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""


def run_node_case(case: str) -> None:
    completed = subprocess.run(
        ["node", "-", str(ADMIN_SCRIPT)],
        input=NODE_HARNESS.replace("__CASE__", textwrap.dedent(case)),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_editor_contains_every_required_control(client):
    """Removing any required editor action from the rendered shell must make this fail."""
    html = client.get("/admin").text
    required = ["add-section", "add-group", "add-activity", "add-session", "save-schedule"]
    for control_id in required:
        assert f'id="{control_id}"' in html


def test_modal_footer_places_activity_actions_and_supports_backdrop_close(client):
    html = client.get("/admin").text
    assert 'id="add-session"' in html
    assert 'id="modal-apply"' in html
    assert 'id="modal-close"' not in html
    assert "Fechar" not in html
    assert '>Salvar<' in html
    script = client.get("/admin/static/admin.js").text
    assert 'editorModal.addEventListener("click"' in script
    assert 'classList?.add("modal-open")' in script
    assert 'classList?.remove("modal-open")' in script


def test_editor_script_uses_portuguese_error_messages(client):
    """Replacing the required user-facing failures with generic or English text must fail."""
    script = client.get("/admin/static/admin.js").text
    assert "O horário final deve ser posterior ao inicial" in script
    assert "Não foi possível salvar a programação" in script


def test_load_admin_data_populates_all_state_and_renders_selected_section():
    """Discarding any API catalog or failing to select/render the loaded schedule must fail."""
    run_node_case(
        """
        const schedule = validSchedule();
        const locations = [{id: "loc-1", name: "Auditório"}];
        const axes = [{id: "geral", name: "Geral"}];
        const responses = [schedule, locations, axes].map((payload) => ({
          ok: true,
          status: 200,
          json: async () => payload,
        }));
        context.fetch = async () => responses.shift();

        await api.loadAdminData();

        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), schedule);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.locations)), locations);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.knowledgeAxes)), axes);
        assert.equal(api.state.selectedSectionId, "secao");
        assert.match(elementFor("#editor-content").innerHTML, /Seção/);
        assert.equal(elementFor("#editor-message").textContent, "");
        """
    )


def test_switching_editor_sections_does_not_create_status_message():
    """Navigation labels are already visible and must not occupy the status region."""
    run_node_case(
        """
        api.state.locations = [];
        api.state.knowledgeAxes = [];
        api.state.schedule = validSchedule();

        api.renderEditorSection("locations");
        assert.equal(elementFor("#editor-message").textContent, "");
        api.renderEditorSection("axes");
        assert.equal(elementFor("#editor-message").textContent, "");
        api.renderEditorSection("schedule");
        assert.equal(elementFor("#editor-message").textContent, "");
        """
    )


def test_validate_draft_accepts_null_catalog_references_and_minute_times():
    """Rejecting supported null references or a valid minute-precision session must fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const schedule = validSchedule();
        schedule.sections[0].groups[0].knowledgeAxis = null;
        schedule.sections[0].groups[0].items[0].sessions[0].location = null;

        assert.deepEqual(Array.from(api.validateDraft(schedule)), []);
        """
    )


def test_validate_draft_accepts_bare_domain_links_and_rejects_incomplete_urls():
    """Links may omit a scheme, but must still contain a usable hostname."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const schedule = validSchedule();
        schedule.sections[0].groups[0].items[0].link = "google.com";
        assert.deepEqual(Array.from(api.validateDraft(schedule)), []);
        schedule.sections[0].groups[0].items[0].link = "https://www.";
        assert.ok(Array.from(api.validateDraft(schedule)).some((item) => item.includes("link")));
        """
    )


def test_validate_draft_rejects_invalid_required_duplicates_references_and_times():
    """Missing required data, duplicate persisted IDs, dangling references, or lax times must fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const schedule = validSchedule();
        schedule.version = 0;
        schedule.eventDate = "2026-02-30";
        schedule.sections[0].title = "   ";
        schedule.sections[0].groups[0].id = "secao";
        schedule.sections[0].groups[0].knowledgeAxis = "inexistente";
        const session = schedule.sections[0].groups[0].items[0].sessions[0];
        session.startTime = "9:00";
        session.endTime = "09:00:30";
        session.location = "Outro local";

        const errors = Array.from(api.validateDraft(schedule));
        assert.ok(errors.some((item) => item.includes("versão")));
        assert.ok(errors.some((item) => item.includes("data")));
        assert.ok(errors.some((item) => item.includes("título")));
        assert.ok(errors.some((item) => item.includes("duplicado")));
        assert.ok(errors.some((item) => item.includes("eixo")));
        assert.ok(errors.some((item) => item.includes("HH:MM")));
        assert.ok(errors.some((item) => item.includes("local")));
        """
    )


def test_validate_draft_never_exposes_raw_persisted_ids():
    """Interpolating a persisted identifier into a visible duplicate error must make this fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const schedule = validSchedule();
        schedule.sections[0].id = "identificador-interno-secreto";
        schedule.sections[0].groups[0].id = "identificador-interno-secreto";

        const errors = Array.from(api.validateDraft(schedule));
        assert.ok(errors.some((item) => item.includes("duplicado")));
        assert.equal(errors.some((item) => item.includes("identificador-interno-secreto")), false);
        """
    )


def test_add_session_changes_only_the_schedule_draft():
    """Sending a session to the API early or failing to append the in-memory draft must fail."""
    run_node_case(
        """
        let fetchCalls = 0;
        context.fetch = async () => { fetchCalls += 1; throw new Error("unexpected fetch"); };
        const activity = {title: "Atividade", sessions: []};

        const session = api.addSession(activity);

        assert.equal(fetchCalls, 0);
        assert.equal(activity.sessions.length, 1);
        assert.equal(activity.sessions[0], session);
        assert.deepEqual(JSON.parse(JSON.stringify(session)), {
          startTime: "", endTime: "", location: null,
        });
        """
    )


def test_save_schedule_sends_idless_draft_and_adopts_canonical_response():
    """Serializing transient IDs or retaining the pre-PUT draft after success must fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const draft = validSchedule();
        delete draft.sections[0].id;
        delete draft.sections[0].groups[0].id;
        delete draft.sections[0].groups[0].items[0].id;
        api.state.schedule = draft;
        const canonical = validSchedule();
        let sent;
        context.fetch = async (path, options) => {
          sent = {path, options, body: JSON.parse(options.body)};
          return {ok: true, status: 200, json: async () => canonical};
        };

        await api.saveSchedule();

        assert.equal(sent.path, "/admin/api/schedule");
        assert.equal(sent.options.method, "PUT");
        assert.equal("id" in sent.body.sections[0], false);
        assert.equal("id" in sent.body.sections[0].groups[0], false);
        assert.equal("id" in sent.body.sections[0].groups[0].items[0], false);
        assert.deepEqual(JSON.parse(JSON.stringify(api.state.schedule)), canonical);
        assert.match(elementFor("#editor-message").textContent, /salva com sucesso/);
        """
    )


def test_save_schedule_preserves_draft_on_validation_http_and_network_failures():
    """Losing edits or replacing them with an error response on any save failure must fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];

        const invalid = validSchedule();
        invalid.eventDate = "";
        api.state.schedule = invalid;
        let fetchCalls = 0;
        context.fetch = async () => { fetchCalls += 1; };
        await api.saveSchedule();
        assert.equal(fetchCalls, 0);
        assert.equal(api.state.schedule, invalid);

        const rejected = validSchedule();
        api.state.schedule = rejected;
        context.fetch = async () => ({
          ok: false,
          status: 500,
          json: async () => ({detail: {message: "Falha controlada", references: []}}),
        });
        await api.saveSchedule();
        assert.equal(api.state.schedule, rejected);
        assert.match(elementFor("#editor-message").textContent, /Falha controlada/);

        const offline = validSchedule();
        api.state.schedule = offline;
        context.fetch = async () => { throw new Error("offline"); };
        await api.saveSchedule();
        assert.equal(api.state.schedule, offline);
        assert.match(
          elementFor("#editor-message").textContent,
          /Não foi possível salvar a programação/,
        );
        """
    )


def test_save_schedule_lets_api_fetch_handle_unauthorized_without_save_error():
    """Showing a misleading save error after apiFetch has already handled a 401 must fail."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const draft = validSchedule();
        api.state.schedule = draft;
        storage.set("adminToken", "secret");
        elementFor("#editor-message").textContent = "";
        context.fetch = async () => ({ok: false, status: 401});

        await api.saveSchedule();

        assert.equal(api.state.schedule, draft);
        assert.equal(storage.has("adminToken"), false);
        assert.equal(elementFor("#editor-message").textContent, "");
        assert.match(elementFor("#login-message").textContent, /sessão expirou/);
        """
    )


def test_apply_restores_focus_to_equivalent_opener_after_rerender():
    """Applying a modal must restore focus even when rerender disconnected its opener."""
    run_node_case(
        """
        api.state.schedule = {version: 1, eventDate: "2026-10-26", sections: []};
        const opener = new FakeElement("add-section");
        const replacement = new FakeElement("add-section-replacement");
        const content = elementFor("#editor-content");
        content.querySelector = () => replacement;
        api.openSectionEditor(null, opener);
        opener.isConnected = false;
        const fields = new Map([
          ["title", {value: "Nova seção"}],
          ["description", {value: ""}],
        ]);
        const form = {
          elements: {namedItem: (name) => fields.get(name)},
          querySelectorAll: () => [],
        };
        elementFor("#modal-content").dispatchEvent({
          type: "submit",
          target: form,
          preventDefault() {},
        });
        assert.equal(replacement.focused, true);
        """
    )


def test_footer_close_restores_focus_to_connected_opener():
    """Closing a modal through its footer must return focus to its opener."""
    run_node_case(
        """
        const opener = new FakeElement("add-section");
        api.openSectionEditor(null, opener);
        elementFor("#editor-modal").close();
        assert.equal(opener.focused, true);
        """
    )


def test_api_error_message_never_exposes_unknown_axis_identifier():
    """Untrusted API detail text must not leak a persisted knowledge-axis identifier."""
    run_node_case(
        """
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        await api.showApiError(
          {json: async () => ({detail: {message: "Falha no eixo eixo-secreto"}})},
          "Não foi possível salvar a programação",
        );
        assert.equal(elementFor("#editor-message").textContent.includes("eixo-secreto"), false);
        assert.match(elementFor("#editor-message").textContent, /Não foi possível salvar/);
        """
    )


def test_unknown_axis_is_preserved_privately_and_rejected_by_validation():
    """Editing a stale axis must retain it for validation instead of converting it to null."""
    run_node_case(
        """
        api.state.locations = [{id: "loc-1", name: "Auditório"}];
        api.state.knowledgeAxes = [{id: "geral", name: "Geral"}];
        const schedule = validSchedule();
        const group = schedule.sections[0].groups[0];
        group.knowledgeAxis = "eixo-secreto";
        api.state.schedule = schedule;
        api.state.selectedSectionId = "secao";
        api.openGroupEditor(group, schedule.sections[0]);
        assert.equal(elementFor("#modal-content").innerHTML.includes("eixo-secreto"), false);
        const staleToken = elementFor("#modal-content").innerHTML.match(
          /<option value="([^"]+)" selected>Eixo não cadastrado<\\/option>/,
        )?.[1];
        assert.ok(staleToken);
        const fields = new Map([
          ["title", {value: "Grupo"}],
          ["knowledgeAxis", {value: staleToken}],
        ]);
        const form = {
          elements: {namedItem: (name) => fields.get(name)},
          querySelectorAll: () => [],
        };
        elementFor("#modal-content").dispatchEvent({
          type: "submit",
          target: form,
          preventDefault() {},
        });
        assert.equal(group.knowledgeAxis, "eixo-secreto");
        assert.ok(Array.from(api.validateDraft(schedule)).some((item) => item.includes("eixo")));
        """
    )


def test_delegated_delete_confirmation_cancellation_preserves_schedule():
    """A delegated delete action must honor cancellation without mutating the draft."""
    run_node_case(
        """
        api.state.schedule = validSchedule();
        api.renderSections();
        const key = elementFor("#editor-content").innerHTML.match(
          /data-action="delete-section" data-key="([^"]+)"/,
        )[1];
        const button = new FakeElement("delete-section");
        button.dataset = {action: "delete-section", key};
        button.closest = () => button;
        confirmResult = false;
        await elementFor("#editor-content").dispatchEvent({type: "click", target: button});
        assert.equal(api.state.schedule.sections.length, 1);
        """
    )
