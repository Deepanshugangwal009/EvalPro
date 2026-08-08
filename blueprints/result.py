from flask import Blueprint, flash, redirect, render_template, session, url_for

import db
from helpers.decorators import login_required

result_bp = Blueprint("result", __name__, url_prefix="/result")


@result_bp.route("/<int:exam_id>")
@login_required
def view_result(exam_id):
    result = db.fetch_one(
        "SELECT e.exam_name, e.exam_date, s.subject_name, r.total_marks, r.obtained_marks, "
        "r.percentage, r.result_status "
        "FROM results r "
        "JOIN exams e ON r.exam_id = e.exam_id "
        "JOIN subjects s ON e.subject_id = s.subject_id "
        "WHERE r.student_id = %s AND r.exam_id = %s",
        (session["user_id"], exam_id),
    )
    if not result:
        flash("Result is not available for this exam.", "danger")
        return redirect(url_for("student.exams"))

    return render_template("result/result.html", result=result)
