from app.models.database import get_db

def list_events(keyword=""):
    db = get_db()
    if keyword.strip():
        term = f"%{keyword.strip()}%"
        return db.execute("""SELECT * FROM Events WHERE status='active'
            AND (name LIKE ? OR description LIKE ? OR venue LIKE ?) ORDER BY date""", (term,term,term)).fetchall()
    return db.execute("SELECT * FROM Events WHERE status='active' ORDER BY date").fetchall()

def get_event(event_id, include_inactive=False):
    db = get_db()
    condition = "" if include_inactive else " AND status='active'"
    event = db.execute(f"SELECT * FROM Events WHERE event_id=?{condition}", (event_id,)).fetchone()
    if not event:
        return None, []
    tickets = db.execute("SELECT * FROM TicketTypes WHERE event_id=? ORDER BY price", (event_id,)).fetchall()
    return event, tickets

def create_event(name, description, event_date, venue, admin_id):
    db = get_db()
    cur = db.execute("INSERT INTO Events(name,description,date,venue,status,created_by) VALUES(?,?,?,?, 'active',?)",
                     (name, description, event_date, venue, admin_id))
    db.commit()
    return cur.lastrowid

def update_event(event_id, name, description, event_date, venue, status):
    db = get_db()
    db.execute("UPDATE Events SET name=?,description=?,date=?,venue=?,status=? WHERE event_id=?",
               (name, description, event_date, venue, status, event_id))
    db.commit()

def remove_event(event_id):
    db = get_db()
    count = db.execute("SELECT COUNT(*) AS n FROM Bookings WHERE event_id=?", (event_id,)).fetchone()["n"]
    if count:
        db.execute("UPDATE Events SET status='inactive' WHERE event_id=?", (event_id,))
        message = "Event has bookings, so it was marked inactive instead of deleted."
    else:
        db.execute("DELETE FROM TicketTypes WHERE event_id=?", (event_id,))
        db.execute("DELETE FROM Events WHERE event_id=?", (event_id,))
        message = "Event removed."
    db.commit()
    return message

def save_ticket(event_id, ticket_id, name, price, quantity):
    db = get_db()
    if ticket_id:
        db.execute("UPDATE TicketTypes SET name=?,price=?,quantity_available=? WHERE ticket_type_id=? AND event_id=?",
                   (name, price, quantity, ticket_id, event_id))
    else:
        db.execute("INSERT INTO TicketTypes(event_id,name,price,quantity_available) VALUES(?,?,?,?)",
                   (event_id, name, price, quantity))
    db.commit()
