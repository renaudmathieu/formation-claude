---
paths: ["salle42/**/*.py"]
---

# Règles métier de Salle42

Ces règles viennent de la spécification, pas du code. Si le code les contredit, c'est le code qui a tort : le signaler avant de corriger.

## Conflits
- Deux réservations d'une même salle sont en conflit si leurs intervalles se chevauchent **strictement** : `a.debut < b.fin et b.debut < a.fin`.
- Des créneaux qui se touchent (10:00–11:00 puis 11:00–12:00) ne sont pas en conflit.
- Seules les réservations actives comptent : une réservation annulée libère son créneau.

## Capacité
- `attendees` est optionnel. Absent, aucune vérification de capacité.
- Présent, il doit être inférieur ou égal à la capacité de la salle, sinon la réservation est refusée avec un message clair (jamais un plantage).

## Créneaux
- La fin est strictement après le début, et une réservation dure au plus 12 heures.
- Les heures saisies sont en heure de Paris ; le stockage est en UTC.

## Annulation
- Annuler passe le statut à `cancelled` ; on ne supprime jamais une ligne de `bookings`.
- Annuler deux fois la même réservation n'est pas une erreur.
