import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "events.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer','admin')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        venue TEXT NOT NULL,
        event_date TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        capacity INTEGER NOT NULL CHECK(capacity > 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        event_id INTEGER NOT NULL REFERENCES events(id),
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        total REAL NOT NULL CHECK(total >= 0),
        payment_status TEXT NOT NULL DEFAULT 'pending'
            CHECK(payment_status IN ('pending','paid','failed')),
        payment_reference TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Create an admin account once, using environment variables where provided.
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
    exists = db.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
    if not exists:
        db.execute(
            "INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)",
            ("Administrator", admin_email, generate_password_hash(admin_password), "admin")
        )
    count = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if count == 0:
        samples = [
            ("Indie Music Night", "An evening of live independent music and local artists.", "The Glass Hall, Kuala Lumpur", "2027-02-14T19:30", 45.00, 250),
            ("Creative Tech Summit", "Talks and workshops on design, software, and emerging technology.", "Convention Centre, Kuala Lumpur", "2027-03-06T09:00", 80.00, 180),
            ("Weekend Food Festival", "Discover local food stalls, desserts, and community vendors.", "Central Park, Petaling Jaya", "2027-03-20T11:00", 15.00, 500),
        ]
        db.executemany(
            "INSERT INTO events (title,description,venue,event_date,price,capacity) VALUES (?,?,?,?,?,?)",
            samples
        )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in as an administrator.", "info")
            return redirect(url_for("login"))
        user = get_db().execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user or user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def csrf_token():
    # Simple session token protection for state-changing form submissions.
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        submitted = request.form.get("_csrf_token", "")
        if not secrets.compare_digest(submitted, session["_csrf_token"]):
            abort(400, description="Invalid form token. Refresh the page and try again.")


@app.context_processor
def inject_globals():
    user = None
    if session.get("user_id"):
        user = get_db().execute(
            "SELECT id,name,email,role FROM users WHERE id=?", (session["user_id"],)
        ).fetchone()
    return {"current_user": user, "csrf_token": session.get("_csrf_token", "")}


@app.template_filter("money")
def money(value):
    return f"RM {float(value):,.2f}"


@app.template_filter("pretty_date")
def pretty_date(value):
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return value


@app.route("/")
def index():
    db = get_db()
    events = db.execute("SELECT * FROM events ORDER BY event_date").fetchall()
    return render_template("index.html", events=events)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
            return render_template("register.html")
        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                (name, email, generate_password_hash(password))
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")
        session.clear()
        session["user_id"] = user["id"]
        session["_csrf_token"] = secrets.token_urlsafe(32)
        flash(f"Welcome back, {user['name']}!", "success")
        destination = request.args.get("next", "")
        if destination.startswith("/") and not destination.startswith("//"):
            return redirect(destination)
        return redirect(url_for("admin_dashboard") if user["role"] == "admin" else url_for("index"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = get_db().execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event:
        abort(404)
    booked = get_db().execute(
        "SELECT COALESCE(SUM(quantity),0) FROM bookings WHERE event_id=? AND payment_status='paid'",
        (event_id,)
    ).fetchone()[0]
    return render_template("event.html", event=event, remaining=max(0, event["capacity"] - booked))


@app.route("/book/<int:event_id>", methods=["POST"])
@login_required
def book(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event:
        abort(404)
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 0
    if quantity < 1 or quantity > 10:
        flash("Choose between 1 and 10 tickets per booking.", "error")
        return redirect(url_for("event_detail", event_id=event_id))
    booked = db.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM bookings WHERE event_id=? AND payment_status='paid'",
        (event_id,)
    ).fetchone()[0]
    if booked + quantity > event["capacity"]:
        flash("Not enough tickets are available for that quantity.", "error")
        return redirect(url_for("event_detail", event_id=event_id))
    total = round(event["price"] * quantity, 2)
    cur = db.execute(
        "INSERT INTO bookings (user_id,event_id,quantity,total,payment_status) VALUES (?,?,?,?,?)",
        (session["user_id"], event_id, quantity, total, "pending")
    )
    db.commit()
    return redirect(url_for("payment", booking_id=cur.lastrowid))


@app.route("/payment/<int:booking_id>", methods=["GET", "POST"])
@login_required
def payment(booking_id):
    db = get_db()
    booking = db.execute("""
        SELECT b.*, e.title, e.event_date, e.venue
        FROM bookings b JOIN events e ON e.id=b.event_id
        WHERE b.id=? AND b.user_id=?
    """, (booking_id, session["user_id"])).fetchone()
    if not booking:
        abort(404)
    if booking["payment_status"] == "paid":
        return redirect(url_for("booking_detail", booking_id=booking_id))
    if request.method == "POST":
        action = request.form.get("payment_action")
        if action == "success":
            # Recheck capacity at payment time to avoid overbooking.
            event = db.execute("SELECT capacity FROM events WHERE id=?", (booking["event_id"],)).fetchone()
            paid = db.execute(
                "SELECT COALESCE(SUM(quantity),0) FROM bookings WHERE event_id=? AND payment_status='paid'",
                (booking["event_id"],)
            ).fetchone()[0]
            if paid + booking["quantity"] > event["capacity"]:
                db.execute("UPDATE bookings SET payment_status='failed' WHERE id=?", (booking_id,))
                db.commit()
                flash("Sorry, the remaining tickets were just taken. No payment was processed.", "error")
                return redirect(url_for("my_bookings"))
            reference = "SIM-" + secrets.token_hex(4).upper()
            db.execute(
                "UPDATE bookings SET payment_status='paid', payment_reference=? WHERE id=?",
                (reference, booking_id)
            )
            db.commit()
            flash("Simulated payment approved. Your booking is confirmed.", "success")
            return redirect(url_for("booking_detail", booking_id=booking_id))
        if action == "fail":
            db.execute("UPDATE bookings SET payment_status='failed' WHERE id=?", (booking_id,))
            db.commit()
            flash("Simulated payment declined. You were not charged.", "error")
            return redirect(url_for("my_bookings"))
    return render_template("payment.html", booking=booking)


@app.route("/my-bookings")
@login_required
def my_bookings():
    bookings = get_db().execute("""
        SELECT b.*, e.title, e.event_date, e.venue
        FROM bookings b JOIN events e ON e.id=b.event_id
        WHERE b.user_id=? ORDER BY b.created_at DESC
    """, (session["user_id"],)).fetchall()
    return render_template("my_bookings.html", bookings=bookings)


@app.route("/booking/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    booking = get_db().execute("""
        SELECT b.*, e.title, e.event_date, e.venue
        FROM bookings b JOIN events e ON e.id=b.event_id
        WHERE b.id=? AND b.user_id=?
    """, (booking_id, session["user_id"])).fetchone()
    if not booking:
        abort(404)
    return render_template("booking_detail.html", booking=booking)


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    events = db.execute("""
        SELECT e.*,
        COALESCE((SELECT SUM(quantity) FROM bookings b WHERE b.event_id=e.id AND b.payment_status='paid'),0) AS sold
        FROM events e ORDER BY event_date
    """).fetchall()
    bookings = db.execute("""
        SELECT b.id,b.quantity,b.total,b.payment_status,b.created_at,u.name AS customer,e.title
        FROM bookings b JOIN users u ON u.id=b.user_id JOIN events e ON e.id=b.event_id
        ORDER BY b.created_at DESC LIMIT 10
    """).fetchall()
    return render_template("admin.html", events=events, bookings=bookings)


@app.route("/admin/events/new", methods=["GET", "POST"])
@admin_required
def event_new():
    if request.method == "POST":
        data = event_form_data()
        if not data:
            return render_template("event_form.html", event=None, heading="Create event")
        db = get_db()
        db.execute(
            "INSERT INTO events (title,description,venue,event_date,price,capacity) VALUES (?,?,?,?,?,?)",
            data
        )
        db.commit()
        flash("Event created.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("event_form.html", event=None, heading="Create event")


@app.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def event_edit(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event:
        abort(404)
    if request.method == "POST":
        data = event_form_data()
        if not data:
            return render_template("event_form.html", event=event, heading="Edit event")
        title, description, venue, event_date, price, capacity = data
        sold = db.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM bookings WHERE event_id=? AND payment_status='paid'",
            (event_id,)
        ).fetchone()[0]
        if capacity < sold:
            flash(f"Capacity cannot be lower than the {sold} tickets already sold.", "error")
            return render_template("event_form.html", event=event, heading="Edit event")
        db.execute("""
            UPDATE events SET title=?,description=?,venue=?,event_date=?,price=?,capacity=? WHERE id=?
        """, (*data, event_id))
        db.commit()
        flash("Event updated.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("event_form.html", event=event, heading="Edit event")


@app.route("/admin/events/<int:event_id>/delete", methods=["POST"])
@admin_required
def event_delete(event_id):
    db = get_db()
    event = db.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
    if not event:
        abort(404)
    bookings_count = db.execute("SELECT COUNT(*) FROM bookings WHERE event_id=?", (event_id,)).fetchone()[0]
    if bookings_count:
        flash("This event has booking records and cannot be deleted. You can edit it instead.", "error")
    else:
        db.execute("DELETE FROM events WHERE id=?", (event_id,))
        db.commit()
        flash("Event deleted.", "success")
    return redirect(url_for("admin_dashboard"))


def event_form_data():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    venue = request.form.get("venue", "").strip()
    event_date = request.form.get("event_date", "").strip()
    try:
        price = float(request.form.get("price", ""))
        capacity = int(request.form.get("capacity", ""))
    except ValueError:
        price, capacity = -1, 0
    if not title or not description or not venue or not event_date or price < 0 or capacity < 1:
        flash("Complete every field. Price must be zero or more and capacity must be at least 1.", "error")
        return None
    try:
        datetime.fromisoformat(event_date)
    except ValueError:
        flash("Enter a valid event date and time.", "error")
        return None
    return (title, description, venue, event_date, round(price, 2), capacity)


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page or record you requested could not be found."), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
