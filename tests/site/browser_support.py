from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Navigation/source changes can cancel an in-flight image transfer.
            # Only client disconnects are expected; other server errors propagate.
            pass


class BrowserTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[2]
        handler = partial(_QuietHandler, directory=cls.repo_root)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=5)

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        self.page.goto(self.base_url + "/site/", wait_until="networkidle")

    def tearDown(self):
        self.page.close()

    def computed(self, selector, property_name, *, first=False):
        locator = self.page.locator(selector)
        if first:
            locator = locator.first
        return locator.evaluate(
            "(element, propertyName) => getComputedStyle(element).getPropertyValue(propertyName).trim()",
            property_name,
        )
