import pytest

from salle42 import storage


@pytest.fixture(autouse=True)
def base_temporaire(tmp_path, monkeypatch):
    """Chaque test travaille sur une base SQLite neuve."""
    monkeypatch.setattr(storage, "DB_PATH", str(tmp_path / "test.db"))
