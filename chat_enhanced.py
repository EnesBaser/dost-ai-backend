"""
Enhanced Chat Endpoint with Learning System
Analyzes messages, learns about user, personalizes responses
"""

from flask import Blueprint, request, jsonify
import openai
import os
from learning_engine import LearningEngine
from context_tracker import ContextTracker
import psycopg2

chat_bp = Blueprint('chat_enhanced', __name__)

def get_db_connection():
    """Get database connection"""
    import os
    from psycopg2.extras import RealDictCursor
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found!")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def save_user_facts(device_id: str, analysis: dict):
    """Save analyzed facts to database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Save interests
        for interest in analysis.get('interests', []):
            cur.execute("""
                INSERT INTO user_facts (device_id, category, fact_key, confidence, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (device_id, category, fact_key)
                DO UPDATE SET 
                    confidence = (user_facts.confidence + EXCLUDED.confidence) / 2,
                    updated_at = CURRENT_TIMESTAMP
            """, (device_id, interest['category'], interest['fact_key'], 
                  interest['confidence'], interest['source']))
        
        # Save location
        if analysis.get('location'):
            loc = analysis['location']
            cur.execute("""
                INSERT INTO user_facts (device_id, category, fact_key, confidence, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (device_id, category, fact_key)
                DO UPDATE SET 
                    confidence = EXCLUDED.confidence,
                    updated_at = CURRENT_TIMESTAMP
            """, (device_id, loc['category'], loc['fact_key'], 
                  loc['confidence'], loc['source']))
        
        # Save personality traits
        for trait in analysis.get('personality', []):
            cur.execute("""
                INSERT INTO personality_traits (device_id, trait, score, evidence_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (device_id, trait)
                DO UPDATE SET 
                    score = (personality_traits.score + EXCLUDED.score) / 2,
                    evidence_count = personality_traits.evidence_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (device_id, trait['trait'], trait['score'], trait['evidence_count']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving facts: {e}")
        return False


def get_user_facts(device_id: str) -> list:
    """Get user facts for personalization"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT category, fact_key, confidence
            FROM user_facts
            WHERE device_id = %s AND confidence > 0.5
            ORDER BY confidence DESC
            LIMIT 20
        """, (device_id,))
        
        facts = []
        for row in cur.fetchall():
            facts.append({
                'category': row[0],
                'fact_key': row[1],
                'confidence': row[2]
            })
        
        cur.close()
        conn.close()
        
        return facts
        
    except Exception as e:
        print(f"❌ Error getting facts: {e}")
        return []


def get_conversation_context(messages: list) -> dict:
    """
    Analyze recent messages to understand conversation context
    Returns topics, keywords, and conversation flow
    """
    if not messages or len(messages) < 2:
        return {'topics': [], 'keywords': [], 'flow': 'new'}
    
    # Get last 5 messages
    recent = messages[-5:]
    
    # Extract keywords and topics
    topics = set()
    keywords = set()
    
    # Technical/domain keywords
    technical_domains = {
        'math': ['türev', 'integral', 'limit', 'matematik', 'denklem', 'fonksiyon'],
        'programming': ['kod', 'python', 'javascript', 'hata', 'bug', 'function', 'class'],
        'engineering': ['cıvata', 'somun', 'malzeme', 'tork', 'çelik', 'mühendis'],
        'health': ['sağlık', 'hasta', 'doktor', 'tedavi', 'ilaç'],
        'education': ['ders', 'öğretmen', 'sınav', 'ödev', 'okul'],
        'sports': ['maç', 'antrenman', 'spor', 'takım', 'gol']
    }
    
    for msg in recent:
        content = msg.get('content', '').lower()
        
        # Check domains
        for domain, domain_keywords in technical_domains.items():
            for kw in domain_keywords:
                if kw in content:
                    topics.add(domain)
                    keywords.add(kw)
    
    # Determine conversation flow
    if len(recent) > 3:
        flow = 'deep_conversation'
    elif len(recent) > 1:
        flow = 'continuing'
    else:
        flow = 'new'
    
    return {
        'topics': list(topics),
        'keywords': list(keywords),
        'flow': flow,
        'message_count': len(recent)
    }


def enhance_prompt_with_context(base_prompt: str, context: dict) -> str:
    """
    Enhance system prompt with conversation context
    """
    if not context['topics']:
        return base_prompt
    
    context_addition = "\n\n🔄 KONUŞMA BAĞLAMI:\n"
    
    # Add topics
    if context['topics']:
        topics_str = ', '.join(context['topics'])
        context_addition += f"- Konular: {topics_str}\n"
    
    # Add flow-based instructions
    if context['flow'] == 'deep_conversation':
        context_addition += """- Derin bir sohbet devam ediyor. 
  Önceki mesajlara referans ver.
  "Dediğim gibi...", "Hatırlarsan..." gibi bağlantılar kur.\n"""
    elif context['flow'] == 'continuing':
        context_addition += "- Devam eden bir sohbet var. Bağlamı koru.\n"
    
    # Domain-specific enhancements
    if 'math' in context['topics']:
        context_addition += """- Matematik konuşuyorsunuz.
  Formüller ver, adım adım açıkla, görsel örnekler sun.\n"""
    
    if 'programming' in context['topics']:
        context_addition += """- Kod üzerine konuşuyorsunuz.
  Kod örnekleri ver, best practices öner, debug yardımı yap.\n"""
    
    if 'engineering' in context['topics']:
        context_addition += """- Teknik/endüstriyel konu.
  Teknik detaylar ver, standartlar belirt, güvenlik hatırlat.\n"""
    
    if 'health' in context['topics']:
        context_addition += """- Sağlık konusu.
  Empatik ol, bilimsel ama anlaşılır, uzmana yönlendir.\n"""
    
    if 'education' in context['topics']:
        context_addition += """- Eğitim konusu.
  Motive et, adım adım öğret, sabırlı ol.\n"""
    
    return base_prompt + context_addition


@chat_bp.route('/chat-enhanced', methods=['POST'])
def chat_enhanced():
    """Enhanced chat endpoint with learning"""
    device_id = request.headers.get('X-Device-ID')
    
    if not device_id:
        return jsonify({'error': 'Device ID required', 'code': 'NO_DEVICE_ID'}), 400
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    conversation_history = data.get('conversation_history', [])
    
    if not user_message:
        return jsonify({'error': 'Message required', 'code': 'NO_MESSAGE'}), 400
    
    try:
        # 1. ANALYZE USER MESSAGE (Learn about user)
        analysis = LearningEngine.analyze_message(user_message)
        
        # 2. SAVE LEARNED FACTS
        save_user_facts(device_id, analysis)
        
        # 3. GET USER FACTS (For personalization)
        user_facts = get_user_facts(device_id)
        
        # 4. BUILD PERSONALIZED SYSTEM PROMPT
        base_prompt = """Sen DostAI'sın, kullanıcının kişisel yapay zeka arkadaşısın.
        
Görevin:
- Kullanıcıyı tanımak ve hatırlamak
- Kişiselleştirilmiş önerilerde bulunmak
- Proaktif ve yardımcı olmak
- Samimi ve arkadaş canlısı olmak

Önemli:
- Kullanıcının ilgi alanlarını, takımlarını, hobilerini hatırla
- Konumuna göre öneriler yap
- Kişiliğine uygun yanıtlar ver"""

        # Add user context
        if user_facts:
            context_parts = ["\n\n📊 KULLANICI PROFİLİ:"]
            
            # Group by category
            facts_by_cat = {}
            for fact in user_facts:
                cat = fact['category']
                if cat not in facts_by_cat:
                    facts_by_cat[cat] = []
                facts_by_cat[cat].append(fact)
            
            # ============================================
            # DOMAIN EXPERTISE DETECTION
            # ============================================
            profession = None
            expertise_mode = None
            
            # Career/Profession
            if 'career' in facts_by_cat:
                for fact in facts_by_cat['career']:
                    if 'profession:' in fact['fact_key']:
                        profession = fact['fact_value'] or fact['fact_key'].split(':')[1].replace('_', ' ').title()
                        context_parts.append(f"- Meslek: {profession}")
            
            # Sports (detailed)
            if 'sports' in facts_by_cat:
                teams = [f['fact_value'] or f['fact_key'].split(':')[1].replace('_', ' ').title() 
                        for f in facts_by_cat['sports'] if 'team:' in f['fact_key']]
                sports = [f['fact_value'] or f['fact_key'].split(':')[1].replace('_', ' ').title()
                         for f in facts_by_cat['sports'] if 'sport:' in f['fact_key']]
                
                if teams:
                    context_parts.append(f"- Takımlar: {', '.join(teams)}")
                if sports:
                    context_parts.append(f"- Spor Dalları: {', '.join(sports)}")
            
            # Hobbies
            if 'hobbies' in facts_by_cat:
                hobbies = [f['fact_value'] or f['fact_key'].split(':')[1].replace('_', ' ').title()
                          for f in facts_by_cat['hobbies']]
                if hobbies:
                    context_parts.append(f"- Hobiler: {', '.join(hobbies)}")
            
            # Cinema
            if 'cinema' in facts_by_cat:
                context_parts.append("- Sinema severim")
            
            # Theater
            if 'theater' in facts_by_cat:
                context_parts.append("- Tiyatro ile ilgileniyorum")
            
            # Location
            if 'location' in facts_by_cat:
                locations = [f['fact_value'] or f['fact_key'].split(':')[1].replace('_', ' ').title()
                           for f in facts_by_cat['location']]
                if locations:
                    context_parts.append(f"- Konum: {', '.join(locations)}")
            
            base_prompt += "\n".join(context_parts)
            
            # ============================================
            # ADAPTIVE EXPERTISE MODE
            # ============================================
            
            # Industrial/Technical (Sanayici, Mühendis, Teknisyen)
            if profession and any(word in profession.lower() for word in ['mühendis', 'teknisyen', 'sanayici', 'usta', 'işçi']):
                expertise_mode = 'technical'
                base_prompt += """

🔧 UZMANLUK MODU: TEKNİK & ENDÜSTRİYEL

Kullanıcı teknik/endüstriyel alanda çalışıyor.

Yaklaşımın:
- Pratik ve somut çözümler sun
- Teknik terminoloji kullan (ama anlaşılır ol)
- Malzeme özellikleri, ölçüler, standartlar hakkında bilgilisin
- Güvenlik önemli, hatırlat
- "Şöyle yap" yerine "Neden böyle" açıkla

Örnekler:
- Cıvata/somun → Çap, sertlik sınıfı, tork değerleri ver
- Malzeme → Özellikler, kullanım alanları
- Arıza → Sebep + çözüm + önleme"""
            
            # Education (Öğrenci, Öğretmen)
            elif profession and any(word in profession.lower() for word in ['öğrenci', 'öğretmen', 'eğitimci', 'hoca']):
                expertise_mode = 'education'
                base_prompt += """

📚 UZMANLUK MODU: EĞİTİM & MOTİVASYON

Kullanıcı eğitim alanında.

Yaklaşımın:
- Empatik ve destekleyici ol
- Motivasyon ver, sabırlı ol
- Karmaşık konuları basitle
- Adım adım öğret
- Görsel örnekler ver
- "Anlamadım" demekten çekinmesinler

Örnekler:
- Matematik → Günlük hayattan örnekler, adım adım
- Motivasyon düşük → Destekle, küçük hedefler koy
- Sınav stresi → Teknikler öner, rahatlat"""
            
            # Programming (Yazılımcı, Developer)
            elif profession and any(word in profession.lower() for word in ['yazılımcı', 'developer', 'programcı', 'coder']) or \
                 any(cat in facts_by_cat for cat in ['technology', 'programming']):
                expertise_mode = 'programming'
                base_prompt += """

💻 UZMANLUK MODU: YAZILIM & KODLAMA

Kullanıcı yazılım geliştirici.

Yaklaşımın:
- Kod örnekleri ver (markdown formatında)
- Best practices öner
- Debugging yardımı yap
- Performans ve güvenlik önemli
- Alternatif yaklaşımlar sun

Örnekler:
- Hata → Neden oldu, nasıl düzelir, gelecekte önleme
- Yeni özellik → Temiz kod, test edilebilir, maintainable
- Seçim yapma → Pros/cons, use case'e göre"""
            
            # Healthcare (Sağlık çalışanı, Hasta)
            elif profession and any(word in profession.lower() for word in ['doktor', 'hemşire', 'sağlık', 'tıp']):
                expertise_mode = 'healthcare'
                base_prompt += """

⚕️ UZMANLUK MODU: SAĞLIK & DESTEK

Kullanıcı sağlık alanıyla ilgili.

Yaklaşımın:
- Empatik ve anlayışlı ol
- Bilimsel ama anlaşılır
- Ciddi konularda uzmana yönlendir
- Destekleyici ol
- Gizlilik ve etik önemli

ÖNEMLİ:
- Tanı koymaya çalışma
- Kesin tedavi önerme
- Acil durumlarda 112'yi hatırlat"""
            
            # General Support (Diğer meslekler)
            else:
                expertise_mode = 'general'
                base_prompt += """

✨ GENEL DESTEK MODU

Kullanıcıyla samimi dost ol.

Yaklaşımın:
- İlgi alanlarına göre konuş
- Kişiliğine uygun ton kullan
- Proaktif önerilerde bulun
- Yaşam deneyimlerini paylaş
- Rehberlik et ama öğüt verme gibi olma"""
        
        # 5. ANALYZE CONVERSATION CONTEXT
        # Build messages for context analysis
        all_messages = conversation_history + [{"role": "user", "content": user_message}]
        context = ContextTracker.analyze_messages(all_messages)
        
        # Add context to prompt
        context_prompt = ContextTracker.build_context_prompt(context)
        base_prompt += context_prompt
        
        # 6. PREPARE MESSAGES FOR OPENAI
        messages = [{"role": "system", "content": base_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # 7. CALL OPENAI
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # 7. RETURN ENHANCED RESPONSE
        return jsonify({
            'response': ai_response,
            'learned_facts': len(analysis.get('interests', [])) + (1 if analysis.get('location') else 0),
            'personalization_level': len(user_facts),
            'timestamp': analysis['timestamp']
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({
            'error': 'Chat failed',
            'message': str(e),
            'code': 'CHAT_ERROR'
        }), 500


# Register routes
def register_enhanced_chat(app):
    """Register enhanced chat routes"""
    app.register_blueprint(chat_bp, url_prefix='/api')
    print("✅ Enhanced chat routes registered")
