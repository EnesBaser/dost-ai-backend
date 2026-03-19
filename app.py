# app.py — DostAI Backend v2.8
import time
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask, jsonify, g, request
from flask_sock import Sock
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import SENTRY_DSN, REDIS_URL
from database import init_db_pool, run_migrations
from services.scheduler import init_firebase, start_scheduler
from services.ai_service import get_client

from routes.chat          import chat_bp
from routes.user          import user_bp
from routes.media         import media_bp
from routes.notifications import notifications_bp
from routes.websocket     import register_websocket

# ── Sentry ────────────────────────────────────────────────────────────────────
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production",
        release="dostai-backend@2.8.0",
    )
    print("✅ Sentry monitoring enabled!")
else:
    print("⚠️ Sentry DSN not found - monitoring disabled")

# ── Flask ─────────────────────────────────────────────────────────────────────
app  = Flask(__name__)
CORS(app)
sock = Sock(app)

# ── Rate limiter ──────────────────────────────────────────────────────────────
def get_device_id():
    try:
        json_body   = request.get_json(silent=True)
        json_device = json_body.get('device_id') if json_body else None
    except Exception:
        json_device = None
    google_id = request.headers.get('X-Google-ID')
    device_id = request.headers.get('X-Device-ID') or json_device or get_remote_address()
    return google_id or device_id

limiter = Limiter(
    app=app,
    key_func=get_device_id,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri=REDIS_URL,
)

# ── Blueprints ────────────────────────────────────────────────────────────────
app.register_blueprint(chat_bp)
app.register_blueprint(user_bp)
app.register_blueprint(media_bp)
app.register_blueprint(notifications_bp)
register_websocket(sock)

# ── Learning system ───────────────────────────────────────────────────────────
try:
    from learning_routes import register_learning_routes
    register_learning_routes(app)
    print("✅ Learning System routes registered!")
except ImportError as e:
    print(f"⚠️ Learning system not available: {e}")

# ── Monitoring ────────────────────────────────────────────────────────────────
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        if duration > 2.0 and SENTRY_DSN:
            sentry_sdk.capture_message(
                f"Slow request: {request.endpoint}", level="warning",
                extras={"duration": duration, "endpoint": request.endpoint}
            )
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
    return response

# ── Temel route'lar ───────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status':   'ok',
        'version':  '2.8.0-production',
        'database': 'postgresql',
    })

@app.route('/')
def home():
    return jsonify({'status': 'ok', 'service': 'DostAI Backend v2.8'})

@app.route('/privacy-policy')
def privacy_policy():
    try:
        with open('privacy-policy.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Privacy Policy", 200

# ── Başlatma ──────────────────────────────────────────────────────────────────
try:
    init_db_pool()
except Exception as e:
    print(f"⚠️ Pool başlatılamadı, lazy init kullanılacak: {e}")

try:
    run_migrations()
except Exception as e:
    print(f"⚠️ Migration skip: {e}")

try:
    get_client()
except Exception as e:
    print(f"⚠️ OpenAI client başlatılamadı: {e}")

init_firebase()
start_scheduler()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
