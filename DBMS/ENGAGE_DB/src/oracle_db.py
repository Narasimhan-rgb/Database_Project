import os
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

try:
    import oracledb
except ImportError:
    oracledb = None


class OracleDB:
    def __init__(self):
        self.user = os.getenv("ORACLE_USER", "BCE5028")
        self.password = os.getenv("ORACLE_PASSWORD", "")
        self.dsn = os.getenv("ORACLE_DSN", "localhost/FREEPDB1")

    def available(self):
        return oracledb is not None and bool(self.password)

    @contextmanager
    def connection(self):
        if oracledb is None:
            raise RuntimeError("python-oracledb is not installed. Run: python -m pip install oracledb")
        with oracledb.connect(user=self.user, password=self.password, dsn=self.dsn) as conn:
            yield conn

    def verify(self):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT SYS_CONTEXT('USERENV','DB_NAME'), USER FROM dual")
                row = cur.fetchone()
                return {"database": row[0], "db_user": row[1], "dsn": self.dsn}

    def query(self, statement, params=None):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(statement, params or {})
                cols = [d[0].lower() for d in cur.description] if cur.description else []
                rows = cur.fetchall() if cur.description else []
        return [dict(zip(cols, [oracle_value(v) for v in row])) for row in rows]


def oracle_value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat(sep=" ") if isinstance(v, datetime) else v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    # python-oracledb returns CLOB/BLOB values as LOB objects.
    # Read them while the Oracle connection is still open.
    if hasattr(v, "read") and callable(v.read):
        try:
            return v.read()
        except Exception:
            return str(v)
    return v
