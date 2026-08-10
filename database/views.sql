USE oes_db;

CREATE OR REPLACE VIEW student_performance_view AS
SELECT r.student_id,
       st.name AS student_name,
       r.exam_id,
       e.exam_name,
       s.subject_name,
       e.exam_date,
       r.total_marks,
       r.obtained_marks,
       r.percentage,
       r.result_status
FROM results r
JOIN students st ON r.student_id = st.student_id
JOIN exams e ON r.exam_id = e.exam_id
JOIN subjects s ON e.subject_id = s.subject_id;

CREATE OR REPLACE VIEW exam_statistics_view AS
SELECT e.exam_id,
       e.exam_name,
       s.subject_name,
       e.exam_date,
       e.total_marks,
       COUNT(r.result_id) AS total_attempts,
       IFNULL(ROUND(AVG(r.percentage), 2), 0) AS average_percentage,
       IFNULL(MAX(r.percentage), 0) AS highest_percentage,
       IFNULL(MIN(r.percentage), 0) AS lowest_percentage
FROM exams e
JOIN subjects s ON e.subject_id = s.subject_id
LEFT JOIN results r ON r.exam_id = e.exam_id
GROUP BY e.exam_id, e.exam_name, s.subject_name, e.exam_date, e.total_marks;
