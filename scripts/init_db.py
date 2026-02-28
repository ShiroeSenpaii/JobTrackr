from pathlib import Path

from psycopg import connect

from app.db import get_database_url


def main() -> None:
    schema_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    with connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print("Database schema initialized.")


if __name__ == "__main__":
    main()
