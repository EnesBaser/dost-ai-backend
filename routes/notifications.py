# routes/notifications.py
from flask import Blueprint, request, jsonify
from auth import require_auth
from config import ADMIN_GOOGLE_IDS
from database import get_db, release_db
from services.scheduler import (
    send_push_notification, generate_personalized_notification,
    run_notification_job, scheduler,
)
from services.ai_service import get_client
from services.learning import get_turkey_time

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/api/register-token', methods=['POST'])
@require_auth
def register_fcm_token():
    conn = None
    try:
        user                 = request.user
        data                 = request.get_json()
        fcm_token            = data.get('fcm_token', '').strip()
        notifications_enabled = data.get('notifications_enabled', True)

        if not fcm_token:
            return jsonify({'error': 'fcm_token gerekli'}), 400

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET fcm_token = %s, notifications_enabled = %s, updated_at = NOW()
            WHERE id = %s
        """, (fcm_token, notifications_enabled, user['id']))
        conn.commit()
        cursor.close()
        print(f"✅ FCM token kaydedildi: user={user['id']}", flush=True)
        return jsonify({'success': True})

    except Exception as e:
        print(f"register_fcm_token error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@notifications_bp.route('/api/notifications/toggle', methods=['POST'])
@require_auth
def toggle_notifications():
    conn = None
    try:
        user    = request.user
        data    = request.get_json()
        enabled = data.get('enabled', True)

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET notifications_enabled = %s WHERE id = %s",
            (enabled, user['id'])
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'notifications_enabled': enabled})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@notifications_bp.route('/api/notifications/test', methods=['POST'])
@require_auth
def test_notification():
    user     = request.user
    is_admin = user.get('google_id') in ADMIN_GOOGLE_IDS
    if not is_admin:
        return jsonify({'error': 'Admin only'}), 403

    conn = None
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT fcm_token FROM users WHERE id = %s", (user['id'],))
        row = cursor.fetchone()
        cursor.close()

        if not row or not row['fcm_token']:
            return jsonify({'error': 'FCM token bulunamadı. Önce uygulamayı aç.'}), 400

        client       = get_client()
        title, body  = generate_personalized_notification(dict(user), client)
        sent         = send_push_notification(row['fcm_token'], title, body, {'type': 'test'})
        return jsonify({'success': sent, 'title': title, 'body': body})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


@notifications_bp.route('/api/scheduler/status', methods=['GET'])
@require_auth
def scheduler_status():
    user     = request.user
    is_admin = user.get('google_id') in ADMIN_GOOGLE_IDS
    if not is_admin:
        return jsonify({'error': 'Admin only'}), 403

    jobs = [
        {
            'id':       job.id,
            'name':     job.name,
            'next_run': str(job.next_run_time) if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
    return jsonify({
        'running':     scheduler.running,
        'jobs':        jobs,
        'turkey_time': get_turkey_time().strftime('%d.%m.%Y %H:%M'),
    })


@notifications_bp.route('/api/notifications/trigger', methods=['POST'])
@require_auth
def trigger_notification_job():
    """Admin: Manuel job tetikle — test için."""
    user     = request.user
    is_admin = user.get('google_id') in ADMIN_GOOGLE_IDS
    if not is_admin:
        return jsonify({'error': 'Admin only'}), 403

    import threading
    t = threading.Thread(
        target=run_notification_job,
        args=("manual",),
        daemon=True,
    )
    t.start()
    return jsonify({'success': True, 'message': 'Job başlatıldı (arka planda çalışıyor)'})
