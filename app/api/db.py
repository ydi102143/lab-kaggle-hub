import os
import psycopg2
from contextlib import contextmanager

def get_db_url():
    return os.getenv("DATABASE_URL", "postgresql://app:app@localhost:5432/app")

@contextmanager
def get_conn():
    conn = psycopg2.connect(get_db_url())
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
