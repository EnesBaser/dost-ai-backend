# auth.py
import traceback as tb
from functools import wraps
from urllib.parse import unquote
from flask import request, jsonify
import sentry_sdk
from config import ADMIN_GOOGLE_IDS, SENTRY_DSN
from database import get_db, release_db


def get_or_create_user(device_id, name=None, google_id=None, email=None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if google_id:
            cursor.execute(
                "SELECT * FROM users WHERE google_id = %s AND deleted_at IS NULL", (google_id,)
            )
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    "UPDATE users SET last_login_at = NOW(), device_id = %s, email = %s WHERE id = %s",
                    (device_id, email, user['id'])
                )
                conn.commit()
                cursor.close()
                return dict(user)

        cursor.execute(
            "SELECT * FROM users WHERE device_id = %s AND deleted_at IS NULL", (device_id,)
        )
        user = cursor.fetchone()
        if user:
            if google_id and not user.get('google_id'):
                cursor.execute(
                    "UPDATE users SET last_login_at = NOW(), google_id = %s, email = %s WHERE id = %s",
                    (google_id, email, user['id'])
                )
            else:
                cursor.execute(
                    "UPDATE users SET last_login_at = NOW(), email = COALESCE(%s, email) WHERE id = %s",
                    (email, user['id'])
                )
            conn.commit()
            cursor.close()
            return dict(user)

        user_name = name or "Arkadaşım"
        cursor.execute("""
            INSERT INTO users (device_id, google_id, email, name, subscription_tier, subscription_status)
            VALUES (%s, %s, %s, %s, 'free', 'active') RETURNING *
        """, (device_id, google_id, email, user_name))
        new_user = cursor.fetchone()
        conn.commit()
        cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (new_user['id'],))
        conn.commit()
        cursor.close()
        print(f"✅ Yeni kullanıcı: {device_id} | google: {google_id}")
        return dict(new_user)

    except Exception as e:
        if conn:
            try: conn.rollback()
            except: pass
        raise
    finally:
        release_db(conn)


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        json_body = request.get_json(silent=True)
        device_id = request.headers.get('X-Device-ID') or (json_body.get('device_id') if json_body else None)
        google_id  = request.headers.get('X-Google-ID')
        email      = request.headers.get('X-Google-Email')

        # Türkçe karakterleri decode et
        raw_name = request.headers.get('X-Google-Name')
        try:
            name = unquote(raw_name) if raw_name else None
        except Exception:
            name = raw_name

        if not device_id and not google_id:
            return jsonify({'error': 'Auth required'}), 401

        identifier = device_id or google_id
        try:
            user = get_or_create_user(identifier, name=name, google_id=google_id, email=email)
            request.user = user
            if SENTRY_DSN:
                sentry_sdk.set_user({"id": str(user['id']), "tier": user['subscription_tier']})
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Auth error: {e}", flush=True)
            print(tb.format_exc(), flush=True)
            return jsonify({'error': f'Auth error: {str(e)}'}), 500
    return decorated_function
