const loginView = document.querySelector("#login-view");
const editorView = document.querySelector("#editor-view");
const loginForm = document.querySelector("#login-form");
const loginUsername = document.querySelector("#username");
const loginPassword = document.querySelector("#password");
const loginMessage = document.querySelector("#login-message");
const editorMessage = document.querySelector("#editor-message");
const editorToast = document.querySelector("#editor-toast");
const editorMessageClose = document.querySelector("#editor-message-close");
const editorContent = document.querySelector("#editor-content");
const editorModal = document.querySelector("#editor-modal");
const modalTitle = document.querySelector("#modal-title");
const modalContent = document.querySelector("#modal-content");
const addSessionButton = document.querySelector("#add-session");
const modalApplyButton = document.querySelector("#modal-apply");
const ADMIN_VIEW_STATE_KEY = "adminViewState";
const EDITOR_SECTIONS = new Set(["schedule", "locations", "axes", "account"]);

const state = {
  schedule: null,
  locations: [],
  locationGroups: [],
  knowledgeAxes: [],
  selectedSectionId: null,
};

const draftKeys = new WeakMap();
let nextDraftKey = 1;
let expandedGroups = new WeakSet();
let savedScheduleSnapshot = null;
let modalOpener = null;
let modalOpenerTarget = null;
let modalContext = null;
let modalWorkingActivity = null;
const modalReferenceValues = new Map();
let nextStaleReference = 1;
const catalogKeys = new WeakMap();
let nextCatalogKey = 1;
let activeEditorSection = "schedule";
let announceTimer = null;

function readEditorViewState() {
  try {
    const value = JSON.parse(sessionStorage.getItem(ADMIN_VIEW_STATE_KEY) || "null");
    if (!value || typeof value !== "object") return null;
    return {
      section: EDITOR_SECTIONS.has(value.section) ? value.section : "schedule",
      selectedSectionId:
        typeof value.selectedSectionId === "string" ? value.selectedSectionId : null,
      expandedGroupIds: Array.isArray(value.expandedGroupIds)
        ? value.expandedGroupIds.filter((id) => typeof id === "string")
        : [],
      scrollY: Number.isFinite(value.scrollY) && value.scrollY >= 0 ? value.scrollY : 0,
    };
  } catch (_error) {
    return null;
  }
}

function saveEditorViewState() {
  const expandedGroupIds = [];
  for (const section of state.schedule?.sections || []) {
    for (const group of section.groups || []) {
      if (group.id && expandedGroups.has(group)) expandedGroupIds.push(group.id);
    }
  }
  sessionStorage.setItem(
    ADMIN_VIEW_STATE_KEY,
    JSON.stringify({
      section: activeEditorSection,
      selectedSectionId: state.selectedSectionId,
      expandedGroupIds,
      scrollY: Number(globalThis.scrollY) || 0,
    }),
  );
}

function restoreScheduleViewState(viewState) {
  const sections = state.schedule?.sections || [];
  const selectedExists = sections.some((section) => section.id === viewState?.selectedSectionId);
  state.selectedSectionId = selectedExists
    ? viewState.selectedSectionId
    : sections[0]?.id || null;
  const expandedIds = new Set(viewState?.expandedGroupIds || []);
  expandedGroups = new WeakSet();
  for (const section of sections) {
    for (const group of section.groups || []) {
      if (group.id && expandedIds.has(group.id)) expandedGroups.add(group);
    }
  }
}

function clearLoginCredentials() {
  loginUsername.value = "";
  loginPassword.value = "";
}

function showLogin(message = "") {
  editorView.hidden = true;
  loginView.hidden = false;
  clearLoginCredentials();
  loginMessage.textContent = message;
}

function announce(message) {
  editorMessage.textContent = message;
  const isError = /não foi possível|obrigatório|não encontrado|informe|selecione|falha|ainda está|carregando/i.test(message);
  editorToast.classList?.toggle("is-error", isError);
  editorToast.hidden = false;
  if (announceTimer) globalThis.clearTimeout?.(announceTimer);
  if (!isError) {
    announceTimer = globalThis.setTimeout?.(() => {
      editorToast.hidden = true;
    }, 5000);
    announceTimer?.unref?.();
  }
}

function dismissEditorToast() {
  editorToast.hidden = true;
  if (announceTimer) globalThis.clearTimeout?.(announceTimer);
  announceTimer = null;
}

editorToast.hidden = true;
editorMessageClose.addEventListener("click", dismissEditorToast);

function scheduleSnapshot(schedule = state.schedule) {
  return JSON.stringify(schedule || null);
}

function scheduleIsDirty() {
  return savedScheduleSnapshot !== null && scheduleSnapshot() !== savedScheduleSnapshot;
}

function updateScheduleSaveState() {
  const saveButton = editorContent.querySelector?.("#save-schedule");
  const status = editorContent.querySelector?.("#schedule-save-status");
  const warning = editorContent.querySelector?.("#schedule-unsaved-warning");
  const dirty = scheduleIsDirty();
  if (saveButton) saveButton.disabled = !dirty;
  if (status) {
    status.textContent = dirty ? "Alterações não salvas" : "Tudo salvo";
    status.classList?.toggle("is-dirty", dirty);
  }
  if (warning) warning.hidden = !dirty;
}

function markScheduleChanged() {
  updateScheduleSaveState();
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

function actionIcon(name) {
  const paths = {
    more: '<circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>',
    add: '<path d="M12 5v14M5 12h14"/>',
    collection: '<rect x="5" y="5" width="14" height="4" rx="1"/><rect x="5" y="10" width="14" height="4" rx="1"/><rect x="5" y="15" width="14" height="4" rx="1"/>',
    activity: '<path d="M8 6h10M8 12h10M8 18h10"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
    edit: '<path d="m4 16.5-.8 3.3 3.3-.8L18.8 6.7a2.3 2.3 0 0 0-3.3-3.3L4 16.5Z"/><path d="m13.5 5.5 3 3"/>',
    delete: '<path d="M5 7h14M10 11v6M14 11v6M7 7l1 13h8l1-13M9 7V4h6v3"/>',
    chevron: '<path d="M7 9.5 12 14.5 17 9.5"/>',
  };
  return `<svg class="action-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${paths[name] || ""}</svg>`;
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
  if (!location) return "Sem local";
  return state.locations.some((record) => record.name === location)
    ? location
    : "Local não cadastrado";
}

function locationNames(locations) {
  if (!Array.isArray(locations) || !locations.length) return "Sem local";
  return locations.map((location) => locationName(location)).join(" · ");
}

function renderSessions(activity) {
  if (!activity.sessions?.length) return '<span class="secondary-text">Sem horários</span>';
  return activity.sessions
    .map(
      (session) =>
        `<span class="session-chip">${escapeHtml(session.startTime)}–${escapeHtml(
          session.endTime,
        )} · ${escapeHtml(locationNames(session.locations ?? (session.location ? [session.location] : [])))}</span>`,
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
          <details class="menu card-menu">
            <summary class="menu-trigger card-menu-trigger" aria-label="Ações da atividade ${escapeHtml(activity.title || "Atividade sem título")}">${actionIcon("more")}</summary>
            <div class="menu-panel card-menu-panel" role="menu">
              <button class="menu-item" type="button" role="menuitem" data-action="edit-activity" data-key="${key}">${actionIcon("edit")}Editar</button>
              <button class="menu-item danger-action" type="button" role="menuitem" data-action="delete-activity" data-key="${key}">${actionIcon("delete")}Excluir</button>
            </div>
          </details>
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
        <article class="schedule-group ${expanded ? "is-expanded" : "is-collapsed"}">
          <header class="group-header">
            <button class="group-toggle" type="button" data-action="toggle-group" data-key="${key}" aria-expanded="${expanded}" aria-label="${expanded ? "Fechar" : "Abrir"} grupo ${escapeHtml(group.title || "Grupo sem título")}">
              <span class="group-toggle-copy">
                <strong>${escapeHtml(group.title || "Grupo sem título")}</strong>
                <span class="secondary-text">${escapeHtml(axisName(group.knowledgeAxis))}</span>
              </span>
              <span class="group-toggle-indicator">${actionIcon("chevron")}</span>
            </button>
            <details class="menu card-menu">
              <summary class="menu-trigger card-menu-trigger" aria-label="Ações do grupo ${escapeHtml(group.title || "Grupo sem título")}">${actionIcon("more")}</summary>
              <div class="menu-panel card-menu-panel" role="menu">
                <button class="menu-item" type="button" role="menuitem" data-action="add-activity-to-group" data-key="${key}">${actionIcon("activity")}Adicionar atividade</button>
                <button class="menu-item" type="button" role="menuitem" data-action="edit-group" data-key="${key}">${actionIcon("edit")}Editar</button>
                <button class="menu-item danger-action" type="button" role="menuitem" data-action="delete-group" data-key="${key}">${actionIcon("delete")}Excluir</button>
              </div>
            </details>
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

  if (savedScheduleSnapshot === null) savedScheduleSnapshot = scheduleSnapshot();

  const section = selectedSection();
  const sectionButtons = state.schedule.sections
    .map((item) => {
      const key = draftKey(item);
      const current = item === section;
      return `<button type="button" data-action="select-section" data-key="${key}" aria-current="${current}">${escapeHtml(item.title || "Seção sem título")}</button>`;
    })
    .join("");
  const addSectionButton = `<button id="add-section" class="section-add-button" type="button" data-action="add-section" aria-label="Adicionar seção"><span class="section-add-icon">${actionIcon("add")}</span><span>Adicionar seção</span></button>`;

  const sectionPanel = section
    ? `<section class="schedule-section">
        <header class="section-heading">
          <div>
            <h3>${escapeHtml(section.title || "Seção sem título")}</h3>
            ${section.description ? `<p>${escapeHtml(section.description)}</p>` : ""}
          </div>
          <div class="card-actions">
            <details class="menu toolbar-menu section-create-menu">
              <summary class="menu-trigger toolbar-menu-trigger"><span>Adicionar</span><span class="menu-chevron">${actionIcon("chevron")}</span></summary>
              <div class="menu-panel toolbar-menu-panel" role="menu">
                <button class="menu-item" type="button" role="menuitem" data-action="add-group">${actionIcon("collection")}Adicionar grupo</button>
                <button class="menu-item" type="button" role="menuitem" data-action="add-activity">${actionIcon("activity")}Adicionar atividade</button>
              </div>
            </details>
            <details class="menu card-menu">
              <summary class="menu-trigger card-menu-trigger" aria-label="Ações da seção ${escapeHtml(section.title || "Seção sem título")}">${actionIcon("more")}</summary>
              <div class="menu-panel card-menu-panel" role="menu">
                <button class="menu-item" type="button" role="menuitem" data-action="edit-section" data-key="${draftKey(section)}">${actionIcon("edit")}Editar seção</button>
                <button class="menu-item danger-action" type="button" role="menuitem" data-action="delete-section" data-key="${draftKey(section)}">${actionIcon("delete")}Excluir seção</button>
              </div>
            </details>
          </div>
        </header>
        <div class="schedule-groups">${renderGroups(section)}</div>
      </section>`
    : '<p class="empty-state">Adicione uma seção para começar a organizar a agenda.</p>';

  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Agenda do evento</p><h2>Programação</h2></div>
      <div class="toolbar-actions">
        <div class="save-status-group">
          <span id="schedule-save-status" class="save-status" role="status"></span>
          <button id="save-schedule" class="primary-action" type="button" data-action="save-schedule" disabled>Salvar alterações</button>
        </div>
      </div>
    </header>
    <nav id="section-list" class="section-list" aria-label="Seções da programação">${sectionButtons}${addSectionButton}</nav>
    <p id="schedule-unsaved-warning" class="schedule-unsaved-warning" role="alert" hidden>
      Há alterações não salvas. Se você atualizar ou sair da página, o rascunho será descartado.
    </p>
    <div id="schedule-sections">${sectionPanel}</div>`;
  updateScheduleSaveState();
}

function renderLocations() {
  const categoryLabels = {
    blocos: "Blocos",
    laboratorios: "Laboratórios",
    estacionamentos: "Estacionamentos",
    outros: "Outros",
  };
  const cards = state.locations.length || state.locationGroups.length
    ? ["blocos", "laboratorios", "estacionamentos", "outros"]
        .map((category) => {
          const locations = state.locations.filter(
            (location) => (location.category || "outros") === category,
          );
          const groups = state.locationGroups
            .filter((group) => group.category === category)
            .map((group) => ({name: group.name, locations: [], id: group.id}));
          const groupsById = new Map(groups.map((group) => [group.id, group]));
          if (category === "estacionamentos") {
            if (!locations.length && !groups.length) return "";
            return `<details class="location-group" open>
              <summary><h3>${categoryLabels[category]}</h3></summary>
              <div class="catalog-list">${locations.length ? locations.map((location) => locationCard(location)).join("") : '<p class="empty-state">Nenhum local cadastrado.</p>'}</div>
            </details>`;
          }
          const grouped = new Map(groups.map((group) => [group.id, group]));
          locations.forEach((location) => {
            const key = location.groupId && groupsById.has(location.groupId)
              ? location.groupId
              : `ungrouped-${category}`;
            if (!grouped.has(key)) grouped.set(key, {name: location.groupName || "Outros", locations: []});
            grouped.get(key).locations.push(location);
          });
          if (!grouped.size) return "";
          return `<div class="location-groups">${Array.from(grouped.values()).map((group) => `<details class="location-group" open>
            <summary><h3>${escapeHtml(group.name)}</h3></summary>
            <div class="catalog-list">${group.locations.length ? group.locations.map((location) => locationCard(location)).join("") : '<p class="empty-state">Nenhum local cadastrado.</p>'}</div>
          </details>`).join("")}</div>`;
        })
        .join("")
    : '<p class="empty-state">Nenhum local cadastrado.</p>';
  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Catálogo da agenda</p><h2>Locais</h2></div>
      <div class="toolbar-actions">
        <button type="button" data-action="add-location-group">Adicionar grupo</button>
        <button type="button" class="primary-action" data-action="add-location">Adicionar local</button>
      </div>
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
            <details class="menu card-menu">
              <summary class="menu-trigger card-menu-trigger" aria-label="Ações do eixo ${escapeHtml(axis.name)}">${actionIcon("more")}</summary>
              <div class="menu-panel card-menu-panel" role="menu">
                <button class="menu-item" type="button" role="menuitem" data-action="edit-axis" data-key="${key}">${actionIcon("edit")}Editar</button>
                <button class="menu-item danger-action" type="button" role="menuitem" data-action="delete-axis" data-key="${key}">${actionIcon("delete")}Excluir</button>
              </div>
            </details>
          </article>`;
        })
        .join("")
    : '<p class="empty-state">Nenhum eixo cadastrado.</p>';
  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Catálogo da agenda</p><h2>Eixos de conhecimento</h2></div>
      <div class="toolbar-actions">
        <button type="button" class="primary-action" data-action="add-axis">Adicionar eixo</button>
      </div>
    </header>
    <div class="catalog-list" id="knowledge-axes-list">${cards}</div>`;
}

function locationCard(location) {
  const key = catalogKey(location);
  return `<article class="catalog-card">
    <div><strong>${escapeHtml(location.roomNumber ? `Sala ${location.roomNumber}` : location.name)}</strong>
      ${location.roomNumber ? `<span class="secondary-text">Sala/local: ${escapeHtml(location.roomNumber)}</span>` : ""}
      ${location.description ? `<p class="secondary-text">${escapeHtml(location.description)}</p>` : ""}
    </div>
    <div class="card-actions">
      <details class="menu card-menu">
        <summary class="menu-trigger card-menu-trigger" aria-label="Ações do local ${escapeHtml(location.name)}">${actionIcon("more")}</summary>
        <div class="menu-panel card-menu-panel" role="menu">
          <button class="menu-item" type="button" role="menuitem" data-action="edit-location" data-key="${key}">${actionIcon("edit")}Editar</button>
          <button class="menu-item danger-action" type="button" role="menuitem" data-action="delete-location" data-key="${key}">${actionIcon("delete")}Excluir</button>
        </div>
      </details>
    </div>
  </article>`;
}

function renderSettings() {
  editorContent.innerHTML = `
    <header class="content-header">
      <div><p class="eyebrow">Preferências do evento</p><h2>Configurações</h2></div>
      <div class="toolbar-actions">
        <button type="button" class="primary-action" data-action="save-schedule">Salvar configurações</button>
      </div>
    </header>
    <section class="settings-panel" aria-labelledby="settings-title">
      <h3 id="settings-title">Identificação do evento</h3>
      <div class="schedule-metadata">
        <label for="schedule-version">Edição do evento</label>
        <input id="schedule-version" name="version" type="number" min="1" inputmode="numeric" value="${escapeHtml(state.schedule.version)}">
        <label for="schedule-date">Data do evento</label>
        <input id="schedule-date" name="eventDate" type="date" value="${escapeHtml(state.schedule.eventDate)}">
      </div>
    </section>`;
}

function renderEditorSection(section) {
  activeEditorSection = EDITOR_SECTIONS.has(section) ? section : "schedule";
  for (const button of editorView.querySelectorAll("button[data-editor-section]")) {
    if (button.dataset.editorSection === activeEditorSection) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  }
  if (activeEditorSection === "locations") {
    renderLocations();
  } else if (activeEditorSection === "axes") {
    renderKnowledgeAxes();
  } else if (activeEditorSection === "account") {
    renderSettings();
  } else {
    renderSections();
  }
}

function selectOptions(items, selectedValue, emptyLabel, multiple = false) {
  const options = [`<option value="">${escapeHtml(emptyLabel)}</option>`];
  const selectedValues = multiple ? new Set(selectedValue || []) : new Set([selectedValue]);
  let selected = selectedValues.has(null) || selectedValues.has("");
  for (const item of items) {
    const value = emptyLabel === "Sem local" ? item.name : item.id;
    const isSelected = selectedValues.has(value);
    selected ||= isSelected;
    options.push(
      `<option value="${escapeHtml(value)}"${isSelected ? " selected" : ""}>${escapeHtml(item.name)}</option>`,
    );
  }
  if (!selected && selectedValue != null && !multiple) {
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
  modalApplyButton.textContent = "Salvar";
  modalApplyButton.hidden = false;
  modalApplyButton.setAttribute("form", modalContent.querySelector("form")?.id || "");
  document.body?.classList?.add("modal-open");
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
  const locationFields = location
    ? `<label>Grupo
        <select name="groupId">
          <option value="">Sem grupo</option>
          ${state.locationGroups
            .map((item) => `<option value="${escapeHtml(item.id)}"${item.id === record?.groupId ? " selected" : ""}>${escapeHtml(item.name)}</option>`)
            .join("")}
        </select>
      </label>
      <label>Categoria
        <select name="category">
          <option value="blocos"${record?.category === "blocos" ? " selected" : ""}>Blocos</option>
          <option value="laboratorios"${record?.category === "laboratorios" ? " selected" : ""}>Laboratórios</option>
          <option value="estacionamentos"${record?.category === "estacionamentos" ? " selected" : ""}>Estacionamentos</option>
          <option value="outros"${record?.category === "outros" || !record ? " selected" : ""}>Outros</option>
        </select>
      </label>
      <label>Número da sala/local <input name="roomNumber" maxlength="80" value="${escapeHtml(record?.roomNumber)}"></label>
      <label>Descrição <textarea name="description" maxlength="500">${escapeHtml(record?.description)}</textarea></label>`
    : "";
  showModal(
    record ? `Editar ${location ? "local" : "eixo"}` : `Adicionar ${location ? "local" : "eixo"}`,
    `<form id="${formId}" class="editor-form">
      <label for="${fieldId}">${label}</label>
      <input id="${fieldId}" name="name" required maxlength="200" autocomplete="off" value="${escapeHtml(record?.name)}">
      ${locationFields}
    </form>`,
    opener,
  );
}

function openLocationEditor(record = null, opener = null) {
  openCatalogEditor("location", record, opener);
}

function openLocationGroupEditor(opener = null) {
  modalReferenceValues.clear();
  modalContext = {type: "location-group"};
  addSessionButton.hidden = true;
  showModal(
    "Adicionar grupo de locais",
    `<form id="location-group-form" class="editor-form">
      <label>Nome do grupo <input name="name" required maxlength="200"></label>
      <label>Tipo
        <select name="category" required>
          <option value="blocos">Blocos</option>
          <option value="laboratorios">Laboratórios</option>
          <option value="estacionamentos">Estacionamentos</option>
          <option value="outros">Outros</option>
        </select>
      </label>
    </form>`,
    opener,
  );
}

function openKnowledgeAxisEditor(record = null, opener = null) {
  openCatalogEditor("axis", record, opener);
}

function sessionEditorMarkup(session, index) {
  return `<div class="session-editor" data-session-index="${index}">
    <label>Início <input name="startTime" type="time" step="60" required value="${escapeHtml(session.startTime)}"></label>
    <label>Fim <input name="endTime" type="time" step="60" required value="${escapeHtml(session.endTime)}"></label>
    <label>Locais <select name="locations" multiple size="4">${selectOptions(state.locations, session.locations ?? (session.location ? [session.location] : []), "Sem local", true)}</select></label>
    <button class="danger-action" type="button" data-action="delete-session">Excluir horário</button>
  </div>`;
}

function addSession(activity = modalWorkingActivity) {
  if (!activity) return null;
  if (!Array.isArray(activity.sessions)) activity.sessions = [];
  const session = { startTime: "", endTime: "", locations: [] };
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
      <label>Link <input name="link" type="text" inputmode="url" autocomplete="url" value="${escapeHtml(activity?.link)}"></label>
      <div id="session-editor-list" class="session-editor-list">${sessions}</div>
    </form>`,
    opener,
  );
  modalApplyButton.setAttribute("form", "item-editor-form");
}

function formValue(form, name) {
  return form.elements.namedItem(name)?.value.trim() || "";
}

function catalogErrorMessage(response, detail, operation = "save") {
  const references = Array.isArray(detail?.references) ? detail.references : [];
  if (response.status === 409 && operation === "delete") {
    return `Este registro ainda está em uso. ${references.map((reference) => escapeHtml(reference)).join(" · ")}`;
  }
  if (response.status === 409 && references.length) {
    return `Este registro ainda está em uso. ${references.map((reference) => escapeHtml(reference)).join(" · ")}`;
  }
  if (response.status === 409) return "Já existe um registro com esse nome.";
  if (response.status === 404) return "Registro não encontrado.";
  if (response.status === 422) return "Informe um nome válido.";
  if (response.status >= 500) return "Não foi possível salvar as alterações.";
  return "Não foi possível concluir a alteração.";
}

async function showCatalogApiError(
  response,
  fallback = "Não foi possível concluir a alteração.",
  operation = "save",
) {
  let message = fallback;
  try {
    const payload = await response.json();
    message = catalogErrorMessage(response, payload?.detail, operation);
  } catch (_error) {
    // A resposta sem JSON mantém o texto seguro definido pelo editor.
    if (response.status === 409 && operation === "delete") {
      message = "Este registro ainda está em uso.";
    }
  }
  announce(message);
}

function isCanonicalCatalogRecord(record) {
  return (
    record &&
    typeof record.id === "string" &&
    record.id.trim() &&
    typeof record.name === "string" &&
    record.name.trim()
  );
}

function isCanonicalCatalogList(records) {
  return Array.isArray(records) && records.every((record) => isCanonicalCatalogRecord(record));
}

function isCanonicalLocationGroupList(groups) {
  return (
    Array.isArray(groups) &&
    groups.every(
      (group) =>
        group &&
        typeof group === "object" &&
        nonEmptyString(group.id) &&
        nonEmptyString(group.name) &&
        ["blocos", "laboratorios", "estacionamentos", "outros"].includes(group.category),
    )
  );
}

function nonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isCanonicalSchedule(schedule) {
  if (
    !schedule ||
    typeof schedule !== "object" ||
    !Number.isInteger(schedule.version) ||
    schedule.version < 1 ||
    !isValidDate(schedule.eventDate) ||
    !Array.isArray(schedule.sections)
  ) {
    return false;
  }
  return schedule.sections.every((section) => {
    if (
      !section ||
      typeof section !== "object" ||
      !nonEmptyString(section.id) ||
      !nonEmptyString(section.title) ||
      !Array.isArray(section.groups)
    ) {
      return false;
    }
    return section.groups.every((group) => {
      if (
        !group ||
        typeof group !== "object" ||
        !nonEmptyString(group.id) ||
        !nonEmptyString(group.title) ||
        !Array.isArray(group.items)
      ) {
        return false;
      }
      if (group.knowledgeAxis != null && !nonEmptyString(group.knowledgeAxis)) return false;
      return group.items.every((activity) => {
        if (
          !activity ||
          typeof activity !== "object" ||
          !nonEmptyString(activity.id) ||
          !nonEmptyString(activity.title) ||
          !Array.isArray(activity.sessions)
        ) {
          return false;
        }
        return activity.sessions.every(
          (session) =>
            session &&
            typeof session === "object" &&
            isMinuteTime(session.startTime) &&
            isMinuteTime(session.endTime) &&
            session.endTime > session.startTime &&
            Array.isArray(session.locations ?? (session.location ? [session.location] : [])) &&
            (session.locations ?? (session.location ? [session.location] : [])).every((location) => nonEmptyString(location)),
        );
      });
    });
  });
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
  if (!isCanonicalCatalogList(locations) || !isCanonicalSchedule(schedule)) {
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
  const payload = {name};
  if (form.elements.namedItem("category")) {
    payload.category = formValue(form, "category") || "outros";
    payload.groupId = formValue(form, "groupId") || null;
    payload.roomNumber = formValue(form, "roomNumber");
    payload.description = formValue(form, "description") || null;
  }
  try {
    const response = await apiFetch(path, {
      method: record ? "PUT" : "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    if (!response.ok) return showCatalogApiError(response);
    const canonical = await response.json();
    if (!isCanonicalCatalogRecord(canonical)) {
      announce("Não foi possível salvar as alterações.");
      return;
    }
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
    if (!response.ok) return showCatalogApiError(response, "Não foi possível excluir o local.", "delete");
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
    if (!isCanonicalCatalogRecord(canonical)) {
      announce("Não foi possível salvar as alterações.");
      return;
    }
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
    if (!response.ok) return showCatalogApiError(response, "Não foi possível excluir o eixo.", "delete");
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
  if (modalContext.type === "location-group") return saveLocationGroup(form);
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
      locations: Array.from(row.querySelector('[name="locations"]').selectedOptions)
        .map((option) => catalogReferenceValue(option.value))
        .filter(Boolean),
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
  markScheduleChanged();
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

async function saveLocationGroup(form = modalContent.querySelector("#location-group-form")) {
  const name = formValue(form, "name");
  if (!name) return announce("O nome do grupo é obrigatório.");
  try {
    const response = await apiFetch("/admin/api/locations/groups", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name, category: formValue(form, "category")}),
    });
    if (!response.ok) return showCatalogApiError(response);
    const group = await response.json();
    state.locationGroups.push(group);
    renderLocations();
    editorModal.close();
    announce("Grupo criado com sucesso.");
  } catch (error) {
    if (error.message !== "unauthorized") announce("Não foi possível salvar as alterações.");
  }
}

function isValidLink(value) {
  if (!value) return true;
  const candidate = /^[a-z][a-z\d+.-]*:\/\//i.test(value) ? value : `https://${value}`;
  try {
    const parsed = new URL(candidate);
    return ["http:", "https:"].includes(parsed.protocol)
      && Boolean(parsed.hostname)
      && parsed.hostname.split(".").every((label) => label.length > 0);
  } catch {
    return false;
  }
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
        if (!isValidLink(activity.link?.trim() || "")) {
          errors.push(`${activityLabel}: informe um link válido.`);
        }
        (activity.sessions || []).forEach((session, sessionIndex) => {
          const sessionLabel = `${activityLabel}, horário ${sessionIndex + 1}`;
          const startValid = isMinuteTime(session.startTime);
          const endValid = isMinuteTime(session.endTime);
          if (!startValid || !endValid) {
            errors.push(`${sessionLabel}: use horários no formato HH:MM.`);
          } else if (session.endTime <= session.startTime) {
            errors.push(`${sessionLabel}: O horário final deve ser posterior ao inicial.`);
          }
          const locations = session.locations ?? (session.location ? [session.location] : []);
          if (!locations.every((location) => locationNames.has(location))) {
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
    savedScheduleSnapshot = scheduleSnapshot();
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
  const viewState = readEditorViewState();
  const [scheduleResponse, locationsResponse, locationGroupsResponse, knowledgeAxesResponse] =
    await Promise.all([
      apiFetch("/admin/api/schedule"),
      apiFetch("/admin/api/locations"),
      apiFetch("/admin/api/locations/groups"),
      apiFetch("/admin/api/knowledge-axes"),
    ]);
  if (
    !scheduleResponse.ok ||
    !locationsResponse.ok ||
    !locationGroupsResponse.ok ||
    !knowledgeAxesResponse.ok
  ) {
    throw new Error("load-failed");
  }
  const [schedule, locations, locationGroups, knowledgeAxes] = await Promise.all([
    scheduleResponse.json(),
    locationsResponse.json(),
    locationGroupsResponse.json(),
    knowledgeAxesResponse.json(),
  ]);
  if (
    !isCanonicalSchedule(schedule) ||
    !isCanonicalCatalogList(locations) ||
    !isCanonicalLocationGroupList(locationGroups) ||
    !isCanonicalCatalogList(knowledgeAxes)
  ) {
    throw new Error("load-failed");
  }
  state.schedule = schedule;
  savedScheduleSnapshot = scheduleSnapshot();
  state.locations = locations;
  state.locationGroups = locationGroups;
  state.knowledgeAxes = knowledgeAxes;
  restoreScheduleViewState(viewState);
  renderEditorSection(viewState?.section || "schedule");
}

async function showEditor() {
  const identity = await apiFetch("/auth/users/me/");
  if (!identity.ok) {
    showLogin("Não foi possível validar sua sessão.");
    return;
  }
  await loadAdminData();
  loginView.hidden = true;
  editorView.hidden = false;
  const scrollY = readEditorViewState()?.scrollY || 0;
  setTimeout(() => globalThis.scrollTo?.(0, scrollY), 0);
}

function logout() {
  sessionStorage.removeItem("adminToken");
  sessionStorage.removeItem(ADMIN_VIEW_STATE_KEY);
  showLogin("Sessão encerrada.");
}

function confirmDeletion(message) {
  return confirm(message);
}

async function handleEditorClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const { action, key } = button.dataset;

  button.closest(".menu")?.removeAttribute("open");

  if (action === "save-schedule") return saveSchedule();
  if (action === "add-section") {
    if (!state.schedule) {
      announce("A programação ainda está carregando.");
      return;
    }
    return openSectionEditor(null, button);
  }
  if (action === "add-group") return openGroupEditor(null, selectedSection(), button);
  if (action === "add-activity") return openActivityEditor(null, null, button);
  if (action === "add-location") return openLocationEditor(null, button);
  if (action === "add-location-group") return openLocationGroupEditor(button);
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
      saveEditorViewState();
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
    markScheduleChanged();
    saveEditorViewState();
    announce("Seção removida do rascunho.");
    return;
  }

  const groupRecord = findGroupByKey(key);
  if (action === "toggle-group" && groupRecord) {
    if (expandedGroups.has(groupRecord.group)) expandedGroups.delete(groupRecord.group);
    else expandedGroups.add(groupRecord.group);
    renderSections();
    saveEditorViewState();
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
    markScheduleChanged();
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
    markScheduleChanged();
    announce("Atividade removida do rascunho.");
  }
}

function closeOpenMenus(exceptMenu = null) {
  editorContent.querySelectorAll(".menu[open]").forEach((openMenu) => {
    if (openMenu !== exceptMenu) openMenu.removeAttribute("open");
  });
}

editorContent.addEventListener("click", handleEditorClick);
editorContent.addEventListener("click", (event) => {
  const toolbarTrigger = event.target.closest?.("summary.menu-trigger");
  if (toolbarTrigger?.tagName === "SUMMARY") {
    event.preventDefault?.();
    const menu = toolbarTrigger.closest(".menu");
    if (menu) {
      closeOpenMenus(menu);
      if (menu.toggleAttribute) menu.toggleAttribute("open");
      else menu.open = !menu.open;
    }
    return;
  }
  const trigger = event.target.closest?.("summary.menu-trigger");
  const menu = event.target.closest?.(".menu");
  if (trigger) {
    closeOpenMenus(menu);
    return;
  }

  if (!menu) {
    closeOpenMenus();
  }
});
editorContent.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const menu = event.target.closest?.(".menu[open]");
  if (!menu) return;
  menu.removeAttribute("open");
  menu.querySelector(".menu-trigger")?.focus();
});
editorContent.addEventListener("change", (event) => {
  if (!state.schedule) return;
  if (event.target.id === "schedule-version") state.schedule.version = Number(event.target.value);
  if (event.target.id === "schedule-date") state.schedule.eventDate = event.target.value;
  markScheduleChanged();
});

editorView.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-editor-section]");
  if (!button) return;
  const section = button.dataset.editorSection;
  if (EDITOR_SECTIONS.has(section)) {
    renderEditorSection(section);
    saveEditorViewState();
  }
});

globalThis.addEventListener?.("pagehide", () => {
  saveEditorViewState();
  clearLoginCredentials();
});

globalThis.addEventListener?.("beforeunload", (event) => {
  if (!scheduleIsDirty()) return;
  event.preventDefault?.();
  event.returnValue = "";
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
    if (modalOpener.dataset?.action === "add-section") {
      editorContent.querySelector("#add-section")?.focus();
      return;
    }
    const menu = modalOpener.closest?.(".menu");
    if (menu) {
      menu.querySelector("summary")?.focus();
      return;
    }
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
  if (!selector) return;
  const target = editorContent.querySelector(selector);
  if (target?.closest?.(".menu")) {
    const menu = target.closest(".menu");
    menu.querySelector("summary")?.focus();
    setTimeout(() => menu.querySelector("summary")?.focus(), 0);
    return;
  }
  target?.focus();
}

editorModal.addEventListener("close", () => {
  document.body?.classList?.remove("modal-open");
  modalApplyButton.hidden = true;
  modalApplyButton.removeAttribute("form");
  addSessionButton.hidden = true;
  modalContext = null;
  modalWorkingActivity = null;
  restoreModalFocus();
  modalOpener = null;
  modalOpenerTarget = null;
});

editorModal.addEventListener("click", (event) => {
  if (event.target === editorModal) editorModal.close();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginMessage.textContent = "";
  const credentials = new URLSearchParams(new FormData(loginForm));
  clearLoginCredentials();
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
