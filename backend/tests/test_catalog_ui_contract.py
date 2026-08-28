import re
import subprocess
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
ADMIN_SCRIPT = PROJECT_ROOT / "static" / "admin" / "admin.js"


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


def run_node_case(case: str) -> None:
    harness = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class FakeElement {
  constructor(id = "") { this.id = id; this.hidden = false; this.innerHTML = ""; this.textContent = ""; this.value = ""; this.dataset = {}; this.isConnected = true; this.listeners = new Map(); this.elements = {namedItem: () => null}; }
  addEventListener(type, callback) { this.listeners.set(type, callback); }
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
