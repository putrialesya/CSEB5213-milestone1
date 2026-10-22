import os
from flask import Flask
from config import Config
from app.models.database import init_db
from app.routes.auth import auth_bp
from app.routes.events import events_bp
from app.routes.bookings import bookings_bp
from app.routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    init_db(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    return app
