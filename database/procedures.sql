USE oes_db;

DROP PROCEDURE IF EXISTS sp_generate_result;

DELIMITER $$

CREATE PROCEDURE sp_generate_result(IN p_attempt_id INT, IN p_pass_percentage INT)
BEGIN
    DECLARE v_student_id INT;
    DECLARE v_exam_id INT;
    DECLARE v_total_marks INT;
    DECLARE v_obtained_marks INT;
    DECLARE v_percentage DECIMAL(5,2);
    DECLARE v_result_status ENUM('Pass','Fail');

    SELECT student_id, exam_id INTO v_student_id, v_exam_id
    FROM attempts
    WHERE attempt_id = p_attempt_id;

    SELECT IFNULL(SUM(marks), 0) INTO v_total_marks
    FROM questions
    WHERE exam_id = v_exam_id;

    SELECT IFNULL(SUM(q.marks), 0) INTO v_obtained_marks
    FROM attempt_answers aa
    JOIN questions q ON aa.question_id = q.question_id
    WHERE aa.attempt_id = p_attempt_id AND aa.selected_answer = q.correct_answer;

    IF v_total_marks > 0 THEN
        SET v_percentage = ROUND((v_obtained_marks * 100) / v_total_marks, 2);
    ELSE
        SET v_percentage = 0;
    END IF;

    IF v_percentage >= p_pass_percentage THEN
        SET v_result_status = 'Pass';
    ELSE
        SET v_result_status = 'Fail';
    END IF;

    UPDATE attempts SET score = v_obtained_marks WHERE attempt_id = p_attempt_id;

    INSERT INTO results (student_id, exam_id, total_marks, obtained_marks, percentage, result_status)
    VALUES (v_student_id, v_exam_id, v_total_marks, v_obtained_marks, v_percentage, v_result_status)
    ON DUPLICATE KEY UPDATE
        total_marks = v_total_marks,
        obtained_marks = v_obtained_marks,
        percentage = v_percentage,
        result_status = v_result_status;
END$$

DELIMITER ;
