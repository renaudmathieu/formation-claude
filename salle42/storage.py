import sqlite3
from datetime import datetime

from salle42.models import Booking, Room

DB_PATH = "salle42.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    equipment TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(id),
    start_utc TEXT NOT NULL,
    end_utc TEXT NOT NULL,
    owner TEXT NOT NULL,
    attendees INTEGER,
    status TEXT NOT NULL DEFAULT 'active'
);
"""

# les salles du 4e étage
ROOMS = [
    ("A", "Aquarium", 6, "écran,visio"),
    ("B", "Bocal", 4, "tableau blanc"),
    ("C", "Cathédrale", 20, "écran,visio,micro"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        conn.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", ROOMS)
        conn.commit()
    return conn


def _room(row):
    equipment = [e for e in row["equipment"].split(",") if e]
    return Room(row["id"], row["name"], row["capacity"], equipment)


def _booking(row):
    return Booking(
        id=row["id"],
        room_id=row["room_id"],
        start=datetime.fromisoformat(row["start_utc"]),
        end=datetime.fromisoformat(row["end_utc"]),
        owner=row["owner"],
        attendees=row["attendees"],
        status=row["status"],
    )


def get_rooms():
    conn = get_conn()
    try:
        return [_room(r) for r in conn.execute("SELECT * FROM rooms ORDER BY id")]
    finally:
        conn.close()


def get_room(room_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        return _room(row) if row else None
    finally:
        conn.close()


def get_bookings(room_id=None):
    conn = get_conn()
    try:
        if room_id:
            rows = conn.execute(
                "SELECT * FROM bookings WHERE room_id = ? ORDER BY start_utc", (room_id,)
            )
        else:
            rows = conn.execute("SELECT * FROM bookings ORDER BY start_utc")
        return [_booking(r) for r in rows]
    finally:
        conn.close()


def get_booking(booking_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        return _booking(row) if row else None
    finally:
        conn.close()


def insert_booking(b):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                b.id,
                b.room_id,
                b.start.isoformat(),
                b.end.isoformat(),
                b.owner,
                b.attendees,
                b.status,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_bookings(bookings):
    """Insère plusieurs réservations dans une seule transaction : toutes ou aucune."""
    conn = get_conn()
    try:
        with conn:
            conn.executemany(
                "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        b.id,
                        b.room_id,
                        b.start.isoformat(),
                        b.end.isoformat(),
                        b.owner,
                        b.attendees,
                        b.status,
                    )
                    for b in bookings
                ],
            )
    finally:
        conn.close()


def set_status(booking_id, status):
    conn = get_conn()
    try:
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        conn.commit()
    finally:
        conn.close()
