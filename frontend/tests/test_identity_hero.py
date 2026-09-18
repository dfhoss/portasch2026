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
        self.assertTrue(self.page.locator("link[href*='fonts.css']").count())
        carousel = self.page.locator(".carousel")
        self.assertTrue(carousel.get_attribute("tabindex"))
        before = self.page.locator(".carousel-track").evaluate("e => e.style.transform")
        carousel.focus()
        carousel.press("ArrowRight")
        self.assertNotEqual(self.page.locator(".carousel-track").evaluate("e => e.style.transform"), before)
        for width, expected in ((1440, 3), (768, 2), (390, 1)):
            self.page.set_viewport_size({"width": width, "height": 1000})
            self.page.wait_for_timeout(200)
            count = self.page.locator(".carousel-track .activity-card").count()
            self.assertGreaterEqual(count, expected)
        self.assertEqual(self.page.locator(".carousel-btn").count(), 2)
