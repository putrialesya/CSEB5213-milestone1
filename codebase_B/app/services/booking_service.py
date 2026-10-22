from datetime import datetime, timezone
import secrets, string
from app.models.database import get_db

def make_reference():
    alphabet = string.ascii_uppercase + string.digits
    return "T2U-" + "".join(secrets.choice(alphabet) for _ in range(10))

def create_booking(user_id, event_id, ticket_type_id, quantity, attendee_name, attendee_email, method, simulate_success):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        event = db.execute("SELECT * FROM Events WHERE event_id=? AND status='active'", (event_id,)).fetchone()
        ticket = db.execute("SELECT * FROM TicketTypes WHERE ticket_type_id=? AND event_id=?",
                            (ticket_type_id, event_id)).fetchone()
        if not event or not ticket:
            raise ValueError("This event or ticket type is no longer available.")
        if quantity < 1 or quantity > 10:
            raise ValueError("Choose a quantity between 1 and 10.")
        if ticket["price"] < 0:
            raise ValueError("Invalid ticket price.")
        if ticket["quantity_available"] < quantity:
            raise ValueError("Not enough tickets are available. Please choose a smaller quantity.")
        total = round(float(ticket["price"]) * quantity, 2)
        reference = make_reference()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        booking_status = "confirmed" if simulate_success else "failed"
        cur = db.execute("""INSERT INTO Bookings(user_id,event_id,booking_reference,booking_date,total_amount,status,attendee_name,attendee_email)
            VALUES(?,?,?,?,?,?,?,?)""", (user_id,event_id,reference,now,total,booking_status,attendee_name.strip(),attendee_email.strip().lower()))
        booking_id = cur.lastrowid
        db.execute("INSERT INTO BookingItems(booking_id,ticket_type_id,quantity,unit_price) VALUES(?,?,?,?)",
                   (booking_id,ticket_type_id,quantity,ticket["price"]))
        db.execute("INSERT INTO Payments(booking_id,amount,method,status,payment_date) VALUES(?,?,?,?,?)",
                   (booking_id,total,method,"success" if simulate_success else "failed",now))
        if simulate_success:
            changed = db.execute("""UPDATE TicketTypes SET quantity_available=quantity_available-?
                WHERE ticket_type_id=? AND quantity_available>=?""", (quantity,ticket_type_id,quantity))
            if changed.rowcount != 1:
                raise ValueError("Tickets sold out while you were booking. Please try again.")
        db.commit()
        return {"booking_id": booking_id, "reference": reference, "total": total, "status": booking_status}
    except Exception:
        db.rollback()
        raise

def get_booking_for_user(booking_id, user_id):
    db = get_db()
    return db.execute("""SELECT b.*,e.name AS event_name,e.date AS event_date,e.venue,
        p.method,p.status AS payment_status,p.payment_date,bi.quantity,bi.unit_price,t.name AS ticket_name
        FROM Bookings b JOIN Events e ON e.event_id=b.event_id
        LEFT JOIN Payments p ON p.booking_id=b.booking_id
        LEFT JOIN BookingItems bi ON bi.booking_id=b.booking_id
        LEFT JOIN TicketTypes t ON t.ticket_type_id=bi.ticket_type_id
        WHERE b.booking_id=? AND b.user_id=?""", (booking_id,user_id)).fetchone()

def history_for_user(user_id):
    return get_db().execute("SELECT b.*,e.name AS event_name,e.date AS event_date FROM Bookings b JOIN Events e ON e.event_id=b.event_id WHERE b.user_id=? ORDER BY b.booking_date DESC", (user_id,)).fetchall()
