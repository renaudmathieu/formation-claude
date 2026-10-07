"""Erreurs métier de Salle42, affichées telles quelles par la CLI et l'API."""


class BookingError(Exception):
    """Erreur métier : la demande est refusée avec un message lisible."""


class RoomNotFound(BookingError):
    def __init__(self, room_id):
        super().__init__(f"Salle inconnue : {room_id}")
        self.room_id = room_id


class BookingNotFound(BookingError):
    def __init__(self, booking_id):
        super().__init__(f"Réservation inconnue : #{booking_id}")
        self.booking_id = booking_id


class InvalidSlot(BookingError):
    """Créneau, date ou heure invalide."""


class CapacityError(BookingError):
    def __init__(self, attendees, room):
        super().__init__(
            f"{attendees} personnes pour {room.name} : capacité de {room.capacity} dépassée"
        )
        self.attendees = attendees
        self.room = room


class ConflictError(BookingError):
    def __init__(self, other, message):
        super().__init__(message)
        self.other = other
