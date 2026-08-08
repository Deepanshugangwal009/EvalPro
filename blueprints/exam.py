from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import db
from blueprints.student import get_student_exam
from helpers.decorators import login_required
from helpers.evaluation import calculate_obtained_marks, calculate_percentage, decide_result_status

exam_bp = Blueprint("exam", __name__, url_prefix="/exam")


def get_available_exam(exam_id):
    exam = get_student_exam(session["user_id"], exam_id)
    if not exam:
        flash("This exam is not available.", "danger")
    elif exam["status"] == "Attempted":
        flash("You have already attempted this exam.", "warning")
    elif exam["status"] != "Available":
        flash("This exam is not open right now.", "warning")
    else:
        return exam
    return None


def get_exam_questions(exam_id):
    return db.fetch_all(
        "SELECT question_id, question_text, option_a, option_b, option_c, option_d, "
        "correct_answer, marks FROM questions WHERE exam_id = %s ORDER BY question_id",
        (exam_id,),
    )


def read_selected_answers(questions):
    selected_answers = {}
    for question in questions:
        selected = request.form.get("question_" + str(question["question_id"]), "")
        if selected not in ["A", "B", "C", "D"]:
            selected = None
        selected_answers[question["question_id"]] = selected
    return selected_answers


@exam_bp.route("/<int:exam_id>/instructions")
@login_required
def instructions(exam_id):
    exam = get_available_exam(exam_id)
    if not exam:
        return redirect(url_for("student.exams"))

    question_summary = db.fetch_one(
        "SELECT COUNT(*) AS question_count FROM questions WHERE exam_id = %s", (exam_id,)
    )
    return render_template(
        "exam/instructions.html", exam=exam, question_count=question_summary["question_count"]
    )


@exam_bp.route("/<int:exam_id>/attempt")
@login_required
def attempt(exam_id):
    exam = get_available_exam(exam_id)
    if not exam:
        return redirect(url_for("student.exams"))

    questions = get_exam_questions(exam_id)
    if not questions:
        flash("This exam does not have any questions yet.", "warning")
        return redirect(url_for("student.exams"))

    return render_template("exam/attempt.html", exam=exam, questions=questions)


@exam_bp.route("/<int:exam_id>/submit", methods=["POST"])
@login_required
def submit(exam_id):
    exam = get_available_exam(exam_id)
    if not exam:
        return redirect(url_for("student.exams"))

    questions = get_exam_questions(exam_id)
    if not questions:
        flash("This exam does not have any questions yet.", "warning")
        return redirect(url_for("student.exams"))

    student_id = session["user_id"]
    selected_answers = read_selected_answers(questions)
    obtained_marks = calculate_obtained_marks(questions, selected_answers)
    total_marks = exam["total_marks"]
    percentage = calculate_percentage(obtained_marks, total_marks)
    result_status = decide_result_status(percentage)

    connection = db.get_connection()
    cursor = connection.cursor()
    try:
        connection.start_transaction()
        cursor.execute(
            "INSERT INTO attempts (student_id, exam_id, score) VALUES (%s, %s, %s)",
            (student_id, exam_id, obtained_marks),
        )
        attempt_id = cursor.lastrowid

        for question in questions:
            cursor.execute(
                "INSERT INTO attempt_answers (attempt_id, question_id, selected_answer) "
                "VALUES (%s, %s, %s)",
                (attempt_id, question["question_id"], selected_answers[question["question_id"]]),
            )

        cursor.execute(
            "INSERT INTO results (student_id, exam_id, total_marks, obtained_marks, percentage, "
            "result_status) VALUES (%s, %s, %s, %s, %s, %s)",
            (student_id, exam_id, total_marks, obtained_marks, percentage, result_status),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        flash("Your exam could not be submitted. Please try again.", "danger")
        return redirect(url_for("student.exams"))
    finally:
        cursor.close()
        connection.close()

    flash("Your exam has been submitted successfully.", "success")
    return redirect(url_for("result.view_result", exam_id=exam_id))
