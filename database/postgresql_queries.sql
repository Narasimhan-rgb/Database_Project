-- ENGAGE V8.1 — PostgreSQL faculty demo queries
-- Run these directly in pgAdmin Query Tool or psql against the ENGAGE PostgreSQL database.
-- The application itself no longer includes a separate DB Query Lab page.

-- 1) Prove that the 12 original PPT ER tables exist.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'engage_user','following','post','likes','saved','reposts',
    'post_hashtag','hashtag','comment_hashtag','comments','comment_likes','reach'
  )
ORDER BY table_name;

-- 2) Display users / student identity data.
SELECT user_id, user_name, handle, email, follower_count, following_count
FROM engage_user
ORDER BY user_id;

-- 3) JOIN: Show which posts Narasimhan liked and the learning topic behind each post.
SELECT l.user_id, u.user_name, p.post_id, p.genre, pls.topic, p.caption, l.liked_at
FROM likes l
JOIN engage_user u ON u.user_id = l.user_id
JOIN post p ON p.post_id = l.post_id
JOIN post_learning_signal pls ON pls.post_id = p.post_id
WHERE l.user_id = 'U007'
ORDER BY l.liked_at DESC;

-- 4) GROUP BY + aggregate: engagement counts per post.
SELECT p.post_id,
       p.genre,
       COUNT(DISTINCT l.user_id) AS likes,
       COUNT(DISTINCT c.comment_id) AS comments,
       COUNT(DISTINCT s.user_id) AS saves,
       COUNT(DISTINCT r.user_id) AS reposts
FROM post p
LEFT JOIN likes l ON l.post_id = p.post_id
LEFT JOIN comments c ON c.post_id = p.post_id
LEFT JOIN saved s ON s.post_id = p.post_id
LEFT JOIN reposts r ON r.post_id = p.post_id
GROUP BY p.post_id, p.genre
ORDER BY likes DESC, comments DESC;

-- 5) VIEW: Weighted learning interests for Narasimhan.
SELECT *
FROM student_topic_scores
WHERE user_id = 'U007'
ORDER BY topic_score DESC;

-- 6) Explainable recommendations for Narasimhan.
SELECT user_name,
       email,
       exam_goal,
       max_monthly_budget,
       provider_name,
       title,
       monthly_cost,
       interest_score,
       affordability_score,
       total_score,
       recommendation_reason,
       recommendation_rank
FROM student_recommendation_explainer
WHERE user_id = 'U007'
ORDER BY recommendation_rank;

-- 7) Compare the second JEE student with a smaller selected budget.
SELECT user_name,
       max_monthly_budget,
       budget_preference,
       provider_name,
       title,
       monthly_cost,
       total_score,
       recommendation_reason,
       recommendation_rank
FROM student_recommendation_explainer
WHERE user_id = 'U008'
ORDER BY recommendation_rank;

-- 8) Nested subquery: Resources within Narasimhan's selected monthly budget.
SELECT resource_id, provider_name, title, monthly_cost, quality_score
FROM learning_resource
WHERE exam_goal = (
    SELECT exam_goal FROM student_profile WHERE user_id = 'U007'
)
AND monthly_cost <= (
    SELECT max_monthly_budget FROM student_profile WHERE user_id = 'U007'
)
ORDER BY quality_score DESC, monthly_cost ASC;

-- 9) Correlated EXISTS: Users who have liked at least one JEE-related post.
SELECT u.user_id, u.user_name, u.email
FROM engage_user u
WHERE EXISTS (
    SELECT 1
    FROM likes l
    JOIN post_learning_signal pls ON pls.post_id = l.post_id
    WHERE l.user_id = u.user_id
      AND pls.exam_goal = 'JEE'
)
ORDER BY u.user_id;

-- 10) Reach + engagement analytics.
SELECT p.post_id,
       p.genre,
       r.impressions,
       r.unique_reach,
       eq.likes,
       eq.comments,
       eq.saves,
       eq.reposts,
       eq.engagement_quality_score
FROM post p
JOIN reach r ON r.post_id = p.post_id
JOIN engagement_quality eq ON eq.post_id = p.post_id
ORDER BY eq.engagement_quality_score DESC;

-- LIVE DEMO IDEA:
-- Like or Save a post in the ENGAGE website, then rerun queries 3, 5 and 6 here.
-- The changed PostgreSQL rows / topic score / recommendation result demonstrate
-- frontend -> Flask -> PostgreSQL -> analytics in real time.
