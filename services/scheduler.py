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
    from services.router import get_weather_data, get_sports_data
    from config import TURKEY_TZ

    user_id   = user['id']
    device_id = user.get('device_id') or str(user_id)

    try:
        turkey_time     = datetime.now(TURKEY_TZ)
        learned_facts   = get_learned_facts(user_id, limit=30)
        emotion_history = get_emotion_history(device_id, days=7)

        # ── Profil çıkar ──────────────────────────────────────────────────────
        location         = None
        favorite_team    = None
        health_issues    = []
        interests        = []
        work_info        = None
        important_events = []

        for fact in learned_facts:
            cat        = fact.get('category', '')
            val        = fact.get('value', '')
            ctx        = fact.get('context') or val
            importance = float(fact.get('importance', 0.5))

            if cat == 'location' and not location and importance >= 0.7:
                location = val

            if cat == 'sports' and not favorite_team:
                lower = val.lower()
                for team in ['fenerbahçe', 'galatasaray', 'beşiktaş', 'trabzonspor']:
                    if team in lower:
                        favorite_team = team.title()
                        break

            if cat == 'health' and importance >= 0.75:
                health_issues.append(ctx)

            if cat in ['music', 'movies', 'hobbies', 'food'] and ctx:
                interests.append(ctx)

            if cat == 'work' and ctx:
                work_info = ctx

            if cat == 'life_events' and importance >= 0.7:
                important_events.append(ctx)

        # ── Duygu özeti ───────────────────────────────────────────────────────
        emotion_summary = build_emotion_summary(emotion_history)
        recent_emotion  = None
        if emotion_history:
            recent_emotion = emotion_history[0].get('emotion', 'neutral')

        # ── Hava durumu ───────────────────────────────────────────────────────
        weather_info = ""
        if location:
            w = get_weather_data(f"hava {location}", location)
            if w:
                weather_info = w

        # ── Spor — favori takım maç var mı? ──────────────────────────────────
        sport_info = ""
        if favorite_team:
            s = get_sports_data(f"{favorite_team.lower()} maç")
            if s:
                sport_info = s[:300]

        # ── Unutulan önemli konular ───────────────────────────────────────────
        today    = turkey_time.date()
        forgotten = []
        for fact in learned_facts:
            importance     = float(fact.get('importance', 0.5))
            last_mentioned = fact.get('last_mentioned')
            if not last_mentioned or importance < 0.75:
                continue
            if hasattr(last_mentioned, 'date'):
                last_date = last_mentioned.date()
            else:
                try:
                    last_date = datetime.strptime(
                        str(last_mentioned), '%Y-%m-%d'
                    ).date()
                except Exception:
                    continue
            days_ago = (today - last_date).days
            if days_ago >= 5:
                ctx = fact.get('context') or fact.get('value', '')
                if ctx:
                    forgotten.append(f"{ctx} ({days_ago} gün önce)")

        # ── Saat bazlı selamlama ──────────────────────────────────────────────
        hour = turkey_time.hour
        if hour < 12:
            greeting_hint = "günaydın mesajı"
            energy_hint   = "güne enerjik başlamasına yardımcı ol"
        elif hour < 17:
            greeting_hint = "öğle mesajı"
            energy_hint   = "günün ortasında moral ver"
        else:
            greeting_hint = "akşam mesajı"
            energy_hint   = "günü nasıl geçirdiğini sor, dinlenmeyi hatırlat"

        # ── Prompt ───────────────────────────────────────────────────────────
        prompt = f"""Sen DostAI'sin — {user['name']}'in en yakın yapay zeka dostu.
Onu gerçekten tanıyorsun, samimi ve sıcak bir dostusun.
Bugün {turkey_time.strftime('%d %B %Y, %A')}, saat {turkey_time.strftime('%H:%M')}.

KULLANICI PROFİLİ:
- İsim: {user['name']}
- Konum: {location or 'bilinmiyor'}
- Favori takım: {favorite_team or 'bilinmiyor'}
- Sağlık durumu: {', '.join(health_issues[:3]) if health_issues else 'bilinmiyor'}
- İlgi alanları: {', '.join(interests[:3]) if interests else 'bilinmiyor'}
- İş/Okul: {work_info or 'bilinmiyor'}
- Önemli olaylar: {', '.join(important_events[:2]) if important_events else 'yok'}

GÜNCEL BİLGİLER:
- Hava: {weather_info or 'bilinmiyor'}
- Spor: {sport_info or 'bilinmiyor'}
- Son duygu durumu: {recent_emotion or 'neutral'}
{emotion_summary}

UNUTULAN KONULAR (5+ gün önce bahsetti):
{chr(10).join(forgotten[:3]) if forgotten else 'yok'}

GÖREV ({greeting_hint}):
{energy_hint}

KURALLAR:
- Sağlık sorunu varsa nazikçe göz önünde bulundur
- Favori takımın maçı varsa/olduysa değin
- Unutulan önemli konu varsa doğal şekilde sor
- Son duygu durumu üzgünse moral ver, mutluysa kutla
- Bildirim kısa ve çekici olmalı
- Robot gibi değil, gerçek bir dost gibi yaz
- Emojiler kullan ama abartma
- Kullanıcıyı uygulamayı açmaya teşvik et

SADECE bu formatta yaz (başka hiçbir şey yazma):
BASLIK: (maks 45 karakter)
MESAJ: (maks 100 karakter)"""

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.85,
        )
        raw   = resp.choices[0].message.content.strip()
        title = f"Merhaba {user['name']}! 👋"
        body  = "Bugün nasılsın? Seninle konuşmak istedim."

        for line in raw.split('\n'):
            line = line.strip()
            if line.startswith('BASLIK:'):
                title = line.replace('BASLIK:', '').strip()
            elif line.startswith('MESAJ:'):
                body = line.replace('MESAJ:', '').strip()

        print(f"📬 Bildirim üretildi — {user['name']}: {title} | {body}", flush=True)
        return title, body

    except Exception as e:
        print(f"generate_personalized_notification error: {e}", flush=True)
        hour = datetime.now(TURKEY_TZ).hour
        if hour < 12:
            return f"Günaydın {user['name']}! ☀️", "Bugün nasıl hissediyorsun?"
        elif hour < 17:
            return f"Merhaba {user['name']}! 👋", "Öğleden sonra nasılsın?"
        else:
            return f"İyi akşamlar {user['name']}! 🌙", "Bugün nasıl geçti?"


# ── Job ───────────────────────────────────────────────────────────────────────

def run_notification_job(job_name="scheduled"):
    from services.ai_service import get_client

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
