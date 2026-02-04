   
    
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import openai  # <- Değişti
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

# OpenAI client setup
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY bulunamadı!")
    openai.api_key = api_key
    print("✅ OpenAI client başarıyla oluşturuldu!")
except Exception as e:
    print(f"❌ OpenAI client oluşturulamadı: {e}")
    openai = None

# Database helper functions
def get_db():
    conn = sqlite3.connect('memory.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_turkey_time():
    return datetime.now(TURKEY_TZ)

def init_db():
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
    <!-- HTML kısmı değişmedi, GitHub'daki aynı -->
    ''')

# /chat endpoint
@app.route('/chat', methods=['POST'])
def chat_mobile():
    data = request.json
    user_message = data.get('message', '')
    user_name = data.get('userName', data.get('user_name', 'Arkadaşım'))
    conversation_history = data.get('conversation_history', [])
    interests = data.get('interests', [])
    emotion = data.get('emotion', 'neutral')
    
    if not openai:
        return jsonify({'response': 'OpenAI bağlantısı kurulamadı'})
    
    save_message('user', user_message)
    
    try:
        interests_text = ', '.join(interests) if interests else 'çeşitli konular'
        
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
        
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-10:])
        messages.append({"role": "user", "content": user_message})
        
        print(f"🔥 Sending to OpenAI: {len(messages)} messages")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.8,
        )
        ai_response = response.choices[0].message.content
        
        print(f"✅ OpenAI Response: {ai_response[:50]}...")
        save_message('assistant', ai_response)
        return jsonify({'response': ai_response})
    except Exception as e:
        print(f"❌ HATA DETAY: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'response': f'OpenAI hatası: {str(e)}'})

@app.route('/api/chat', methods=['POST'])
def chat_web():
    return chat_mobile()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    print("✅ Veritabanı hazır!")
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
