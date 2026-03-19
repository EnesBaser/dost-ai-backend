"""
Learning System API Routes
Manages user facts, preferences, and personalization
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import psycopg2
from learning_engine import LearningEngine

learning_bp = Blueprint('learning', __name__)

def get_db_connection():
    """Get database connection"""
    import os
    from psycopg2.extras import RealDictCursor
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found!")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

# ================================================
# USER FACTS ENDPOINTS
# ================================================

@learning_bp.route('/facts', methods=['GET'])
def get_user_facts():
    """Get all facts for a user"""
    device_id = request.headers.get('X-Device-ID')
    
    print(f"🔍 GET_FACTS called with device_id: {device_id}")
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    try:
        print("🔍 Attempting to get DB connection...")
        conn = get_db_connection()
        print("✅ DB connection successful!")
        
        cur = conn.cursor()
        print("✅ Cursor created!")
        
        cur.execute("""
            SELECT category, fact_key, fact_value, confidence, source, created_at
            FROM user_facts
            WHERE device_id = %s
            ORDER BY confidence DESC, created_at DESC
        """, (device_id,))
        print("✅ Query executed!")
        
        facts = []
        for row in cur.fetchall():
            facts.append({
                'category': row['category'],
                'fact_key': row['fact_key'],
                'fact_value': row['fact_value'],
                'confidence': row['confidence'],
                'source': row['source'],
                'created_at': row['created_at'].isoformat()
            })
        
        cur.close()
        conn.close()
        
        print(f"✅ Returning {len(facts)} facts")
        return jsonify({'facts': facts, 'count': len(facts)})
    
    except Exception as e:
        print(f"❌ ERROR IN GET_FACTS: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get facts', 'details': str(e)}), 500


@learning_bp.route('/facts', methods=['POST'])
def add_user_fact():
    """Add or update a user fact"""
    device_id = request.headers.get('X-Device-ID')
    data = request.get_json()
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    category = data.get('category')
    fact_key = data.get('fact_key')
    fact_value = data.get('fact_value', '')
    confidence = data.get('confidence', 1.0)
    source = data.get('source', 'explicit')
    
    if not category or not fact_key:
        return jsonify({'error': 'Category and fact_key required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Upsert (insert or update)
        cur.execute("""
            INSERT INTO user_facts (device_id, category, fact_key, fact_value, confidence, source)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (device_id, category, fact_key) 
            DO UPDATE SET 
                fact_value = EXCLUDED.fact_value,
                confidence = EXCLUDED.confidence,
                updated_at = CURRENT_TIMESTAMP
        """, (device_id, category, fact_key, fact_value, confidence, source))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Fact saved'})
    
    except Exception as e:
        print(f"Error saving fact: {e}")
        return jsonify({'error': 'Failed to save fact'}), 500


@learning_bp.route('/analyze', methods=['POST'])
def analyze_message():
    """Analyze a message and extract facts"""
    device_id = request.headers.get('X-Device-ID')
    data = request.get_json()
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    message = data.get('message', '')
    auto_save = data.get('auto_save', True)
    
    # Analyze message
    analysis = LearningEngine.analyze_message(message)
    
    # Auto-save facts if enabled
    if auto_save:
        try:
            print(f"🔍 AUTO-SAVE starting for device: {device_id}")
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Save interests
            for interest in analysis['interests']:
                print(f"🔍 Saving interest: {interest}")
                cur.execute("""
                    INSERT INTO user_facts (device_id, category, fact_key, confidence, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, category, fact_key)
                    DO UPDATE SET 
                        confidence = (user_facts.confidence + EXCLUDED.confidence) / 2,
                        updated_at = CURRENT_TIMESTAMP
                """, (device_id, interest['category'], interest['fact_key'], 
                      interest['confidence'], interest['source']))
                print(f"✅ Interest saved!")
            
            # Save location
            if analysis['location']:
                print(f"🔍 Saving location: {analysis['location']}")
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
                print(f"✅ Location saved!")
            
            # Save personality traits
            for trait in analysis['personality']:
                print(f"🔍 Saving trait: {trait}")
                cur.execute("""
                    INSERT INTO personality_traits (device_id, trait, score, evidence_count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (device_id, trait)
                    DO UPDATE SET 
                        score = (personality_traits.score + EXCLUDED.score) / 2,
                        evidence_count = personality_traits.evidence_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (device_id, trait['trait'], trait['score'], trait['evidence_count']))
                print(f"✅ Trait saved!")
            
            print(f"🔍 Committing transaction...")
            conn.commit()
            print(f"✅ COMMIT SUCCESSFUL!")
            cur.close()
            conn.close()
            print(f"✅ Connection closed!")
            
        except Exception as e:
            print(f"❌ Error auto-saving facts: {e}")
            import traceback
            traceback.print_exc()
    
    return jsonify({
        'analysis': analysis,
        'auto_saved': auto_save
    })


# ================================================
# USER PREFERENCES ENDPOINTS
# ================================================

@learning_bp.route('/preferences', methods=['GET'])
def get_preferences():
    """Get user preferences"""
    device_id = request.headers.get('X-Device-ID')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT location_city, location_district, notification_time, 
                   proactive_suggestions, data_collection
            FROM user_preferences
            WHERE device_id = %s
        """, (device_id,))
        
        row = cur.fetchone()
        
        if row:
            preferences = {
                'location_city': row[0],
                'location_district': row[1],
                'notification_time': str(row[2]) if row[2] else None,
                'proactive_suggestions': row[3],
                'data_collection': row[4]
            }
        else:
            # Return defaults
            preferences = {
                'location_city': None,
                'location_district': None,
                'notification_time': '09:00',
                'proactive_suggestions': True,
                'data_collection': True
            }
        
        cur.close()
        conn.close()
        
        return jsonify(preferences)
    
    except Exception as e:
        print(f"Error getting preferences: {e}")
        return jsonify({'error': 'Failed to get preferences'}), 500


@learning_bp.route('/preferences', methods=['PUT'])
def update_preferences():
    """Update user preferences"""
    device_id = request.headers.get('X-Device-ID')
    data = request.get_json()
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Upsert preferences
        cur.execute("""
            INSERT INTO user_preferences (
                device_id, location_city, location_district, 
                notification_time, proactive_suggestions, data_collection
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (device_id)
            DO UPDATE SET
                location_city = COALESCE(EXCLUDED.location_city, user_preferences.location_city),
                location_district = COALESCE(EXCLUDED.location_district, user_preferences.location_district),
                notification_time = COALESCE(EXCLUDED.notification_time, user_preferences.notification_time),
                proactive_suggestions = COALESCE(EXCLUDED.proactive_suggestions, user_preferences.proactive_suggestions),
                data_collection = COALESCE(EXCLUDED.data_collection, user_preferences.data_collection),
                updated_at = CURRENT_TIMESTAMP
        """, (
            device_id,
            data.get('location_city'),
            data.get('location_district'),
            data.get('notification_time'),
            data.get('proactive_suggestions'),
            data.get('data_collection')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Preferences updated'})
    
    except Exception as e:
        print(f"Error updating preferences: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500


# ================================================
# PERSONALIZATION ENDPOINTS
# ================================================

@learning_bp.route('/personalized-prompt', methods=['POST'])
def get_personalized_prompt():
    """Get personalized system prompt based on user facts"""
    device_id = request.headers.get('X-Device-ID')
    data = request.get_json()
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    message = data.get('message', '')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get user facts
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
        
        # Generate personalized prompt
        personalized_prompt = LearningEngine.generate_personalized_prompt(facts, message)
        
        return jsonify({
            'personalized_prompt': personalized_prompt,
            'facts_used': len(facts)
        })
    
    except Exception as e:
        print(f"Error generating prompt: {e}")
        return jsonify({'error': 'Failed to generate prompt'}), 500


@learning_bp.route('/personality', methods=['GET'])
def get_personality():
    """Get user personality profile"""
    device_id = request.headers.get('X-Device-ID')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT trait, score, evidence_count
            FROM personality_traits
            WHERE device_id = %s
            ORDER BY score DESC
        """, (device_id,))
        
        traits = []
        for row in cur.fetchall():
            traits.append({
                'trait': row[0],
                'score': row[1],
                'evidence_count': row[2]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({'personality': traits})
    
    except Exception as e:
        print(f"Error getting personality: {e}")
        return jsonify({'error': 'Failed to get personality'}), 500


# ================================================
# REGISTRATION
# ================================================

def register_learning_routes(app):
    """Register learning routes with Flask app"""
    app.register_blueprint(learning_bp, url_prefix='/api/learning')
    print("✅ Learning system routes registered")
