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
    return render_template("admin/dashboard.html")


@admin_bp.route("/subjects")
@admin_required
def subjects():
    subject_list = db.fetch_all(
        "SELECT subject_id, subject_name, subject_code FROM subjects ORDER BY subject_name"
    )
    return render_template("admin/subjects.html", subjects=subject_list)


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


@admin_bp.route("/exams/<int:exam_id>/questions")
@admin_required
def exam_questions(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    questions = db.fetch_all(
        "SELECT question_id, question_text, option_a, option_b, option_c, option_d, "
        "correct_answer, marks FROM questions WHERE exam_id = %s ORDER BY question_id",
        (exam_id,),
    )
    return render_template("admin/questions.html", exam=exam, questions=questions)


@admin_bp.route("/exams/<int:exam_id>/questions/add", methods=["GET", "POST"])
@admin_required
def add_question(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("admin.dashboard"))

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
        return redirect(url_for("admin.dashboard"))

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
        return redirect(url_for("admin.dashboard"))

    db.execute("DELETE FROM questions WHERE question_id = %s", (question_id,))
    update_exam_total_marks(question["exam_id"])
    flash("Question deleted successfully.", "success")
    return redirect(url_for("admin.exam_questions", exam_id=question["exam_id"]))
