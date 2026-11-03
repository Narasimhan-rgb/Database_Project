import json
import os
import re
from contextlib import contextmanager

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


class PostgresStore:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "")
        self.database = os.getenv("POSTGRES_DB", "engage_meta")
        self.admin_db = os.getenv("POSTGRES_ADMIN_DB", "postgres")
        self.last_error = None
        self._ready = False

    def _conninfo(self, database=None):
        return (
            f"host={self.host} port={self.port} dbname={database or self.database} "
            f"user={self.user} password={self.password} connect_timeout=3"
        )

    def initialize(self):
        if self._ready:
            return True

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.database):
            raise ValueError("POSTGRES_DB contains invalid characters.")

        # Create the application database if needed.
        with psycopg.connect(self._conninfo(self.admin_db), autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.database,))
                if cur.fetchone() is None:
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database)))

        with psycopg.connect(self._conninfo(), autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS query_history (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
                        query_text TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        row_count INTEGER NOT NULL DEFAULT 0,
                        error_message TEXT,
                        executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS saved_queries (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
                        title VARCHAR(160) NOT NULL,
                        query_text TEXT NOT NULL,
                        category VARCHAR(64) NOT NULL DEFAULT 'general',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE(viewer_id, title)
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommendations (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
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
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommendation_feedback (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
                        suggestion_type VARCHAR(32) NOT NULL,
                        target_key VARCHAR(128) NOT NULL,
                        feedback VARCHAR(24) NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        viewer_id VARCHAR(32) PRIMARY KEY,
                        preferred_genres JSONB NOT NULL DEFAULT '[]'::jsonb,
                        preferred_hashtags JSONB NOT NULL DEFAULT '[]'::jsonb,
                        recommendation_mode VARCHAR(24) NOT NULL DEFAULT 'balanced',
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS direct_messages (
                        id BIGSERIAL PRIMARY KEY,
                        sender_id VARCHAR(32) NOT NULL,
                        receiver_id VARCHAR(32) NOT NULL,
                        body TEXT NOT NULL,
                        sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        read_at TIMESTAMPTZ
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stories (
                        id BIGSERIAL PRIMARY KEY,
                        user_id VARCHAR(32) NOT NULL,
                        caption VARCHAR(500),
                        media_url TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
                        search_text VARCHAR(300) NOT NULL,
                        searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_events (
                        id BIGSERIAL PRIMARY KEY,
                        viewer_id VARCHAR(32) NOT NULL,
                        event_type VARCHAR(64) NOT NULL,
                        target_type VARCHAR(64),
                        target_key VARCHAR(128),
                        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_history_viewer_time
                    ON query_history(viewer_id, executed_at DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_recommendations_viewer_status
                    ON recommendations(viewer_id, status, score DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_pair_time
                    ON direct_messages(sender_id, receiver_id, sent_at DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stories_expiry
                    ON stories(expires_at DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_search_history_viewer_time
                    ON search_history(viewer_id, searched_at DESC)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_app_events_viewer_time
                    ON app_events(viewer_id, created_at DESC)
                """)

        self._ready = True
        self.last_error = None
        return True

    def try_initialize(self):
        try:
            return self.initialize()
        except Exception as exc:
            self._ready = False
            self.last_error = str(exc)
            return False

    def status(self):
        ok = self.try_initialize()
        return {
            "connected": ok,
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "error": None if ok else self.last_error,
        }

    @contextmanager
    def connection(self):
        if not self.try_initialize():
            raise RuntimeError(
                "PostgreSQL is not connected. Start PostgreSQL and check the POSTGRES_* values in .env. "
                + (self.last_error or "")
            )
        with psycopg.connect(self._conninfo(), row_factory=dict_row) as conn:
            yield conn

    def log_query(self, viewer_id, query_text, success, row_count=0, error_message=None):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO query_history
                    (viewer_id, query_text, success, row_count, error_message)
                    VALUES (%s, %s, %s, %s, %s)
                """, (viewer_id, query_text, bool(success), int(row_count), error_message))
            conn.commit()

    def query_history(self, viewer_id, limit=30):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, viewer_id, query_text, success, row_count, error_message, executed_at
                    FROM query_history
                    WHERE viewer_id = %s
                    ORDER BY executed_at DESC
                    LIMIT %s
                """, (viewer_id, int(limit)))
                return cur.fetchall()

    def save_query(self, viewer_id, title, query_text, category="general"):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO saved_queries(viewer_id, title, query_text, category)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(viewer_id, title)
                    DO UPDATE SET
                        query_text = EXCLUDED.query_text,
                        category = EXCLUDED.category,
                        created_at = NOW()
                    RETURNING id, viewer_id, title, query_text, category, created_at
                """, (viewer_id, title, query_text, category))
                row = cur.fetchone()
            conn.commit()
            return row

    def saved_queries(self, viewer_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, viewer_id, title, query_text, category, created_at
                    FROM saved_queries
                    WHERE viewer_id = %s
                    ORDER BY created_at DESC
                """, (viewer_id,))
                return cur.fetchall()

    def delete_saved_query(self, viewer_id, query_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM saved_queries WHERE id = %s AND viewer_id = %s",
                    (int(query_id), viewer_id)
                )
            conn.commit()

    def store_recommendations(self, viewer_id, items):
        if not items:
            return
        with self.connection() as conn:
            with conn.cursor() as cur:
                for item in items:
                    cur.execute("""
                        INSERT INTO recommendations
                        (viewer_id, suggestion_type, target_key, title, reason, score, payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT(viewer_id, suggestion_type, target_key)
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            reason = EXCLUDED.reason,
                            score = EXCLUDED.score,
                            payload = EXCLUDED.payload,
                            status = CASE
                                WHEN recommendations.status = 'dismissed' THEN 'dismissed'
                                ELSE 'new'
                            END,
                            generated_at = NOW(),
                            updated_at = NOW()
                    """, (
                        viewer_id,
                        item["suggestion_type"],
                        item["target_key"],
                        item["title"],
                        item["reason"],
                        float(item.get("score", 0)),
                        json.dumps(item.get("payload", {})),
                    ))
            conn.commit()

    def recommendation_statuses(self, viewer_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT suggestion_type, target_key, status
                    FROM recommendations
                    WHERE viewer_id = %s
                """, (viewer_id,))
                return {
                    (r["suggestion_type"], r["target_key"]): r["status"]
                    for r in cur.fetchall()
                }


    def add_feedback(self, viewer_id, suggestion_type, target_key, feedback):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recommendation_feedback
                    (viewer_id, suggestion_type, target_key, feedback)
                    VALUES (%s, %s, %s, %s)
                """, (viewer_id, suggestion_type, target_key, feedback))
                cur.execute("""
                    UPDATE recommendations
                    SET status = %s, updated_at = NOW()
                    WHERE viewer_id = %s
                      AND suggestion_type = %s
                      AND target_key = %s
                """, (
                    "accepted" if feedback == "interested" else "dismissed",
                    viewer_id, suggestion_type, target_key
                ))
            conn.commit()

    def get_preferences(self, viewer_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT viewer_id, preferred_genres, preferred_hashtags,
                           recommendation_mode, updated_at
                    FROM user_preferences
                    WHERE viewer_id = %s
                """, (viewer_id,))
                row = cur.fetchone()
                if row:
                    return row
                return {
                    "viewer_id": viewer_id,
                    "preferred_genres": [],
                    "preferred_hashtags": [],
                    "recommendation_mode": "balanced",
                    "updated_at": None,
                }

    def save_preferences(self, viewer_id, preferred_genres, preferred_hashtags, recommendation_mode):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_preferences
                    (viewer_id, preferred_genres, preferred_hashtags, recommendation_mode)
                    VALUES (%s, %s::jsonb, %s::jsonb, %s)
                    ON CONFLICT(viewer_id)
                    DO UPDATE SET
                        preferred_genres = EXCLUDED.preferred_genres,
                        preferred_hashtags = EXCLUDED.preferred_hashtags,
                        recommendation_mode = EXCLUDED.recommendation_mode,
                        updated_at = NOW()
                    RETURNING viewer_id, preferred_genres, preferred_hashtags,
                              recommendation_mode, updated_at
                """, (
                    viewer_id,
                    json.dumps(preferred_genres or []),
                    json.dumps(preferred_hashtags or []),
                    recommendation_mode or "balanced",
                ))
                row = cur.fetchone()
            conn.commit()
            return row

    def table_preview(self, table_name, limit=50):
        allowed = {
            "recommendations",
            "query_history",
            "saved_queries",
            "recommendation_feedback",
            "user_preferences",
            "direct_messages",
            "stories",
            "search_history",
            "app_events",
        }
        if table_name not in allowed:
            raise ValueError("Unknown PostgreSQL table.")
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT * FROM {} ORDER BY 1 DESC LIMIT %s").format(sql.Identifier(table_name)),
                    (int(limit),)
                )
                return cur.fetchall()


    def send_message(self, sender_id, receiver_id, body):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO direct_messages(sender_id, receiver_id, body)
                    VALUES (%s, %s, %s)
                    RETURNING id, sender_id, receiver_id, body, sent_at, read_at
                """, (sender_id, receiver_id, body))
                row = cur.fetchone()
            conn.commit()
            return row

    def messages_between(self, user_a, user_b, limit=100):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, sender_id, receiver_id, body, sent_at, read_at
                    FROM direct_messages
                    WHERE (sender_id = %s AND receiver_id = %s)
                       OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY sent_at ASC
                    LIMIT %s
                """, (user_a, user_b, user_b, user_a, int(limit)))
                rows = cur.fetchall()
                cur.execute("""
                    UPDATE direct_messages
                    SET read_at = COALESCE(read_at, NOW())
                    WHERE sender_id = %s AND receiver_id = %s AND read_at IS NULL
                """, (user_b, user_a))
            conn.commit()
            return rows

    def conversation_summaries(self, viewer_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH peers AS (
                        SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END AS peer_id,
                               id, body, sent_at, sender_id, receiver_id, read_at
                        FROM direct_messages
                        WHERE sender_id = %s OR receiver_id = %s
                    ),
                    latest AS (
                        SELECT DISTINCT ON (peer_id)
                               peer_id, body, sent_at
                        FROM peers
                        ORDER BY peer_id, sent_at DESC
                    ),
                    unread AS (
                        SELECT sender_id AS peer_id, COUNT(*) AS unread_count
                        FROM direct_messages
                        WHERE receiver_id = %s AND read_at IS NULL
                        GROUP BY sender_id
                    )
                    SELECT l.peer_id, l.body AS last_message, l.sent_at,
                           COALESCE(u.unread_count, 0) AS unread_count
                    FROM latest l
                    LEFT JOIN unread u USING(peer_id)
                    ORDER BY l.sent_at DESC
                """, (viewer_id, viewer_id, viewer_id, viewer_id))
                return cur.fetchall()

    def create_story(self, user_id, caption=None, media_url=None):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO stories(user_id, caption, media_url)
                    VALUES (%s, %s, %s)
                    RETURNING id, user_id, caption, media_url, created_at, expires_at
                """, (user_id, caption, media_url))
                row = cur.fetchone()
            conn.commit()
            return row

    def active_stories(self):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, user_id, caption, media_url, created_at, expires_at
                    FROM stories
                    WHERE expires_at > NOW()
                    ORDER BY created_at DESC
                """)
                return cur.fetchall()

    def log_search(self, viewer_id, search_text):
        search_text = (search_text or "").strip()
        if not search_text:
            return
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO search_history(viewer_id, search_text)
                    VALUES (%s, %s)
                """, (viewer_id, search_text))
            conn.commit()

    def recent_searches(self, viewer_id, limit=10):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT search_text, MAX(searched_at) AS searched_at, COUNT(*) AS times
                    FROM search_history
                    WHERE viewer_id = %s
                    GROUP BY search_text
                    ORDER BY MAX(searched_at) DESC
                    LIMIT %s
                """, (viewer_id, int(limit)))
                return cur.fetchall()

    def log_event(self, viewer_id, event_type, target_type=None, target_key=None, metadata=None):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO app_events(viewer_id, event_type, target_type, target_key, metadata)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                """, (
                    viewer_id, event_type, target_type, target_key,
                    json.dumps(metadata or {})
                ))
            conn.commit()

    def recent_events(self, viewer_id, limit=30):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, viewer_id, event_type, target_type, target_key, metadata, created_at
                    FROM app_events
                    WHERE viewer_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (viewer_id, int(limit)))
                return cur.fetchall()

    def set_recommendation_status(self, viewer_id, suggestion_type, target_key, status):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE recommendations
                    SET status = %s, updated_at = NOW()
                    WHERE viewer_id = %s AND suggestion_type = %s AND target_key = %s
                """, (status, viewer_id, suggestion_type, target_key))
            conn.commit()
