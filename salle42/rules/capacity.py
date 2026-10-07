"""Capacité des salles."""

from salle42.errors import CapacityError
from salle42.models import Room


def check_capacity(attendees: int | None, room: Room) -> None:
    """Vérifie que l'effectif annoncé tient dans la salle.

    Args:
        attendees: Nombre de personnes, optionnel. Absent, rien n'est vérifié.
        room: La salle demandée.

    Raises:
        CapacityError: Si `attendees` dépasse la capacité de la salle.
    """
    if attendees is not None and attendees > room.capacity:
        raise CapacityError(attendees, room)
