import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from datetime import datetime
from config import DATABASE_URL

# Thread-safe connection pool
try:
    db_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, dsn=DATABASE_URL)
except Exception as e:
    print(f"Baza ulanishida xato: {e}")
    db_pool = None

@contextmanager
def get_db():
    if not db_pool:
        yield None
        return
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

def init_db():
    if not db_pool: return
    with get_db() as conn:
        with conn.cursor() as cursor:
            # Foydalanuvchilar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Esselar tarixi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS essays (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    topic TEXT,
                    criteria TEXT,
                    essay_text TEXT,
                    result_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()

def save_user(user_id: int, first_name: str, username: str):
    if not db_pool: return
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, first_name, username) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, first_name, username))
        conn.commit()

def save_essay(user_id: int, topic: str, criteria: str, essay_text: str, result_text: str):
    if not db_pool: return
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO essays (user_id, topic, criteria, essay_text, result_text)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, topic, criteria, essay_text, result_text))
        conn.commit()

def get_stats(user_id: int):
    if not db_pool: return 0
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM essays WHERE user_id = %s", (user_id,))
            return cursor.fetchone()[0]

init_db()
