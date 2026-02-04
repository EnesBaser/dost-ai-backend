from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime
import pytz

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

# Database helper functions
def get_db():
    conn = sqlite3.connect('memory.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_turkey_time():
    """Türkiye saatini döndür"""
    return datetime.now(TURKEY_TZ)

def init_db():
    """Veritabanını başlat"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Mesajı Türkiye saati ile kaydet"""
    conn = get_db()
    turkey_time = get_turkey_time().isoformat()
    conn.execute('INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)', 
                 (role, content, turkey_time))
    conn.commit()
    conn.close()

def get_conversation_history(limit=10):
    conn = get_db()
    messages = conn.execute(
        'SELECT role, content FROM messages ORDER BY id DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [{"role": msg['role'], "content": msg['content']} for msg in reversed(messages)]

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
            border-radius: 18px 18px 4px 18px;
        }
        .message.ai .bubble {
            background: white;
            color: #333;
            border-radius: 18px 18px 18px 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .time {
            font-size: 0.75em;
            opacity: 0.7;
            margin-top: 5px;
        }
        .input-area {
            padding: 15px;
            background: white;
            border-radius: 0 0 20px 20px;
            display: flex;
            gap: 10px;
            border-top: 1px solid #eee;
        }
        #messageInput {
            flex: 1;
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 25px;
            font-size: 1em;
            outline: none;
        }
        #sendBtn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        #sendBtn:hover { transform: scale(1.05); }
        #sendBtn:disabled { opacity: 0.5; cursor: not-allowed; }
        .typing {
            display: flex;
            padding: 12px 16px;
            background: white;
            border-radius: 18px 18px 18px 4px;
            max-width: 70px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .typing span {
            height: 8px;
            width: 8px;
            background: #667eea;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
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
            <p>Kişisel AI Asistanın - Seni Hatırlıyor! 🧠</p>
        </div>
        <div class="messages" id="messages">
            <div class="message ai">
                <div class="bubble">
                    Merhaba! Ben Dost, senin AI arkadaşın. Artık konuşmalarımızı hatırlıyorum! 😊
                    <div class="time" id="firstTime"></div>
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Mesajını yaz..." />
            <button id="sendBtn" onclick="sendMessage()">Gönder</button>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        document.getElementById('firstTime').textContent = new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'});

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
            typing.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
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

# MOBİL UYGULAMA İÇİN - /chat endpoint
# MOBİL UYGULAMA İÇİN - /chat endpoint
@app.route('/chat', methods=['POST'])
def chat_mobile():
    """Mobil uygulama için endpoint"""
    data = request.json
    user_message = data.get('message', '')
    user_name = data.get('userName', data.get('user_name', 'Arkadaşım'))  # DEĞİŞTİ: Her iki key'i de kontrol et
    conversation_history = data.get('conversation_history', [])  # YENİ: Flutter'dan gelen history
    interests = data.get('interests', [])
    emotion = data.get('emotion', 'neutral')
    
    if not client:
        return jsonify({'response': 'OpenAI bağlantısı kurulamadı'})
    
    # Save user message
    save_message('user', user_message)
    
    try:
        # Kişiselleştirilmiş ve duygusal sistem mesajı
        interests_text = ', '.join(interests) if interests else 'çeşitli konular'
        
        # Duygusal context ekle
        emotional_context = ""
        if emotion == 'sad':
            emotional_context = f"{user_name} üzgün görünüyor. Destekleyici, empatik ve teselli edici ol."
        elif emotion == 'happy':
            emotional_context = f"{user_name} mutlu görünüyor. Sevincini paylaş ve bu pozitif enerjiyi destekle."
        elif emotion == 'confused':
            emotional_context = f"{user_name} kafası karışık görünüyor. Açık, net ve yol gösterici ol."
        elif emotion == 'angry':
            emotional_context = f"{user_name} sinirli görünüyor. Sakin, anlayışlı ve sabırlı ol."
        
        system_prompt = f"""Sen Dost adında, {user_name}'ın en iyi arkadaşısın. 
Samimi, destekleyici ve eğlenceli konuşursun. 
{user_name}'ın ilgi alanları: {interests_text}. 
Geçmiş konuşmaları hatırla ve kullan. İsmiyle hitap et.
{emotional_context}
Kısa ve samimi yanıtlar ver. Uzun paragraflar yazma."""
        
        # Prepare messages for GPT - Flutter'dan gelen history'yi kullan
        messages = [{"role": "system", "content": system_prompt}]
        
        # DEĞİŞTİ: Flutter'dan gelen conversation_history'yi kullan
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Son 10 mesaj
        
        # Şu anki mesajı ekle
        messages.append({"role": "user", "content": user_message})
        
        print(f"🔥 Sending to OpenAI: {len(messages)} messages")  # DEBUG
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.8,
        )
        ai_response = response.choices[0].message.content
        
        print(f"✅ OpenAI Response: {ai_response[:50]}...")  # DEBUG
        
        # Save AI response
        save_message('assistant', ai_response)
        
        return jsonify({'response': ai_response})
    except Exception as e:
        print(f"❌ HATA DETAY: {str(e)}")
        import traceback
        traceback.print_exc()  # YENİ: Detaylı hata
        return jsonify({'response': f'OpenAI hatası: {str(e)}'})
# WEB ARAYÜZÜ İÇİN - /api/chat endpoint (eski uyumluluk)
@app.route('/api/chat', methods=['POST'])
def chat_web():
    """Web arayüzü için endpoint"""
    return chat_mobile()  # Aynı fonksiyonu kullan

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})
if __name__ == '__main__':
    init_db()
    print("✅ Veritabanı hazır!")
    
    port = int(os.environ.get('PORT', 8080))  # Railway PORT
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)