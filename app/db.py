import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from psycopg import Connection, connect
from psycopg.rows import dict_row

load_dotenv()


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jobtrackr")


@contextmanager
def get_conn() -> Connection:
    conn = connect(get_database_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_sql_file(relative_path: str) -> str:
    root = Path(__file__).resolve().parent.parent
    return (root / relative_path).read_text(encoding="utf-8")
