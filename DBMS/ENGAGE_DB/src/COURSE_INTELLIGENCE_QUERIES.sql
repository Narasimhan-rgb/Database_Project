-- ENGAGE Course Intelligence V9 - Paste into PostgreSQL / pgAdmin Query Tool.
-- Run setup_postgres.py before querying the V9 views.

-- Q1. Count JEE students among all student profiles.
SELECT COUNT(*) AS total_student_profiles,
       COUNT(*) FILTER (WHERE UPPER(TRIM(exam_goal))='JEE') AS jee_students,
       ROUND(100.0*COUNT(*) FILTER (WHERE UPPER(TRIM(exam_goal))='JEE') / NULLIF(COUNT(*),0),2) AS jee_percentage
FROM student_profile;

-- Q2. Count JEE students with monthly declared max budget >= 2000.
SELECT COUNT(*) AS jee_budget_qualified_students
FROM student_profile
WHERE UPPER(TRIM(exam_goal))='JEE' AND max_monthly_budget >= 2000;

-- Q3. Ranked exam goals by weighted engagement.
SELECT exam_goal, likes, shares, comments, saves, reposts, trending_score
FROM course_goal_trending ORDER BY trending_score DESC, exam_goal;

-- Q4. Ranked resource titles with engagement-topic score.
SELECT title, provider_name, exam_goal, topic, monthly_cost, trending_score
FROM course_resource_trending ORDER BY trending_score DESC, title;

-- Q5. Find all affordable JEE resources using student U007's budget.
SELECT lr.title, lr.provider_name, lr.monthly_cost,
       sp.max_monthly_budget AS student_budget, lr.trending_score
FROM student_profile sp
JOIN course_resource_trending lr ON LOWER(TRIM(lr.exam_goal))=LOWER(TRIM(sp.exam_goal))
WHERE sp.user_id='U007'
  AND LOWER(TRIM(lr.exam_goal))='jee'
  AND lr.monthly_cost <= sp.max_monthly_budget
ORDER BY lr.trending_score DESC, lr.quality_score DESC, lr.monthly_cost;

-- Q6. Inspect scores per original post, verifying no double counts.
SELECT post_id, exam_goal, topic, likes, shares, comments, saves, reposts,
       likes + shares*2 + comments*4 + saves*3 + reposts*5 AS verified_score
FROM course_post_engagement
ORDER BY verified_score DESC, post_id;
