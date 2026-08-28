"""Isolated live-server fixtures for browser coverage of the admin panel."""

from __future__ import annotations

import json
import shutil
import socket
import threading
import time
import urllib.request
from pathlib import Path
from typing import Iterator

import bcrypt
import pytest
import uvicorn
from playwright.sync_api import Browser, Page, sync_playwright

PROJECT_ROOT = Path(__file__).parents[2]
TEST_JWT_SECRET = "e2e-only-jwt-secret-with-sufficient-length"
TEST_USERNAME = "e2e-admin"
TEST_PASSWORD = "e2e-password-only"


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(headless=True)
        yield instance
        instance.close()


@pytest.fixture
def temporary_databases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Copy every JSON store and replace users with a runtime-only bcrypt credential."""

    paths = {
        name: tmp_path / name
        for name in ("users.json", "schedule.json", "locations.json", "knowledge_axes.json")
    }
    for name, destination in paths.items():
        shutil.copyfile(PROJECT_ROOT / "db" / name, destination)

    password_hash = bcrypt.hashpw(TEST_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    paths["users.json"].write_text(
        json.dumps(
            {
                "users": [
                    {
                        "id": 1,
                        "username": TEST_USERNAME,
                        "user_type": "admin",
                        "hashed_password": password_hash,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_PATH", str(paths["users.json"]))
    monkeypatch.setenv("SCHEDULE_PATH", str(paths["schedule.json"]))
    monkeypatch.setenv("LOCATIONS_PATH", str(paths["locations.json"]))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(paths["knowledge_axes.json"]))
    monkeypatch.setenv("TOKEN_JWT", TEST_JWT_SECRET)
    return paths


@pytest.fixture
def live_server(
    temporary_databases: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> Iterator[str]:
    """Run Uvicorn on a reserved local port and always tear it down boundedly."""

    del temporary_databases  # The fixture dependency intentionally establishes env first.
    from app import app

    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reservation.bind(("127.0.0.1", 0))
    port = reservation.getsockname()[1]
    reservation.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    thread_errors: list[BaseException] = []

    def run_server() -> None:
        try:
            server.run()
        except BaseException as error:  # Propagate startup/runtime failures to the test thread.
            thread_errors.append(error)

    thread = threading.Thread(target=run_server, name="admin-e2e-uvicorn", daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    try:
        while not server.started:
            if thread_errors:
                raise RuntimeError("Uvicorn failed to start") from thread_errors[0]
            if not thread.is_alive():
                raise RuntimeError("Uvicorn thread exited before startup")
            if time.monotonic() >= deadline:
                raise TimeoutError("Uvicorn startup exceeded 10 seconds")
            time.sleep(0.02)
        url = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(f"{url}/health", timeout=2) as response:
            if response.status != 200:
                raise RuntimeError(f"Health check returned {response.status}")
        yield url
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("Uvicorn thread did not stop within 5 seconds")
        if thread_errors:
            raise RuntimeError("Uvicorn failed during the browser test") from thread_errors[0]


@pytest.fixture
def admin_page(browser: Browser, live_server: str) -> Iterator[Page]:
    page = browser.new_page()
    page.goto(f"{live_server}/admin", wait_until="domcontentloaded")
    yield page
    page.close()


@pytest.fixture
def live_server_url(live_server: str) -> str:
    """Named alias useful for tests that need a second browser context."""

    return live_server
