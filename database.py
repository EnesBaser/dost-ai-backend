# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool as psycopg2_pool
from config import DATABASE_URL, DB_MIN_CONN, DB_MAX_CONN

_db_pool = None

def init_db_pool():
    global _db_pool
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found!")
    _db_pool = psycopg2_pool.ThreadedConnectionPool(
        minconn=DB_MIN_CONN,
        maxconn=DB_MAX_CONN,
        dsn=DATABASE_URL,
        connect_timeout=10,
    )
    print("✅ DB connection pool başlatıldı!")

def get_db():
    global _db_pool
    if _db_pool is None:
        init_db_pool()
    conn = _db_pool.getconn()
    conn.cursor_factory = RealDictCursor
    if conn.closed:
        _db_pool.putconn(conn)
        conn = _db_pool.getconn()
        conn.cursor_factory = RealDictCursor
    return conn

def release_db(conn):
    global _db_pool
    if _db_pool and conn:
        try:
            _db_pool.putconn(conn)
        except Exception:
            pass

def run_migrations():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS fcm_token TEXT,
            ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS last_notified_at TIMESTAMP
        """)
        conn.commit()
        cursor.close()
        print("✅ DB migration tamamlandı!")
    except Exception as e:
        print(f"⚠️ Migration warning: {e}", flush=True)
        if conn:
            try: conn.rollback()
            except: pass
    finally:
        release_db(conn)
