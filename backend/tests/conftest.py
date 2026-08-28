import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_JWT_SECRET = "test-only-jwt-secret-with-sufficient-length"


@dataclass(frozen=True)
class TemporaryDatabase:
    schedule: Path
    locations: Path
    knowledge_axes: Path
    users: Path


@pytest.fixture
def temporary_database(tmp_path: Path) -> TemporaryDatabase:
    paths = TemporaryDatabase(
        schedule=tmp_path / "schedule.json",
        locations=tmp_path / "locations.json",
        knowledge_axes=tmp_path / "knowledge_axes.json",
        users=tmp_path / "users.json",
    )
    for source_name, destination in (
        ("schedule.json", paths.schedule),
        ("locations.json", paths.locations),
        ("knowledge_axes.json", paths.knowledge_axes),
        ("users.json", paths.users),
    ):
        shutil.copyfile(PROJECT_ROOT / "db" / source_name, destination)
    return paths


@pytest.fixture
def configured_environment(
    monkeypatch: pytest.MonkeyPatch, temporary_database: TemporaryDatabase
) -> TemporaryDatabase:
    monkeypatch.setenv("TOKEN_JWT", TEST_JWT_SECRET)
    monkeypatch.setenv("SCHEDULE_PATH", str(temporary_database.schedule))
    monkeypatch.setenv("LOCATIONS_PATH", str(temporary_database.locations))
    monkeypatch.setenv("KNOWLEDGE_AXES_PATH", str(temporary_database.knowledge_axes))
    monkeypatch.setenv("DATABASE_PATH", str(temporary_database.users))
    return temporary_database


@pytest.fixture
def auth_headers(configured_environment: TemporaryDatabase) -> dict[str, str]:
    from routes.auth import create_access_token

    token = create_access_token({"sub": "admin-test"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(configured_environment: TemporaryDatabase) -> Iterator[TestClient]:
    from app import app
    from clients.knowledge_axes import KnowledgeAxisRepository
    from clients.locations import LocationRepository
    from routes.knowledge_axes import get_knowledge_axis_repository
    from routes.locations import get_location_repository
    from routes.schedule import get_schedule_file_path

    app.dependency_overrides[get_schedule_file_path] = lambda: configured_environment.schedule
    app.dependency_overrides[get_location_repository] = lambda: LocationRepository(
        configured_environment.locations, configured_environment.schedule
    )
    app.dependency_overrides[get_knowledge_axis_repository] = lambda: KnowledgeAxisRepository(
        configured_environment.knowledge_axes, configured_environment.schedule
    )

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def schedule_copy(tmp_path: Path) -> Path:
    source = PROJECT_ROOT / "db" / "schedule.json"
    destination = tmp_path / "schedule.json"
    shutil.copyfile(source, destination)
    return destination
