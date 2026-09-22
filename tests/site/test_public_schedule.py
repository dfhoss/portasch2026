from datetime import datetime, timezone
from pathlib import Path

try:
    from .browser_support import BrowserTestCase
except ImportError:
    from browser_support import BrowserTestCase


class PublicScheduleTests(BrowserTestCase):
    def test_public_schedule_uses_only_the_four_json_sources(self):
        requests = []
        self.page.on("request", lambda request: requests.append(request))
        self.page.reload(wait_until="networkidle")

        public_requests = {
            (request.method, request.url.rsplit("/", 1)[-1])
            for request in requests
            if "/db/" in request.url
        }
        assert public_requests == {
            ("GET", "schedule.json"),
            ("GET", "knowledge_axes.json"),
            ("GET", "locations.json"),
            ("GET", "settings.json"),
        }
        assert not any("/api/" in request.url for request in requests)
        assert (
            self.page.locator(".schedule-item")
            .filter(has_text="Voz e Ação: conhecendo o curso de Administração")
            .count()
            > 0
        )
        assert (
            self.page.locator(".activity-card")
            .filter(has_text="Visita guiada ao Campus")
            .count()
            == 0
        )

    def test_settings_fixture_simulates_live_and_finalized_without_writing_schedule(self):
        schedule_path = Path(__file__).resolve().parents[2] / "db" / "schedule.json"
        original_schedule = schedule_path.read_bytes()
        title = "Voz e Ação: conhecendo o curso de Administração"
        cases = (
            (datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc), "EM BREVE"),
            (datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc), "AO VIVO"),
            (datetime(2026, 9, 23, 0, 1, tzinfo=timezone.utc), "FINALIZADA"),
        )

        for instant, expected_status in cases:
            page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                page.clock.install(time=instant)
                page.route(
                    "**/db/settings.json",
                    lambda route: route.fulfill(
                        status=200,
                        content_type="application/json",
                        body='{"eventDate":"2026-09-22"}',
                    ),
                )
                page.goto(self.base_url + "/", wait_until="networkidle")
                assert (
                    page.locator(f".schedule-item[data-schedule-status='{expected_status}']")
                    .filter(has_text=title)
                    .count()
                    > 0
                )
            finally:
                page.close()

        assert schedule_path.read_bytes() == original_schedule

    def test_public_schedule_failure_is_silent_and_read_only(self):
        requests = []
        errors = []
        self.page.on("request", lambda request: requests.append(request))
        self.page.on("pageerror", lambda error: errors.append(str(error)))
        self.page.route("**/db/*.json", lambda route: route.abort())
        self.page.reload(wait_until="networkidle")

        assert self.page.locator(".hero-image").count() == 1
        assert self.page.get_by_role("heading", name="Regulamento da Gincana").is_visible()
        assert self.page.locator(".campus-map-img").count() > 0
        assert self.page.locator("[data-schedule-root]").get_attribute("aria-busy") == "false"
        assert self.page.locator(".schedule-item").count() == 0
        assert not any(
            request.method in {"PUT", "POST", "PATCH", "DELETE"} for request in requests
        )
        assert errors == []
