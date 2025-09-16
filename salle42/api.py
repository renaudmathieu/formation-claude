from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from salle42 import services

app = FastAPI(title="Salle42")


class BookingIn(BaseModel):
    room_id: str
    day: str
    start: str
    end: str
    owner: str
    attendees: int | None = None


@app.get("/rooms")
def get_rooms():
    return [services.room_to_dict(r) for r in services.list_rooms()]


@app.get("/bookings")
def get_bookings(room_id: str | None = None, day: str | None = None):
    return [services.booking_to_dict(b) for b in services.list_bookings(room_id, day)]


@app.post("/bookings", status_code=201)
def post_booking(payload: BookingIn):
    try:
        booking = services.book_from_dict(payload.model_dump())
    except services.RoomNotFound as e:
        raise HTTPException(404, str(e))
    except services.ConflictError as e:
        raise HTTPException(409, str(e))
    except services.BookingError as e:
        raise HTTPException(400, str(e))
    return services.booking_to_dict(booking)


@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    try:
        booking = services.cancel(booking_id)
    except services.BookingNotFound as e:
        raise HTTPException(404, str(e))
    return services.booking_to_dict(booking)
