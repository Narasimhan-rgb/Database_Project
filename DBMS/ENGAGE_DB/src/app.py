import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from db import PostgresDB, json_rows
from oracle_db import OracleDB, oracle_value
from course_intelligence import course_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(course_bp)
db = PostgresDB()
oracle_db = OracleDB()
UPLOAD_DIR = Path(app.root_path) / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_UPLOADS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)


def fail(message, code=500):
    return jsonify({"ok": False, "error": str(message)}), code


def sentiment_for(text):
    t = (text or "").lower()
    positive = ["good", "great", "nice", "love", "excellent", "amazing", "useful", "clear", "cool", "best", "helpful"]
    negative = ["bad", "hate", "difficult", "confusing", "worst", "painful", "problem", "fail", "wrong"]
    if any(w in t for w in positive):
        return "Positive"
    if any(w in t for w in negative):
        return "Negative"
    return "Neutral"


def log_event_safe(viewer_id, event_type, target_type=None, target_key=None, metadata=None):
    try:
        db.execute(
            """INSERT INTO app_events(viewer_id,event_type,target_type,target_key,metadata)
               VALUES (%s,%s,%s,%s,%s::jsonb)""",
            (viewer_id, event_type, target_type, target_key, json.dumps(metadata or {})),
        )
    except Exception:
        pass


def log_query_safe(viewer_id, query_text, success, row_count=0, error_message=None):
    try:
        db.execute(
            """INSERT INTO query_history(viewer_id,query_text,success,row_count,error_message)
               VALUES (%s,%s,%s,%s,%s)""",
            (viewer_id, query_text, bool(success), int(row_count), error_message),
        )
    except Exception:
        pass


FEED_SQL = """
SELECT
    p.post_id,
    p.caption,
    p.content_type AS media_type,
    p.genre,
    p.language,
    p.location,
    p.post_date,
    p.created_at,
    p.visual_seed,
    p.media_url,
    u.user_id AS creator_id,
    u.user_name AS creator_name,
    u.handle AS creator_handle,
    u.avatar_color AS creator_color,
    (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.post_id) AS likes,
    (SELECT COUNT(*) FROM saved s WHERE s.post_id=p.post_id) AS saves,
    (SELECT COUNT(*) FROM reposts r WHERE r.post_id=p.post_id) AS reposts,
    (SELECT COUNT(*) FROM post_shares sh WHERE sh.post_id=p.post_id) AS shares,
    (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.post_id) AS comments,
    COALESCE((SELECT array_agg(h.hashtag_name ORDER BY h.hashtag_name)
              FROM post_hashtag ph JOIN hashtag h ON h.hashtag_id=ph.hashtag_id
              WHERE ph.post_id=p.post_id), ARRAY[]::varchar[]) AS hashtags,
    COALESCE(rr.impressions,0) AS impressions,
    COALESCE(rr.unique_reach,0) AS unique_reach,
    EXISTS(SELECT 1 FROM likes vl WHERE vl.user_id=%s AND vl.post_id=p.post_id) AS viewer_liked,
    EXISTS(SELECT 1 FROM saved vs WHERE vs.user_id=%s AND vs.post_id=p.post_id) AS viewer_saved,
    EXISTS(SELECT 1 FROM reposts vr WHERE vr.user_id=%s AND vr.post_id=p.post_id) AS viewer_reposted
FROM post p
JOIN engage_user u ON u.user_id=p.user_id
LEFT JOIN reach rr ON rr.post_id=p.post_id
WHERE (%s::varchar IS NULL OR p.user_id=%s)
ORDER BY p.created_at DESC
"""


def feed_rows(viewer_id, profile_user_id=None):
    return json_rows(db.query(FEED_SQL, (viewer_id, viewer_id, viewer_id, profile_user_id, profile_user_id)))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    try:
        row = db.verify()
        postgres = {
            "connected": True,
            "database": row["database"],
            "db_user": row["db_user"],
            "host": db.host,
            "port": db.port,
            "error": None,
        }
        return ok(status="connected", postgres=postgres, engine="PostgreSQL")
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": "PostgreSQL connection failed: " + str(exc),
            "postgres": {"connected": False, "error": str(exc)},
        }), 503


@app.get("/api/bootstrap")
def bootstrap():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        rows = json_rows(db.query("""
            SELECT u.user_id,u.user_name,u.full_name,u.handle,u.email,u.bio,u.city,
                   u.avatar_color,u.avatar_url,
                   u.follower_count AS followers,u.following_count AS following,
                   EXISTS(SELECT 1 FROM following f
                          WHERE f.follower_user_id=%s AND f.following_user_id=u.user_id) AS viewer_follows
            FROM engage_user u
            ORDER BY u.follower_count DESC,u.user_name
        """, (viewer_id,)))
        current = next((u for u in rows if u["user_id"] == viewer_id), None)
        stats = json_rows(db.query("""
            SELECT
              (SELECT COUNT(*) FROM engage_user) AS users,
              (SELECT COUNT(*) FROM post) AS posts,
              (SELECT COUNT(*) FROM likes) AS likes,
              (SELECT COUNT(*) FROM comments) AS comments
        """))[0]
        return ok({"users": rows, "current_user": current, "stats": stats})
    except Exception as exc:
        return fail(exc)


@app.get("/api/feed")
def feed():
    viewer_id = request.args.get("viewer_id", "U007")
    profile_user_id = request.args.get("profile_user_id")
    try:
        return ok(feed_rows(viewer_id, profile_user_id))
    except Exception as exc:
        return fail(exc)


@app.post("/api/post/<post_id>/view")
def record_post_view(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        dwell = max(0.0, min(float(body.get("dwell_seconds", 2) or 0), 120.0))
        completed = bool(body.get("completed", False))
        db.execute("""
            INSERT INTO post_view_event(user_id,post_id,dwell_seconds,completed)
            VALUES (%s,%s,%s,%s)
        """, (viewer_id, post_id, dwell, completed))
        return ok({"recorded": True})
    except Exception as exc:
        return fail(exc, 400)


@app.get("/api/explore")
def explore():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        rows = feed_rows(viewer_id)
        rows.sort(key=lambda x: (x["likes"] + x["saves"] * 2 + x["reposts"] * 3 + x["comments"] * 2, str(x["created_at"])), reverse=True)
        return ok(rows)
    except Exception as exc:
        return fail(exc)


@app.get("/api/profile/<user_id>")
def profile(user_id):
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        rows = json_rows(db.query("""
            SELECT u.user_id,u.user_name,u.full_name,u.handle,u.email,u.bio,u.city,u.avatar_color,u.avatar_url,
                   u.follower_count AS followers,u.following_count AS following,
                   (SELECT COUNT(*) FROM post p WHERE p.user_id=u.user_id) AS posts,
                   EXISTS(SELECT 1 FROM following f WHERE f.follower_user_id=%s AND f.following_user_id=u.user_id) AS viewer_follows
            FROM engage_user u WHERE u.user_id=%s
        """, (viewer_id, user_id)))
        if not rows:
            return fail("User not found", 404)
        return ok(rows[0])
    except Exception as exc:
        return fail(exc)


@app.get("/api/comments/<post_id>")
def comments(post_id):
    try:
        rows = db.query("""
            SELECT c.comment_id,c.comment_text,c.sentiment,c.created_at,
                   u.user_id,u.user_name,u.handle,u.avatar_color,
                   c.parent_comment_id,
                   (SELECT COUNT(*) FROM comment_likes cl WHERE cl.comment_id=c.comment_id) AS likes
            FROM comments c JOIN engage_user u ON u.user_id=c.user_id
            WHERE c.post_id=%s
            ORDER BY c.created_at
        """, (post_id,))
        return ok(json_rows(rows))
    except Exception as exc:
        return fail(exc)


@app.get("/api/notifications")
def notifications():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        items = []
        items += json_rows(db.query("""
            SELECT a.user_id AS actor_id,a.user_name AS actor_name,a.handle AS actor_handle,a.avatar_color AS actor_color,
                   'follow' AS type,'started following you' AS text,f.followed_at AS happened_at
            FROM following f JOIN engage_user a ON a.user_id=f.follower_user_id
            WHERE f.following_user_id=%s AND a.user_id<>%s
            ORDER BY f.followed_at DESC LIMIT 8
        """, (viewer_id, viewer_id)))
        items += json_rows(db.query("""
            SELECT a.user_id AS actor_id,a.user_name AS actor_name,a.handle AS actor_handle,a.avatar_color AS actor_color,
                   p.post_id,p.caption AS post_caption,'like' AS type,'liked your post' AS text,l.liked_at AS happened_at
            FROM likes l
            JOIN engage_user a ON a.user_id=l.user_id
            JOIN post p ON p.post_id=l.post_id
            WHERE p.user_id=%s AND a.user_id<>%s
            ORDER BY l.liked_at DESC LIMIT 10
        """, (viewer_id, viewer_id)))
        items += json_rows(db.query("""
            SELECT a.user_id AS actor_id,a.user_name AS actor_name,a.handle AS actor_handle,a.avatar_color AS actor_color,
                   p.post_id,c.comment_text,'comment' AS type,'commented on your post' AS text,c.created_at AS happened_at
            FROM comments c
            JOIN engage_user a ON a.user_id=c.user_id
            JOIN post p ON p.post_id=c.post_id
            WHERE p.user_id=%s AND a.user_id<>%s
            ORDER BY c.created_at DESC LIMIT 10
        """, (viewer_id, viewer_id)))
        items.sort(key=lambda x: str(x.get("happened_at", "")), reverse=True)
        return ok(items[:20])
    except Exception as exc:
        return fail(exc)


@app.get("/api/search")
def search():
    q = (request.args.get("q") or "").strip()
    viewer_id = request.args.get("viewer_id", "U007")
    if not q:
        return ok({"users": [], "hashtags": [], "posts": []})
    try:
        db.execute("INSERT INTO search_history(viewer_id,search_text) VALUES (%s,%s)", (viewer_id, q))
    except Exception:
        pass
    like_q = f"%{q}%"
    try:
        users = json_rows(db.query("""
            SELECT user_id,user_name,handle,avatar_color FROM engage_user
            WHERE user_name ILIKE %s OR handle ILIKE %s OR email ILIKE %s
            ORDER BY follower_count DESC LIMIT 8
        """, (like_q, like_q, like_q)))
        hashtags = json_rows(db.query("""
            SELECT h.hashtag_name AS hashtag,h.purpose,COUNT(ph.post_id) AS posts
            FROM hashtag h LEFT JOIN post_hashtag ph ON ph.hashtag_id=h.hashtag_id
            WHERE h.hashtag_name ILIKE %s
            GROUP BY h.hashtag_id,h.hashtag_name,h.purpose
            ORDER BY posts DESC LIMIT 8
        """, (like_q,)))
        posts = json_rows(db.query("""
            SELECT p.post_id,p.caption,p.visual_seed,u.handle AS creator_handle
            FROM post p JOIN engage_user u ON u.user_id=p.user_id
            WHERE p.caption ILIKE %s OR p.genre ILIKE %s
            ORDER BY p.created_at DESC LIMIT 8
        """, (like_q, like_q)))
        return ok({"users": users, "hashtags": hashtags, "posts": posts})
    except Exception as exc:
        return fail(exc)


@app.get("/api/analytics")
def analytics():
    try:
        summary = json_rows(db.query("""
            SELECT
              (SELECT COUNT(*) FROM engage_user) AS users,
              (SELECT COUNT(*) FROM post) AS posts,
              (SELECT COUNT(*) FROM likes) AS likes,
              (SELECT COUNT(*) FROM saved) AS saves,
              (SELECT COUNT(*) FROM reposts) AS reposts,
              (SELECT COUNT(*) FROM comments) AS comments,
              (SELECT COUNT(*) FROM hashtag) AS hashtags,
              COALESCE((SELECT SUM(impressions) FROM reach),0) AS impressions,
              COALESCE((SELECT SUM(unique_reach) FROM reach),0) AS unique_reach
        """))[0]
        top_posts = json_rows(db.query("""
            SELECT p.post_id,p.caption,u.handle AS creator,COUNT(l.user_id) AS likes
            FROM post p JOIN engage_user u ON u.user_id=p.user_id
            LEFT JOIN likes l ON l.post_id=p.post_id
            GROUP BY p.post_id,p.caption,u.handle ORDER BY likes DESC,p.post_id LIMIT 6
        """))
        hashtags = json_rows(db.query("""
            SELECT h.hashtag_name AS hashtag,COUNT(DISTINCT ph.post_id) AS posts,
                   COUNT(DISTINCT l.user_id || ':' || l.post_id)
                 + COUNT(DISTINCT s.user_id || ':' || s.post_id)
                 + COUNT(DISTINCT r.user_id || ':' || r.post_id) AS engagement
            FROM hashtag h
            LEFT JOIN post_hashtag ph ON ph.hashtag_id=h.hashtag_id
            LEFT JOIN likes l ON l.post_id=ph.post_id
            LEFT JOIN saved s ON s.post_id=ph.post_id
            LEFT JOIN reposts r ON r.post_id=ph.post_id
            GROUP BY h.hashtag_id,h.hashtag_name
            ORDER BY engagement DESC,posts DESC LIMIT 8
        """))
        sentiments = json_rows(db.query("SELECT sentiment,COUNT(*) AS count FROM comments GROUP BY sentiment ORDER BY count DESC"))
        top_users = json_rows(db.query("""
            SELECT user_name,handle,follower_count AS followers
            FROM engage_user ORDER BY follower_count DESC,user_name LIMIT 8
        """))
        return ok({"summary": summary, "top_posts": top_posts, "hashtags": hashtags, "sentiments": sentiments, "top_users": top_users})
    except Exception as exc:
        return fail(exc)


@app.get("/api/data/<entity>")
def data_entity(entity):
    queries = {
        "users": "SELECT user_id,user_name,handle,email,city,follower_count,following_count FROM engage_user ORDER BY user_id",
        "posts": """SELECT p.post_id,u.handle AS creator,p.caption,p.genre,p.post_date,p.location FROM post p JOIN engage_user u ON u.user_id=p.user_id ORDER BY p.post_id""",
        "comments": """SELECT c.comment_id,u.handle AS user,c.post_id,c.comment_text AS comment,c.sentiment,c.parent_comment_id FROM comments c JOIN engage_user u ON u.user_id=c.user_id ORDER BY c.comment_id""",
        "hashtags": "SELECT hashtag_id,hashtag_name AS hashtag,purpose FROM hashtag ORDER BY hashtag_id",
        "reach": "SELECT reach_id,post_id,impressions,unique_reach FROM reach ORDER BY post_id",
        "follows": """SELECT a.handle AS follower,b.handle AS following,f.followed_at FROM following f JOIN engage_user a ON a.user_id=f.follower_user_id JOIN engage_user b ON b.user_id=f.following_user_id ORDER BY follower,following""",
        "engagement": """
            SELECT u.handle AS user,'LIKE' AS action,l.post_id FROM likes l JOIN engage_user u ON u.user_id=l.user_id
            UNION ALL SELECT u.handle,'SAVE',s.post_id FROM saved s JOIN engage_user u ON u.user_id=s.user_id
            UNION ALL SELECT u.handle,'REPOST',r.post_id FROM reposts r JOIN engage_user u ON u.user_id=r.user_id
            ORDER BY user,action,post_id
        """,
    }
    if entity not in queries:
        return fail("Unknown data entity", 404)
    try:
        return ok(json_rows(db.query(queries[entity])))
    except Exception as exc:
        return fail(exc)


@app.get("/api/graph")
def graph():
    try:
        nodes = json_rows(db.query("""
            SELECT 'U:'||user_id AS id,'User' AS type,handle AS label FROM engage_user
            UNION ALL SELECT 'P:'||post_id,'Post',post_id FROM post
            UNION ALL SELECT 'H:'||hashtag_id,'Hashtag',hashtag_name FROM hashtag
            LIMIT 45
        """))
        links = json_rows(db.query("""
            SELECT 'U:'||user_id AS source,'P:'||post_id AS target,'CREATED' AS type FROM post
            UNION ALL SELECT 'U:'||follower_user_id,'U:'||following_user_id,'FOLLOWS' FROM following
            UNION ALL SELECT 'U:'||user_id,'P:'||post_id,'LIKED' FROM likes
            UNION ALL SELECT 'P:'||ph.post_id,'H:'||ph.hashtag_id,'TAGGED_WITH' FROM post_hashtag ph
            LIMIT 90
        """))
        return ok({"nodes": nodes, "links": links})
    except Exception as exc:
        return fail(exc)


def toggle_pair(table, viewer_id, post_id, id_col="user_id"):
    with db.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {table} WHERE post_id=%s AND {id_col}=%s", (post_id, viewer_id))
            exists = cur.fetchone() is not None
            if exists:
                cur.execute(f"DELETE FROM {table} WHERE post_id=%s AND {id_col}=%s", (post_id, viewer_id))
                active = False
            else:
                cur.execute(f"INSERT INTO {table}(post_id,{id_col}) VALUES (%s,%s)", (post_id, viewer_id))
                active = True
        conn.commit()
    return {"active": active}


@app.post("/api/post/<post_id>/like")
def toggle_like(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        row = toggle_pair("likes", viewer_id, post_id)
        log_event_safe(viewer_id, "like_toggle", "post", post_id, row)
        return ok(row)
    except Exception as exc:
        return fail(exc)


@app.post("/api/post/<post_id>/save")
def toggle_save(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        row = toggle_pair("saved", viewer_id, post_id)
        log_event_safe(viewer_id, "save_toggle", "post", post_id, row)
        return ok(row)
    except Exception as exc:
        return fail(exc)


@app.post("/api/post/<post_id>/repost")
def toggle_repost(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT repost_id FROM reposts WHERE post_id=%s AND user_id=%s", (post_id, viewer_id))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM reposts WHERE repost_id=%s", (row["repost_id"],))
                    active = False
                else:
                    cur.execute("INSERT INTO reposts(post_id,user_id,text_highlight) VALUES (%s,%s,%s)", (post_id, viewer_id, "Shared from ENGAGE"))
                    active = True
            conn.commit()
        result = {"active": active}
        log_event_safe(viewer_id, "repost_toggle", "post", post_id, result)
        return ok(result)
    except Exception as exc:
        return fail(exc)


@app.post("/api/post/<post_id>/share")
def share_post(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        db.execute("""INSERT INTO post_shares(post_id,user_id) VALUES (%s,%s)
                      ON CONFLICT (post_id,user_id) DO NOTHING""", (post_id, viewer_id))
        log_event_safe(viewer_id, "post_link_shared", "post", post_id)
        return ok({"shared": True})
    except Exception as exc:
        return fail(exc)


@app.post("/api/follow/<target_id>")
def toggle_follow(target_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    if viewer_id == target_id:
        return fail("You cannot follow yourself.", 400)
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM following WHERE follower_user_id=%s AND following_user_id=%s", (viewer_id, target_id))
                exists = cur.fetchone() is not None
                if exists:
                    cur.execute("DELETE FROM following WHERE follower_user_id=%s AND following_user_id=%s", (viewer_id, target_id))
                    active = False
                else:
                    cur.execute("INSERT INTO following(follower_user_id,following_user_id) VALUES (%s,%s)", (viewer_id, target_id))
                    active = True
                cur.execute("""
                    UPDATE engage_user u SET
                      follower_count=(SELECT COUNT(*) FROM following f WHERE f.following_user_id=u.user_id),
                      following_count=(SELECT COUNT(*) FROM following f WHERE f.follower_user_id=u.user_id)
                    WHERE u.user_id IN (%s,%s)
                """, (viewer_id, target_id))
            conn.commit()
        result = {"active": active}
        log_event_safe(viewer_id, "follow_toggle", "user", target_id, result)
        return ok(result)
    except Exception as exc:
        return fail(exc)


@app.post("/api/post")
def create_post():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    caption = (body.get("caption") or "").strip()
    if not caption:
        return fail("Caption is required.", 400)
    post_id = "P" + uuid.uuid4().hex[:8].upper()
    genre = (body.get("genre") or "general").strip().lower()
    location = (body.get("location") or "").strip()
    media_url = body.get("media_url")
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO post(post_id,user_id,caption,content_type,genre,post_date,language,location,visual_seed,media_url)
                    VALUES (%s,%s,%s,'image',%s,CURRENT_DATE,'English',%s,%s,%s)
                """, (post_id, viewer_id, caption, genre, location, int(uuid.uuid4().int % 18) + 1, media_url))
                cur.execute("INSERT INTO reach(reach_id,post_id,impressions,unique_reach) VALUES (%s,%s,0,0)", ("R" + post_id[1:], post_id))
                tags = sorted(set(re.findall(r"#[A-Za-z0-9_]+", caption)))
                for tag in tags:
                    cur.execute("SELECT hashtag_id FROM hashtag WHERE lower(hashtag_name)=lower(%s)", (tag,))
                    h = cur.fetchone()
                    if h:
                        hid = h["hashtag_id"]
                    else:
                        hid = "H" + uuid.uuid4().hex[:8].upper()
                        cur.execute("INSERT INTO hashtag(hashtag_id,hashtag_name,purpose) VALUES (%s,%s,%s)", (hid, tag, genre))
                    cur.execute("INSERT INTO post_hashtag(post_id,hashtag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (post_id, hid))

                # Course Intelligence V9: tag new educational posts with a
                # real goal/topic so subsequent interactions update trending.
                # Only explicit goal words/hashtags are accepted; don't infer
                # a student's financial status or goal from arbitrary likes.
                cur.execute("""SELECT DISTINCT exam_goal FROM (
                    SELECT exam_goal FROM student_profile
                    UNION SELECT exam_goal FROM learning_resource
                ) x""")
                known_goals = [r['exam_goal'] for r in cur.fetchall()]
                matched_goal = next((g for g in known_goals
                    if re.search(r'(?<![a-z0-9])' + re.escape(g.lower()) + r'(?![a-z0-9])', caption.lower())), None)
                if matched_goal:
                    cur.execute("SELECT DISTINCT topic FROM learning_resource WHERE lower(exam_goal)=lower(%s)", (matched_goal,))
                    topics = [r['topic'] for r in cur.fetchall()]
                    topic = next((t for t in topics if re.search(r'(?<![a-z0-9])' + re.escape(t.lower()) + r'(?![a-z0-9])', caption.lower())), 'general')
                    cur.execute("""INSERT INTO post_learning_signal(post_id,exam_goal,topic,signal_type)
                                   VALUES (%s,%s,%s,%s) ON CONFLICT (post_id) DO NOTHING""",
                                (post_id, matched_goal, topic, 'creator_tag'))
            conn.commit()
        log_event_safe(viewer_id, "post_created", "post", post_id, {"genre": genre})
        return ok({"post_id": post_id})
    except Exception as exc:
        return fail(exc)


@app.post("/api/post/<post_id>/comment")
def add_comment(post_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    text = (body.get("comment_text") or "").strip()
    if not text:
        return fail("Comment is required.", 400)
    cid = "C" + uuid.uuid4().hex[:8].upper()
    sentiment = sentiment_for(text)
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO comments(comment_id,comment_text,sentiment,user_id,post_id)
                    VALUES (%s,%s,%s,%s,%s)
                """, (cid, text, sentiment, viewer_id, post_id))
                for tag in sorted(set(re.findall(r"#[A-Za-z0-9_]+", text))):
                    cur.execute("SELECT hashtag_id FROM hashtag WHERE lower(hashtag_name)=lower(%s)", (tag,))
                    h = cur.fetchone()
                    if h:
                        hid = h["hashtag_id"]
                    else:
                        hid = "H" + uuid.uuid4().hex[:8].upper()
                        cur.execute("INSERT INTO hashtag(hashtag_id,hashtag_name,purpose) VALUES (%s,%s,'comment')", (hid, tag))
                    cur.execute("INSERT INTO comment_hashtag(comment_id,hashtag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (cid, hid))
            conn.commit()
        log_event_safe(viewer_id, "comment_created", "post", post_id, {"comment_id": cid, "sentiment": sentiment})
        return ok({"comment_id": cid, "sentiment": sentiment})
    except Exception as exc:
        return fail(exc)


def get_student_opportunities(viewer_id):
    profile_rows = json_rows(db.query("""
        SELECT sp.*,u.user_name,u.handle,u.email
        FROM student_profile sp JOIN engage_user u ON u.user_id=sp.user_id
        WHERE sp.user_id=%s
    """, (viewer_id,)))
    profile = profile_rows[0] if profile_rows else None
    resources = json_rows(db.query("""
        SELECT user_id,user_name,email,exam_goal,max_monthly_budget,budget_preference,preferred_mode,
               resource_id,provider_name,title,topic,resource_type,delivery_mode,monthly_cost,
               quality_score,scholarship_available,raw_topic_score,goal_score,interest_score,
               affordability_score,mode_score,total_score,recommendation_reason,recommendation_rank
        FROM student_recommendation_explainer
        WHERE user_id=%s AND monthly_cost <= %s
        ORDER BY total_score DESC, recommendation_rank ASC, monthly_cost ASC
    """, (viewer_id, profile['max_monthly_budget'] if profile else 0)))
    if resources:
        with db.connection() as conn:
            with conn.cursor() as cur:
                for r in resources:
                    cur.execute("""
                        INSERT INTO resource_recommendation
                        (user_id,resource_id,interest_score,affordability_score,goal_score,total_score,reason)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (user_id,resource_id) DO UPDATE SET
                          interest_score=EXCLUDED.interest_score,
                          affordability_score=EXCLUDED.affordability_score,
                          goal_score=EXCLUDED.goal_score,
                          total_score=EXCLUDED.total_score,
                          reason=EXCLUDED.reason,
                          generated_at=NOW()
                    """, (viewer_id,r["resource_id"],r["interest_score"],r["affordability_score"],r["goal_score"],r["total_score"],r["recommendation_reason"]))
            conn.commit()
    return profile, resources


@app.get("/api/student-profile")
def student_profile_get():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        profile, resources = get_student_opportunities(viewer_id)
        return ok({"profile": profile, "resources": resources})
    except Exception as exc:
        return fail(exc)


@app.post("/api/student-profile")
def student_profile_save():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        budget = max(0, float(body.get("max_monthly_budget", 0) or 0))
        budget_pref = body.get("budget_preference", "balanced")
        if budget_pref not in {"affordable","balanced","premium"}:
            budget_pref = "balanced"
        mode = body.get("preferred_mode", "online")
        if mode not in {"online","offline","hybrid"}:
            mode = "online"
        db.execute("""
            INSERT INTO student_profile
            (user_id,academic_stage,exam_goal,max_monthly_budget,budget_preference,preferred_mode,language_preference,city)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id) DO UPDATE SET
              academic_stage=EXCLUDED.academic_stage,
              exam_goal=EXCLUDED.exam_goal,
              max_monthly_budget=EXCLUDED.max_monthly_budget,
              budget_preference=EXCLUDED.budget_preference,
              preferred_mode=EXCLUDED.preferred_mode,
              language_preference=EXCLUDED.language_preference,
              city=EXCLUDED.city,
              updated_at=NOW()
        """, (viewer_id, body.get("academic_stage","Class 12"), body.get("exam_goal","JEE"), budget,
              budget_pref, mode, body.get("language_preference","English"), body.get("city")))
        log_event_safe(viewer_id, "student_profile_updated", "student_profile", viewer_id,
                       {"exam_goal": body.get("exam_goal","JEE"), "max_monthly_budget": budget, "preferred_mode": mode})
        profile, resources = get_student_opportunities(viewer_id)
        return ok({"profile": profile, "resources": resources})
    except Exception as exc:
        return fail(exc, 400)


def generate_suggestions(viewer_id):
    pref = json_rows(db.query("SELECT * FROM user_preferences WHERE viewer_id=%s", (viewer_id,)))
    preferences = pref[0] if pref else {"viewer_id": viewer_id, "preferred_genres": [], "preferred_hashtags": [], "recommendation_mode": "balanced"}

    users = json_rows(db.query("""
        SELECT u.user_id,u.user_name,u.handle,u.avatar_color,u.follower_count,
               (SELECT COUNT(*) FROM following f2
                WHERE f2.follower_user_id IN (SELECT following_user_id FROM following WHERE follower_user_id=%s)
                  AND f2.following_user_id=u.user_id) AS mutual_score
        FROM engage_user u
        WHERE u.user_id<>%s
          AND NOT EXISTS(SELECT 1 FROM following f WHERE f.follower_user_id=%s AND f.following_user_id=u.user_id)
        ORDER BY mutual_score DESC,u.follower_count DESC,u.handle
        LIMIT 6
    """, (viewer_id, viewer_id, viewer_id)))
    for u in users:
        u["score"] = float(u.get("mutual_score") or 0) + float(u.get("follower_count") or 0) / 10
        u["reason"] = f"{u.get('mutual_score',0)} mutual connection(s) · {u.get('follower_count',0)} followers"

    posts = json_rows(db.query("""
        WITH top_genres AS (
          SELECT genre,preference_score FROM user_genre_scores WHERE user_id=%s
        )
        SELECT p.post_id,p.caption,p.genre,p.visual_seed,p.media_url,u.handle AS creator_handle,
               eq.engagement_quality_score,
               COALESCE(tg.preference_score,0) AS genre_preference,
               (eq.engagement_quality_score + COALESCE(tg.preference_score,0)*4) AS score
        FROM post p
        JOIN engage_user u ON u.user_id=p.user_id
        JOIN engagement_quality eq ON eq.post_id=p.post_id
        LEFT JOIN top_genres tg ON tg.genre=p.genre
        WHERE p.user_id<>%s
        ORDER BY score DESC,p.created_at DESC
        LIMIT 8
    """, (viewer_id, viewer_id)))
    for p in posts:
        if float(p.get("genre_preference") or 0) > 0:
            p["reason"] = f"Because you engage with {p['genre']} content · quality score {p['engagement_quality_score']}"
        else:
            p["reason"] = f"Trending in ENGAGE · quality score {p['engagement_quality_score']}"

    hashtags = json_rows(db.query("""
        SELECT h.hashtag_name AS hashtag,COUNT(*) AS score
        FROM likes l
        JOIN post_hashtag ph ON ph.post_id=l.post_id
        JOIN hashtag h ON h.hashtag_id=ph.hashtag_id
        WHERE l.user_id=%s
        GROUP BY h.hashtag_name
        ORDER BY score DESC,h.hashtag_name
        LIMIT 8
    """, (viewer_id,)))
    for h in hashtags:
        h["reason"] = f"Appears in {h['score']} post(s) you liked"

    profile, resources = get_student_opportunities(viewer_id)
    return users, posts, hashtags, preferences, profile, resources


def persist_recommendations(viewer_id, users, posts, hashtags):
    with db.connection() as conn:
        with conn.cursor() as cur:
            items = []
            for u in users:
                items.append(("user", u["user_id"], "@" + u["handle"], u["reason"], float(u.get("score", 0)), u))
            for p in posts:
                items.append(("post", p["post_id"], p["post_id"], p["reason"], float(p.get("score", 0)), p))
            for h in hashtags:
                items.append(("hashtag", h["hashtag"], h["hashtag"], h["reason"], float(h.get("score", 0)), h))
            for typ, key, title, reason, score, payload in items:
                cur.execute("""
                    INSERT INTO recommendations(viewer_id,suggestion_type,target_key,title,reason,score,payload)
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                    ON CONFLICT(viewer_id,suggestion_type,target_key) DO UPDATE SET
                      title=EXCLUDED.title,reason=EXCLUDED.reason,score=EXCLUDED.score,payload=EXCLUDED.payload,
                      generated_at=NOW(),updated_at=NOW()
                """, (viewer_id, typ, key, title, reason, score, json.dumps(payload, default=str)))
        conn.commit()


@app.get("/api/suggestions")
def suggestions():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        users, posts, hashtags, preferences, profile, resources = generate_suggestions(viewer_id)
        persist_recommendations(viewer_id, users, posts, hashtags)
        statuses = {(r["suggestion_type"], r["target_key"]): r["status"] for r in db.query("SELECT suggestion_type,target_key,status FROM recommendations WHERE viewer_id=%s", (viewer_id,))}
        users = [x for x in users if statuses.get(("user", x["user_id"])) != "dismissed"]
        posts = [x for x in posts if statuses.get(("post", x["post_id"])) != "dismissed"]
        hashtags = [x for x in hashtags if statuses.get(("hashtag", x["hashtag"])) != "dismissed"]
        return ok({"users": users, "posts": posts, "hashtags": hashtags, "preferences": preferences, "profile": profile, "resources": resources, "postgres_persisted": True})
    except Exception as exc:
        return fail(exc)


@app.post("/api/suggestions/status")
def suggestion_status():
    body = request.get_json(silent=True) or {}
    try:
        db.execute("""
            UPDATE recommendations SET status=%s,updated_at=NOW()
            WHERE viewer_id=%s AND suggestion_type=%s AND target_key=%s
        """, (body.get("status", "dismissed"), body.get("viewer_id", "U007"), body.get("suggestion_type"), body.get("target_key")))
        return ok()
    except Exception as exc:
        return fail(exc)


@app.post("/api/suggestions/feedback")
def suggestion_feedback():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    feedback = body.get("feedback", "interested")
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO recommendation_feedback(viewer_id,suggestion_type,target_key,feedback)
                               VALUES (%s,%s,%s,%s)""",
                            (viewer_id, body.get("suggestion_type"), body.get("target_key"), feedback))
                cur.execute("""
                    UPDATE recommendations SET status=%s,updated_at=NOW()
                    WHERE viewer_id=%s AND suggestion_type=%s AND target_key=%s
                """, ("dismissed" if feedback == "not_interested" else "interested", viewer_id, body.get("suggestion_type"), body.get("target_key")))
            conn.commit()
        return ok()
    except Exception as exc:
        return fail(exc)


@app.get("/api/preferences")
def get_preferences():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        rows = json_rows(db.query("SELECT * FROM user_preferences WHERE viewer_id=%s", (viewer_id,)))
        return ok(rows[0] if rows else {"viewer_id": viewer_id, "preferred_genres": [], "preferred_hashtags": [], "recommendation_mode": "balanced"})
    except Exception as exc:
        return fail(exc)


@app.post("/api/preferences")
def save_preferences():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        db.execute("""
            INSERT INTO user_preferences(viewer_id,preferred_genres,preferred_hashtags,recommendation_mode)
            VALUES (%s,%s::jsonb,%s::jsonb,%s)
            ON CONFLICT(viewer_id) DO UPDATE SET
              preferred_genres=EXCLUDED.preferred_genres,
              preferred_hashtags=EXCLUDED.preferred_hashtags,
              recommendation_mode=EXCLUDED.recommendation_mode,
              updated_at=NOW()
        """, (viewer_id, json.dumps(body.get("preferred_genres", [])), json.dumps(body.get("preferred_hashtags", [])), body.get("recommendation_mode", "balanced")))
        return ok()
    except Exception as exc:
        return fail(exc)


@app.get("/api/messages/conversations")
def message_conversations():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        rows = json_rows(db.query("""
            WITH peers AS (
              SELECT CASE WHEN sender_id=%s THEN receiver_id ELSE sender_id END AS peer_id,
                     MAX(sent_at) AS last_at
              FROM direct_messages
              WHERE sender_id=%s OR receiver_id=%s
              GROUP BY CASE WHEN sender_id=%s THEN receiver_id ELSE sender_id END
            )
            SELECT p.peer_id,u.user_name,u.handle,u.avatar_color,
                   (SELECT body FROM direct_messages d
                    WHERE (d.sender_id=%s AND d.receiver_id=p.peer_id) OR (d.sender_id=p.peer_id AND d.receiver_id=%s)
                    ORDER BY sent_at DESC LIMIT 1) AS last_message,
                   (SELECT COUNT(*) FROM direct_messages d2
                    WHERE d2.sender_id=p.peer_id AND d2.receiver_id=%s AND d2.read_at IS NULL) AS unread_count,
                   p.last_at
            FROM peers p JOIN engage_user u ON u.user_id=p.peer_id
            ORDER BY p.last_at DESC
        """, (viewer_id, viewer_id, viewer_id, viewer_id, viewer_id, viewer_id, viewer_id)))
        return ok(rows)
    except Exception as exc:
        return fail(exc)


@app.get("/api/messages/<peer_id>")
def get_messages(peer_id):
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE direct_messages SET read_at=NOW() WHERE sender_id=%s AND receiver_id=%s AND read_at IS NULL", (peer_id, viewer_id))
                cur.execute("""
                    SELECT id,sender_id,receiver_id,body,sent_at,read_at FROM direct_messages
                    WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)
                    ORDER BY sent_at
                """, (viewer_id, peer_id, peer_id, viewer_id))
                rows = cur.fetchall()
            conn.commit()
        return ok(json_rows(rows))
    except Exception as exc:
        return fail(exc)


@app.post("/api/messages/<peer_id>")
def send_message(peer_id):
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    text = (body.get("body") or "").strip()
    if not text:
        return fail("Message is required", 400)
    try:
        rows = db.execute("""
            INSERT INTO direct_messages(sender_id,receiver_id,body) VALUES (%s,%s,%s)
            RETURNING id,sender_id,receiver_id,body,sent_at
        """, (viewer_id, peer_id, text), returning=True)
        return ok(json_rows(rows)[0])
    except Exception as exc:
        return fail(exc)


@app.get("/api/stories")
def get_stories():
    try:
        return ok(json_rows(db.query("""
            SELECT s.id,s.user_id,u.user_name,u.handle,u.avatar_color,u.avatar_url,s.caption,s.media_url,s.created_at,s.expires_at
            FROM stories s JOIN engage_user u ON u.user_id=s.user_id
            WHERE s.expires_at>NOW() ORDER BY s.created_at DESC
        """)))
    except Exception as exc:
        return fail(exc)


@app.post("/api/stories")
def add_story():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    try:
        rows = db.execute("""
            INSERT INTO stories(user_id,caption,media_url) VALUES (%s,%s,%s)
            RETURNING id,user_id,caption,media_url,created_at,expires_at
        """, (viewer_id, body.get("caption"), body.get("media_url")), returning=True)
        return ok(json_rows(rows)[0])
    except Exception as exc:
        return fail(exc)


@app.get("/api/recent-searches")
def recent_searches():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        return ok(json_rows(db.query("""
            SELECT search_text,MAX(searched_at) AS searched_at FROM search_history
            WHERE viewer_id=%s GROUP BY search_text ORDER BY searched_at DESC LIMIT 8
        """, (viewer_id,))))
    except Exception as exc:
        return fail(exc)


@app.get("/api/app-events")
def app_events():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        return ok(json_rows(db.query("""
            SELECT id,event_type,target_type,target_key,metadata,created_at
            FROM app_events WHERE viewer_id=%s ORDER BY created_at DESC LIMIT 40
        """, (viewer_id,))))
    except Exception as exc:
        return fail(exc)


ALLOWED_INSPECT = {
    "engage_user", "following", "post", "likes", "saved", "reposts", "post_shares",
    "post_hashtag", "hashtag", "comment_hashtag", "comments", "comment_likes", "reach",
    "user_preference_summary", "user_genre_scores", "engagement_quality", "creator_summary",
    "recommendations", "recommendation_feedback", "user_preferences", "saved_queries", "query_history",
    "direct_messages", "stories", "search_history", "app_events",
    "student_profile", "post_learning_signal", "learning_resource", "resource_recommendation", "post_view_event",
    "student_topic_scores", "student_resource_matches", "student_recommendation_explainer",
    "course_post_engagement", "course_goal_trending", "course_resource_trending",
}


@app.get("/api/postgres/table/<table_name>")
def postgres_table(table_name):
    if table_name not in ALLOWED_INSPECT:
        return fail("Table/view not allowed", 404)
    try:
        rows = db.query(f'SELECT * FROM "{table_name}" LIMIT 100')
        return ok(json_rows(rows))
    except Exception as exc:
        return fail(exc)


@app.post("/api/upload")
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return fail("No file selected", 400)
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_UPLOADS:
        return fail("Unsupported image type", 400)
    name = f"{uuid.uuid4().hex}{ext}"
    file.save(UPLOAD_DIR / secure_filename(name))
    return ok({"media_url": f"/static/uploads/{name}"})


SQL_EXAMPLES = [
    {"name": "Narasimhan learning matches", "query": "SELECT user_name,email,exam_goal,max_monthly_budget,provider_name,title,monthly_cost,total_score,recommendation_reason FROM student_recommendation_explainer WHERE user_id='U007' ORDER BY recommendation_rank;"},
    {"name": "Affordable-student learning matches", "query": "SELECT user_name,max_monthly_budget,provider_name,title,monthly_cost,total_score,recommendation_reason FROM student_recommendation_explainer WHERE user_id='U008' ORDER BY recommendation_rank;"},
    {"name": "All 12 PPT ER tables", "query": "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('engage_user','following','post','likes','saved','reposts','post_hashtag','hashtag','comment_hashtag','comments','comment_likes','reach') ORDER BY table_name;"},
    {"name": "Posts with creators using JOIN", "query": "SELECT p.post_id,u.user_name,p.genre,p.caption FROM post p JOIN engage_user u ON u.user_id=p.user_id ORDER BY p.created_at DESC;"},
    {"name": "What Narasimhan engaged with", "query": "SELECT p.post_id,p.genre,pls.topic,p.caption FROM likes l JOIN post p ON p.post_id=l.post_id LEFT JOIN post_learning_signal pls ON pls.post_id=p.post_id WHERE l.user_id='U007' ORDER BY l.liked_at DESC;"},
    {"name": "Weighted topic interest", "query": "SELECT * FROM student_topic_scores WHERE user_id='U007' ORDER BY topic_score DESC;"},
    {"name": "Resources within a selected budget", "query": "SELECT lr.provider_name,lr.title,lr.monthly_cost,sp.max_monthly_budget FROM student_profile sp JOIN learning_resource lr ON lr.exam_goal=sp.exam_goal WHERE sp.user_id='U008' AND lr.monthly_cost<=sp.max_monthly_budget ORDER BY lr.monthly_cost,lr.quality_score DESC;"},
    {"name": "Engagement quality view", "query": "SELECT * FROM engagement_quality ORDER BY engagement_quality_score DESC;"},
    {"name": "Nested subquery: above-average reach", "query": "SELECT p.post_id,p.caption,r.unique_reach FROM post p JOIN reach r ON r.post_id=p.post_id WHERE r.unique_reach>(SELECT AVG(unique_reach) FROM reach) ORDER BY r.unique_reach DESC;"},
    {"name": "Correlated EXISTS: users who saved JEE content", "query": "SELECT u.user_id,u.user_name FROM engage_user u WHERE EXISTS (SELECT 1 FROM saved s JOIN post_learning_signal pls ON pls.post_id=s.post_id WHERE s.user_id=u.user_id AND pls.exam_goal='JEE') ORDER BY u.user_name;"},
]



@app.get("/api/sql/examples")
def sql_examples():
    return ok(SQL_EXAMPLES)


@app.get("/api/sql/suggest")
def sql_suggest():
    q = (request.args.get("q") or "").lower()
    tokens = set(re.findall(r"[a-z0-9_]+", q))
    scored = []
    for ex in SQL_EXAMPLES:
        text = (ex["name"] + " " + ex["query"]).lower()
        score = sum(2 for t in tokens if t in text)
        if "follow" in q and "follower" in text:
            score += 3
        if "like" in q and "like" in text:
            score += 3
        if "recommend" in q and "preference" in text:
            score += 4
        scored.append({**ex, "score": score})
    scored.sort(key=lambda x: (-x["score"], x["name"]))
    return ok(scored[:5])


BLOCKED_SQL = re.compile(r"\b(drop|truncate|alter|grant|revoke|copy|vacuum|cluster|reindex|listen|notify|do|call)\b", re.I)
ALLOWED_START = re.compile(r"^(select|with|explain|insert|update|delete)\b", re.I)


def normalize_single_sql(query):
    q = re.sub(r"--.*?$", "", query or "", flags=re.M).strip()
    if q.endswith(";"):
        q = q[:-1].strip()
    if not q:
        raise ValueError("Enter an SQL query first")
    if ";" in q:
        raise ValueError("Run exactly one SQL statement at a time")
    if not ALLOWED_START.match(q):
        raise ValueError("Console supports SELECT/WITH/EXPLAIN/INSERT/UPDATE/DELETE. Destructive schema commands are blocked.")
    if BLOCKED_SQL.search(q):
        raise ValueError("That SQL command is blocked in the demo console")
    return q


@app.post("/api/sql")
def sql_console():
    body = request.get_json(silent=True) or {}
    viewer_id = body.get("viewer_id", "U007")
    raw = body.get("query", "")
    started = time.perf_counter()
    try:
        query = normalize_single_sql(raw)
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '5s'")
                cur.execute(query)
                rows = cur.fetchmany(200) if cur.description else []
                row_count = len(rows) if cur.description else max(cur.rowcount, 0)
                contains_updates = not re.match(r"^(select|with|explain)\b", query, re.I)
            conn.commit()
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        log_query_safe(viewer_id, raw, True, row_count)
        summary = {
            "query_type": query.split(None, 1)[0].upper(),
            "contains_updates": contains_updates,
            "result_consumed_after_ms": elapsed,
            "nodes_created": 0, "nodes_deleted": 0,
            "relationships_created": 0, "relationships_deleted": 0,
            "properties_set": row_count if contains_updates else 0,
        }
        return ok(json_rows(rows), summary=summary)
    except Exception as exc:
        log_query_safe(viewer_id, raw, False, 0, str(exc))
        return fail(exc, 400)




ORACLE_EXAMPLES = [
    {
        "name": "All users",
        "query": "SELECT user_id, user_name, email, city FROM engage_user ORDER BY user_id"
    },
    {
        "name": "Posts with creators using JOIN",
        "query": "SELECT p.post_id, u.user_name, p.genre, p.caption FROM post p JOIN engage_user u ON u.user_id = p.user_id ORDER BY p.created_at DESC FETCH FIRST 20 ROWS ONLY"
    },
    {
        "name": "Who liked which post",
        "query": "SELECT u.user_name, l.post_id, p.genre FROM likes l JOIN engage_user u ON u.user_id = l.user_id JOIN post p ON p.post_id = l.post_id ORDER BY l.post_id, u.user_name"
    },
    {
        "name": "Follower count using LEFT JOIN",
        "query": "SELECT u.user_id, u.user_name, COUNT(f.follower_user_id) AS follower_count FROM engage_user u LEFT JOIN following f ON f.following_user_id = u.user_id GROUP BY u.user_id, u.user_name ORDER BY follower_count DESC"
    },
    {
        "name": "JEE learning resources by cost",
        "query": "SELECT resource_id, provider_name, title, monthly_cost, quality_score FROM learning_resource WHERE exam_goal = 'JEE' ORDER BY monthly_cost, quality_score DESC"
    },
    {
        "name": "Narasimhan study profile",
        "query": "SELECT u.user_name, u.email, s.exam_goal, s.max_monthly_budget, s.budget_preference, s.preferred_mode FROM engage_user u JOIN student_profile s ON s.user_id = u.user_id WHERE u.user_id = 'U007'"
    },
]

ORACLE_BLOCKED_SQL = re.compile(
    r"\b(drop|truncate|alter|grant|revoke|shutdown|startup|host|spool|connect|disconnect)\b",
    re.I,
)
ORACLE_ALLOWED_START = re.compile(r"^(select|with|insert|update|delete)\b", re.I)


def normalize_oracle_sql(query):
    q = re.sub(r"--.*?$", "", query or "", flags=re.M).strip()
    if q.endswith(";"):
        q = q[:-1].strip()
    if not q:
        raise ValueError("Enter an Oracle SQL statement first")
    if ";" in q:
        raise ValueError("Run exactly one Oracle SQL statement at a time")
    if not ORACLE_ALLOWED_START.match(q):
        raise ValueError("Oracle Studio supports SELECT/WITH/INSERT/UPDATE/DELETE. DDL is blocked in this demo interface.")
    if ORACLE_BLOCKED_SQL.search(q):
        raise ValueError("That Oracle command is blocked in the Studio interface")
    return q


@app.get("/api/oracle/status")
def oracle_status():
    try:
        return ok(oracle_db.verify())
    except Exception as exc:
        return fail(exc, 503)


@app.get("/api/oracle/examples")
def oracle_examples():
    return ok(ORACLE_EXAMPLES)


@app.post("/api/oracle/sql")
def oracle_sql_console():
    body = request.get_json(silent=True) or {}
    raw = body.get("query", "")
    started = time.perf_counter()
    try:
        query = normalize_oracle_sql(raw)
        with oracle_db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                if cur.description:
                    columns = [d[0].lower() for d in cur.description]
                    raw_rows = cur.fetchmany(200)
                    rows = [
                        {columns[i]: oracle_value(value) for i, value in enumerate(row)}
                        for row in raw_rows
                    ]
                    row_count = len(rows)
                    contains_updates = False
                else:
                    rows = []
                    row_count = max(cur.rowcount, 0)
                    contains_updates = True
            conn.commit()

        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return ok(
            rows,
            summary={
                "engine": "Oracle",
                "query_type": query.split(None, 1)[0].upper(),
                "contains_updates": contains_updates,
                "row_count": row_count,
                "elapsed_ms": elapsed,
            },
        )
    except Exception as exc:
        return fail(exc, 400)


@app.get("/api/postgres/status")
def postgres_status():
    return health()


@app.get("/api/query-history")
def query_history():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        return ok(json_rows(db.query("""
            SELECT id,viewer_id,query_text,success,row_count,error_message,executed_at
            FROM query_history WHERE viewer_id=%s ORDER BY executed_at DESC LIMIT 30
        """, (viewer_id,))))
    except Exception as exc:
        return fail(exc)


@app.get("/api/saved-queries")
def saved_queries():
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        return ok(json_rows(db.query("""
            SELECT id,viewer_id,title,query_text,category,created_at
            FROM saved_queries WHERE viewer_id=%s ORDER BY created_at DESC
        """, (viewer_id,))))
    except Exception as exc:
        return fail(exc)


@app.post("/api/saved-queries")
def save_query():
    body = request.get_json(silent=True) or {}
    try:
        rows = db.execute("""
            INSERT INTO saved_queries(viewer_id,title,query_text,category)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT(viewer_id,title) DO UPDATE SET query_text=EXCLUDED.query_text,category=EXCLUDED.category,created_at=NOW()
            RETURNING id,viewer_id,title,query_text,category,created_at
        """, (body.get("viewer_id", "U007"), body.get("title", "My SQL query"), body.get("query_text", ""), body.get("category", "demo")), returning=True)
        return ok(json_rows(rows)[0])
    except Exception as exc:
        return fail(exc)


@app.delete("/api/saved-queries/<int:query_id>")
def delete_saved_query(query_id):
    viewer_id = request.args.get("viewer_id", "U007")
    try:
        db.execute("DELETE FROM saved_queries WHERE id=%s AND viewer_id=%s", (query_id, viewer_id))
        return ok()
    except Exception as exc:
        return fail(exc)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
