import os
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv

from db import PostgresDB

load_dotenv()


def ensure_database(db):
    try:
        return db.verify()
    except Exception as first_error:
        admin_db = os.getenv("POSTGRES_ADMIN_DB", "postgres")
        try:
            with psycopg.connect(
                host=db.host,
                port=db.port,
                dbname=admin_db,
                user=db.user,
                password=db.password,
                autocommit=True,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db.database,))
                    if cur.fetchone() is None:
                        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db.database)))
                        print(f"Created PostgreSQL database: {db.database}")
            return db.verify()
        except Exception:
            raise first_error


def main():
    db = PostgresDB()
    try:
        status = ensure_database(db)
        schema = Path(__file__).with_name("postgres_schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        print("ENGAGE V8 PostgreSQL schema is ready.")
        print(f"Database: {status['database']} @ {db.host}:{db.port}")
        print("Core PPT ER tables + student opportunity layer + analytics views created.")
    except Exception as exc:
        print("PostgreSQL setup could not complete.")
        print(exc)
        print("Check that PostgreSQL is running and that POSTGRES_USER / POSTGRES_PASSWORD in .env are correct.")
        raise


if __name__ == "__main__":
    main()
