import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from salle42 import storage
from salle42.models import Booking, Room

TZ = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]

# horaires d'ouverture du bâtiment (utilisés par free_slots)
OUVERTURE = time(8, 0)
FERMETURE = time(20, 0)


class BookingError(Exception):
    pass


class RoomNotFound(BookingError):
    def __init__(self, room_id):
        super().__init__(f"Salle inconnue : {room_id}")
        self.room_id = room_id


class BookingNotFound(BookingError):
    def __init__(self, booking_id):
        super().__init__(f"Réservation inconnue : #{booking_id}")
        self.booking_id = booking_id


class InvalidSlot(BookingError):
    pass


class CapacityError(BookingError):
    def __init__(self, attendees, room):
        super().__init__(
            f"{attendees} personnes pour {room.name} : capacité de {room.capacity} dépassée"
        )
        self.attendees = attendees
        self.room = room


class ConflictError(BookingError):
    def __init__(self, other):
        super().__init__(
            f"Conflit avec #{other.id} ({hhmm(other.start)}–{hhmm(other.end)}, {other.owner})"
        )
        self.other = other


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


def overlaps(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end


def find_conflicts(room_id, start, end):
    conflicts = []
    for b in storage.get_bookings(room_id):
        if overlaps(start, end, b.start, b.end):
            conflicts.append(b)
    return conflicts


def check_capacity(attendees, room):
    if attendees > room.capacity:
        raise CapacityError(attendees, room)


def check_slot(start, end):
    if end <= start:
        raise InvalidSlot("La fin doit être après le début")
    if end - start > timedelta(hours=12):
        raise InvalidSlot("Une réservation ne peut pas dépasser 12 heures")


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
    conflicts = find_conflicts(room.id, start_utc, end_utc)
    if conflicts:
        raise ConflictError(conflicts[0])
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
