"""Validité d'un créneau."""

from datetime import datetime, timedelta

from salle42.errors import InvalidSlot

DUREE_MAX = timedelta(hours=12)


def check_slot(start: datetime, end: datetime) -> None:
    """Vérifie qu'un créneau a une fin après son début et dure au plus 12 heures.

    Raises:
        InvalidSlot: Si le créneau ne respecte pas ces deux règles.
    """
    if end <= start:
        raise InvalidSlot("La fin doit être après le début")
    if end - start > DUREE_MAX:
        raise InvalidSlot("Une réservation ne peut pas dépasser 12 heures")
