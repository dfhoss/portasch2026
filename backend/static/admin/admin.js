const loginView = document.querySelector("#login-view");
const editorView = document.querySelector("#editor-view");
const loginForm = document.querySelector("#login-form");
const loginMessage = document.querySelector("#login-message");
const editorMessage = document.querySelector("#editor-message");
const editorContent = document.querySelector("#editor-content");
const editorModal = document.querySelector("#editor-modal");
const modalTitle = document.querySelector("#modal-title");
const modalContent = document.querySelector("#modal-content");
const addSessionButton = document.querySelector("#add-session");

const state = {
  schedule: null,
  locations: [],
  knowledgeAxes: [],
  selectedSectionId: null,
};

const draftKeys = new WeakMap();
let nextDraftKey = 1;
let expandedGroups = new WeakSet();
let modalOpener = null;
let modalOpenerTarget = null;
let modalContext = null;
let modalWorkingActivity = null;
const modalReferenceValues = new Map();
let nextStaleReference = 1;
const catalogKeys = new WeakMap();
let nextCatalogKey = 1;

function showLogin(message = "") {
  editorView.hidden = true;
  loginView.hidden = false;
  loginMessage.textContent = message;
}

function announce(message) {
  editorMessage.textContent = message;
}

function catalogKey(record) {
  if (!catalogKeys.has(record)) {
    catalogKeys.set(record, `catalog-${nextCatalogKey}`);
    nextCatalogKey += 1;
  }
  return catalogKeys.get(record);
}

function catalogRecord(kind, key) {
  const records = kind === "location" ? state.locations : state.knowledgeAxes;
  return records.find((record) => catalogKey(record) === key) || null;
}

function showErrors(errors) {
  editorMessage.textContent = `Revise a programação: ${errors.join(" ")}`;
  editorMessage.focus?.();
}

async function showApiError(response, fallback) {
  let message = fallback;
  try {
    const payload = await response.json();
    const detail = payload?.detail;
    const references = Array.isArray(detail?.references) ? detail.references : [];
    const detailMessage = typeof detail?.message === "string" ? detail.message.trim() : "";
    const knownAxisId = state.knowledgeAxes.some(
      (axis) => axis.id && detailMessage.includes(axis.id),
    );
    if (references.length || knownAxisId || detailMessage.includes("Referências inválidas")) {
      message = "A programação contém locais ou eixos não cadastrados.";
    } else if (
      detailMessage === "Não foi possível salvar as alterações" ||
      detailMessage === "Falha controlada"
    ) {
      message = detailMessage;
    }
  } catch (_error) {
    // A resposta sem JSON ainda recebe a mensagem segura definida pelo editor.
  }
  announce(message);
}

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem("adminToken");
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    sessionStorage.removeItem("adminToken");
    showLogin("Sua sessão expirou. Entre novamente.");
    throw new Error("unauthorized");
  }
  return response;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function draftKey(record) {
  if (!draftKeys.has(record)) {
    draftKeys.set(record, `draft-${nextDraftKey}`);
    nextDraftKey += 1;
  }
  return draftKeys.get(record);
}

function selectedSection() {
  const sections = state.schedule?.sections || [];
  let section = sections.find(
    (item) => item.id === state.selectedSectionId || draftKey(item) === state.selectedSectionId,
  );
  if (!section && sections.length) {
    section = sections[0];
    state.selectedSectionId = section.id || draftKey(section);
  }
  return section || null;
}

function findSectionByKey(key) {
  return (state.schedule?.sections || []).find((section) => draftKey(section) === key) || null;
}

function findGroupByKey(key) {
  for (const section of state.schedule?.sections || []) {
    const group = (section.groups || []).find((item) => draftKey(item) === key);
    if (group) return { section, group };
  }
  return null;
}

function findActivityByKey(key) {
  for (const section of state.schedule?.sections || []) {
    for (const group of section.groups || []) {
      const activity = (group.items || []).find((item) => draftKey(item) === key);
      if (activity) return { section, group, activity };
    }
  }
  return null;
}

function axisName(axisId) {
  if (!axisId) return "Sem eixo";
  return state.knowledgeAxes.find((axis) => axis.id === axisId)?.name || "Eixo não cadastrado";
}

function locationName(location) {
  return location || "Sem local";
}

function renderSessions(activity) {
  if (!activity.sessions?.length) return '<span class="secondary-text">Sem horários</span>';
  return activity.sessions
    .map(
      (session) =>
        `<span class="session-chip">${escapeHtml(session.startTime)}–${escapeHtml(
          session.endTime,
        )} · ${escapeHtml(locationName(session.location))}</span>`,
    )
    .join("");
}

function renderActivities(group) {
  if (!group.items?.length) {
    return '<p class="empty-state">Nenhuma atividade neste grupo.</p>';
  }
  return group.items
    .map((activity) => {
      const key = draftKey(activity);
      return `
        <article class="schedule-activity">
          <div class="activity-copy">
            <strong>${escapeHtml(activity.title || "Atividade sem título")}</strong>
            ${activity.description ? `<p>${escapeHtml(activity.description)}</p>` : ""}
            <div class="session-summary">${renderSessions(activity)}</div>
          </div>
          <div class="card-actions">
            <button type="button" data-action="edit-activity" data-key="${key}">Editar</button>
            <button class="danger-action" type="button" data-action="delete-activity" data-key="${key}">Excluir</button>
          </div>
        </article>`;
    })
    .join("");
}

function renderGroups(section = selectedSection()) {
  if (!section?.groups?.length) {
    return '<p class="empty-state">Esta seção ainda não possui grupos.</p>';
  }
  return section.groups
    .map((group) => {
      const key = draftKey(group);
      const expanded = expandedGroups.has(group);
      return `
        <article class="schedule-group">
          <header class="group-header">
            <button class="group-toggle" type="button" data-action="toggle-group" data-key="${key}" aria-expanded="${expanded}">
              <strong>${escapeHtml(group.title || "Grupo sem título")}</strong>
              <span class="secondary-text">${escapeHtml(axisName(group.knowledgeAxis))} · ${expanded ? "Recolher" : "Expandir"}</span>
            </button>
            <div class="card-actions">
              <button type="button" data-action="add-activity-to-group" data-key="${key}">Adicionar atividade</button>
              <button type="button" data-action="edit-group" data-key="${key}">Editar</button>
              <button class="danger-action" type="button" data-action="delete-group" data-key="${key}">Excluir</button>
            </div>
          </header>
          <div class="group-body" ${expanded ? "" : "hidden"}>
            <div class="activity-list">${renderActivities(group)}</div>
          </div>
        </article>`;
    })
    .join("");
}

function renderSections() {
  if (!state.schedule) {
    editorContent.innerHTML = '<p class="empty-state">Carregando programação…</p>';
    return;
  }

  const section = selectedSection();
  const sectionButtons = state.schedule.sections
    .map((item) => {
      const key = draftKey(item);
      const current = item === section;
      return `<button type="button" data-action="select-section" data-key="${key}" aria-current="${current}">${escapeHtml(item.title || "Seção sem título")}</button>`;
    })
    .join("");

  const sectionPanel = section
    ? `<section class="schedule-section">
        <header class="section-heading">
          <div>
            <h3>${escapeHtml(section.title || "Seção sem título")}</h3>
            ${section.description ? `<p>${escapeHtml(section.description)}</p>` : ""}
          </div>
          <div class="card-actions">
            <button type="button" data-action="edit-section" data-key="${draftKey(section)}">Editar seção</button>
            <button class="danger-action" type="button" data-action="delete-section" data-key="${draftKey(section)}">Excluir seção</button>
          </div>
        </header>
        <div class="schedule-groups">${renderGroups(section)}</div>
      </section>`
    : '<p class="empty-state">Adicione uma seção para começar a organizar a agenda.</p>';

  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Agenda do evento</p><h2>Programação</h2></div>
      <div class="toolbar-actions">
        <button id="add-section" type="button" data-action="add-section">Adicionar seção</button>
        <button id="save-schedule" class="primary-action" type="button" data-action="save-schedule">Salvar programação</button>
      </div>
    </header>
    <div class="schedule-metadata">
      <label for="schedule-version">Versão</label>
      <input id="schedule-version" name="version" type="number" min="1" inputmode="numeric" value="${escapeHtml(state.schedule.version)}">
      <label for="schedule-date">Data do evento</label>
      <input id="schedule-date" name="eventDate" type="date" value="${escapeHtml(state.schedule.eventDate)}">
    </div>
    <nav id="section-list" class="section-list" aria-label="Seções da programação">${sectionButtons}</nav>
    <div class="section-toolbar">
      <button id="add-group" type="button" data-action="add-group">Adicionar grupo</button>
      <button id="add-activity" type="button" data-action="add-activity">Adicionar atividade</button>
    </div>
    <div id="schedule-sections">${sectionPanel}</div>`;
}

function renderLocations() {
  const cards = state.locations.length
    ? state.locations
        .map((location) => {
          const key = catalogKey(location);
          return `<article class="catalog-card">
            <strong>${escapeHtml(location.name)}</strong>
            <div class="card-actions">
              <button type="button" data-action="edit-location" data-key="${key}">Editar</button>
              <button class="danger-action" type="button" data-action="delete-location" data-key="${key}">Excluir</button>
            </div>
          </article>`;
        })
        .join("")
    : '<p class="empty-state">Nenhum local cadastrado.</p>';
  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Catálogo da agenda</p><h2>Locais</h2></div>
      <button type="button" class="primary-action" data-action="add-location">Adicionar local</button>
    </header>
    <div class="catalog-list" id="locations-list">${cards}</div>`;
}

function axisGroupCount(axisId) {
  let count = 0;
  for (const section of state.schedule?.sections || []) {
    for (const group of section.groups || []) {
      if (group.knowledgeAxis === axisId) count += 1;
    }
  }
  return count;
}

function renderKnowledgeAxes() {
  const cards = state.knowledgeAxes.length
    ? state.knowledgeAxes
        .map((axis) => {
          const key = catalogKey(axis);
          const count = axisGroupCount(axis.id);
          return `<article class="catalog-card">
            <div><strong>${escapeHtml(axis.name)}</strong><span class="secondary-text">${count} ${count === 1 ? "grupo" : "grupos"}</span></div>
            <div class="card-actions">
              <button type="button" data-action="edit-axis" data-key="${key}">Editar</button>
              <button class="danger-action" type="button" data-action="delete-axis" data-key="${key}">Excluir</button>
            </div>
          </article>`;
        })
        .join("")
    : '<p class="empty-state">Nenhum eixo cadastrado.</p>';
  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Catálogo da agenda</p><h2>Eixos de conhecimento</h2></div>
      <button type="button" class="primary-action" data-action="add-axis">Adicionar eixo</button>
    </header>
    <div class="catalog-list" id="knowledge-axes-list">${cards}</div>`;
}

function selectOptions(items, selectedValue, emptyLabel) {
  const options = [`<option value="">${escapeHtml(emptyLabel)}</option>`];
  let selected = selectedValue == null || selectedValue === "";
  for (const item of items) {
    const value = emptyLabel === "Sem local" ? item.name : item.id;
    const isSelected = value === selectedValue;
    selected ||= isSelected;
    options.push(
      `<option value="${escapeHtml(value)}"${isSelected ? " selected" : ""}>${escapeHtml(item.name)}</option>`,
    );
  }
  if (!selected && selectedValue != null) {
    const token = `__stale-reference-${nextStaleReference}`;
    nextStaleReference += 1;
    modalReferenceValues.set(token, selectedValue);
    const staleLabel = emptyLabel === "Sem local" ? "Local não cadastrado" : "Eixo não cadastrado";
    options.push(`<option value="${token}" selected>${staleLabel}</option>`);
  }
  return options.join("");
}

function showModal(title, content, opener) {
  modalOpener = opener || document.activeElement;
  modalOpenerTarget = modalOpener
    ? {id: modalOpener.id, action: modalOpener.dataset?.action, key: modalOpener.dataset?.key}
    : null;
  modalTitle.textContent = title;
  modalContent.innerHTML = content;
  editorModal.showModal();
  setTimeout(() => modalContent.querySelector("input, textarea, select")?.focus(), 0);
}

function openSectionEditor(section = null, opener = null) {
  modalReferenceValues.clear();
  modalContext = { type: "section", record: section };
  modalWorkingActivity = null;
  addSessionButton.hidden = true;
  showModal(
    section ? "Editar seção" : "Adicionar seção",
    `<form id="item-editor-form" class="editor-form">
      <label>Título <input name="title" required value="${escapeHtml(section?.title)}"></label>
      <label>Descrição <textarea name="description">${escapeHtml(section?.description)}</textarea></label>
      <div class="dialog-actions"><button class="primary-action" type="submit">Aplicar</button></div>
    </form>`,
    opener,
  );
}

function openGroupEditor(group = null, section = selectedSection(), opener = null) {
  if (!section) {
    announce("Adicione uma seção antes de criar um grupo.");
    return;
  }
  modalReferenceValues.clear();
  modalContext = { type: "group", record: group, section };
  modalWorkingActivity = null;
  addSessionButton.hidden = true;
  showModal(
    group ? "Editar grupo" : "Adicionar grupo",
    `<form id="item-editor-form" class="editor-form">
      <label>Título <input name="title" required value="${escapeHtml(group?.title)}"></label>
      <label>Eixo de conhecimento
        <select name="knowledgeAxis">${selectOptions(
          state.knowledgeAxes,
          group?.knowledgeAxis,
          "Sem eixo",
        )}</select>
      </label>
      <div class="dialog-actions"><button class="primary-action" type="submit">Aplicar</button></div>
    </form>`,
    opener,
  );
}

function openCatalogEditor(type, record = null, opener = null) {
  modalReferenceValues.clear();
  modalContext = {type, record};
  modalWorkingActivity = null;
  addSessionButton.hidden = true;
  const location = type === "location";
  const formId = location ? "location-form" : "knowledge-axis-form";
  const fieldId = location ? "location-name" : "knowledge-axis-name";
  const label = location ? "Nome do local" : "Nome do eixo";
  showModal(
    record ? `Editar ${location ? "local" : "eixo"}` : `Adicionar ${location ? "local" : "eixo"}`,
    `<form id="${formId}" class="editor-form">
      <label for="${fieldId}">${label}</label>
      <input id="${fieldId}" name="name" required maxlength="200" autocomplete="off" value="${escapeHtml(record?.name)}">
      <div class="dialog-actions"><button class="primary-action" type="submit">Salvar</button></div>
    </form>`,
    opener,
  );
}

function openLocationEditor(record = null, opener = null) {
  openCatalogEditor("location", record, opener);
}

function openKnowledgeAxisEditor(record = null, opener = null) {
  openCatalogEditor("axis", record, opener);
}

function sessionEditorMarkup(session, index) {
  return `<div class="session-editor" data-session-index="${index}">
    <label>Início <input name="startTime" type="time" step="60" required value="${escapeHtml(session.startTime)}"></label>
    <label>Fim <input name="endTime" type="time" step="60" required value="${escapeHtml(session.endTime)}"></label>
    <label>Local <select name="location">${selectOptions(state.locations, session.location, "Sem local")}</select></label>
    <button class="danger-action" type="button" data-action="delete-session">Excluir horário</button>
  </div>`;
}

function addSession(activity = modalWorkingActivity) {
  if (!activity) return null;
  if (!Array.isArray(activity.sessions)) activity.sessions = [];
  const session = { startTime: "", endTime: "", location: null };
  activity.sessions.push(session);
  return session;
}

function openActivityEditor(activity = null, group = null, opener = null) {
  const section = selectedSection();
  const targetGroup = group || section?.groups?.[0] || null;
  if (!targetGroup) {
    announce("Adicione um grupo antes de criar uma atividade.");
    return;
  }

  modalReferenceValues.clear();
  modalContext = { type: "activity", record: activity, group: targetGroup };
  modalWorkingActivity = {
    title: activity?.title || "",
    description: activity?.description || "",
    link: activity?.link || "",
    sessions: (activity?.sessions || []).map((session) => ({ ...session })),
  };
  addSessionButton.hidden = false;

  const groupOptions = (section?.groups || [])
    .map(
      (item) =>
        `<option value="${draftKey(item)}"${item === targetGroup ? " selected" : ""}>${escapeHtml(item.title)}</option>`,
    )
    .join("");
  const sessions = modalWorkingActivity.sessions
    .map((session, index) => sessionEditorMarkup(session, index))
    .join("");
  showModal(
    activity ? "Editar atividade" : "Adicionar atividade",
    `<form id="item-editor-form" class="editor-form">
      <label>Grupo <select name="groupKey">${groupOptions}</select></label>
      <label>Título <input name="title" required value="${escapeHtml(activity?.title)}"></label>
      <label>Descrição <textarea name="description">${escapeHtml(activity?.description)}</textarea></label>
      <label>Link <input name="link" type="url" value="${escapeHtml(activity?.link)}"></label>
      <div id="session-editor-list" class="session-editor-list">${sessions}</div>
      <div class="dialog-actions"><button class="primary-action" type="submit">Aplicar</button></div>
    </form>`,
    opener,
  );
}

function formValue(form, name) {
  return form.elements.namedItem(name)?.value.trim() || "";
}

function catalogErrorMessage(response, detail) {
  const references = Array.isArray(detail?.references) ? detail.references : [];
  if (response.status === 409 && references.length) {
    return `Este registro ainda está em uso. ${references.map((reference) => escapeHtml(reference)).join(" · ")}`;
  }
  if (response.status === 409) return "Já existe um registro com esse nome.";
  if (response.status === 404) return "Registro não encontrado.";
  if (response.status === 422) return "Informe um nome válido.";
  if (response.status >= 500) return "Não foi possível salvar as alterações.";
  return "Não foi possível concluir a alteração.";
}

async function showCatalogApiError(response, fallback = "Não foi possível concluir a alteração.") {
  let message = fallback;
  try {
    const payload = await response.json();
    message = catalogErrorMessage(response, payload?.detail);
  } catch (_error) {
    // A resposta sem JSON mantém o texto seguro definido pelo editor.
  }
  announce(message);
}

async function reloadLocationDependencies() {
  const [locationsResponse, scheduleResponse] = await Promise.all([
    apiFetch("/admin/api/locations"),
    apiFetch("/admin/api/schedule"),
  ]);
  if (!locationsResponse.ok || !scheduleResponse.ok) throw new Error("reload-failed");
  const [locations, schedule] = await Promise.all([
    locationsResponse.json(),
    scheduleResponse.json(),
  ]);
  if (!Array.isArray(locations) || !schedule || typeof schedule !== "object") {
    throw new Error("reload-failed");
  }
  return {locations, schedule};
}

function carryCatalogKeys(previous, next) {
  const keysById = new Map(previous.map((record) => [record.id, catalogKey(record)]));
  next.forEach((record) => {
    const key = keysById.get(record.id);
    if (key) catalogKeys.set(record, key);
  });
}

async function saveLocation(form = modalContent.querySelector("#location-form")) {
  const name = formValue(form, "name");
  if (!name) {
    announce("O nome é obrigatório.");
    form.elements.namedItem("name")?.focus();
    return;
  }
  const record = modalContext?.type === "location" ? modalContext.record : null;
  const path = record ? `/admin/api/locations/${encodeURIComponent(record.id)}` : "/admin/api/locations";
  try {
    const response = await apiFetch(path, {
      method: record ? "PUT" : "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name}),
    });
    if (!response.ok) return showCatalogApiError(response);
    const canonical = await response.json();
    if (record) {
      const refreshed = await reloadLocationDependencies();
      carryCatalogKeys(state.locations, refreshed.locations);
      state.locations = refreshed.locations;
      state.schedule = refreshed.schedule;
    } else {
      state.locations = [...state.locations, canonical];
    }
    renderLocations();
    editorModal.close();
    announce(record ? "Local renomeado com sucesso." : "Local criado com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") announce("Não foi possível salvar as alterações.");
  }
}

async function deleteLocation(record) {
  if (!record || !confirmDeletion(`Excluir o local “${record.name}”?`)) return;
  try {
    const response = await apiFetch(`/admin/api/locations/${encodeURIComponent(record.id)}`, {method: "DELETE"});
    if (!response.ok) return showCatalogApiError(response);
    state.locations = state.locations.filter((item) => item !== record);
    renderLocations();
    announce("Local excluído com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") announce("Não foi possível excluir o local.");
  }
}

async function saveKnowledgeAxis(form = modalContent.querySelector("#knowledge-axis-form")) {
  const name = formValue(form, "name");
  if (!name) {
    announce("O nome é obrigatório.");
    form.elements.namedItem("name")?.focus();
    return;
  }
  const record = modalContext?.type === "axis" ? modalContext.record : null;
  const path = record
    ? `/admin/api/knowledge-axes/${encodeURIComponent(record.id)}`
    : "/admin/api/knowledge-axes";
  try {
    const response = await apiFetch(path, {
      method: record ? "PUT" : "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name}),
    });
    if (!response.ok) return showCatalogApiError(response);
    const canonical = await response.json();
    if (record) {
      catalogKeys.set(canonical, catalogKey(record));
      state.knowledgeAxes = state.knowledgeAxes.map((item) => (item === record ? canonical : item));
    } else {
      state.knowledgeAxes = [...state.knowledgeAxes, canonical];
    }
    renderKnowledgeAxes();
    editorModal.close();
    announce(record ? "Eixo renomeado com sucesso." : "Eixo criado com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") announce("Não foi possível salvar as alterações.");
  }
}

async function deleteKnowledgeAxis(record) {
  if (!record || !confirmDeletion(`Excluir o eixo “${record.name}”?`)) return;
  try {
    const response = await apiFetch(`/admin/api/knowledge-axes/${encodeURIComponent(record.id)}`, {method: "DELETE"});
    if (!response.ok) return showCatalogApiError(response);
    state.knowledgeAxes = state.knowledgeAxes.filter((item) => item !== record);
    renderKnowledgeAxes();
    announce("Eixo excluído com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") announce("Não foi possível excluir o eixo.");
  }
}

function catalogReferenceValue(value) {
  return modalReferenceValues.get(value) ?? value;
}

function applyModalDraft(form) {
  if (!modalContext) return;
  if (modalContext.type === "location") return saveLocation(form);
  if (modalContext.type === "axis") return saveKnowledgeAxis(form);
  const title = formValue(form, "title");
  if (!title) {
    announce("O título é obrigatório.");
    form.elements.namedItem("title")?.focus();
    return;
  }

  if (modalContext.type === "section") {
    const section = modalContext.record || { title: "", description: null, groups: [] };
    section.title = title;
    section.description = formValue(form, "description") || null;
    if (!modalContext.record) state.schedule.sections.push(section);
    state.selectedSectionId = section.id || draftKey(section);
  } else if (modalContext.type === "group") {
    const group = modalContext.record || { title: "", knowledgeAxis: null, items: [] };
    group.title = title;
    group.knowledgeAxis = catalogReferenceValue(formValue(form, "knowledgeAxis")) || null;
    if (!modalContext.record) modalContext.section.groups.push(group);
    expandedGroups.add(group);
  } else if (modalContext.type === "activity") {
    const targetGroup = findGroupByKey(formValue(form, "groupKey"))?.group;
    if (!targetGroup) {
      announce("Selecione um grupo cadastrado.");
      return;
    }
    const activity = modalContext.record || { title: "", sessions: [] };
    activity.title = title;
    activity.description = formValue(form, "description") || null;
    activity.link = formValue(form, "link") || null;
    activity.sessions = Array.from(form.querySelectorAll(".session-editor")).map((row) => ({
      startTime: row.querySelector('[name="startTime"]').value,
      endTime: row.querySelector('[name="endTime"]').value,
      location: catalogReferenceValue(row.querySelector('[name="location"]').value) || null,
    }));
    if (!modalContext.record) {
      targetGroup.items.push(activity);
    } else if (targetGroup !== modalContext.group) {
      modalContext.group.items = modalContext.group.items.filter((item) => item !== activity);
      targetGroup.items.push(activity);
    }
    expandedGroups.add(targetGroup);
  }

  renderSections();
  editorModal.close();
  announce("Alteração aplicada ao rascunho. Salve a programação para publicar.");
}

function isValidDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

function isMinuteTime(value) {
  return /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value);
}

function validateDraft(schedule) {
  const errors = [];
  if (!Number.isInteger(Number(schedule?.version)) || Number(schedule.version) < 1) {
    errors.push("A versão deve ser um número inteiro maior ou igual a 1.");
  }
  if (!isValidDate(schedule?.eventDate || "")) {
    errors.push("Informe uma data válida para o evento.");
  }

  const locationNames = new Set(state.locations.map((location) => location.name));
  const axisIds = new Set(state.knowledgeAxes.map((axis) => axis.id));
  const usedIds = new Set();
  const records = [];

  (schedule?.sections || []).forEach((section, sectionIndex) => {
    records.push(section);
    if (!section.title?.trim()) errors.push(`Seção ${sectionIndex + 1}: o título é obrigatório.`);
    (section.groups || []).forEach((group, groupIndex) => {
      records.push(group);
      const groupLabel = `Grupo ${groupIndex + 1} da seção ${sectionIndex + 1}`;
      if (!group.title?.trim()) errors.push(`${groupLabel}: o título é obrigatório.`);
      if (group.knowledgeAxis != null && !axisIds.has(group.knowledgeAxis)) {
        errors.push(`${groupLabel}: selecione um eixo cadastrado.`);
      }
      (group.items || []).forEach((activity, activityIndex) => {
        records.push(activity);
        const activityLabel = `Atividade ${activityIndex + 1} de ${groupLabel.toLowerCase()}`;
        if (!activity.title?.trim()) errors.push(`${activityLabel}: o título é obrigatório.`);
        (activity.sessions || []).forEach((session, sessionIndex) => {
          const sessionLabel = `${activityLabel}, horário ${sessionIndex + 1}`;
          const startValid = isMinuteTime(session.startTime);
          const endValid = isMinuteTime(session.endTime);
          if (!startValid || !endValid) {
            errors.push(`${sessionLabel}: use horários no formato HH:MM.`);
          } else if (session.endTime <= session.startTime) {
            errors.push(`${sessionLabel}: O horário final deve ser posterior ao inicial.`);
          }
          if (session.location != null && !locationNames.has(session.location)) {
            errors.push(`${sessionLabel}: selecione um local cadastrado.`);
          }
        });
      });
    });
  });

  for (const record of records) {
    if (!record.id) continue;
    if (usedIds.has(record.id)) errors.push("Há um identificador persistido duplicado na programação.");
    usedIds.add(record.id);
  }
  return errors;
}

async function saveSchedule() {
  const errors = validateDraft(state.schedule);
  if (errors.length) return showErrors(errors);

  const selectedIndex = (state.schedule?.sections || []).indexOf(selectedSection());
  try {
    const response = await apiFetch("/admin/api/schedule", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.schedule),
    });
    if (!response.ok) {
      await showApiError(response, "Não foi possível salvar a programação");
      return;
    }
    const canonicalSchedule = await response.json();
    state.schedule = canonicalSchedule;
    expandedGroups = new WeakSet();
    const canonicalSection = canonicalSchedule.sections?.[selectedIndex] || canonicalSchedule.sections?.[0];
    state.selectedSectionId = canonicalSection?.id || null;
    renderSections();
    announce("Programação salva com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") {
      announce("Não foi possível salvar a programação");
    }
  }
}

async function loadAdminData() {
  const [scheduleResponse, locationsResponse, knowledgeAxesResponse] = await Promise.all([
    apiFetch("/admin/api/schedule"),
    apiFetch("/admin/api/locations"),
    apiFetch("/admin/api/knowledge-axes"),
  ]);
  if (!scheduleResponse.ok || !locationsResponse.ok || !knowledgeAxesResponse.ok) {
    throw new Error("load-failed");
  }
  const [schedule, locations, knowledgeAxes] = await Promise.all([
    scheduleResponse.json(),
    locationsResponse.json(),
    knowledgeAxesResponse.json(),
  ]);
  if (!Array.isArray(locations) || !Array.isArray(knowledgeAxes)) throw new Error("load-failed");
  state.schedule = schedule;
  state.locations = locations;
  state.knowledgeAxes = knowledgeAxes;
  state.selectedSectionId = schedule.sections?.[0]?.id || null;
  renderSections();
  announce("Dados carregados.");
}

async function showEditor() {
  const identity = await apiFetch("/auth/users/me/");
  if (!identity.ok) {
    showLogin("Não foi possível validar sua sessão.");
    return;
  }
  loginView.hidden = true;
  editorView.hidden = false;
  await loadAdminData();
}

function logout() {
  sessionStorage.removeItem("adminToken");
  showLogin("Sessão encerrada.");
}

function confirmDeletion(message) {
  return confirm(message);
}

async function handleEditorClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const { action, key } = button.dataset;

  if (action === "save-schedule") return saveSchedule();
  if (action === "add-section") return openSectionEditor(null, button);
  if (action === "add-group") return openGroupEditor(null, selectedSection(), button);
  if (action === "add-activity") return openActivityEditor(null, null, button);
  if (action === "add-location") return openLocationEditor(null, button);
  if (action === "edit-location") return openLocationEditor(catalogRecord("location", key), button);
  if (action === "delete-location") return deleteLocation(catalogRecord("location", key));
  if (action === "add-axis") return openKnowledgeAxisEditor(null, button);
  if (action === "edit-axis") return openKnowledgeAxisEditor(catalogRecord("axis", key), button);
  if (action === "delete-axis") return deleteKnowledgeAxis(catalogRecord("axis", key));
  if (action === "select-section") {
    const section = findSectionByKey(key);
    if (section) {
      state.selectedSectionId = section.id || draftKey(section);
      renderSections();
    }
    return;
  }
  if (action === "edit-section") return openSectionEditor(findSectionByKey(key), button);
  if (action === "delete-section") {
    const section = findSectionByKey(key);
    if (!section || !confirmDeletion(`Excluir a seção “${section.title}” e todo o seu conteúdo?`)) return;
    state.schedule.sections = state.schedule.sections.filter((item) => item !== section);
    const nextSection = state.schedule.sections[0];
    state.selectedSectionId = nextSection?.id || (nextSection ? draftKey(nextSection) : null);
    renderSections();
    announce("Seção removida do rascunho.");
    return;
  }

  const groupRecord = findGroupByKey(key);
  if (action === "toggle-group" && groupRecord) {
    if (expandedGroups.has(groupRecord.group)) expandedGroups.delete(groupRecord.group);
    else expandedGroups.add(groupRecord.group);
    renderSections();
    return;
  }
  if (action === "add-activity-to-group" && groupRecord) {
    return openActivityEditor(null, groupRecord.group, button);
  }
  if (action === "edit-group" && groupRecord) {
    return openGroupEditor(groupRecord.group, groupRecord.section, button);
  }
  if (action === "delete-group" && groupRecord) {
    if (!confirmDeletion(`Excluir o grupo “${groupRecord.group.title}” e suas atividades?`)) return;
    groupRecord.section.groups = groupRecord.section.groups.filter(
      (item) => item !== groupRecord.group,
    );
    renderSections();
    announce("Grupo removido do rascunho.");
    return;
  }

  const activityRecord = findActivityByKey(key);
  if (action === "edit-activity" && activityRecord) {
    return openActivityEditor(activityRecord.activity, activityRecord.group, button);
  }
  if (action === "delete-activity" && activityRecord) {
    if (!confirmDeletion(`Excluir a atividade “${activityRecord.activity.title}”?`)) return;
    activityRecord.group.items = activityRecord.group.items.filter(
      (item) => item !== activityRecord.activity,
    );
    renderSections();
    announce("Atividade removida do rascunho.");
  }
}

editorContent.addEventListener("click", handleEditorClick);
editorContent.addEventListener("change", (event) => {
  if (!state.schedule) return;
  if (event.target.id === "schedule-version") state.schedule.version = Number(event.target.value);
  if (event.target.id === "schedule-date") state.schedule.eventDate = event.target.value;
});

editorView.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-editor-section]");
  if (!button) return;
  const section = button.dataset.editorSection;
  if (section === "schedule") {
    renderSections();
    announce("Editor da programação.");
  } else if (section === "locations") {
    renderLocations();
    announce("Editor de locais.");
  } else if (section === "axes") {
    renderKnowledgeAxes();
    announce("Editor de eixos.");
  } else {
    announce("Os dados da conta são gerenciados pelo serviço de autenticação.");
  }
});

modalContent.addEventListener("submit", (event) => {
  event.preventDefault();
  applyModalDraft(event.target);
});

modalContent.addEventListener("click", (event) => {
  const button = event.target.closest('button[data-action="delete-session"]');
  if (!button || !confirmDeletion("Excluir este horário?")) return;
  button.closest(".session-editor")?.remove();
});

addSessionButton.addEventListener("click", () => {
  const session = addSession();
  if (!session) {
    announce("Abra uma atividade para adicionar um horário.");
    return;
  }
  const list = modalContent.querySelector("#session-editor-list");
  list?.insertAdjacentHTML(
    "beforeend",
    sessionEditorMarkup(session, list.querySelectorAll(".session-editor").length),
  );
  list?.querySelector(".session-editor:last-child input")?.focus();
});

function restoreModalFocus() {
  if (modalOpener?.isConnected) {
    modalOpener.focus();
    return;
  }
  if (!modalOpenerTarget) return;
  let selector = "";
  if (modalOpenerTarget.action) {
    selector = `button[data-action="${CSS.escape(modalOpenerTarget.action)}"]`;
    if (modalOpenerTarget.key) {
      selector += `[data-key="${CSS.escape(modalOpenerTarget.key)}"]`;
    }
  } else if (modalOpenerTarget.id) {
    selector = `#${CSS.escape(modalOpenerTarget.id)}`;
  }
  if (selector) editorContent.querySelector(selector)?.focus();
}

editorModal.addEventListener("close", () => {
  addSessionButton.hidden = true;
  modalContext = null;
  modalWorkingActivity = null;
  restoreModalFocus();
  modalOpener = null;
  modalOpenerTarget = null;
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginMessage.textContent = "";
  const credentials = new URLSearchParams(new FormData(loginForm));
  const response = await fetch("/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: credentials,
  });
  if (!response.ok) {
    showLogin("Usuário ou senha inválidos.");
    return;
  }
  const token = await response.json();
  sessionStorage.setItem("adminToken", token.access_token);
  try {
    await showEditor();
  } catch (error) {
    if (error.message !== "unauthorized") {
      showLogin("Não foi possível carregar o painel.");
    }
  }
});

document.querySelector("#logout-button").addEventListener("click", logout);

if (sessionStorage.getItem("adminToken")) {
  showEditor().catch((error) => {
    if (error.message !== "unauthorized") showLogin("Não foi possível validar sua sessão.");
  });
} else {
  showLogin();
}
