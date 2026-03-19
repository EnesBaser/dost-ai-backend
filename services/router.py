# services/router.py
import re
import requests as req_lib
from config import (
    API_FOOTBALL_KEY, OPENWEATHER_KEY, EXCHANGERATE_KEY,
    TURKISH_LEAGUE_ID, TR_TEAM_KEYWORDS, EURO_TEAM_KEYWORDS
)
from services.search import web_search

ALL_TEAM_KEYWORDS = TR_TEAM_KEYWORDS + EURO_TEAM_KEYWORDS

# ── Spor ──────────────────────────────────────────────────────────────────────

SPORT_TRIGGERS = [
    'maç', 'mac', 'skor', 'gol', 'puan', 'lig', 'şampiyon',
    'sonuç', 'sonuc', 'oynadı', 'oynadi', 'attı', 'atti',
    'kazandı', 'kazandi', 'kaybetti', 'berabere', 'futbol',
    'basketbol', 'süper lig', 'super lig', 'champions league',
    'şampiyonlar ligi', 'avrupa ligi', 'uefa', 'dün', 'dun',
    'bu hafta', 'geçen hafta', 'gecen hafta', 'son maç', 'son mac',
]

TIME_TRIGGERS = ['dün', 'dun', 'bu hafta', 'geçen hafta', 'gecen hafta', 'son maç', 'son mac']


def _get_team_id(team_name, headers):
    """Takım adından API-Football team ID'si döner."""
    try:
        resp = req_lib.get(
            'https://v3.football.api-sports.io/teams',
            headers=headers,
            params={'search': team_name},
            timeout=5
        )
        if resp.status_code != 200:
            return None, None
        teams = resp.json().get('response', [])
        if not teams:
            return None, None
        return teams[0]['team']['id'], teams[0]['team']['name']
    except Exception:
        return None, None


def _format_fixture(fix):
    home       = fix['teams']['home']['name']
    away       = fix['teams']['away']['name']
    home_score = fix['goals']['home']
    away_score = fix['goals']['away']
    status     = fix['fixture']['status']['long']
    date_str   = fix['fixture']['date'][:16].replace('T', ' ')
    league     = fix['league']['name']

    if home_score is not None and away_score is not None:
        return f"• {date_str} | {league} | {home} {home_score}–{away_score} {away} ({status})"
    return f"• {date_str} | {league} | {home} vs {away}"


def get_sports_data(message_lower):
    if not API_FOOTBALL_KEY:
        return None

    if not any(t in message_lower for t in SPORT_TRIGGERS):
        return None

    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': API_FOOTBALL_KEY,
    }

    # Mesajdaki tüm takımları bul
    found_teams = []
    for team in ALL_TEAM_KEYWORDS:
        if team in message_lower:
            found_teams.append(team)

    try:
        # ── İki takım varsa: aralarındaki maçı bul ───────────────────────────
        if len(found_teams) >= 2:
            team1_id, team1_name = _get_team_id(found_teams[0], headers)
            team2_id, team2_name = _get_team_id(found_teams[1], headers)

            if not team1_id or not team2_id:
                return None

            # Takım 1'in son 10 maçını çek, içinde takım 2'yi filtrele
            resp = req_lib.get(
                'https://v3.football.api-sports.io/fixtures',
                headers=headers,
                params={'team': team1_id, 'last': 10, 'timezone': 'Europe/Istanbul'},
                timeout=5
            )
            if resp.status_code != 200:
                return None

            fixtures = resp.json().get('response', [])
            # Takım 2'nin oynadığı maçları filtrele
            h2h_fixtures = [
                f for f in fixtures
                if f['teams']['home']['id'] == team2_id
                or f['teams']['away']['id'] == team2_id
            ]

            if h2h_fixtures:
                parts = [f"⚽ {team1_name} vs {team2_name}:"]
                for fix in h2h_fixtures[:3]:
                    parts.append(_format_fixture(fix))
                return '\n'.join(parts)

            # H2H bulunamazsa web search'e düş
            print("⚠️ H2H maç bulunamadı, web search'e düşülüyor", flush=True)
            return None

        # ── Tek takım varsa: son + sonraki maçlar ────────────────────────────
        elif len(found_teams) == 1:
            team_id, team_name = _get_team_id(found_teams[0], headers)
            if not team_id:
                return None

            last_resp = req_lib.get(
                'https://v3.football.api-sports.io/fixtures',
                headers=headers,
                params={'team': team_id, 'last': 3, 'timezone': 'Europe/Istanbul'},
                timeout=5
            )
            next_resp = req_lib.get(
                'https://v3.football.api-sports.io/fixtures',
                headers=headers,
                params={'team': team_id, 'next': 3, 'timezone': 'Europe/Istanbul'},
                timeout=5
            )

            fixtures = []
            if last_resp.status_code == 200:
                fixtures += last_resp.json().get('response', [])
            if next_resp.status_code == 200:
                fixtures += next_resp.json().get('response', [])

            if not fixtures:
                return None

            parts = [f"⚽ {team_name} — Maçlar:"]
            for fix in fixtures:
                parts.append(_format_fixture(fix))
            return '\n'.join(parts)

        # ── Takım yok ama spor sorusu → Süper Lig son maçlar ─────────────────
        else:
            resp = req_lib.get(
                'https://v3.football.api-sports.io/fixtures',
                headers=headers,
                params={'league': TURKISH_LEAGUE_ID, 'last': 5, 'timezone': 'Europe/Istanbul'},
                timeout=5
            )
            if resp.status_code != 200:
                return None

            fixtures = resp.json().get('response', [])
            if not fixtures:
                return None

            parts = ["⚽ Süper Lig — Son Maçlar:"]
            for fix in fixtures:
                parts.append(_format_fixture(fix))
            return '\n'.join(parts)

    except Exception as e:
        print(f"API-Football error: {e}", flush=True)
        return None


# ── Hava ──────────────────────────────────────────────────────────────────────

WEATHER_TRIGGERS = [
    'hava', 'sıcaklık', 'sicaklik', 'yağmur', 'yagmur', 'kar',
    'derece', 'nem', 'rüzgar', 'ruzgar', 'bulut', 'güneş', 'gunes',
    'hava durumu', 'dışarısı', 'disarisi', 'soğuk', 'soguk', 'sıcak', 'sicak',
]

TR_CITIES = [
    'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 'konya',
    'gaziantep', 'mersin', 'kayseri', 'trabzon', 'samsun', 'denizli',
    'eskişehir', 'eskisehir', 'diyarbakır', 'diyarbakir', 'malatya',
    'erzurum', 'van', 'bodrum', 'muğla', 'mugla', 'fethiye',
]


def get_weather_data(message_lower, user_location=None):
    if not OPENWEATHER_KEY:
        return None
    if not any(t in message_lower for t in WEATHER_TRIGGERS):
        return None

    city = next((c for c in TR_CITIES if c in message_lower), None)
    if not city and user_location:
        city = user_location.split(',')[0].strip().lower()
    if not city:
        city = 'Istanbul'

    try:
        resp = req_lib.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'q': f'{city},TR', 'appid': OPENWEATHER_KEY, 'units': 'metric', 'lang': 'tr'},
            timeout=5
        )
        if resp.status_code != 200:
            return None

        data      = resp.json()
        temp      = round(data['main']['temp'])
        feels     = round(data['main']['feels_like'])
        desc      = data['weather'][0]['description']
        humidity  = data['main']['humidity']
        wind      = round(data['wind']['speed'] * 3.6)
        city_name = data['name']

        return (
            f"🌤 {city_name} hava durumu: {temp}°C (hissedilen {feels}°C), "
            f"{desc}, nem %{humidity}, rüzgar {wind} km/s"
        )
    except Exception as e:
        print(f"OpenWeatherMap error: {e}", flush=True)
        return None


# ── Finans ────────────────────────────────────────────────────────────────────

FINANCE_TRIGGERS = ['dolar', 'euro', 'döviz', 'doviz', 'kur', 'borsa', 'bist']

CRYPTO_TRIGGERS = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'kripto', 'crypto', 'coin',
    'usdt', 'doge', 'solana', 'sol', 'bnb', 'xrp', 'avax', 'ada',
    'shib', 'ltc', 'trx', 'matic', 'polygon', 'link', 'near', 'atom',
]

KNOWN_COINS = {
    'btc': 'bitcoin', 'bitcoin': 'bitcoin',
    'eth': 'ethereum', 'ethereum': 'ethereum',
    'doge': 'dogecoin', 'dogecoin': 'dogecoin',
    'sol': 'solana', 'solana': 'solana',
    'bnb': 'binancecoin',
    'xrp': 'ripple', 'ripple': 'ripple',
    'avax': 'avalanche-2',
    'ada': 'cardano', 'cardano': 'cardano',
    'matic': 'matic-network', 'polygon': 'matic-network',
    'link': 'chainlink', 'chainlink': 'chainlink',
    'ltc': 'litecoin', 'litecoin': 'litecoin',
    'shib': 'shiba-inu', 'shiba': 'shiba-inu',
    'trx': 'tron', 'tron': 'tron',
    'atom': 'cosmos', 'cosmos': 'cosmos',
    'near': 'near',
}


def get_finance_data(message_lower):
    is_finance = any(t in message_lower for t in FINANCE_TRIGGERS)
    is_crypto  = any(t in message_lower for t in CRYPTO_TRIGGERS)

    if not is_finance and not is_crypto:
        return None

    parts = []

    # Döviz
    if is_finance:
        try:
            if EXCHANGERATE_KEY:
                url = f'https://v6.exchangerate-api.com/v6/{EXCHANGERATE_KEY}/latest/USD'
            else:
                url = 'https://api.exchangerate-api.com/v4/latest/USD'

            resp = req_lib.get(url, timeout=5)
            if resp.status_code == 200:
                rates    = resp.json().get('conversion_rates') or resp.json().get('rates', {})
                usd_try  = rates.get('TRY', 0)
                eur_usd  = rates.get('EUR', 0)
                eur_try  = round(usd_try / eur_usd, 2) if eur_usd else 0
                if usd_try:
                    parts.append(f"💵 1 USD = {round(usd_try, 2)} TRY")
                if eur_try:
                    parts.append(f"💶 1 EUR = {eur_try} TRY")
        except Exception as e:
            print(f"ExchangeRate error: {e}", flush=True)

    # Kripto
    if is_crypto:
        try:
            words    = re.findall(r'[a-zA-Z0-9]+', message_lower)
            coin_ids = []
            coin_display = {}

            for word in words:
                if word in KNOWN_COINS:
                    cid = KNOWN_COINS[word]
                    if cid not in coin_ids:
                        coin_ids.append(cid)
                        coin_display[cid] = word.upper()

            if not coin_ids:
                coin_ids    = ['bitcoin', 'ethereum']
                coin_display = {'bitcoin': 'Bitcoin', 'ethereum': 'Ethereum'}

            resp = req_lib.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': ','.join(coin_ids),
                    'vs_currencies': 'usd,try',
                    'include_24hr_change': 'true',
                },
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                for coin in coin_ids:
                    if coin not in data:
                        continue
                    usd_price  = data[coin].get('usd', 0)
                    try_price  = data[coin].get('try', 0)
                    change_24h = data[coin].get('usd_24h_change', 0)
                    change_str = f"{'📈' if change_24h >= 0 else '📉'} {change_24h:+.1f}%"
                    name       = coin_display.get(coin, coin.title())
                    if usd_price < 1:
                        parts.append(f"🪙 {name}: ${usd_price:.4f} ({try_price:.2f} TRY) {change_str}")
                    else:
                        parts.append(f"🪙 {name}: ${usd_price:,.2f} ({try_price:,.0f} TRY) {change_str}")
        except Exception as e:
            print(f"CoinGecko error: {e}", flush=True)

    return '\n'.join(parts) if parts else None


# ── Web search keyword listesi ────────────────────────────────────────────────

WEB_SEARCH_TRIGGERS = [
    'haber', 'son dakika', 'güncel', 'bugün ne oldu',
    'etkinlik', 'konser', 'sergi', 'festival', 'tiyatro',
    'sinema', 'vizyonda', 'ne zaman', 'nerede', 'açık mı', 'kapalı mı',
    'yeni çıktı', 'yeni album', 'yeni film', 'yeni sezon',
    'seçim', 'deprem', 'trafik', 'grev',
    'altın', 'altin', 'gram altın', 'çeyrek', 'yarım altın',
    'gümüş', 'gumus', 'petrol',
    'araştır', 'firma', 'şirket', 'hakkında bilgi',
    'kimdir', 'nedir', 'telefon', 'adres', 'web sitesi',
    'en iyi', 'karşılaştır', 'hangisi daha iyi', 'tavsiye',
]


def needs_web_search(message):
    return any(k in message.lower() for k in WEB_SEARCH_TRIGGERS)


# ── Ana router ────────────────────────────────────────────────────────────────

def route_query(message, user_location=None):
    """
    Öncelik: Sports API → Weather API → Finance API → Web Search → None
    Sports API sonuç döndüremezse (H2H bulunamadı gibi) web search'e düşer.
    """
    msg_lower = message.lower()

    # 1. Spor
    sports_result = get_sports_data(msg_lower)
    if sports_result:
        print("✅ Router: SPORTS API", flush=True)
        return sports_result, 'sports_api'

    # 2. Spor sorusu ama API sonuç vermediyse → web search'e düş
    is_sport_question = any(t in msg_lower for t in SPORT_TRIGGERS)
    if is_sport_question:
        search_result = web_search(message[:150])
        if search_result:
            print("✅ Router: SPORTS → WEB SEARCH fallback", flush=True)
            return search_result, 'web_search'

    # 3. Hava
    weather_result = get_weather_data(msg_lower, user_location)
    if weather_result:
        print("✅ Router: WEATHER API", flush=True)
        return weather_result, 'weather_api'

    # 4. Finans
    finance_result = get_finance_data(msg_lower)
    if finance_result:
        print("✅ Router: FINANCE API", flush=True)
        return finance_result, 'finance_api'

    # 5. Genel web search
    if needs_web_search(message):
        search_result = web_search(message[:150])
        if search_result:
            print("✅ Router: WEB SEARCH", flush=True)
            return search_result, 'web_search'

    return None, None
