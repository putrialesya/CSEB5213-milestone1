"""Create tables, an admin account, and sample events. Safe to run repeatedly."""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from app.models.database import get_db, init_db

app = create_app()
with app.app_context():
    init_db()
    db = get_db()
    admin_email = "admin@ticketdemo.local"
    row = db.execute("SELECT user_id FROM Users WHERE email = ?", (admin_email,)).fetchone()
    if not row:
        cur = db.execute(
            "INSERT INTO Users (name,email,password_hash,role) VALUES (?,?,?,?)",
            ("Demo Admin", admin_email, generate_password_hash("Admin123!"), "admin")
        )
        admin_id = cur.lastrowid
    else:
        admin_id = row["user_id"]

    samples = [
        ("Kuala Lumpur Music Night", "A live music showcase featuring local artists.", date.today() + timedelta(days=30), "Kuala Lumpur", [
            ("General Admission", 45.00, 300), ("VIP", 120.00, 50)]),
        ("Malaysia Tech & Innovation Expo", "Discover new ideas, demos, and talks from the tech community.", date.today() + timedelta(days=45), "MITEC, Kuala Lumpur", [
            ("Standard", 25.00, 500), ("Student", 10.00, 150)]),
        ("Weekend Food Festival", "A weekend of local flavours, food stalls, and family activities.", date.today() + timedelta(days=60), "Shah Alam", [
            ("Day Pass", 15.00, 400)])
    ]
    for name, desc, event_date, venue, ticket_types in samples:
        existing = db.execute("SELECT event_id FROM Events WHERE name = ?", (name,)).fetchone()
        if existing:
            continue
        cur = db.execute(
            "INSERT INTO Events (name,description,date,venue,status,created_by) VALUES (?,?,?,?,?,?)",
            (name, desc, event_date.isoformat(), venue, "active", admin_id)
        )
        event_id = cur.lastrowid
        for ticket_name, price, quantity in ticket_types:
            db.execute(
                "INSERT INTO TicketTypes (event_id,name,price,quantity_available) VALUES (?,?,?,?)",
                (event_id, ticket_name, price, quantity)
            )
    db.commit()
    print("Seed complete.")
    print(f"Admin login: {admin_email} / Admin123!")
    print("Change the demo password before any real deployment.")
