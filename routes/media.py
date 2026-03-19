# routes/media.py
import re
import base64
import os
import requests as req_lib
from flask import Blueprint, request, jsonify
from auth import require_auth
from services.ai_service import get_client
from database import get_db, release_db
from config import TAVILY_API_KEY, ADMIN_GOOGLE_IDS

media_bp = Blueprint('media', __name__)


# ── TTS ───────────────────────────────────────────────────────────────────────

@media_bp.route('/api/tts', methods=['POST'])
@require_auth
def text_to_speech():
    client = get_client()
    if not client:
        return jsonify({'error': 'OpenAI not configured'}), 503

    data  = request.get_json()
    text  = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text required'}), 400

    voice = data.get('voice', 'nova')
    if voice not in ['alloy', 'echo', 'fable', 'nova', 'onyx', 'shimmer']:
        voice = 'nova'

    text = re.sub(r"[^\w\s.,!?'\"()-]", '', text)[:500]

    try:
        response  = client.audio.speech.create(
            model="tts-1", voice=voice, input=text,
            response_format="mp3", speed=1.0,
        )
        audio_b64 = base64.b64encode(response.content).decode('utf-8')
        return jsonify({'audio': audio_b64})
    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({'error': str(e)}), 500


# ── STT ───────────────────────────────────────────────────────────────────────

@media_bp.route('/api/stt', methods=['POST'])
@require_auth
def speech_to_text():
    client = get_client()
    if not client:
        return jsonify({'error': 'OpenAI not configured'}), 503

    if 'audio' not in request.files:
        return jsonify({'error': 'audio file required'}), 400

    audio_file = request.files['audio']
    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(
                audio_file.filename or 'audio.m4a',
                audio_file.read(),
                audio_file.content_type or 'audio/m4a',
            ),
            language="tr",
            response_format="text",
        )
        text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()

        noise_phrases = [
            'tesekkurler', 'tesekkur ederim', 'sag olun',
            'thank you', 'thanks', 'music', 'muzik',
        ]
        if len(text) < 3 or text.lower().strip('.,!? ') in noise_phrases:
            return jsonify({'text': ''})

        return jsonify({'text': text})
    except Exception as e:
        print(f"STT error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Image analyze ─────────────────────────────────────────────────────────────

@media_bp.route('/api/image/analyze', methods=['POST'])
@require_auth
def analyze_image():
    client = get_client()
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Görsel bulunamadı'}), 400

        image_file  = request.files['image']
        user_prompt = request.form.get('prompt', 'Bu görseli detaylıca analiz et ve açıkla.')
        image_bytes = image_file.read()
        image_data  = base64.b64encode(image_bytes).decode('utf-8')

        filename  = image_file.filename or 'image.jpg'
        ext       = os.path.splitext(filename)[1].lower()
        mime_map  = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{mime_type};base64,{image_data}',
                            'detail': 'high',
                        },
                    },
                    {
                        'type': 'text',
                        'text': f"{user_prompt}\n\nTürkçe yanıt ver, samimi ve arkadaşça bir dil kullan.",
                    },
                ],
            }],
            max_tokens=1000,
        )
        analysis = response.choices[0].message.content
        return jsonify({'analysis': analysis, 'status': 'success'})

    except Exception as e:
        print(f'❌ Image analyze error: {e}', flush=True)
        return jsonify({'error': str(e)}), 500


# ── Image generate ────────────────────────────────────────────────────────────

@media_bp.route('/api/image/generate', methods=['POST'])
@require_auth
def generate_image():
    client  = get_client()
    user    = request.user
    is_admin = user.get('google_id') in ADMIN_GOOGLE_IDS

    if not is_admin and user.get('subscription_tier') == 'free':
        return jsonify({
            'error':   'premium_required',
            'message': 'DALL-E görsel üretimi Premium özelliğidir.',
        }), 403

    monthly_limit = 999 if is_admin else 20
    conn = None

    try:
        if not is_admin:
            conn   = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM analytics_events
                WHERE user_id = %s
                  AND event_name = 'image_generated'
                  AND created_at >= date_trunc('month', NOW())
            """, (str(user['id']),))
            row           = cursor.fetchone()
            monthly_count = int(row['cnt']) if row else 0
            cursor.close()
            release_db(conn)
            conn = None

            if monthly_count >= monthly_limit:
                return jsonify({
                    'error':   'monthly_limit_reached',
                    'message': f'Bu ay {monthly_limit} görsel limitinize ulaştınız.',
                    'count':   monthly_count,
                    'limit':   monthly_limit,
                }), 429
        else:
            monthly_count = 0

        data   = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'error': 'Prompt gerekli'}), 400

        enhanced = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{
                'role': 'user',
                'content': (
                    f"Bu Türkçe görsel talebini, DALL-E 3 için İngilizce detaylı "
                    f"bir prompt'a çevir. Sadece prompt'u yaz:\n\n{prompt}"
                ),
            }],
            max_tokens=200,
        )
        english_prompt = enhanced.choices[0].message.content.strip()

        image_response = client.images.generate(
            model='dall-e-3', prompt=english_prompt,
            size='1024x1024', quality='standard', n=1,
        )
        image_url      = image_response.data[0].url
        revised_prompt = image_response.data[0].revised_prompt or english_prompt

        return jsonify({
            'image_url':       image_url,
            'revised_prompt':  revised_prompt,
            'original_prompt': prompt,
            'status':          'success',
            'monthly_remaining': monthly_limit - monthly_count - 1,
        })

    except Exception as e:
        print(f'❌ Image generate error: {e}', flush=True)
        return jsonify({'error': str(e)}), 500
    finally:
        release_db(conn)


# ── Image search ──────────────────────────────────────────────────────────────

@media_bp.route('/api/image/search', methods=['POST'])
@require_auth
def search_images():
    try:
        data  = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'Sorgu gerekli'}), 400

        if not TAVILY_API_KEY:
            return jsonify({'error': 'Arama servisi yapılandırılmamış'}), 500

        response = req_lib.post(
            'https://api.tavily.com/search',
            json={
                'api_key':       TAVILY_API_KEY,
                'query':         query,
                'search_depth':  'basic',
                'include_images': True,
                'max_results':   5,
            },
            timeout=15,
        )
        if response.status_code == 200:
            result  = response.json()
            images  = result.get('images', [])
            formatted = [
                {
                    'url':    img if isinstance(img, str) else img.get('url', ''),
                    'title':  '' if isinstance(img, str) else img.get('description', ''),
                    'source': '',
                }
                for img in images[:6]
                if (isinstance(img, str) and img) or (isinstance(img, dict) and img.get('url'))
            ]
            return jsonify({'results': formatted, 'status': 'success'})

        return jsonify({'results': [], 'status': 'no_results'})

    except Exception as e:
        print(f'❌ Image search error: {e}', flush=True)
        return jsonify({'error': str(e)}), 500
