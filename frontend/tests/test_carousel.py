from browser_support import BrowserTestCase


class CarouselTest(BrowserTestCase):
    def open_at(self, width):
        self.page.set_viewport_size({"width": width, "height": 1000})
        self.page.reload(wait_until="networkidle")

    def active_page(self):
        return self.page.locator(".carousel-dots .dot").evaluate_all(
            "dots => dots.findIndex(dot => dot.classList.contains('active'))"
        )

    def offset(self):
        return self.page.locator(".carousel-track").evaluate(
            "e => new DOMMatrix(getComputedStyle(e).transform).m41"
        )

    def settle(self):
        self.page.wait_for_timeout(600)

    def test_desktop_next_and_dot_select_the_same_page(self):
        self.assertEqual(self.page.locator(".carousel-dots .dot").count(), 2)
        self.page.locator(".carousel-btn.next").click()
        self.settle()
        self.assertEqual(self.active_page(), 1)
        next_offset = self.offset()
        self.page.locator(".carousel-dots .dot").first.click()
        self.settle()
        self.page.locator(".carousel-dots .dot").nth(1).click()
        self.settle()
        self.assertAlmostEqual(self.offset(), next_offset, delta=1)
        self.assertEqual(self.page.locator('.dot[aria-current="true"]').count(), 1)

    def test_active_dot_is_not_fractionally_scaled(self):
        active = self.page.locator(".carousel-dots .dot.active")
        self.assertEqual(active.evaluate("e => getComputedStyle(e).transform"), "none")
        self.assertEqual(active.evaluate("e => getComputedStyle(e).filter"), "none")
        self.assertEqual(active.bounding_box()["width"] % 1, 0)

    def test_wrap_keeps_moving_forward_then_restores_first_page(self):
        for width in (1440, 390):
            with self.subTest(width=width):
                self.open_at(width)
                initial = self.offset()
                self.page.locator(".carousel-dots .dot").last.click()
                self.settle()
                last = self.offset()
                self.page.locator(".carousel").press("ArrowRight")
                self.page.wait_for_timeout(100)
                self.assertLess(self.offset(), last, "O retorno deve continuar para a frente")
                self.settle()
                self.assertAlmostEqual(self.offset(), initial, delta=1)
                self.assertEqual(self.active_page(), 0)
                self.assertFalse(self.page.locator(".carousel-btn.next").is_disabled())
                self.assertFalse(self.page.locator(".carousel-btn.prev").is_disabled())

    def test_reverse_wrap_resize_and_reduced_motion(self):
        self.page.emulate_media(reduced_motion="reduce")
        self.open_at(390)
        self.page.locator(".carousel-btn.prev").click()
        self.assertEqual(self.active_page(), 4)
        self.page.set_viewport_size({"width": 768, "height": 1000})
        self.page.wait_for_timeout(200)
        self.assertEqual(self.page.locator(".carousel-dots .dot").count(), 3)
        self.assertEqual(self.page.locator(".dot.active").count(), 1)
        self.page.locator(".carousel-btn.next").click()
        self.assertEqual(self.active_page(), 0)
        clones = self.page.locator('[data-carousel-clone]')
        self.assertGreater(clones.count(), 0)
        self.assertTrue(clones.evaluate_all("items => items.every(e => e.inert && e.getAttribute('aria-hidden') === 'true')"))
        self.assertEqual(self.page.locator(".activity-card:not([data-carousel-clone])").count(), 5)

    def test_resize_with_same_page_size_preserves_selection_and_focus(self):
        self.page.emulate_media(reduced_motion="reduce")
        self.page.locator(".carousel-dots .dot").last.click()
        self.page.set_viewport_size({"width": 1300, "height": 1000})
        self.page.wait_for_timeout(200)
        self.assertEqual(self.active_page(), 1)
        self.assertTrue(self.page.locator(".dot.active").evaluate("e => e === document.activeElement"))

    def test_autoplay_waits_five_seconds_and_restarts_after_keyboard(self):
        from datetime import datetime, timezone

        self.page.clock.install(time=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.page.clock.pause_at(datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc))
        self.page.reload(wait_until="load")
        self.page.clock.run_for(4999)
        self.assertEqual(self.active_page(), 0)
        self.page.clock.run_for(1)
        self.assertEqual(self.active_page(), 1)
        self.page.clock.run_for(600)
        self.page.locator(".carousel").press("ArrowLeft")
        self.page.clock.run_for(4999)
        self.assertEqual(self.active_page(), 0)
        self.page.clock.run_for(1)
        self.assertEqual(self.active_page(), 1)

    def test_mobile_touch_does_not_leave_hover_colors_or_scale(self):
        self.open_at(390)
        button = self.page.locator(".carousel-btn.next")
        button.dispatch_event("pointerdown", {"pointerType": "touch"})
        button.dispatch_event("pointerup", {"pointerType": "touch"})
        self.page.wait_for_timeout(100)
        styles = button.evaluate("e => ({background: getComputedStyle(e).backgroundColor, transform: getComputedStyle(e).transform})")
        self.assertEqual(styles["background"], "rgb(57, 58, 237)")
        self.assertEqual(styles["transform"], "none")
