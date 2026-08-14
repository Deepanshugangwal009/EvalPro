USE oes_db;
   
INSERT IGNORE INTO admins (username, password) VALUES
('adminKD@9987', 'scrypt:32768:8:1$V12QJhJ3vFfWnLOa$00e504c9b89968318dd5b34e823fadf3e2d44255f06d1c4160101625420d766a1e957966be12c305ee81968f88d98f250d1aa1d794664193dceccc80ef8b38e7');

INSERT IGNORE INTO subjects (subject_name, subject_code) VALUES
('Database Management System', 'CS201'),
('Operating System', 'CS202'),
('Computer Networks', 'CS203'),
('Web Technology', 'CS204');
