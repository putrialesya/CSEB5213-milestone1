from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from app.services.event_service import get_event
from app.services.booking_service import create_booking, get_booking_for_user, history_for_user

bookings_bp = Blueprint("bookings", __name__)

def customer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to book tickets.", "error")
            return redirect(url_for("auth.login"))
        if session.get("role") != "customer":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@bookings_bp.route("/events/<int:event_id>/book", methods=["GET","POST"])
@customer_required
def book(event_id):
    event, tickets = get_event(event_id)
    if not event:
        abort(404)
    if request.method == "POST":
        try:
            ticket_id = int(request.form.get("ticket_type_id","0"))
            quantity = int(request.form.get("quantity","0"))
            attendee_name = request.form.get("attendee_name","").strip()
            attendee_email = request.form.get("attendee_email","").strip()
            method = request.form.get("method","card")
            simulation = request.form.get("payment_result","success")
            if not attendee_name or "@" not in attendee_email:
                raise ValueError("Enter a valid attendee name and email.")
            if method not in ("card","online_banking","ewallet"):
                raise ValueError("Choose a valid payment method.")
            if simulation not in ("success","failed"):
                raise ValueError("Choose a valid simulated payment result.")
            result = create_booking(session["user_id"], event_id, ticket_id, quantity, attendee_name, attendee_email, method, simulation == "success")
            if result["status"] == "failed":
                flash("Simulated payment failed. Your booking is not confirmed and no tickets were deducted.", "error")
            return redirect(url_for("bookings.confirmation", booking_id=result["booking_id"]))
        except (ValueError, TypeError) as exc:
            flash(str(exc) or "Please check your booking details.", "error")
        except Exception:
            flash("We couldn't complete the booking. Please try again.", "error")
    return render_template("book.html", event=event, tickets=tickets)

@bookings_bp.route("/booking/<int:booking_id>")
@customer_required
def confirmation(booking_id):
    booking = get_booking_for_user(booking_id, session["user_id"])
    if not booking:
        abort(404)
    return render_template("confirmation.html", booking=booking)

@bookings_bp.route("/my-bookings")
@customer_required
def history():
    return render_template("history.html", bookings=history_for_user(session["user_id"]))
