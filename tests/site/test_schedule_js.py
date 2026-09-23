import subprocess
from pathlib import Path

SCHEDULE_SCRIPT = Path(__file__).parents[2] / "static" / "site" / "js" / "schedule.js"


def run_node_case(case: str) -> None:
    source = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const scheduleModule = {{exports: {{}}}};
const script = fs.readFileSync(process.argv[2], "utf8");
vm.runInNewContext(script, {{module: scheduleModule, exports: scheduleModule.exports, console, URL}});
const api = scheduleModule.exports;
{case}
"""
    completed = subprocess.run(
        ["node", "-", str(SCHEDULE_SCRIPT)],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_schedule_module_exports_the_public_contract():
    run_node_case(
        """
const names = [
  "loadPublicDocuments",
  "findCompleteProgramSection",
  "normalizeScheduleDocument",
  "statusForActivity",
  "deriveShiftView",
  "deriveAxisView",
  "selectCarouselActivities",
  "renderGroups",
];
for (const name of names) assert.equal(typeof api[name], "function", name);
        """
    )


def test_load_public_documents_requires_successful_json_responses():
    run_node_case(
        """
(async () => {
const files = ["schedule.json", "knowledge_axes.json", "locations.json", "settings.json"];
const payloads = [
  {sections: []},
  {knowledgeAxes: []},
  {locations: []},
  {eventDate: "2026-09-22"},
];
const fetchImpl = async (url) => {
  const index = files.indexOf(url.pathname.split("/").at(-1));
  return {ok: true, json: async () => payloads[index]};
};
const loaded = await api.loadPublicDocuments(fetchImpl, "https://example.test/");
assert.deepEqual(loaded.schedule, payloads[0]);
assert.deepEqual(loaded.knowledgeAxes, payloads[1]);
assert.deepEqual(loaded.locations, payloads[2]);
assert.deepEqual(loaded.settings, payloads[3]);

await assert.rejects(
  api.loadPublicDocuments(
    async (url) => ({ok: url.pathname.endsWith("schedule.json") ? false : true, json: async () => ({})}),
    "https://example.test/",
  ),
);
await assert.rejects(
  api.loadPublicDocuments(
    async (url) => ({ok: true, json: async () => {
      if (url.pathname.endsWith("locations.json")) throw new Error("JSON inválido");
      return {};
    }}),
    "https://example.test/",
  ),
);
await assert.rejects(
  api.loadPublicDocuments(
    async (url) => ({
      ok: true,
      json: async () => url.pathname.endsWith("settings.json")
        ? {eventDate: "2026-02-30"}
        : {},
    }),
    "https://example.test/",
  ),
);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
        """
    )


def test_normalization_uses_catalogs_without_mutating_the_schedule():
    run_node_case(
        """
const schedule = {
  version: 1,
  sections: [{id: "complete-program", title: "Completa", groups: [
    {id: "sem-eixo", title: "Grupo <seguro>", knowledgeAxis: null, items: [
      {id: "atividade-1", title: "Título <seguro>", description: "Descrição", sessions: [
        {startTime: "11:59", endTime: "12:00", locations: ["Sala A", "", "Sala B"]},
      ]},
    ]},
    {id: "eixo-desconhecido", title: "Outro", knowledgeAxis: "axis-secret", items: []},
  ]}],
};
const original = JSON.parse(JSON.stringify(schedule));
const completeSection = api.findCompleteProgramSection(schedule);
assert.equal(completeSection.id, "complete-program");
assert.equal(api.findCompleteProgramSection({sections: []}), null);
const normalized = api.normalizeScheduleDocument(
  schedule,
  {knowledgeAxes: [{id: "axis-real", name: "Eixo real"}]},
  {locations: [{name: "Sala A"}, {name: "Sala B"}]},
  {eventDate: "2026-09-22"},
);
assert.equal(normalized.eventDate, "2026-09-22");
assert.equal(normalized.section.groups[0].knowledgeAxis, null);
assert.equal(
  normalized.section.groups[0].items[0].sessions[0].location,
  `Sala A ${String.fromCodePoint(0x00b7)} Sala B`,
);
assert.equal(normalized.section.groups[1].knowledgeAxis, "axis-secret");
assert.deepEqual(schedule, original);
assert.deepEqual(schedule.sections[0].groups[0].items[0].sessions[0].locations, [
  "Sala A",
  "",
  "Sala B",
]);
        """
    )


def test_status_and_shift_boundaries_use_the_event_timezone():
    run_node_case(
        """
const timeZone = "America/Sao_Paulo";
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-22",
    new Date("2026-09-22T13:30:00.000Z"),
    timeZone,
  ),
  "AO VIVO",
);
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-22",
    new Date("2026-09-22T14:00:00.000Z"),
    timeZone,
  ),
  "FINALIZADA",
);
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-23",
    new Date("2026-09-22T13:30:00.000Z"),
    timeZone,
  ),
  "AO VIVO",
);
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-21",
    new Date("2026-09-22T12:00:00.000Z"),
    timeZone,
  ),
  "EM BREVE",
);

const section = {groups: [{
  id: "limites",
  title: "Limites",
  knowledgeAxis: null,
  items: [
    {id: "morning-only", title: "Manhã", sessions: [{startTime: "11:59", endTime: "12:00"}]},
    {id: "afternoon-only", title: "Tarde", sessions: [{startTime: "12:00", endTime: "18:00"}]},
    {id: "evening-only", title: "Noite", sessions: [{startTime: "18:00", endTime: "21:01"}]},
  ],
}]};
const views = api.deriveShiftView(
  section,
  "2026-09-22",
  new Date("2026-09-22T13:30:00.000Z"),
  timeZone,
);
const idsByShift = Object.fromEntries(
  views.map((view) => [view.id, view.courses.flatMap((course) => course.items.map((entry) => entry.item.id))]),
);
assert.deepEqual(JSON.parse(JSON.stringify(idsByShift.morning)), ["morning-only"]);
assert.deepEqual(JSON.parse(JSON.stringify(idsByShift.afternoon)), ["afternoon-only"]);
assert.deepEqual(JSON.parse(JSON.stringify(idsByShift.evening)), ["evening-only"]);
        """
    )


def test_carousel_prioritizes_time_statuses_without_event_date_gate():
    run_node_case(
        """
const now = new Date("2026-09-22T13:30:00.000Z");
const activities = [
  {id: "soon", sessions: [{startTime: "11:00", endTime: "12:00"}]},
  {id: "live", sessions: [{startTime: "10:00", endTime: "11:00"}]},
  {id: "past", sessions: [{startTime: "08:00", endTime: "09:00"}]},
];
const selected = api.selectCarouselActivities(
  activities,
  "2027-01-01",
  now,
  "America/Sao_Paulo",
);
assert.deepEqual(JSON.parse(JSON.stringify(selected.map((activity) => activity.id))), [
  "live",
  "soon",
  "past",
]);
        """
    )


def test_carousel_shows_only_the_current_or_nearest_session():
    run_node_case(
        """
const sessions = [
  {startTime: "19:00", endTime: "21:00", location: "Noite"},
  {startTime: "08:30", endTime: "12:00", location: "Manhã"},
  {startTime: "13:00", endTime: "18:00", location: "Tarde"},
];
const selectSessionsAt = (instant) => api.selectCarouselActivities(
  [{id: "multi-slot", sessions}],
  "2027-01-01",
  new Date(instant),
  "America/Sao_Paulo",
)[0].sessions;

assert.deepEqual(
  JSON.parse(JSON.stringify(selectSessionsAt("2026-09-22T14:00:00.000Z"))),
  [sessions[1]],
);
assert.deepEqual(
  JSON.parse(JSON.stringify(selectSessionsAt("2026-09-22T15:00:00.000Z"))),
  [sessions[2]],
);
assert.deepEqual(
  JSON.parse(JSON.stringify(selectSessionsAt("2026-09-23T00:05:00.000Z"))),
  [sessions[0]],
);
        """
    )


def test_axis_view_keeps_unknown_groups_under_sem_eixo():
    run_node_case(
        """
const section = {groups: [
  {id: "real-group", title: "Real", knowledgeAxis: "axis-real", items: []},
  {id: "no-axis", title: "Sem referência", knowledgeAxis: null, items: []},
  {id: "unknown-axis", title: "Desconhecido", knowledgeAxis: "axis-secret", items: []},
]};
const groups = api.deriveAxisView(
  section,
  {knowledgeAxes: [{id: "axis-real", name: "Eixo real"}]},
  "2026-09-22",
  new Date("2026-09-22T13:30:00.000Z"),
  "America/Sao_Paulo",
);
assert.deepEqual(JSON.parse(JSON.stringify(groups.map((group) => group.label))), ["Eixo real", "Sem eixo"]);
assert.deepEqual(JSON.parse(JSON.stringify(groups[0].courses.map((course) => course.id))), ["real-group"]);
assert.deepEqual(JSON.parse(JSON.stringify(groups[1].courses.map((course) => course.id))), ["no-axis", "unknown-axis"]);
        """
    )


def test_carousel_selection_is_unique_prioritized_and_limited():
    run_node_case(
        """
const now = new Date("2026-09-22T13:30:00.000Z");
const activities = [
  {id: "next-1", sessions: [{startTime: "11:00", endTime: "12:00"}]},
  {id: "live-1", sessions: [{startTime: "10:00", endTime: "11:00"}]},
  {id: "live-1", sessions: [{startTime: "10:00", endTime: "11:00"}]},
  {id: "past-1", sessions: [{startTime: "08:00", endTime: "09:00"}]},
  {id: "next-2", sessions: [{startTime: "12:00", endTime: "13:00"}]},
  {id: "live-2", sessions: [{startTime: "10:15", endTime: "10:45"}]},
  {id: "next-3", sessions: [{startTime: "13:00", endTime: "14:00"}]},
  {id: "next-4", sessions: [{startTime: "15:00", endTime: "16:00"}]},
];
const selected = api.selectCarouselActivities(
  activities,
  "2026-09-22",
  now,
  "America/Sao_Paulo",
);
assert.deepEqual(JSON.parse(JSON.stringify(selected.map((activity) => activity.id))), [
  "live-1",
  "live-2",
  "next-1",
  "next-2",
  "next-3",
]);
assert.equal(new Set(selected.map((activity) => activity.id)).size, selected.length);
assert.ok(selected.length <= 5);
        """
    )
