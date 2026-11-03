from pathlib import Path
from db import PostgresDB


def main():
    db = PostgresDB()
    db.verify()
    schema = Path(__file__).resolve().parents[1] / "postgres_schema.sql"
    db.executescript(schema.read_text(encoding="utf-8"))
    print("ENGAGE PostgreSQL Query Lab schema is ready.")
    print("Open: http://127.0.0.1:5000/query-lab")


if __name__ == "__main__":
    main()
