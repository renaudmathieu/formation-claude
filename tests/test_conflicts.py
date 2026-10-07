from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from salle42 import services

PARIS = ZoneInfo("Europe/Paris")


def h(hour, minute=0):
    return datetime(2026, 9, 14, hour, minute, tzinfo=PARIS)


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        ((h(10), h(11)), (h(11), h(12)), False),  # B2 : créneaux qui se touchent
        ((h(11), h(12)), (h(10), h(11)), False),  # B2, dans l'autre sens
        ((h(10), h(11)), (h(10, 30), h(11, 30)), True),  # chevauchement partiel
        ((h(10), h(12)), (h(10, 30), h(11)), True),  # inclusion
        ((h(10), h(11)), (h(10), h(11)), True),  # créneaux identiques
        ((h(9), h(10)), (h(11), h(12)), False),  # disjoints
    ],
)
def test_overlaps_is_strict(a, b, attendu):
    assert services.overlaps(*a, *b) is attendu


def test_adjacent_bookings_are_accepted():
    services.book("B", "2026-09-14", "10:00", "11:00", "renaud", 3)
    services.book("B", "2026-09-14", "11:00", "12:00", "nico")
    assert len(services.list_bookings("B")) == 2


def test_overlapping_booking_is_refused():
    services.book("B", "2026-09-14", "10:00", "11:00", "renaud")
    with pytest.raises(services.ConflictError):
        services.book("B", "2026-09-14", "10:30", "11:30", "nico")
