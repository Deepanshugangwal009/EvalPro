from flask import Blueprint, flash, redirect, render_template, request, url_for

import db
from helpers.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def subject_code_exists(subject_code, subject_id=0):
    subject = db.fetch_one(
        "SELECT subject_id FROM subjects WHERE subject_code = %s AND subject_id <> %s",
        (subject_code, subject_id),
    )
    return subject is not None


def get_subject_list():
    return db.fetch_all(
        "SELECT subject_id, subject_name, subject_code FROM subjects ORDER BY subject_name"
    )


def get_exam(exam_id):
    return db.fetch_one(
        "SELECT e.exam_id, e.exam_name, e.total_marks, s.subject_name "
        "FROM exams e JOIN subjects s ON e.subject_id = s.subject_id "
        "WHERE e.exam_id = %s",
        (exam_id,),
    )


def update_exam_total_marks(exam_id):
    db.execute(
        "UPDATE exams SET total_marks = "
        "(SELECT IFNULL(SUM(marks), 0) FROM questions WHERE exam_id = %s) "
        "WHERE exam_id = %s",
        (exam_id, exam_id),
    )


def read_exam_form():
    subject_id = request.form.get("subject_id", "").strip()
    duration = request.form.get("duration", "").strip()
    return {
        "exam_name": request.form.get("exam_name", "").strip(),
        "subject_id": int(subject_id) if subject_id.isdigit() else 0,
        "duration": int(duration) if duration.isdigit() else 0,
        "exam_date": request.form.get("exam_date", ""),
        "start_time": request.form.get("start_time", ""),
        "end_time": request.form.get("end_time", ""),
        "is_active": 1 if request.form.get("is_active") else 0,
    }


def is_exam_valid(exam):
    filled = all(
        exam[field] for field in ["exam_name", "exam_date", "start_time", "end_time"]
    )
    return (
        filled
        and exam["subject_id"] > 0
        and exam["duration"] > 0
        and exam["start_time"] < exam["end_time"]
    )


def blank_exam():
    return {
        "exam_name": "",
        "subject_id": 0,
        "duration": 60,
        "exam_date": "",
        "start_time": "",
        "end_time": "",
        "is_active": 1,
    }


def read_question_form():
    marks = request.form.get("marks", "").strip()
    return {
        "question_text": request.form.get("question_text", "").strip(),
        "option_a": request.form.get("option_a", "").strip(),
        "option_b": request.form.get("option_b", "").strip(),
        "option_c": request.form.get("option_c", "").strip(),
        "option_d": request.form.get("option_d", "").strip(),
        "correct_answer": request.form.get("correct_answer", ""),
        "marks": int(marks) if marks.isdigit() else 0,
    }


def is_question_valid(question):
    filled = all(
        question[field]
        for field in ["question_text", "option_a", "option_b", "option_c", "option_d"]
    )
    return filled and question["correct_answer"] in ["A", "B", "C", "D"] and question["marks"] > 0


def blank_question():
    return {
        "question_text": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "correct_answer": "",
        "marks": 1,
    }


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    summary = db.fetch_one(
        "SELECT (SELECT COUNT(*) FROM students) AS total_students, "
        "(SELECT COUNT(*) FROM subjects) AS total_subjects, "
        "(SELECT COUNT(*) FROM exams) AS total_exams, "
        "(SELECT COUNT(*) FROM attempts) AS total_attempts"
    )
    return render_template("admin/dashboard.html", summary=summary)


@admin_bp.route("/reports")
@admin_required
def reports():
    exam_statistics = db.fetch_all(
        "SELECT exam_name, subject_name, exam_date, total_marks, total_attempts, "
        "average_percentage, highest_percentage, lowest_percentage "
        "FROM exam_statistics_view ORDER BY exam_date DESC, exam_name"
    )
    top_performers = db.fetch_all(
        "SELECT student_name, COUNT(*) AS exams_attempted, "
        "ROUND(AVG(percentage), 2) AS average_percentage, MAX(percentage) AS best_percentage "
        "FROM student_performance_view GROUP BY student_id, student_name "
        "ORDER BY average_percentage DESC LIMIT 5"
    )
    result_summary = db.fetch_one(
        "SELECT COUNT(*) AS total_results, IFNULL(SUM(result_status = 'Pass'), 0) AS pass_count, "
        "IFNULL(SUM(result_status = 'Fail'), 0) AS fail_count FROM results"
    )
    return render_template(
        "admin/reports.html",
        exam_statistics=exam_statistics,
        subject_report=db.call_procedure("sp_subject_report"),
        top_performers=top_performers,
        result_summary=result_summary,
    )


@admin_bp.route("/subjects")
@admin_required
def subjects():
    return render_template("admin/subjects.html", subjects=get_subject_list())


@admin_bp.route("/subjects/add", methods=["GET", "POST"])
@admin_required
def add_subject():
    subject = {"subject_name": "", "subject_code": ""}

    if request.method == "POST":
        subject["subject_name"] = request.form.get("subject_name", "").strip()
        subject["subject_code"] = request.form.get("subject_code", "").strip()

        if not subject["subject_name"] or not subject["subject_code"]:
            flash("Subject name and subject code are required.", "danger")
        elif subject_code_exists(subject["subject_code"]):
            flash("This subject code is already used by another subject.", "danger")
        else:
            db.execute(
                "INSERT INTO subjects (subject_name, subject_code) VALUES (%s, %s)",
                (subject["subject_name"], subject["subject_code"]),
            )
            flash("Subject added successfully.", "success")
            return redirect(url_for("admin.subjects"))

    return render_template("admin/subject_form.html", subject=subject, form_title="Add Subject")


@admin_bp.route("/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
@admin_required
def edit_subject(subject_id):
    subject = db.fetch_one(
        "SELECT subject_id, subject_name, subject_code FROM subjects WHERE subject_id = %s",
        (subject_id,),
    )
    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for("admin.subjects"))

    if request.method == "POST":
        subject["subject_name"] = request.form.get("subject_name", "").strip()
        subject["subject_code"] = request.form.get("subject_code", "").strip()

        if not subject["subject_name"] or not subject["subject_code"]:
            flash("Subject name and subject code are required.", "danger")
        elif subject_code_exists(subject["subject_code"], subject_id):
            flash("This subject code is already used by another subject.", "danger")
        else:
            db.execute(
                "UPDATE subjects SET subject_name = %s, subject_code = %s WHERE subject_id = %s",
                (subject["subject_name"], subject["subject_code"], subject_id),
            )
            flash("Subject updated successfully.", "success")
            return redirect(url_for("admin.subjects"))

    return render_template("admin/subject_form.html", subject=subject, form_title="Edit Subject")


@admin_bp.route("/subjects/delete/<int:subject_id>", methods=["POST"])
@admin_required
def delete_subject(subject_id):
    linked_exam = db.fetch_one("SELECT exam_id FROM exams WHERE subject_id = %s", (subject_id,))
    if linked_exam:
        flash("This subject has exams linked to it, so it cannot be deleted.", "danger")
        return redirect(url_for("admin.subjects"))

    db.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
    flash("Subject deleted successfully.", "success")
    return redirect(url_for("admin.subjects"))


@admin_bp.route("/exams")
@admin_required
def exams():
    exam_list = db.fetch_all(
        "SELECT e.exam_id, e.exam_name, s.subject_name, e.duration, e.total_marks, e.exam_date, "
        "CAST(e.start_time AS CHAR) AS start_time, CAST(e.end_time AS CHAR) AS end_time, "
        "e.is_active, "
        "(SELECT COUNT(*) FROM questions q WHERE q.exam_id = e.exam_id) AS question_count "
        "FROM exams e JOIN subjects s ON e.subject_id = s.subject_id "
        "ORDER BY e.exam_date DESC, e.start_time"
    )
    return render_template("admin/exams.html", exams=exam_list)


@admin_bp.route("/exams/add", methods=["GET", "POST"])
@admin_required
def add_exam():
    exam = blank_exam()

    if request.method == "POST":
        exam = read_exam_form()
        if not is_exam_valid(exam):
            flash("Please fill the exam details correctly and keep end time after start time.", "danger")
        else:
            db.execute(
                "INSERT INTO exams (exam_name, subject_id, duration, exam_date, start_time, "
                "end_time, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    exam["exam_name"],
                    exam["subject_id"],
                    exam["duration"],
                    exam["exam_date"],
                    exam["start_time"],
                    exam["end_time"],
                    exam["is_active"],
                ),
            )
            flash("Exam created successfully.", "success")
            return redirect(url_for("admin.exams"))

    return render_template(
        "admin/exam_form.html", exam=exam, subjects=get_subject_list(), form_title="Create Exam"
    )


@admin_bp.route("/exams/edit/<int:exam_id>", methods=["GET", "POST"])
@admin_required
def edit_exam(exam_id):
    exam = db.fetch_one(
        "SELECT exam_id, exam_name, subject_id, duration, exam_date, "
        "CAST(start_time AS CHAR) AS start_time, CAST(end_time AS CHAR) AS end_time, is_active "
        "FROM exams WHERE exam_id = %s",
        (exam_id,),
    )
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("admin.exams"))

    if request.method == "POST":
        exam = read_exam_form()
        if not is_exam_valid(exam):
            flash("Please fill the exam details correctly and keep end time after start time.", "danger")
        else:
            db.execute(
                "UPDATE exams SET exam_name = %s, subject_id = %s, duration = %s, exam_date = %s, "
                "start_time = %s, end_time = %s, is_active = %s WHERE exam_id = %s",
                (
                    exam["exam_name"],
                    exam["subject_id"],
                    exam["duration"],
                    exam["exam_date"],
                    exam["start_time"],
                    exam["end_time"],
                    exam["is_active"],
                    exam_id,
                ),
            )
            flash("Exam updated successfully.", "success")
            return redirect(url_for("admin.exams"))

    return render_template(
        "admin/exam_form.html", exam=exam, subjects=get_subject_list(), form_title="Edit Exam"
    )


@admin_bp.route("/exams/delete/<int:exam_id>", methods=["POST"])
@admin_required
def delete_exam(exam_id):
    linked_attempt = db.fetch_one("SELECT attempt_id FROM attempts WHERE exam_id = %s", (exam_id,))
    if linked_attempt:
        flash("Students have already attempted this exam, so it cannot be deleted.", "danger")
        return redirect(url_for("admin.exams"))

    db.execute("DELETE FROM exams WHERE exam_id = %s", (exam_id,))
    flash("Exam deleted successfully.", "success")
    return redirect(url_for("admin.exams"))


@admin_bp.route("/exams/<int:exam_id>/questions")
@admin_required
def exam_questions(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("admin.exams"))

    questions = db.fetch_all(
        "SELECT question_id, question_text, option_a, option_b, option_c, option_d, "
        "correct_answer, marks FROM questions WHERE exam_id = %s ORDER BY question_id",
        (exam_id,),
    )
    return render_template("admin/exam_questions.html", exam=exam, questions=questions)


@admin_bp.route("/exams/<int:exam_id>/questions/add", methods=["GET", "POST"])
@admin_required
def add_question(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("admin.exams"))

    question = blank_question()

    if request.method == "POST":
        question = read_question_form()
        if not is_question_valid(question):
            flash("Please fill every question field and choose a valid correct answer.", "danger")
        else:
            db.execute(
                "INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, "
                "option_d, correct_answer, marks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    exam_id,
                    question["question_text"],
                    question["option_a"],
                    question["option_b"],
                    question["option_c"],
                    question["option_d"],
                    question["correct_answer"],
                    question["marks"],
                ),
            )
            update_exam_total_marks(exam_id)
            flash("Question added successfully.", "success")
            return redirect(url_for("admin.exam_questions", exam_id=exam_id))

    return render_template(
        "admin/question_form.html", exam=exam, question=question, form_title="Add Question"
    )


@admin_bp.route("/questions/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    question = db.fetch_one(
        "SELECT question_id, exam_id, question_text, option_a, option_b, option_c, option_d, "
        "correct_answer, marks FROM questions WHERE question_id = %s",
        (question_id,),
    )
    if not question:
        flash("Question not found.", "danger")
        return redirect(url_for("admin.exams"))

    exam = get_exam(question["exam_id"])

    if request.method == "POST":
        question = read_question_form()
        if not is_question_valid(question):
            flash("Please fill every question field and choose a valid correct answer.", "danger")
        else:
            db.execute(
                "UPDATE questions SET question_text = %s, option_a = %s, option_b = %s, "
                "option_c = %s, option_d = %s, correct_answer = %s, marks = %s "
                "WHERE question_id = %s",
                (
                    question["question_text"],
                    question["option_a"],
                    question["option_b"],
                    question["option_c"],
                    question["option_d"],
                    question["correct_answer"],
                    question["marks"],
                    question_id,
                ),
            )
            update_exam_total_marks(exam["exam_id"])
            flash("Question updated successfully.", "success")
            return redirect(url_for("admin.exam_questions", exam_id=exam["exam_id"]))

    return render_template(
        "admin/question_form.html", exam=exam, question=question, form_title="Edit Question"
    )


@admin_bp.route("/questions/delete/<int:question_id>", methods=["POST"])
@admin_required
def delete_question(question_id):
    question = db.fetch_one(
        "SELECT exam_id FROM questions WHERE question_id = %s", (question_id,)
    )
    if not question:
        flash("Question not found.", "danger")
        return redirect(url_for("admin.exams"))

    linked_answer = db.fetch_one(
        "SELECT answer_id FROM attempt_answers WHERE question_id = %s", (question_id,)
    )
    if linked_answer:
        flash("This question is part of a submitted exam, so it cannot be deleted.", "danger")
        return redirect(url_for("admin.exam_questions", exam_id=question["exam_id"]))

    db.execute("DELETE FROM questions WHERE question_id = %s", (question_id,))
    update_exam_total_marks(question["exam_id"])
    flash("Question deleted successfully.", "success")
    return redirect(url_for("admin.exam_questions", exam_id=question["exam_id"]))
