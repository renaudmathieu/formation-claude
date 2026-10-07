from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from typer.testing import CliRunner

from salle42 import services, storage
from salle42.cli import app
from salle42.rules.recurrence import weekly_slots

PARIS = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")


def paris(*args):
    return datetime(*args, tzinfo=PARIS).astimezone(UTC)


def test_weekly_slots_one_per_week_same_local_time():
    slots = weekly_slots(paris(2026, 9, 14, 10), paris(2026, 9, 14, 11), 4)
    assert [s.astimezone(PARIS).strftime("%d/%m %H:%M") for s, _ in slots] == [
        "14/09 10:00",
        "21/09 10:00",
        "28/09 10:00",
        "05/10 10:00",
    ]


def test_weekly_slots_keep_local_time_across_dst_change():
    # Passage à l'heure d'hiver le 25/10/2026 : 10:00 à Paris reste 10:00
    slots = weekly_slots(paris(2026, 10, 19, 10), paris(2026, 10, 19, 11), 2)
    (before, _), (after, _) = slots
    assert before.astimezone(PARIS).hour == 10
    assert after.astimezone(PARIS).hour == 10
    assert (before.hour, after.hour) == (8, 9)  # en UTC, l'heure change


def test_book_weekly_creates_n_bookings():
    bookings = services.book_weekly("B", "2026-09-14", "10:00", "11:00", "evan", 4)
    assert len(bookings) == 4
    assert len(storage.get_bookings("B")) == 4


def test_book_weekly_is_all_or_nothing():
    services.book("B", "2026-09-28", "10:30", "11:30", "lea")
    with pytest.raises(services.ConflictError) as erreur:
        services.book_weekly("B", "2026-09-14", "10:00", "11:00", "evan", 4)
    assert "28/09" in str(erreur.value)  # la première date en conflit
    assert len(storage.get_bookings("B")) == 1  # rien n'a été créé


def test_book_weekly_needs_at_least_one_week():
    with pytest.raises(services.InvalidSlot):
        services.book_weekly("B", "2026-09-14", "10:00", "11:00", "evan", 0)


def test_cli_weekly_summary():
    result = CliRunner().invoke(
        app, ["book", "B", "2026-09-14", "10:00", "11:00", "--by", "evan", "--weekly", "4"]
    )
    assert result.exit_code == 0
    assert "4 réservations créées (14/09 → 05/10)" in result.output
