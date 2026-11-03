from datetime import datetime, timezone
from decimal import Decimal

from db import PostgresDB
from oracle_db import OracleDB

PG = PostgresDB()
ORA = OracleDB()

# Parent tables come before child tables.
TABLES = [
    ("engage_user", [
        "user_id","user_name","full_name","handle","email",
        "follower_count","following_count","bio","city",
        "avatar_color","avatar_url","created_at"
    ]),
    ("post", [
        "post_id","user_id","caption","content_type","genre","post_date",
        "language","location","created_at","visual_seed","media_url"
    ]),
    ("hashtag", [
        "hashtag_id","hashtag_name","purpose"
    ]),
    ("learning_resource", [
        "resource_id","provider_name","title","exam_goal","topic",
        "resource_type","delivery_mode","monthly_cost","quality_score",
        "scholarship_available","verified","description","resource_url","created_at"
    ]),
    ("student_profile", [
        "user_id","academic_stage","exam_goal","max_monthly_budget",
        "budget_preference","preferred_mode","language_preference","city","updated_at"
    ]),
    ("following", [
        "follower_user_id","following_user_id","followed_at"
    ]),
    ("likes", [
        "post_id","user_id","liked_at"
    ]),
    ("saved", [
        "post_id","user_id","saved_at"
    ]),
    ("reposts", [
        "repost_id","post_id","user_id","text_highlight","reposted_at"
    ]),
    ("post_hashtag", [
        "post_id","hashtag_id"
    ]),
    ("reach", [
        "reach_id","post_id","impressions","unique_reach"
    ]),
    ("post_learning_signal", [
        "post_id","exam_goal","topic","signal_type"
    ]),
]

COMMENT_COLS = [
    "comment_id","comment_text","sentiment","user_id","post_id",
    "towhom","numberofreplies","positive_replies","negative_replies",
    "parent_comment_id","created_at"
]

AFTER_COMMENT_TABLES = [
    ("comment_likes", ["user_id","comment_id","liked_at"]),
    ("comment_hashtag", ["comment_id","hashtag_id"]),
]


def normalize_value(value):
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, Decimal):
        return value
    return value


def fetch_rows(table, cols):
    return PG.query(f"SELECT {','.join(cols)} FROM {table}")


def insert_rows(cur, table, cols, rows):
    if not rows:
        print(f"[SYNC] {table}: 0 rows")
        return 0

    binds = ",".join(f":{i+1}" for i in range(len(cols)))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({binds})"

    payload = [
        tuple(normalize_value(row[c]) for c in cols)
        for row in rows
    ]

    try:
        cur.executemany(sql, payload)
    except Exception as exc:
        raise RuntimeError(
            f"Oracle sync failed while inserting table '{table}'. "
            f"Rows attempted: {len(payload)}. Original error: {exc}"
        ) from exc

    print(f"[SYNC] {table}: {len(payload)} rows")
    return len(payload)


def clear_oracle(cur):
    try:
        cur.execute("UPDATE comments SET parent_comment_id = NULL")
    except Exception:
        pass

    delete_order = [
        "comment_hashtag",
        "comment_likes",
        "comments",
        "post_hashtag",
        "reposts",
        "saved",
        "likes",
        "reach",
        "following",
        "post_learning_signal",
        "student_profile",
        "learning_resource",
        "hashtag",
        "post",
        "engage_user",
    ]

    for table in delete_order:
        try:
            cur.execute(f"DELETE FROM {table}")
            print(f"[CLEAR] {table}")
        except Exception as exc:
            if "ORA-00942" in str(exc):
                print(f"[SKIP] {table}: not present")
                continue
            raise RuntimeError(
                f"Could not clear Oracle table '{table}': {exc}"
            ) from exc


def sync_comments(cur):
    rows = fetch_rows("comments", COMMENT_COLS)
    if not rows:
        print("[SYNC] comments: 0 rows")
        return

    base_cols = [
        "comment_id","comment_text","sentiment","user_id","post_id",
        "towhom","numberofreplies","positive_replies","negative_replies",
        "created_at"
    ]

    base_rows = []
    parent_links = []

    for row in rows:
        base_rows.append({key: row[key] for key in base_cols})
        if row["parent_comment_id"]:
            parent_links.append((row["parent_comment_id"], row["comment_id"]))

    insert_rows(cur, "comments", base_cols, base_rows)

    for parent_id, comment_id in parent_links:
        cur.execute(
            "UPDATE comments SET parent_comment_id = :1 WHERE comment_id = :2",
            (parent_id, comment_id)
        )

    print(f"[SYNC] comments parent links: {len(parent_links)}")


def main():
    PG.verify()
    status = ORA.verify()

    print(
        f"Oracle connected: {status.get('database')} as "
        f"{status.get('db_user')} @ {status.get('dsn')}"
    )

    with ORA.connection() as oc:
        with oc.cursor() as cur:
            print("\n--- Clearing old Oracle mirror data ---")
            clear_oracle(cur)

            print("\n--- Copying PostgreSQL data to Oracle ---")
            for table, cols in TABLES:
                rows = fetch_rows(table, cols)
                insert_rows(cur, table, cols, rows)

            sync_comments(cur)

            for table, cols in AFTER_COMMENT_TABLES:
                rows = fetch_rows(table, cols)
                insert_rows(cur, table, cols, rows)

        oc.commit()

    print("\nPostgreSQL -> Oracle mirror sync completed successfully.")


if __name__ == "__main__":
    main()
