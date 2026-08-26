import json
from contextlib import contextmanager

DATABASE_PATH = "db/users.json"


def load_database(db_path: str = DATABASE_PATH) -> dict:
    with open(db_path, "r", encoding="utf-8") as database_file:
        return json.load(database_file)


def get_user(username: str, db_path: str = DATABASE_PATH) -> dict | None:
    users = load_database(db_path).get("users", [])
    return next((user for user in users if user.get("username") == username), None)


@contextmanager
def database_connection(db_path: str = DATABASE_PATH):
    yield load_database(db_path)
