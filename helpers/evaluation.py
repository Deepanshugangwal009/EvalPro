from config import Config


def calculate_obtained_marks(questions, selected_answers):
    obtained_marks = 0
    for question in questions:
        if selected_answers.get(question["question_id"]) == question["correct_answer"]:
            obtained_marks += question["marks"]
    return obtained_marks


def calculate_percentage(obtained_marks, total_marks):
    if total_marks <= 0:
        return 0.0
    return round(obtained_marks * 100 / total_marks, 2)


def decide_result_status(percentage):
    if percentage >= Config.PASS_PERCENTAGE:
        return "Pass"
    return "Fail"
