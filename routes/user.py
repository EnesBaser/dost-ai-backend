# routes/user.py
import json
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from auth import require_auth
from database import get_db, release_db
from config import TIER_LIMITS, ADMIN_GOOGLE_IDS
from services.learning import get_emotion_history

user_bp = Blueprint('user', __name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProfileSchema(Schema):
    name      = fields.Str(validate=validate.Length(max=100))
    nickname  = fields.Str(validate=validate.Length(max=100))
    interests = fields.List(fields.Str(validate=validate.Length(max=50)))
    location  = fields.Str(validate=validate.Length(max=100))
    language  = fields.Str(validate=validate.Length(equal=2))


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_user_profile(user_id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT up.*, u.name, u.nickname
            FROM user_profiles up
            JOIN users u ON u.id = up.user_id
            WHERE up.user_id = %s
        """, (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        return dict(profile) if profile else None
    finally:
        release_db(conn)


def save_or_update_profile(user_id, profile_data):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        if 'name' in profile_data:
            cursor.execute(
                "UPDATE users SET name = %s WHERE id = %s",
                (profile_data['name'], user_id)
            )
        if 'nickname' in profile_data:
            cursor.execute(
                "UPDATE users SET nickname = %s WHERE id = %s",
                (profile_data.get('nickname'), user_id)
            )
        cursor.execute("""
            UPDATE user_profiles
            SET interests = %s, location = %s, language = %s, updated_at = NOW()
            WHERE user_id = %s
        """, (
            json.dumps(profile_data.get('interests', [])),
            profile_data.get('location'),
            profile_data.get('language', 'tr'),
            user_id,
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        return False
    finally:
        release_db(conn)


def check_usage_limit(user_id, tier='free'):
    from services.learning import get_turkey_time
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_turkey_time().date()
        cursor.execute("""
            SELECT message_count FROM usage_stats
            WHERE user_id = %s AND date = %s
        """, (user_id, today))
        stats   = cursor.fetchone()
        current = stats['message_count'] if stats else 0
        limit   = TIER_LIMITS[tier]['daily_messages']
        cursor.close()
        return {
            'allowed':   current < limit,
            'current':   current,
            'limit':     limit,
            'remaining': max(0, limit - current),
        }
    finally:
        release_db(conn)


def check_daily_cost_limit(user_id, tier='free'):
    from services.learning import get_turkey_time
    from services.ai_service import calculate_cost
    from config import MAX_DAILY_COST_PER_USER
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_turkey_time().date()
        cursor.execute("""
            SELECT COALESCE(SUM(token_count), 0) AS total_tokens
            FROM messages WHERE user_id = %s AND DATE(created_at) = %s
        """, (user_id, today))
        result       = cursor.fetchone()
        total_tokens = result['total_tokens'] if result else 0
        cost         = calculate_cost(total_tokens)
        max_cost     = MAX_DAILY_COST_PER_USER.get(tier, 0.10)
        cursor.close()
        return {
            'allowed':        cost < max_cost,
            'current_cost':   cost,
            'max_cost':       max_cost,
            'remaining_cost': max(0, max_cost - cost),
        }
    finally:
        release_db(conn)


def increment_usage(user_id, token_count=0):
    from services.learning import get_turkey_time
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_turkey_time().date()
        cursor.execute("""
            INSERT INTO usage_stats (user_id, date, message_count, token_count)
            VALUES (%s, %s, 1, %s)
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                message_count = usage_stats.message_count + 1,
                token_count   = usage_stats.token_count + %s,
                updated_at    = NOW()
        """, (user_id, today, token_count, token_count))
        conn.commit()
        cursor.close()
    except Exception as e:
        if conn:
            conn.rollback()
    finally:
        release_db(conn)


def save_message(user_id, role, content, token_count=0, emotion=None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (user_id, role, content, token_count, emotion)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (user_id, role, content, token_count, emotion))
        message_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return message_id
    except Exception as e:
        if conn:
            conn.rollback()
        return None
    finally:
        release_db(conn)


def get_message_count(user_id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE user_id = %s", (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result['count'] if result else 0
    finally:
        release_db(conn)


# ── Routes ────────────────────────────────────────────────────────────────────

@user_bp.route('/user/profile', methods=['GET', 'POST'])
@require_auth
def user_profile():
    user = request.user
    if request.method == 'GET':
        profile = get_user_profile(user['id'])
        return jsonify({'profile': profile})

    try:
        schema = ProfileSchema()
        data   = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid input', 'details': err.messages}), 400

    success = save_or_update_profile(user['id'], data)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Profile update failed'}), 500

@user_bp.route('/api/my-facts/delete', methods=['POST'])
@require_auth
def delete_facts():
    """Seçili fact'leri veya tümünü sil."""
    conn = None
    try:
        user      = request.user
        data      = request.get_json()
        delete_all = data.get('delete_all', False)
        fact_keys  = data.get('fact_keys', [])  # [{"category": "health", "key": "kronik kalp"}]
        device_id  = user.get('device_id') or str(user['id'])

        conn   = get_db()
        cursor = conn.cursor()

        if delete_all:
            cursor.execute(
                "DELETE FROM user_facts WHERE device_id = %s",
                (str(device_id),)
            )
        elif fact_keys:
            for item in fact_keys:
                cursor.execute("""
                    DELETE FROM user_facts
                    WHERE device_id = %s
                      AND category = %s
                      AND fact_key = %s
                """, (str(device_id), item['category'], item['key']))

        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'deleted': len(fact_keys) if not delete_all else 'all'})

    except Exception as e:
        print(f"delete_facts error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@user_bp.route('/usage', methods=['GET'])
@require_auth
def usage_stats():
    user           = request.user
    is_admin       = user.get('google_id') in ADMIN_GOOGLE_IDS
    effective_tier = 'pro' if is_admin else user['subscription_tier']
    usage          = check_usage_limit(user['id'], effective_tier)
    cost           = check_daily_cost_limit(user['id'], effective_tier)
    return jsonify({
        'tier':        effective_tier,
        'daily_limit': usage['limit'],
        'used_today':  usage['current'],
        'remaining':   usage['remaining'],
        'cost_today':  round(cost['current_cost'], 4),
        'cost_limit':  cost['max_cost'],
    })

@user_bp.route('/admin')
def admin_panel():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Admin panel not found", 404

@user_bp.route('/api/account/delete', methods=['POST'])
@require_auth
def delete_account():
    """Kullanıcının tüm verilerini ve hesabını sil."""
    conn = None
    try:
        user      = request.user
        device_id = user.get('device_id') or str(user['id'])

        conn   = get_db()
        cursor = conn.cursor()

        # Tüm verileri sil
        cursor.execute("DELETE FROM user_facts WHERE device_id = %s", (device_id,))
        cursor.execute("DELETE FROM user_emotion_history WHERE device_id = %s", (device_id,))
        cursor.execute("DELETE FROM messages WHERE user_id = %s", (str(user['id']),))
        cursor.execute("DELETE FROM usage_stats WHERE user_id = %s", (str(user['id']),))
        cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (str(user['id']),))
        cursor.execute(
            "UPDATE users SET deleted_at = NOW(), fcm_token = NULL WHERE id = %s",
            (str(user['id']),)
        )
        conn.commit()
        cursor.close()
        print(f"✅ Hesap silindi: {user['id']}", flush=True)
        return jsonify({'success': True})

    except Exception as e:
        print(f"delete_account error: {e}", flush=True)
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@user_bp.route('/api/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    conn = None
    try:
        user = request.user
        data = request.get_json()
        tier = data.get('tier', 'premium')
        if tier not in ['free', 'premium', 'pro']:
            return jsonify({'error': 'Invalid tier'}), 400
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET subscription_tier = %s WHERE id = %s',
            (tier, user['id'])
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'tier': tier})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@user_bp.route('/api/my-facts', methods=['GET'])
@require_auth
def my_facts():
    user    = request.user
    conn    = None
    try:
        conn      = get_db()
        cursor    = conn.cursor()
        device_id = user.get('device_id') or str(user['id'])
        cursor.execute("""
            SELECT
                category, fact_key, fact_value, confidence,
                COALESCE(importance, 0.5)  AS importance,
                COALESCE(frequency, 1)     AS frequency,
                COALESCE(last_mentioned, updated_at::date) AS last_mentioned,
                updated_at
            FROM user_facts
            WHERE device_id = %s AND confidence > 0.2
            ORDER BY (COALESCE(importance, 0.5) * confidence * LN(COALESCE(frequency, 1) + 1)) DESC
            LIMIT 50
        """, (str(device_id),))
        rows  = cursor.fetchall()
        cursor.close()
        facts = []
        for row in rows:
            try:
                facts.append({
                    'category':     str(row['category']),
                    'key':          str(row['fact_key']),
                    'value':        str(row['fact_value']),
                    'confidence':   round(float(row['confidence']), 2),
                    'importance':   round(float(row['importance']), 2),
                    'frequency':    int(row['frequency']),
                    'last_mentioned': str(row['last_mentioned']) if row['last_mentioned'] else None,
                })
            except Exception:
                pass
        return jsonify({'facts': facts, 'count': len(facts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@user_bp.route('/api/my-emotions', methods=['GET'])
@require_auth
def my_emotions():
    user      = request.user
    device_id = user.get('device_id') or str(user['id'])
    days      = int(request.args.get('days', 30))
    history   = get_emotion_history(device_id, days=days)
    return jsonify({'emotions': history, 'count': len(history)})
