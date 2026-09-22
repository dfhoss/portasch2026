/**
 * Agenda pública da UFFS.
 *
 * O site é somente leitura: os quatro documentos vêm da entrega pública do backend
 * e todo conteúdo persistido é inserido no DOM como texto ou atributo.
 */

const SHIFTS = Object.freeze([
  {id: "morning", label: "Manhã", startMinutes: 0, endMinutes: 12 * 60},
  {id: "afternoon", label: "Tarde", startMinutes: 12 * 60, endMinutes: 18 * 60},
  {id: "evening", label: "Noite", startMinutes: 18 * 60, endMinutes: 21 * 60 + 1},
]);

const STATUS_CLASSES = Object.freeze({
  "AO VIVO": "live",
  "EM BREVE": "soon",
  FINALIZADA: "finalized",
});

const STATUS_PRIORITIES = Object.freeze(["AO VIVO", "EM BREVE", "FINALIZADA"]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function publicDataError() {
  return new Error("Falha ao carregar os dados públicos");
}

async function loadPublicDocuments(fetchImpl = fetch, baseURI = document.baseURI) {
  const files = ["schedule.json", "knowledge_axes.json", "locations.json", "settings.json"];
  const responses = await Promise.all(
    files.map((fileName) => fetchImpl(new URL(`/db/${fileName}`, baseURI))),
  );
  if (
    responses.some(
      (response) => !isRecord(response) || response.ok !== true || typeof response.json !== "function",
    )
  ) {
    throw publicDataError();
  }

  const documents = await Promise.all(responses.map((response) => response.json()));
  if (documents.some((document) => !isRecord(document))) throw publicDataError();
  const settings = documents[3];
  if (typeof settings.eventDate !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(settings.eventDate)) {
    throw publicDataError();
  }

  return {
    schedule: documents[0],
    knowledgeAxes: documents[1],
    locations: documents[2],
    settings,
  };
}

function findCompleteProgramSection(document) {
  if (!isRecord(document) || !Array.isArray(document.sections)) return null;
  return document.sections.find(
    (section) => isRecord(section) && section.id === "complete-program",
  ) || null;
}

function createKnowledgeAxisMap(document = {}) {
  const axes = Array.isArray(document.knowledgeAxes) ? document.knowledgeAxes : [];
  return new Map(
    axes
      .filter((axis) => isRecord(axis) && typeof axis.id === "string" && axis.id)
      .map((axis) => [axis.id, axis.name]),
  );
}

function createLocationMap(document = {}) {
  const locations = Array.isArray(document.locations) ? document.locations : [];
  return new Map(
    locations
      .filter((location) => isRecord(location) && typeof location.name === "string")
      .map((location) => [location.name, location.name]),
  );
}

function normalizeSession(session, locationMap) {
  const source = isRecord(session) ? session : {};
  const locations = Array.isArray(source.locations) ? source.locations : [];
  const names = locations
    .filter((location) => typeof location === "string")
    .map((location) => locationMap.get(location) || location.trim())
    .filter(Boolean);
  return {...source, location: names.join(" · ")};
}

function normalizeItem(item, locationMap) {
  const source = isRecord(item) ? item : {};
  return {
    ...source,
    sessions: (Array.isArray(source.sessions) ? source.sessions : []).map((session) =>
      normalizeSession(session, locationMap),
    ),
  };
}

function normalizeGroup(group, locationMap) {
  const source = isRecord(group) ? group : {};
  return {
    ...source,
    items: (Array.isArray(source.items) ? source.items : []).map((item) =>
      normalizeItem(item, locationMap),
    ),
  };
}

function normalizeKnowledgeAxes(document) {
  const axes = Array.isArray(document?.knowledgeAxes) ? document.knowledgeAxes : [];
  return axes
    .filter((axis) => isRecord(axis) && typeof axis.id === "string" && axis.id)
    .map((axis) => ({...axis}));
}

function normalizeScheduleDocument(schedule, axisDocument, locationDocument, settings) {
  const section = findCompleteProgramSection(schedule);
  if (!section || !isRecord(settings) || typeof settings.eventDate !== "string") return null;

  const locationMap = createLocationMap(locationDocument);
  return {
    eventDate: settings.eventDate,
    knowledgeAxes: normalizeKnowledgeAxes(axisDocument),
    section: {
      ...section,
      groups: (Array.isArray(section.groups) ? section.groups : []).map((group) =>
        normalizeGroup(group, locationMap),
      ),
    },
  };
}

function timeToMinutes(value) {
  if (typeof value !== "string") return 0;
  const [hours, minutes] = value.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return 0;
  return hours * 60 + minutes;
}

function formatTime(value) {
  if (typeof value !== "string" || !value) return "";
  const [hours, minutes] = value.split(":");
  const hour = Number.parseInt(hours, 10);
  if (!Number.isFinite(hour)) return value;
  return minutes === "00" || !minutes ? `${hour}h` : `${hour}h${minutes}`;
}

function localDateAndMinutes(now, timeZone) {
  try {
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat("en-GB", {
        timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      })
        .formatToParts(now)
        .filter(({type}) => type !== "literal")
        .map(({type, value}) => [type, value]),
    );

    return {
      date: `${parts.year}-${parts.month}-${parts.day}`,
      minutes: Number(parts.hour) * 60 + Number(parts.minute),
    };
  } catch {
    const localNow = new Date(now);
    return {
      date: localNow.toISOString().slice(0, 10),
      minutes: localNow.getHours() * 60 + localNow.getMinutes(),
    };
  }
}

function sessionInterval(session) {
  return {
    startMinutes: timeToMinutes(session?.startTime),
    endMinutes: timeToMinutes(session?.endTime),
  };
}

function overlapsShift(session, shift) {
  const interval = sessionInterval(session);
  return (
    interval.startMinutes < shift.endMinutes &&
    interval.endMinutes > shift.startMinutes
  );
}

function statusForActivity(sessions, eventDate, now, timeZone = "America/Sao_Paulo") {
  const localNow = localDateAndMinutes(now, timeZone);
  if (localNow.date < eventDate) return "EM BREVE";
  if (localNow.date > eventDate) return "FINALIZADA";

  const validSessions = (Array.isArray(sessions) ? sessions : []).filter(
    (session) => session?.startTime && session?.endTime,
  );
  if (
    validSessions.some((session) => {
      const interval = sessionInterval(session);
      return (
        interval.startMinutes <= localNow.minutes &&
        localNow.minutes < interval.endMinutes
      );
    })
  ) {
    return "AO VIVO";
  }
  if (validSessions.some((session) => timeToMinutes(session.startTime) > localNow.minutes)) {
    return "EM BREVE";
  }
  return validSessions.length ? "FINALIZADA" : "EM BREVE";
}

function makeActivityEntry(sourceGroup, item, sessions, eventDate, now, timeZone) {
  const status = statusForActivity(sessions, eventDate, now, timeZone);
  return {
    item,
    courseTitle: sourceGroup.title,
    sessions,
    status,
    finalized: status === "FINALIZADA",
  };
}

function deriveShiftView(section, eventDate, now, timeZone = "America/Sao_Paulo") {
  return SHIFTS.map((shift) => {
    const courses = [];
    for (const sourceGroup of section?.groups || []) {
      const items = [];
      for (const item of sourceGroup.items || []) {
        const matchingSessions = (item.sessions || []).filter((session) =>
          overlapsShift(session, shift),
        );
        if (!matchingSessions.length) continue;
        items.push(
          makeActivityEntry(sourceGroup, item, matchingSessions, eventDate, now, timeZone),
        );
      }
      if (items.length) {
        courses.push({id: sourceGroup.id, title: sourceGroup.title, items});
      }
    }
    return {id: shift.id, label: shift.label, courses};
  });
}

function axisEntries(knowledgeAxes) {
  const source = Array.isArray(knowledgeAxes)
    ? knowledgeAxes
    : knowledgeAxes?.knowledgeAxes;
  return (Array.isArray(source) ? source : []).filter(
    (axis) => isRecord(axis) && typeof axis.id === "string" && axis.id && axis.name,
  );
}

function createAxisCourse(sourceGroup, eventDate, now, timeZone) {
  return {
    id: sourceGroup.id,
    title: sourceGroup.title,
    items: (sourceGroup.items || []).map((item) =>
      makeActivityEntry(sourceGroup, item, item.sessions || [], eventDate, now, timeZone),
    ),
  };
}

function deriveAxisView(
  section,
  knowledgeAxes,
  eventDate,
  now,
  timeZone = "America/Sao_Paulo",
) {
  const groups = [];
  const sourceGroups = section?.groups || [];
  const axes = axisEntries(knowledgeAxes);
  const knownIds = new Set(axes.map((axis) => axis.id));

  for (const axis of axes) {
    groups.push({
      id: axis.id,
      label: axis.name,
      courses: sourceGroups
        .filter((sourceGroup) => sourceGroup.knowledgeAxis === axis.id)
        .map((sourceGroup) => createAxisCourse(sourceGroup, eventDate, now, timeZone)),
    });
  }

  const ungrouped = sourceGroups
    .filter((sourceGroup) => !knownIds.has(sourceGroup.knowledgeAxis))
    .map((sourceGroup) => createAxisCourse(sourceGroup, eventDate, now, timeZone));
  if (ungrouped.length) groups.push({id: "without-axis", label: "Sem eixo", courses: ungrouped});
  return groups;
}

function appendText(parent, tagName, text) {
  const element = document.createElement(tagName);
  element.textContent = text == null ? "" : String(text);
  parent.appendChild(element);
  return element;
}

function renderSession(parent, session) {
  const element = document.createElement("p");
  element.className = "schedule-session";

  if (session.startTime) {
    const start = document.createElement("time");
    start.setAttribute("datetime", session.startTime);
    start.textContent = formatTime(session.startTime);
    element.appendChild(start);
  }
  if (session.endTime) {
    if (element.childNodes.length) appendText(element, "span", " às ");
    const end = document.createElement("time");
    end.setAttribute("datetime", session.endTime);
    end.textContent = formatTime(session.endTime);
    element.appendChild(end);
  }
  if (session.location) {
    if (element.childNodes.length) element.appendChild(document.createElement("br"));
    const location = appendText(element, "span", session.location);
    location.className = "schedule-session__location";
  }
  parent.appendChild(element);
}

function renderItemCard(entry) {
  const item = entry.item || {};
  const status = entry.status || (entry.finalized ? "FINALIZADA" : "EM BREVE");
  const statusClass = STATUS_CLASSES[status] || "soon";
  const card = document.createElement("li");
  card.className = `schedule-item schedule-view-item schedule-item--${statusClass}`;
  card.setAttribute("data-schedule-item", item.id || "");
  card.setAttribute("data-schedule-status", status);
  card.setAttribute("data-schedule-finalized", String(status === "FINALIZADA"));

  const badge = appendText(card, "span", status);
  badge.className = "schedule-item__status";

  if (entry.courseTitle) {
    const course = appendText(card, "p", entry.courseTitle);
    course.className = "schedule-item__course";
    course.setAttribute("data-schedule-item-course", "");
  }

  const title = appendText(card, "h5", item.title);
  title.className = "schedule-item__title";
  if (item.description) {
    const description = appendText(card, "p", item.description);
    description.className = "schedule-item__description";
  }
  for (const session of entry.sessions || []) renderSession(card, session);

  if (item.link) {
    const link = document.createElement("a");
    link.href = item.link;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.className = "schedule-item__link";
    link.textContent = "Mais informações";
    card.appendChild(link);
  }
  return card;
}

function renderGroups(container, groups) {
  const openIds = new Set(
    Array.from(container.querySelectorAll("details[open][data-schedule-group]")).map((details) =>
      details.getAttribute("data-schedule-group"),
    ),
  );
  container.replaceChildren();
  let headingId = 100;

  for (const group of groups) {
    const details = document.createElement("details");
    details.className = "schedule-view-group";
    details.setAttribute("data-schedule-group", group.id);
    details.open = openIds.has(String(group.id));

    const summary = document.createElement("summary");
    summary.className = "schedule-view-group__summary";
    const heading = appendText(summary, "h3", group.label);
    heading.className = "schedule-group__title";
    heading.id = `schedule-heading-${++headingId}`;
    details.setAttribute("aria-labelledby", heading.id);
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "schedule-view-group__content";
    const courses = Array.isArray(group.courses) ? group.courses : [];
    const totalItems = courses.reduce((total, course) => total + course.items.length, 0);
    const count = appendText(
      heading,
      "span",
      ` ${totalItems} ${totalItems === 1 ? "atividade" : "atividades"}`,
    );
    count.className = "schedule-view-group__count";

    if (!totalItems) {
      const empty = appendText(content, "p", "Nenhuma atividade disponível.");
      empty.className = "schedule-view-group__empty";
    }

    for (const course of courses) {
      const courseSection = document.createElement("section");
      courseSection.className = "schedule-course";
      courseSection.setAttribute("data-schedule-course", course.id || "");
      const courseHeading = appendText(courseSection, "h4", course.title);
      courseHeading.className = "schedule-course__title";
      courseHeading.id = `schedule-heading-${++headingId}`;
      courseSection.setAttribute("aria-labelledby", courseHeading.id);

      const list = document.createElement("ul");
      list.className = "schedule-list";
      for (const entry of course.items || []) list.appendChild(renderItemCard(entry));
      courseSection.appendChild(list);
      content.appendChild(courseSection);
    }
    details.appendChild(content);
    container.appendChild(details);
  }
}

function createViewGroups(sectionData, mode, knowledgeAxes, eventDate, now, timeZone) {
  return mode === "knowledge-axis"
    ? deriveAxisView(sectionData, knowledgeAxes, eventDate, now, timeZone)
    : deriveShiftView(sectionData, eventDate, now, timeZone);
}

function setupViewSelector({
  selectorEl,
  groupsContainerEl,
  sectionData,
  knowledgeAxes = [],
  eventDate,
  timeZone = "America/Sao_Paulo",
  defaultMode = "shift",
}) {
  if (!selectorEl || !groupsContainerEl || !sectionData) return null;

  const buttons = Array.from(selectorEl.querySelectorAll('[role="radio"][data-schedule-view]'));
  let currentMode = defaultMode;

  function updateButtons() {
    buttons.forEach((button) => {
      const active = button.getAttribute("data-schedule-view") === currentMode;
      button.setAttribute("aria-checked", String(active));
      button.tabIndex = active ? 0 : -1;
    });
  }

  function renderMode() {
    const groups = createViewGroups(
      sectionData,
      currentMode,
      knowledgeAxes,
      eventDate,
      new Date(),
      timeZone,
    );
    renderGroups(groupsContainerEl, groups);
  }

  function switchMode(mode) {
    if (!buttons.some((button) => button.getAttribute("data-schedule-view") === mode)) return;
    currentMode = mode;
    updateButtons();
    renderMode();
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => switchMode(button.getAttribute("data-schedule-view")));
    button.addEventListener("keydown", (event) => {
      const index = buttons.indexOf(button);
      let target = null;
      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        target = buttons[(index + 1) % buttons.length];
      } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        target = buttons[(index - 1 + buttons.length) % buttons.length];
      } else if (event.key === "Home") {
        target = buttons[0];
      } else if (event.key === "End") {
        target = buttons[buttons.length - 1];
      }
      if (target) {
        event.preventDefault();
        target.focus();
        switchMode(target.getAttribute("data-schedule-view"));
      }
    });
  });

  updateButtons();
  renderMode();
  return {switchMode, getCurrentMode: () => currentMode};
}

function flattenActivities(section, eventDate, now, timeZone = "America/Sao_Paulo") {
  const activities = [];
  for (const sourceGroup of section?.groups || []) {
    for (const item of sourceGroup.items || []) {
      const sessions = item.sessions || [];
      activities.push({
        id: item.id,
        item,
        courseTitle: sourceGroup.title,
        sessions,
        status: statusForActivity(sessions, eventDate, now, timeZone),
      });
    }
  }
  return activities;
}

function selectCarouselActivities(
  activities,
  eventDate,
  now,
  timeZone = "America/Sao_Paulo",
) {
  const localNow = localDateAndMinutes(now, timeZone);
  const unique = new Set();
  const byPriority = new Map(STATUS_PRIORITIES.map((status) => [status, []]));
  for (const activity of activities || []) {
    if (!activity || unique.has(activity.id)) continue;
    unique.add(activity.id);
    const status = statusForActivity(
      activity.sessions || activity.item?.sessions,
      eventDate,
      now,
      timeZone,
    );
    if (byPriority.has(status)) byPriority.get(status).push(activity);
  }

  let candidates;
  if (localNow.date < eventDate) {
    candidates = byPriority.get("EM BREVE");
  } else if (localNow.date > eventDate) {
    candidates = byPriority.get("FINALIZADA");
  } else {
    candidates = STATUS_PRIORITIES.flatMap((status) => byPriority.get(status));
  }
  return candidates.slice(0, 5);
}

function appendActivityLocation(parent, text) {
  const location = appendText(parent, "p", text);
  location.className = "card-location";
}

function activityTimeText(sessions) {
  return (sessions || [])
    .map((session) => {
      const start = formatTime(session.startTime);
      const end = formatTime(session.endTime);
      return end ? `${start} – ${end}` : start;
    })
    .filter(Boolean)
    .join(" · ");
}

function renderCarouselCard(activity) {
  const item = activity.item || activity;
  const card = document.createElement("article");
  card.className = "activity-card";
  card.setAttribute("data-schedule-item", item.id || activity.id || "");
  card.setAttribute("data-schedule-status", activity.status || "EM BREVE");

  const top = document.createElement("div");
  top.className = "card-top";
  const status = appendText(top, "span", activity.status || "EM BREVE");
  status.className = `status-badge ${STATUS_CLASSES[activity.status] || "soon"}`;
  const time = appendText(top, "span", activityTimeText(activity.sessions || item.sessions));
  time.className = "card-time";
  card.appendChild(top);

  const title = appendText(card, "h3", item.title);
  title.className = "card-title";
  const locations = (activity.sessions || item.sessions || [])
    .map((session) => session.location)
    .filter(Boolean)
    .filter((location, index, values) => values.indexOf(location) === index)
    .join(" · ");
  if (locations) appendActivityLocation(card, locations);
  if (item.description) {
    const description = appendText(card, "p", item.description);
    description.className = "card-desc";
  }
  if (activity.courseTitle) {
    const footer = document.createElement("div");
    footer.className = "card-footer";
    const tag = appendText(footer, "span", activity.courseTitle);
    tag.className = "card-tag";
    card.appendChild(footer);
  }
  return card;
}

function renderCarousel(track, activities) {
  if (!track) return;
  track.replaceChildren(...activities.map((activity) => renderCarouselCard(activity)));
}

async function initCompleteProgram() {
  const section = document.getElementById("complete-program");
  const root = section?.querySelector("[data-schedule-root]");
  const selector = section?.querySelector(".schedule-view-selector");
  const groupsContainer = section?.querySelector(".schedule-view-groups");
  const track = document.querySelector(".carousel-track");
  if (!section || !root || !groupsContainer) return;

  root.setAttribute("aria-busy", "true");
  groupsContainer.replaceChildren();
  if (track) track.replaceChildren();

  try {
    const documents = await loadPublicDocuments(fetch, document.baseURI);
    const normalized = normalizeScheduleDocument(
      documents.schedule,
      documents.knowledgeAxes,
      documents.locations,
      documents.settings,
    );
    if (!normalized) throw publicDataError();

    const selectedButton = selector?.querySelector('[role="radio"][aria-checked="true"]');
    setupViewSelector({
      selectorEl: selector,
      groupsContainerEl: groupsContainer,
      sectionData: normalized.section,
      knowledgeAxes: normalized.knowledgeAxes,
      eventDate: normalized.eventDate,
      defaultMode: selectedButton?.getAttribute("data-schedule-view") || "shift",
    });

    const now = new Date();
    const activities = selectCarouselActivities(
      flattenActivities(normalized.section, normalized.eventDate, now),
      normalized.eventDate,
      now,
    );
    renderCarousel(track, activities);
    root.setAttribute("aria-busy", "false");
    if (track && typeof window.initializeCarousel === "function") window.initializeCarousel();
  } catch {
    root.setAttribute("aria-busy", "false");
  }
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => void initCompleteProgram(), {once: true});
  } else {
    void initCompleteProgram();
  }
}

const publicScheduleApi = {
  SHIFTS,
  loadPublicDocuments,
  findCompleteProgramSection,
  createKnowledgeAxisMap,
  createLocationMap,
  normalizeScheduleDocument,
  statusForActivity,
  deriveShiftView,
  deriveAxisView,
  flattenActivities,
  selectCarouselActivities,
  renderGroups,
  setupViewSelector,
  initCompleteProgram,
};

if (typeof window !== "undefined") window.CompleteProgram = publicScheduleApi;
if (typeof module !== "undefined" && module.exports) module.exports = publicScheduleApi;
