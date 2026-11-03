from pathlib import Path
from oracle_db import OracleDB


def main():
    db = OracleDB()
    status = db.verify()
    sql_text = Path(__file__).with_name("oracle_schema.sql").read_text(encoding="utf-8")
    statements = [x.strip() for x in sql_text.split(";") if x.strip()]
    with db.connection() as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                try:
                    cur.execute(stmt)
                except Exception as exc:
                    # ORA-00955 = object already exists; safe for reruns.
                    if "ORA-00955" not in str(exc):
                        raise
        conn.commit()
    print(f"Oracle ENGAGE mirror schema ready: {status['database']} as {status['db_user']} @ {status['dsn']}")


if __name__ == "__main__":
    main()
