import sqlite3
from flask import current_app, g

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS Users (
 user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('customer','admin'))
);
CREATE TABLE IF NOT EXISTS Events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
 description TEXT NOT NULL, date TEXT NOT NULL, venue TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
 created_by INTEGER NOT NULL, FOREIGN KEY(created_by) REFERENCES Users(user_id)
);
CREATE TABLE IF NOT EXISTS TicketTypes (
 ticket_type_id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
 name TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0),
 quantity_available INTEGER NOT NULL CHECK(quantity_available >= 0),
 FOREIGN KEY(event_id) REFERENCES Events(event_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Bookings (
 booking_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
 event_id INTEGER NOT NULL, booking_reference TEXT NOT NULL UNIQUE,
 booking_date TEXT NOT NULL, total_amount REAL NOT NULL CHECK(total_amount >= 0),
 status TEXT NOT NULL CHECK(status IN ('pending','confirmed','failed','cancelled')),
 attendee_name TEXT NOT NULL, attendee_email TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES Users(user_id),
 FOREIGN KEY(event_id) REFERENCES Events(event_id)
);
CREATE TABLE IF NOT EXISTS BookingItems (
 booking_item_id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER NOT NULL,
 ticket_type_id INTEGER NOT NULL, quantity INTEGER NOT NULL CHECK(quantity > 0),
 unit_price REAL NOT NULL CHECK(unit_price >= 0),
 FOREIGN KEY(booking_id) REFERENCES Bookings(booking_id) ON DELETE CASCADE,
 FOREIGN KEY(ticket_type_id) REFERENCES TicketTypes(ticket_type_id)
);
CREATE TABLE IF NOT EXISTS Payments (
 payment_id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER NOT NULL,
 amount REAL NOT NULL CHECK(amount >= 0), method TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('success','failed')),
 payment_date TEXT NOT NULL,
 FOREIGN KEY(booking_id) REFERENCES Bookings(booking_id)
);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app=None):
    from flask import current_app
    if app is None:
        app = current_app
    os_path = app.config["DATABASE"]
    import os
    os.makedirs(os.path.dirname(os_path), exist_ok=True)
    db = sqlite3.connect(os_path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    db.commit()
    db.close()
    app.teardown_appcontext(close_db)
