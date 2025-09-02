from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Room:
    id: str
    name: str
    capacity: int
    equipment: list[str] = field(default_factory=list)


@dataclass
class Booking:
    id: str
    room_id: str
    start: datetime  # UTC
    end: datetime  # UTC
    owner: str
    attendees: int | None = None
    status: str = "active"
