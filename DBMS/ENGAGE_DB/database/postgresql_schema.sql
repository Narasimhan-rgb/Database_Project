-- ENGAGE DB V7: PostgreSQL-only schema
-- Core ER model from the project PPT + application support tables.

CREATE TABLE IF NOT EXISTS engage_user (
    user_id VARCHAR(32) PRIMARY KEY,
    user_name VARCHAR(120) NOT NULL,
    full_name VARCHAR(160),
    handle VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(180) UNIQUE,
    follower_count INTEGER NOT NULL DEFAULT 0 CHECK (follower_count >= 0),
    following_count INTEGER NOT NULL DEFAULT 0 CHECK (following_count >= 0),
    bio TEXT,
    city VARCHAR(120),
    avatar_color VARCHAR(32),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post (
    post_id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    caption TEXT NOT NULL,
    content_type VARCHAR(32) NOT NULL DEFAULT 'image',
    genre VARCHAR(64) NOT NULL,
    post_date DATE NOT NULL DEFAULT CURRENT_DATE,
    language VARCHAR(64) DEFAULT 'English',
    location VARCHAR(180),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    visual_seed INTEGER DEFAULT 1,
    media_url TEXT
);

CREATE TABLE IF NOT EXISTS following (
    follower_user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    following_user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    followed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_user_id, following_user_id),
    CHECK (follower_user_id <> following_user_id)
);

CREATE TABLE IF NOT EXISTS likes (
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    liked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS saved (
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS reposts (
    repost_id BIGSERIAL PRIMARY KEY,
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    text_highlight TEXT,
    reposted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS hashtag (
    hashtag_id VARCHAR(32) PRIMARY KEY,
    hashtag_name VARCHAR(120) UNIQUE NOT NULL,
    purpose VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS post_hashtag (
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    hashtag_id VARCHAR(32) NOT NULL REFERENCES hashtag(hashtag_id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, hashtag_id)
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(32) PRIMARY KEY,
    comment_text TEXT NOT NULL,
    sentiment VARCHAR(24) NOT NULL DEFAULT 'Neutral' CHECK (sentiment IN ('Positive','Neutral','Negative')),
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    towhom VARCHAR(32),
    numberofreplies INTEGER NOT NULL DEFAULT 0,
    positive_replies INTEGER NOT NULL DEFAULT 0,
    negative_replies INTEGER NOT NULL DEFAULT 0,
    parent_comment_id VARCHAR(32) REFERENCES comments(comment_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comment_likes (
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    comment_id VARCHAR(32) NOT NULL REFERENCES comments(comment_id) ON DELETE CASCADE,
    liked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, comment_id)
);

CREATE TABLE IF NOT EXISTS comment_hashtag (
    comment_id VARCHAR(32) NOT NULL REFERENCES comments(comment_id) ON DELETE CASCADE,
    hashtag_id VARCHAR(32) NOT NULL REFERENCES hashtag(hashtag_id) ON DELETE CASCADE,
    PRIMARY KEY (comment_id, hashtag_id)
);

CREATE TABLE IF NOT EXISTS reach (
    reach_id VARCHAR(32) PRIMARY KEY,
    post_id VARCHAR(32) UNIQUE NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    impressions INTEGER NOT NULL DEFAULT 0 CHECK (impressions >= 0),
    unique_reach INTEGER NOT NULL DEFAULT 0 CHECK (unique_reach >= 0)
);

-- Application support tables. These are still PostgreSQL, so the full stack uses one DBMS.
CREATE TABLE IF NOT EXISTS recommendations (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    suggestion_type VARCHAR(32) NOT NULL,
    target_key VARCHAR(128) NOT NULL,
    title VARCHAR(220) NOT NULL,
    reason TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(24) NOT NULL DEFAULT 'new',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(viewer_id, suggestion_type, target_key)
);

CREATE TABLE IF NOT EXISTS recommendation_feedback (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    suggestion_type VARCHAR(32) NOT NULL,
    target_key VARCHAR(128) NOT NULL,
    feedback VARCHAR(24) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    viewer_id VARCHAR(32) PRIMARY KEY REFERENCES engage_user(user_id) ON DELETE CASCADE,
    preferred_genres JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_hashtags JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation_mode VARCHAR(24) NOT NULL DEFAULT 'balanced',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS query_history (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) REFERENCES engage_user(user_id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_queries (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    title VARCHAR(160) NOT NULL,
    query_text TEXT NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(viewer_id, title)
);

CREATE TABLE IF NOT EXISTS direct_messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    receiver_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS stories (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    caption VARCHAR(500),
    media_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE TABLE IF NOT EXISTS search_history (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    search_text VARCHAR(300) NOT NULL,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_events (
    id BIGSERIAL PRIMARY KEY,
    viewer_id VARCHAR(32) REFERENCES engage_user(user_id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    target_type VARCHAR(64),
    target_key VARCHAR(128),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_user_time ON post(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_genre_time ON post(genre, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id, liked_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_user ON saved(user_id, saved_at DESC);
CREATE INDEX IF NOT EXISTS idx_reposts_user ON reposts(user_id, reposted_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, created_at);
CREATE INDEX IF NOT EXISTS idx_following_target ON following(following_user_id);
CREATE INDEX IF NOT EXISTS idx_messages_pair ON direct_messages(sender_id, receiver_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_viewer ON app_events(viewer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_history_viewer ON query_history(viewer_id, executed_at DESC);

CREATE OR REPLACE VIEW engagement_quality AS
SELECT
    p.post_id,
    p.genre,
    u.handle AS creator_handle,
    COUNT(DISTINCT l.user_id) AS likes,
    COUNT(DISTINCT c.comment_id) AS comments,
    COUNT(DISTINCT r.user_id) AS reposts,
    COUNT(DISTINCT s.user_id) AS saves,
    COUNT(DISTINCT l.user_id)
      + COUNT(DISTINCT c.comment_id) * 3
      + COUNT(DISTINCT r.user_id) * 5
      + COUNT(DISTINCT s.user_id) * 4 AS engagement_quality_score
FROM post p
JOIN engage_user u ON u.user_id = p.user_id
LEFT JOIN likes l ON l.post_id = p.post_id
LEFT JOIN comments c ON c.post_id = p.post_id
LEFT JOIN reposts r ON r.post_id = p.post_id
LEFT JOIN saved s ON s.post_id = p.post_id
GROUP BY p.post_id, p.genre, u.handle;

CREATE OR REPLACE VIEW user_genre_scores AS
WITH signals AS (
    SELECT l.user_id, p.genre, 1::numeric AS weight FROM likes l JOIN post p ON p.post_id = l.post_id
    UNION ALL
    SELECT s.user_id, p.genre, 4::numeric FROM saved s JOIN post p ON p.post_id = s.post_id
    UNION ALL
    SELECT r.user_id, p.genre, 5::numeric FROM reposts r JOIN post p ON p.post_id = r.post_id
    UNION ALL
    SELECT c.user_id, p.genre, 3::numeric FROM comments c JOIN post p ON p.post_id = c.post_id
), scored AS (
    SELECT user_id, genre, SUM(weight) AS preference_score
    FROM signals
    GROUP BY user_id, genre
)
SELECT * FROM scored;

CREATE OR REPLACE VIEW user_preference_summary AS
WITH ranked AS (
    SELECT
        ugs.*,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY preference_score DESC, genre) AS rn
    FROM user_genre_scores ugs
)
SELECT
    u.user_id,
    u.user_name,
    u.handle,
    u.email,
    r.genre AS preferred_genre,
    COALESCE(r.preference_score, 0) AS preference_score,
    rec.post_id AS recommended_post_id,
    rec.caption AS recommended_caption,
    CASE
      WHEN r.genre IS NULL THEN 'Interact with posts to build a recommendation profile.'
      ELSE 'Recommended from weighted LIKE/SAVE/REPOST/COMMENT activity in ' || r.genre || '.'
    END AS recommendation_reason
FROM engage_user u
LEFT JOIN ranked r ON r.user_id = u.user_id AND r.rn = 1
LEFT JOIN LATERAL (
    SELECT p2.post_id, p2.caption
    FROM post p2
    WHERE r.genre IS NOT NULL
      AND p2.genre = r.genre
      AND p2.user_id <> u.user_id
      AND NOT EXISTS (SELECT 1 FROM likes l2 WHERE l2.user_id = u.user_id AND l2.post_id = p2.post_id)
    ORDER BY p2.created_at DESC
    LIMIT 1
) rec ON TRUE;

CREATE OR REPLACE VIEW creator_summary AS
SELECT
    u.user_id,
    u.user_name,
    u.handle,
    COUNT(DISTINCT p.post_id) AS total_posts,
    COUNT(DISTINCT l.user_id || ':' || l.post_id) AS likes_received,
    COUNT(DISTINCT c.comment_id) AS comments_received,
    COUNT(DISTINCT s.user_id || ':' || s.post_id) AS saves_received,
    COUNT(DISTINCT r.user_id || ':' || r.post_id) AS reposts_received
FROM engage_user u
LEFT JOIN post p ON p.user_id = u.user_id
LEFT JOIN likes l ON l.post_id = p.post_id
LEFT JOIN comments c ON c.post_id = p.post_id
LEFT JOIN saved s ON s.post_id = p.post_id
LEFT JOIN reposts r ON r.post_id = p.post_id
GROUP BY u.user_id, u.user_name, u.handle;

-- ENGAGE V8 education-opportunity layer.
-- These tables sit on top of the original PPT ER model; the 12 core ER tables remain unchanged.
CREATE TABLE IF NOT EXISTS student_profile (
    user_id VARCHAR(32) PRIMARY KEY REFERENCES engage_user(user_id) ON DELETE CASCADE,
    academic_stage VARCHAR(64),
    exam_goal VARCHAR(64) NOT NULL DEFAULT 'JEE',
    max_monthly_budget NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (max_monthly_budget >= 0),
    budget_preference VARCHAR(24) NOT NULL DEFAULT 'balanced' CHECK (budget_preference IN ('affordable','balanced','premium')),
    preferred_mode VARCHAR(24) NOT NULL DEFAULT 'online' CHECK (preferred_mode IN ('online','offline','hybrid')),
    language_preference VARCHAR(64) DEFAULT 'English',
    city VARCHAR(120),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post_learning_signal (
    post_id VARCHAR(32) PRIMARY KEY REFERENCES post(post_id) ON DELETE CASCADE,
    exam_goal VARCHAR(64) NOT NULL DEFAULT 'GENERAL',
    topic VARCHAR(64) NOT NULL,
    signal_type VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_resource (
    resource_id VARCHAR(32) PRIMARY KEY,
    provider_name VARCHAR(160) NOT NULL,
    title VARCHAR(220) NOT NULL,
    exam_goal VARCHAR(64) NOT NULL,
    topic VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    delivery_mode VARCHAR(24) NOT NULL CHECK (delivery_mode IN ('online','offline','hybrid')),
    monthly_cost NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (monthly_cost >= 0),
    quality_score NUMERIC(4,2) NOT NULL DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 10),
    scholarship_available BOOLEAN NOT NULL DEFAULT FALSE,
    verified BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    resource_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resource_recommendation (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    resource_id VARCHAR(32) NOT NULL REFERENCES learning_resource(resource_id) ON DELETE CASCADE,
    interest_score NUMERIC(8,2) NOT NULL DEFAULT 0,
    affordability_score NUMERIC(8,2) NOT NULL DEFAULT 0,
    goal_score NUMERIC(8,2) NOT NULL DEFAULT 0,
    total_score NUMERIC(8,2) NOT NULL DEFAULT 0,
    reason TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_learning_resource_goal_topic ON learning_resource(exam_goal, topic);
CREATE INDEX IF NOT EXISTS idx_resource_recommendation_user_score ON resource_recommendation(user_id, total_score DESC);

CREATE OR REPLACE VIEW student_topic_scores AS
WITH signals AS (
    SELECT l.user_id, pls.topic, 1::numeric AS weight
    FROM likes l JOIN post_learning_signal pls ON pls.post_id=l.post_id
    UNION ALL
    SELECT s.user_id, pls.topic, 4::numeric
    FROM saved s JOIN post_learning_signal pls ON pls.post_id=s.post_id
    UNION ALL
    SELECT r.user_id, pls.topic, 5::numeric
    FROM reposts r JOIN post_learning_signal pls ON pls.post_id=r.post_id
    UNION ALL
    SELECT c.user_id, pls.topic, 3::numeric
    FROM comments c JOIN post_learning_signal pls ON pls.post_id=c.post_id
)
SELECT user_id, topic, SUM(weight) AS topic_score
FROM signals
GROUP BY user_id, topic;

CREATE OR REPLACE VIEW student_resource_matches AS
SELECT
    sp.user_id,
    u.user_name,
    u.email,
    sp.exam_goal,
    sp.max_monthly_budget,
    sp.budget_preference,
    sp.preferred_mode,
    lr.resource_id,
    lr.provider_name,
    lr.title,
    lr.topic,
    lr.resource_type,
    lr.delivery_mode,
    lr.monthly_cost,
    lr.quality_score,
    lr.scholarship_available,
    COALESCE(sts.topic_score, 0) AS raw_topic_score,
    CASE WHEN lr.exam_goal=sp.exam_goal THEN 35 ELSE 5 END AS goal_score,
    LEAST(COALESCE(sts.topic_score,0) * 2, 30) AS interest_score,
    CASE
      WHEN lr.monthly_cost=0 THEN 25
      WHEN lr.monthly_cost <= sp.max_monthly_budget THEN 25
      WHEN lr.scholarship_available AND lr.monthly_cost <= sp.max_monthly_budget * 1.75 THEN 18
      WHEN lr.monthly_cost <= sp.max_monthly_budget * 1.25 THEN 12
      ELSE 0
    END AS affordability_score,
    CASE WHEN lr.delivery_mode=sp.preferred_mode OR lr.delivery_mode='hybrid' THEN 5 ELSE 0 END AS mode_score,
    ROUND((
      CASE WHEN lr.exam_goal=sp.exam_goal THEN 35 ELSE 5 END
      + LEAST(COALESCE(sts.topic_score,0) * 2, 30)
      + CASE
          WHEN lr.monthly_cost=0 THEN 25
          WHEN lr.monthly_cost <= sp.max_monthly_budget THEN 25
          WHEN lr.scholarship_available AND lr.monthly_cost <= sp.max_monthly_budget * 1.75 THEN 18
          WHEN lr.monthly_cost <= sp.max_monthly_budget * 1.25 THEN 12
          ELSE 0
        END
      + CASE WHEN lr.delivery_mode=sp.preferred_mode OR lr.delivery_mode='hybrid' THEN 5 ELSE 0 END
      + (lr.quality_score / 2)
    )::numeric, 2) AS total_score,
    CASE
      WHEN lr.monthly_cost=0 THEN 'Free option aligned with the student''s goal and engagement pattern.'
      WHEN lr.monthly_cost <= sp.max_monthly_budget THEN 'Fits the student-selected monthly budget and matches observed learning interests.'
      WHEN lr.scholarship_available THEN 'Above the selected budget, but scholarship support is available; shown as an alternative.'
      ELSE 'Relevant to the learning goal, but currently above the selected budget.'
    END AS recommendation_reason
FROM student_profile sp
JOIN engage_user u ON u.user_id=sp.user_id
JOIN learning_resource lr ON lr.exam_goal=sp.exam_goal
LEFT JOIN student_topic_scores sts ON sts.user_id=sp.user_id AND sts.topic=lr.topic;

CREATE OR REPLACE VIEW student_recommendation_explainer AS
SELECT * FROM (
    SELECT
      srm.*,
      ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total_score DESC, monthly_cost ASC, quality_score DESC) AS recommendation_rank
    FROM student_resource_matches srm
) ranked
WHERE recommendation_rank <= 5;

CREATE TABLE IF NOT EXISTS post_view_event (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    dwell_seconds NUMERIC(8,2) NOT NULL DEFAULT 0 CHECK (dwell_seconds >= 0),
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_post_view_event_user_time ON post_view_event(user_id, viewed_at DESC);

CREATE OR REPLACE VIEW student_topic_scores AS
WITH signals AS (
    SELECT l.user_id, pls.topic, 1::numeric AS weight
    FROM likes l JOIN post_learning_signal pls ON pls.post_id=l.post_id
    UNION ALL
    SELECT s.user_id, pls.topic, 4::numeric
    FROM saved s JOIN post_learning_signal pls ON pls.post_id=s.post_id
    UNION ALL
    SELECT r.user_id, pls.topic, 5::numeric
    FROM reposts r JOIN post_learning_signal pls ON pls.post_id=r.post_id
    UNION ALL
    SELECT c.user_id, pls.topic, 3::numeric
    FROM comments c JOIN post_learning_signal pls ON pls.post_id=c.post_id
    UNION ALL
    SELECT v.user_id, pls.topic,
           LEAST(1.5::numeric, 0.20::numeric + LEAST(v.dwell_seconds,20)::numeric / 20::numeric)
    FROM post_view_event v JOIN post_learning_signal pls ON pls.post_id=v.post_id
)
SELECT user_id, topic, ROUND(SUM(weight),2) AS topic_score
FROM signals
GROUP BY user_id, topic;


-- ENGAGE Course Intelligence: shares are independent of reposts, so their
-- engagement weights are counted exactly once. Safe on existing databases.
CREATE TABLE IF NOT EXISTS post_shares (
    post_id VARCHAR(32) NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    user_id VARCHAR(32) NOT NULL REFERENCES engage_user(user_id) ON DELETE CASCADE,
    shared_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_post_shares_user ON post_shares(user_id, shared_at DESC);

-- Aggregate each activity type independently to prevent JOIN multiplication.
CREATE OR REPLACE VIEW course_post_engagement AS
SELECT pls.post_id, pls.exam_goal, pls.topic,
       COALESCE(l.n,0)::bigint AS likes,
       COALESCE(sh.n,0)::bigint AS shares,
       COALESCE(c.n,0)::bigint AS comments,
       COALESCE(sa.n,0)::bigint AS saves,
       COALESCE(r.n,0)::bigint AS reposts,
       (COALESCE(l.n,0) + COALESCE(sh.n,0)*2 + COALESCE(c.n,0)*4
         + COALESCE(sa.n,0)*3 + COALESCE(r.n,0)*5)::bigint AS trending_score
FROM post_learning_signal pls
LEFT JOIN (SELECT post_id,COUNT(*) AS n FROM likes GROUP BY post_id) l USING (post_id)
LEFT JOIN (SELECT post_id,COUNT(*) AS n FROM post_shares GROUP BY post_id) sh USING (post_id)
LEFT JOIN (SELECT post_id,COUNT(*) AS n FROM comments GROUP BY post_id) c USING (post_id)
LEFT JOIN (SELECT post_id,COUNT(*) AS n FROM saved GROUP BY post_id) sa USING (post_id)
LEFT JOIN (SELECT post_id,COUNT(*) AS n FROM reposts GROUP BY post_id) r USING (post_id);

-- All configured student goals and resources appear, including those with zero posts.
CREATE OR REPLACE VIEW course_goal_trending AS
WITH goals AS (
    SELECT LOWER(TRIM(exam_goal)) AS goal_key, MIN(TRIM(exam_goal)) AS exam_goal
    FROM (SELECT exam_goal FROM student_profile UNION ALL
          SELECT exam_goal FROM learning_resource) g
    WHERE TRIM(exam_goal) <> '' GROUP BY LOWER(TRIM(exam_goal))
), scores AS (
    SELECT LOWER(TRIM(exam_goal)) AS goal_key,
           COUNT(*)::bigint AS post_count,
           SUM(likes)::bigint AS likes, SUM(shares)::bigint AS shares,
           SUM(comments)::bigint AS comments, SUM(saves)::bigint AS saves,
           SUM(reposts)::bigint AS reposts, SUM(trending_score)::bigint AS trending_score
    FROM course_post_engagement GROUP BY LOWER(TRIM(exam_goal))
)
SELECT g.exam_goal, COALESCE(s.post_count,0)::bigint AS post_count,
       COALESCE(s.likes,0)::bigint AS likes, COALESCE(s.shares,0)::bigint AS shares,
       COALESCE(s.comments,0)::bigint AS comments, COALESCE(s.saves,0)::bigint AS saves,
       COALESCE(s.reposts,0)::bigint AS reposts,
       COALESCE(s.trending_score,0)::bigint AS trending_score
FROM goals g LEFT JOIN scores s USING (goal_key);

-- Resources are mapped to posts by GOAL + TOPIC, never claimed as individual
-- provider reactions unless that relationship is specifically recorded.
CREATE OR REPLACE VIEW course_resource_trending AS
WITH topic_scores AS (
    SELECT LOWER(TRIM(exam_goal)) AS goal_key, LOWER(TRIM(topic)) AS topic_key,
           SUM(likes)::bigint AS likes, SUM(shares)::bigint AS shares,
           SUM(comments)::bigint AS comments, SUM(saves)::bigint AS saves,
           SUM(reposts)::bigint AS reposts, SUM(trending_score)::bigint AS trending_score
    FROM course_post_engagement GROUP BY LOWER(TRIM(exam_goal)),LOWER(TRIM(topic))
)
SELECT lr.resource_id, lr.provider_name, lr.title, lr.exam_goal, lr.topic,
       lr.resource_type, lr.delivery_mode, lr.monthly_cost, lr.quality_score,
       lr.scholarship_available, lr.description, lr.resource_url,
       COALESCE(ts.likes,0)::bigint AS likes, COALESCE(ts.shares,0)::bigint AS shares,
       COALESCE(ts.comments,0)::bigint AS comments, COALESCE(ts.saves,0)::bigint AS saves,
       COALESCE(ts.reposts,0)::bigint AS reposts,
       COALESCE(ts.trending_score,0)::bigint AS trending_score
FROM learning_resource lr
LEFT JOIN topic_scores ts ON ts.goal_key=LOWER(TRIM(lr.exam_goal))
                          AND ts.topic_key=LOWER(TRIM(lr.topic));
