# config.py
import os
import pytz
from dotenv import load_dotenv

load_dotenv()

# ── Timezone ──────────────────────────────────────────────────────────────────
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Modeller
MODEL_CHAT        = "gpt-4o-mini"      # Sohbet — hızlı, ucuz
MODEL_SMART       = "gpt-4o"           # Web sonucu yorumlama, karmaşık sorular
MODEL_EXTRACTION  = "gpt-4o-mini"      # Fact extraction
MODEL_TTS         = "tts-1"
MODEL_STT         = "whisper-1"
MODEL_IMAGE       = "gpt-4o"
MODEL_IMAGE_GEN   = "dall-e-3"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL')
DB_MIN_CONN  = 2
DB_MAX_CONN  = 20

# ── Redis / Rate limiter ──────────────────────────────────────────────────────
REDIS_URL = os.getenv('REDIS_URL', 'memory://')

# ── External APIs ─────────────────────────────────────────────────────────────
SENTRY_DSN          = os.getenv('SENTRY_DSN')
TAVILY_API_KEY      = os.getenv('TAVILY_API_KEY')
SERPER_API_KEY      = os.getenv('SERPER_API_KEY')
API_FOOTBALL_KEY    = os.getenv('API_FOOTBALL_KEY')
OPENWEATHER_KEY     = os.getenv('OPENWEATHER_API_KEY')
EXCHANGERATE_KEY    = os.getenv('EXCHANGERATE_API_KEY')

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')

# ── Admin ─────────────────────────────────────────────────────────────────────
ADMIN_GOOGLE_IDS = {'117096745782071439494'}

# ── Tier limitleri ────────────────────────────────────────────────────────────
TIER_LIMITS = {
    'free':    {'daily_messages': 30,     'max_tokens': 150},
    'premium': {'daily_messages': 500,    'max_tokens': 500},
    'pro':     {'daily_messages': 999999, 'max_tokens': 1000},
}

MAX_DAILY_COST_PER_USER = {
    'free':    0.10,
    'premium': 1.00,
    'pro':     5.00,
}

# ── Spor ──────────────────────────────────────────────────────────────────────
TURKISH_LEAGUE_ID = 203

TR_TEAM_KEYWORDS = [
    'galatasaray', 'fenerbahçe', 'fenerbahce', 'beşiktaş', 'besiktas',
    'trabzonspor', 'başakşehir', 'basaksehir', 'antalyaspor', 'konyaspor',
    'kasımpaşa', 'kasimpasa', 'sivasspor', 'alanyaspor', 'kayserispor',
    'hatayspor', 'gaziantep', 'rizespor', 'adana demirspor', 'pendikspor',
    'fatih karagümrük', 'karagumruk', 'samsunspor', 'bodrumspor',
]

EURO_TEAM_KEYWORDS = [
    'real madrid', 'barcelona', 'atletico', 'manchester', 'liverpool',
    'arsenal', 'chelsea', 'city', 'united', 'juventus', 'milan', 'inter',
    'napoli', 'roma', 'psg', 'paris saint', 'dortmund', 'bayern', 'ajax',
    'porto', 'benfica',
]
