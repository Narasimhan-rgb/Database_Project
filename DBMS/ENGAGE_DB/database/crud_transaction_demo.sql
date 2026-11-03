-- Oracle SQL*Plus example: INSERT / SELECT / UPDATE / DELETE with ROLLBACK.
-- Do not run inside the live PostgreSQL application's SQL console.
SAVEPOINT engage_demo_start;
INSERT INTO engage_user (user_id,user_name,handle,city) VALUES ('U_DEMO_2026','Demo Student','demo_student_2026','Chennai');
SELECT user_id,user_name,city FROM engage_user WHERE user_id='U_DEMO_2026';
UPDATE engage_user SET city='Vellore' WHERE user_id='U_DEMO_2026';
SELECT user_id,user_name,city FROM engage_user WHERE user_id='U_DEMO_2026';
DELETE FROM engage_user WHERE user_id='U_DEMO_2026';
SELECT COUNT(*) AS after_delete FROM engage_user WHERE user_id='U_DEMO_2026';
ROLLBACK TO SAVEPOINT engage_demo_start;
