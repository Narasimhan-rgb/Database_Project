import os
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


class PostgresDB:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "127.0.0.1"))
        self.port = int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432")))
        self.database = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "engage_meta"))
        self.user = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres"))
        self.password = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", ""))

    def conninfo(self):
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
        }

    @contextmanager
    def connection(self):
        with psycopg.connect(**self.conninfo(), row_factory=dict_row) as conn:
            yield conn

    def verify(self):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database() AS database, current_user AS db_user")
                return cur.fetchone()

    def query(self, statement, params=None):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(statement, params or ())
                rows = cur.fetchall() if cur.description else []
            return rows

    def execute(self, statement, params=None, returning=False):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(statement, params or ())
                rows = cur.fetchall() if returning and cur.description else []
            conn.commit()
            return rows

    def executescript(self, sql_text):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text)
            conn.commit()


def json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def json_rows(rows):
    out = []
    for row in rows:
        out.append({k: json_value(v) for k, v in dict(row).items()})
    return out
