# services/scheduler.py
import time
import json
import traceback as tb
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TURKEY_TZ, FIREBASE_CREDENTIALS_JSON

try:
    import firebase_admin
    from firebase_admin import credentials, messaging as fcm_messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ firebase-admin paketi yok")

_firebase_initialized = False
scheduler = BackgroundScheduler(timezone=TURKEY_TZ)


# ── Firebase ──────────────────────────────────────────────────────────────────

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized or not FIREBASE_AVAILABLE:
        return _firebase_initialized
    try:
        if not FIREBASE_CREDENTIALS_JSON:
            print("⚠️ FIREBASE_CREDENTIALS_JSON bulunamadı — push notifications devre dışı")
            return False
        creds_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("✅ Firebase Admin SDK başlatıldı!")
        return True
    except Exception as e:
        print(f"❌ Firebase init error: {e}", flush=True)
        return False


def send_push_notification(fcm_token, title, body, data=None):
    if not _firebase_initialized or not fcm_token:
        return False
    try:
        message = fcm_messaging.Message(
            notification=fcm_messaging.Notification(title=title, body=body),
            data=data or {},
            token=fcm_token,
            android=fcm_messaging.AndroidConfig(
                priority='high',
                notification=fcm_messaging.AndroidNotification(
                    color='#9333EA',
                    sound='default',
                    channel_id='dostai_notifications',
                )
            ),
            apns=fcm_messaging.APNSConfig(
                payload=fcm_messaging.APNSPayload(
                    aps=fcm_messaging.Aps(sound='default', badge=1)
                )
            )
        )
        response = fcm_messaging.send(message)
        print(f"✅ FCM gönderildi: {response}", flush=True)
        return True
    except Exception as e:
        err_str = str(e)
        if 'Requested entity was not found' in err_str or 'registration-token-not-registered' in err_str:
            _clear_fcm_token(fcm_token)
        else:
            print(f"❌ FCM error: {e}", flush=True)
        return False


def _clear_fcm_token(fcm_token):
    from database import get_db, release_db
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET fcm_token = NULL WHERE fcm_token = %s", (fcm_token,))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"_clear_fcm_token error: {e}", flush=True)
    finally:
        release_db(conn)


# ── Kullanıcı sorgulama ───────────────────────────────────────────────────────

def get_users_for_notification():
    from database import get_db, release_db
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, device_id, fcm_token, subscription_tier
            FROM users
            WHERE
                fcm_token IS NOT NULL
                AND notifications_enabled = TRUE
                AND deleted_at IS NULL
                AND last_login_at >= NOW() - INTERVAL '7 days'
                AND (
                    last_notified_at IS NULL
                    OR last_notified_at < NOW() - INTERVAL '4 hours'
                )
            ORDER BY last_login_at DESC
            LIMIT 500
        """)
        users = cursor.fetchall()
        cursor.close()
        return [dict(u) for u in users]
    except Exception as e:
        print(f"get_users_for_notification error: {e}", flush=True)
        return []
    finally:
        release_db(conn)


def update_last_notified(user_id):
    from database import get_db, release_db
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_notified_at = NOW() WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"update_last_notified error: {e}", flush=True)
    finally:
        release_db(conn)


# ── Kişiselleştirilmiş bildirim üretimi ──────────────────────────────────────

def generate_personalized_notification(user, client):
    from services.learning import (
        get_learned_facts, get_emotion_history,
        build_emotion_summary,
    )
    from services.router import get_weather_data
    from config import TURKEY_TZ

    user_id   = user['id']
    device_id = user.get('device_id') or str(user_id)

    try:
        turkey_time    = datetime.now(TURKEY_TZ)
        learned_facts  = get_learned_facts(user_id, limit=15)
        emotion_history = get_emotion_history(device_id, days=3)

        location = next(
            (f['value'] for f in learned_facts if f.get('category') == 'location' and f.get('value')),
            None
        )
        interests = [
            f.get('context') or f.get('value')
            for f in learned_facts
            if f.get('category') in ['sports', 'music', 'movies', 'hobbies', 'food']
            and f.get('value')
        ]
        high_imp = [f for f in learned_facts if float(f.get('importance', 0)) >= 0.7][:3]
        facts_summary  = ', '.join([f.get('context') or f.get('value', '') for f in high_imp if f.get('value')])
        emotion_summary = build_emotion_summary(emotion_history)

        weather_info = ""
        if location:
            w = get_weather_data(f"hava {location}", location)
            if w:
                weather_info = w

        hour = turkey_time.hour
        if hour < 12:
            greeting_hint = "sabah mesajı, günaydın ile başla"
        elif hour < 17:
            greeting_hint = "öğle mesajı, iyi günler ile başla"
        else:
            greeting_hint = "akşam mesajı, iyi akşamlar ile başla"

        prompt = f"""Sen DostAI'sin, {user['name']}'in yapay zeka dostu.
Bugün {turkey_time.strftime('%d %B %Y')}, saat {turkey_time.strftime('%H:%M')}.

İlgi alanları: {', '.join(interests[:3]) if interests else 'bilinmiyor'}
Önemli bilgiler: {facts_summary or 'yok'}
Hava: {weather_info or 'bilinmiyor'}
{emotion_summary}

Push notification için ({greeting_hint}):
BASLIK: maks 40 karakter, sıcak ve kişisel
MESAJ: maks 90 karakter, merak uyandıran, samimi

SADECE bu formatta yaz:
BASLIK: ...
MESAJ: ..."""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.9,
        )
        raw   = resp.choices[0].message.content.strip()
        title = f"Merhaba {user['name']}! 👋"
        body  = "Bugün nasılsın? Seninle konuşmak istedim."

        for line in raw.split('\n'):
            if line.startswith('BASLIK:'):
                title = line.replace('BASLIK:', '').strip()
            elif line.startswith('MESAJ:'):
                body = line.replace('MESAJ:', '').strip()
        return title, body

    except Exception as e:
        print(f"generate_personalized_notification error: {e}", flush=True)
        hour = datetime.now(TURKEY_TZ).hour
        if hour < 12:
            return f"Günaydın {user['name']}! ☀️", "Bugün nasıl bir gün geçiriyorsun?"
        elif hour < 17:
            return f"Merhaba {user['name']}! 👋", "Öğleden sonra nasılsın?"
        else:
            return f"İyi akşamlar {user['name']}! 🌙", "Bugün nasıl geçti?"


# ── Job ───────────────────────────────────────────────────────────────────────

def run_notification_job(job_name="scheduled"):
    from services.ai_service import get_client
    from database import get_db, release_db

    turkey_time = datetime.now(TURKEY_TZ)
    print(f"🔔 Notification job başladı ({job_name}): {turkey_time.strftime('%H:%M')}", flush=True)

    client = get_client()
    users  = get_users_for_notification()
    print(f"📱 Bildirim gönderilecek: {len(users)} kullanıcı", flush=True)

    success_count = 0
    fail_count    = 0

    for user in users:
        try:
            title, body = generate_personalized_notification(user, client)
            if not title or not body:
                continue
            sent = send_push_notification(
                fcm_token=user['fcm_token'],
                title=title,
                body=body,
                data={'type': 'proactive', 'screen': 'chat', 'job': job_name}
            )
            if sent:
                update_last_notified(user['id'])
                success_count += 1
            else:
                fail_count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Notification error user {user['id']}: {e}", flush=True)
            fail_count += 1

    print(f"✅ Job bitti: {success_count} başarılı, {fail_count} başarısız", flush=True)


# ── Scheduler başlatma ────────────────────────────────────────────────────────

def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        func=lambda: run_notification_job("morning"),
        trigger=CronTrigger(hour=9, minute=0, timezone=TURKEY_TZ),
        id='morning_notification',
        name='Sabah 09:00 bildirimi',
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        func=lambda: run_notification_job("afternoon"),
        trigger=CronTrigger(hour=13, minute=0, timezone=TURKEY_TZ),
        id='afternoon_notification',
        name='Öğlen 13:00 bildirimi',
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    print("✅ APScheduler başlatıldı! (09:00 + 13:00 TR saati)")
