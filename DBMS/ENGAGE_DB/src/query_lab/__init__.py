import re
import time
from flask import Blueprint, jsonify, render_template, request
from db import PostgresDB, json_rows
from oracle_db import OracleDB

query_lab_bp = Blueprint(
    "query_lab",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/query-lab",
)

db = PostgresDB()
oracle_db = OracleDB()

TEAM_MEMBERS = ["Narasimhan", "Shri Vishwa", "Skandhan"]

CORE_TABLES = [
    "engage_user", "following", "post", "likes", "saved", "reposts",
    "post_hashtag", "hashtag", "comment_hashtag", "comments", "comment_likes", "reach",
]

QUERY_LIBRARY = [
    {"id":"q1","title":"Narasimhan: full recommendation explanation","concept":"VIEW + JOIN + RANKING","why":"Shows identity, selected budget, engagement-derived interest and ranked learning options in one faculty-friendly result.","sql":"SELECT user_name,email,exam_goal,max_monthly_budget,provider_name,title,monthly_cost,interest_score,affordability_score,total_score,recommendation_reason FROM student_recommendation_explainer WHERE user_id='U007' ORDER BY recommendation_rank;"},
    {"id":"q2","title":"Affordable-profile recommendation","concept":"PERSONALIZATION","why":"Shows how the same JEE goal produces free/low-cost options when the student explicitly selects a smaller budget.","sql":"SELECT user_name,max_monthly_budget,provider_name,title,monthly_cost,scholarship_available,total_score,recommendation_reason FROM student_recommendation_explainer WHERE user_id='U008' ORDER BY recommendation_rank;"},
    {"id":"q3","title":"What engagement created the interest profile?","concept":"MULTI-TABLE JOIN","why":"Joins likes, posts and learning signals to show why a topic became important for the student.","sql":"SELECT l.user_id,p.post_id,p.genre,pls.topic,p.caption FROM likes l JOIN post p ON p.post_id=l.post_id JOIN post_learning_signal pls ON pls.post_id=p.post_id WHERE l.user_id='U007' ORDER BY l.liked_at DESC;"},
    {"id":"q4","title":"Weighted topic interest","concept":"VIEW + AGGREGATION","why":"Combines LIKE, SAVE, REPOST and COMMENT weights into explainable topic scores.","sql":"SELECT * FROM student_topic_scores WHERE user_id='U007' ORDER BY topic_score DESC;"},
    {"id":"q5","title":"Resources within Arun's selected budget","concept":"JOIN + FILTER","why":"Demonstrates that affordability is an explicit profile constraint, not a guessed socioeconomic attribute.","sql":"SELECT sp.user_id,sp.max_monthly_budget,lr.provider_name,lr.title,lr.monthly_cost FROM student_profile sp JOIN learning_resource lr ON lr.exam_goal=sp.exam_goal WHERE sp.user_id='U008' AND lr.monthly_cost<=sp.max_monthly_budget ORDER BY lr.monthly_cost,lr.quality_score DESC;"},
    {"id":"q6","title":"Posts with creators","concept":"INNER JOIN","why":"A standard ER-model foreign-key JOIN between POST and USER.","sql":"SELECT p.post_id,u.user_name,u.email,p.genre,p.caption FROM post p JOIN engage_user u ON u.user_id=p.user_id ORDER BY p.created_at DESC;"},
    {"id":"q7","title":"Genre engagement summary","concept":"GROUP BY + AGGREGATES","why":"Shows which content genres receive likes, saves and reposts.","sql":"SELECT p.genre,COUNT(DISTINCT l.user_id||':'||l.post_id) AS likes,COUNT(DISTINCT s.user_id||':'||s.post_id) AS saves,COUNT(DISTINCT r.user_id||':'||r.post_id) AS reposts FROM post p LEFT JOIN likes l ON l.post_id=p.post_id LEFT JOIN saved s ON s.post_id=p.post_id LEFT JOIN reposts r ON r.post_id=p.post_id GROUP BY p.genre ORDER BY likes DESC,saves DESC;"},
    {"id":"q8","title":"Above-average reach","concept":"NESTED SUBQUERY","why":"Shows a classic nested subquery using the PPT REACH table.","sql":"SELECT p.post_id,p.caption,r.unique_reach FROM post p JOIN reach r ON r.post_id=p.post_id WHERE r.unique_reach>(SELECT AVG(unique_reach) FROM reach) ORDER BY r.unique_reach DESC;"},
    {"id":"q9","title":"Users who saved JEE content","concept":"CORRELATED EXISTS","why":"Correlates each user against SAVED plus the learning-signal layer.","sql":"SELECT u.user_id,u.user_name FROM engage_user u WHERE EXISTS (SELECT 1 FROM saved s JOIN post_learning_signal pls ON pls.post_id=s.post_id WHERE s.user_id=u.user_id AND pls.exam_goal='JEE') ORDER BY u.user_name;"},
    {"id":"q10","title":"Engagement Quality Score","concept":"SQL VIEW","why":"Uses the PPT project metric across likes, comments, reposts and saves.","sql":"SELECT * FROM engagement_quality ORDER BY engagement_quality_score DESC;"},
    {"id":"q11","title":"Verify all PPT ER tables","concept":"INFORMATION_SCHEMA","why":"Proves all 12 relational tables shown in the ER/PPT exist in PostgreSQL.","sql":"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('engage_user','following','post','likes','saved','reposts','post_hashtag','hashtag','comment_hashtag','comments','comment_likes','reach') ORDER BY table_name;"},
]


BLOCKED = re.compile(r"\b(drop|truncate|alter|grant|revoke|copy|vacuum|cluster|reindex|listen|notify|do|call)\b", re.I)
ALLOWED = re.compile(r"^(select|with|explain|insert|update|delete)\b", re.I)


def clean_sql(raw):
    q = re.sub(r"--.*?$", "", raw or "", flags=re.M).strip()
    if q.endswith(";"):
        q = q[:-1].strip()
    if not q:
        raise ValueError("Enter an SQL statement")
    if ";" in q:
        raise ValueError("Run exactly one statement at a time")
    if not ALLOWED.match(q):
        raise ValueError("Use SELECT/WITH/EXPLAIN/INSERT/UPDATE/DELETE in the live console")
    if BLOCKED.search(q):
        raise ValueError("Destructive schema commands are blocked in the live demo console")
    return q


def execute_sql(raw):
    q = clean_sql(raw)
    started = time.perf_counter()
    with db.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout='5s'")
            cur.execute(q)
            cols = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchmany(200) if cur.description else []
            row_count = len(rows) if cur.description else max(cur.rowcount, 0)
        conn.commit()
    return {
        "ok": True,
        "columns": cols,
        "rows": json_rows(rows),
        "row_count": row_count,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "engine": "PostgreSQL",
    }


def execute_oracle_sql(raw):
    q = clean_sql(raw)
    started = time.perf_counter()
    with oracle_db.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            cols = [d[0].lower() for d in cur.description] if cur.description else []
            rows = cur.fetchmany(200) if cur.description else []
            row_count = len(rows) if cur.description else max(cur.rowcount, 0)
        conn.commit()
    normalized=[]
    for row in rows:
        item={}
        for k,v in zip(cols,row):
            if hasattr(v,"read"):
                try: v=v.read()
                except Exception: v=str(v)
            item[k]=v.isoformat(sep=" ") if hasattr(v,"isoformat") else v
        normalized.append(item)
    return {"ok":True,"columns":cols,"rows":normalized,"row_count":row_count,
            "elapsed_ms":round((time.perf_counter()-started)*1000,2),"engine":"Oracle"}


@query_lab_bp.get("/")
def index():
    return render_template(
        "query_lab.html",
        team_members=TEAM_MEMBERS,
        query_library=QUERY_LIBRARY,
        core_tables=CORE_TABLES,
    )


@query_lab_bp.get("/api/health")
def health():
    try:
        row = db.verify()
        return jsonify({"ok": True, "postgres": {"database": row["database"], "db_user": row["db_user"]}})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@query_lab_bp.get("/api/oracle-health")
def oracle_health():
    try:
        row=oracle_db.verify()
        return jsonify({"ok":True,"oracle":row})
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),500


@query_lab_bp.post("/api/custom-oracle")
def custom_oracle_sql():
    body=request.get_json(silent=True) or {}
    try:
        return jsonify(execute_oracle_sql(str(body.get("sql",""))))
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),400


@query_lab_bp.post("/api/run/<query_id>")
def run_library(query_id):
    item = next((q for q in QUERY_LIBRARY if q["id"] == query_id), None)
    if not item:
        return jsonify({"ok": False, "error": "Unknown query"}), 404
    try:
        return jsonify(execute_sql(item["sql"]))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@query_lab_bp.post("/api/custom-select")
def custom_sql():
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(execute_sql(str(body.get("sql", ""))))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@query_lab_bp.get("/api/table/<table_name>")
def table(table_name):
    allowed = set(CORE_TABLES + ["user_preference_summary", "user_genre_scores", "engagement_quality", "creator_summary", "student_profile", "post_learning_signal", "learning_resource", "resource_recommendation", "post_view_event", "student_topic_scores", "student_resource_matches", "student_recommendation_explainer"])
    if table_name not in allowed:
        return jsonify({"ok": False, "error": "Unknown table/view"}), 404
    try:
        rows = db.query(f'SELECT * FROM "{table_name}" LIMIT 100')
        return jsonify({"ok": True, "columns": list(rows[0].keys()) if rows else [], "rows": json_rows(rows), "row_count": len(rows), "elapsed_ms": 0, "engine": "PostgreSQL"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@query_lab_bp.post("/api/toggle-like")
def toggle_like():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id", "U007")
    post_id = body.get("post_id", "P001")
    try:
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM likes WHERE user_id=%s AND post_id=%s", (user_id, post_id))
                exists = cur.fetchone() is not None
                if exists:
                    cur.execute("DELETE FROM likes WHERE user_id=%s AND post_id=%s", (user_id, post_id))
                    action = "UNLIKED"
                else:
                    cur.execute("INSERT INTO likes(user_id,post_id) VALUES (%s,%s)", (user_id, post_id))
                    action = "LIKED"
                cur.execute("SELECT COUNT(*) AS c FROM likes WHERE post_id=%s", (post_id,))
                count = cur.fetchone()["c"]
            conn.commit()
        return jsonify({"ok": True, "action": action, "user_id": user_id, "post_id": post_id, "like_count": count})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
