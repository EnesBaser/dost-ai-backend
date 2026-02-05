import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI

# --------------------
# Flask App
# --------------------
app = Flask(__name__)
CORS(app)  # 🔴 MOBİL İÇİN KRİTİK

# --------------------
# OpenAI Client
# --------------------
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY bulunamadı")
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client hazır")
except Exception as e:
    print(f"❌ OpenAI client hatası: {e}")
    client = None

# --------------------
# Database
# --------------------
DB_PATH = "chat.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()
print("✅ Veritabanı hazır")

# --------------------
# Web UI
# --------------------
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dost AI</title>
<style>
body { font-family: Arial; background:#f0f0f0; display:flex; justify-content:center; }
#box { width:100%; max-width:500px; background:white; margin-top:40px; padding:20px; border-radius:10px; }
#messages { height:300px; overflow:auto; border:1px solid #ccc; padding:10px; margin-bottom:10px; }
input { width:80%; padding:8px; }
button { padding:8px; }
</style>
</head>
<body>
<div id="box">
<h2>🤖 Dost AI</h2>
<div id="messages"></div>
<input id="msg" placeholder="Mesaj yaz">
<button onclick="send()">Gönder</button>
</div>

<script>
async function send() {
    const input = document.getElementById("msg");
    const text = input.value.trim();
    if(!text) return;
    input.value = "";

    document.getElementById("messages").innerHTML += "<div><b>Sen:</b> "+text+"</div>";

    const res = await fetch("/chat", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ message:text })
    });

    const data = await res.json();
    document.getElementById("messages").innerHTML += "<div><b>Dost:</b> "+data.response+"</div>";
}
</script>
</body>
</html>
""")

# --------------------
# Chat API
# --------------------
@app.route("/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({"response": "AI hazır değil"}), 500

    data = request.get_json()
    user_message = data.get("message", "")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (role, content) VALUES (?,?)", ("user", user_message))
    conn.commit()

    c.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    messages = [{"role": r, "content": c} for r,c in reversed(rows)]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        return jsonify({"response": str(e)}), 500

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (role, content) VALUES (?,?)", ("assistant", reply))
    conn.commit()
    conn.close()

    return jsonify({"response": reply})

# --------------------
# Health
# --------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
