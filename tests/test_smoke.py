import pytest

from salle42 import services, storage


@pytest.fixture(autouse=True)
def base_temporaire(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", str(tmp_path / "test.db"))


def test_rooms():
    assert [r.id for r in services.list_rooms()] == ["A", "B", "C"]


def test_book_without_attendees():
    booking = services.book("B", "2026-09-14", "10:00", "11:00", owner="moi")
    assert booking.attendees is None


def test_book_over_capacity_is_refused():
    with pytest.raises(services.CapacityError):
        services.book("B", "2026-09-14", "10:00", "11:00", owner="moi", attendees=5)
