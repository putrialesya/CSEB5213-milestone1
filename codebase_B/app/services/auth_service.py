from werkzeug.security import check_password_hash, generate_password_hash
from app.models.database import get_db

def register_customer(name, email, password):
    db = get_db()
    try:
        db.execute("INSERT INTO Users(name,email,password_hash,role) VALUES(?,?,?,'customer')",
                   (name.strip(), email.strip().lower(), generate_password_hash(password)))
        db.commit()
        return True, None
    except Exception as exc:
        db.rollback()
        if "UNIQUE constraint failed: Users.email" in str(exc):
            return False, "That email is already registered."
        return False, "Could not create the account. Please try again."

def authenticate(email, password):
    user = get_db().execute("SELECT * FROM Users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
