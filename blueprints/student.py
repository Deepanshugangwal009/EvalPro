from flask import Blueprint, render_template, session

import db
from helpers.decorators import login_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_exam_status(exam):
    if exam["attempt_id"]:
        return "Attempted"
    if exam["is_upcoming"]:
        return "Upcoming"
    if exam["is_closed"]:
        return "Closed"
    return "Available"


def get_student_exams(student_id, exam_id=None):
    query = (
        "SELECT e.exam_id, e.exam_name, s.subject_name, e.duration, e.total_marks, e.exam_date, "
        "CAST(e.start_time AS CHAR) AS start_time, CAST(e.end_time AS CHAR) AS end_time, "
        "a.attempt_id, "
        "TIMESTAMP(e.exam_date, e.start_time) > NOW() AS is_upcoming, "
        "TIMESTAMP(e.exam_date, e.end_time) < NOW() AS is_closed "
        "FROM exams e "
        "JOIN subjects s ON e.subject_id = s.subject_id "
        "LEFT JOIN attempts a ON a.exam_id = e.exam_id AND a.student_id = %s "
        "WHERE e.is_active = 1"
    )
    params = [student_id]
    if exam_id:
        query += " AND e.exam_id = %s"
        params.append(exam_id)

    exams = db.fetch_all(query + " ORDER BY e.exam_date, e.start_time", tuple(params))
    for exam in exams:
        exam["status"] = get_exam_status(exam)
    return exams


def get_student_exam(student_id, exam_id):
    exams = get_student_exams(student_id, exam_id)
    return exams[0] if exams else None


@student_bp.route("/dashboard")
@login_required
def dashboard():
    student_id = session["user_id"]
    exams = get_student_exams(student_id)
    available_count = sum(1 for exam in exams if exam["status"] == "Available")

    attempt_summary = db.fetch_one(
        "SELECT COUNT(*) AS attempted_count FROM attempts WHERE student_id = %s", (student_id,)
    )
    result_summary = db.fetch_one(
        "SELECT IFNULL(AVG(percentage), 0) AS average_percentage FROM results WHERE student_id = %s",
        (student_id,),
    )

    return render_template(
        "student/dashboard.html",
        available_count=available_count,
        attempted_count=attempt_summary["attempted_count"],
        average_percentage=result_summary["average_percentage"],
    )


@student_bp.route("/exams")
@login_required
def exams():
    return render_template("student/exam_list.html", exams=get_student_exams(session["user_id"]))
