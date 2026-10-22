from flask import Blueprint, render_template, request, abort
from app.services.event_service import list_events, get_event

events_bp = Blueprint("events", __name__)

@events_bp.route("/")
def index():
    keyword = request.args.get("q","")
    return render_template("events.html", events=list_events(keyword), keyword=keyword)

@events_bp.route("/events/<int:event_id>")
def detail(event_id):
    event, tickets = get_event(event_id)
    if not event:
        abort(404)
    return render_template("event_detail.html", event=event, tickets=tickets)
