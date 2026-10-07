"""Détection des conflits entre réservations d'une même salle."""

from collections.abc import Iterable
from datetime import datetime

from salle42.models import Booking


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Dit si deux intervalles se chevauchent strictement.

    Des créneaux qui se touchent (10:00–11:00 puis 11:00–12:00) ne sont pas en conflit.
    """
    return a_start < b_end and b_start < a_end


def find_conflicts(start: datetime, end: datetime, bookings: Iterable[Booking]) -> list[Booking]:
    """Renvoie les réservations actives qui chevauchent le créneau demandé.

    Args:
        start: Début du créneau demandé, en UTC.
        end: Fin du créneau demandé, en UTC.
        bookings: Les réservations existantes de la salle, quel que soit leur statut.

    Returns:
        Les réservations en conflit, dans l'ordre reçu. Une réservation annulée
        libère son créneau et n'est jamais en conflit.
    """
    return [b for b in bookings if b.status != "cancelled" and overlaps(start, end, b.start, b.end)]
