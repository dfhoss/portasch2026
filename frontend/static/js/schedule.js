/**
 * Complete Program Schedule - Interactive Component Script
 * Portas Abertas UFFS - fonte de dados: ../backend/db/schedule.json
 */

const SHIFTS = Object.freeze([
  { id: "morning", label: "Manhã", startMinutes: 0, endMinutes: 12 * 60 },
  { id: "afternoon", label: "Tarde", startMinutes: 12 * 60, endMinutes: 18 * 60 },
  { id: "evening", label: "Noite", startMinutes: 18 * 60, endMinutes: 21 * 60 + 1 },
]);

function normalizeScheduleDocument(document, axisDocument = {}, locationDocument = {}) {
  const section = (document.sections || []).find(
    (candidate) => candidate.id === "complete-program",
  );
  if (!section) return null;

  const locationNames = new Map(
    (locationDocument.locations || []).map((location) => [location.name, location.name]),
  );
  const knowledgeAxes = (axisDocument.knowledgeAxes || []).map((axis) => [axis.id, axis.name]);

  return {
    eventDate: document.eventDate,
    knowledgeAxes,
    section: {
      ...section,
      groups: section.groups.map((group) => ({
        ...group,
        items: group.items.map((item) => ({
          ...item,
          sessions: item.sessions.map((session) => ({
            ...session,
            location: (session.locations || [])
              .map((location) => locationNames.get(location) || location)
              .join(" · "),
          })),
        })),
      })),
    },
  };
}

function timeToMinutes(value) {
  if (!value) return 0;
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + (minutes || 0);
}

function formatTime(value) {
  if (!value) return "";
  const [hours, minutes] = value.split(":");
  const hour = Number.parseInt(hours, 10);
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
        .filter(({ type }) => type !== "literal")
        .map(({ type, value }) => [type, value]),
    );

    return {
      date: `${parts.year}-${parts.month}-${parts.day}`,
      minutes: Number(parts.hour) * 60 + Number(parts.minute),
    };
  } catch {
    return {
      date: new Date().toISOString().slice(0, 10),
      minutes: now.getHours() * 60 + now.getMinutes(),
    };
  }
}

function sessionInterval(session) {
  return {
    startMinutes: timeToMinutes(session.startTime),
    endMinutes: timeToMinutes(session.endTime || "21:00"),
  };
}

function overlapsShift(session, shift) {
  const interval = sessionInterval(session);
  return (
    interval.startMinutes < shift.endMinutes &&
    interval.endMinutes > shift.startMinutes
  );
}

function isFinalized(sessions, eventDate, localNow) {
  if (!eventDate || localNow.date < eventDate) return false;
  if (localNow.date > eventDate || localNow.minutes >= 21 * 60) return true;
  if (!sessions || sessions.length === 0) return false;
  return sessions.every(
    (session) =>
      session.endTime && timeToMinutes(session.endTime) <= localNow.minutes,
  );
}

function appendText(parent, tagName, text) {
  const el = document.createElement(tagName);
  el.textContent = text;
  parent.appendChild(el);
  return el;
}

function renderSession(parent, session) {
  const p = document.createElement("p");
  p.classList.add("schedule-session");

  if (session.startTime) {
    const start = document.createElement("time");
    start.setAttribute("datetime", session.startTime);
    start.textContent = formatTime(session.startTime);
    p.appendChild(start);
  }

  if (session.endTime) {
    if (p.childNodes.length) appendText(p, "span", " às ");
    const end = document.createElement("time");
    end.setAttribute("datetime", session.endTime);
    end.textContent = formatTime(session.endTime);
    p.appendChild(end);
  }

  if (session.location) {
    if (p.childNodes.length) p.appendChild(document.createElement("br"));
    const loc = document.createElement("span");
    loc.classList.add("schedule-session__location");
    loc.textContent = session.location;
    p.appendChild(loc);
  }

  parent.appendChild(p);
}

function renderItemCard(item, courseTitle, sessions, finalized, idPrefix) {
  const li = document.createElement("li");
  li.className = "schedule-item schedule-view-item";
  if (finalized) li.classList.add("schedule-item--finalized");
  li.setAttribute("data-schedule-item", item.id);
  li.setAttribute("data-schedule-finalized", String(finalized));

  if (finalized) {
    const badge = appendText(li, "span", "Finalizado");
    badge.className = "schedule-item__status";
  }

  if (courseTitle) {
    const courseEl = appendText(li, "p", courseTitle);
    courseEl.className = "schedule-item__course";
    courseEl.setAttribute("data-schedule-item-course", "");
  }

  const title = appendText(li, "h5", item.title);
  title.className = "schedule-item__title";

  if (item.description) {
    const desc = appendText(li, "p", item.description);
    desc.className = "schedule-item__description";
  }

  for (const session of sessions) {
    renderSession(li, session);
  }

  if (item.link) {
    const a = document.createElement("a");
    a.href = item.link;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.className = "schedule-item__link";
    a.textContent = "Mais informações";
    li.appendChild(a);
  }

  return li;
}

/**
 * Derive Shift groups view model
 */
function deriveShiftView(section, eventDate, now, timeZone) {
  const localNow = localDateAndMinutes(now, timeZone);
  return SHIFTS.map((shift) => {
    const courses = [];
    for (const sourceGroup of section.groups || []) {
      const items = [];
      for (const item of sourceGroup.items || []) {
        const matchingSessions = (item.sessions || []).filter((s) =>
          overlapsShift(s, shift),
        );
        if (matchingSessions.length === 0) continue;
        items.push({
          item,
          courseTitle: sourceGroup.title,
          sessions: matchingSessions,
          finalized: isFinalized(matchingSessions, eventDate, localNow),
        });
      }
      if (items.length > 0) {
        courses.push({
          id: sourceGroup.id,
          title: sourceGroup.title,
          items,
        });
      }
    }
    return { id: shift.id, label: shift.label, courses };
  });
}

/**
 * Derive Knowledge Axis groups view model
 */
function deriveAxisView(section, knowledgeAxes, eventDate, now, timeZone) {
  const localNow = localDateAndMinutes(now, timeZone);
  const groups = [];

  for (const [axisId, label] of knowledgeAxes) {
    const courses = (section.groups || [])
      .filter((g) => g.knowledgeAxis === axisId)
      .map((sourceGroup) => ({
        id: sourceGroup.id,
        title: sourceGroup.title,
        items: (sourceGroup.items || []).map((item) => ({
          item,
          courseTitle: null,
          sessions: item.sessions || [],
          finalized: isFinalized(item.sessions || [], eventDate, localNow),
        })),
      }));

    if (courses.length > 0) {
      groups.push({ id: axisId, label, courses });
    }
  }
  return groups;
}

/**
 * Render groups into container element
 */
function renderGroups(container, groups) {
  container.innerHTML = "";
  let headingId = 100;

  for (const group of groups) {
    const details = document.createElement("details");
    details.className = "schedule-view-group";
    details.setAttribute("data-schedule-group", group.id);

    const summary = document.createElement("summary");
    summary.className = "schedule-view-group__summary";

    const h3 = document.createElement("h3");
    h3.className = "schedule-group__title";
    h3.id = `schedule-heading-${++headingId}`;
    h3.textContent = group.label;

    const totalItems = group.courses.reduce((acc, c) => acc + c.items.length, 0);
    const countSpan = appendText(
      h3,
      "span",
      ` ${totalItems} ${totalItems === 1 ? "atividade" : "atividades"}`,
    );
    countSpan.className = "schedule-view-group__count";

    summary.appendChild(h3);
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "schedule-view-group__content";

    if (totalItems === 0) {
      const empty = appendText(content, "p", "Nenhuma atividade disponível.");
      empty.className = "schedule-view-group__empty";
    }

    for (const course of group.courses) {
      const courseSec = document.createElement("section");
      courseSec.className = "schedule-course";
      courseSec.setAttribute("data-schedule-course", course.id);

      const courseH4 = appendText(courseSec, "h4", course.title);
      courseH4.className = "schedule-course__title";
      courseH4.id = `schedule-heading-${++headingId}`;
      courseSec.setAttribute("aria-labelledby", courseH4.id);

      const ul = document.createElement("ul");
      ul.className = "schedule-list";

      for (const entry of course.items) {
        const card = renderItemCard(
          entry.item,
          entry.courseTitle,
          entry.sessions,
          entry.finalized,
          group.id,
        );
        ul.appendChild(card);
      }

      courseSec.appendChild(ul);
      content.appendChild(courseSec);
    }

    details.appendChild(content);
    container.appendChild(details);
  }
}

/**
 * Initialize schedule view selector interactivity
 */
function setupViewSelector({
  selectorEl,
  groupsContainerEl,
  sectionData,
  knowledgeAxes = [],
  eventDate = "2026-10-26",
  timeZone = "America/Sao_Paulo",
  defaultMode = "shift",
  initialShiftHtml = null,
}) {
  if (!selectorEl || !groupsContainerEl) return;

  const buttons = Array.from(
    selectorEl.querySelectorAll('[role="radio"][data-schedule-view]'),
  );
  let currentMode = defaultMode;

  function switchMode(mode) {
    currentMode = mode;
    buttons.forEach((btn) => {
      const active = btn.getAttribute("data-schedule-view") === mode;
      btn.setAttribute("aria-checked", String(active));
      btn.tabIndex = active ? 0 : -1;
    });

    if (mode === "shift" && initialShiftHtml) {
      groupsContainerEl.innerHTML = initialShiftHtml;
      return;
    }

    if (sectionData) {
      const now = new Date();
      const groups =
        mode === "knowledge-axis"
          ? deriveAxisView(sectionData, knowledgeAxes, eventDate, now, timeZone)
          : deriveShiftView(sectionData, eventDate, now, timeZone);

      renderGroups(groupsContainerEl, groups);
    }
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-schedule-view");
      if (mode && mode !== currentMode) switchMode(mode);
    });

    btn.addEventListener("keydown", (e) => {
      const index = buttons.indexOf(btn);
      let target = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        target = buttons[(index + 1) % buttons.length];
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        target = buttons[(index - 1 + buttons.length) % buttons.length];
      } else if (e.key === "Home") {
        target = buttons[0];
      } else if (e.key === "End") {
        target = buttons[buttons.length - 1];
      }

      if (target) {
        e.preventDefault();
        target.focus();
        target.click();
      }
    });
  });

  return { switchMode };
}

/**
 * Auto-initialize if present in DOM
 */
function initCompleteProgram() {
  const section = document.getElementById("complete-program");
  if (!section) return;

  const selector = section.querySelector(".schedule-view-selector");
  const groupsContainer = section.querySelector(".schedule-view-groups");
  if (!selector || !groupsContainer) return;

  // Preserve pre-rendered HTML for instant fallback
  const initialShiftHtml = groupsContainer.innerHTML;

  let sectionData = null;
  let eventDate = null;
  let timeZone = "America/Sao_Paulo";

  // Check inline script element if any
  const inlineDataEl = document.getElementById("complete-program-data");
  if (inlineDataEl && inlineDataEl.textContent) {
    try {
      const json = JSON.parse(inlineDataEl.textContent);
      if (json.section || json.groups) sectionData = json.section || json;
      if (json.eventDate) eventDate = json.eventDate;
      if (json.timeZone) timeZone = json.timeZone;
    } catch (e) {}
  }

  setupViewSelector({
    selectorEl: selector,
    groupsContainerEl: groupsContainer,
    sectionData,
    eventDate,
    timeZone,
    defaultMode: "shift",
    initialShiftHtml,
  });

  // The backend JSON files are the only source of schedule content.
  (async () => {
    try {
      const urls = ["schedule.json", "knowledge_axes.json", "locations.json"].map(
        (fileName) => new URL(`../backend/db/${fileName}`, document.baseURI),
      );
      const responses = await Promise.all(urls.map((url) => fetch(url)));
      if (responses.some((response) => !response.ok)) {
        throw new Error("Não foi possível carregar os dados do backend.");
      }

      const [schedule, axes, locations] = await Promise.all(
        responses.map((response) => response.json()),
      );
      const normalized = normalizeScheduleDocument(schedule, axes, locations);
      if (!normalized) throw new Error("A agenda não contém a seção complete-program.");
      sectionData = normalized.section;
      eventDate = normalized.eventDate;
      setupViewSelector({
        selectorEl: selector,
        groupsContainerEl: groupsContainer,
        sectionData,
        knowledgeAxes: normalized.knowledgeAxes,
        eventDate,
        timeZone,
        defaultMode: selector.querySelector('[aria-checked="true"]')?.getAttribute("data-schedule-view") || "shift",
        initialShiftHtml,
      });
    } catch (e) {}
  })();
}

// Robust execution whether script is deferred, loaded after DOM, or as module
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCompleteProgram);
  } else {
    initCompleteProgram();
  }
}

// Expose exports globally and to CommonJS if present
if (typeof window !== "undefined") {
  window.CompleteProgram = {
    SHIFTS,
    normalizeScheduleDocument,
    deriveShiftView,
    deriveAxisView,
    renderGroups,
    setupViewSelector,
    initCompleteProgram,
  };
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    SHIFTS,
    normalizeScheduleDocument,
    deriveShiftView,
    deriveAxisView,
    renderGroups,
    setupViewSelector,
    initCompleteProgram,
  };
}
