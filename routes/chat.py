# routes/chat.py
import json
import traceback as tb
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
import sentry_sdk

from auth import require_auth
from config import ADMIN_GOOGLE_IDS, TIER_LIMITS, SENTRY_DSN
from services.ai_service import get_client
from services.learning import (
    get_learned_facts, get_emotion_history, save_emotion,
    build_facts_prompt, build_emotion_summary, build_forgotten_facts_prompt,
    extract_learnings, get_turkey_time,
)
from services.router import route_query
from routes.user import (
    get_user_profile, check_usage_limit, check_daily_cost_limit,
    increment_usage, save_message, get_message_count,
)

chat_bp = Blueprint('chat', __name__)

# ── Schema ────────────────────────────────────────────────────────────────────

class ChatSchema(Schema):
    message              = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    conversation_history = fields.List(fields.Dict(), required=False)
    emotion              = fields.Str(validate=validate.OneOf(['neutral', 'happy', 'sad', 'angry', 'confused']))
    device_id            = fields.Str(required=False, load_default=None)
    userName             = fields.Str(required=False, load_default=None)
    userProfile          = fields.Dict(required=False, load_default=None)
    tts_enabled          = fields.Bool(required=False, load_default=False)
    voice                = fields.Str(required=False, load_default='nova')


# ── Function calling ──────────────────────────────────────────────────────────

FUNCTIONS = [
    {
        "name": "create_event",
        "description": "Kullanıcı bir etkinlik, randevu veya hatırlatma oluşturmak istediğinde çağır",
        "parameters": {
            "type": "object",
            "properties": {
                "title":            {"type": "string", "description": "Etkinlik başlığı"},
                "description":      {"type": "string", "description": "Etkinlik açıklaması (opsiyonel)"},
                "date":             {"type": "string", "description": "Tarih YYYY-MM-DD formatında"},
                "time":             {"type": "string", "description": "Saat HH:MM formatında (24 saat)"},
                "reminder_minutes": {"type": "integer", "description": "Kaç dakika önce hatırlatılsın"},
            },
            "required": ["title", "date", "time"],
        }
    }
]


# ── Tracking ──────────────────────────────────────────────────────────────────

def track_event(event_name, user_id=None, properties=None):
    from database import get_db, release_db
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_events (event_name, user_id, properties, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (event_name, user_id, json.dumps(properties or {})))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f'❌ track_event error: {e}', flush=True)
    finally:
        release_db(conn)


# ── System prompt builder ─────────────────────────────────────────────────────

def build_system_prompt(user, profile, learned_facts, emotion_history,
                        total_messages, emotion, web_context, turkey_time):
    interests      = profile.get('interests', []) if profile else []
    interests_text = ', '.join(interests) if interests else 'çeşitli konular'

    facts_text       = build_facts_prompt(learned_facts)
    emotion_summary  = build_emotion_summary(emotion_history)
    forgotten_prompt = build_forgotten_facts_prompt(learned_facts)

    emotional_context = ""
    if emotion == 'sad':
        emotional_context = f"\n{user['name']} ŞU AN ÜZGÜN. Çok destekleyici ve empatik ol, önce dinle."
    elif emotion == 'happy':
        emotional_context = f"\n{user['name']} ŞU AN MUTLU! Enerjisini paylaş, kutla."
    elif emotion == 'angry':
        emotional_context = f"\n{user['name']} ŞU AN SİNİRLİ. Sakin, anlayışlı ve sabırlı ol."
    elif emotion == 'confused':
        emotional_context = f"\n{user['name']} ŞU AN KAFASI KARIŞIK. Net, adım adım açıkla."

    days_since_created = (turkey_time.date() - user['created_at'].date()).days
    relationship_context = ""
    if days_since_created > 0:
        relationship_context = f"\n{user['name']} ile {days_since_created} gündür arkadaşsınız."

    return (
        f"Sen DostAI'sin — {user['name']}'in gerçek anlamda kişisel yapay zeka dostusun.\n"
        f"Kullanıcı: {user['name']}\n"
        f"İlgi alanları: {interests_text}\n"
        f"Bugün: {turkey_time.strftime('%d %B %Y, %A')} | Saat: {turkey_time.strftime('%H:%M')}\n"
        f"Toplam konuşma: {total_messages} mesaj{relationship_context}"
        f"{emotional_context}"
        f"{emotion_summary}"
        f"{facts_text}"
        f"{forgotten_prompt}"
        f"{web_context}\n\n"
        "GÖREVİN:\n"
        "- Seni tanıyan bir dost gibi konuş, robot gibi değil\n"
        "- Öğrendiklerini doğal şekilde konuşmaya yansıt — ama zorla değil\n"
        "- ⭐ ile işaretli konular kullanıcı için çok önemli\n"
        "- Kullanıcı sağlık şikayeti veya yeni bilgi paylaşırsa mutlaka değin\n"
        "- Duygu geçmişine duyarlı ol\n"
        "- Kısa, samimi, günlük dil kullan\n"
        "- Asla 'Nasıl yardımcı olabilirim?' diye başlama\n"
        "- Asla listeleme yapma, doğal cümlelerle konuş\n"
        "- Fiyat/kur/kripto verisi sağlandıysa direkt söyle\n"
        "- Web arama sonucu varsa onu kullan, kullanıcıyı dışarıya yönlendirme\n"
        "- Sağlık konularında somut ama abartısız öneriler ver\n"
    )


def build_web_context(data_result, data_source):
    if not data_result:
        return ""
    if data_source == 'sports_api':
        return (
            f"\n\n[SPOR VERİSİ — API-Football, %100 güncel]:\n{data_result}\n\n"
            "KRİTİK KURAL: Yukarıdaki spor verisini AYNEN kullan. "
            "Kendi bilginden HİÇBİR skor, isim veya tarih ekleme."
        )
    elif data_source == 'weather_api':
        return (
            f"\n\n[HAVA DURUMU — OpenWeatherMap, anlık]:\n{data_result}\n\n"
            "Bu veriyi kullan, kendi tahminini ekleme."
        )
    elif data_source == 'finance_api':
        return (
            f"\n\n[DÖVİZ/KRİPTO — Anlık kur]:\n{data_result}\n\n"
            "Bu veriyi kullan, kendi tahmini fiyat söyleme."
        )
    elif data_source == 'web_search':
        return (
            f"\n\n[WEB ARAMA SONUÇLARI]:\n{data_result}\n\n"
            "KRİTİK KURAL: Web sonuçlarında ne yazıyorsa SADECE ONU kullan. "
            "Sonuçlar yetersizse 'güncel bilgiye tam ulaşamadım' de."
        )
    return ""


# ── Ana chat endpoint ─────────────────────────────────────────────────────────

@chat_bp.route('/chat', methods=['POST'])
@require_auth
def chat():
    user     = request.user
    is_admin = user.get('google_id') in ADMIN_GOOGLE_IDS
    client   = get_client()

    if not client:
        return jsonify({'response': 'OpenAI bağlantısı kurulamadı'}), 500

    try:
        schema = ChatSchema()
        data   = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid input', 'details': err.messages}), 400

    user_message         = data.get('message', '')
    conversation_history = data.get('conversation_history', [])
    emotion              = data.get('emotion', 'neutral')
    effective_tier       = 'pro' if is_admin else user['subscription_tier']

    # Limit kontrol
    if not is_admin:
        usage = check_usage_limit(user['id'], effective_tier)
        if not usage['allowed']:
            track_event('daily_limit_reached', str(user['id']), {'tier': effective_tier})
            return jsonify({
                'error':   'daily_limit_exceeded',
                'message': f"Günlük mesaj limitiniz doldu ({usage['limit']} mesaj). Premium'a geçin!",
                'limit':   usage['limit'],
                'current': usage['current'],
            }), 429

        cost_check = check_daily_cost_limit(user['id'], effective_tier)
        if not cost_check['allowed']:
            return jsonify({
                'error':   'daily_cost_exceeded',
                'message': "Günlük maliyet limitiniz doldu. Yarın tekrar deneyin!",
            }), 429

    # Duygu & mesaj kaydet
    device_id = user.get('device_id') or str(user['id'])
    if emotion and emotion != 'neutral':
        save_emotion(device_id, emotion, intensity=0.6, context=user_message[:100])
    save_message(user['id'], 'user', user_message, emotion=emotion)

    try:
        turkey_time    = get_turkey_time()
        profile        = get_user_profile(user['id'])
        learned_facts  = get_learned_facts(user['id'], 20)
        emotion_history = get_emotion_history(device_id, days=7)
        total_messages = get_message_count(user['id'])

        # Kullanıcı konumu
        user_location = None
        if profile and profile.get('location'):
            user_location = profile['location']
        else:
            user_location = next(
                (f['value'] for f in learned_facts if f.get('category') == 'location' and f.get('value')),
                None
            )

        # Veri router
        data_result, data_source = route_query(user_message, user_location)
        web_context = build_web_context(data_result, data_source)

        # System prompt
        system_prompt = build_system_prompt(
            user, profile, learned_facts, emotion_history,
            total_messages, emotion, web_context, turkey_time,
        )

        # Mesaj geçmişi
        tier_limits  = TIER_LIMITS[effective_tier]
        max_tokens   = tier_limits['max_tokens']
        history_limit = 10 if effective_tier == 'free' else 50

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-history_limit:])
        messages.append({"role": "user", "content": user_message})

        use_functions = effective_tier != 'free'

        # OpenAI çağrısı
        response = client.chat.completions.create(
            model=TIER_LIMITS[effective_tier].get('model', 'gpt-4o-mini'),
            messages=messages,
            functions=FUNCTIONS if use_functions else None,
            function_call="auto" if use_functions else None,
            max_tokens=max_tokens,
            temperature=0.8,
        )

        assistant_message = response.choices[0].message
        token_count       = response.usage.total_tokens

        track_event('message_sent', str(user['id']), {
            'tier':        effective_tier,
            'tokens':      token_count,
            'emotion':     emotion,
            'data_source': data_source or 'none',
        })

        # Function call
        if assistant_message.function_call:
            function_name = assistant_message.function_call.name
            function_args = json.loads(assistant_message.function_call.arguments)
            if assistant_message.content:
                save_message(user['id'], 'assistant', assistant_message.content, token_count)
            increment_usage(user['id'], token_count)
            return jsonify({
                "response":      assistant_message.content or "Tamam!",
                "function_call": {"name": function_name, "arguments": function_args},
            })

        # Normal yanıt
        ai_response = assistant_message.content
        save_message(user['id'], 'assistant', ai_response, token_count)
        increment_usage(user['id'], token_count)
        extract_learnings(user['id'], user_message, ai_response, client)

        usage_after = check_usage_limit(user['id'], effective_tier)
        cost_after  = check_daily_cost_limit(user['id'], effective_tier)

        return jsonify({
            'response':     ai_response,
            'new_learnings': [],
            'web_searched': bool(web_context),
            'data_source':  data_source or 'none',
            'audio':        None,
            'usage': {
                'remaining': usage_after['remaining'],
                'limit':     usage_after['limit'],
            },
            'cost': {
                'current': round(cost_after['current_cost'], 4),
                'max':     cost_after['max_cost'],
            },
        })

    except Exception as e:
        print(f"Chat error: {e}", flush=True)
        print(tb.format_exc(), flush=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        return jsonify({'error': f'Chat error: {str(e)}'}), 500
