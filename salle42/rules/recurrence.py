"""Récurrence hebdomadaire (F1)."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")


def weekly_slots(start: datetime, end: datetime, count: int) -> list[tuple[datetime, datetime]]:
    """Calcule `count` créneaux hebdomadaires à partir d'un premier créneau.

    Les semaines s'ajoutent en heure de Paris : une réunion de 10:00 reste à 10:00
    après un changement d'heure, même si son heure UTC change.

    Args:
        start: Début du premier créneau, en UTC.
        end: Fin du premier créneau, en UTC.
        count: Nombre d'occurrences, la première comprise.

    Returns:
        Les couples (début, fin) en UTC, dans l'ordre chronologique.
    """
    local_start = start.astimezone(PARIS)
    local_end = end.astimezone(PARIS)
    return [
        (
            (local_start + timedelta(weeks=i)).astimezone(UTC),
            (local_end + timedelta(weeks=i)).astimezone(UTC),
        )
        for i in range(count)
    ]
