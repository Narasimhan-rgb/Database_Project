from pathlib import Path
from db import PostgresDB
from sample_data import (
    USERS, POSTS, HASHTAGS, POST_TAGS, FOLLOWS, LIKES, SAVES, REPOSTS,
    COMMENTS, REPLIES, COMMENT_LIKES, REACH, LEARNING_SIGNALS, STUDENT_PROFILES, LEARNING_RESOURCES,
)

EMAILS = {
    "U001": "sricharan@engage.local",
    "U002": "vitconferences@engage.local",
    "U003": "pokecate@engage.local",
    "U004": "ashok@engage.local",
    "U005": "ishh@engage.local",
    "U006": "adiyenram@engage.local",
    "U007": "narasimhan@engage.local",
    "U008": "arun@engage.local",
    "U009": "diya@engage.local",
    "U010": "rahul@engage.local",
}

COMMENT_TAGS = {
    "C001": ["#JEE", "#Physics"],
    "C002": ["#JEE", "#FreeResources"],
    "C004": ["#AffordableLearning", "#Coaching"],
    "C005": ["#MockTest"],
    "C006": ["#Scholarship"],
    "C009": ["#Database"],
}
MESSAGES = [
    ("U007", "U008", "I found a free mock-test resource in ENGAGE. Check your For You page."),
    ("U008", "U007", "Nice. My recommendations are mostly free or low-cost because of the budget I selected."),
    ("U004", "U007", "Mine is showing premium mock analytics and mentorship options."),
    ("U006", "U008", "Also check the scholarship resource before paying for a batch."),
]
STORIES = [
    ("U007", "JEE + coding build day ✨", "/static/assets/study_table.svg"),
    ("U002", "Free mock-test checklist", "/static/assets/library_corner.svg"),
    ("U003", "Chemistry revision", "/static/assets/coffee_notes.svg"),
    ("U004", "Test-series analytics", "/static/assets/analytics_board.svg"),
    ("U006", "Affordable prep options", "/static/assets/friends_campus.svg"),
    ("U008", "Self-study evening", "/static/assets/workspace.svg"),
]


def ensure_schema(db):
    schema = Path(__file__).with_name("postgres_schema.sql").read_text(encoding="utf-8")
    db.executescript(schema)


def main():
    db = PostgresDB()
    db.verify()
    ensure_schema(db)

    with db.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                TRUNCATE TABLE
                    post_view_event, resource_recommendation, post_learning_signal, learning_resource, student_profile,
                    recommendation_feedback, recommendations, user_preferences,
                    query_history, saved_queries, direct_messages, stories,
                    search_history, app_events,
                    comment_hashtag, comment_likes, comments,
                    post_hashtag, hashtag, post_shares, reposts, saved, likes,
                    reach, following, post, engage_user
                RESTART IDENTITY CASCADE
            """)

            for u in USERS:
                cur.execute("""
                    INSERT INTO engage_user
                    (user_id, user_name, full_name, handle, email, bio, city, avatar_color, avatar_url)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    u["user_id"], u["user_name"], u["user_name"], u["handle"],
                    EMAILS.get(u["user_id"]), u.get("bio"), u.get("city"),
                    u.get("avatar_color"), u.get("avatar_url"),
                ))

            for p in POSTS:
                cur.execute("""
                    INSERT INTO post
                    (post_id, user_id, caption, content_type, genre, post_date, language,
                     location, created_at, visual_seed, media_url)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    p["post_id"], p["creator"], p["caption"], p["media_type"], p["genre"],
                    p["post_date"], p["language"], p["location"], p["created_at"],
                    p["visual_seed"], p.get("media_url"),
                ))

            for post_id, (exam_goal, topic, signal_type) in LEARNING_SIGNALS.items():
                cur.execute("""
                    INSERT INTO post_learning_signal(post_id, exam_goal, topic, signal_type)
                    VALUES (%s,%s,%s,%s)
                """, (post_id, exam_goal, topic, signal_type))

            for h in HASHTAGS:
                cur.execute("INSERT INTO hashtag(hashtag_id, hashtag_name, purpose) VALUES (%s,%s,%s)",
                            (h["hashtag_id"], h["hashtag_name"], h["purpose"]))

            tag_ids = {h["hashtag_name"]: h["hashtag_id"] for h in HASHTAGS}
            for post_id, tags in POST_TAGS.items():
                for tag in tags:
                    if tag in tag_ids:
                        cur.execute("INSERT INTO post_hashtag(post_id, hashtag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                                    (post_id, tag_ids[tag]))

            for follower, following in FOLLOWS:
                cur.execute("INSERT INTO following(follower_user_id, following_user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (follower, following))

            for user_id, post_id in LIKES:
                cur.execute("INSERT INTO likes(post_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (post_id, user_id))

            for user_id, post_id in SAVES:
                cur.execute("INSERT INTO saved(post_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (post_id, user_id))

            for user_id, post_id, highlight in REPOSTS:
                cur.execute("""
                    INSERT INTO reposts(post_id, user_id, text_highlight)
                    VALUES (%s,%s,%s) ON CONFLICT (post_id,user_id) DO NOTHING
                """, (post_id, user_id, highlight))

            reply_parent = {child: parent for child, parent in REPLIES}
            for c in COMMENTS:
                cur.execute("""
                    INSERT INTO comments
                    (comment_id, comment_text, sentiment, user_id, post_id, parent_comment_id, towhom, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    c["comment_id"], c["text"], c["sentiment"], c["user"], c["post"],
                    reply_parent.get(c["comment_id"]), reply_parent.get(c["comment_id"]), c["created_at"],
                ))

            for user_id, comment_id in COMMENT_LIKES:
                cur.execute("INSERT INTO comment_likes(user_id, comment_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (user_id, comment_id))

            for comment_id, tags in COMMENT_TAGS.items():
                for tag in tags:
                    if tag in tag_ids:
                        cur.execute("INSERT INTO comment_hashtag(comment_id, hashtag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                                    (comment_id, tag_ids[tag]))

            for post_id, (impressions, unique_reach) in REACH.items():
                cur.execute("""
                    INSERT INTO reach(reach_id, post_id, impressions, unique_reach)
                    VALUES (%s,%s,%s,%s)
                """, ("R" + post_id[1:], post_id, impressions, unique_reach))

            cur.execute("""
                UPDATE engage_user u
                SET follower_count = (SELECT COUNT(*) FROM following f WHERE f.following_user_id = u.user_id),
                    following_count = (SELECT COUNT(*) FROM following f WHERE f.follower_user_id = u.user_id)
            """)

            cur.execute("""
                UPDATE comments c
                SET numberofreplies = x.total,
                    positive_replies = x.positive,
                    negative_replies = x.negative
                FROM (
                    SELECT parent_comment_id,
                           COUNT(*) AS total,
                           COUNT(*) FILTER (WHERE sentiment='Positive') AS positive,
                           COUNT(*) FILTER (WHERE sentiment='Negative') AS negative
                    FROM comments
                    WHERE parent_comment_id IS NOT NULL
                    GROUP BY parent_comment_id
                ) x
                WHERE c.comment_id = x.parent_comment_id
            """)

            for sp in STUDENT_PROFILES:
                cur.execute("""
                    INSERT INTO student_profile
                    (user_id,academic_stage,exam_goal,max_monthly_budget,budget_preference,preferred_mode,language_preference,city)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (sp["user_id"],sp["academic_stage"],sp["exam_goal"],sp["max_monthly_budget"],sp["budget_preference"],sp["preferred_mode"],sp["language_preference"],sp["city"]))

            for lr in LEARNING_RESOURCES:
                cur.execute("""
                    INSERT INTO learning_resource
                    (resource_id,provider_name,title,exam_goal,topic,resource_type,delivery_mode,monthly_cost,quality_score,scholarship_available,verified,description)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (lr["resource_id"],lr["provider_name"],lr["title"],lr["exam_goal"],lr["topic"],lr["resource_type"],lr["delivery_mode"],lr["monthly_cost"],lr["quality_score"],lr["scholarship_available"],lr["verified"],lr["description"]))

            # Persist the current explainable top matches so they can be inspected as rows too.
            cur.execute("""
                INSERT INTO resource_recommendation
                (user_id,resource_id,interest_score,affordability_score,goal_score,total_score,reason)
                SELECT user_id,resource_id,interest_score,affordability_score,goal_score,total_score,recommendation_reason
                FROM student_recommendation_explainer
                ON CONFLICT (user_id,resource_id) DO UPDATE SET
                  interest_score=EXCLUDED.interest_score,
                  affordability_score=EXCLUDED.affordability_score,
                  goal_score=EXCLUDED.goal_score,
                  total_score=EXCLUDED.total_score,
                  reason=EXCLUDED.reason,
                  generated_at=NOW()
            """)

            for sender, receiver, body in MESSAGES:
                cur.execute("INSERT INTO direct_messages(sender_id, receiver_id, body) VALUES (%s,%s,%s)",
                            (sender, receiver, body))

            for user_id, caption, media_url in STORIES:
                cur.execute("INSERT INTO stories(user_id, caption, media_url) VALUES (%s,%s,%s)",
                            (user_id, caption, media_url))

            cur.execute("""
                INSERT INTO user_preferences(viewer_id, preferred_genres, preferred_hashtags, recommendation_mode)
                VALUES ('U007', '["education","guidance","technology"]'::jsonb, '["#JEE","#StudyTips","#Coding"]'::jsonb, 'balanced')
                ON CONFLICT (viewer_id) DO UPDATE SET
                    preferred_genres=EXCLUDED.preferred_genres,
                    preferred_hashtags=EXCLUDED.preferred_hashtags,
                    recommendation_mode=EXCLUDED.recommendation_mode,
                    updated_at=NOW()
            """)

        conn.commit()

    from demo_expansion import insert_extra
    expanded = insert_extra(db)
    print("ENGAGE V11 demo expansion:", expanded)
    print("ENGAGE V10 course-intelligence sample data created successfully.")
    print(f"Users: {len(USERS)} | Posts: {len(POSTS)} | Comments: {len(COMMENTS)}")
    print("Core PPT ER tables: 12 | Education layer: student profiles + resources + explainable matches")
    print("Demo user: U007 / Narasimhan D / narasimhan@engage.local")


if __name__ == "__main__":
    main()
