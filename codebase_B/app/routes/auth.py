from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import register_customer, authenticate

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        password = request.form.get("password","")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
        else:
            ok, error = register_customer(name,email,password)
            if ok:
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("auth.login"))
            flash(error, "error")
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form.get("email",""), request.form.get("password",""))
        if not user:
            flash("Email or password is incorrect.", "error")
        else:
            session.clear()
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            return redirect(url_for("admin.dashboard") if user["role"] == "admin" else url_for("events.index"))
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("events.index"))
