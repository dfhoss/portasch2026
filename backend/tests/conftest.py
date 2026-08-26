import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def schedule_copy(tmp_path: Path) -> Path:
    source = PROJECT_ROOT / "db" / "schedule.json"
    destination = tmp_path / "schedule.json"
    shutil.copyfile(source, destination)
    return destination
