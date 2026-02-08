from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime
import pytz
import json

load_dotenv()
app = Flask(__name__)
CORS(app)

# Türkiye timezone'u tanımla
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

try:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY bulunamadı!")
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client başarıyla oluşturuldu!")
except Exception as e:
    print(f"❌ OpenAI client oluşturulamadı: {e}")
    client = None

# OpenAI Function Definitions
FUNCTIONS = [
    {
        "name": "create_event",
        "description": "Kullanıcı bir etkinlik, randevu veya hatırlatma oluşturmak istediğinde bu fonksiyonu çağır. Örnek: 'Yarın saat 3'te diş doktoruna git', 'Cuma 14:00'da toplantı', 'Pazartesi sabah spor'",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Etkinliğin başlığı, kısa ve öz (örn: 'Diş doktoru', 'Toplantı', 'Spor')"
                },
                "description": {
                    "type": "string",
                    "description": "Etkinlik hakkında ek bilgi (opsiyonel)"
                },
                "date": {
                    "type": "string",
                    "description": "Tarih YYYY-MM-DD formatında (örn: '2026-02-08')"
                },
                "time": {
                    "type": "string",
                    "description": "Saat HH:MM formatında 24 saat (örn: '15:00', '09:30')"
                },
                "reminder_minutes": {
                    "type": "integer",
                    "description": "Kaç dakika önce hatırlatma (5, 15, 30, 60). Belirtilmediyse null"
                }
            },
            "required": ["title", "date", "time"]
        }
    },
    {
        "name": "web_search",
        "description": "Güncel bilgi, haber, veya gerçek zamanlı veri gerektiğinde bu fonksiyonu çağır. Örnek: 'Bugün hava nasıl?', 'Dolar kuru kaç?', 'Son haberler neler?', 'iPhone 15 özellikleri'",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Arama sorgusu, kısa ve net (örn: 'İstanbul hava durumu', 'dolar kuru')"
                },
                "count": {
                    "type": "integer",
                    "description": "Kaç sonuç döndürülsün (varsayılan: 5)"
                }
            },
            "required": ["query"]
        }
    }
]

# Brave Search helper
def brave_search(query, count=5):
    """Brave Search API ile arama yap"""
    import requests
    
    api_key = os.getenv('BRAVE_SEARCH_API_KEY')
    if not api_key:
        return None
    
    try:
        headers = {
            'Accept': 'application/json',
            'X-Subscription-Token': api_key
        }
        
        params = {
            'q': query,
            'count': count,
            'search_lang': 'tr'  # Türkçe öncelik
        }
        
        response = requests.get(
            'https://api.search.brave.com/res/v1/web/search',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Web sonuçlarını işle
            if 'web' in data and 'results' in data['web']:
                for item in data['web']['results'][:count]:
                    results.append({
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'url': item.get('url', '')
                    })
            
            return results
        return None
    except Exception as e:
        print(f"Brave Search Error: {e}")
        return None

# Database helper functions
def get_db():
    conn = sqlite3.connect('memory.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_turkey_time():
    """Türkiye saatini döndür"""
    return datetime.now(TURKEY_TZ)

def init_db():
    """Veritabanını başlat - KALICI HAFIZA SİSTEMİ"""
    conn = get_db()
    
    # Mesajlar tablosu
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # YENI: User profile tablosu - KALICI KULLANICI BİLGİLERİ
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            nickname TEXT,
            interests TEXT,
            birthday TEXT,
            created_at TEXT,
            last_updated TEXT,
            onboarding_completed INTEGER DEFAULT 0,
            additional_info TEXT
        )
    ''')
    
    # YENI: Conversation summaries - Eski konuşmaların özetleri
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_range_start INTEGER,
            message_range_end INTEGER,
            summary TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with permanent memory system!")

def save_message(role, content):
    """Mesajı Türkiye saati ile kaydet"""
    conn = get_db()
    turkey_time = get_turkey_time().isoformat()
    conn.execute('INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)', 
                 (role, content, turkey_time))
    conn.commit()
    conn.close()

def save_or_update_user_profile(profile_data):
    """Kullanıcı profilini kaydet veya güncelle - KALICI HAFIZA"""
    conn = get_db()
    turkey_time = get_turkey_time().isoformat()
    
    # Profil var mı kontrol et
    existing = conn.execute('SELECT id FROM user_profile WHERE id = 1').fetchone()
    
    if existing:
        # Güncelle
        conn.execute('''
            UPDATE user_profile 
            SET name = ?, 
                nickname = ?, 
                interests = ?, 
                birthday = ?,
                last_updated = ?,
                onboarding_completed = ?,
                additional_info = ?
            WHERE id = 1
        ''', (
            profile_data.get('name'),
            profile_data.get('nickname'),
            json.dumps(profile_data.get('interests', [])),
            profile_data.get('birthday'),
            turkey_time,
            profile_data.get('onboarding_completed', 1),
            json.dumps(profile_data.get('additional_info', {}))
        ))
    else:
        # Yeni oluştur
        conn.execute('''
            INSERT INTO user_profile 
            (id, name, nickname, interests, birthday, created_at, last_updated, onboarding_completed, additional_info)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_data.get('name'),
            profile_data.get('nickname'),
            json.dumps(profile_data.get('interests', [])),
            profile_data.get('birthday'),
            turkey_time,
            turkey_time,
            profile_data.get('onboarding_completed', 1),
            json.dumps(profile_data.get('additional_info', {}))
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ User profile saved/updated: {profile_data.get('name')}")

def get_user_profile():
    """Kullanıcı profilini getir - KALICI HAFIZA"""
    conn = get_db()
    profile = conn.execute('SELECT * FROM user_profile WHERE id = 1').fetchone()
    conn.close()
    
    if profile:
        return {
            'name': profile['name'],
            'nickname': profile['nickname'],
            'interests': json.loads(profile['interests']) if profile['interests'] else [],
            'birthday': profile['birthday'],
            'created_at': profile['created_at'],
            'last_updated': profile['last_updated'],
            'onboarding_completed': profile['onboarding_completed'],
            'additional_info': json.loads(profile['additional_info']) if profile['additional_info'] else {}
        }
    return None

def get_conversation_history_smart(limit=100):
    """
    Akıllı konuşma geçmişi - KALICI HAFIZA
    - Son {limit} mesajı TAM OLARAK al
    - Daha eski mesajlar varsa özet kullan
    """
    conn = get_db()
    
    # Toplam mesaj sayısı
    total_messages = conn.execute('SELECT COUNT(*) as count FROM messages').fetchone()['count']
    
    # Son {limit} mesajı al
    recent_messages = conn.execute(
        'SELECT role, content FROM messages ORDER BY id DESC LIMIT ?',
        (limit,)
    ).fetchall()
    
    history = [{"role": msg['role'], "content": msg['content']} for msg in reversed(recent_messages)]
    
    # Eğer daha eski mesajlar varsa, özet ekle
    if total_messages > limit:
        summary = conn.execute(
            'SELECT summary FROM conversation_summaries ORDER BY id DESC LIMIT 1'
        ).fetchone()
        
        if summary:
            # Özetin başına ekle
            history.insert(0, {
                "role": "system",
                "content": f"📝 Önceki konuşma özeti: {summary['summary']}"
            })
    
    conn.close()
    return history, total_messages

def create_conversation_summary():
    """
    Her 200 mesajda bir otomatik özet oluştur - TOKEN TASARRUFU
    Bu fonksiyon arka planda çağrılabilir
    """
    conn = get_db()
    
    # Son özetten sonraki mesajları al
    last_summary = conn.execute(
        'SELECT message_range_end FROM conversation_summaries ORDER BY id DESC LIMIT 1'
    ).fetchone()
    
    start_id = last_summary['message_range_end'] + 1 if last_summary else 1
    
    # Özetlenecek mesajları al (200 mesaj)
    messages_to_summarize = conn.execute(
        '''SELECT id, role, content FROM messages 
           WHERE id >= ? AND id < ? 
           ORDER BY id ASC''',
        (start_id, start_id + 200)
    ).fetchall()
    
    if len(messages_to_summarize) >= 200:
        # OpenAI ile özet oluştur
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages_to_summarize])
        
        try:
            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Aşağıdaki konuşmayı özetle. Önemli detayları, kullanıcının tercihlerini, geçmiş olayları koru. Kısa ve öz yaz."
                    },
                    {
                        "role": "user",
                        "content": conversation_text
                    }
                ],
                max_tokens=300
            )
            
            summary = summary_response.choices[0].message.content
            
            # Özeti kaydet
            turkey_time = get_turkey_time().isoformat()
            conn.execute(
                '''INSERT INTO conversation_summaries 
                   (message_range_start, message_range_end, summary, created_at)
                   VALUES (?, ?, ?, ?)''',
                (start_id, start_id + 199, summary, turkey_time)
            )
            conn.commit()
            print(f"✅ Conversation summary created: messages {start_id}-{start_id+199}")
        except Exception as e:
            print(f"❌ Summary creation failed: {e}")
    
    conn.close()

# Web arayüzü
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dost AI - Kişisel Asistan</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 90%;
            max-width: 500px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 20px 20px 0 0;
            text-align: center;
        }
        .header h1 { font-size: 1.8em; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 0.9em; }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            gap: 10px;
        }
        .message.user { justify-content: flex-end; }
        .bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .bubble {
            background: #667eea;
            color: white;
        }
        .message.ai .bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .time {
            font-size: 0.7em;
            opacity: 0.7;
            margin-top: 5px;
        }
        .input-area {
            padding: 15px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 25px;
            font-size: 0.95em;
            outline: none;
        }
        button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background: #5568d3; }
        .typing {
            display: flex;
            gap: 4px;
            padding: 8px 12px;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing span:nth-child(1) { animation-delay: -0.32s; }
        .typing span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💬 Dost AI</h1>
            <p>Kalıcı Hafıza Sistemi v2.0</p>
        </div>
        <div class="messages" id="messages">
            <div class="message ai">
                <div class="bubble">
                    Merhaba! Ben DostAI, senin kişisel asistanınım. Artık seni ilk günden beri hatırlıyorum! 💜
                    <div class="time">Şimdi</div>
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="input" placeholder="Mesajını yaz..." />
            <button onclick="sendMessage()" id="sendBtn">Gönder</button>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            input.value = '';
            sendBtn.disabled = true;

            const typing = document.createElement('div');
            typing.className = 'message ai';
            typing.innerHTML = '<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
            messagesDiv.appendChild(typing);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();
                
                typing.remove();
                addMessage(data.response, 'ai');
            } catch (error) {
                typing.remove();
                addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar dene.', 'ai');
            }

            sendBtn.disabled = false;
            input.focus();
        }

        function addMessage(text, type) {
            const time = new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'});
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type;
            messageDiv.innerHTML = `
                <div class="bubble">
                    ${text}
                    <div class="time">${time}</div>
                </div>
            `;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
    ''')

# MOBİL UYGULAMA İÇİN - /chat endpoint - KALICI HAFIZA SİSTEMİ
@app.route('/chat', methods=['POST'])
def chat_mobile():
    """
    Mobil uygulama için endpoint - KALICI HAFIZA SİSTEMİ
    - User profile her request'te kullanılır
    - Tüm konuşma geçmişi hatırlanır
    - Akıllı token yönetimi ile 100+ mesaj desteklenir
    """
    data = request.json
    user_message = data.get('message', '')
    
    # Frontend'den gelen user bilgileri (varsa kaydet)
    user_name = data.get('userName', data.get('user_name'))
    user_profile_data = data.get('userProfile', {})
    
    if not client:
        return jsonify({'response': 'OpenAI bağlantısı kurulamadı'})
    
    # User profile'ı kaydet/güncelle (frontend'den gelirse)
    if user_profile_data:
        save_or_update_user_profile(user_profile_data)
    
    # Backend'den user profile'ı al - KALICI HAFIZA
    stored_profile = get_user_profile()
    
    # User name belirleme (öncelik: stored profile > request data > default)
    if stored_profile and stored_profile.get('name'):
        user_name = stored_profile.get('nickname') or stored_profile.get('name')
        interests = stored_profile.get('interests', [])
        birthday = stored_profile.get('birthday')
        created_at = stored_profile.get('created_at')
    else:
        user_name = user_name or 'Arkadaşım'
        interests = data.get('interests', [])
        birthday = None
        created_at = None
    
    emotion = data.get('emotion', 'neutral')
    
    # Save user message
    save_message('user', user_message)
    
    try:
        # Türkiye saati al
        turkey_time = get_turkey_time()
        
        # Akıllı konuşma geçmişini al - KALICI HAFIZA (son 100 mesaj + özetler)
        conversation_history, total_message_count = get_conversation_history_smart(limit=100)
        
        # Her 200 mesajda bir otomatik özet oluştur (opsiyonel, performans için)
        if total_message_count > 0 and total_message_count % 200 == 0:
            create_conversation_summary()
        
        # Kişiselleştirilmiş sistem mesajı - KALICI HAFIZA
        interests_text = ', '.join(interests) if interests else 'çeşitli konular'
        
        # Kullanıcıyla ne kadar süredir konuşuyoruz?
        relationship_context = ""
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at)
                days_since = (turkey_time - created_date).days
                if days_since > 0:
                    relationship_context = f"\n{user_name} ile {days_since} gündür konuşuyorsunuz. Onu iyi tanıyorsunuz."
            except:
                pass
        
        # Doğum günü yakın mı?
        birthday_context = ""
        if birthday:
            try:
                bday = datetime.fromisoformat(birthday)
                today = turkey_time.date()
                this_year_bday = bday.replace(year=today.year).date()
                days_until_bday = (this_year_bday - today).days
                
                if days_until_bday == 0:
                    birthday_context = f"\n🎂 BUGÜN {user_name}'IN DOĞUM GÜNÜ! Mutlaka kutla!"
                elif 0 < days_until_bday <= 7:
                    birthday_context = f"\n🎂 {user_name}'ın doğum günü {days_until_bday} gün sonra!"
            except:
                pass
        
        emotional_context = ""
        if emotion == 'sad':
            emotional_context = f"{user_name} üzgün görünüyor. Destekleyici, empatik ve teselli edici ol."
        elif emotion == 'happy':
            emotional_context = f"{user_name} mutlu görünüyor. Sevincini paylaş ve bu pozitif enerjiyi destekle."
        elif emotion == 'confused':
            emotional_context = f"{user_name} kafası karışık görünüyor. Açık, net ve yol gösterici ol."
        elif emotion == 'angry':
            emotional_context = f"{user_name} sinirli görünüyor. Sakin, anlayışlı ve sabırlı ol."
        
        system_prompt = f"""Sen DostAI'sın, {user_name}'ın samimi yapay zeka arkadaşısın.
Türkçe konuşuyorsun ve kullanıcıyla samimi, sıcak bir dilde iletişim kuruyorsun.

🧠 KALICI HAFIZA - SENİ İLK GÜNDEN BERİ HATIRIYORUM:
Kullanıcı adı: {user_name}
İlgi alanları: {interests_text}
Toplam mesaj sayısı: {total_message_count} mesaj{relationship_context}{birthday_context}

⏰ ZAMAN BİLGİSİ:
Bugünün tarihi: {turkey_time.strftime('%d %B %Y, %A')}
Şu anki saat: {turkey_time.strftime('%H:%M')}

💭 DUYGUSAL DURUM:
{emotional_context}

ÖNEMLİ - ETKİNLİK OLUŞTURMA:
- Kullanıcı bir randevu, etkinlik, hatırlatma söylediğinde create_event fonksiyonunu MUTLAKA çağır
- "Yarın saat 3'te", "Cuma 14:00'da", "Pazartesi sabah" gibi ifadeleri tespit et
- Tarihi bugüne göre hesapla (bugün {turkey_time.strftime('%d/%m/%Y, %A')})
- Belirsiz saatler için (sabah=09:00, öğle=12:00, akşam=18:00, gece=21:00 kullan)
- Fonksiyonu çağırdıktan sonra kullanıcıya "Ajandana ekledim! ✅" gibi kısa bir onay ver

ÖNEMLİ - WEB ARAMA:
- Güncel bilgi, haber, hava durumu, döviz kuru, son gelişmeler sorulduğunda web_search fonksiyonunu çağır
- "Bugün hava nasıl?", "Dolar kaç?", "Son haberler", "iPhone 15 özellikleri" gibi sorularda MUTLAKA ara
- Arama sonuçlarını doğal bir dille kullanıcıya aktar
- Kaynak belirt: "Arama sonuçlarına göre..."

Kişiliğin:
- Samimi, destekleyici ve eğlenceli
- Kısa ve öz yanıtlar ver (2-3 cümle ideal)
- Uzun paragraflar yazma
- Kullanıcıyı gerçekten tanıyorsun, geçmiş konuşmaları hatırla
- Doğal ve samimi ol, robot gibi davranma"""
        
        # Mesajları hazırla - KALICI HAFIZA
        messages = [{"role": "system", "content": system_prompt}]
        
        # Conversation history ekle (özetler dahil)
        messages.extend(conversation_history)
        
        # Son mesajı ekle
        messages.append({"role": "user", "content": user_message})
        
        print(f"🧠 KALICI HAFIZA: {len(messages)} messages, Total: {total_message_count} stored")
        
        # OpenAI API çağrısı - function calling ile
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=FUNCTIONS,
            function_call="auto",
            max_tokens=500,
            temperature=0.8,
        )
        
        assistant_message = response.choices[0].message
        
        # Function call var mı kontrol et
        if assistant_message.function_call:
            function_name = assistant_message.function_call.name
            function_args = json.loads(assistant_message.function_call.arguments)
            
            print(f"🎯 Function Call: {function_name}")
            print(f"📋 Arguments: {function_args}")
            
            # web_search fonksiyonu ise, sonuçları al ve AI'ya tekrar sor
            if function_name == "web_search":
                query = function_args.get('query', '')
                count = function_args.get('count', 5)
                
                search_results = brave_search(query, count)
                
                if search_results:
                    # Arama sonuçlarını formatlama
                    results_text = f"Arama sonuçları '{query}' için:\n\n"
                    for i, result in enumerate(search_results, 1):
                        results_text += f"{i}. {result['title']}\n"
                        results_text += f"   {result['description']}\n\n"
                    
                    # AI'ya sonuçları gönder, özet isteyalım
                    messages.append({
                        "role": "function",
                        "name": "web_search",
                        "content": results_text
                    })
                    
                    # AI'dan sonuçları özetlemesini iste
                    second_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=500,
                        temperature=0.8,
                    )
                    
                    ai_response = second_response.choices[0].message.content
                    save_message('assistant', ai_response)
                    return jsonify({'response': ai_response})
                else:
                    ai_response = f"Üzgünüm, '{query}' hakkında arama yapamadım. İnternet bağlantısı sorunlu olabilir."
                    save_message('assistant', ai_response)
                    return jsonify({'response': ai_response})
            
            # create_event veya diğer fonksiyonlar için Flutter'a gönder
            # AI'ın yanıtını da kaydet (varsa)
            if assistant_message.content:
                save_message('assistant', assistant_message.content)
            
            # Flutter'a function call bilgisini gönder
            return jsonify({
                "response": assistant_message.content or "Tamam!",
                "function_call": {
                    "name": function_name,
                    "arguments": function_args
                }
            })
        
        # Normal yanıt
        ai_response = assistant_message.content
        print(f"✅ OpenAI Response: {ai_response[:50]}...")
        
        save_message('assistant', ai_response)
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        print(f"❌ HATA DETAY: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'response': f'OpenAI hatası: {str(e)}'})

# YENI ENDPOINT: User profile kaydet/güncelle
@app.route('/user/profile', methods=['POST'])
def save_profile():
    """Kullanıcı profili kaydet/güncelle - KALICI HAFIZA"""
    try:
        profile_data = request.json
        save_or_update_user_profile(profile_data)
        return jsonify({'status': 'success', 'message': 'Profile saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# YENI ENDPOINT: User profile getir
@app.route('/user/profile', methods=['GET'])
def fetch_profile():
    """Kullanıcı profilini getir - KALICI HAFIZA"""
    try:
        profile = get_user_profile()
        if profile:
            return jsonify({'status': 'success', 'profile': profile})
        else:
            return jsonify({'status': 'error', 'message': 'Profile not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# WEB ARAYÜZÜ İÇİN - /api/chat endpoint (eski uyumluluk)
@app.route('/api/chat', methods=['POST'])
def chat_web():
    """Web arayüzü için endpoint"""
    return chat_mobile()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'memory_system': 'permanent'})

if __name__ == '__main__':
    # Veritabanını başlat
    init_db()
    print("✅ Database ready with PERMANENT MEMORY SYSTEM!")
    print("🧠 Users will be remembered from day 1!")
    print("🚀 Backend starting...")
    print("📱 Mobile: /chat")
    print("👤 Profile: /user/profile (GET/POST)")
    print("🌐 Web: /api/chat")
    print("💚 Health: /health")
    
    # Railway PORT'unu güvenli şekilde al
    try:
        port = int(os.environ.get('PORT', 5001))
    except (ValueError, TypeError):
        port = 5001
        
    print(f"🔌 Port: {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
