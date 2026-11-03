-- ENGAGE DB | Oracle SQL*Plus | 4 common + 9 individually assigned queries.
-- Connect using: sqlplus BCE5028@localhost/FREEPDB1
-- The original source uses string IDs: U007 and P003, NOT numeric 101/201.
SET LINESIZE 180;
SET PAGESIZE 80;
SET SERVEROUTPUT ON;

PROMPT === COMMON 1: Users in Chennai ===
SELECT user_id,user_name,full_name,handle,email,city FROM engage_user WHERE LOWER(city)=LOWER('Chennai');

PROMPT === COMMON 2: Posts by Narasimhan (U007) ===
SELECT post_id,caption,content_type,genre,post_date FROM post WHERE user_id='U007' ORDER BY post_date DESC;

PROMPT === COMMON 8: Most-used hashtags ===
SELECT h.hashtag_id,h.hashtag_name,COUNT(ph.post_id) AS usage_count FROM hashtag h LEFT JOIN post_hashtag ph ON h.hashtag_id=ph.hashtag_id GROUP BY h.hashtag_id,h.hashtag_name ORDER BY usage_count DESC;

PROMPT === COMMON 11: Likes by genre as a percentage ===
SELECT p.genre, COUNT(*) AS likes_in_genre, ROUND(100*COUNT(*)/NULLIF((SELECT COUNT(*) FROM likes WHERE user_id='U007'),0),2) AS like_percentage FROM likes l JOIN post p ON l.post_id=p.post_id WHERE l.user_id='U007' GROUP BY p.genre ORDER BY like_percentage DESC;

PROMPT === SKANDHAN 3: Total likes per post ===
SELECT p.post_id,p.caption,COUNT(l.user_id) AS total_likes FROM post p LEFT JOIN likes l ON p.post_id=l.post_id GROUP BY p.post_id,p.caption ORDER BY total_likes DESC;

PROMPT === SKANDHAN 6: Posts saved by Narasimhan ===
SELECT p.post_id,p.caption,p.genre,s.saved_at FROM saved s JOIN post p ON s.post_id=p.post_id WHERE s.user_id='U007' ORDER BY s.saved_at DESC;

PROMPT === SKANDHAN 17: Like count of an existing post ===
SELECT post_id,COUNT(user_id) AS total_likes FROM likes WHERE post_id=(SELECT MIN(post_id) FROM likes) GROUP BY post_id;

PROMPT === SHRI VISHWA 4: Total saves per post ===
SELECT p.post_id,p.caption,COUNT(s.user_id) AS total_saves FROM post p LEFT JOIN saved s ON p.post_id=s.post_id GROUP BY p.post_id,p.caption ORDER BY total_saves DESC;

PROMPT === SHRI VISHWA 7: Posts liked by Narasimhan ===
SELECT p.post_id,p.caption,p.genre,p.content_type,l.liked_at FROM likes l JOIN post p ON l.post_id=p.post_id WHERE l.user_id='U007' ORDER BY l.liked_at DESC;

PROMPT === SHRI VISHWA 18: Comments on one existing post ===
SELECT post_id,COUNT(comment_id) AS total_comments FROM comments WHERE post_id=(SELECT MIN(post_id) FROM comments) GROUP BY post_id;

PROMPT === NARASIMHAN 5: Comment counts for all posts ===
SELECT p.post_id,p.caption,COUNT(c.comment_id) AS total_comments FROM post p LEFT JOIN comments c ON p.post_id=c.post_id GROUP BY p.post_id,p.caption ORDER BY total_comments DESC;

PROMPT === NARASIMHAN X: Posts commented by Narasimhan ===
SELECT p.post_id,p.caption,p.genre,c.comment_text,c.sentiment,c.created_at FROM comments c JOIN post p ON c.post_id=p.post_id WHERE c.user_id='U007' ORDER BY c.created_at DESC;

PROMPT === NARASIMHAN 19: Saves on an existing post ===
SELECT post_id,COUNT(user_id) AS total_saves FROM saved WHERE post_id=(SELECT MIN(post_id) FROM saved) GROUP BY post_id;

PROMPT === ADVANCED: Above-average post likes (nested aggregate) ===
WITH counts AS (SELECT p.post_id,p.genre,COUNT(l.user_id) AS like_count FROM post p LEFT JOIN likes l ON l.post_id=p.post_id GROUP BY p.post_id,p.genre) SELECT * FROM counts WHERE like_count>(SELECT AVG(like_count) FROM counts) ORDER BY like_count DESC;

PROMPT === ADVANCED: Correlated subquery to count posts per user ===
SELECT u.user_id,u.user_name,(SELECT COUNT(*) FROM post p WHERE p.user_id=u.user_id) AS post_count FROM engage_user u ORDER BY post_count DESC;

PROMPT === ADVANCED: Followers per user ===
SELECT u.user_id,u.user_name,COUNT(f.follower_user_id) AS followers FROM engage_user u LEFT JOIN following f ON f.following_user_id=u.user_id GROUP BY u.user_id,u.user_name ORDER BY followers DESC;

PROMPT === ADVANCED: Student affordability JOIN ===
SELECT u.user_name,lr.provider_name,lr.title,lr.monthly_cost FROM engage_user u JOIN student_profile sp ON sp.user_id=u.user_id JOIN learning_resource lr ON lr.exam_goal=sp.exam_goal AND lr.monthly_cost<=sp.max_monthly_budget WHERE u.user_id='U007' ORDER BY lr.monthly_cost;

PROMPT === TRANSACTION DEMO: UPDATE then ROLLBACK ===
SAVEPOINT before_demo;
UPDATE engage_user SET bio='Temporary demo change' WHERE user_id='U007';
SELECT user_id,bio FROM engage_user WHERE user_id='U007';
ROLLBACK TO before_demo;
SELECT user_id,bio FROM engage_user WHERE user_id='U007';

PROMPT === TRANSACTION DEMO: INSERT then ROLLBACK ===
SAVEPOINT before_insert_demo;
INSERT INTO hashtag(hashtag_id,hashtag_name,purpose) VALUES ('H_DEMO','#FacultyDemo','demonstration');
SELECT hashtag_id,hashtag_name FROM hashtag WHERE hashtag_id='H_DEMO';
ROLLBACK TO before_insert_demo;

PROMPT === TRANSACTION DEMO: DELETE then ROLLBACK ===
SAVEPOINT before_delete_demo;
DELETE FROM comment_likes WHERE user_id='U002' AND comment_id='C001';
SELECT COUNT(*) AS remaining_demo_pairs FROM comment_likes WHERE user_id='U002' AND comment_id='C001';
ROLLBACK TO before_delete_demo;

PROMPT === VIEW DEMO: Create or replace an analysis view ===
CREATE OR REPLACE VIEW v_engage_post_likes AS SELECT p.post_id,p.genre,COUNT(l.user_id) AS like_count FROM post p LEFT JOIN likes l ON l.post_id=p.post_id GROUP BY p.post_id,p.genre;
SELECT * FROM v_engage_post_likes ORDER BY like_count DESC;

PROMPT === INDEX DEMO: Create if not already created; Oracle index creation has implicit commit ===
-- Check first: SELECT index_name,table_name FROM user_indexes WHERE table_name='COMMENTS';
-- Optional for faculty demonstration on a fresh account:
-- CREATE INDEX idx_engage_comments_post_demo ON comments(post_id);
-- DROP INDEX idx_engage_comments_post_demo;
