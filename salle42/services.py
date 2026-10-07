import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from salle42 import storage
from salle42.errors import (
    BookingError,
    BookingNotFound,
    CapacityError,
    ConflictError,
    InvalidSlot,
    RoomNotFound,
)
from salle42.models import Booking, Room
from salle42.rules import conflicts
from salle42.rules.capacity import check_capacity
from salle42.rules.conflicts import overlaps
from salle42.rules.recurrence import weekly_slots
from salle42.rules.slots import check_slot

# Réexportés pour la CLI, l'API et les tests : `services.ConflictError`, etc.
__all__ = [
    "BookingError",
    "BookingNotFound",
    "CapacityError",
    "ConflictError",
    "InvalidSlot",
    "RoomNotFound",
    "check_capacity",
    "check_slot",
    "overlaps",
]

TZ = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]

# horaires d'ouverture du bâtiment (utilisés par free_slots)
OUVERTURE = time(8, 0)
FERMETURE = time(20, 0)


# ---------------------------------------------------------------- dates


def parse_day(day):
    try:
        return date.fromisoformat(day)
    except ValueError:
        raise InvalidSlot(f"Date invalide : {day} (attendu : AAAA-MM-JJ)")


def parse_hour(hour):
    try:
        h, m = hour.split(":")
        return time(int(h), int(m))
    except ValueError:
        raise InvalidSlot(f"Heure invalide : {hour} (attendu : HH:MM)")


def to_utc(day, hour):
    local = datetime.combine(parse_day(day), parse_hour(hour), tzinfo=TZ)
    return local.astimezone(UTC)


def to_local(dt):
    return dt.astimezone(TZ)


def hhmm(dt):
    return to_local(dt).strftime("%H:%M")


def jour_fr(dt):
    local = to_local(dt)
    return f"{JOURS[local.weekday()]} {local.strftime('%d/%m')}"


# ---------------------------------------------------------------- règles


def find_conflicts(room_id, start, end):
    return conflicts.find_conflicts(start, end, storage.get_bookings(room_id))


def conflict_error(other):
    return ConflictError(
        other,
        f"Conflit avec #{other.id} "
        f"({jour_fr(other.start)} {hhmm(other.start)}–{hhmm(other.end)}, {other.owner})",
    )


# ---------------------------------------------------------------- réservations


def list_rooms():
    return storage.get_rooms()


def get_room_or_fail(room_id):
    room = storage.get_room(room_id.upper())
    if room is None:
        raise RoomNotFound(room_id)
    return room


def book(room_id, day, start, end, owner, attendees=None):
    room = get_room_or_fail(room_id)
    start_utc = to_utc(day, start)
    end_utc = to_utc(day, end)
    check_slot(start_utc, end_utc)
    check_capacity(attendees, room)
    en_conflit = find_conflicts(room.id, start_utc, end_utc)
    if en_conflit:
        raise conflict_error(en_conflit[0])
    booking = Booking(
        id=uuid.uuid4().hex[:4],
        room_id=room.id,
        start=start_utc,
        end=end_utc,
        owner=owner,
        attendees=attendees,
    )
    storage.insert_booking(booking)
    return booking


def book_weekly(room_id, day, start, end, owner, weeks, attendees=None):
    """Crée une réservation par semaine pendant `weeks` semaines, tout ou rien (F1).

    Args:
        room_id: Code de la salle (A, B, C).
        day: Date de la première occurrence, AAAA-MM-JJ.
        start: Heure de début, HH:MM, heure de Paris.
        end: Heure de fin, HH:MM, heure de Paris.
        owner: Qui réserve.
        weeks: Nombre d'occurrences, au moins 1.
        attendees: Nombre de personnes, optionnel.

    Returns:
        Les réservations créées, dans l'ordre chronologique.

    Raises:
        InvalidSlot: Si `weeks` est inférieur à 1 ou si le créneau est invalide.
        CapacityError: Si `attendees` dépasse la capacité de la salle.
        ConflictError: Au premier créneau en conflit ; aucune réservation n'est alors créée.
    """
    if weeks < 1:
        raise InvalidSlot("--weekly attend un nombre de semaines au moins égal à 1")
    room = get_room_or_fail(room_id)
    start_utc = to_utc(day, start)
    end_utc = to_utc(day, end)
    check_slot(start_utc, end_utc)
    check_capacity(attendees, room)
    bookings = []
    for slot_start, slot_end in weekly_slots(start_utc, end_utc, weeks):
        en_conflit = find_conflicts(room.id, slot_start, slot_end)
        if en_conflit:
            raise conflict_error(en_conflit[0])
        bookings.append(
            Booking(
                id=uuid.uuid4().hex[:4],
                room_id=room.id,
                start=slot_start,
                end=slot_end,
                owner=owner,
                attendees=attendees,
            )
        )
    storage.insert_bookings(bookings)
    return bookings


def book_from_dict(payload):
    # utilisé par l'API
    if not payload.get("owner"):
        raise BookingError("owner est obligatoire")
    return book(
        payload["room_id"],
        payload["day"],
        payload["start"],
        payload["end"],
        payload["owner"],
        payload.get("attendees"),
    )


def cancel(booking_id):
    booking = storage.get_booking(booking_id.lstrip("#"))
    if booking is None:
        raise BookingNotFound(booking_id)
    if booking.status == "cancelled":
        return booking
    storage.set_status(booking.id, "cancelled")
    booking.status = "cancelled"
    return booking


def list_bookings(room_id=None, day=None):
    bookings = storage.get_bookings(room_id.upper() if room_id else None)
    if day:
        d = date.fromisoformat(day)
        bookings = [b for b in bookings if to_local(b.start).date() == d]
    return [b for b in bookings if b.status != "cancelled"]


def free_slots(room_id, day):
    # TODO: pas encore branché dans la CLI (demande #9)
    room = get_room_or_fail(room_id)
    d = parse_day(day)
    cursor = datetime.combine(d, OUVERTURE, tzinfo=TZ).astimezone(UTC)
    closing = datetime.combine(d, FERMETURE, tzinfo=TZ).astimezone(UTC)
    slots = []
    for b in list_bookings(room.id, day):
        if b.start > cursor:
            slots.append((cursor, b.start))
        cursor = max(cursor, b.end)
    if cursor < closing:
        slots.append((cursor, closing))
    return slots


def occupancy_rate(room_id, day):
    # demandé par les services généraux, jamais livré
    total = timedelta(hours=12)
    used = timedelta()
    for b in list_bookings(room_id, day):
        used += b.end - b.start
    return round(used / total * 100, 1)


# ---------------------------------------------------------------- affichage


def format_room(room: Room):
    return f"{room.id}  {room.name:<11} {room.capacity:>2} pers.  [{', '.join(room.equipment)}]"


def format_booking(b: Booking):
    room = storage.get_room(b.room_id)
    name = room.name if room else b.room_id
    who = b.owner if b.attendees is None else f"{b.owner}, {b.attendees} pers."
    line = f"Réservation #{b.id} : {name}, {jour_fr(b.start)} {hhmm(b.start)}–{hhmm(b.end)} ({who})"
    if b.status == "cancelled":
        line += " [annulée]"
    return line


def format_series(bookings):
    """Résumé d'une série hebdomadaire : « 4 réservations créées (14/09 → 05/10) »."""
    first, last = bookings[0], bookings[-1]
    period = f"{to_local(first.start):%d/%m} → {to_local(last.start):%d/%m}"
    return f"{len(bookings)} réservations créées ({period})"


def format_booking_short(b: Booking):
    # même chose que format_booking mais sans la salle (pour list --room)
    who = b.owner if b.attendees is None else f"{b.owner}, {b.attendees} pers."
    return f"#{b.id}  {jour_fr(b.start)} {hhmm(b.start)}–{hhmm(b.end)}  {who}"


def booking_to_dict(b: Booking):
    return {
        "id": b.id,
        "room_id": b.room_id,
        "start": b.start.isoformat(),
        "end": b.end.isoformat(),
        "owner": b.owner,
        "attendees": b.attendees,
        "status": b.status,
    }


def room_to_dict(r: Room):
    return {"id": r.id, "name": r.name, "capacity": r.capacity, "equipment": r.equipment}
