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
        self.page.wait_for_function("document.querySelector('.hero-image')?.currentSrc.endsWith('/hero-mobile.png')")
        self.assertEqual(hero.evaluate("e => [e.naturalWidth, e.naturalHeight]"), [1080, 437])

    def test_hero_has_no_overflow_and_h1(self):
        for width in (390, 768, 1440):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.reload(wait_until="networkidle")
            self.assertEqual(self.page.locator("h1").count(), 1)
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width)
            self.assertLessEqual(self.page.evaluate("document.body.scrollWidth"), width)

    def test_assets_controls_and_responsive_carousel_contract(self):
        self.assertTrue(self.page.locator(".hero-image").evaluate("e => e.complete && e.naturalWidth > 0"))
        self.assertTrue(self.page.evaluate("document.fonts.status === 'loaded'"))
        ratio = self.page.locator(".hero-image").evaluate("e => e.naturalWidth / e.naturalHeight")
        rendered = self.page.locator(".hero-image").bounding_box()
        self.assertAlmostEqual(ratio, rendered["width"] / rendered["height"], delta=0.01)
        carousel = self.page.locator(".carousel")
        self.assertTrue(carousel.get_attribute("tabindex"))
        before = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        carousel.focus()
        carousel.press("ArrowRight")
        self.assertNotEqual(self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before)
        self.page.keyboard.press("Tab")
        self.assertTrue(self.page.evaluate("document.activeElement.matches('button, [tabindex]')"))
        for width, expected in ((1440, 3), (768, 2), (390, 1)):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.wait_for_timeout(200)
            count = self.page.locator(".carousel-track .activity-card").count()
            self.assertGreaterEqual(count, expected)
        self.assertEqual(self.page.locator(".carousel-btn").count(), 2)
        self.page.screenshot(path=".superpowers/sdd/2026-09-18-frontend-new-identity/task-2-1440.png", full_page=True)

    def test_short_swipe_does_not_navigate_but_long_swipe_does(self):
        carousel = self.page.locator(".carousel")
        before = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        carousel.dispatch_event("touchstart", {"touches": [{"identifier": 1, "clientX": 300, "clientY": 100}]})
        carousel.dispatch_event("touchend", {"changedTouches": [{"identifier": 1, "clientX": 260, "clientY": 100}]})
        self.assertEqual(self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before)
        carousel.dispatch_event("touchstart", {"touches": [{"identifier": 1, "clientX": 300, "clientY": 100}]})
        carousel.dispatch_event("touchend", {"changedTouches": [{"identifier": 1, "clientX": 200, "clientY": 100}]})
        self.assertNotEqual(self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before)
