try:
    from .browser_support import BrowserTestCase
except ImportError:
    from browser_support import BrowserTestCase


class HeroIdentityTests(BrowserTestCase):
    def test_hero_uses_integral_desktop_and_mobile_assets(self):
        self.page.set_viewport_size({"width": 1440, "height": 1000})
        self.page.reload(wait_until="networkidle")
        hero = self.page.locator(".hero-image")
        self.assertEqual(hero.count(), 1, "A home precisa de um único hero")
        self.assertTrue(hero.evaluate("e => e.currentSrc").endswith("/hero-desktop.jpg"))
        self.assertEqual(hero.evaluate("e => [e.naturalWidth, e.naturalHeight]"), [5938, 1250])
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.wait_for_function(
            "document.querySelector('.hero-image')?.currentSrc.endsWith('/hero-mobile.png')"
        )
        self.assertEqual(hero.evaluate("e => [e.naturalWidth, e.naturalHeight]"), [1080, 437])

    def test_hero_has_no_overflow_and_h1(self):
        for width in (390, 768, 1440):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.reload(wait_until="networkidle")
            self.assertEqual(self.page.locator("h1").count(), 1)
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width)
            self.assertLessEqual(self.page.evaluate("document.body.scrollWidth"), width)

    def test_assets_controls_and_responsive_carousel_contract(self):
        self.assertTrue(
            self.page.locator(".hero-image").evaluate("e => e.complete && e.naturalWidth > 0")
        )
        self.assertTrue(self.page.evaluate("document.fonts.status === 'loaded'"))
        for width in (390, 768, 1440):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.wait_for_timeout(200)
            natural = self.page.locator(".hero-image").evaluate(
                "e => [e.naturalWidth, e.naturalHeight]"
            )
            rendered = self.page.locator(".hero-image").bounding_box()
            assert rendered is not None, "O hero deve ter uma caixa renderizada"
            self.assertAlmostEqual(
                rendered["height"], rendered["width"] * natural[1] / natural[0], delta=1
            )
        carousel = self.page.locator(".carousel")
        self.assertTrue(carousel.get_attribute("tabindex"))
        prev = self.page.locator(".carousel-btn.prev")
        next_button = self.page.locator(".carousel-btn.next")
        self.assertFalse(prev.is_disabled())
        self.assertFalse(next_button.is_disabled())
        before = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        carousel.focus()
        carousel.press("ArrowRight")
        self.assertNotEqual(
            self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before
        )
        self.page.keyboard.press("Tab")
        self.assertTrue(self.page.evaluate("document.activeElement.matches('button, [tabindex]')"))
        for width, expected in ((1440, 3), (768, 2), (390, 1)):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.reload(wait_until="networkidle")
            self.page.wait_for_timeout(200)
            viewport = self.page.locator(".carousel")
            box = viewport.bounding_box()
            assert box is not None, "O carrossel deve ter uma caixa renderizada"
            visible = sum(
                1
                for card in self.page.locator(".carousel-track .activity-card").all()
                if (rect := card.bounding_box())
                and rect["x"] >= box["x"] - 1
                and rect["x"] + rect["width"] <= box["x"] + box["width"] + 1
            )
            self.assertEqual(visible, expected)
        self.assertEqual(self.page.locator(".carousel-btn").count(), 2)
        initial = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        for _ in range(self.page.locator(".carousel-dots .dot").count()):
            next_button.click()
            self.page.wait_for_timeout(600)
        self.assertEqual(
            self.page.locator(".carousel-track").evaluate("e => e.style.transform"), initial
        )
        self.assertFalse(next_button.is_disabled())
        self.assertFalse(prev.is_disabled())

    def test_short_swipe_does_not_navigate_but_long_swipe_does(self):
        carousel = self.page.locator(".carousel")
        before = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        carousel.dispatch_event(
            "touchstart", {"touches": [{"identifier": 1, "clientX": 300, "clientY": 100}]}
        )
        carousel.dispatch_event(
            "touchend", {"changedTouches": [{"identifier": 1, "clientX": 260, "clientY": 100}]}
        )
        self.assertEqual(
            self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before
        )
        carousel.dispatch_event(
            "touchstart", {"touches": [{"identifier": 1, "clientX": 300, "clientY": 100}]}
        )
        carousel.dispatch_event(
            "touchend", {"changedTouches": [{"identifier": 1, "clientX": 200, "clientY": 100}]}
        )
        self.assertNotEqual(
            self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before
        )

    def test_repeated_carousel_initialization_does_not_duplicate_cards_or_dots(self):
        self.page.evaluate(
            """
            () => {
              const track = document.querySelector('.carousel-track');
              const card = document.createElement('article');
              card.className = 'activity-card';
              card.setAttribute('data-schedule-item', 'fixture-card');
              card.textContent = 'Fixture';
              track.replaceChildren(card);
              window.initializeCarousel();
              window.initializeCarousel();
              if (track.querySelectorAll('[data-carousel-clone]').length !== 0) {
                throw new Error('clones inesperados');
              }
              if (track.querySelectorAll('.activity-card:not([data-carousel-clone])').length !== 1) {
                throw new Error('cards duplicados');
              }
              if (document.querySelectorAll('.carousel-dots .dot').length !== 1) {
                throw new Error('dots duplicados');
              }
            }
            """
        )

    def test_agenda_failure_keeps_static_content_and_carousel_empty(self):
        self.page.route("**/db/schedule.json", lambda route: route.abort())
        self.page.reload(wait_until="networkidle")
        self.assertEqual(self.page.locator(".activity-card").count(), 0)
        self.assertGreater(self.page.locator(".carousel-btn").count(), 0)
        self.assertEqual(
            self.page.locator("[data-schedule-root]").get_attribute("aria-busy"), "false"
        )
        self.assertGreater(self.page.locator(".hero-image").count(), 0)
        self.assertGreater(self.page.locator(".rule-btn").count(), 0)
        self.assertGreater(self.page.locator(".campus-map-img").count(), 0)
        self.assertIn("ROLANDO AGORA", self.page.locator("main").inner_text().upper())

    def test_successful_loads_have_no_application_page_errors_and_capture_viewports(self):
        errors = []
        self.page.on("pageerror", lambda error: errors.append(str(error)))
        for width, name in ((390, "390"), (768, "768"), (1440, "1440")):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.reload(wait_until="networkidle")
            self.page.screenshot(
                path=f".superpowers/sdd/2026-09-18-frontend-new-identity/task-2-{name}.png",
                full_page=True,
            )
        self.assertEqual(errors, [])
