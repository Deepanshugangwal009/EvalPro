import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db

auth_bp = Blueprint("auth", __name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
MINIMUM_PASSWORD_LENGTH = 6


def get_registration_error(name, email, password, course, semester):
    if not name or not email or not password or not course or not semester:
        return "Please fill all the fields."
    if not EMAIL_PATTERN.match(email):
        return "Please enter a valid email address."
    if len(password) < MINIMUM_PASSWORD_LENGTH:
        return "Password must be at least {} characters long.".format(MINIMUM_PASSWORD_LENGTH)
    if not semester.isdigit() or not 1 <= int(semester) <= 8:
        return "Semester must be a number between 1 and 8."
    return None


def start_session(role, user_id, user_name):
    session.clear()
    session.permanent = True
    session["role"] = role
    session["user_id"] = user_id
    session["user_name"] = user_name


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()

        registration_error = get_registration_error(name, email, password, course, semester)
        if registration_error:
            flash(registration_error, "danger")
            return render_template("auth/register.html")

        existing_student = db.fetch_one(
            "SELECT student_id FROM students WHERE email = %s", (email,)
        )
        if existing_student:
            flash("This email is already registered.", "danger")
            return render_template("auth/register.html")

        db.execute(
            "INSERT INTO students (name, email, password, course, semester) VALUES (%s, %s, %s, %s, %s)",
            (name, email, generate_password_hash(password), course, int(semester)),
        )
        flash("Registration successful. You can login now.", "success")
        return redirect(url_for("auth.student_login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        student = db.fetch_one(
            "SELECT student_id, name, password FROM students WHERE email = %s", (email,)
        )
        if student and check_password_hash(student["password"], password):
            start_session("student", student["student_id"], student["name"])
            flash("Logged in successfully.", "success")
            return redirect(url_for("student.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/student_login.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = db.fetch_one(
            "SELECT admin_id, username, password FROM admins WHERE username = %s", (username,)
        )
        if admin and check_password_hash(admin["password"], password):
            start_session("admin", admin["admin_id"], admin["username"])
            flash("Logged in as admin.", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/admin_login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))
