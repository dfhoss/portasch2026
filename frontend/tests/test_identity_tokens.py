import unittest

from browser_support import BrowserTestCase


class IdentityTokensTest(BrowserTestCase):
    def test_standard_theme_applies_new_component_pairs(self):
        self.assertEqual(self.computed("body", "background-color"), "rgb(210, 222, 207)")
        self.assertEqual(
            self.computed(".activity-card", "background-color", first=True),
            "rgb(255, 255, 255)",
        )
        self.assertIn("Open Sans", self.computed("body", "font-family"))
        self.assertEqual(
            self.computed(".carousel-btn.next", "background-color"),
            "rgb(57, 58, 237)",
        )
        self.assertEqual(
            self.computed('.schedule-view-selector__option[aria-checked="true"]', "color"),
            "rgb(216, 249, 59)",
        )

    def test_finalized_activity_uses_the_complete_semantic_pair(self):
        item = self.page.locator(".schedule-item").first
        item.wait_for(state="attached")
        item.evaluate(
            """element => {
                element.classList.add('schedule-item--finalized');
                const status = document.createElement('span');
                status.className = 'schedule-item__status';
                status.textContent = 'Finalizada';
                element.prepend(status);
            }"""
        )
        self.assertEqual(
            item.evaluate("element => getComputedStyle(element).backgroundColor"),
            "rgb(210, 222, 207)",
        )
        self.assertEqual(
            item.locator(".schedule-item__status").evaluate(
                "element => getComputedStyle(element).color"
            ),
            "rgb(255, 255, 255)",
        )

    def test_legacy_theme_attribute_switches_equivalent_component_pairs(self):
        self.page.locator("html").evaluate(
            "element => element.setAttribute('data-theme', 'high-contrast')"
        )
        self.assertEqual(self.computed("body", "background-color"), "rgb(20, 21, 43)")
        self.assertEqual(
            self.computed(".carousel-btn.next", "background-color"),
            "rgb(200, 255, 0)",
        )
        self.assertEqual(
            self.computed(".carousel-btn.next", "color"),
            "rgb(20, 21, 43)",
        )

        self.page.locator("html").evaluate(
            "element => element.setAttribute('data-theme', 'dark')"
        )
        self.assertEqual(self.computed("body", "background-color"), "rgb(20, 21, 43)")

    def test_required_local_font_faces_load(self):
        requested_faces = (
            ("Open Sans", 400),
            ("Open Sans", 700),
            ("Disket Mono", 400),
            ("Disket Mono", 700),
            ("Retropix", 400),
            ("Garet", 400),
            ("Garet", 700),
        )
        for family, weight in requested_faces:
            with self.subTest(family=family, weight=weight):
                loaded = self.page.evaluate(
                    """async ([family, weight]) => {
                        await document.fonts.load(`${weight} 16px "${family}"`);
                        return [...document.fonts].some(face =>
                            face.family.replaceAll('"', '') === family &&
                            face.weight === String(weight) &&
                            face.style === 'normal' &&
                            face.status === 'loaded'
                        );
                    }""",
                    [family, weight],
                )
                self.assertTrue(loaded)

    def test_runtime_stylesheets_have_no_pending_placeholders(self):
        stylesheet_texts = self.page.evaluate(
            """async () => Promise.all(
                [...document.querySelectorAll('link[rel="stylesheet"]')]
                    .map(link => fetch(link.href).then(response => response.text()))
            )"""
        )
        self.assertNotIn("PENDENTE", "\n".join(stylesheet_texts))


if __name__ == "__main__":
    unittest.main()
