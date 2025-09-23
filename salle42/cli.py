from typing import Annotated

import typer

from salle42 import services

app = typer.Typer(help="Salle42 : réservation de salles de réunion", no_args_is_help=True)


@app.command()
def rooms():
    """Liste les salles."""
    for room in services.list_rooms():
        typer.echo(services.format_room(room))


@app.command()
def book(
    room: str,
    day: str,
    start: str,
    end: str,
    by: Annotated[str, typer.Option("--by", help="Qui réserve")],
    attendees: Annotated[
        int | None, typer.Option("--attendees", help="Nombre de personnes")
    ] = None,
):
    """Réserve une salle : salle42 book B 2026-09-14 10:00 11:00 --by renaud"""
    try:
        booking = services.book(room, day, start, end, by, attendees)
    except services.BookingError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
    typer.echo("✓ " + services.format_booking(booking))


@app.command()
def cancel(booking_id: str):
    """Annule une réservation."""
    try:
        booking = services.cancel(booking_id)
    except services.BookingError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
    typer.echo(f"✓ #{booking.id} annulée, créneau libéré")


@app.command("list")
def list_bookings(
    room: Annotated[str | None, typer.Option("--room", help="Filtrer par salle")] = None,
    day: Annotated[str | None, typer.Option("--date", help="AAAA-MM-JJ")] = None,
):
    """Liste les réservations actives."""
    bookings = services.list_bookings(room, day)
    if not bookings:
        typer.echo("Aucune réservation.")
    for b in bookings:
        typer.echo(services.format_booking(b))


if __name__ == "__main__":
    app()
