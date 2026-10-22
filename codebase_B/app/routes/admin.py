from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app.models.database import get_db
from app.services.event_service import create_event, update_event, remove_event, get_event, save_ticket

admin_bp = Blueprint("admin", __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    events = db.execute("SELECT e.*, COUNT(DISTINCT b.booking_id) AS booking_count FROM Events e LEFT JOIN Bookings b ON b.event_id=e.event_id GROUP BY e.event_id ORDER BY e.date").fetchall()
    bookings = db.execute("SELECT b.*,u.name AS customer_name,e.name AS event_name FROM Bookings b JOIN Users u ON u.user_id=b.user_id JOIN Events e ON e.event_id=b.event_id ORDER BY b.booking_date DESC").fetchall()
    return render_template("admin_dashboard.html", events=events, bookings=bookings)

@admin_bp.route("/events/new", methods=["GET","POST"])
@admin_required
def new_event():
    if request.method == "POST":
        name=request.form.get("name","").strip(); desc=request.form.get("description","").strip()
        event_date=request.form.get("date",""); venue=request.form.get("venue","").strip()
        if not all((name,desc,event_date,venue)):
            flash("All event fields are required.", "error")
        else:
            create_event(name,desc,event_date,venue,session["user_id"])
            flash("Event created. Add ticket types from the dashboard.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("event_form.html", event=None)

@admin_bp.route("/events/<int:event_id>/edit", methods=["GET","POST"])
@admin_required
def edit_event(event_id):
    db=get_db()
    event=db.execute("SELECT * FROM Events WHERE event_id=?",(event_id,)).fetchone()
    if not event: abort(404)
    if request.method == "POST":
        fields=[request.form.get(k,"").strip() for k in ("name","description","date","venue")]
        status=request.form.get("status","active")
        if not all(fields) or status not in ("active","inactive"):
            flash("Complete all fields and choose a valid status.", "error")
        else:
            update_event(event_id,*fields,status)
            flash("Event updated.", "success")
            return redirect(url_for("admin.dashboard"))
    tickets=db.execute("SELECT * FROM TicketTypes WHERE event_id=? ORDER BY ticket_type_id",(event_id,)).fetchall()
    return render_template("event_form.html", event=event, tickets=tickets)

@admin_bp.route("/events/<int:event_id>/remove", methods=["POST"])
@admin_required
def delete_event(event_id):
    msg=remove_event(event_id)
    flash(msg,"success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/events/<int:event_id>/tickets", methods=["POST"])
@admin_required
def ticket_save(event_id):
    event,_=get_event(event_id,include_inactive=True)
    if not event: abort(404)
    try:
        name=request.form.get("name","").strip()
        price=float(request.form.get("price","-1"))
        quantity=int(request.form.get("quantity","-1"))
        ticket_id=request.form.get("ticket_type_id","")
        ticket_id=int(ticket_id) if ticket_id else None
        if not name or price < 0 or quantity < 0 or price != price or price == float("inf"):
            raise ValueError
        save_ticket(event_id,ticket_id,name,round(price,2),quantity)
        flash("Ticket type saved.","success")
    except (ValueError, TypeError):
        flash("Enter a ticket name, a non-negative price, and a non-negative whole-number quantity.","error")
    return redirect(url_for("admin.edit_event",event_id=event_id))
