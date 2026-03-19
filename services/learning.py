# services/learning.py
import json
import threading
import traceback as tb
from datetime import datetime
from config import TURKEY_TZ, MODEL_EXTRACTION
from database import get_db, release_db

# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────

def get_turkey_time():
    from datetime import datetime
    return datetime.now(TURKEY_TZ)


def get_learned_facts(user_id, limit=20):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM users WHERE id = %s", (str(user_id),))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return []
        device_id = row['device_id']
        cursor.execute("""
            SELECT
                category,
                fact_key   AS value,
                fact_value AS context,
                confidence,
                COALESCE(importance, 0.5)    AS importance,
                COALESCE(frequency, 1)       AS frequency,
                COALESCE(last_mentioned, updated_at::date) AS last_mentioned,
                source,
                updated_at
            FROM user_facts
            WHERE device_id = %s AND confidence > 0.2
            ORDER BY
                (COALESCE(importance, 0.5) * confidence * LN(COALESCE(frequency, 1) + 1)) DESC,
                updated_at DESC
            LIMIT %s
        """, (device_id, limit))
        facts = cursor.fetchall()
        cursor.close()
        return [dict(f) for f in facts]
    finally:
        release_db(conn)


def get_emotion_history(device_id, days=7):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT emotion, intensity, context, created_at
            FROM user_emotion_history
            WHERE device_id = %s
              AND created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC
            LIMIT 50
        """, (device_id, days))
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"get_emotion_history error: {e}", flush=True)
        return []
    finally:
        release_db(conn)


def save_emotion(device_id, emotion, intensity=0.5, context=None):
    if not emotion or emotion == 'neutral':
        return
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_emotion_history (device_id, emotion, intensity, context)
            VALUES (%s, %s, %s, %s)
        """, (device_id, emotion, intensity, context))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"save_emotion error: {e}", flush=True)
        if conn:
            conn.rollback()
    finally:
        release_db(conn)


def build_emotion_summary(emotion_history):
    if not emotion_history:
        return ""
    counts = {}
    for e in emotion_history:
        em = e.get('emotion', 'neutral')
        if em and em != 'neutral':
            counts[em] = counts.get(em, 0) + 1
    if not counts:
        return ""
    emotion_tr = {
        'sad': 'üzgün', 'happy': 'mutlu',
        'angry': 'sinirli', 'confused': 'kafası karışık',
    }
    dominant       = max(counts, key=counts.get)
    dominant_count = counts[dominant]
    dominant_tr    = emotion_tr.get(dominant, dominant)
    if dominant_count >= 3:
        return f"\n[DUYGU GEÇMİŞİ]: Son günlerde {dominant_tr} hissediyor ({dominant_count} kez). Buna duyarlı ol."
    return f"\n[DUYGU GEÇMİŞİ]: Yakın zamanda {dominant_tr} hissetmiş. Dikkat et."


def build_facts_prompt(facts):
    if not facts:
        return ""
    cat_names = {
        'sports': 'Spor', 'music': 'Müzik', 'food': 'Yemek',
        'hobbies': 'Hobiler', 'work': 'İş/Meslek', 'education': 'Eğitim',
        'location': 'Konum', 'family': 'Aile', 'technology': 'Teknoloji',
        'daily_routine': 'Rutin', 'personality': 'Kişilik',
        'movies': 'Film/Dizi', 'life_events': 'Hayat Olayları',
        'health': 'Sağlık', 'relationships': 'İlişkiler', 'finance': 'Finans',
    }
    grouped = {}
    for fact in facts[:20]:
        cat       = fact.get('category', 'general')
        val       = fact.get('value', '')
        ctx       = fact.get('context', '')
        importance = float(fact.get('importance', 0.5))
        frequency  = int(fact.get('frequency', 1))
        if not val:
            continue
        if cat not in grouped:
            grouped[cat] = []
        display = ctx if ctx and ctx != val else val
        marker  = " ⭐" if importance >= 0.8 or frequency >= 5 else ""
        grouped[cat].append(f"{display}{marker}")

    if not grouped:
        return ""

    lines = ["\n\nBU KULLANICI HAKKINDA BİLDİKLERİM (⭐ = çok önemli/sık bahsedilen):"]
    for cat, vals in grouped.items():
        cat_display = cat_names.get(cat, cat.title())
        lines.append(f"- {cat_display}: {', '.join(vals[:4])}")
    return '\n'.join(lines)


def build_forgotten_facts_prompt(facts):
    if not facts:
        return ""
    today    = get_turkey_time().date()
    forgotten = []
    for fact in facts:
        importance    = float(fact.get('importance', 0.5))
        last_mentioned = fact.get('last_mentioned')
        if not last_mentioned or importance < 0.6:
            continue
        if hasattr(last_mentioned, 'date'):
            last_date = last_mentioned.date()
        else:
            try:
                last_date = datetime.strptime(str(last_mentioned), '%Y-%m-%d').date()
            except Exception:
                continue
        days_ago = (today - last_date).days
        if days_ago >= 5:
            ctx = fact.get('context') or fact.get('value', '')
            forgotten.append(f"'{ctx}' ({days_ago} gün önce bahsetti)")
    if not forgotten:
        return ""
    return f"\n[UNUTULAN KONULAR]: {', '.join(forgotten[:2])} — uygunsa doğal şekilde sor."


# ── Extraction ────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """Asagidaki Turkce konusmayi analiz et ve asagidakileri cikar.

Kullanici mesaji: "{msg}"

GOREV 1 - Kisisel bilgileri bul:
Mesajda ACIKCA veya DOLAYLI olarak ifade edilen tum kisisel bilgileri al.
Gecici semptomlar, gundelik deneyimler, ruh hali bile dahil.

GOREV 2 - Cururtucu bilgileri bul:
Eger mesaj daha onceki bir bilgiyle ACIKCA celisiyor olabilecek ifadeler iceriyorsa,
bunlari contradictions listesine ekle.

GOREV 3 - Duygu yogunlugunu bul:
Mesajdaki duygusal tonu ve yogunlugunu belirle.

Yanit formati (SADECE JSON, baska hicbir sey yazma):
{{
  "learnings": [
    {{
      "category": "health",
      "value": "cildinde kucuk benekler var",
      "context": "Cildinde kucuk kucuk benekler oldugunu soyledi",
      "confidence": 0.85,
      "importance": 0.75,
      "frequency_hint": 1
    }}
  ],
  "contradictions": [],
  "emotion": {{
    "detected": "neutral",
    "intensity": 0.5,
    "context": ""
  }}
}}

Kategoriler: health, sports, music, food, hobbies, work, education, location,
family, technology, personality, movies, life_events, relationships, finance

Onemli:
- confidence: ne kadar kesin (0.5-1.0)
- importance: saglik/aile/is yuksek (0.7-0.9), hobiler orta (0.4-0.6)
- emotion.detected: neutral / happy / sad / angry / confused
- Hicbir somut bilgi yoksa learnings bos liste olsun
"""


def _do_extract_learnings(user_id, user_message, ai_response, client):
    print(f"🔍 extract_learnings START: user_id={user_id}, msg='{user_message[:40]}'", flush=True)
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM users WHERE id = %s", (str(user_id),))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return
        device_id = row['device_id']

        if not client or len(user_message.strip()) < 5:
            cursor.close()
            return

        resp = client.chat.completions.create(
            model=MODEL_EXTRACTION,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(msg=user_message)}],
            max_tokens=500,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        if '```' in raw:
            raw = raw[raw.find('{'):raw.rfind('}') + 1]

        parsed        = json.loads(raw)
        gpt_facts     = parsed.get("learnings", [])
        contradictions = parsed.get("contradictions", [])
        emotion_data  = parsed.get("emotion", {})
        print(f"🧠 Extraction result: {len(gpt_facts)} facts", flush=True)

        # Yeni fact'leri kaydet
        for fact in gpt_facts:
            if not fact.get('value') or not fact.get('category'):
                continue
            try:
                cursor.execute("""
                    INSERT INTO user_facts
                        (device_id, category, fact_key, fact_value, confidence,
                         source, importance, frequency, last_mentioned)
                    VALUES (%s, %s, %s, %s, %s, 'gpt_extraction', %s, %s, CURRENT_DATE)
                    ON CONFLICT (device_id, category, fact_key)
                    DO UPDATE SET
                        fact_value     = EXCLUDED.fact_value,
                        confidence     = LEAST(user_facts.confidence + 0.1, 1.0),
                        importance     = GREATEST(user_facts.importance, EXCLUDED.importance),
                        frequency      = user_facts.frequency + EXCLUDED.frequency,
                        last_mentioned = CURRENT_DATE,
                        updated_at     = CURRENT_TIMESTAMP
                """, (
                    device_id,
                    fact['category'],
                    fact['value'],
                    fact.get('context', ''),
                    float(fact.get('confidence', 0.7)),
                    float(fact.get('importance', 0.5)),
                    int(fact.get('frequency_hint', 1)),
                ))
                print(f"  → {fact.get('category')}: {fact.get('value')}", flush=True)
            except Exception as ex:
                print(f"fact insert error: {ex}", flush=True)

        # Çelişkileri işle
        for contradiction in contradictions:
            cat = contradiction.get('category')
            val = contradiction.get('value')
            if not cat or not val:
                continue
            try:
                cursor.execute("""
                    UPDATE user_facts
                    SET confidence = confidence - 0.3, updated_at = CURRENT_TIMESTAMP
                    WHERE device_id = %s AND category = %s AND fact_key != %s
                """, (device_id, cat, val))
                cursor.execute("""
                    DELETE FROM user_facts
                    WHERE device_id = %s AND category = %s AND confidence < 0.2
                """, (device_id, cat))
            except Exception as ex:
                print(f"contradiction update error: {ex}", flush=True)

        # Duygu kaydet
        detected  = emotion_data.get('detected', 'neutral')
        intensity = float(emotion_data.get('intensity', 0.5))
        ctx       = emotion_data.get('context', '')
        if detected and detected != 'neutral':
            try:
                cursor.execute("""
                    INSERT INTO user_emotion_history (device_id, emotion, intensity, context)
                    VALUES (%s, %s, %s, %s)
                """, (device_id, detected, intensity, ctx))
            except Exception as ex:
                print(f"emotion save error: {ex}", flush=True)

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f"_do_extract_learnings error: {e}", flush=True)
        print(tb.format_exc(), flush=True)
        if conn:
            try: conn.rollback()
            except: pass
    finally:
        release_db(conn)


def extract_learnings(user_id, user_message, ai_response, client):
    """Async — chat endpoint'ini bloke etmez."""
    t = threading.Thread(
        target=_do_extract_learnings,
        args=(user_id, user_message, ai_response, client),
        daemon=True,
    )
    t.start()
