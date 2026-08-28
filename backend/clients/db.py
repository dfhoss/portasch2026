import json
import os
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = "db/users.json"


def get_database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", DATABASE_PATH))


def load_database(db_path: str | Path | None = None) -> dict:
    path = Path(db_path) if db_path is not None else get_database_path()
    with path.open("r", encoding="utf-8") as database_file:
        return json.load(database_file)


def get_user(username: str, db_path: str | Path | None = None) -> dict | None:
    users = load_database(db_path).get("users", [])
    return next((user for user in users if user.get("username") == username), None)


@contextmanager
def database_connection(db_path: str | Path | None = None):
    yield load_database(db_path)
