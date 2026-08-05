from functools import wraps

from flask import flash, redirect, session, url_for


def role_required(role, login_endpoint):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("Please login to continue.", "warning")
                return redirect(url_for(login_endpoint))
            return view(*args, **kwargs)
        return wrapper
    return decorator


login_required = role_required("student", "auth.student_login")
admin_required = role_required("admin", "auth.admin_login")
